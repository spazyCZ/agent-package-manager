"""Scan a registered source for artifacts."""

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

from aam_cli.services.source_service import scan_source

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
@click.argument("name")
@click.option("--type", "type_filter", multiple=True, help="Filter by artifact type")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def scan(
    ctx: click.Context,
    name: str,
    type_filter: tuple[str, ...],
    output_json: bool,
) -> None:
    """Scan a registered source for artifacts."""
    console: Console = ctx.obj["console"]
    err_console: Console = ctx.obj["err_console"]
    logger.info(f"CLI source scan: name='{name}'")

    try:
        result = scan_source(name)
    except ValueError as error:
        err_console.print(f"[red]Error:[/red] {error}")
        ctx.exit(1)
        return

    artifacts = result["artifacts"]
    if type_filter:
        artifacts = [artifact for artifact in artifacts if artifact["type"] in type_filter]

    if output_json:
        output = {**result, "artifacts": artifacts}
        click.echo(json.dumps(output, indent=2))
        return

    console.print()
    console.print(
        f"[bold]{result['source_name']}[/bold] — "
        f"Commit {result['commit'][:12]}"
    )
    if result["scan_path"]:
        console.print(f"  Scan path: {result['scan_path']}")
    console.print()

    if not artifacts:
        console.print("  No artifacts found.")
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("Name", style="cyan")
    table.add_column("Type")
    table.add_column("Path")
    table.add_column("Description", max_width=255)

    for artifact in artifacts:
        description = (artifact.get("description") or "")[:255]
        table.add_row(
            artifact["name"],
            artifact["type"],
            artifact["path"],
            description,
        )

    console.print(table)
    console.print()
    console.print(f"  Total: [bold]{len(artifacts)}[/bold] artifacts")
    console.print()
