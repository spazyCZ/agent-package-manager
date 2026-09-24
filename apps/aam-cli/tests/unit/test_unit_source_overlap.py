"""Unit tests for source overlap detection and duplicate materialization.

Tests the _normalize_source_identity(), _find_overlapping_source() helpers,
the overlap guard in add_source(), the overlap skip in
register_default_sources() / enable_default_sources(), and the
first-source-wins deduplication in materialize_source_packages().
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from aam_cli.core.config import AamConfig, SourceEntry
from aam_cli.services.source_service import (
    _find_overlapping_source,
    _normalize_source_identity,
    add_source,
    enable_default_sources,
    materialize_source_packages,
    register_default_sources,
    ArtifactIndex,
    VirtualPackage,
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


def _make_config(sources: list[SourceEntry] | None = None) -> AamConfig:
    """Create a test AamConfig with optional sources."""
    return AamConfig(sources=sources or [])


def _make_source_entry(
    name: str = "openai/skills",
    url: str = "https://github.com/openai/skills",
    ref: str = "main",
    path: str = "",
    last_commit: str = "abc123",
) -> SourceEntry:
    """Create a test SourceEntry."""
    return SourceEntry(
        name=name,
        url=url,
        ref=ref,
        path=path,
        last_commit=last_commit,
        last_fetched="2026-02-08T10:00:00Z",
        artifact_count=5,
    )


def _make_virtual_package(
    name: str,
    source_name: str,
    qualified_name: str | None = None,
) -> VirtualPackage:
    """Create a minimal VirtualPackage for materialization tests."""
    return VirtualPackage(
        name=name,
        qualified_name=qualified_name or f"{source_name}/{name}",
        source_name=source_name,
        type="skill",
        path=f"skills/{name}",
        commit_sha="abc123",
        cache_dir="/tmp/cache",
        scan_path="",
        description=f"Test {name}",
    )


################################################################################
#                                                                              #
# _normalize_source_identity TESTS                                             #
#                                                                              #
################################################################################


class TestNormalizeSourceIdentity:
    """Tests for _normalize_source_identity()."""

    def test_unit_strips_dot_git_suffix(self) -> None:
        """Strips .git suffix from clone URL."""
        url, path = _normalize_source_identity(
            "https://github.com/org/repo.git", ""
        )
        assert url == "https://github.com/org/repo"

    def test_unit_lowercases_url(self) -> None:
        """Lowercases the full URL."""
        url, _path = _normalize_source_identity(
            "https://GitHub.com/Org/Repo", ""
        )
        assert url == "https://github.com/org/repo"

    def test_unit_strips_trailing_slash_from_url(self) -> None:
        """Strips trailing slashes from the URL."""
        url, _path = _normalize_source_identity(
            "https://github.com/org/repo/", ""
        )
        assert url == "https://github.com/org/repo"

    def test_unit_strips_surrounding_slashes_from_path(self) -> None:
        """Strips leading and trailing slashes from the path."""
        _url, path = _normalize_source_identity(
            "https://github.com/org/repo", "/skills/"
        )
        assert path == "skills"

    def test_unit_empty_path_stays_empty(self) -> None:
        """Empty path normalizes to empty string."""
        _url, path = _normalize_source_identity(
            "https://github.com/org/repo", ""
        )
        assert path == ""

    def test_unit_combined_normalization(self) -> None:
        """Full normalization: .git, case, trailing slash, path slashes."""
        url, path = _normalize_source_identity(
            "https://GitHub.com/Org/Repo.git/", "/skills/.curated/"
        )
        assert url == "https://github.com/org/repo"
        assert path == "skills/.curated"


################################################################################
#                                                                              #
# _find_overlapping_source TESTS                                               #
#                                                                              #
################################################################################


class TestFindOverlappingSource:
    """Tests for _find_overlapping_source()."""

    def test_unit_no_overlap_different_repo(self) -> None:
        """Different repos do not overlap."""
        existing = _make_source_entry(
            name="openai/skills",
            url="https://github.com/openai/skills",
            path="skills",
        )
        config = _make_config(sources=[existing])

        result = _find_overlapping_source(
            config, "https://github.com/anthropic/skills", "skills"
        )

        assert result is None

    def test_unit_exact_overlap_same_url_and_path(self) -> None:
        """Same repo URL and same path is a direct overlap."""
        existing = _make_source_entry(
            name="github/awesome-copilot",
            url="https://github.com/github/awesome-copilot",
            path="skills",
        )
        config = _make_config(sources=[existing])

        result = _find_overlapping_source(
            config, "https://github.com/github/awesome-copilot", "skills"
        )

        assert result is existing

    def test_unit_overlap_with_dot_git_suffix(self) -> None:
        """URL with .git suffix overlaps with URL without it."""
        existing = _make_source_entry(
            name="github/awesome-copilot",
            url="https://github.com/github/awesome-copilot",
            path="skills",
        )
        config = _make_config(sources=[existing])

        result = _find_overlapping_source(
            config, "https://github.com/github/awesome-copilot.git", "skills"
        )

        assert result is existing

    def test_unit_overlap_case_insensitive_url(self) -> None:
        """URL comparison is case-insensitive."""
        existing = _make_source_entry(
            name="github/awesome-copilot",
            url="https://github.com/GitHub/Awesome-Copilot",
            path="skills",
        )
        config = _make_config(sources=[existing])

        result = _find_overlapping_source(
            config, "https://github.com/github/awesome-copilot", "skills"
        )

        assert result is existing

    def test_unit_overlap_new_path_is_subdir_of_existing(self) -> None:
        """New source scanning a subdirectory of an existing source."""
        existing = _make_source_entry(
            name="github/awesome-copilot",
            url="https://github.com/github/awesome-copilot",
            path="skills",
        )
        config = _make_config(sources=[existing])

        result = _find_overlapping_source(
            config,
            "https://github.com/github/awesome-copilot",
            "skills/.curated",
        )

        assert result is existing

    def test_unit_overlap_existing_path_is_subdir_of_new(self) -> None:
        """Existing source is a subdirectory of the new source's scope."""
        existing = _make_source_entry(
            name="github/awesome-copilot:curated",
            url="https://github.com/github/awesome-copilot",
            path="skills/.curated",
        )
        config = _make_config(sources=[existing])

        result = _find_overlapping_source(
            config,
            "https://github.com/github/awesome-copilot",
            "skills",
        )

        assert result is existing

    def test_unit_no_overlap_disjoint_paths_same_repo(self) -> None:
        """Same repo but completely disjoint paths do not overlap."""
        existing = _make_source_entry(
            name="github/awesome-copilot:agents",
            url="https://github.com/github/awesome-copilot",
            path="agents",
        )
        config = _make_config(sources=[existing])

        result = _find_overlapping_source(
            config,
            "https://github.com/github/awesome-copilot",
            "skills",
        )

        assert result is None

    def test_unit_no_overlap_empty_config(self) -> None:
        """Empty config never overlaps."""
        config = _make_config(sources=[])

        result = _find_overlapping_source(
            config, "https://github.com/org/repo", "skills"
        )

        assert result is None

    def test_unit_overlap_both_empty_paths(self) -> None:
        """Same repo with both paths empty is an overlap (full repo scope)."""
        existing = _make_source_entry(
            name="org/repo",
            url="https://github.com/org/repo",
            path="",
        )
        config = _make_config(sources=[existing])

        result = _find_overlapping_source(
            config, "https://github.com/org/repo", ""
        )

        assert result is existing

    def test_unit_no_false_overlap_on_prefix_substring(self) -> None:
        """Path 'skills-extra' should NOT overlap with 'skills'."""
        existing = _make_source_entry(
            name="org/repo",
            url="https://github.com/org/repo",
            path="skills",
        )
        config = _make_config(sources=[existing])

        result = _find_overlapping_source(
            config, "https://github.com/org/repo", "skills-extra"
        )

        assert result is None


################################################################################
#                                                                              #
# add_source OVERLAP GUARD TESTS                                               #
#                                                                              #
################################################################################


class TestAddSourceOverlap:
    """Tests for the overlap guard in add_source()."""

    @patch("aam_cli.services.source_service.load_config")
    def test_unit_add_source_rejects_overlapping_source(
        self,
        mock_load: MagicMock,
    ) -> None:
        """Adding a source that overlaps an existing one raises ValueError."""
        existing = _make_source_entry(
            name="github/awesome-copilot",
            url="https://github.com/github/awesome-copilot",
            path="skills",
        )
        mock_load.return_value = _make_config(sources=[existing])

        with pytest.raises(ValueError, match="AAM_SOURCE_OVERLAP"):
            add_source(
                "https://github.com/github/awesome-copilot",
                path="skills",
                name="github/awesome-copilot:skills",
            )

    @patch("aam_cli.services.source_service.save_global_config")
    @patch("aam_cli.services.source_service.scan_directory")
    @patch("aam_cli.services.source_service.get_head_sha")
    @patch("aam_cli.services.source_service.clone_shallow")
    @patch("aam_cli.services.source_service.validate_cache")
    @patch("aam_cli.services.source_service.get_cache_dir")
    @patch("aam_cli.services.source_service.load_config")
    def test_unit_add_source_allows_disjoint_paths(
        self,
        mock_load: MagicMock,
        mock_cache_dir: MagicMock,
        mock_validate: MagicMock,
        mock_clone: MagicMock,
        mock_sha: MagicMock,
        mock_scan: MagicMock,
        mock_save: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Adding a source with a disjoint path on the same repo succeeds."""
        existing = _make_source_entry(
            name="github/awesome-copilot:agents",
            url="https://github.com/github/awesome-copilot",
            path="agents",
        )

        cache_dir = tmp_path / "cache"
        cache_dir.mkdir(parents=True)

        mock_load.return_value = _make_config(sources=[existing])
        mock_cache_dir.return_value = cache_dir
        mock_validate.return_value = False
        mock_clone.return_value = cache_dir
        mock_sha.return_value = "abc123def456"
        mock_scan.return_value = []

        result = add_source(
            "https://github.com/github/awesome-copilot",
            path="skills",
        )

        assert result["name"] == "github/awesome-copilot:skills"
        mock_save.assert_called_once()


################################################################################
#                                                                              #
# register_default_sources OVERLAP SKIP TESTS                                  #
#                                                                              #
################################################################################


class TestRegisterDefaultSourcesOverlap:
    """Tests for overlap skipping in register_default_sources()."""

    @patch("aam_cli.services.source_service.save_global_config")
    @patch("aam_cli.services.source_service.load_config")
    def test_unit_skips_default_overlapping_user_source(
        self,
        mock_load: MagicMock,
        mock_save: MagicMock,
    ) -> None:
        """A default is skipped when a user source covers the same repo+path."""
        user_source = _make_source_entry(
            name="my-awesome-copilot",
            url="https://github.com/github/awesome-copilot",
            path="skills",
        )
        mock_load.return_value = _make_config(sources=[user_source])

        result = register_default_sources()

        # "github/awesome-copilot" default has url=github/awesome-copilot
        # path=skills which overlaps with the user source
        assert "github/awesome-copilot" in result["skipped"]

    @patch("aam_cli.services.source_service.save_global_config")
    @patch("aam_cli.services.source_service.load_config")
    def test_unit_registers_non_overlapping_defaults(
        self,
        mock_load: MagicMock,
        mock_save: MagicMock,
    ) -> None:
        """Defaults that don't overlap with existing sources are registered."""
        user_source = _make_source_entry(
            name="my-custom-source",
            url="https://github.com/custom/repo",
            path="",
        )
        mock_load.return_value = _make_config(sources=[user_source])

        result = register_default_sources()

        # All 4 defaults should be registered since none overlap
        assert len(result["registered"]) > 0
        assert "my-custom-source" not in result["registered"]


################################################################################
#                                                                              #
# enable_default_sources OVERLAP SKIP TESTS                                    #
#                                                                              #
################################################################################


class TestEnableDefaultSourcesOverlap:
    """Tests for overlap skipping in enable_default_sources()."""

    @patch("aam_cli.services.source_service.save_global_config")
    @patch("aam_cli.services.source_service.load_config")
    def test_unit_skips_default_overlapping_user_source(
        self,
        mock_load: MagicMock,
        mock_save: MagicMock,
    ) -> None:
        """A default is skipped when enable finds overlap with user source."""
        user_source = _make_source_entry(
            name="my-awesome-copilot",
            url="https://github.com/github/awesome-copilot",
            path="skills",
        )
        mock_load.return_value = _make_config(sources=[user_source])

        result = enable_default_sources()

        assert "github/awesome-copilot" in result["skipped"]


################################################################################
#                                                                              #
# materialize_source_packages DEDUP TESTS                                      #
#                                                                              #
################################################################################


class TestMaterializeDeduplication:
    """Tests for first-source-wins dedup in materialize_source_packages()."""

    @patch("aam_cli.services.source_service._ensure_sources_registry_configured")
    @patch("aam_cli.services.source_service._publish_virtual_package_to_registry")
    @patch("aam_cli.services.source_service.build_source_index")
    @patch("aam_cli.registry.local.LocalRegistry.init_registry")
    @patch("aam_cli.utils.paths.get_sources_registry_dir")
    def test_unit_skips_duplicate_names_across_sources(
        self,
        mock_registry_dir: MagicMock,
        mock_init_registry: MagicMock,
        mock_build_index: MagicMock,
        mock_publish: MagicMock,
        mock_ensure: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Second source with the same artifact name is skipped."""
        registry_dir = tmp_path / "sources-registry"
        registry_dir.mkdir()
        mock_registry_dir.return_value = registry_dir
        mock_init_registry.return_value = MagicMock()

        # Two artifacts with the same unqualified name from different sources
        vp1 = _make_virtual_package("copilot-sdk", "microsoft/skills")
        vp2 = _make_virtual_package("copilot-sdk", "github/awesome-copilot")
        vp3 = _make_virtual_package("unique-skill", "openai/skills")

        index = ArtifactIndex(
            build_timestamp="2026-02-22T00:00:00Z",
            total_count=3,
            sources_indexed=3,
        )
        index.by_qualified_name = {
            vp1.qualified_name: vp1,
            vp2.qualified_name: vp2,
            vp3.qualified_name: vp3,
        }
        index.by_name = {
            "copilot-sdk": [vp1, vp2],
            "unique-skill": [vp3],
        }
        mock_build_index.return_value = index

        config = _make_config()
        result = materialize_source_packages(config)

        # 2 packages published (first copilot-sdk + unique-skill)
        assert result["packages_created"] == 2
        # 1 duplicate skipped (second copilot-sdk)
        assert result["skipped_duplicates"] == 1
        assert len(result["errors"]) == 0
        # publish called exactly twice (not three times)
        assert mock_publish.call_count == 2

    @patch("aam_cli.services.source_service._ensure_sources_registry_configured")
    @patch("aam_cli.services.source_service._publish_virtual_package_to_registry")
    @patch("aam_cli.services.source_service.build_source_index")
    @patch("aam_cli.registry.local.LocalRegistry.init_registry")
    @patch("aam_cli.utils.paths.get_sources_registry_dir")
    def test_unit_no_duplicates_all_unique(
        self,
        mock_registry_dir: MagicMock,
        mock_init_registry: MagicMock,
        mock_build_index: MagicMock,
        mock_publish: MagicMock,
        mock_ensure: MagicMock,
        tmp_path: Path,
    ) -> None:
        """All unique names result in zero skipped duplicates."""
        registry_dir = tmp_path / "sources-registry"
        registry_dir.mkdir()
        mock_registry_dir.return_value = registry_dir
        mock_init_registry.return_value = MagicMock()

        vp1 = _make_virtual_package("skill-a", "source-1")
        vp2 = _make_virtual_package("skill-b", "source-2")

        index = ArtifactIndex(
            build_timestamp="2026-02-22T00:00:00Z",
            total_count=2,
            sources_indexed=2,
        )
        index.by_qualified_name = {
            vp1.qualified_name: vp1,
            vp2.qualified_name: vp2,
        }
        mock_build_index.return_value = index

        config = _make_config()
        result = materialize_source_packages(config)

        assert result["packages_created"] == 2
        assert result["skipped_duplicates"] == 0
        assert mock_publish.call_count == 2

    @patch("aam_cli.services.source_service._ensure_sources_registry_configured")
    @patch("aam_cli.services.source_service._publish_virtual_package_to_registry")
    @patch("aam_cli.services.source_service.build_source_index")
    @patch("aam_cli.registry.local.LocalRegistry.init_registry")
    @patch("aam_cli.utils.paths.get_sources_registry_dir")
    def test_unit_publish_error_does_not_block_subsequent(
        self,
        mock_registry_dir: MagicMock,
        mock_init_registry: MagicMock,
        mock_build_index: MagicMock,
        mock_publish: MagicMock,
        mock_ensure: MagicMock,
        tmp_path: Path,
    ) -> None:
        """A publish error on one package does not prevent others."""
        registry_dir = tmp_path / "sources-registry"
        registry_dir.mkdir()
        mock_registry_dir.return_value = registry_dir
        mock_init_registry.return_value = MagicMock()

        vp1 = _make_virtual_package("broken-skill", "source-1")
        vp2 = _make_virtual_package("good-skill", "source-1")

        index = ArtifactIndex(
            build_timestamp="2026-02-22T00:00:00Z",
            total_count=2,
            sources_indexed=1,
        )
        index.by_qualified_name = {
            vp1.qualified_name: vp1,
            vp2.qualified_name: vp2,
        }
        mock_build_index.return_value = index

        mock_publish.side_effect = [
            FileNotFoundError("Source path not found"),
            None,
        ]

        config = _make_config()
        result = materialize_source_packages(config)

        assert result["packages_created"] == 1
        assert result["skipped_duplicates"] == 0
        assert len(result["errors"]) == 1
        assert "broken-skill" in result["errors"][0]
