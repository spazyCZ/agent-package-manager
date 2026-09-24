"""Outdated command for AAM CLI.

Compares installed source packages against their source HEAD commits
and reports which packages have updates available.

Reference: spec 004 US4; contracts/cli-commands.md.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import json
import logging

import click
from rich.console import Console
from rich.table import Table

from aam_cli.core.config import load_config
from aam_cli.core.workspace import read_lock_file
from aam_cli.services.upgrade_service import check_outdated
from aam_cli.utils.paths import resolve_project_dir

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# COMMAND                                                                      #
#                                                                              #
################################################################################


@click.command()
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.option(
    "--global", "-g", "is_global", is_flag=True,
    help="Check global ~/.aam/ packages for updates",
)
@click.pass_context
def outdated(ctx: click.Context, output_json: bool, is_global: bool) -> None:
    """Check for outdated source-installed packages.

    Compares installed package commit SHAs against the source HEAD.
    Packages not installed from sources are shown as "(no source)".

    Use ``-g`` / ``--global`` to check packages in the user-wide
    ``~/.aam/`` directory instead of the project-local ``.aam/`` workspace.

    Examples::

        aam outdated
        aam outdated --json
        aam outdated -g
    """
    console: Console = ctx.obj["console"]
    project_dir = resolve_project_dir(is_global)

    # -----
    # Visual indicator for global mode
    # -----
    if is_global:
        console.print("[dim]Operating in global mode (~/.aam/)[/dim]\n")

    logger.info("Checking for outdated packages")

    # -----
    # Step 1: Run outdated check
    # -----
    config = load_config(project_dir)
    lock = read_lock_file(project_dir)

    result = check_outdated(lock, config)

    # -----
    # Step 2: JSON output
    # -----
    if output_json:
        data = {
            "outdated": [
                {
                    "name": o.name,
                    "current_commit": o.current_commit,
                    "latest_commit": o.latest_commit,
                    "source_name": o.source_name,
                    "has_local_modifications": o.has_local_modifications,
                }
                for o in result.outdated
            ],
            "up_to_date": result.up_to_date,
            "no_source": result.no_source,
            "stale_sources": result.stale_sources,
        }
        click.echo(json.dumps(data, indent=2))
        return

    # -----
    # Step 3: Rich table output
    # -----
    if not lock.packages:
        console.print("No packages installed.")
        return

    if result.stale_sources:
        for src in result.stale_sources:
            console.print(
                f"[yellow]⚠[/yellow] Source '{src}' not updated in 7+ days. "
                f"Run 'aam source update {src}'."
            )
        console.print()

    if not result.outdated:
        console.print("[green]✓[/green] All packages are up to date.")
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("Package", style="cyan")
    table.add_column("Current")
    table.add_column("Latest")
    table.add_column("Source")
    table.add_column("Status")

    for o in result.outdated:
        status = "[yellow]outdated[/yellow]"
        if o.has_local_modifications:
            status = "[red]outdated (modified)[/red]"

        table.add_row(
            o.name,
            o.current_commit,
            o.latest_commit,
            o.source_name,
            status,
        )

    for name in result.up_to_date:
        table.add_row(name, "", "", "", "[green]up to date[/green]")

    for name in result.no_source:
        table.add_row(name, "", "", "(no source)", "[dim]registry[/dim]")

    console.print()
    console.print(table)
    console.print()
    console.print(
        f"  {result.total_outdated} outdated, "
        f"{len(result.up_to_date)} up to date, "
        f"{len(result.no_source)} from registry"
    )
    console.print()


