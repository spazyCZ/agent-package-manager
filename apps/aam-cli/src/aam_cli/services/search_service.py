"""Search service for AAM.

Provides unified package search across configured registries and git
sources.  Returns structured ``SearchResponse`` data for use by both
the CLI command and the MCP tool.

Contracts reference: specs/005-improve-search-ux/contracts/search-service.md
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging

from pydantic import BaseModel, Field

from aam_cli.core.config import AamConfig
from aam_cli.registry.factory import create_registry
from aam_cli.services.source_service import build_source_index

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

# --- Limit validation ---
MIN_SEARCH_LIMIT: int = 1
MAX_SEARCH_LIMIT: int = 50
DEFAULT_SEARCH_LIMIT: int = 10

# --- Relevance scoring tiers (highest-tier-wins) ---
SCORE_EXACT_NAME: int = 100
SCORE_NAME_PREFIX: int = 80
SCORE_NAME_CONTAINS: int = 60
SCORE_KEYWORD_MATCH: int = 50
SCORE_DESCRIPTION_CONTAINS: int = 30

# --- Validation constants ---
VALID_ARTIFACT_TYPES: list[str] = ["skill", "agent", "prompt", "instruction"]
VALID_SORT_OPTIONS: list[str] = ["relevance", "name", "recent"]

################################################################################
#                                                                              #
# PYDANTIC MODELS                                                              #
#                                                                              #
################################################################################


class SearchResult(BaseModel):
    """A unified search result from a registry package or source artifact.

    Used by both CLI display and MCP tool response.

    Attributes:
        name: Package or artifact name.
        version: Version string or ``source@<sha>`` for source artifacts.
        description: Human-readable description (empty string if none).
        keywords: Package keywords (empty list for sources).
        artifact_types: Types such as ``skill``, ``agent``, ``prompt``,
            ``instruction``.
        origin: Origin label — registry name or ``[source] <qualified>``.
        origin_type: Discriminator: ``registry`` or ``source``.
        score: Relevance score 0–100.
        updated_at: ISO 8601 timestamp (empty string if unknown).
    """

    name: str
    version: str
    description: str = ""
    keywords: list[str] = Field(default_factory=list)
    artifact_types: list[str] = Field(default_factory=list)
    origin: str = ""
    origin_type: str = "registry"
    score: int = Field(default=0, ge=0, le=100)
    updated_at: str = ""


class SearchResponse(BaseModel):
    """Response envelope returned by :func:`search_packages`.

    Attributes:
        results: Scored, filtered, sorted, and limited results.
        total_count: Total matches before limiting (for "Showing X of Y").
        warnings: User-facing warning messages (empty list if none).
        all_names: Full name index, populated only when ``results`` is
            empty (for "Did you mean?" computation).
    """

    results: list[SearchResult] = Field(default_factory=list)
    total_count: int = 0
    warnings: list[str] = Field(default_factory=list)
    all_names: list[str] = Field(default_factory=list)


################################################################################
#                                                                              #
# SCORING                                                                      #
#                                                                              #
################################################################################


def compute_relevance_score(
    query_lower: str,
    name_lower: str,
    description_lower: str,
    keywords_lower: list[str],
) -> int:
    """Compute the relevance score for a candidate against a query.

    Implements a tiered highest-match-wins algorithm.  The candidate
    receives the score of its **highest** matching tier (a result that
    matches both name and description gets only the name score).

    Tiers (in evaluation order):
        1. Empty query (browse mode) → ``SCORE_EXACT_NAME`` (100)
        2. Exact name match          → ``SCORE_EXACT_NAME`` (100)
        3. Name starts with query    → ``SCORE_NAME_PREFIX`` (80)
        4. Name contains query       → ``SCORE_NAME_CONTAINS`` (60)
        5. Keyword exact match       → ``SCORE_KEYWORD_MATCH`` (50)
        6. Description contains      → ``SCORE_DESCRIPTION_CONTAINS`` (30)
        7. No match                  → 0

    Args:
        query_lower: Lowercased query string.
        name_lower: Lowercased package/artifact name.
        description_lower: Lowercased description.
        keywords_lower: Lowercased keywords list.

    Returns:
        Integer score between 0 and 100.
    """
    # -----
    # Tier 1: Browse mode — empty query matches everything at top score
    # -----
    if not query_lower:
        return SCORE_EXACT_NAME

    # -----
    # Tier 2: Exact name match
    # -----
    if query_lower == name_lower:
        return SCORE_EXACT_NAME

    # -----
    # Tier 3: Name starts with query
    # -----
    if name_lower.startswith(query_lower):
        return SCORE_NAME_PREFIX

    # -----
    # Tier 4: Name contains query
    # -----
    if query_lower in name_lower:
        return SCORE_NAME_CONTAINS

    # -----
    # Tier 5: Keyword exact match
    # -----
    if query_lower in keywords_lower:
        return SCORE_KEYWORD_MATCH

    # -----
    # Tier 6: Description contains query
    # -----
    if query_lower in description_lower:
        return SCORE_DESCRIPTION_CONTAINS

    # -----
    # No match
    # -----
    return 0


################################################################################
#                                                                              #
# SERVICE FUNCTIONS                                                            #
#                                                                              #
################################################################################


def search_packages(
    query: str,
    config: AamConfig,
    limit: int = DEFAULT_SEARCH_LIMIT,
    package_types: list[str] | None = None,
    source_filter: str | None = None,
    registry_filter: str | None = None,
    sort_by: str = "relevance",
) -> SearchResponse:
    """Search configured registries and sources for matching packages.

    Iterates over all configured registries and git sources, scores
    each candidate using :func:`compute_relevance_score`, applies
    optional filters, sorts, and returns a :class:`SearchResponse`.

    Args:
        query: Search query string (case-insensitive).  Empty string
            triggers browse mode (all packages, equal score).
        config: AAM configuration with registries and sources.
        limit: Maximum results to return (1–50).
        package_types: Optional artifact type filter (OR logic).
        source_filter: Limit to a specific git source name.
        registry_filter: Limit to a specific registry name.
        sort_by: Sort order — ``relevance``, ``name``, or ``recent``.

    Returns:
        :class:`SearchResponse` with scored, filtered, sorted results.

    Raises:
        ValueError: If *limit* is outside [1, 50], *sort_by* is invalid,
            or no registries and no sources are configured.
    """
    logger.info(
        f"Searching packages: query='{query}', limit={limit}, "
        f"package_types={package_types}, source_filter={source_filter}, "
        f"registry_filter={registry_filter}, sort_by={sort_by}"
    )

    warnings: list[str] = []
    all_results: list[SearchResult] = []
    all_names: list[str] = []

    # ------------------------------------------------------------------
    # Step 1: Validate limit
    # ------------------------------------------------------------------
    if limit < MIN_SEARCH_LIMIT or limit > MAX_SEARCH_LIMIT:
        raise ValueError(
            f"[AAM_INVALID_ARGUMENT] limit must be between "
            f"{MIN_SEARCH_LIMIT} and {MAX_SEARCH_LIMIT}, got {limit}"
        )

    # ------------------------------------------------------------------
    # Step 2: Validate sort_by
    # ------------------------------------------------------------------
    if sort_by not in VALID_SORT_OPTIONS:
        raise ValueError(
            f"[AAM_INVALID_ARGUMENT] sort_by must be one of "
            f"{VALID_SORT_OPTIONS}, got '{sort_by}'"
        )

    # ------------------------------------------------------------------
    # Step 3: Validate package_types — warn on unknown, keep valid
    # ------------------------------------------------------------------
    valid_types: list[str] | None = None
    if package_types is not None:
        valid_types = []
        for pt in package_types:
            if pt in VALID_ARTIFACT_TYPES:
                valid_types.append(pt)
            else:
                warnings.append(
                    f"Unknown artifact type '{pt}'. "
                    f"Valid types: {', '.join(VALID_ARTIFACT_TYPES)}"
                )
        if not valid_types:
            valid_types = None  # all were invalid → no filtering

    # ------------------------------------------------------------------
    # Step 4: Validate source_filter / registry_filter
    # ------------------------------------------------------------------
    source_names = [s.name for s in config.sources]
    registry_names = [r.name for r in config.registries]

    if source_filter and source_filter not in source_names:
        warnings.append(
            f"Source '{source_filter}' not found. "
            f"Available: {', '.join(source_names) if source_names else '(none)'}"
        )

    if registry_filter and registry_filter not in registry_names:
        warnings.append(
            f"Registry '{registry_filter}' not found. "
            f"Available: {', '.join(registry_names) if registry_names else '(none)'}"
        )

    # ------------------------------------------------------------------
    # Step 5: Error when no registries AND no sources
    # ------------------------------------------------------------------
    if not config.registries and not config.sources:
        raise ValueError(
            "[AAM_NO_SOURCES] No registries or sources configured. "
            "Run 'aam registry init' or 'aam source add' to get started."
        )

    query_lower = query.lower()

    # ------------------------------------------------------------------
    # Step 6: Search registries (skip when source_filter is set)
    # ------------------------------------------------------------------
    if not source_filter:
        for reg_source in config.registries:
            # -----
            # If a registry_filter is set, skip non-matching registries
            # -----
            if registry_filter and reg_source.name != registry_filter:
                continue

            try:
                logger.debug(f"Searching registry: name='{reg_source.name}'")
                reg = create_registry(reg_source)
                entries = reg.search(query)

                for entry in entries:
                    score = compute_relevance_score(
                        query_lower=query_lower,
                        name_lower=entry.name.lower(),
                        description_lower=(entry.description or "").lower(),
                        keywords_lower=[k.lower() for k in entry.keywords],
                    )

                    # -----
                    # Always collect name for "Did you mean?" before filtering
                    # -----
                    all_names.append(entry.name)

                    if score == 0 and query_lower:
                        continue  # no match

                    all_results.append(
                        SearchResult(
                            name=entry.name,
                            version=entry.latest,
                            description=entry.description or "",
                            keywords=entry.keywords,
                            artifact_types=entry.artifact_types,
                            origin=reg_source.name,
                            origin_type="registry",
                            score=score,
                            updated_at=getattr(entry, "updated_at", "") or "",
                        )
                    )

            except (ValueError, OSError, KeyError) as exc:
                warning_msg = (
                    f"Could not search registry '{reg_source.name}': {exc}"
                )
                warnings.append(warning_msg)
                logger.warning(warning_msg, exc_info=True)

    # ------------------------------------------------------------------
    # Step 7: Search sources (skip when registry_filter is set)
    # ------------------------------------------------------------------
    if not registry_filter:
        try:
            index = build_source_index(config)

            for vp in index.by_qualified_name.values():
                # -----
                # If a source_filter is set, skip non-matching sources
                # -----
                if source_filter and vp.source_name != source_filter:
                    continue

                score = compute_relevance_score(
                    query_lower=query_lower,
                    name_lower=vp.name.lower(),
                    description_lower=(vp.description or "").lower(),
                    keywords_lower=[],  # sources have no keywords
                )

                # -----
                # Always collect name for "Did you mean?" before filtering
                # -----
                all_names.append(vp.name)

                if score == 0 and query_lower:
                    continue  # no match

                all_results.append(
                    SearchResult(
                        name=vp.name,
                        version=f"source@{vp.commit_sha[:7]}",
                        description=vp.description or "",
                        keywords=[],
                        artifact_types=[vp.type],
                        origin=f"[source] {vp.source_name}",
                        origin_type="source",
                        score=score,
                        updated_at="",
                    )
                )

        except (ValueError, OSError) as exc:
            warning_msg = f"Could not search sources: {exc}"
            warnings.append(warning_msg)
            logger.warning(warning_msg, exc_info=True)

    # ------------------------------------------------------------------
    # Step 8: Apply package_types filter (OR logic)
    # ------------------------------------------------------------------
    if valid_types:
        all_results = [
            r for r in all_results
            if any(t in r.artifact_types for t in valid_types)
        ]

    # ------------------------------------------------------------------
    # Step 9: Sort
    # ------------------------------------------------------------------
    if sort_by == "relevance":
        all_results.sort(key=lambda r: (-r.score, r.name))
    elif sort_by == "name":
        all_results.sort(key=lambda r: r.name.lower())
    elif sort_by == "recent":
        all_results.sort(key=lambda r: r.updated_at, reverse=True)

    # ------------------------------------------------------------------
    # Step 10: Compute total_count before limiting
    # ------------------------------------------------------------------
    total_count = len(all_results)

    # ------------------------------------------------------------------
    # Step 11: Apply limit
    # ------------------------------------------------------------------
    limited_results = all_results[:limit]

    # ------------------------------------------------------------------
    # Step 12: Populate all_names when results empty
    # ------------------------------------------------------------------
    response_all_names: list[str] = []
    if not limited_results:
        response_all_names = all_names

    logger.info(
        f"Search complete: query='{query}', "
        f"total_found={total_count}, returned={len(limited_results)}, "
        f"warnings={len(warnings)}"
    )

    return SearchResponse(
        results=limited_results,
        total_count=total_count,
        warnings=warnings,
        all_names=response_all_names,
    )
