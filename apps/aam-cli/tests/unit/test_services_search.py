"""Unit tests for search service."""

import logging
from unittest.mock import MagicMock, patch

import pytest

from aam_cli.services.search_service import search_packages

logger = logging.getLogger(__name__)


class TestSearchService:

    def _make_config(self, registries=None):
        config = MagicMock()
        config.registries = registries or []
        return config

    def test_unit_search_no_registries(self) -> None:
        config = self._make_config(registries=[])
        result = search_packages("test", config)
        assert result == []

    def test_unit_search_single_registry(self) -> None:
        mock_entry = MagicMock()
        mock_entry.name = "test-pkg"
        mock_entry.latest = "1.0.0"
        mock_entry.description = "A test package"
        mock_entry.artifact_types = ["skill"]
        mock_entry.keywords = []

        mock_reg = MagicMock()
        mock_reg.search.return_value = [mock_entry]

        mock_source = MagicMock()
        mock_source.name = "local"

        with patch("aam_cli.services.search_service.create_registry", return_value=mock_reg):
            config = self._make_config(registries=[mock_source])
            result = search_packages("test", config)
            assert len(result) == 1
            assert result[0]["name"] == "test-pkg"

    def test_unit_search_with_limit(self) -> None:
        entries = []
        for i in range(5):
            e = MagicMock()
            e.name = f"pkg-{i}"
            e.latest = "1.0.0"
            e.description = f"Package {i}"
            e.artifact_types = ["skill"]
            entries.append(e)

        mock_reg = MagicMock()
        mock_reg.search.return_value = entries

        mock_source = MagicMock()
        mock_source.name = "local"

        with patch("aam_cli.services.search_service.create_registry", return_value=mock_reg):
            config = self._make_config(registries=[mock_source])
            result = search_packages("pkg", config, limit=3)
            assert len(result) == 3

    def test_unit_search_with_type_filter(self) -> None:
        skill_entry = MagicMock()
        skill_entry.name = "skill-pkg"
        skill_entry.latest = "1.0.0"
        skill_entry.description = "Skill"
        skill_entry.artifact_types = ["skill"]

        agent_entry = MagicMock()
        agent_entry.name = "agent-pkg"
        agent_entry.latest = "1.0.0"
        agent_entry.description = "Agent"
        agent_entry.artifact_types = ["agent"]

        mock_reg = MagicMock()
        mock_reg.search.return_value = [skill_entry, agent_entry]

        mock_source = MagicMock()
        mock_source.name = "local"

        with patch("aam_cli.services.search_service.create_registry", return_value=mock_reg):
            config = self._make_config(registries=[mock_source])
            result = search_packages("", config, package_type="skill")
            assert len(result) == 1
            assert result[0]["name"] == "skill-pkg"

    def test_unit_search_invalid_limit(self) -> None:
        config = self._make_config(registries=[])
        with pytest.raises(ValueError, match="AAM_INVALID_ARGUMENT"):
            search_packages("test", config, limit=0)
        with pytest.raises(ValueError, match="AAM_INVALID_ARGUMENT"):
            search_packages("test", config, limit=51)
