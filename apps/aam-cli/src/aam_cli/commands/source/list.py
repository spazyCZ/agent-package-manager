"""List configured artifact sources."""

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

from aam_cli.services.source_service import list_sources

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


@click.command("list")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def list_cmd(ctx: click.Context, output_json: bool) -> None:
    """List all configured remote sources."""
    console: Console = ctx.obj["console"]
    logger.info("CLI source list")

    result = list_sources()

    if output_json:
        click.echo(json.dumps(result, indent=2))
        return

    sources = result["sources"]

    if not sources:
        console.print()
        console.print("No sources configured. Use 'aam source add' to register one.")
        console.print()
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("Name", style="cyan")
    table.add_column("Publisher", style="magenta")
    table.add_column("URL")
    table.add_column("Ref")
    table.add_column("Path")
    table.add_column("Artifacts", justify="right")
    table.add_column("Last Fetched")

    for source_entry in sources:
        name_display = source_entry["name"]
        if source_entry["default"]:
            name_display += " [dim](default)[/dim]"

        publisher = (
            source_entry["name"].split("/")[0]
            if "/" in source_entry["name"]
            else "—"
        )

        fetched = source_entry.get("last_fetched", "")
        if fetched:
            fetched = fetched[:10]

        table.add_row(
            name_display,
            publisher,
            source_entry["url"],
            source_entry["ref"],
            source_entry["path"] or "—",
            str(source_entry.get("artifact_count", "—")),
            fetched or "—",
        )

    console.print()
    console.print(table)
    console.print()
    console.print(f"  Total: {result['count']} source(s)")
    console.print()
