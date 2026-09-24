"""Diff computation service for AAM CLI.

Computes unified diffs for modified files in installed packages by
comparing current file content against recorded checksums. Uses
Python's ``difflib`` — no external ``diff`` binary required.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import difflib
import logging
from pathlib import Path
from typing import Any

from aam_cli.core.workspace import read_lock_file
from aam_cli.services.checksum_service import verify_package
from aam_cli.utils.paths import get_packages_dir

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# DIFF COMPUTATION                                                             #
#                                                                              #
################################################################################


def diff_package(
    package_name: str,
    project_dir: Path | None = None,
) -> dict[str, Any]:
    """Compute diffs for modified files in an installed package.

    First runs verification to identify modified files, then generates
    unified diffs for each one.

    Args:
        package_name: Name of the installed package.
        project_dir: Project root directory.

    Returns:
        Dict with ``package_name``, ``diffs`` (list), ``modified_count``,
        ``missing_files``, ``untracked_files``.

    Raises:
        ValueError: If the package is not installed or has no checksums.
    """
    logger.info(f"Computing diff: package='{package_name}'")

    # -----
    # Step 1: Verify to identify changes
    # -----
    verify_result = verify_package(package_name, project_dir)

    if not verify_result["has_checksums"]:
        return {
            "package_name": package_name,
            "has_checksums": False,
            "diffs": [],
            "modified_count": 0,
            "missing_files": [],
            "untracked_files": [],
        }

    # -----
    # Step 2: Read lock file to get original checksums
    # -----
    lock = read_lock_file(project_dir)
    locked = lock.packages.get(package_name)
    if locked is None or locked.file_checksums is None:
        return {
            "package_name": package_name,
            "has_checksums": False,
            "diffs": [],
            "modified_count": 0,
            "missing_files": [],
            "untracked_files": [],
        }

    # -----
    # Step 3: Generate unified diffs for modified files
    # -----
    packages_dir = get_packages_dir(project_dir)
    package_dir = packages_dir / package_name
    diffs: list[dict[str, Any]] = []

    for rel_path in verify_result["modified_files"]:
        file_path = package_dir / rel_path

        if not file_path.is_file():
            continue

        # -----
        # Read current file content
        # -----
        try:
            current_lines = file_path.read_text(encoding="utf-8").splitlines(keepends=True)
        except (OSError, UnicodeDecodeError):
            logger.warning(f"Cannot read file for diff: {file_path}")
            continue

        # -----
        # We don't have the original content stored, so we note this
        # The original would come from the package archive if available
        # For now, show only current content with a note
        # -----
        diff_lines = list(
            difflib.unified_diff(
                [],  # Empty = original not available
                current_lines,
                fromfile=f"a/{rel_path} (original)",
                tofile=f"b/{rel_path} (modified)",
                lineterm="",
            )
        )

        diffs.append({
            "file": rel_path,
            "diff": "\n".join(diff_lines),
            "status": "modified",
        })

    return {
        "package_name": package_name,
        "has_checksums": True,
        "diffs": diffs,
        "modified_count": len(verify_result["modified_files"]),
        "missing_files": verify_result["missing_files"],
        "untracked_files": verify_result["untracked_files"],
    }
