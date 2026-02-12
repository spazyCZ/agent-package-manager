"""Verify command for AAM CLI.

Checks installed package files against their recorded SHA-256
checksums in the lock file to detect local modifications.

Reference: contracts/cli-commands.md (aam verify)
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import json
import logging
import sys

import click
from rich.console import Console

from aam_cli.services.checksum_service import verify_all, verify_package

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
# COMMAND                                                                      #
#                                                                              #
################################################################################


@click.command()
@click.argument("package", required=False)
@click.option("--all", "check_all", is_flag=True, help="Verify all installed packages")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def verify(
    package: str | None,
    check_all: bool,
    output_json: bool,
) -> None:
    """Verify installed package integrity.

    Checks each installed file's SHA-256 checksum against the recorded
    value in aam-lock.yaml. Reports modified, missing, and untracked files.

    PACKAGE is the name of the package to verify. Use --all to verify
    all installed packages.

    Examples:

      aam verify my-package

      aam verify --all

      aam verify my-package --json
    """
    logger.info(f"CLI verify: package='{package}', all={check_all}")

    if not package and not check_all:
        err_console.print(
            "[red]Error:[/red] Specify a package name or use --all"
        )
        sys.exit(1)

    try:
        result = verify_all() if check_all else verify_package(package)  # type: ignore[arg-type]
    except ValueError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    if output_json:
        click.echo(json.dumps(result, indent=2))
        return

    # -----
    # Rich output
    # -----
    if check_all:
        _display_all_results(result)
    else:
        _display_single_result(result)


def _display_single_result(result: dict) -> None:
    """Display verification result for a single package."""
    console.print()
    name = result["package_name"]
    version = result["version"]

    if not result["has_checksums"]:
        console.print(
            f"[yellow]⚠[/yellow] '{name}@{version}' — "
            f"No file checksums available (installed before checksum tracking)"
        )
        console.print()
        return

    if result["is_clean"]:
        console.print(
            f"[green]✓[/green] '{name}@{version}' — "
            f"All files intact ({len(result['ok_files'])} files verified)"
        )
    else:
        console.print(
            f"[red]✗[/red] '{name}@{version}' — "
            f"Modifications detected"
        )

        if result["modified_files"]:
            console.print(f"\n  [yellow]Modified ({len(result['modified_files'])}):[/yellow]")
            for f in result["modified_files"]:
                console.print(f"    [yellow]~[/yellow] {f}")

        if result["missing_files"]:
            console.print(f"\n  [red]Missing ({len(result['missing_files'])}):[/red]")
            for f in result["missing_files"]:
                console.print(f"    [red]-[/red] {f}")

        if result["untracked_files"]:
            console.print(f"\n  [dim]Untracked ({len(result['untracked_files'])}):[/dim]")
            for f in result["untracked_files"]:
                console.print(f"    [dim]+[/dim] {f}")

    console.print()


def _display_all_results(result: dict) -> None:
    """Display verification results for all packages."""
    console.print()

    for pkg_result in result["results"]:
        _display_single_result(pkg_result)

    console.print(
        f"  Summary: {result['clean_packages']} clean, "
        f"{result['modified_packages']} modified "
        f"(out of {result['total_packages']} packages)"
    )
    console.print()
