"""Config command for AAM CLI.

Provides ``aam config set``, ``aam config get``, and ``aam config list``
to manage AAM configuration values.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging

import click
from rich.console import Console
from rich.table import Table

from aam_cli.core.config import load_config, save_global_config

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# COMMAND GROUP                                                                #
#                                                                              #
################################################################################


@click.group()
@click.pass_context
def config(ctx: click.Context) -> None:
    """Manage AAM configuration."""
    pass


################################################################################
#                                                                              #
# SET COMMAND                                                                  #
#                                                                              #
################################################################################


@config.command("set")
@click.argument("key")
@click.argument("value")
@click.pass_context
def config_set(ctx: click.Context, key: str, value: str) -> None:
    """Set a configuration value.

    Examples::

        aam config set default_platform cursor
        aam config set author.name "My Name"
    """
    console: Console = ctx.obj["console"]

    logger.info(f"Setting config: key='{key}', value='{value}'")

    cfg = load_config()

    # -----
    # Handle dotted keys for nested config
    # -----
    parts = key.split(".")

    if len(parts) == 1:
        # Top-level key
        if hasattr(cfg, key):
            setattr(cfg, key, value)
        else:
            console.print(f"[red]Error:[/red] Unknown config key: {key}")
            ctx.exit(1)
            return
    elif len(parts) == 2:
        # Nested key (e.g., author.name, security.require_checksum)
        section, field = parts
        section_obj = getattr(cfg, section, None)
        if section_obj is not None and hasattr(section_obj, field):
            # Convert value to appropriate type
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

    save_global_config(cfg)
    console.print(f"[green]✓[/green] Set {key} = {value}")


################################################################################
#                                                                              #
# GET COMMAND                                                                  #
#                                                                              #
################################################################################


@config.command("get")
@click.argument("key")
@click.pass_context
def config_get(ctx: click.Context, key: str) -> None:
    """Get a configuration value.

    Examples::

        aam config get default_platform
        aam config get author.name
    """
    console: Console = ctx.obj["console"]

    cfg = load_config()

    parts = key.split(".")

    if len(parts) == 1:
        value = getattr(cfg, key, None)
        if value is not None:
            console.print(f"{key} = {value}")
        else:
            console.print(f"[red]Error:[/red] Unknown config key: {key}")
            ctx.exit(1)
    elif len(parts) == 2:
        section, field = parts
        section_obj = getattr(cfg, section, None)
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


################################################################################
#                                                                              #
# LIST COMMAND                                                                 #
#                                                                              #
################################################################################


@config.command("list")
@click.pass_context
def config_list(ctx: click.Context) -> None:
    """List all configuration values."""
    console: Console = ctx.obj["console"]

    cfg = load_config()

    console.print("[bold]AAM Configuration:[/bold]\n")

    table = Table(show_header=True, header_style="bold")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Source", style="dim")

    # -----
    # Flatten config into key-value pairs
    # -----
    table.add_row("default_platform", cfg.default_platform, "config")
    table.add_row(
        "active_platforms",
        ", ".join(cfg.active_platforms),
        "config",
    )

    for idx, reg in enumerate(cfg.registries):
        table.add_row(f"registries.{idx}.name", reg.name, "config")
        table.add_row(f"registries.{idx}.url", reg.url, "config")
        table.add_row(
            f"registries.{idx}.default",
            str(reg.default),
            "config",
        )

    table.add_row(
        "security.require_checksum",
        str(cfg.security.require_checksum),
        "default",
    )
    table.add_row(
        "security.require_signature",
        str(cfg.security.require_signature),
        "default",
    )

    if cfg.author.name:
        table.add_row("author.name", cfg.author.name, "config")
    if cfg.author.email:
        table.add_row("author.email", cfg.author.email, "config")

    console.print(table)
