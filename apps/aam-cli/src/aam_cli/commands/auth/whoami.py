"""Show current registry authentication status."""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging

import click
from rich.console import Console

from aam_cli.commands.auth import get_token

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
def whoami(ctx: click.Context, registry: str) -> None:
    """Show current authentication status."""
    console: Console = ctx.obj["console"]
    registry_url = registry.rstrip("/")

    token = get_token(registry_url)
    if token:
        masked = token[:4] + "..." + token[-4:] if len(token) > 8 else "****"
        console.print(f"Logged in to [bold]{registry_url}[/bold] (token: {masked})")
    else:
        console.print(f"Not logged in to {registry_url}")
