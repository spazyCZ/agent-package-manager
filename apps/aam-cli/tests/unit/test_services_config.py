"""Unit tests for config service."""

import logging
from unittest.mock import MagicMock, patch

import pytest

from aam_cli.services.config_service import get_config, set_config, list_config

logger = logging.getLogger(__name__)


class TestConfigService:

    def test_unit_get_config_all(self) -> None:
        mock_cfg = MagicMock()
        mock_cfg.model_dump.return_value = {"default_platform": "cursor", "registries": []}
        with patch("aam_cli.services.config_service.load_config", return_value=mock_cfg):
            result = get_config(key=None)
            assert result["key"] is None
            assert result["source"] == "merged"
            assert "default_platform" in result["value"]

    def test_unit_get_config_key(self) -> None:
        mock_cfg = MagicMock()
        mock_cfg.default_platform = "cursor"
        with patch("aam_cli.services.config_service.load_config", return_value=mock_cfg):
            result = get_config(key="default_platform")
            assert result["key"] == "default_platform"
            assert result["value"] == "cursor"

    def test_unit_set_config(self) -> None:
        mock_cfg = MagicMock()
        mock_cfg.default_platform = "cursor"
        with patch("aam_cli.services.config_service.load_config", return_value=mock_cfg):
            with patch("aam_cli.services.config_service.save_global_config"):
                result = set_config(key="default_platform", value="vscode")
                assert result["key"] == "default_platform"
                assert result["value"] == "vscode"
