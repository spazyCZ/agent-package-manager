"""List unpackaged source candidates."""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import json
import logging
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from aam_cli.services.source_service import list_candidates

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


@click.command()
@click.option("--source", "source_filter", default=None, help="Filter by source name")
@click.option("--type", "type_filter", multiple=True, help="Filter by artifact type")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def candidates(
    ctx: click.Context,
    source_filter: str | None,
    type_filter: tuple[str, ...],
    output_json: bool,
) -> None:
    """List unpackaged artifact candidates across sources."""
    console: Console = ctx.obj["console"]
    err_console: Console = ctx.obj["err_console"]
    logger.info("CLI source candidates")

    type_list = list(type_filter) if type_filter else None

    try:
        result = list_candidates(
            source_filter=source_filter,
            type_filter=type_list,
        )
    except ValueError as error:
        err_console.print(f"[red]Error:[/red] {error}")
        ctx.exit(1)
        return

    if output_json:
        click.echo(json.dumps(result, indent=2))
        return

    candidates_list = result["candidates"]

    if not candidates_list:
        console.print()
        console.print("No unpackaged candidates found.")
        console.print()
        return

    by_source: dict[str, list[dict[str, Any]]] = {}
    for candidate in candidates_list:
        source_name = candidate.get("source_name", "unknown")
        by_source.setdefault(source_name, []).append(candidate)

    console.print()
    for source_name, artifacts in by_source.items():
        console.print(f"[bold]{source_name}[/bold]")

        table = Table(show_header=True, header_style="bold")
        table.add_column("Name", style="cyan")
        table.add_column("Type")
        table.add_column("Path")

        for artifact in artifacts:
            table.add_row(artifact["name"], artifact["type"], artifact["path"])

        console.print(table)
        console.print()

    console.print(
        f"  Total candidates: [bold]{result['total_count']}[/bold]"
    )
    console.print()
