"""Clean cached package archives."""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging

import click
from rich.console import Console

from aam_cli.services import cache_service

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


@click.command("clean")
@click.argument("package_spec", required=False)
@click.pass_context
def cache_clean(ctx: click.Context, package_spec: str | None) -> None:
    """Remove cached package archives."""
    console: Console = ctx.obj["console"]

    if package_spec and "@" in package_spec:
        parts = package_spec.rsplit("@", 1)
        if len(parts) == 2:
            package_name, version = parts[0], parts[1]
            removed = cache_service.clean(package_name, version)
            console.print(f"Removed {removed} cached entries for {package_spec}")
            return

    removed = cache_service.clean()
    console.print(f"[green]✓[/green] Cleaned {removed} cached packages")
