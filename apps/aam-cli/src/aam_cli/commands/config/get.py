"""Get an AAM configuration value."""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging

import click
from rich.console import Console

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


@click.command("get")
@click.argument("key")
@click.pass_context
def config_get(ctx: click.Context, key: str) -> None:
    """Get a configuration value."""
    console: Console = ctx.obj["console"]

    config_data = load_config()
    parts = key.split(".")

    if len(parts) == 1:
        value = getattr(config_data, key, None)
        if value is not None:
            console.print(f"{key} = {value}")
        else:
            console.print(f"[red]Error:[/red] Unknown config key: {key}")
            ctx.exit(1)
    elif len(parts) == 2:
        section, field = parts
        section_obj = getattr(config_data, section, None)
        if section_obj is not None:
            value = getattr(section_obj, field, None)
            if value is not None:
                console.print(f"{key} = {value}")
            else:
                console.print(f"[red]Error:[/red] Unknown config key: {key}")
                ctx.exit(1)
        else:
            console.print(f"[red]Error:[/red] Unknown config section: {section}")
            ctx.exit(1)
    else:
        console.print(f"[red]Error:[/red] Unsupported config key depth: {key}")
        ctx.exit(1)
