"""Unit tests for default source registration.

Tests the register_default_sources() function that pre-populates
the source list during ``aam init``.

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
# TESTS                                                                        #
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
        # Only the second default should be registered
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

    def test_unit_default_sources_constant_valid(self) -> None:
        """DEFAULT_SOURCES list has required fields."""
        assert len(DEFAULT_SOURCES) >= 1
        for source in DEFAULT_SOURCES:
            assert "name" in source
            assert "url" in source
            assert "ref" in source
