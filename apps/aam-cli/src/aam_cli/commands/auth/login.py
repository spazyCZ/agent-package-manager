"""Authenticate with a package registry."""

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
@click.option("--token", prompt="Auth token", hide_input=True, help="Authentication token")
@click.pass_context
def login(ctx: click.Context, registry: str, token: str) -> None:
    """Authenticate with a package registry."""
    console: Console = ctx.obj["console"]
    registry_url = registry.rstrip("/")

    auth = _load_auth()
    auth[registry_url] = token
    _save_auth(auth)

    console.print(f"[green]✓[/green] Logged in to {registry_url}")
