"""Unit tests for MCP read-only tools."""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import asyncio
import json
import logging
from typing import Any
from unittest.mock import patch

from fastmcp import Client

from aam_cli.mcp.server import create_mcp_server

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# HELPER: PARSE MCP RESULT                                                     #
#                                                                              #
################################################################################


def _parse_mcp_result(result: Any) -> Any:
    """Extract parsed data from the MCP call_tool result.

    FastMCP's ``Client.call_tool`` returns a ``CallToolResult``.
    We prefer parsing ``.content[0].text`` (plain JSON) because
    ``.data`` may contain Pydantic wrapper objects for list returns.
    Falls back to ``.data`` for empty collections or dict results.

    Args:
        result: Raw ``CallToolResult`` from ``client.call_tool``.

    Returns:
        Parsed data (dict or list) from the tool response.
    """
    content = getattr(result, "content", result)
    if isinstance(content, list) and len(content) > 0:
        item = content[0]
        if hasattr(item, "text"):
            return json.loads(item.text)

    if hasattr(result, "data") and result.data is not None:
        data = result.data
        if isinstance(data, (dict, list)):
            return data

    return {}


################################################################################
#                                                                              #
# TESTS                                                                        #
#                                                                              #
################################################################################


class TestReadTools:
    """Tests for read-only MCP tools with mocked services."""

    def _run_async(self, coro):  # type: ignore[no-untyped-def]
        """Run an async coroutine synchronously."""
        return asyncio.run(coro)

    def test_unit_aam_search_returns_results(self) -> None:
        """Mock search_service, verify tool returns dict with results."""
        from aam_cli.services.search_service import SearchResponse, SearchResult

        mock_response = SearchResponse(
            results=[
                SearchResult(
                    name="test-pkg",
                    version="1.0.0",
                    description="Test",
                    artifact_types=["skill"],
                    origin="local",
                    origin_type="registry",
                    score=80,
                )
            ],
            total_count=1,
            warnings=[],
            all_names=[],
        )
        with (
            patch(
                "aam_cli.mcp.tools_read.search_packages",
                return_value=mock_response,
            ),
            patch("aam_cli.mcp.tools_read.load_config"),
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool(
                        "aam_search", {"query": "test"}
                    )
                    assert result is not None
                    data = _parse_mcp_result(result)
                    assert "results" in data
                    assert "total_count" in data
                    assert data["total_count"] == 1
                    assert len(data["results"]) == 1
                    assert data["results"][0]["name"] == "test-pkg"

            self._run_async(check())

    def test_unit_aam_search_empty_query(self) -> None:
        """Verify empty results returned for empty query."""
        from aam_cli.services.search_service import SearchResponse

        mock_response = SearchResponse(
            results=[],
            total_count=0,
            warnings=[],
            all_names=[],
        )
        with (
            patch(
                "aam_cli.mcp.tools_read.search_packages",
                return_value=mock_response,
            ),
            patch("aam_cli.mcp.tools_read.load_config"),
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool(
                        "aam_search", {"query": ""}
                    )
                    assert result is not None
                    data = _parse_mcp_result(result)
                    assert "results" in data
                    assert data["total_count"] == 0
                    assert data["results"] == []

            self._run_async(check())

    def test_unit_aam_search_new_params(self) -> None:
        """Verify new search parameters (package_types, source_filter, etc.)."""
        from aam_cli.services.search_service import SearchResponse, SearchResult

        mock_response = SearchResponse(
            results=[
                SearchResult(
                    name="skill-pkg",
                    version="1.0.0",
                    description="A skill",
                    artifact_types=["skill"],
                    origin="local",
                    origin_type="registry",
                    score=100,
                )
            ],
            total_count=1,
            warnings=[],
            all_names=[],
        )
        with (
            patch(
                "aam_cli.mcp.tools_read.search_packages",
                return_value=mock_response,
            ),
            patch("aam_cli.mcp.tools_read.load_config"),
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool(
                        "aam_search",
                        {
                            "query": "skill",
                            "package_types": ["skill"],
                            "sort_by": "name",
                        },
                    )
                    assert result is not None
                    data = _parse_mcp_result(result)
                    assert data["total_count"] == 1
                    assert data["results"][0]["name"] == "skill-pkg"

            self._run_async(check())

    def test_unit_aam_search_response_structure(self) -> None:
        """Verify response has results, total_count, warnings keys."""
        from aam_cli.services.search_service import SearchResponse, SearchResult

        mock_response = SearchResponse(
            results=[
                SearchResult(
                    name="test-pkg",
                    version="1.0.0",
                    description="Test",
                    artifact_types=["skill"],
                    origin="local",
                    origin_type="registry",
                    score=80,
                )
            ],
            total_count=1,
            warnings=["Test warning"],
            all_names=[],
        )
        with (
            patch(
                "aam_cli.mcp.tools_read.search_packages",
                return_value=mock_response,
            ),
            patch("aam_cli.mcp.tools_read.load_config"),
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool(
                        "aam_search", {"query": "test"}
                    )
                    assert result is not None
                    data = _parse_mcp_result(result)
                    assert "results" in data
                    assert "total_count" in data
                    assert "warnings" in data
                    assert data["warnings"] == ["Test warning"]

            self._run_async(check())

    def test_unit_aam_list_no_workspace(self) -> None:
        """Verify empty list (not error) when no workspace."""
        with patch(
            "aam_cli.mcp.tools_read.list_installed_packages",
            return_value=[],
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool("aam_list", {})
                    assert result is not None
                    data = _parse_mcp_result(result)
                    assert isinstance(data, list)
                    assert len(data) == 0

            self._run_async(check())

    def test_unit_aam_info_package_found(self) -> None:
        """Mock package_service, verify detail dict."""
        mock_info = {
            "name": "test-pkg",
            "version": "1.0.0",
            "description": "Test",
            "author": None,
            "license": None,
            "repository": None,
            "homepage": None,
            "keywords": [],
            "artifacts": {},
            "dependencies": {},
            "platforms": {},
            "installed": True,
            "installed_version": "1.0.0",
        }
        with patch(
            "aam_cli.mcp.tools_read.get_package_info",
            return_value=mock_info,
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool(
                        "aam_info", {"package_name": "test-pkg"}
                    )
                    assert result is not None
                    data = _parse_mcp_result(result)
                    assert isinstance(data, dict)
                    assert data["name"] == "test-pkg"
                    assert data["version"] == "1.0.0"
                    assert data["installed"] is True

            self._run_async(check())

    def test_unit_aam_validate_valid_package(self) -> None:
        """Mock validate_service, verify report."""
        mock_report = {
            "valid": True,
            "package_name": "test",
            "package_version": "1.0.0",
            "errors": [],
            "warnings": [],
            "artifact_count": 2,
            "artifacts_valid": True,
        }
        with patch(
            "aam_cli.mcp.tools_read.validate_package",
            return_value=mock_report,
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool(
                        "aam_validate", {"path": "."}
                    )
                    assert result is not None
                    data = _parse_mcp_result(result)
                    assert isinstance(data, dict)
                    assert data["valid"] is True
                    assert data["errors"] == []

            self._run_async(check())

    def test_unit_aam_config_get_all(self) -> None:
        """Mock config_service, verify full config returned."""
        mock_config = {
            "key": None,
            "value": {"default_platform": "cursor"},
            "source": "merged",
        }
        with patch(
            "aam_cli.mcp.tools_read.get_config",
            return_value=mock_config,
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool("aam_config_get", {})
                    assert result is not None
                    data = _parse_mcp_result(result)
                    assert isinstance(data, dict)
                    assert data["source"] == "merged"
                    assert "value" in data

            self._run_async(check())

    def test_unit_aam_registry_list(self) -> None:
        """Mock registry_service, verify list returned."""
        mock_registries = [
            {
                "name": "local",
                "url": "file:///tmp",
                "type": "local",
                "is_default": True,
                "accessible": True,
            }
        ]
        with patch(
            "aam_cli.mcp.tools_read.list_registries",
            return_value=mock_registries,
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool("aam_registry_list", {})
                    assert result is not None
                    data = _parse_mcp_result(result)
                    assert isinstance(data, list)
                    assert len(data) == 1
                    assert data[0]["name"] == "local"
                    assert data[0]["is_default"] is True

            self._run_async(check())

    def test_unit_aam_doctor(self) -> None:
        """Mock doctor_service, verify report returned."""
        mock_report = {
            "healthy": True,
            "checks": [],
            "summary": "All good",
        }
        with patch(
            "aam_cli.mcp.tools_read.run_diagnostics",
            return_value=mock_report,
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool("aam_doctor", {})
                    assert result is not None
                    data = _parse_mcp_result(result)
                    assert isinstance(data, dict)
                    assert data["healthy"] is True
                    assert data["summary"] == "All good"

            self._run_async(check())
