"""Remove saved registry authentication."""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging

import click
from rich.console import Console

from aam_cli.commands.auth import _load_auth, _save_auth

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


@click.command()
@click.option("--registry", default="https://registry.aam.dev", help="Registry URL")
@click.pass_context
def logout(ctx: click.Context, registry: str) -> None:
    """Remove authentication for a registry."""
    console: Console = ctx.obj["console"]
    registry_url = registry.rstrip("/")

    auth = _load_auth()
    if registry_url in auth:
        del auth[registry_url]
        _save_auth(auth)
        console.print(f"[green]✓[/green] Logged out from {registry_url}")
    else:
        console.print(f"[yellow]Not logged in to {registry_url}[/yellow]")
