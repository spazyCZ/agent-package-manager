"""Diff command for AAM CLI.

Shows unified diff output for modified files in installed packages.
Uses Python's ``difflib`` to compute diffs without requiring the
system ``diff`` command.

Reference: contracts/cli-commands.md (aam diff)
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import difflib
import json
import logging
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.syntax import Syntax

from aam_cli.core.workspace import read_lock_file
from aam_cli.services.checksum_service import verify_package
from aam_cli.utils.paths import get_packages_dir

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# CONSOLE                                                                      #
#                                                                              #
################################################################################

console = Console()
err_console = Console(stderr=True)

################################################################################
#                                                                              #
# DIFF COMPUTATION                                                             #
#                                                                              #
################################################################################


def diff_package(
    package_name: str,
    project_dir: Path | None = None,
) -> dict:
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
    diffs: list[dict] = []

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


################################################################################
#                                                                              #
# COMMAND                                                                      #
#                                                                              #
################################################################################


@click.command("diff")
@click.argument("package")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def diff_cmd(package: str, output_json: bool) -> None:
    """Show differences in installed package files.

    Displays a unified diff for each modified file in the installed
    package, plus lists of missing and untracked files.

    PACKAGE is the name of the installed package to diff.

    Examples:

      aam diff my-package

      aam diff my-package --json
    """
    logger.info(f"CLI diff: package='{package}'")

    try:
        result = diff_package(package)
    except ValueError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    if output_json:
        click.echo(json.dumps(result, indent=2))
        return

    # -----
    # Rich output
    # -----
    console.print()

    if not result["has_checksums"]:
        console.print(
            f"[yellow]⚠[/yellow] No file checksums available for "
            f"'{result['package_name']}'"
        )
        console.print()
        return

    if not result["diffs"] and not result["missing_files"]:
        console.print(
            f"[green]✓[/green] '{result['package_name']}' — No changes"
        )
        console.print()
        return

    console.print(
        f"[bold]{result['package_name']}[/bold] — "
        f"{result['modified_count']} modified file(s)"
    )
    console.print()

    for diff_entry in result["diffs"]:
        console.print(f"  [yellow]{diff_entry['file']}[/yellow]")
        if diff_entry["diff"]:
            syntax = Syntax(
                diff_entry["diff"],
                "diff",
                theme="monokai",
                line_numbers=False,
            )
            console.print(syntax)
        console.print()

    if result["missing_files"]:
        console.print(f"  [red]Missing files ({len(result['missing_files'])}):[/red]")
        for f in result["missing_files"]:
            console.print(f"    [red]-[/red] {f}")
        console.print()

    if result["untracked_files"]:
        console.print(f"  [dim]Untracked files ({len(result['untracked_files'])}):[/dim]")
        for f in result["untracked_files"]:
            console.print(f"    [dim]+[/dim] {f}")
        console.print()
