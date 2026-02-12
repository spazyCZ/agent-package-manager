"""Outdated command for AAM CLI.

Compares installed source packages against their source HEAD commits
and reports which packages have updates available.

Reference: spec 004 US4; contracts/cli-commands.md.
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
from rich.table import Table

from aam_cli.core.config import load_config
from aam_cli.core.workspace import read_lock_file
from aam_cli.services.upgrade_service import OutdatedPackage, OutdatedResult
from aam_cli.utils.paths import resolve_project_dir

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
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.option(
    "--global", "-g", "is_global", is_flag=True,
    help="Check global ~/.aam/ packages for updates",
)
@click.pass_context
def outdated(ctx: click.Context, output_json: bool, is_global: bool) -> None:
    """Check for outdated source-installed packages.

    Compares installed package commit SHAs against the source HEAD.
    Packages not installed from sources are shown as "(no source)".

    Use ``-g`` / ``--global`` to check packages in the user-wide
    ``~/.aam/`` directory instead of the project-local ``.aam/`` workspace.

    Examples::

        aam outdated
        aam outdated --json
        aam outdated -g
    """
    console: Console = ctx.obj["console"]
    project_dir = resolve_project_dir(is_global)

    # -----
    # Visual indicator for global mode
    # -----
    if is_global:
        console.print("[dim]Operating in global mode (~/.aam/)[/dim]\n")

    logger.info("Checking for outdated packages")

    # -----
    # Step 1: Run outdated check
    # -----
    config = load_config(project_dir)
    lock = read_lock_file(project_dir)

    result = check_outdated(lock, config)

    # -----
    # Step 2: JSON output
    # -----
    if output_json:
        data = {
            "outdated": [
                {
                    "name": o.name,
                    "current_commit": o.current_commit,
                    "latest_commit": o.latest_commit,
                    "source_name": o.source_name,
                    "has_local_modifications": o.has_local_modifications,
                }
                for o in result.outdated
            ],
            "up_to_date": result.up_to_date,
            "no_source": result.no_source,
            "stale_sources": result.stale_sources,
        }
        click.echo(json.dumps(data, indent=2))
        return

    # -----
    # Step 3: Rich table output
    # -----
    if not lock.packages:
        console.print("No packages installed.")
        return

    if result.stale_sources:
        for src in result.stale_sources:
            console.print(
                f"[yellow]⚠[/yellow] Source '{src}' not updated in 7+ days. "
                f"Run 'aam source update {src}'."
            )
        console.print()

    if not result.outdated:
        console.print("[green]✓[/green] All packages are up to date.")
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("Package", style="cyan")
    table.add_column("Current")
    table.add_column("Latest")
    table.add_column("Source")
    table.add_column("Status")

    for o in result.outdated:
        status = "[yellow]outdated[/yellow]"
        if o.has_local_modifications:
            status = "[red]outdated (modified)[/red]"

        table.add_row(
            o.name,
            o.current_commit,
            o.latest_commit,
            o.source_name,
            status,
        )

    for name in result.up_to_date:
        table.add_row(name, "", "", "", "[green]up to date[/green]")

    for name in result.no_source:
        table.add_row(name, "", "", "(no source)", "[dim]registry[/dim]")

    console.print()
    console.print(table)
    console.print()
    console.print(
        f"  {result.total_outdated} outdated, "
        f"{len(result.up_to_date)} up to date, "
        f"{len(result.no_source)} from registry"
    )
    console.print()


################################################################################
#                                                                              #
# OUTDATED CHECK LOGIC                                                         #
#                                                                              #
################################################################################


def check_outdated(
    lock: "LockFile",  # noqa: F821
    config: "AamConfig",  # noqa: F821
) -> OutdatedResult:
    """Compare installed source packages against source HEAD commits.

    Groups packages by source for efficient cache reads.

    Args:
        lock: Parsed lock file.
        config: AAM configuration.

    Returns:
        :class:`OutdatedResult` with categorized packages.
    """
    from datetime import UTC, datetime

    from aam_cli.services.git_service import get_cache_dir, get_head_sha, validate_cache
    from aam_cli.utils.git_url import parse

    logger.info(f"Checking outdated: packages={len(lock.packages)}")

    result = OutdatedResult()

    # -----
    # Build source HEAD SHA cache (one read per source)
    # -----
    source_head_cache: dict[str, str] = {}
    stale_threshold_days = 7

    for source_entry in config.sources:
        try:
            parsed = parse(source_entry.url)
            cache_dir = get_cache_dir(parsed.host, parsed.owner, parsed.repo)

            if validate_cache(cache_dir):
                source_head_cache[source_entry.name] = get_head_sha(cache_dir)

            # -----
            # Check for stale sources
            # -----
            if source_entry.last_fetched:
                fetched_dt = datetime.fromisoformat(source_entry.last_fetched)
                now = datetime.now(UTC)
                if (now - fetched_dt).days > stale_threshold_days:
                    result.stale_sources.append(source_entry.name)

        except (ValueError, OSError) as e:
            logger.warning(
                f"Cannot read HEAD for source '{source_entry.name}': {e}"
            )

    # -----
    # Compare each installed package
    # -----
    for pkg_name, locked in lock.packages.items():
        if not locked.source_name or not locked.source_commit:
            result.no_source.append(pkg_name)
            continue

        head_sha = source_head_cache.get(locked.source_name)

        if not head_sha:
            # Source cache missing — can't determine status
            result.no_source.append(pkg_name)
            continue

        if locked.source_commit == head_sha:
            result.up_to_date.append(pkg_name)
        else:
            # -----
            # Check for local modifications
            # -----
            has_mods = False
            try:
                from aam_cli.services.checksum_service import check_modifications

                mod_result = check_modifications(pkg_name)
                has_mods = mod_result.get("has_modifications", False)
            except Exception:
                pass

            result.outdated.append(
                OutdatedPackage(
                    name=pkg_name,
                    current_commit=locked.source_commit[:7],
                    latest_commit=head_sha[:7],
                    source_name=locked.source_name,
                    has_local_modifications=has_mods,
                )
            )

    result.total_outdated = len(result.outdated)

    logger.info(
        f"Outdated check complete: outdated={result.total_outdated}, "
        f"up_to_date={len(result.up_to_date)}, no_source={len(result.no_source)}"
    )

    return result
