"""Remove a configured registry."""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging

import click
from rich.console import Console

from aam_cli.core.config import load_config, save_global_config

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


@click.command("remove")
@click.argument("name")
@click.pass_context
def registry_remove(ctx: click.Context, name: str) -> None:
    """Remove a configured registry."""
    console: Console = ctx.obj["console"]

    logger.info(f"Removing registry: name='{name}'")

    config_data = load_config()
    found = config_data.get_registry_by_name(name)
    if not found:
        console.print(
            f"[red]Error:[/red] Registry '{name}' not found. "
            "Run 'aam registry list' to see configured registries."
        )
        ctx.exit(1)
        return

    config_data.registries = [registry for registry in config_data.registries if registry.name != name]
    save_global_config(config_data)

    console.print(f"[green]✓[/green] Removed registry '{name}'")
