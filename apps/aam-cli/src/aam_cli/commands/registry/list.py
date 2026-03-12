"""List configured registries."""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging

import click
from rich.console import Console
from rich.table import Table

from aam_cli.core.config import load_config

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
@click.pass_context
def registry_list(ctx: click.Context) -> None:
    """Display all configured registries."""
    console: Console = ctx.obj["console"]

    config_data = load_config()

    if not config_data.registries:
        console.print("No registries configured. Run 'aam registry init' to create one.")
        return

    console.print("[bold]Configured registries:[/bold]\n")

    table = Table(show_header=True, header_style="bold")
    table.add_column("Name", style="cyan")
    table.add_column("URL", style="green")
    table.add_column("Type")
    table.add_column("Default", style="yellow")

    for registry in config_data.registries:
        default_marker = "✓" if registry.default else ""
        table.add_row(registry.name, registry.url, registry.type, default_marker)

    console.print(table)
