"""Update one or more registered artifact sources."""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import json
import logging

import click
from rich.console import Console

from aam_cli.services.source_service import update_source

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
@click.argument("name", required=False)
@click.option("--all", "update_all", is_flag=True, help="Update all sources")
@click.option("--dry-run", is_flag=True, help="Preview changes without modifying cache")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def update(
    ctx: click.Context,
    name: str | None,
    update_all: bool,
    dry_run: bool,
    output_json: bool,
) -> None:
    """Fetch upstream changes for a source."""
    console: Console = ctx.obj["console"]
    err_console: Console = ctx.obj["err_console"]
    logger.info(f"CLI source update: name='{name}', all={update_all}")

    if not name and not update_all:
        err_console.print(
            "[red]Error:[/red] Specify a source name or use --all"
        )
        ctx.exit(1)
        return

    try:
        result = update_source(
            source_name=name,
            update_all=update_all,
            dry_run=dry_run,
        )
    except ValueError as error:
        err_console.print(f"[red]Error:[/red] {error}")
        ctx.exit(1)
        return
    except Exception as error:
        err_console.print(f"[red]Error:[/red] Update failed: {error}")
        logger.error(f"Source update failed: {error}", exc_info=True)
        ctx.exit(1)
        return

    if output_json:
        click.echo(json.dumps(result, indent=2))
        return

    console.print()
    if dry_run:
        console.print("[yellow]DRY RUN[/yellow] — No changes applied")
        console.print()

    for report in result["reports"]:
        source_name = report["source_name"]

        if report.get("fetch_failed"):
            console.print(
                f"[yellow]⚠[/yellow] '{source_name}' — "
                f"Network error, using cached data"
            )
            continue

        if not report["has_changes"]:
            console.print(
                f"[green]✓[/green] '{source_name}' — Already up to date"
            )
            continue

        console.print(
            f"[green]✓[/green] '{source_name}' — Updated "
            f"({report['old_commit'][:8]} → {report['new_commit'][:8]})"
        )

        new = report["new_artifacts"]
        modified = report["modified_artifacts"]
        removed = report["removed_artifacts"]

        if new:
            console.print(f"    [green]+{len(new)} new[/green]")
        if modified:
            console.print(f"    [yellow]~{len(modified)} modified[/yellow]")
        if removed:
            console.print(f"    [red]-{len(removed)} removed[/red]")

    console.print()
    console.print(f"  Sources updated: {result['sources_updated']}")

    materialization = result.get("materialization", {})
    if materialization:
        package_count = materialization.get("packages_created", 0)
        skipped = materialization.get("skipped_duplicates", 0)
        materialization_errors = materialization.get("errors", [])
        if package_count > 0:
            console.print(
                f"  [green]✓[/green] Materialized {package_count} "
                f"installable packages"
            )
        if skipped > 0:
            console.print(
                f"  [dim]ℹ[/dim] Skipped {skipped} cross-source "
                f"duplicates (first source wins)"
            )
        for error in materialization_errors:
            console.print(f"  [yellow]⚠[/yellow] {error}")

    console.print()
