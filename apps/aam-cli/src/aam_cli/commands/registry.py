"""Registry commands for AAM CLI.

Provides ``aam registry init``, ``aam registry add``,
``aam registry list``, and ``aam registry remove``.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from aam_cli.core.config import RegistrySource, load_config, save_global_config
from aam_cli.registry.local import LocalRegistry
from aam_cli.utils.paths import to_file_url

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
def registry(ctx: click.Context) -> None:
    """Manage registry connections."""
    pass


################################################################################
#                                                                              #
# INIT COMMAND                                                                 #
#                                                                              #
################################################################################


@registry.command("init")
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
    """Create a new local file-based registry.

    Creates the directory structure with ``registry.yaml``,
    ``index.yaml``, and ``packages/``.

    Examples::

        aam registry init ~/my-packages
        aam registry init ./local-registry --default
        aam registry init ~/packages --force
    """
    console: Console = ctx.obj["console"]
    registry_path = Path(path).expanduser().resolve()

    logger.info(
        f"Initializing local registry: path='{registry_path}', default={default}, force={force}"
    )

    # -----
    # Step 1: Initialize the registry directory
    # -----
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

    # -----
    # Step 2: Optionally register as default
    # -----
    if default:
        config = load_config()
        registry_name = registry_path.name
        url = to_file_url(registry_path)

        # Remove any existing default
        for existing_reg in config.registries:
            existing_reg.default = False

        config.registries.append(
            RegistrySource(
                name=registry_name,
                url=url,
                type="local",
                default=True,
            )
        )
        save_global_config(config)
        console.print(f"\n[green]✓[/green] Registered as default: '{registry_name}' ({url})")


################################################################################
#                                                                              #
# ADD COMMAND                                                                  #
#                                                                              #
################################################################################


@registry.command("add")
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
    """Register a new registry source.

    Examples::

        aam registry add local file:///home/user/my-packages
        aam registry add local file:///home/user/packages --default
    """
    console: Console = ctx.obj["console"]

    logger.info(f"Adding registry: name='{name}', url='{url}', default={default}")

    config = load_config()

    # -----
    # Check for duplicate name
    # -----
    if config.get_registry_by_name(name):
        console.print(
            f"[red]Error:[/red] Registry '{name}' already configured. "
            f"Use 'aam registry remove {name}' first."
        )
        ctx.exit(1)
        return

    # -----
    # Validate local URL path exists
    # -----
    if url.startswith("file://"):
        from aam_cli.utils.paths import parse_file_url

        local_path = parse_file_url(url)
        if not local_path.is_dir():
            console.print(f"[red]Error:[/red] Registry path does not exist: {local_path}")
            ctx.exit(1)
            return

    # -----
    # Set as default if requested
    # -----
    if default:
        for existing_reg in config.registries:
            existing_reg.default = False

    config.registries.append(
        RegistrySource(
            name=name,
            url=url,
            type="local" if url.startswith("file://") else "http",
            default=default,
        )
    )

    save_global_config(config)

    console.print(f"[green]✓[/green] Added registry '{name}' ({url})")
    if default:
        console.print("  Set as default: yes")


################################################################################
#                                                                              #
# LIST COMMAND                                                                 #
#                                                                              #
################################################################################


@registry.command("list")
@click.pass_context
def registry_list(ctx: click.Context) -> None:
    """Display all configured registries."""
    console: Console = ctx.obj["console"]

    config = load_config()

    if not config.registries:
        console.print("No registries configured. Run 'aam registry init' to create one.")
        return

    console.print("[bold]Configured registries:[/bold]\n")

    table = Table(show_header=True, header_style="bold")
    table.add_column("Name", style="cyan")
    table.add_column("URL", style="green")
    table.add_column("Type")
    table.add_column("Default", style="yellow")

    for reg in config.registries:
        default_marker = "✓" if reg.default else ""
        table.add_row(reg.name, reg.url, reg.type, default_marker)

    console.print(table)


################################################################################
#                                                                              #
# REMOVE COMMAND                                                               #
#                                                                              #
################################################################################


@registry.command("remove")
@click.argument("name")
@click.pass_context
def registry_remove(ctx: click.Context, name: str) -> None:
    """Remove a configured registry.

    Examples::

        aam registry remove local
    """
    console: Console = ctx.obj["console"]

    logger.info(f"Removing registry: name='{name}'")

    config = load_config()

    # -----
    # Find the registry to remove
    # -----
    found = config.get_registry_by_name(name)
    if not found:
        console.print(
            f"[red]Error:[/red] Registry '{name}' not found. "
            "Run 'aam registry list' to see configured registries."
        )
        ctx.exit(1)
        return

    config.registries = [r for r in config.registries if r.name != name]
    save_global_config(config)

    console.print(f"[green]✓[/green] Removed registry '{name}'")
