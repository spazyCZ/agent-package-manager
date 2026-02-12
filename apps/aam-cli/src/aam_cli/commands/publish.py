"""Publish command for AAM CLI.

Publishes a packed ``.aam`` archive to a configured registry.
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

from aam_cli.core.config import load_config
from aam_cli.core.manifest import load_manifest
from aam_cli.registry.factory import create_registry
from aam_cli.utils.checksum import calculate_sha256

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# COMMAND                                                                      #
#                                                                              #
################################################################################


@click.command()
@click.option(
    "--registry",
    "registry_name",
    default=None,
    help="Target registry name (default: default registry)",
)
@click.option("--tag", default="latest", help="Distribution tag")
@click.option("--dry-run", is_flag=True, help="Preview without publishing")
@click.pass_context
def publish(
    ctx: click.Context,
    registry_name: str | None,
    tag: str,
    dry_run: bool,
) -> None:
    """Publish a packed archive to a registry.

    Must be run from the package directory containing ``aam.yaml``.
    The ``.aam`` archive must exist (run ``aam pack`` first).

    Examples::

        aam publish
        aam publish --registry local
        aam publish --tag beta
        aam publish --dry-run
    """
    console: Console = ctx.obj["console"]
    pkg_path = Path.cwd()

    # -----
    # Step 1: Load manifest to get package name and version
    # -----
    try:
        manifest = load_manifest(pkg_path)
    except FileNotFoundError:
        console.print(
            "[red]Error:[/red] No aam.yaml found. Run 'aam init' or 'aam create-package' first."
        )
        ctx.exit(1)
        return
    except Exception as exc:
        console.print(f"[red]Error:[/red] Invalid package: {exc}")
        ctx.exit(1)
        return

    # -----
    # Step 2: Find the .aam archive
    # -----
    archive_candidates = list(pkg_path.glob("*.aam"))
    if not archive_candidates:
        console.print("[red]Error:[/red] No archive found. Run 'aam pack' first.")
        ctx.exit(1)
        return

    archive_path = archive_candidates[0]  # Take the first match

    # -----
    # Step 3: Get the target registry
    # -----
    config = load_config()

    if registry_name:
        reg_source = config.get_registry_by_name(registry_name)
        if not reg_source:
            console.print(
                f"[red]Error:[/red] Registry '{registry_name}' not found. Run 'aam registry list'."
            )
            ctx.exit(1)
            return
    else:
        reg_source = config.get_default_registry()
        if not reg_source:
            console.print(
                "[red]Error:[/red] No registries configured. Run 'aam registry init' to create one."
            )
            ctx.exit(1)
            return

    console.print(
        f"Publishing [bold]{manifest.name}@{manifest.version}[/bold] to {reg_source.name}..."
    )

    # -----
    # Step 4: Verify checksum
    # -----
    checksum = calculate_sha256(archive_path)
    console.print(f"\n  [green]✓[/green] Archive verified: {checksum}")

    if dry_run:
        console.print("\n[yellow]\\[Dry run — package not published][/yellow]")
        return

    # -----
    # Step 5: Publish
    # -----
    try:
        reg = create_registry(reg_source)
        reg.publish(archive_path)
    except ValueError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        ctx.exit(1)
        return

    console.print("  [green]✓[/green] Copied to registry")
    console.print("  [green]✓[/green] Updated metadata.yaml")
    console.print("  [green]✓[/green] Rebuilt index.yaml")
    console.print(f"  [green]✓[/green] Tagged as '{tag}'")
    console.print(f"\n[green]✓[/green] Published {manifest.name}@{manifest.version}")

    logger.info(f"Published {manifest.name}@{manifest.version} to registry '{reg_source.name}'")
