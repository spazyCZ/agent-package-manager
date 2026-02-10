"""Evaluation: Suggestion hit-rate for find_similar_names().

SC-005: Verify that the intended package appears in suggestions
for >= 80% of misspelled queries.
"""

import logging

from aam_cli.utils.text_match import find_similar_names

from .datasets.search_suggestion_dataset import SUGGESTION_DATASET

logger = logging.getLogger(__name__)


def test_eval_suggestion_hit_rate_sc005() -> None:
    """SC-005: 80% of misspelled queries return the intended suggestion."""
    hits = 0
    total = len(SUGGESTION_DATASET)

    for entry in SUGGESTION_DATASET:
        query = entry["query"]
        names = entry["names"]
        expected = entry["expected"]

        suggestions = find_similar_names(query, names)

        if expected in suggestions:
            hits += 1
        else:
            logger.warning(
                f"MISS: query='{query}', expected='{expected}', "
                f"got={suggestions}"
            )

    hit_rate = hits / total if total > 0 else 0
    logger.info(f"SC-005 suggestion hit rate: {hit_rate:.0%} ({hits}/{total})")

    assert hit_rate >= 0.8, (
        f"SC-005 FAILED: suggestion hit rate {hit_rate:.0%} < 80% "
        f"({hits}/{total} misspelled queries returned intended suggestion)"
    )
