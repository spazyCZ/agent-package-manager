"""Cache management commands for AAM CLI.

Provides ``aam cache clean`` and ``aam cache ls`` for managing
the package download cache.

Reference: UAAPS v0.5.0 spec §11 packaging.
"""

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
# COMMANDS                                                                     #
#                                                                              #
################################################################################


@click.group()
def cache() -> None:
    """Manage the package download cache."""


@cache.command("clean")
@click.argument("package_spec", required=False)
@click.pass_context
def cache_clean(ctx: click.Context, package_spec: str | None) -> None:
    """Remove cached package archives.

    Pass ``pkg@version`` to remove a specific entry, or omit to clean all.

    Examples::

        aam cache clean
        aam cache clean @scope/my-pkg@1.0.0
    """
    console: Console = ctx.obj["console"]

    if package_spec and "@" in package_spec:
        parts = package_spec.rsplit("@", 1)
        if len(parts) == 2:
            pkg_name, version = parts[0], parts[1]
            removed = cache_service.clean(pkg_name, version)
            console.print(f"Removed {removed} cached entries for {package_spec}")
            return

    removed = cache_service.clean()
    console.print(f"[green]✓[/green] Cleaned {removed} cached packages")


@cache.command("ls")
@click.pass_context
def cache_ls(ctx: click.Context) -> None:
    """List cached package archives.

    Examples::

        aam cache ls
    """
    console: Console = ctx.obj["console"]

    entries = cache_service.list_cached()

    if not entries:
        console.print("Cache is empty.")
        return

    console.print(f"[bold]Cached packages ({len(entries)}):[/bold]\n")
    total_size = 0
    for entry in entries:
        size_kb = entry["size_bytes"] / 1024
        total_size += entry["size_bytes"]
        console.print(f"  {entry['name']}  [dim]{size_kb:.1f} KB[/dim]")

    console.print(f"\n  Total: {total_size / 1024:.1f} KB")
