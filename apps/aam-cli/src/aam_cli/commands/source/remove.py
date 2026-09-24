"""Remove a configured artifact source."""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import json
import logging

import click
from rich.console import Console

from aam_cli.services.source_service import remove_source

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
@click.option("--purge-cache", is_flag=True, help="Delete the cached clone directory")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def remove(ctx: click.Context, name: str, purge_cache: bool, output_json: bool) -> None:
    """Remove a configured source."""
    console: Console = ctx.obj["console"]
    err_console: Console = ctx.obj["err_console"]
    logger.info(f"CLI source remove: name='{name}'")

    try:
        result = remove_source(name, purge_cache=purge_cache)
    except ValueError as error:
        err_console.print(f"[red]Error:[/red] {error}")
        ctx.exit(1)
        return

    if output_json:
        click.echo(json.dumps(result, indent=2))
        return

    console.print()
    console.print(
        f"[green]✓[/green] Source '[bold]{name}[/bold]' removed"
    )
    if result["cache_purged"]:
        console.print("  Cache directory purged")
    console.print()
