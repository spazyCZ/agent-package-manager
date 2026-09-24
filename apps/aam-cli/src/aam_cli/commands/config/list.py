"""List AAM configuration values."""

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
def config_list(ctx: click.Context) -> None:
    """List all configuration values."""
    console: Console = ctx.obj["console"]

    config_data = load_config()

    console.print("[bold]AAM Configuration:[/bold]\n")

    table = Table(show_header=True, header_style="bold")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Source", style="dim")

    table.add_row("default_platform", config_data.default_platform, "config")
    table.add_row(
        "active_platforms",
        ", ".join(config_data.active_platforms),
        "config",
    )

    for index, registry in enumerate(config_data.registries):
        table.add_row(f"registries.{index}.name", registry.name, "config")
        table.add_row(f"registries.{index}.url", registry.url, "config")
        table.add_row(
            f"registries.{index}.default",
            str(registry.default),
            "config",
        )

    table.add_row(
        "security.require_checksum",
        str(config_data.security.require_checksum),
        "default",
    )
    table.add_row(
        "security.require_signature",
        str(config_data.security.require_signature),
        "default",
    )

    if config_data.author.name:
        table.add_row("author.name", config_data.author.name, "config")
    if config_data.author.email:
        table.add_row("author.email", config_data.author.email, "config")

    console.print(table)
