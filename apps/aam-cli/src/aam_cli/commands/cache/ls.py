"""List cached package archives."""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging

import click
from rich.console import Console

from aam_cli.services import cache_service

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


@click.command("ls")
@click.pass_context
def cache_ls(ctx: click.Context) -> None:
    """List cached package archives."""
    console: Console = ctx.obj["console"]

    entries = cache_service.list_cached()

    if not entries:
        console.print("Cache is empty.")
        return

    console.print(f"[bold]Cached packages ({len(entries)}):[/bold]\n")
    total_size = 0
    for entry in entries:
        size_kb = entry["size_bytes"] / 1024
        total_size += entry["size_bytes"]
        console.print(f"  {entry['name']}  [dim]{size_kb:.1f} KB[/dim]")

    console.print(f"\n  Total: {total_size / 1024:.1f} KB")
