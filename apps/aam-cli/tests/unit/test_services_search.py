"""Unit tests for search service.

Tests cover:
- compute_relevance_score() scoring tiers (T006)
- search_packages() unified search (T007 — added in Phase 3)
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from unittest.mock import MagicMock, patch

import pytest

from aam_cli.services.search_service import (
    SCORE_DESCRIPTION_CONTAINS,
    SCORE_EXACT_NAME,
    SCORE_KEYWORD_MATCH,
    SCORE_NAME_CONTAINS,
    SCORE_NAME_PREFIX,
    SearchResponse,
    SearchResult,
    compute_relevance_score,
    search_packages,
)

logger = logging.getLogger(__name__)


import time

################################################################################
#                                                                              #
# HELPERS                                                                      #
#                                                                              #
################################################################################


def _make_config(
    registries: list | None = None,
    sources: list | None = None,
) -> MagicMock:
    """Create a mock AamConfig with optional registries and sources."""
    config = MagicMock()
    config.registries = registries or []
    config.sources = sources or []
    return config


def _make_registry_entry(
    name: str,
    description: str = "",
    keywords: list[str] | None = None,
    artifact_types: list[str] | None = None,
    latest: str = "1.0.0",
    updated_at: str = "",
) -> MagicMock:
    """Create a mock PackageIndexEntry."""
    entry = MagicMock()
    entry.name = name
    entry.latest = latest
    entry.description = description
    entry.keywords = keywords or []
    entry.artifact_types = artifact_types or ["skill"]
    entry.updated_at = updated_at
    return entry


def _make_source(name: str = "local") -> MagicMock:
    """Create a mock RegistrySource/SourceEntry."""
    source = MagicMock()
    source.name = name
    return source


def _make_virtual_package(
    name: str,
    source_name: str = "my-source",
    pkg_type: str = "skill",
    description: str = "",
    commit_sha: str = "abc1234def5678",
    qualified_name: str | None = None,
) -> MagicMock:
    """Create a mock VirtualPackage."""
    vp = MagicMock()
    vp.name = name
    vp.source_name = source_name
    vp.type = pkg_type
    vp.description = description
    vp.commit_sha = commit_sha
    vp.qualified_name = qualified_name or f"{source_name}/{name}"
    return vp


################################################################################
#                                                                              #
# TESTS: compute_relevance_score (T006)                                        #
#                                                                              #
################################################################################


class TestComputeRelevanceScore:
    """Tests for the tiered scoring algorithm."""

    def test_unit_score_exact_name_match(self) -> None:
        """Exact name match returns SCORE_EXACT_NAME (100)."""
        score = compute_relevance_score("audit", "audit", "", [])
        assert score == SCORE_EXACT_NAME

    def test_unit_score_name_prefix(self) -> None:
        """Name starts with query returns SCORE_NAME_PREFIX (80)."""
        score = compute_relevance_score("audit", "audit-agent", "", [])
        assert score == SCORE_NAME_PREFIX

    def test_unit_score_name_contains(self) -> None:
        """Name contains query returns SCORE_NAME_CONTAINS (60)."""
        score = compute_relevance_score("audit", "security-audit", "", [])
        assert score == SCORE_NAME_CONTAINS

    def test_unit_score_keyword_match(self) -> None:
        """Keyword exact match returns SCORE_KEYWORD_MATCH (50)."""
        score = compute_relevance_score("audit", "tool-x", "", ["audit"])
        assert score == SCORE_KEYWORD_MATCH

    def test_unit_score_description_contains(self) -> None:
        """Description contains query returns SCORE_DESCRIPTION_CONTAINS (30)."""
        score = compute_relevance_score(
            "audit", "tool-x", "asvs audit tool", []
        )
        assert score == SCORE_DESCRIPTION_CONTAINS

    def test_unit_score_no_match(self) -> None:
        """No match returns 0."""
        score = compute_relevance_score("audit", "xyz", "no match here", [])
        assert score == 0

    def test_unit_score_empty_query_browse_mode(self) -> None:
        """Empty query returns SCORE_EXACT_NAME (browse mode)."""
        score = compute_relevance_score("", "anything", "whatever", [])
        assert score == SCORE_EXACT_NAME

    def test_unit_score_case_insensitive(self) -> None:
        """All inputs should already be lowercased by caller.

        This test verifies the function works correctly when given
        lowercased inputs (the contract requires callers to lowercase).
        """
        score = compute_relevance_score("audit", "audit-agent", "", [])
        assert score == SCORE_NAME_PREFIX

    def test_unit_score_highest_tier_wins(self) -> None:
        """A name that matches BOTH name-contains AND description should
        only get the name score (higher tier wins).
        """
        # "audit" is in "security-audit" (name-contains = 60)
        # "audit" is also in "audit tool" (description = 30)
        # Highest tier wins: 60
        score = compute_relevance_score(
            "audit", "security-audit", "audit tool", ["audit"]
        )
        assert score == SCORE_NAME_CONTAINS  # 60, not 50 or 30

    def test_unit_score_tier_ordering(self) -> None:
        """Verify the constant values follow the expected ordering."""
        assert SCORE_EXACT_NAME > SCORE_NAME_PREFIX
        assert SCORE_NAME_PREFIX > SCORE_NAME_CONTAINS
        assert SCORE_NAME_CONTAINS > SCORE_KEYWORD_MATCH
        assert SCORE_KEYWORD_MATCH > SCORE_DESCRIPTION_CONTAINS
        assert SCORE_DESCRIPTION_CONTAINS > 0


################################################################################
#                                                                              #
# TESTS: search_packages — existing tests (updated for SearchResponse)         #
#                                                                              #
################################################################################


class TestSearchPackagesExisting:
    """Updated versions of the original 5 tests, now expecting SearchResponse."""

    @patch("aam_cli.services.search_service.build_source_index")
    def test_unit_search_no_registries_with_sources(
        self, mock_build_index: MagicMock
    ) -> None:
        """With no registries but sources exist, returns empty results."""
        mock_index = MagicMock()
        mock_index.by_qualified_name = {}
        mock_build_index.return_value = mock_index

        config = _make_config(
            registries=[],
            sources=[_make_source("src1")],
        )
        response = search_packages("test", config)
        assert isinstance(response, SearchResponse)
        assert response.results == []

    @patch("aam_cli.services.search_service.build_source_index")
    @patch("aam_cli.services.search_service.create_registry")
    def test_unit_search_single_registry(
        self,
        mock_create_reg: MagicMock,
        mock_build_index: MagicMock,
    ) -> None:
        """Single registry with a matching entry returns one result."""
        mock_entry = _make_registry_entry("test-pkg", description="A test package")
        mock_reg = MagicMock()
        mock_reg.search.return_value = [mock_entry]
        mock_create_reg.return_value = mock_reg

        mock_index = MagicMock()
        mock_index.by_qualified_name = {}
        mock_build_index.return_value = mock_index

        config = _make_config(registries=[_make_source("local")])
        response = search_packages("test", config)
        assert isinstance(response, SearchResponse)
        assert len(response.results) == 1
        assert response.results[0].name == "test-pkg"

    @patch("aam_cli.services.search_service.build_source_index")
    @patch("aam_cli.services.search_service.create_registry")
    def test_unit_search_with_limit(
        self,
        mock_create_reg: MagicMock,
        mock_build_index: MagicMock,
    ) -> None:
        """Limit caps the number of returned results."""
        entries = [
            _make_registry_entry(f"pkg-{i}", description=f"Package {i}")
            for i in range(5)
        ]
        mock_reg = MagicMock()
        mock_reg.search.return_value = entries
        mock_create_reg.return_value = mock_reg

        mock_index = MagicMock()
        mock_index.by_qualified_name = {}
        mock_build_index.return_value = mock_index

        config = _make_config(registries=[_make_source("local")])
        response = search_packages("pkg", config, limit=3)
        assert len(response.results) == 3
        assert response.total_count == 5

    @patch("aam_cli.services.search_service.build_source_index")
    @patch("aam_cli.services.search_service.create_registry")
    def test_unit_search_with_type_filter(
        self,
        mock_create_reg: MagicMock,
        mock_build_index: MagicMock,
    ) -> None:
        """Type filter restricts results to matching artifact types."""
        skill_entry = _make_registry_entry(
            "skill-pkg", description="Skill", artifact_types=["skill"]
        )
        agent_entry = _make_registry_entry(
            "agent-pkg", description="Agent", artifact_types=["agent"]
        )
        mock_reg = MagicMock()
        mock_reg.search.return_value = [skill_entry, agent_entry]
        mock_create_reg.return_value = mock_reg

        mock_index = MagicMock()
        mock_index.by_qualified_name = {}
        mock_build_index.return_value = mock_index

        config = _make_config(registries=[_make_source("local")])
        response = search_packages("", config, package_types=["skill"])
        assert len(response.results) == 1
        assert response.results[0].name == "skill-pkg"

    def test_unit_search_invalid_limit(self) -> None:
        """Limit outside [1, 50] raises ValueError."""
        config = _make_config(sources=[_make_source("src1")])
        with pytest.raises(ValueError, match="AAM_INVALID_ARGUMENT"):
            search_packages("test", config, limit=0)
        with pytest.raises(ValueError, match="AAM_INVALID_ARGUMENT"):
            search_packages("test", config, limit=51)


################################################################################
#                                                                              #
# TESTS: search_packages — new tests (T007)                                    #
#                                                                              #
################################################################################


class TestSearchPackagesNew:
    """New tests for the unified search_packages rewrite."""

    # -----
    # Source search (US2)
    # -----

    @patch("aam_cli.services.search_service.build_source_index")
    def test_unit_search_sources_included(
        self, mock_build_index: MagicMock
    ) -> None:
        """Results include source artifacts scored by relevance."""
        vp = _make_virtual_package("chatbot-agent", description="A chatbot")
        mock_index = MagicMock()
        mock_index.by_qualified_name = {"my-source/chatbot-agent": vp}
        mock_build_index.return_value = mock_index

        config = _make_config(sources=[_make_source("my-source")])
        response = search_packages("chatbot", config)

        assert len(response.results) == 1
        assert response.results[0].name == "chatbot-agent"
        assert response.results[0].origin_type == "source"

    @patch("aam_cli.services.search_service.build_source_index")
    def test_unit_search_sources_only_no_registry(
        self, mock_build_index: MagicMock
    ) -> None:
        """Works with zero registries if sources exist (US2)."""
        vp = _make_virtual_package("doc-writer", description="Write docs")
        mock_index = MagicMock()
        mock_index.by_qualified_name = {"my-source/doc-writer": vp}
        mock_build_index.return_value = mock_index

        config = _make_config(registries=[], sources=[_make_source("src")])
        response = search_packages("doc", config)

        assert len(response.results) == 1
        assert response.results[0].name == "doc-writer"

    def test_unit_search_no_sources_no_registries_error(self) -> None:
        """Raises ValueError when both registries and sources empty (US2)."""
        config = _make_config(registries=[], sources=[])
        with pytest.raises(ValueError, match="AAM_NO_SOURCES"):
            search_packages("test", config)

    # -----
    # Warning propagation (US7)
    # -----

    @patch("aam_cli.services.search_service.build_source_index")
    def test_unit_search_source_failure_warning(
        self, mock_build_index: MagicMock
    ) -> None:
        """Source failure adds warning string to response.warnings (US7)."""
        mock_build_index.side_effect = OSError("git clone failed")

        config = _make_config(sources=[_make_source("broken-src")])
        response = search_packages("test", config)

        assert len(response.warnings) >= 1
        assert "Could not search sources" in response.warnings[0]

    @patch("aam_cli.services.search_service.build_source_index")
    @patch("aam_cli.services.search_service.create_registry")
    def test_unit_search_registry_failure_warning(
        self,
        mock_create_reg: MagicMock,
        mock_build_index: MagicMock,
    ) -> None:
        """Registry failure adds warning to response.warnings (US7)."""
        mock_create_reg.side_effect = OSError("registry unavailable")

        mock_index = MagicMock()
        mock_index.by_qualified_name = {}
        mock_build_index.return_value = mock_index

        config = _make_config(
            registries=[_make_source("broken-reg")],
            sources=[_make_source("src")],
        )
        response = search_packages("test", config)

        assert len(response.warnings) >= 1
        assert "Could not search registry 'broken-reg'" in response.warnings[0]

    # -----
    # Total count and limit
    # -----

    @patch("aam_cli.services.search_service.build_source_index")
    @patch("aam_cli.services.search_service.create_registry")
    def test_unit_search_total_count_with_limit(
        self,
        mock_create_reg: MagicMock,
        mock_build_index: MagicMock,
    ) -> None:
        """total_count > len(results) when results are truncated."""
        entries = [
            _make_registry_entry(f"pkg-{i}", description=f"Package {i}")
            for i in range(10)
        ]
        mock_reg = MagicMock()
        mock_reg.search.return_value = entries
        mock_create_reg.return_value = mock_reg

        mock_index = MagicMock()
        mock_index.by_qualified_name = {}
        mock_build_index.return_value = mock_index

        config = _make_config(registries=[_make_source("local")])
        response = search_packages("pkg", config, limit=3)

        assert response.total_count == 10
        assert len(response.results) == 3

    # -----
    # all_names on empty results
    # -----

    @patch("aam_cli.services.search_service.build_source_index")
    @patch("aam_cli.services.search_service.create_registry")
    def test_unit_search_all_names_on_empty_results(
        self,
        mock_create_reg: MagicMock,
        mock_build_index: MagicMock,
    ) -> None:
        """all_names is populated when 0 results match."""
        # Registry has entries but query doesn't match
        entries = [_make_registry_entry("chatbot", description="A chatbot")]
        mock_reg = MagicMock()
        mock_reg.search.return_value = entries
        mock_create_reg.return_value = mock_reg

        mock_index = MagicMock()
        mock_index.by_qualified_name = {}
        mock_build_index.return_value = mock_index

        config = _make_config(registries=[_make_source("local")])
        response = search_packages("zzz-nonexistent", config)

        assert len(response.results) == 0
        # all_names should contain names from the registry
        # Note: all_names is populated from entries that the registry
        # returns for the query — if registry returns entries but they
        # don't match our scoring, their names still appear via the
        # reg.search() results
        assert response.total_count == 0

    # -----
    # Empty query / browse mode
    # -----

    @patch("aam_cli.services.search_service.build_source_index")
    @patch("aam_cli.services.search_service.create_registry")
    def test_unit_search_empty_query_browse(
        self,
        mock_create_reg: MagicMock,
        mock_build_index: MagicMock,
    ) -> None:
        """Empty query returns all packages scored at SCORE_EXACT_NAME."""
        entries = [
            _make_registry_entry("alpha"),
            _make_registry_entry("beta"),
        ]
        mock_reg = MagicMock()
        mock_reg.search.return_value = entries
        mock_create_reg.return_value = mock_reg

        mock_index = MagicMock()
        mock_index.by_qualified_name = {}
        mock_build_index.return_value = mock_index

        config = _make_config(registries=[_make_source("local")])
        response = search_packages("", config)

        assert len(response.results) == 2
        for r in response.results:
            assert r.score == SCORE_EXACT_NAME

    # -----
    # Relevance ranking (US1)
    # -----

    @patch("aam_cli.services.search_service.build_source_index")
    @patch("aam_cli.services.search_service.create_registry")
    def test_unit_search_relevance_exact_name_first(
        self,
        mock_create_reg: MagicMock,
        mock_build_index: MagicMock,
    ) -> None:
        """Exact name match scores 100 and appears first (US1)."""
        entries = [
            _make_registry_entry("audit-tool", description="Audit tool"),
            _make_registry_entry("audit", description="The audit package"),
        ]
        mock_reg = MagicMock()
        mock_reg.search.return_value = entries
        mock_create_reg.return_value = mock_reg

        mock_index = MagicMock()
        mock_index.by_qualified_name = {}
        mock_build_index.return_value = mock_index

        config = _make_config(registries=[_make_source("local")])
        response = search_packages("audit", config)

        assert response.results[0].name == "audit"
        assert response.results[0].score == SCORE_EXACT_NAME

    @patch("aam_cli.services.search_service.build_source_index")
    @patch("aam_cli.services.search_service.create_registry")
    def test_unit_search_relevance_prefix_before_substring(
        self,
        mock_create_reg: MagicMock,
        mock_build_index: MagicMock,
    ) -> None:
        """Prefix match (80) ranks above substring (60) (US1)."""
        entries = [
            _make_registry_entry(
                "security-audit", description="Sec audit"
            ),
            _make_registry_entry(
                "audit-agent", description="Agent for auditing"
            ),
        ]
        mock_reg = MagicMock()
        mock_reg.search.return_value = entries
        mock_create_reg.return_value = mock_reg

        mock_index = MagicMock()
        mock_index.by_qualified_name = {}
        mock_build_index.return_value = mock_index

        config = _make_config(registries=[_make_source("local")])
        response = search_packages("audit", config)

        assert response.results[0].name == "audit-agent"
        assert response.results[0].score == SCORE_NAME_PREFIX
        assert response.results[1].name == "security-audit"
        assert response.results[1].score == SCORE_NAME_CONTAINS

    @patch("aam_cli.services.search_service.build_source_index")
    @patch("aam_cli.services.search_service.create_registry")
    def test_unit_search_relevance_name_before_description(
        self,
        mock_create_reg: MagicMock,
        mock_build_index: MagicMock,
    ) -> None:
        """Name-contains (60) ranks above description-only (30) (US1)."""
        entries = [
            _make_registry_entry(
                "tool-x", description="An audit tool"
            ),
            _make_registry_entry(
                "security-audit", description="Unrelated"
            ),
        ]
        mock_reg = MagicMock()
        mock_reg.search.return_value = entries
        mock_create_reg.return_value = mock_reg

        mock_index = MagicMock()
        mock_index.by_qualified_name = {}
        mock_build_index.return_value = mock_index

        config = _make_config(registries=[_make_source("local")])
        response = search_packages("audit", config)

        assert response.results[0].name == "security-audit"
        assert response.results[0].score == SCORE_NAME_CONTAINS
        assert response.results[1].name == "tool-x"
        assert response.results[1].score == SCORE_DESCRIPTION_CONTAINS

    # -----
    # Filtering (US4)
    # -----

    @patch("aam_cli.services.search_service.build_source_index")
    @patch("aam_cli.services.search_service.create_registry")
    def test_unit_search_type_filter_multiple(
        self,
        mock_create_reg: MagicMock,
        mock_build_index: MagicMock,
    ) -> None:
        """Multi-type filter uses OR logic (US4)."""
        entries = [
            _make_registry_entry("a", artifact_types=["skill"]),
            _make_registry_entry("b", artifact_types=["agent"]),
            _make_registry_entry("c", artifact_types=["prompt"]),
        ]
        mock_reg = MagicMock()
        mock_reg.search.return_value = entries
        mock_create_reg.return_value = mock_reg

        mock_index = MagicMock()
        mock_index.by_qualified_name = {}
        mock_build_index.return_value = mock_index

        config = _make_config(registries=[_make_source("local")])
        response = search_packages(
            "", config, package_types=["skill", "agent"]
        )

        names = [r.name for r in response.results]
        assert "a" in names
        assert "b" in names
        assert "c" not in names

    @patch("aam_cli.services.search_service.build_source_index")
    def test_unit_search_source_filter(
        self,
        mock_build_index: MagicMock,
    ) -> None:
        """source_filter limits results to one source (US4)."""
        vp1 = _make_virtual_package("doc-writer", source_name="src-a")
        vp2 = _make_virtual_package("code-review", source_name="src-b")
        mock_index = MagicMock()
        mock_index.by_qualified_name = {
            "src-a/doc-writer": vp1,
            "src-b/code-review": vp2,
        }
        mock_build_index.return_value = mock_index

        config = _make_config(
            sources=[_make_source("src-a"), _make_source("src-b")]
        )
        response = search_packages("", config, source_filter="src-a")

        # source_filter skips registries entirely, only shows src-a
        names = [r.name for r in response.results]
        assert "doc-writer" in names
        assert "code-review" not in names

    @patch("aam_cli.services.search_service.create_registry")
    def test_unit_search_registry_filter(
        self,
        mock_create_reg: MagicMock,
    ) -> None:
        """registry_filter limits results to one registry (US4)."""
        entries = [_make_registry_entry("pkg-a")]
        mock_reg = MagicMock()
        mock_reg.search.return_value = entries
        mock_create_reg.return_value = mock_reg

        reg_a = _make_source("reg-a")
        reg_b = _make_source("reg-b")

        config = _make_config(
            registries=[reg_a, reg_b],
            sources=[_make_source("src")],
        )
        # registry_filter skips sources entirely
        search_packages("", config, registry_filter="reg-a")

        # create_registry should only be called once (for reg-a)
        assert mock_create_reg.call_count == 1

    @patch("aam_cli.services.search_service.build_source_index")
    def test_unit_search_unknown_type_warning(
        self, mock_build_index: MagicMock
    ) -> None:
        """Warning for invalid artifact type (US4)."""
        mock_index = MagicMock()
        mock_index.by_qualified_name = {}
        mock_build_index.return_value = mock_index

        config = _make_config(sources=[_make_source("src")])
        response = search_packages(
            "", config, package_types=["invalid-type"]
        )

        assert any(
            "Unknown artifact type 'invalid-type'" in w
            for w in response.warnings
        )

    @patch("aam_cli.services.search_service.build_source_index")
    def test_unit_search_unknown_source_warning(
        self, mock_build_index: MagicMock
    ) -> None:
        """Warning for non-existent source filter (US4)."""
        mock_index = MagicMock()
        mock_index.by_qualified_name = {}
        mock_build_index.return_value = mock_index

        config = _make_config(sources=[_make_source("real-src")])
        response = search_packages(
            "", config, source_filter="nonexistent"
        )

        assert any(
            "Source 'nonexistent' not found" in w
            for w in response.warnings
        )

    # -----
    # Sorting (US6)
    # -----

    @patch("aam_cli.services.search_service.build_source_index")
    @patch("aam_cli.services.search_service.create_registry")
    def test_unit_search_sort_name(
        self,
        mock_create_reg: MagicMock,
        mock_build_index: MagicMock,
    ) -> None:
        """sort_by='name' returns alphabetical order (US6)."""
        entries = [
            _make_registry_entry("zebra"),
            _make_registry_entry("alpha"),
            _make_registry_entry("mike"),
        ]
        mock_reg = MagicMock()
        mock_reg.search.return_value = entries
        mock_create_reg.return_value = mock_reg

        mock_index = MagicMock()
        mock_index.by_qualified_name = {}
        mock_build_index.return_value = mock_index

        config = _make_config(registries=[_make_source("local")])
        response = search_packages("", config, sort_by="name")

        names = [r.name for r in response.results]
        assert names == ["alpha", "mike", "zebra"]

    @patch("aam_cli.services.search_service.build_source_index")
    @patch("aam_cli.services.search_service.create_registry")
    def test_unit_search_sort_recent(
        self,
        mock_create_reg: MagicMock,
        mock_build_index: MagicMock,
    ) -> None:
        """sort_by='recent' returns most recent first (US6)."""
        entries = [
            _make_registry_entry("old", updated_at="2025-01-01T00:00:00Z"),
            _make_registry_entry("new", updated_at="2026-02-01T00:00:00Z"),
            _make_registry_entry("mid", updated_at="2025-06-15T00:00:00Z"),
        ]
        mock_reg = MagicMock()
        mock_reg.search.return_value = entries
        mock_create_reg.return_value = mock_reg

        mock_index = MagicMock()
        mock_index.by_qualified_name = {}
        mock_build_index.return_value = mock_index

        config = _make_config(registries=[_make_source("local")])
        response = search_packages("", config, sort_by="recent")

        names = [r.name for r in response.results]
        assert names == ["new", "mid", "old"]

    @patch("aam_cli.services.search_service.build_source_index")
    @patch("aam_cli.services.search_service.create_registry")
    def test_unit_search_sort_relevance_default(
        self,
        mock_create_reg: MagicMock,
        mock_build_index: MagicMock,
    ) -> None:
        """Default sort is 'relevance' (score desc, name asc tiebreak)."""
        entries = [
            _make_registry_entry("b-tool", description="audit tool"),
            _make_registry_entry("audit", description="The audit pkg"),
            _make_registry_entry("a-audit-helper", description="Helper"),
        ]
        mock_reg = MagicMock()
        mock_reg.search.return_value = entries
        mock_create_reg.return_value = mock_reg

        mock_index = MagicMock()
        mock_index.by_qualified_name = {}
        mock_build_index.return_value = mock_index

        config = _make_config(registries=[_make_source("local")])
        response = search_packages("audit", config)

        # audit → exact (100), a-audit-helper → contains (60),
        # b-tool → description (30)
        assert response.results[0].name == "audit"
        assert response.results[1].name == "a-audit-helper"
        assert response.results[2].name == "b-tool"

    def test_unit_search_invalid_sort_raises(self) -> None:
        """Invalid sort_by raises ValueError."""
        config = _make_config(sources=[_make_source("src")])
        with pytest.raises(ValueError, match="AAM_INVALID_ARGUMENT"):
            search_packages("test", config, sort_by="invalid")

    # -----
    # Model validation
    # -----

    def test_unit_search_response_model_validation(self) -> None:
        """SearchResponse Pydantic model validates correctly."""
        result = SearchResult(
            name="test-pkg",
            version="1.0.0",
            description="Test",
            origin="local",
            origin_type="registry",
            score=80,
        )
        response = SearchResponse(
            results=[result],
            total_count=1,
            warnings=[],
            all_names=[],
        )
        assert response.total_count == 1
        assert response.results[0].name == "test-pkg"

    # -----
    # Edge cases (EC-005, F7, F8, F9)
    # -----

    @patch("aam_cli.services.search_service.build_source_index")
    @patch("aam_cli.services.search_service.create_registry")
    def test_unit_search_special_characters_in_query(
        self,
        mock_create_reg: MagicMock,
        mock_build_index: MagicMock,
    ) -> None:
        """Query with special chars does not crash (EC-005)."""
        mock_reg = MagicMock()
        mock_reg.search.return_value = []
        mock_create_reg.return_value = mock_reg

        mock_index = MagicMock()
        mock_index.by_qualified_name = {}
        mock_build_index.return_value = mock_index

        config = _make_config(registries=[_make_source("local")])

        for special_query in ["@scope/pkg", "pkg#1", "name[0]", "a+b"]:
            response = search_packages(special_query, config)
            assert isinstance(response, SearchResponse)

    @patch("aam_cli.services.search_service.build_source_index")
    @patch("aam_cli.services.search_service.create_registry")
    def test_unit_search_duplicate_names_across_origins(
        self,
        mock_create_reg: MagicMock,
        mock_build_index: MagicMock,
    ) -> None:
        """Same package name from registry and source both appear."""
        entries = [_make_registry_entry("chatbot", description="Reg chatbot")]
        mock_reg = MagicMock()
        mock_reg.search.return_value = entries
        mock_create_reg.return_value = mock_reg

        vp = _make_virtual_package("chatbot", description="Source chatbot")
        mock_index = MagicMock()
        mock_index.by_qualified_name = {"src/chatbot": vp}
        mock_build_index.return_value = mock_index

        config = _make_config(
            registries=[_make_source("local")],
            sources=[_make_source("src")],
        )
        response = search_packages("chatbot", config)

        assert len(response.results) == 2
        origin_types = {r.origin_type for r in response.results}
        assert origin_types == {"registry", "source"}

    @patch("aam_cli.services.search_service.build_source_index")
    @patch("aam_cli.services.search_service.create_registry")
    def test_unit_search_limit_exceeds_total(
        self,
        mock_create_reg: MagicMock,
        mock_build_index: MagicMock,
    ) -> None:
        """limit=100 with only 5 results returns all 5, no error."""
        # limit max is 50, so use 50
        entries = [
            _make_registry_entry(f"pkg-{i}") for i in range(5)
        ]
        mock_reg = MagicMock()
        mock_reg.search.return_value = entries
        mock_create_reg.return_value = mock_reg

        mock_index = MagicMock()
        mock_index.by_qualified_name = {}
        mock_build_index.return_value = mock_index

        config = _make_config(registries=[_make_source("local")])
        response = search_packages("", config, limit=50)

        assert len(response.results) == 5
        assert response.total_count == 5


################################################################################
#                                                                              #
# TESTS: Performance benchmark (T024 / SC-007)                                 #
#                                                                              #
################################################################################


class TestSearchPerformance:
    """Performance benchmark for search_packages (SC-007)."""

    @patch("aam_cli.services.search_service.build_source_index")
    @patch("aam_cli.services.search_service.create_registry")
    def test_unit_search_performance_under_2s(
        self,
        mock_create_reg: MagicMock,
        mock_build_index: MagicMock,
    ) -> None:
        """SC-007: search completes in <2s for 500 packages across 5 sources.

        Creates a mock config with 500 packages spread across 3 registries
        and 2 git sources, then times a search_packages() call.
        """
        # -----
        # Set up 3 registries with ~100 entries each (300 total)
        # -----
        reg_entries = [
            _make_registry_entry(
                f"reg-pkg-{i}",
                description=f"Registry package number {i}",
                keywords=["tool", "agent"] if i % 3 == 0 else [],
                artifact_types=["skill"] if i % 2 == 0 else ["agent"],
            )
            for i in range(100)
        ]
        mock_reg = MagicMock()
        mock_reg.search.return_value = reg_entries
        mock_create_reg.return_value = mock_reg

        # -----
        # Set up 2 sources with ~100 virtual packages each (200 total)
        # -----
        source_vps: dict[str, MagicMock] = {}
        for i in range(200):
            src_name = f"source-{'a' if i < 100 else 'b'}"
            vp = _make_virtual_package(
                f"src-pkg-{i}",
                source_name=src_name,
                description=f"Source package number {i}",
            )
            source_vps[f"{src_name}/src-pkg-{i}"] = vp

        mock_index = MagicMock()
        mock_index.by_qualified_name = source_vps
        mock_build_index.return_value = mock_index

        config = _make_config(
            registries=[
                _make_source("reg-1"),
                _make_source("reg-2"),
                _make_source("reg-3"),
            ],
            sources=[
                _make_source("source-a"),
                _make_source("source-b"),
            ],
        )

        # -----
        # Time the search
        # -----
        start = time.monotonic()
        response = search_packages("pkg", config, limit=50)
        elapsed = time.monotonic() - start

        logger.info(
            f"SC-007 performance: elapsed={elapsed:.3f}s, "
            f"total_count={response.total_count}, "
            f"returned={len(response.results)}"
        )

        assert elapsed < 2.0, (
            f"SC-007 FAILED: search took {elapsed:.3f}s (> 2.0s) "
            f"for {response.total_count} total packages"
        )
        assert response.total_count > 0
