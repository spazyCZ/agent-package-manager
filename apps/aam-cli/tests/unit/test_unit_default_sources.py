"""Unit tests for default source registration and enable-defaults command.

Tests the register_default_sources() and enable_default_sources()
functions that manage the 4 curated community skill sources.

Reference: tasks.md T062–T064 (Phase 11).
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from unittest.mock import MagicMock, patch

from aam_cli.core.config import AamConfig, SourceEntry
from aam_cli.services.source_service import (
    DEFAULT_SOURCES,
    enable_default_sources,
    register_default_sources,
)

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# TESTS: register_default_sources()                                            #
#                                                                              #
################################################################################


class TestRegisterDefaultSources:
    """Tests for source_service.register_default_sources()."""

    @patch("aam_cli.services.source_service.save_global_config")
    @patch("aam_cli.services.source_service.load_config")
    def test_unit_registers_defaults_on_empty_config(
        self,
        mock_load: MagicMock,
        mock_save: MagicMock,
    ) -> None:
        """Registers all defaults when config has no sources."""
        mock_load.return_value = AamConfig()

        result = register_default_sources()

        assert len(result["registered"]) == len(DEFAULT_SOURCES)
        assert len(result["skipped"]) == 0
        mock_save.assert_called_once()

        # Verify sources were added to config
        saved_config = mock_save.call_args[0][0]
        assert len(saved_config.sources) == len(DEFAULT_SOURCES)
        for source in saved_config.sources:
            assert source.default is True

    @patch("aam_cli.services.source_service.save_global_config")
    @patch("aam_cli.services.source_service.load_config")
    def test_unit_skips_existing_sources(
        self,
        mock_load: MagicMock,
        _mock_save: MagicMock,
    ) -> None:
        """Skips sources that are already registered."""
        existing = SourceEntry(
            name=DEFAULT_SOURCES[0]["name"],
            url=DEFAULT_SOURCES[0]["url"],
            ref="main",
        )
        config = AamConfig(sources=[existing])
        mock_load.return_value = config

        result = register_default_sources()

        assert DEFAULT_SOURCES[0]["name"] in result["skipped"]
        # Only the remaining defaults should be registered
        assert len(result["registered"]) == len(DEFAULT_SOURCES) - 1

    @patch("aam_cli.services.source_service.save_global_config")
    @patch("aam_cli.services.source_service.load_config")
    def test_unit_skips_removed_defaults(
        self,
        mock_load: MagicMock,
        _mock_save: MagicMock,
    ) -> None:
        """Skips sources that user previously removed."""
        config = AamConfig(
            removed_defaults=[DEFAULT_SOURCES[0]["name"]],
        )
        mock_load.return_value = config

        result = register_default_sources()

        assert DEFAULT_SOURCES[0]["name"] in result["skipped"]
        assert len(result["registered"]) == len(DEFAULT_SOURCES) - 1

    @patch("aam_cli.services.source_service.save_global_config")
    @patch("aam_cli.services.source_service.load_config")
    def test_unit_no_save_when_nothing_registered(
        self,
        mock_load: MagicMock,
        mock_save: MagicMock,
    ) -> None:
        """Does not save config when all defaults are skipped."""
        removed = [d["name"] for d in DEFAULT_SOURCES]
        config = AamConfig(removed_defaults=removed)
        mock_load.return_value = config

        result = register_default_sources()

        assert len(result["registered"]) == 0
        assert len(result["skipped"]) == len(DEFAULT_SOURCES)
        mock_save.assert_not_called()

    def test_unit_default_sources_constant_has_five_entries(self) -> None:
        """DEFAULT_SOURCES list contains exactly 5 curated sources."""
        assert len(DEFAULT_SOURCES) == 5

    def test_unit_default_sources_constant_valid(self) -> None:
        """DEFAULT_SOURCES list has required fields."""
        for source in DEFAULT_SOURCES:
            assert "name" in source
            assert "url" in source
            assert "ref" in source

    def test_unit_default_sources_have_unique_names(self) -> None:
        """All default sources have unique names."""
        names = [d["name"] for d in DEFAULT_SOURCES]
        assert len(names) == len(set(names))


################################################################################
#                                                                              #
# TESTS: enable_default_sources()                                             #
#                                                                              #
################################################################################


class TestEnableDefaultSources:
    """Tests for source_service.enable_default_sources()."""

    @patch("aam_cli.services.source_service.save_global_config")
    @patch("aam_cli.services.source_service.load_config")
    def test_unit_enables_all_defaults_on_empty_config(
        self,
        mock_load: MagicMock,
        mock_save: MagicMock,
    ) -> None:
        """Enables all 5 defaults when config has no sources."""
        mock_load.return_value = AamConfig()

        result = enable_default_sources()

        assert len(result["registered"]) == 5
        assert len(result["skipped"]) == 0
        assert len(result["re_enabled"]) == 0
        assert result["total"] == 5
        mock_save.assert_called_once()

        # -----
        # Verify all sources were persisted with default=True
        # -----
        saved_config = mock_save.call_args[0][0]
        assert len(saved_config.sources) == 5
        for source in saved_config.sources:
            assert source.default is True

    @patch("aam_cli.services.source_service.save_global_config")
    @patch("aam_cli.services.source_service.load_config")
    def test_unit_skips_already_configured_sources(
        self,
        mock_load: MagicMock,
        mock_save: MagicMock,
    ) -> None:
        """Skips sources already in the config."""
        existing = SourceEntry(
            name=DEFAULT_SOURCES[0]["name"],
            url=DEFAULT_SOURCES[0]["url"],
            ref="main",
        )
        config = AamConfig(sources=[existing])
        mock_load.return_value = config

        result = enable_default_sources()

        assert DEFAULT_SOURCES[0]["name"] in result["skipped"]
        assert len(result["registered"]) == 4
        assert result["total"] == 5
        mock_save.assert_called_once()

    @patch("aam_cli.services.source_service.save_global_config")
    @patch("aam_cli.services.source_service.load_config")
    def test_unit_re_enables_previously_removed_defaults(
        self,
        mock_load: MagicMock,
        mock_save: MagicMock,
    ) -> None:
        """Re-enables sources that were previously removed by the user."""
        removed_name = DEFAULT_SOURCES[0]["name"]
        config = AamConfig(removed_defaults=[removed_name])
        mock_load.return_value = config

        result = enable_default_sources()

        # -----
        # The removed source should be re-enabled
        # -----
        assert removed_name in result["re_enabled"]
        assert removed_name in result["registered"]
        assert len(result["registered"]) == 5

        # -----
        # removed_defaults should be cleared for this source
        # -----
        saved_config = mock_save.call_args[0][0]
        assert removed_name not in saved_config.removed_defaults

    @patch("aam_cli.services.source_service.save_global_config")
    @patch("aam_cli.services.source_service.load_config")
    def test_unit_no_save_when_all_already_present(
        self,
        mock_load: MagicMock,
        mock_save: MagicMock,
    ) -> None:
        """Does not save when all 5 defaults are already configured."""
        existing_sources = [
            SourceEntry(
                name=d["name"],
                url=d["url"],
                ref=d["ref"],
                path=d.get("path", ""),
                default=True,
            )
            for d in DEFAULT_SOURCES
        ]
        config = AamConfig(sources=existing_sources)
        mock_load.return_value = config

        result = enable_default_sources()

        assert len(result["registered"]) == 0
        assert len(result["skipped"]) == 5
        assert result["total"] == 5
        mock_save.assert_not_called()

    @patch("aam_cli.services.source_service.save_global_config")
    @patch("aam_cli.services.source_service.load_config")
    def test_unit_re_enables_all_removed_defaults(
        self,
        mock_load: MagicMock,
        mock_save: MagicMock,
    ) -> None:
        """Re-enables all defaults when all were previously removed."""
        all_removed = [d["name"] for d in DEFAULT_SOURCES]
        config = AamConfig(removed_defaults=all_removed)
        mock_load.return_value = config

        result = enable_default_sources()

        assert len(result["registered"]) == 5
        assert len(result["re_enabled"]) == 5
        assert len(result["skipped"]) == 0
        mock_save.assert_called_once()

        # -----
        # All removed_defaults should be cleared
        # -----
        saved_config = mock_save.call_args[0][0]
        assert len(saved_config.removed_defaults) == 0
