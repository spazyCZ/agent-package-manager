"""Initialize a local registry."""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from pathlib import Path

import click
from rich.console import Console

from aam_cli.core.config import RegistrySource, load_config, save_global_config
from aam_cli.registry.local import LocalRegistry
from aam_cli.utils.paths import to_file_url

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


@click.command("init")
@click.argument("path", type=click.Path())
@click.option("--default", is_flag=True, help="Also register and set as default")
@click.option("--force", is_flag=True, help="Reinitialize even if registry exists")
@click.pass_context
def registry_init(
    ctx: click.Context,
    path: str,
    default: bool,
    force: bool,
) -> None:
    """Create a new local file-based registry."""
    console: Console = ctx.obj["console"]
    registry_path = Path(path).expanduser().resolve()

    logger.info(
        f"Initializing local registry: path='{registry_path}', default={default}, force={force}"
    )

    try:
        LocalRegistry.init_registry(registry_path, force=force)
    except ValueError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        ctx.exit(1)
        return
    except PermissionError:
        console.print(
            f"[red]Error:[/red] Cannot write to {registry_path}: "
            "Permission denied.\n"
            "[yellow]Suggestion:[/yellow] Check directory permissions or "
            "choose a different location with write access."
        )
        ctx.exit(1)
        return

    console.print(f"[green]✓[/green] Created local registry at {registry_path}")
    console.print("  registry.yaml")
    console.print("  index.yaml")
    console.print("  packages/")

    if default:
        config_data = load_config()
        registry_name = registry_path.name
        url = to_file_url(registry_path)

        for existing_registry in config_data.registries:
            existing_registry.default = False

        config_data.registries.append(
            RegistrySource(
                name=registry_name,
                url=url,
                type="local",
                default=True,
            )
        )
        save_global_config(config_data)
        console.print(
            f"\n[green]✓[/green] Registered as default: '{registry_name}' ({url})"
        )
