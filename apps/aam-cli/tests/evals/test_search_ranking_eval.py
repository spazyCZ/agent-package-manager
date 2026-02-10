"""Evaluation: Ranking accuracy for compute_relevance_score().

SC-001: Verify that the expected package appears in the top 3 results
for >= 90% of dataset entries.
"""

import logging

from aam_cli.services.search_service import compute_relevance_score

from .datasets.search_ranking_dataset import RANKING_DATASET

logger = logging.getLogger(__name__)


def test_eval_ranking_accuracy_sc001() -> None:
    """SC-001: 90% of queries place expected package in top 3."""
    hits = 0
    total = len(RANKING_DATASET)

    for entry in RANKING_DATASET:
        query = entry["query"].lower()
        must_include = entry["must_include"]

        # -----
        # Score all candidates
        # -----
        scored: list[tuple[int, str]] = []
        for c in entry["candidates"]:
            score = compute_relevance_score(
                query_lower=query,
                name_lower=c["name"].lower(),
                description_lower=c["description"].lower(),
                keywords_lower=[k.lower() for k in c["keywords"]],
            )
            scored.append((score, c["name"]))

        # -----
        # Sort by score descending, name ascending (same as service)
        # -----
        scored.sort(key=lambda x: (-x[0], x[1]))
        top_3_names = [name for _, name in scored[:3]]

        if must_include in top_3_names:
            hits += 1
        else:
            logger.warning(
                f"MISS: query='{query}', must_include='{must_include}', "
                f"top_3={top_3_names}"
            )

    accuracy = hits / total if total > 0 else 0
    logger.info(f"SC-001 ranking accuracy: {accuracy:.0%} ({hits}/{total})")

    assert accuracy >= 0.9, (
        f"SC-001 FAILED: ranking accuracy {accuracy:.0%} < 90% "
        f"({hits}/{total} queries placed expected package in top 3)"
    )
