"""Add a registry connection."""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging

import click
from rich.console import Console

from aam_cli.core.config import RegistrySource, load_config, save_global_config

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


@click.command("add")
@click.argument("name")
@click.argument("url")
@click.option("--default", is_flag=True, help="Set as default registry")
@click.pass_context
def registry_add(
    ctx: click.Context,
    name: str,
    url: str,
    default: bool,
) -> None:
    """Register a new registry source."""
    console: Console = ctx.obj["console"]

    logger.info(f"Adding registry: name='{name}', url='{url}', default={default}")

    config_data = load_config()

    if config_data.get_registry_by_name(name):
        console.print(
            f"[red]Error:[/red] Registry '{name}' already configured. "
            f"Use 'aam registry remove {name}' first."
        )
        ctx.exit(1)
        return

    if url.startswith("file://"):
        from aam_cli.utils.paths import parse_file_url

        local_path = parse_file_url(url)
        if not local_path.is_dir():
            console.print(f"[red]Error:[/red] Registry path does not exist: {local_path}")
            ctx.exit(1)
            return

    if default:
        for existing_registry in config_data.registries:
            existing_registry.default = False

    config_data.registries.append(
        RegistrySource(
            name=name,
            url=url,
            type="local" if url.startswith("file://") else "http",
            default=default,
        )
    )

    save_global_config(config_data)

    console.print(f"[green]✓[/green] Added registry '{name}' ({url})")
    if default:
        console.print("  Set as default: yes")
