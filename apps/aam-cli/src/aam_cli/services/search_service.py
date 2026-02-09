"""Search service for AAM.

Provides package search across configured registries.
Returns structured data for use by both CLI and MCP.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from typing import Any

from aam_cli.core.config import AamConfig
from aam_cli.registry.factory import create_registry

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

MIN_SEARCH_LIMIT = 1
MAX_SEARCH_LIMIT = 50
DEFAULT_SEARCH_LIMIT = 10

################################################################################
#                                                                              #
# SERVICE FUNCTIONS                                                            #
#                                                                              #
################################################################################


def search_packages(
    query: str,
    config: AamConfig,
    limit: int = DEFAULT_SEARCH_LIMIT,
    package_type: str | None = None,
) -> list[dict[str, Any]]:
    """Search configured registries for packages matching a query.

    Iterates over all registries in the config, aggregates results,
    and applies optional type filtering and limit capping.

    Args:
        query: Search query string (case-insensitive substring).
        config: AAM configuration with registry sources.
        limit: Maximum results to return (1-50).
        package_type: Optional artifact type filter (e.g. "skill", "agent").

    Returns:
        List of SearchResult dicts per data-model.md.

    Raises:
        ValueError: If limit is outside the allowed range [1, 50].
    """
    logger.info(
        f"Searching packages: query='{query}', limit={limit}, "
        f"package_type={package_type}"
    )

    # -----
    # Validate limit range
    # -----
    if limit < MIN_SEARCH_LIMIT or limit > MAX_SEARCH_LIMIT:
        raise ValueError(
            f"[AAM_INVALID_ARGUMENT] limit must be between "
            f"{MIN_SEARCH_LIMIT} and {MAX_SEARCH_LIMIT}, got {limit}"
        )

    # -----
    # Return empty list if no registries configured
    # -----
    if not config.registries:
        logger.warning("No registries configured for search")
        return []

    # -----
    # Search all configured registries
    # -----
    all_results: list[dict[str, Any]] = []

    for reg_source in config.registries:
        logger.debug(f"Searching registry: name='{reg_source.name}'")
        reg = create_registry(reg_source)
        entries = reg.search(query)

        for entry in entries:
            # -----
            # Apply artifact type filter if specified
            # -----
            if package_type and package_type not in entry.artifact_types:
                continue

            all_results.append(
                {
                    "name": entry.name,
                    "version": entry.latest,
                    "description": entry.description,
                    "author": getattr(entry, "author", None),
                    "artifact_types": entry.artifact_types,
                    "registry": reg_source.name,
                }
            )

    # -----
    # Apply limit
    # -----
    results = all_results[:limit]

    logger.info(
        f"Search complete: query='{query}', "
        f"total_found={len(all_results)}, returned={len(results)}"
    )

    return results
