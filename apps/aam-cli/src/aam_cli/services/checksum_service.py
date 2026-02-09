"""Checksum verification service for installed package integrity.

Provides business logic for verifying that installed package files
have not been modified locally. Also handles pre-upgrade backup
creation for safe upgrades.

Reference: spec.md User Story 4; data-model.md entities 9, 12.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
import shutil
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aam_cli.core.workspace import (
    get_installed_packages,
)
from aam_cli.utils.checksum import calculate_sha256
from aam_cli.utils.paths import get_global_aam_dir, get_packages_dir

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# DATA MODELS                                                                  #
#                                                                              #
################################################################################


@dataclass
class VerifyResult:
    """Result of verifying installed package integrity.

    Attributes:
        package_name: Name of the verified package.
        version: Installed package version.
        ok_files: Files matching their recorded checksums.
        modified_files: Files whose checksums differ from recorded.
        missing_files: Files in checksums but not on disk.
        untracked_files: Files on disk but not in checksums.
        has_checksums: False if the lock file lacks file checksums.
        is_clean: True if no modifications detected.
    """

    package_name: str
    version: str
    ok_files: list[str] = field(default_factory=list)
    modified_files: list[str] = field(default_factory=list)
    missing_files: list[str] = field(default_factory=list)
    untracked_files: list[str] = field(default_factory=list)
    has_checksums: bool = True
    is_clean: bool = True


@dataclass
class BackupRecord:
    """Record of a backup created before upgrading a package.

    Attributes:
        package_name: Name of the backed-up package.
        backup_dir: Path to the backup directory.
        backed_up_files: Relative paths of backed-up files.
        created_at: ISO 8601 timestamp of backup creation.
    """

    package_name: str
    backup_dir: str
    backed_up_files: list[str] = field(default_factory=list)
    created_at: str = ""


################################################################################
#                                                                              #
# CONSTANTS                                                                    #
#                                                                              #
################################################################################

# Backup directory name under ~/.aam/
BACKUPS_DIR_NAME: str = "backups"

# Checksum prefix (matches checksum.py convention)
CHECKSUM_PREFIX: str = "sha256:"

################################################################################
#                                                                              #
# INTERNAL HELPERS                                                             #
#                                                                              #
################################################################################


def _compute_file_sha256(file_path: Path) -> str:
    """Compute SHA-256 hex digest for a single file.

    Returns only the hex digest without the ``sha256:`` prefix,
    matching the ``FileChecksums.files`` format.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hex digest string.
    """
    full_checksum = calculate_sha256(file_path)
    # -----
    # Strip the "sha256:" prefix since FileChecksums stores raw hex
    # -----
    return full_checksum.removeprefix(CHECKSUM_PREFIX)


def _list_package_files(package_dir: Path) -> list[str]:
    """List all files in a package directory, relative to it.

    Excludes hidden files and directories.

    Args:
        package_dir: Root directory of the installed package.

    Returns:
        List of relative file paths as strings.
    """
    files: list[str] = []
    for file_path in package_dir.rglob("*"):
        if file_path.is_file():
            rel = str(file_path.relative_to(package_dir))
            # Skip hidden files
            if not any(part.startswith(".") for part in Path(rel).parts):
                files.append(rel)
    return sorted(files)


################################################################################
#                                                                              #
# PUBLIC API: VERIFY                                                           #
#                                                                              #
################################################################################


def verify_package(
    package_name: str,
    project_dir: Path | None = None,
) -> dict[str, Any]:
    """Verify integrity of an installed package's files.

    Compares each file's current SHA-256 checksum against the
    recorded checksums in the lock file.

    Args:
        package_name: Name of the package to verify.
        project_dir: Project root directory.

    Returns:
        Dict with verification results matching ``VerifyResult``
        fields.

    Raises:
        ValueError: If the package is not installed.
    """
    logger.info(f"Verifying package: name='{package_name}'")

    # -----
    # Load lock file and find the package
    # -----
    packages = get_installed_packages(project_dir)
    locked = packages.get(package_name)

    if locked is None:
        raise ValueError(
            f"[AAM_PACKAGE_NOT_INSTALLED] Package '{package_name}' "
            f"is not installed"
        )

    # -----
    # Check if file checksums are available
    # -----
    if locked.file_checksums is None:
        logger.info(
            f"No file checksums available for '{package_name}'. "
            f"Package was installed before checksum tracking was added."
        )
        return {
            "package_name": package_name,
            "version": locked.version,
            "ok_files": [],
            "modified_files": [],
            "missing_files": [],
            "untracked_files": [],
            "has_checksums": False,
            "is_clean": True,
        }

    # -----
    # Get the package installation directory
    # -----
    packages_dir = get_packages_dir(project_dir)
    package_dir = packages_dir / package_name

    if not package_dir.is_dir():
        raise ValueError(
            f"[AAM_PACKAGE_NOT_INSTALLED] Package directory for "
            f"'{package_name}' not found at {package_dir}"
        )

    # -----
    # Compare checksums
    # -----
    recorded = locked.file_checksums.files
    ok_files: list[str] = []
    modified_files: list[str] = []
    missing_files: list[str] = []

    for rel_path, expected_hash in recorded.items():
        file_path = package_dir / rel_path
        if not file_path.is_file():
            missing_files.append(rel_path)
            continue

        actual_hash = _compute_file_sha256(file_path)
        if actual_hash == expected_hash:
            ok_files.append(rel_path)
        else:
            modified_files.append(rel_path)

    # -----
    # Find untracked files (on disk but not in checksums)
    # -----
    disk_files = set(_list_package_files(package_dir))
    recorded_files = set(recorded.keys())
    untracked_files = sorted(disk_files - recorded_files)

    is_clean = not modified_files and not missing_files

    logger.info(
        f"Verification complete: package='{package_name}', "
        f"ok={len(ok_files)}, modified={len(modified_files)}, "
        f"missing={len(missing_files)}, untracked={len(untracked_files)}, "
        f"clean={is_clean}"
    )

    return {
        "package_name": package_name,
        "version": locked.version,
        "ok_files": ok_files,
        "modified_files": modified_files,
        "missing_files": missing_files,
        "untracked_files": untracked_files,
        "has_checksums": True,
        "is_clean": is_clean,
    }


def verify_all(
    project_dir: Path | None = None,
) -> dict[str, Any]:
    """Verify integrity of all installed packages.

    Args:
        project_dir: Project root directory.

    Returns:
        Dict with ``results`` list and summary counts.
    """
    logger.info("Verifying all installed packages")

    packages = get_installed_packages(project_dir)
    results: list[dict[str, Any]] = []

    for pkg_name in packages:
        result = verify_package(pkg_name, project_dir)
        results.append(result)

    clean_count = sum(1 for r in results if r["is_clean"])
    modified_count = sum(1 for r in results if not r["is_clean"])

    return {
        "results": results,
        "total_packages": len(results),
        "clean_packages": clean_count,
        "modified_packages": modified_count,
    }


################################################################################
#                                                                              #
# PUBLIC API: BACKUP                                                           #
#                                                                              #
################################################################################


def create_backup(
    package_name: str,
    modified_files: list[str],
    project_dir: Path | None = None,
) -> dict[str, Any]:
    """Create a backup of modified files before an upgrade.

    Copies modified files to ``~/.aam/backups/<name>--<date>/``.

    Args:
        package_name: Name of the package to back up.
        modified_files: List of relative file paths to back up.
        project_dir: Project root directory.

    Returns:
        Dict with backup metadata.
    """
    logger.info(
        f"Creating backup: package='{package_name}', "
        f"files={len(modified_files)}"
    )

    # -----
    # Create backup directory
    # -----
    now = datetime.now(UTC)
    date_str = now.strftime("%Y%m%d-%H%M%S")
    backup_dir = (
        get_global_aam_dir()
        / BACKUPS_DIR_NAME
        / f"{package_name}--{date_str}"
    )
    backup_dir.mkdir(parents=True, exist_ok=True)

    # -----
    # Copy modified files
    # -----
    packages_dir = get_packages_dir(project_dir)
    package_dir = packages_dir / package_name
    backed_up: list[str] = []

    for rel_path in modified_files:
        src = package_dir / rel_path
        dst = backup_dir / rel_path

        if src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            backed_up.append(rel_path)
            logger.debug(f"Backed up: {rel_path}")

    logger.info(
        f"Backup created: dir='{backup_dir}', files={len(backed_up)}"
    )

    return {
        "package_name": package_name,
        "backup_dir": str(backup_dir),
        "backed_up_files": backed_up,
        "created_at": now.isoformat(),
    }


################################################################################
#                                                                              #
# PUBLIC API: CHECK MODIFICATIONS (UPGRADE WARNING)                            #
#                                                                              #
################################################################################


def check_modifications(
    package_name: str,
    project_dir: Path | None = None,
) -> dict[str, Any]:
    """Check if an installed package has locally modified files.

    Used before upgrade/reinstall to warn the user about local changes
    that would be overwritten.

    Args:
        package_name: Name of the package to check.
        project_dir: Project root directory.

    Returns:
        Dict with keys ``has_modifications``, ``modified_files``,
        ``missing_files``, ``has_checksums``.
    """
    logger.info(f"Checking modifications: package='{package_name}'")

    packages = get_installed_packages(project_dir)
    locked = packages.get(package_name)

    if locked is None:
        return {
            "has_modifications": False,
            "modified_files": [],
            "missing_files": [],
            "has_checksums": False,
        }

    if locked.file_checksums is None:
        return {
            "has_modifications": False,
            "modified_files": [],
            "missing_files": [],
            "has_checksums": False,
        }

    # -----
    # Re-use verify_package logic for consistency
    # -----
    result = verify_package(package_name, project_dir)

    has_mods = bool(result["modified_files"] or result["missing_files"])

    logger.info(
        f"Modification check complete: package='{package_name}', "
        f"has_modifications={has_mods}, "
        f"modified={len(result['modified_files'])}, "
        f"missing={len(result['missing_files'])}"
    )

    return {
        "has_modifications": has_mods,
        "modified_files": result["modified_files"],
        "missing_files": result["missing_files"],
        "has_checksums": True,
    }


################################################################################
#                                                                              #
# PUBLIC API: COMPUTE CHECKSUMS                                                #
#                                                                              #
################################################################################


def compute_file_checksums(
    directory: Path,
    files: list[str] | None = None,
) -> dict[str, str]:
    """Compute SHA-256 checksums for files in a directory.

    Args:
        directory: Root directory to compute checksums for.
        files: Optional list of specific files to checksum.
            If None, checksums all files in the directory.

    Returns:
        Dict mapping relative file paths to hex digests.
    """
    logger.info(f"Computing file checksums: dir='{directory}'")

    if files is None:
        files = _list_package_files(directory)

    checksums: dict[str, str] = {}
    for rel_path in files:
        file_path = directory / rel_path
        if file_path.is_file():
            checksums[rel_path] = _compute_file_sha256(file_path)

    logger.info(f"Checksums computed: files={len(checksums)}")
    return checksums
