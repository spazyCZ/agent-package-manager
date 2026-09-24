"""``aam prune`` — Remove unlisted package directories.

Compares ``.agent-packages/`` directory listing against the lock file
and removes any directories not tracked in ``package.agent.lock``.
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

from aam_cli.services.dependency_tree_service import prune_deps

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
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be removed without making changes.",
)
@click.option(
    "--project",
    default=None,
    type=click.Path(exists=True),
    help="Project directory (defaults to current directory).",
)
@click.pass_context
def prune(
    ctx: click.Context,
    dry_run: bool,
    project: str | None,
) -> None:
    """Remove package directories not tracked in the lock file.

    Compares ``.agent-packages/`` against ``package.agent.lock`` and
    removes any directories that are not locked. Useful for cleaning up
    after failed installs or manual modifications.

    With ``--dry-run``, only shows what would be removed.

    Examples::

        aam prune --dry-run
        aam prune
        aam prune --project ./my-project
    """
    console: Console = ctx.obj["console"]
    project_dir = Path(project).resolve() if project else Path.cwd()

    logger.info(f"Running prune: dry_run={dry_run}")

    try:
        result = prune_deps(project_dir=project_dir, dry_run=dry_run)
    except ValueError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        ctx.exit(1)
        return

    # -----
    # Display results
    # -----
    to_remove: list[str] = result.get("would_remove") or result.get("removed", [])
    packages_removed = result.get("packages_removed", 0)

    if not to_remove:
        console.print(
            "[green]✓[/green] No unlisted directories found. "
            "Package tree is clean."
        )
        return

    if dry_run:
        console.print(
            f"[yellow]Would remove {len(to_remove)} unlisted director(ies):[/yellow]"
        )
        for dir_name in to_remove:
            console.print(f"  • {dir_name}")
        console.print(
            "\n[dim]Run 'aam prune' (without --dry-run) to apply.[/dim]"
        )
    else:
        console.print(
            f"[green]✓[/green] Pruned {packages_removed} unlisted director(ies):"
        )
        for dir_name in to_remove:
            console.print(f"  • {dir_name}")
