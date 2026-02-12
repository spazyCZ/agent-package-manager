"""Search command for AAM CLI.

Thin presentation layer that delegates all search logic to
:func:`aam_cli.services.search_service.search_packages` and displays
results as a Rich Table or JSON envelope.

Contracts reference: specs/005-improve-search-ux/contracts/search-service.md
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

from aam_cli.core.config import load_config
from aam_cli.core.workspace import read_lock_file
from aam_cli.services.search_service import search_packages
from aam_cli.utils.paths import resolve_project_dir
from aam_cli.utils.text_match import find_similar_names

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# HELPERS                                                                      #
#                                                                              #
################################################################################


def _collect_installed_names() -> set[str]:
    """Return the set of package names installed in local and global workspaces.

    Reads both the project-local lock file (``.aam/aam-lock.yaml``) and the
    global lock file (``~/.aam/aam-lock.yaml``).  If either file is missing or
    empty the corresponding set is simply empty — no error is raised.

    Returns:
        A set of installed package names (union of local and global).
    """
    local_lock = read_lock_file(resolve_project_dir(is_global=False))
    global_lock = read_lock_file(resolve_project_dir(is_global=True))

    installed = set(local_lock.packages.keys()) | set(
        global_lock.packages.keys()
    )

    logger.debug(
        f"Collected installed names: "
        f"local={len(local_lock.packages)}, "
        f"global={len(global_lock.packages)}, "
        f"union={len(installed)}"
    )

    return installed


################################################################################
#                                                                              #
# COMMAND                                                                      #
#                                                                              #
################################################################################


@click.command()
@click.argument("query", default="")
@click.option("--limit", "-l", default=255, help="Maximum number of results (1-255)")
@click.option(
    "--type",
    "-t",
    "package_types",
    multiple=True,
    help="Filter by artifact type (repeatable: --type skill --type agent)",
)
@click.option(
    "--source",
    "-s",
    "source_filter",
    default=None,
    help="Limit to a specific git source name",
)
@click.option(
    "--registry",
    "-r",
    "registry_filter",
    default=None,
    help="Limit to a specific registry name",
)
@click.option(
    "--sort",
    "sort_by",
    type=click.Choice(["relevance", "name", "recent"], case_sensitive=False),
    default="relevance",
    help="Sort order (default: relevance)",
)
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def search(
    ctx: click.Context,
    query: str,
    limit: int,
    package_types: tuple[str, ...],
    source_filter: str | None,
    registry_filter: str | None,
    sort_by: str,
    output_json: bool,
) -> None:
    """Search configured registries and sources for packages.

    Uses relevance-ranked scoring with tiered matching on name,
    keywords, and description.  Results are displayed in a Rich Table
    sorted by relevance score (or the chosen sort order).

    Examples::

        aam search chatbot
        aam search "code review" --type skill
        aam search audit --limit 5 --sort name
        aam search doc --source google-gemini
        aam search data --type skill --type agent
        aam search chatbot --json
    """
    console: Console = ctx.obj["console"]

    logger.info(
        f"Search command: query='{query}', limit={limit}, "
        f"types={package_types}, source={source_filter}, "
        f"registry={registry_filter}, sort={sort_by}"
    )

    config = load_config()

    # ------------------------------------------------------------------
    # Call the unified search service
    # ------------------------------------------------------------------
    types_list = list(package_types) if package_types else None

    try:
        response = search_packages(
            query=query,
            config=config,
            limit=limit,
            package_types=types_list,
            source_filter=source_filter,
            registry_filter=registry_filter,
            sort_by=sort_by,
        )
    except ValueError as exc:
        logger.error(f"Search failed: {exc}")
        console.print(f"[red]Error:[/red] {exc}")
        ctx.exit(1)
        return

    # ------------------------------------------------------------------
    # Mark installed packages
    # ------------------------------------------------------------------
    # Cross-reference results against both local and global lock files
    # so the user can see at a glance which packages are already present.
    # ------------------------------------------------------------------
    installed_names = _collect_installed_names()

    for result in response.results:
        if result.name in installed_names:
            result.installed = True

    logger.debug(
        f"Installed check: {len(installed_names)} installed packages, "
        f"{sum(1 for r in response.results if r.installed)} matches"
    )

    # ------------------------------------------------------------------
    # Display warnings
    # ------------------------------------------------------------------
    for warning in response.warnings:
        console.print(f"[yellow]Warning:[/yellow] {warning}")

    # ------------------------------------------------------------------
    # JSON output path
    # ------------------------------------------------------------------
    if output_json:
        json_output = response.model_dump(mode="json")
        # Remove all_names from JSON output (internal use only)
        json_output.pop("all_names", None)
        console.print(json.dumps(json_output, indent=2))
        return

    # ------------------------------------------------------------------
    # Empty results — "Did you mean?" suggestions
    # ------------------------------------------------------------------
    if not response.results:
        if query:
            console.print(f'No packages found matching "{query}".')
        else:
            console.print("No packages found.")

        # -----
        # Show suggestions if available
        # -----
        if response.all_names and query:
            suggestions = find_similar_names(query, response.all_names)
            if suggestions:
                suggestion_str = ", ".join(suggestions)
                console.print(
                    f"\n[dim]Did you mean:[/dim] {suggestion_str}"
                )

        return

    # ------------------------------------------------------------------
    # Build Rich Table
    # ------------------------------------------------------------------
    if response.total_count > len(response.results):
        title = (
            f'Search results for "{query}" '
            f"(showing {len(response.results)} of {response.total_count})"
        )
    else:
        title = (
            f'Search results for "{query}" '
            f"({response.total_count} matches)"
            if query
            else f"All packages ({response.total_count} matches)"
        )

    table = Table(title=title, show_lines=False, pad_edge=False)
    table.add_column("Name", style="cyan bold", no_wrap=True)
    table.add_column("Version", style="dim", no_wrap=True)
    table.add_column("Type", no_wrap=True)
    table.add_column("Source", style="magenta", no_wrap=True)
    table.add_column("Installed", justify="center", no_wrap=True)
    table.add_column("Description", style="dim", max_width=255)

    for result in response.results:
        types_str = ", ".join(result.artifact_types)
        installed_marker = "[green]✓[/green]" if result.installed else ""
        desc = (result.description or "")[:255]
        table.add_row(
            result.name,
            result.version,
            types_str,
            result.origin,
            installed_marker,
            desc,
        )

    console.print(table)
