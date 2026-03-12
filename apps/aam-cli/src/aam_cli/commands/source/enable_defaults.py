"""Enable curated default source repositories."""

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

from aam_cli.services.source_service import DEFAULT_SOURCES, enable_default_sources

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# COMMAND                                                                      #
#                                                                              #
################################################################################


@click.command("enable-defaults")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def enable_defaults(ctx: click.Context, output_json: bool) -> None:
    """Enable all default community skill sources."""
    console: Console = ctx.obj["console"]
    err_console: Console = ctx.obj["err_console"]
    logger.info("CLI source enable-defaults")

    try:
        result = enable_default_sources()
    except Exception as error:
        err_console.print(f"[red]Error:[/red] Failed to enable defaults: {error}")
        logger.error(f"Enable defaults failed: {error}", exc_info=True)
        ctx.exit(1)
        return

    if output_json:
        click.echo(json.dumps(result, indent=2))
        return

    console.print()

    for name in result["registered"]:
        if name in result["re_enabled"]:
            console.print(
                f"  [green]✓[/green] [bold]{name}[/bold] — re-enabled"
            )
        else:
            console.print(
                f"  [green]✓[/green] [bold]{name}[/bold] — added"
            )

    for name in result["skipped"]:
        console.print(
            f"  [dim]–[/dim] [dim]{name}[/dim] — already configured"
        )

    console.print()

    added = len(result["registered"])
    skipped = len(result["skipped"])

    if added > 0:
        console.print(
            f"  [green]{added} source(s) enabled[/green], "
            f"{skipped} already configured "
            f"(out of {result['total']} defaults)"
        )
        console.print()
        console.print(
            "  Run [bold]aam source update --all[/bold] to clone and scan."
        )
    else:
        console.print(
            f"  All {result['total']} default sources are already configured."
        )

    console.print()

    table = Table(
        title="Default Skill Sources",
        show_header=True,
        header_style="bold",
    )
    table.add_column("#", justify="right", style="dim")
    table.add_column("Name", style="cyan")
    table.add_column("URL")
    table.add_column("Path")

    for index, default in enumerate(DEFAULT_SOURCES, start=1):
        table.add_row(
            str(index),
            default["name"],
            default["url"],
            default.get("path", ""),
        )

    console.print(table)
    console.print()
