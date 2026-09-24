"""``aam pkg publish`` — Publish archive to a registry.

Delegates to :mod:`aam_cli.services.publish_service`, which loads the
universal manifest (``package.agent.json`` / ``package.agent.yaml`` /
``aam.yaml``) and enforces ``governance.publish_policy`` before publishing.

Reference: spec 004 US7.
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

from aam_cli.core.manifest import load_manifest_universal
from aam_cli.services.governance_service import PolicyViolationError
from aam_cli.services.publish_service import publish_package

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


@click.command("publish")
@click.option(
    "--registry",
    "registry_name",
    default=None,
    help="Target registry name (default: default registry)",
)
@click.option("--tag", default="latest", help="Distribution tag")
@click.option("--dry-run", is_flag=True, help="Preview without publishing")
@click.pass_context
def pkg_publish(
    ctx: click.Context,
    registry_name: str | None,
    tag: str,
    dry_run: bool,
) -> None:
    """Publish a packed archive to a registry.

    Must be run from the package directory containing a manifest
    (``package.agent.json``, ``package.agent.yaml``, or ``aam.yaml``).

    Examples::

        aam pkg publish
        aam pkg publish --registry local
        aam pkg publish --tag beta
    """
    console: Console = ctx.obj["console"]
    pkg_path = Path.cwd()

    # -----
    # Step 1: Load manifest just to report name/version and support dry-run
    # -----
    try:
        manifest = load_manifest_universal(pkg_path)
    except FileNotFoundError:
        console.print(
            "[red]Error:[/red] No manifest found. Run 'aam pkg init' first."
        )
        ctx.exit(1)
        return
    except Exception as exc:
        console.print(f"[red]Error:[/red] Invalid package: {exc}")
        ctx.exit(1)
        return

    console.print(f"Publishing [bold]{manifest.name}@{manifest.version}[/bold]...")

    if dry_run:
        console.print("\n[yellow]\\[Dry run — package not published][/yellow]")
        return

    # -----
    # Step 2: Publish via the shared service (universal manifest loading +
    # governance publish_policy enforcement)
    # -----
    try:
        result = publish_package(
            registry_name=registry_name,
            tag=tag,
            project_dir=pkg_path,
        )
    except PolicyViolationError as exc:
        console.print(f"[red]Error:[/red] {exc.violation.message}")
        ctx.exit(1)
        return
    except ValueError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        ctx.exit(1)
        return

    console.print(f"\n  [green]✓[/green] Archive verified: {result['checksum']}")
    console.print("  [green]✓[/green] Copied to registry")
    console.print("  [green]✓[/green] Updated metadata.yaml")
    console.print("  [green]✓[/green] Rebuilt index.yaml")
    console.print(f"  [green]✓[/green] Tagged as '{tag}'")
    console.print(
        f"\n[green]✓[/green] Published {result['package_name']}@{result['version']}"
    )

    logger.info(
        f"Published {result['package_name']}@{result['version']} "
        f"to registry '{result['registry']}'"
    )
