"""Text matching utilities for search scoring and fuzzy suggestions.

Provides fuzzy name matching using Python stdlib ``difflib`` for
"Did you mean?" suggestions when search returns no results.

No external dependencies — uses only ``difflib.SequenceMatcher``.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import difflib
import logging

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

SUGGESTION_THRESHOLD: float = 0.6
"""Minimum ``SequenceMatcher.ratio()`` for a name to be considered similar."""

MAX_SUGGESTIONS: int = 3
"""Maximum number of "Did you mean?" suggestions to return."""

################################################################################
#                                                                              #
# PUBLIC FUNCTIONS                                                             #
#                                                                              #
################################################################################


def find_similar_names(
    query: str,
    names: list[str],
    threshold: float = SUGGESTION_THRESHOLD,
    max_suggestions: int = MAX_SUGGESTIONS,
) -> list[str]:
    """Find names similar to *query* for "Did you mean?" suggestions.

    Compares the query against every name in *names* using
    ``difflib.SequenceMatcher.ratio()``, keeping those that exceed the
    *threshold* and returning the top *max_suggestions* sorted by
    descending similarity.

    Args:
        query: The user's original search query.
        names: All known package / artifact names to compare against.
        threshold: Minimum similarity ratio (0.0–1.0) for inclusion.
        max_suggestions: Maximum number of suggestions to return.

    Returns:
        A list of similar names sorted by descending similarity.
        Empty list if no name exceeds the threshold.
    """
    logger.debug(
        f"Finding similar names: query='{query}', "
        f"candidates={len(names)}, threshold={threshold}"
    )

    # -----
    # Early exit on empty inputs
    # -----
    if not query or not names:
        return []

    query_lower = query.lower()

    # -----
    # Compute similarity for each candidate
    # -----
    scored: list[tuple[float, str]] = []
    for name in names:
        ratio = difflib.SequenceMatcher(
            None, query_lower, name.lower()
        ).ratio()
        if ratio >= threshold:
            scored.append((ratio, name))

    # -----
    # Sort by similarity descending, then take top N
    # -----
    scored.sort(key=lambda pair: pair[0], reverse=True)
    suggestions = [name for _, name in scored[:max_suggestions]]

    logger.debug(
        f"Similar names result: query='{query}', "
        f"suggestions={suggestions}"
    )

    return suggestions
