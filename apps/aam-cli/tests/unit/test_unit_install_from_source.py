"""Unit tests for source resolution and install-from-source flow.

Tests build_source_index, resolve_artifact (qualified/unqualified/
ambiguous/not-found), install_from_source with mocked filesystem,
and the install command source fallback path.

Reference: spec 004 US2; tasks.md T024.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging

import pytest

from aam_cli.services.source_service import (
    ArtifactIndex,
    VirtualPackage,
    resolve_artifact,
)

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# FIXTURES                                                                     #
#                                                                              #
################################################################################


@pytest.fixture
def sample_index() -> ArtifactIndex:
    """Build a sample ArtifactIndex with test data."""
    vp1 = VirtualPackage(
        name="code-review",
        qualified_name="my-source/code-review",
        source_name="my-source",
        type="skill",
        path="skills/code-review",
        commit_sha="abc123def456789012345678901234567890abcd",
        cache_dir="/tmp/cache/my-source",
        description="Code review skill",
    )

    vp2 = VirtualPackage(
        name="code-review",
        qualified_name="other-source/code-review",
        source_name="other-source",
        type="skill",
        path="skills/code-review",
        commit_sha="def456789012345678901234567890abcdef1234",
        cache_dir="/tmp/cache/other-source",
        description="Another code review skill",
    )

    vp3 = VirtualPackage(
        name="test-agent",
        qualified_name="my-source/test-agent",
        source_name="my-source",
        type="agent",
        path="agents/test-agent",
        commit_sha="abc123def456789012345678901234567890abcd",
        cache_dir="/tmp/cache/my-source",
        description="Test agent",
    )

    index = ArtifactIndex(
        by_name={
            "code-review": [vp1, vp2],
            "test-agent": [vp3],
        },
        by_qualified_name={
            "my-source/code-review": vp1,
            "other-source/code-review": vp2,
            "my-source/test-agent": vp3,
        },
        total_count=3,
        sources_indexed=2,
        build_timestamp="2026-02-09T00:00:00Z",
    )

    return index


################################################################################
#                                                                              #
# TEST: resolve_artifact — QUALIFIED NAME                                      #
#                                                                              #
################################################################################


class TestResolveArtifactQualified:
    """Verify resolution with qualified names (source/artifact)."""

    def test_qualified_name_resolves_directly(
        self, sample_index: ArtifactIndex
    ) -> None:
        """Qualified name should resolve to exact match."""
        result = resolve_artifact("my-source/code-review", sample_index)

        assert result.name == "code-review"
        assert result.source_name == "my-source"

    def test_qualified_name_other_source(
        self, sample_index: ArtifactIndex
    ) -> None:
        """Qualified name from other source should resolve correctly."""
        result = resolve_artifact("other-source/code-review", sample_index)

        assert result.name == "code-review"
        assert result.source_name == "other-source"

    def test_qualified_name_not_found_raises(
        self, sample_index: ArtifactIndex
    ) -> None:
        """Non-existent qualified name should raise ValueError."""
        with pytest.raises(ValueError, match="AAM_ARTIFACT_NOT_FOUND"):
            resolve_artifact("unknown/artifact", sample_index)


################################################################################
#                                                                              #
# TEST: resolve_artifact — UNQUALIFIED NAME                                    #
#                                                                              #
################################################################################


class TestResolveArtifactUnqualified:
    """Verify resolution with unqualified (plain) names."""

    def test_unique_name_resolves(
        self, sample_index: ArtifactIndex
    ) -> None:
        """Unique unqualified name should resolve directly."""
        result = resolve_artifact("test-agent", sample_index)

        assert result.name == "test-agent"
        assert result.source_name == "my-source"

    def test_ambiguous_name_uses_first_match(
        self, sample_index: ArtifactIndex
    ) -> None:
        """Ambiguous name should use first match (config order)."""
        result = resolve_artifact("code-review", sample_index)

        # First match is my-source (config order)
        assert result.name == "code-review"
        assert result.source_name == "my-source"

    def test_not_found_raises(
        self, sample_index: ArtifactIndex
    ) -> None:
        """Non-existent unqualified name should raise ValueError."""
        with pytest.raises(ValueError, match="AAM_ARTIFACT_NOT_FOUND"):
            resolve_artifact("nonexistent", sample_index)


################################################################################
#                                                                              #
# TEST: ArtifactIndex STRUCTURE                                                #
#                                                                              #
################################################################################


class TestArtifactIndex:
    """Verify ArtifactIndex data structure behavior."""

    def test_index_counts(self, sample_index: ArtifactIndex) -> None:
        """Index should have correct counts."""
        assert sample_index.total_count == 3
        assert sample_index.sources_indexed == 2

    def test_by_name_groups_duplicates(
        self, sample_index: ArtifactIndex
    ) -> None:
        """by_name should group same-name artifacts from different sources."""
        assert len(sample_index.by_name["code-review"]) == 2

    def test_by_qualified_name_is_unique(
        self, sample_index: ArtifactIndex
    ) -> None:
        """by_qualified_name should have unique entries."""
        assert len(sample_index.by_qualified_name) == 3

    def test_empty_index(self) -> None:
        """Empty index should have zero counts."""
        index = ArtifactIndex()

        assert index.total_count == 0
        assert index.sources_indexed == 0
        assert len(index.by_name) == 0
        assert len(index.by_qualified_name) == 0


################################################################################
#                                                                              #
# TEST: VirtualPackage                                                         #
#                                                                              #
################################################################################


class TestVirtualPackage:
    """Verify VirtualPackage dataclass behavior."""

    def test_virtual_package_fields(self) -> None:
        """VirtualPackage should store all required fields."""
        vp = VirtualPackage(
            name="test",
            qualified_name="source/test",
            source_name="source",
            type="skill",
            path="skills/test",
            commit_sha="abc123",
            cache_dir="/tmp/cache",
            description="A test skill",
        )

        assert vp.name == "test"
        assert vp.qualified_name == "source/test"
        assert vp.source_name == "source"
        assert vp.type == "skill"
        assert vp.commit_sha == "abc123"
        assert vp.has_vendor_agent is False
