"""Authentication commands for AAM CLI.

Provides ``aam login``, ``aam logout``, and ``aam whoami`` for
managing registry authentication tokens.

Reference: UAAPS v0.5.0 spec §11 packaging.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import json
import logging
from pathlib import Path

import click
from rich.console import Console

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# CONSTANTS                                                                    #
#                                                                              #
################################################################################

AUTH_FILE: Path = Path.home() / ".aam" / "auth.json"

################################################################################
#                                                                              #
# AUTH HELPERS                                                                 #
#                                                                              #
################################################################################


def _load_auth() -> dict[str, str]:
    """Load auth tokens from ``~/.aam/auth.json``.

    Returns:
        Dict mapping registry URLs to tokens.
    """
    if AUTH_FILE.is_file():
        return json.loads(AUTH_FILE.read_text(encoding="utf-8"))
    return {}


def _save_auth(auth_data: dict[str, str]) -> None:
    """Save auth tokens to ``~/.aam/auth.json``.

    Args:
        auth_data: Dict mapping registry URLs to tokens.
    """
    AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    AUTH_FILE.write_text(json.dumps(auth_data, indent=2), encoding="utf-8")
    AUTH_FILE.chmod(0o600)
    logger.info(f"Auth data saved to {AUTH_FILE}")


def get_token(registry_url: str) -> str | None:
    """Get the auth token for a registry URL.

    Args:
        registry_url: Registry base URL.

    Returns:
        Token string or None if not authenticated.
    """
    auth = _load_auth()
    return auth.get(registry_url.rstrip("/"))


################################################################################
#                                                                              #
# COMMANDS                                                                     #
#                                                                              #
################################################################################


@click.command()
@click.option("--registry", default="https://registry.aam.dev", help="Registry URL")
@click.option("--token", prompt="Auth token", hide_input=True, help="Authentication token")
@click.pass_context
def login(ctx: click.Context, registry: str, token: str) -> None:
    """Authenticate with a package registry.

    Examples::

        aam login --registry https://registry.aam.dev
        aam login --token mytoken123
    """
    console: Console = ctx.obj["console"]
    registry_url = registry.rstrip("/")

    auth = _load_auth()
    auth[registry_url] = token
    _save_auth(auth)

    console.print(f"[green]✓[/green] Logged in to {registry_url}")


@click.command()
@click.option("--registry", default="https://registry.aam.dev", help="Registry URL")
@click.pass_context
def logout(ctx: click.Context, registry: str) -> None:
    """Remove authentication for a registry.

    Examples::

        aam logout
        aam logout --registry https://custom-registry.example.com
    """
    console: Console = ctx.obj["console"]
    registry_url = registry.rstrip("/")

    auth = _load_auth()
    if registry_url in auth:
        del auth[registry_url]
        _save_auth(auth)
        console.print(f"[green]✓[/green] Logged out from {registry_url}")
    else:
        console.print(f"[yellow]Not logged in to {registry_url}[/yellow]")


@click.command()
@click.option("--registry", default="https://registry.aam.dev", help="Registry URL")
@click.pass_context
def whoami(ctx: click.Context, registry: str) -> None:
    """Show current authentication status.

    Examples::

        aam whoami
        aam whoami --registry https://custom-registry.example.com
    """
    console: Console = ctx.obj["console"]
    registry_url = registry.rstrip("/")

    token = get_token(registry_url)
    if token:
        masked = token[:4] + "..." + token[-4:] if len(token) > 8 else "****"
        console.print(f"Logged in to [bold]{registry_url}[/bold] (token: {masked})")
    else:
        console.print(f"Not logged in to {registry_url}")
