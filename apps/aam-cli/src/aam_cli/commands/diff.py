"""Diff command for AAM CLI.

Shows unified diff output for modified files in installed packages.
Delegates diff computation to :mod:`aam_cli.services.diff_service`.

Reference: contracts/cli-commands.md (aam diff)
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
from rich.syntax import Syntax

from aam_cli.services.diff_service import diff_package

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
