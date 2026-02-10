"""Search command for AAM CLI.

Searches configured registries for packages matching a query.
Uses case-insensitive substring matching per R-004.
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

from aam_cli.core.config import load_config
from aam_cli.registry.factory import create_registry

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
@click.argument("query")
@click.option("--limit", "-l", default=10, help="Maximum number of results")
@click.option(
    "--type",
    "-t",
    "package_type",
    help="Filter by artifact type",
)
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def search(
    ctx: click.Context,
    query: str,
    limit: int,
    package_type: str | None,
    output_json: bool,
) -> None:
    """Search configured registries for packages.

    Uses case-insensitive substring matching on name, description,
    and keywords.

    Examples::

        aam search chatbot
        aam search "code review" --type skill
        aam search audit --limit 5
        aam search audit --json
    """
    console: Console = ctx.obj["console"]

    logger.info(f"Searching packages: query='{query}', limit={limit}")

    config = load_config()

    if not config.registries:
        console.print(
            "[red]Error:[/red] No registries configured. Run 'aam registry init' to create one."
        )
        ctx.exit(1)
        return

    # -----
    # Search all configured registries
    # -----
    all_results: list[dict] = []

    for reg_source in config.registries:
        reg = create_registry(reg_source)
        entries = reg.search(query)

        for entry in entries:
            # Filter by artifact type if specified
            if package_type and package_type not in entry.artifact_types:
                continue

            all_results.append(
                {
                    "name": entry.name,
                    "version": entry.latest,
                    "description": entry.description,
                    "keywords": entry.keywords,
                    "artifact_types": entry.artifact_types,
                    "registry": reg_source.name,
                }
            )

    # -----
    # Step 2: Search source artifact index (spec 004)
    # -----
    source_results: list[dict] = []
    try:
        from aam_cli.services.source_service import build_source_index

        index = build_source_index(config)
        query_lower = query.lower()

        for vp in index.by_qualified_name.values():
            # -----
            # Match by name or description (case-insensitive)
            # -----
            name_match = query_lower in vp.name.lower()
            desc_match = vp.description and query_lower in vp.description.lower()

            if name_match or desc_match:
                if package_type and vp.type != package_type:
                    continue

                source_results.append(
                    {
                        "name": vp.name,
                        "version": f"source@{vp.commit_sha[:7]}",
                        "description": vp.description or "",
                        "keywords": [],
                        "artifact_types": [vp.type],
                        "registry": f"[source] {vp.source_name}",
                    }
                )
    except Exception as e:
        logger.debug(f"Source search failed (non-fatal): {e}")

    # -----
    # Combine and limit results
    # -----
    combined = all_results + source_results
    results = combined[:limit]

    # -----
    # Output
    # -----
    if output_json:
        console.print(json.dumps(results, indent=2))
        return

    if not results:
        console.print(f'No packages found matching "{query}".')
        return

    console.print(f'Search results for "{query}" ({len(results)} matches):\n')

    for result in results:
        types_str = ", ".join(result["artifact_types"]) if result["artifact_types"] else ""
        registry_label = result.get("registry", "")

        # -----
        # Tag source results with [source] indicator
        # -----
        source_tag = ""
        if registry_label.startswith("[source]"):
            source_tag = " [dim][source][/dim]"

        console.print(
            f"  [cyan]{result['name']}[/cyan]  "
            f"{result['version']}{source_tag}"
        )
        console.print(f"    {result['description']}")
        if types_str:
            console.print(f"    [{types_str}]")
        console.print()
