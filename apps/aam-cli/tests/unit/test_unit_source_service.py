"""Unit tests for source management service.

Tests add, scan, update, list, remove, and candidates operations
with mocked git_service and scanner dependencies.

Reference: tasks.md T028, T033, T038, T042.
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
from aam_cli.detection.scanner import DetectedArtifact
from aam_cli.services.source_service import (
    add_source,
    list_sources,
    remove_source,
    scan_source,
    update_source,
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


def _make_detected_artifacts() -> list[DetectedArtifact]:
    """Create sample DetectedArtifact instances."""
    return [
        DetectedArtifact(
            name="gh-fix-ci",
            type="skill",
            source_path=Path("skills/gh-fix-ci"),
            description="Fix CI skill",
        ),
        DetectedArtifact(
            name="playwright",
            type="skill",
            source_path=Path("skills/playwright"),
            description="Playwright testing",
        ),
        DetectedArtifact(
            name="my-agent",
            type="agent",
            source_path=Path("agents/my-agent"),
            description="Test agent",
        ),
    ]


################################################################################
#                                                                              #
# ADD SOURCE TESTS                                                             #
#                                                                              #
################################################################################


class TestAddSource:
    """Tests for source_service.add_source()."""

    @patch("aam_cli.services.source_service.save_global_config")
    @patch("aam_cli.services.source_service.scan_directory")
    @patch("aam_cli.services.source_service.get_head_sha")
    @patch("aam_cli.services.source_service.clone_shallow")
    @patch("aam_cli.services.source_service.validate_cache")
    @patch("aam_cli.services.source_service.get_cache_dir")
    @patch("aam_cli.services.source_service.load_config")
    def test_unit_add_source_success(
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
        """Successfully adds a new source."""
        # Ensure cache dir exists so _scan_cached_source finds it
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir(parents=True)

        mock_load.return_value = _make_config()
        mock_cache_dir.return_value = cache_dir
        mock_validate.return_value = False
        mock_clone.return_value = cache_dir
        mock_sha.return_value = "abc123def456"
        mock_scan.return_value = _make_detected_artifacts()

        result = add_source("openai/skills")

        assert result["name"] == "openai/skills"
        assert result["artifact_count"] == 3
        assert result["artifacts_by_type"]["skills"] == 2
        assert result["artifacts_by_type"]["agents"] == 1
        mock_save.assert_called_once()

    @patch("aam_cli.services.source_service.load_config")
    def test_unit_add_source_duplicate_raises(
        self, mock_load: MagicMock
    ) -> None:
        """Adding a duplicate source name raises ValueError."""
        existing = _make_source_entry()
        mock_load.return_value = _make_config(sources=[existing])

        with pytest.raises(ValueError, match="AAM_SOURCE_ALREADY_EXISTS"):
            add_source("openai/skills")


################################################################################
#                                                                              #
# SCAN SOURCE TESTS                                                            #
#                                                                              #
################################################################################


class TestScanSource:
    """Tests for source_service.scan_source()."""

    @patch("aam_cli.services.source_service.scan_directory")
    @patch("aam_cli.services.source_service.get_head_sha")
    @patch("aam_cli.services.source_service.validate_cache")
    @patch("aam_cli.services.source_service.get_cache_dir")
    @patch("aam_cli.services.source_service.load_config")
    def test_unit_scan_source_success(
        self,
        mock_load: MagicMock,
        mock_cache_dir: MagicMock,
        mock_validate: MagicMock,
        mock_sha: MagicMock,
        mock_scan: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Successfully scans a registered source."""
        # Ensure cache dir exists so _scan_cached_source finds it
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir(parents=True)

        source = _make_source_entry()
        mock_load.return_value = _make_config(sources=[source])
        mock_cache_dir.return_value = cache_dir
        mock_validate.return_value = True
        mock_sha.return_value = "abc123"
        mock_scan.return_value = _make_detected_artifacts()

        result = scan_source("openai/skills")

        assert result["source_name"] == "openai/skills"
        assert result["total_count"] == 3
        assert len(result["artifacts"]) == 3

    @patch("aam_cli.services.source_service.load_config")
    def test_unit_scan_source_not_found_raises(
        self, mock_load: MagicMock
    ) -> None:
        """Scanning a non-existent source raises ValueError."""
        mock_load.return_value = _make_config()

        with pytest.raises(ValueError, match="AAM_SOURCE_NOT_FOUND"):
            scan_source("nonexistent/source")


################################################################################
#                                                                              #
# UPDATE SOURCE TESTS                                                          #
#                                                                              #
################################################################################


class TestUpdateSource:
    """Tests for source_service.update_source()."""

    @patch("aam_cli.services.source_service.save_global_config")
    @patch("aam_cli.services.source_service.scan_directory")
    @patch("aam_cli.services.source_service.get_head_sha")
    @patch("aam_cli.services.source_service.validate_cache")
    @patch("aam_cli.services.source_service.fetch")
    @patch("aam_cli.services.source_service.get_cache_dir")
    @patch("aam_cli.services.source_service.load_config")
    def test_unit_update_no_changes(
        self,
        mock_load: MagicMock,
        mock_cache_dir: MagicMock,
        _mock_fetch: MagicMock,
        mock_validate: MagicMock,
        mock_sha: MagicMock,
        mock_scan: MagicMock,
        _mock_save: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Update with no new commits reports no changes."""
        source = _make_source_entry(last_commit="abc123")
        mock_load.return_value = _make_config(sources=[source])
        mock_cache_dir.return_value = tmp_path / "cache"
        mock_validate.return_value = True
        mock_sha.return_value = "abc123"  # Same commit
        mock_scan.return_value = _make_detected_artifacts()

        result = update_source("openai/skills")

        assert len(result["reports"]) == 1
        assert result["reports"][0]["has_changes"] is False

    @patch("aam_cli.services.source_service.load_config")
    def test_unit_update_source_not_found_raises(
        self, mock_load: MagicMock
    ) -> None:
        """Updating a non-existent source raises ValueError."""
        mock_load.return_value = _make_config()

        with pytest.raises(ValueError, match="AAM_SOURCE_NOT_FOUND"):
            update_source("nonexistent")

    def test_unit_update_requires_name_or_all(self) -> None:
        """Must specify source_name or update_all=True."""
        with pytest.raises(ValueError, match="AAM_INVALID_ARGUMENT"):
            update_source(source_name=None, update_all=False)


################################################################################
#                                                                              #
# LIST / REMOVE TESTS                                                          #
#                                                                              #
################################################################################


class TestListSources:
    """Tests for source_service.list_sources()."""

    @patch("aam_cli.services.source_service.load_config")
    def test_unit_list_empty(self, mock_load: MagicMock) -> None:
        """List with no sources returns empty list."""
        mock_load.return_value = _make_config()

        result = list_sources()

        assert result["count"] == 0
        assert result["sources"] == []

    @patch("aam_cli.services.source_service.load_config")
    def test_unit_list_with_sources(self, mock_load: MagicMock) -> None:
        """List returns all configured sources."""
        sources = [
            _make_source_entry("src1", "https://github.com/a/b"),
            _make_source_entry("src2", "https://github.com/c/d"),
        ]
        mock_load.return_value = _make_config(sources=sources)

        result = list_sources()

        assert result["count"] == 2
        assert result["sources"][0]["name"] == "src1"
        assert result["sources"][1]["name"] == "src2"


class TestRemoveSource:
    """Tests for source_service.remove_source()."""

    @patch("aam_cli.services.source_service.save_global_config")
    @patch("aam_cli.services.source_service.load_config")
    def test_unit_remove_source_success(
        self, mock_load: MagicMock, mock_save: MagicMock
    ) -> None:
        """Successfully removes a source from config."""
        source = _make_source_entry()
        mock_load.return_value = _make_config(sources=[source])

        result = remove_source("openai/skills")

        assert result["removed"] is True
        mock_save.assert_called_once()

    @patch("aam_cli.services.source_service.load_config")
    def test_unit_remove_not_found_raises(
        self, mock_load: MagicMock
    ) -> None:
        """Removing a non-existent source raises ValueError."""
        mock_load.return_value = _make_config()

        with pytest.raises(ValueError, match="AAM_SOURCE_NOT_FOUND"):
            remove_source("nonexistent")

    @patch("aam_cli.services.source_service.save_global_config")
    @patch("aam_cli.services.source_service.load_config")
    def test_unit_remove_default_tracks_in_removed_defaults(
        self, mock_load: MagicMock, _mock_save: MagicMock
    ) -> None:
        """Removing a default source adds it to removed_defaults."""
        source = _make_source_entry()
        source.default = True
        config = _make_config(sources=[source])
        mock_load.return_value = config

        remove_source("openai/skills")

        assert "openai/skills" in config.removed_defaults
