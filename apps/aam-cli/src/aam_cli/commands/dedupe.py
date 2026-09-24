"""``aam dedupe`` — Detect and remove duplicate package installations.

Scans ``.agent-packages/`` for packages that appear in multiple
sub-namespace directories (typically from pre-update or migrated installs)
and hoists compatible versions to the root level.
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

from aam_cli.services.dependency_tree_service import dedupe_deps

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
    help="Show what would be deduped without making changes.",
)
@click.option(
    "--project",
    default=None,
    type=click.Path(exists=True),
    help="Project directory (defaults to current directory).",
)
@click.pass_context
def dedupe(
    ctx: click.Context,
    dry_run: bool,
    project: str | None,
) -> None:
    """Detect and remove duplicate package installations.

    Scans ``.agent-packages/`` for packages installed in multiple
    sub-namespace directories and removes duplicates, keeping the
    root-level copy.

    With ``--dry-run``, only shows what would be changed.

    Examples::

        aam dedupe --dry-run
        aam dedupe
        aam dedupe --project ./my-project
    """
    console: Console = ctx.obj["console"]
    project_dir = Path(project).resolve() if project else Path.cwd()

    logger.info(f"Running dedupe: dry_run={dry_run}")

    result = dedupe_deps(project_dir=project_dir, dry_run=dry_run)

    # -----
    # Display results
    # -----
    duplicates: list[str] = result.get("would_dedupe") or result.get("deduped", [])
    packages_changed = result.get("packages_changed", 0)

    if not duplicates:
        console.print(
            "[green]✓[/green] No duplicate packages found. "
            "Package layout is already flat."
        )
        return

    if dry_run:
        console.print(
            f"[yellow]Would dedupe {len(duplicates)} package(s):[/yellow]"
        )
        for pkg in duplicates:
            console.print(f"  • {pkg}")
        console.print(
            "\n[dim]Run 'aam dedupe' (without --dry-run) to apply.[/dim]"
        )
    else:
        console.print(
            f"[green]✓[/green] Deduped {packages_changed} package(s):"
        )
        for pkg in duplicates:
            console.print(f"  • {pkg}")
