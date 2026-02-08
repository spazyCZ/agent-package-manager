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
    # Limit results
    # -----
    results = all_results[:limit]

    # -----
    # Output
    # -----
    if output_json:
        console.print(json.dumps(results, indent=2))
        return

    if not results:
        console.print(f'No packages found matching "{query}".')
        return

    console.print(f'Search results for "{query}" ({len(results)} packages):\n')

    for result in results:
        types_str = ", ".join(result["artifact_types"]) if result["artifact_types"] else ""
        console.print(f"  [cyan]{result['name']}[/cyan]  {result['version']}")
        console.print(f"    {result['description']}")
        if types_str:
            console.print(f"    [{types_str}]")
        console.print()
