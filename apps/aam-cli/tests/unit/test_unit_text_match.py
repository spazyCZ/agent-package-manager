"""Unit tests for text matching utilities (find_similar_names)."""

import logging

from aam_cli.utils.text_match import (
    MAX_SUGGESTIONS,
    SUGGESTION_THRESHOLD,
    find_similar_names,
)

logger = logging.getLogger(__name__)


################################################################################
#                                                                              #
# TEST: find_similar_names                                                     #
#                                                                              #
################################################################################


class TestFindSimilarNames:
    """Tests for the find_similar_names() fuzzy matching utility."""

    # -----
    # Typical typo matches
    # -----

    def test_unit_similar_names_exact_typo(self) -> None:
        """A common typo like 'chatbt' should match 'chatbot-agent'."""
        names = ["chatbot-agent", "data-processor", "code-review"]
        result = find_similar_names("chatbt", names)
        assert "chatbot-agent" in result

    def test_unit_similar_names_typo_audiit(self) -> None:
        """A doubled-letter typo 'audiit' should match 'audit'."""
        names = ["audit", "search", "install"]
        result = find_similar_names("audiit", names)
        assert "audit" in result

    # -----
    # No match scenarios
    # -----

    def test_unit_similar_names_no_match(self) -> None:
        """Completely unrelated query returns empty list."""
        names = ["chatbot-agent", "data-processor", "code-review"]
        result = find_similar_names("xyz", names)
        assert result == []

    def test_unit_similar_names_empty_names_list(self) -> None:
        """Empty names list returns empty list."""
        result = find_similar_names("chatbot", [])
        assert result == []

    def test_unit_similar_names_empty_query(self) -> None:
        """Empty query returns empty list (no meaningful comparison)."""
        names = ["chatbot-agent", "data-processor"]
        result = find_similar_names("", names)
        assert result == []

    # -----
    # Multiple suggestions and ordering
    # -----

    def test_unit_similar_names_multiple_sorted_by_similarity(self) -> None:
        """Multiple matches are returned sorted by descending similarity."""
        names = ["chatbot", "chatbot-agent", "chatbot-skills", "xyz"]
        result = find_similar_names("chatbt", names)
        # "chatbot" should be the most similar (exact-ish), then others
        assert len(result) >= 1
        # Verify descending similarity — first element is the closest
        assert result[0] == "chatbot"

    # -----
    # Threshold filtering
    # -----

    def test_unit_similar_names_threshold_filtering(self) -> None:
        """Names below threshold are excluded."""
        names = ["chatbot-agent", "zzz-unrelated"]
        # With very high threshold, even close names may be excluded
        result = find_similar_names("chatbt", names, threshold=0.99)
        assert result == []

    def test_unit_similar_names_low_threshold_includes_more(self) -> None:
        """Low threshold includes more distant matches."""
        names = ["chatbot", "chat", "data"]
        result = find_similar_names("chatbt", names, threshold=0.3)
        assert len(result) >= 2  # "chatbot" and "chat" should match

    # -----
    # max_suggestions limit
    # -----

    def test_unit_similar_names_max_limit(self) -> None:
        """Respects max_suggestions limit."""
        names = [f"chatbot-{i}" for i in range(10)]
        result = find_similar_names("chatbot", names, max_suggestions=2)
        assert len(result) <= 2

    def test_unit_similar_names_default_max_is_three(self) -> None:
        """Default max_suggestions is MAX_SUGGESTIONS (3)."""
        assert MAX_SUGGESTIONS == 3
        names = [f"chatbot-{i}" for i in range(10)]
        result = find_similar_names("chatbot", names)
        assert len(result) <= MAX_SUGGESTIONS

    # -----
    # Case insensitivity
    # -----

    def test_unit_similar_names_case_insensitive(self) -> None:
        """Matching is case-insensitive."""
        names = ["ChatBot-Agent", "DATA-Processor"]
        result = find_similar_names("chatbt", names)
        assert "ChatBot-Agent" in result

    # -----
    # Constants
    # -----

    def test_unit_suggestion_threshold_value(self) -> None:
        """SUGGESTION_THRESHOLD is 0.6 as specified in data-model.md."""
        assert SUGGESTION_THRESHOLD == 0.6

    def test_unit_max_suggestions_value(self) -> None:
        """MAX_SUGGESTIONS is 3 as specified in data-model.md."""
        assert MAX_SUGGESTIONS == 3
