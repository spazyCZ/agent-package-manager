"""Set an AAM configuration value."""

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


@click.command("set")
@click.argument("key")
@click.argument("value")
@click.pass_context
def config_set(ctx: click.Context, key: str, value: str) -> None:
    """Set a configuration value."""
    console: Console = ctx.obj["console"]

    logger.info(f"Setting config: key='{key}', value='{value}'")

    config_data = load_config()
    parts = key.split(".")

    if len(parts) == 1:
        if hasattr(config_data, key):
            current = getattr(config_data, key)
            if isinstance(current, bool):
                setattr(config_data, key, value.lower() in ("true", "1", "yes"))
            elif isinstance(current, int):
                setattr(config_data, key, int(value))
            elif key == "active_platforms":
                # Keep list[str] shape for model serialization and config YAML.
                parsed_platforms = [item.strip() for item in value.split(",") if item.strip()]
                setattr(config_data, key, parsed_platforms)
            else:
                setattr(config_data, key, value)
        else:
            console.print(f"[red]Error:[/red] Unknown config key: {key}")
            ctx.exit(1)
            return
    elif len(parts) == 2:
        section, field = parts
        section_obj = getattr(config_data, section, None)
        if section_obj is not None and hasattr(section_obj, field):
            current = getattr(section_obj, field)
            if isinstance(current, bool):
                setattr(section_obj, field, value.lower() in ("true", "1", "yes"))
            elif isinstance(current, int):
                setattr(section_obj, field, int(value))
            else:
                setattr(section_obj, field, value)
        else:
            console.print(f"[red]Error:[/red] Unknown config key: {key}")
            ctx.exit(1)
            return
    else:
        console.print(f"[red]Error:[/red] Unsupported config key depth: {key}")
        ctx.exit(1)
        return

    save_global_config(config_data)
    console.print(f"[green]✓[/green] Set {key} = {value}")
