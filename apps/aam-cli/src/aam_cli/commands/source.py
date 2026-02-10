"""CLI commands for managing remote git artifact sources.

Provides the ``aam source`` command group with subcommands:
  - ``add``: Register a new remote git source
  - ``scan``: Scan a source for artifacts
  - ``update``: Fetch upstream changes
  - ``list``: Show all configured sources
  - ``remove``: Remove a configured source
  - ``candidates``: List unpackaged artifact candidates

Reference: contracts/cli-commands.md
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import json
import logging

import click
from rich.console import Console
from rich.table import Table

from aam_cli.services.source_service import (
    add_source,
    list_candidates,
    list_sources,
    remove_source,
    scan_source,
    update_source,
)

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# COMMAND GROUP                                                                 #
#                                                                              #
################################################################################


@click.group()
@click.pass_context
def source(ctx: click.Context) -> None:
    """Manage remote git artifact sources.

    Add, scan, update, list, and remove remote git repositories
    as artifact sources for AAM.
    """
    # -----
    # Ensure console is available in subcommands via ctx
    # -----
    ctx.ensure_object(dict)
    if "console" not in ctx.obj:
        ctx.obj["console"] = Console()
    if "err_console" not in ctx.obj:
        ctx.obj["err_console"] = Console(stderr=True)


################################################################################
#                                                                              #
# ADD                                                                          #
#                                                                              #
################################################################################


@source.command()
@click.argument("source_url")
@click.option("--ref", default=None, help="Git reference (branch, tag, or commit SHA)")
@click.option("--path", "scan_path", default=None, help="Subdirectory to scan within the repo")
@click.option("--name", default=None, help="Custom display name for the source")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def add(
    ctx: click.Context,
    source_url: str,
    ref: str | None,
    scan_path: str | None,
    name: str | None,
    output_json: bool,
) -> None:
    """Add a remote git repository as an artifact source.

    SOURCE_URL can be a GitHub shorthand (owner/repo), HTTPS URL,
    SSH URL (git@...), git+https:// URL, or a full GitHub tree URL
    with embedded branch and path.

    Examples:

      aam source add openai/skills

      aam source add https://github.com/openai/skills/tree/main/skills/.curated

      aam source add openai/skills --path skills/.curated --ref main

      aam source add git@github.com:openai/skills.git --name my-skills
    """
    console: Console = ctx.obj["console"]
    err_console: Console = ctx.obj["err_console"]
    logger.info(f"CLI source add: url='{source_url}'")

    try:
        result = add_source(
            source_str=source_url,
            ref=ref,
            path=scan_path,
            name=name,
        )
    except ValueError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        ctx.exit(1)
        return
    except Exception as e:
        err_console.print(f"[red]Error:[/red] Failed to add source: {e}")
        logger.error(f"Source add failed: {e}", exc_info=True)
        ctx.exit(1)
        return

    if output_json:
        click.echo(json.dumps(result, indent=2))
        return

    # -----
    # Rich output
    # -----
    console.print()
    console.print(f"[green]✓[/green] Source '[bold]{result['name']}[/bold]' added successfully")
    console.print()
    console.print(f"  Repository:  {result['url']}")
    console.print(f"  Ref:         {result['ref']}")
    if result['path']:
        console.print(f"  Path:        {result['path']}")
    console.print(f"  Commit:      {result['commit'][:12]}")
    console.print()

    by_type = result['artifacts_by_type']
    console.print(f"  Artifacts found: [bold]{result['artifact_count']}[/bold]")
    if by_type['skills']:
        console.print(f"    Skills:       {by_type['skills']}")
    if by_type['agents']:
        console.print(f"    Agents:       {by_type['agents']}")
    if by_type['prompts']:
        console.print(f"    Prompts:      {by_type['prompts']}")
    if by_type['instructions']:
        console.print(f"    Instructions: {by_type['instructions']}")
    console.print()


################################################################################
#                                                                              #
# SCAN                                                                         #
#                                                                              #
################################################################################


@source.command()
@click.argument("name")
@click.option("--type", "type_filter", multiple=True, help="Filter by artifact type")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def scan(
    ctx: click.Context,
    name: str,
    type_filter: tuple[str, ...],
    output_json: bool,
) -> None:
    """Scan a registered source for artifacts.

    NAME is the display name of the source (as shown by 'aam source list').

    Examples:

      aam source scan openai/skills

      aam source scan openai/skills --type skill --type agent
    """
    console: Console = ctx.obj["console"]
    err_console: Console = ctx.obj["err_console"]
    logger.info(f"CLI source scan: name='{name}'")

    try:
        result = scan_source(name)
    except ValueError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        ctx.exit(1)
        return

    # -----
    # Apply type filter if specified
    # -----
    artifacts = result["artifacts"]
    if type_filter:
        artifacts = [a for a in artifacts if a["type"] in type_filter]

    if output_json:
        output = {**result, "artifacts": artifacts}
        click.echo(json.dumps(output, indent=2))
        return

    # -----
    # Rich output
    # -----
    console.print()
    console.print(
        f"[bold]{result['source_name']}[/bold] — "
        f"Commit {result['commit'][:12]}"
    )
    if result['scan_path']:
        console.print(f"  Scan path: {result['scan_path']}")
    console.print()

    if not artifacts:
        console.print("  No artifacts found.")
        return

    # -----
    # Build table of artifacts
    # -----
    table = Table(show_header=True, header_style="bold")
    table.add_column("Name", style="cyan")
    table.add_column("Type")
    table.add_column("Path")
    table.add_column("Description", max_width=50)

    for artifact in artifacts:
        table.add_row(
            artifact["name"],
            artifact["type"],
            artifact["path"],
            artifact.get("description", "") or "",
        )

    console.print(table)
    console.print()
    console.print(
        f"  Total: [bold]{len(artifacts)}[/bold] artifacts"
    )
    console.print()


################################################################################
#                                                                              #
# UPDATE                                                                       #
#                                                                              #
################################################################################


@source.command()
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
    """Fetch upstream changes for a source.

    NAME is the source to update. Use --all to update all sources.

    Examples:

      aam source update openai/skills

      aam source update --all

      aam source update openai/skills --dry-run
    """
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
    except ValueError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        ctx.exit(1)
        return
    except Exception as e:
        err_console.print(f"[red]Error:[/red] Update failed: {e}")
        logger.error(f"Source update failed: {e}", exc_info=True)
        ctx.exit(1)
        return

    if output_json:
        click.echo(json.dumps(result, indent=2))
        return

    # -----
    # Rich output
    # -----
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
    console.print(
        f"  Sources updated: {result['sources_updated']}"
    )
    console.print()


################################################################################
#                                                                              #
# LIST                                                                         #
#                                                                              #
################################################################################


@source.command(name="list")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def list_cmd(ctx: click.Context, output_json: bool) -> None:
    """List all configured remote sources.

    Examples:

      aam source list

      aam source list --json
    """
    console: Console = ctx.obj["console"]
    logger.info("CLI source list")

    result = list_sources()

    if output_json:
        click.echo(json.dumps(result, indent=2))
        return

    sources = result["sources"]

    if not sources:
        console.print()
        console.print("No sources configured. Use 'aam source add' to register one.")
        console.print()
        return

    # -----
    # Build Rich table
    # -----
    table = Table(show_header=True, header_style="bold")
    table.add_column("Name", style="cyan")
    table.add_column("URL")
    table.add_column("Ref")
    table.add_column("Path")
    table.add_column("Artifacts", justify="right")
    table.add_column("Last Fetched")

    for s in sources:
        name_display = s["name"]
        if s["default"]:
            name_display += " [dim](default)[/dim]"

        fetched = s.get("last_fetched", "")
        if fetched:
            # Show just the date portion
            fetched = fetched[:10]

        table.add_row(
            name_display,
            s["url"],
            s["ref"],
            s["path"] or "—",
            str(s.get("artifact_count", "—")),
            fetched or "—",
        )

    console.print()
    console.print(table)
    console.print()
    console.print(f"  Total: {result['count']} source(s)")
    console.print()


################################################################################
#                                                                              #
# REMOVE                                                                       #
#                                                                              #
################################################################################


@source.command()
@click.argument("name")
@click.option("--purge-cache", is_flag=True, help="Delete the cached clone directory")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def remove(ctx: click.Context, name: str, purge_cache: bool, output_json: bool) -> None:
    """Remove a configured source.

    NAME is the display name of the source to remove.

    Examples:

      aam source remove openai/skills

      aam source remove openai/skills --purge-cache
    """
    console: Console = ctx.obj["console"]
    err_console: Console = ctx.obj["err_console"]
    logger.info(f"CLI source remove: name='{name}'")

    try:
        result = remove_source(name, purge_cache=purge_cache)
    except ValueError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        ctx.exit(1)
        return

    if output_json:
        click.echo(json.dumps(result, indent=2))
        return

    console.print()
    console.print(
        f"[green]✓[/green] Source '[bold]{name}[/bold]' removed"
    )
    if result["cache_purged"]:
        console.print("  Cache directory purged")
    console.print()


################################################################################
#                                                                              #
# CANDIDATES                                                                   #
#                                                                              #
################################################################################


@source.command()
@click.option("--source", "source_filter", default=None, help="Filter by source name")
@click.option("--type", "type_filter", multiple=True, help="Filter by artifact type")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def candidates(
    ctx: click.Context,
    source_filter: str | None,
    type_filter: tuple[str, ...],
    output_json: bool,
) -> None:
    """List unpackaged artifact candidates across sources.

    Shows artifacts discovered in registered sources that have not
    yet been packaged.

    Examples:

      aam source candidates

      aam source candidates --source openai/skills --type skill
    """
    console: Console = ctx.obj["console"]
    err_console: Console = ctx.obj["err_console"]
    logger.info("CLI source candidates")

    type_list = list(type_filter) if type_filter else None

    try:
        result = list_candidates(
            source_filter=source_filter,
            type_filter=type_list,
        )
    except ValueError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        ctx.exit(1)
        return

    if output_json:
        click.echo(json.dumps(result, indent=2))
        return

    candidates_list = result["candidates"]

    if not candidates_list:
        console.print()
        console.print("No unpackaged candidates found.")
        console.print()
        return

    # -----
    # Group by source
    # -----
    by_source: dict[str, list[dict]] = {}
    for c in candidates_list:
        src = c.get("source_name", "unknown")
        by_source.setdefault(src, []).append(c)

    console.print()
    for src_name, arts in by_source.items():
        console.print(f"[bold]{src_name}[/bold]")

        table = Table(show_header=True, header_style="bold")
        table.add_column("Name", style="cyan")
        table.add_column("Type")
        table.add_column("Path")

        for a in arts:
            table.add_row(a["name"], a["type"], a["path"])

        console.print(table)
        console.print()

    console.print(
        f"  Total candidates: [bold]{result['total_count']}[/bold]"
    )
    console.print()
