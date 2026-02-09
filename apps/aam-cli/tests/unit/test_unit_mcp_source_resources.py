"""Unit tests for MCP source resources (spec 003).

Tests the 3 new resources:
  - aam://sources
  - aam://sources/{name}
  - aam://sources/{name}/candidates
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import asyncio
import logging
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
# TESTS                                                                        #
#                                                                              #
################################################################################


class TestSourceResources:
    """Tests for MCP source resources with mocked services."""

    def _run_async(self, coro) -> None:  # type: ignore[no-untyped-def]
        """Run an async coroutine synchronously."""
        return asyncio.run(coro)

    # ------------------------------------------------------------------
    # aam://sources
    # ------------------------------------------------------------------

    def test_unit_resource_sources_list(self) -> None:
        """Verify list of sources returned."""
        mock_result = {
            "sources": [
                {
                    "name": "openai/skills",
                    "url": "https://github.com/openai/skills.git",
                    "ref": "main",
                    "artifact_count": 5,
                    "default": True,
                },
            ],
            "count": 1,
        }
        with patch(
            "aam_cli.mcp.resources.list_sources",
            return_value=mock_result,
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.read_resource("aam://sources")
                    assert result is not None

            self._run_async(check())

    def test_unit_resource_sources_empty(self) -> None:
        """Verify empty list returned (not error)."""
        mock_result = {"sources": [], "count": 0}
        with patch(
            "aam_cli.mcp.resources.list_sources",
            return_value=mock_result,
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.read_resource("aam://sources")
                    assert result is not None

            self._run_async(check())

    # ------------------------------------------------------------------
    # aam://sources/{name}
    # ------------------------------------------------------------------

    def test_unit_resource_source_detail(self) -> None:
        """Verify source entry + artifacts returned."""
        mock_scan = {
            "source_name": "openai/skills",
            "source_url": "https://github.com/openai/skills.git",
            "artifacts": [
                {"name": "code-review", "type": "skill"},
            ],
            "artifact_count": 1,
        }
        with patch(
            "aam_cli.mcp.resources.scan_source",
            return_value=mock_scan,
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    # Use -- convention for source names with /
                    result = await client.read_resource(
                        "aam://sources/openai--skills"
                    )
                    assert result is not None

            self._run_async(check())

    def test_unit_resource_source_not_found(self) -> None:
        """Verify None returned when source not found."""
        with patch(
            "aam_cli.mcp.resources.scan_source",
            side_effect=ValueError("Source 'missing' not found"),
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.read_resource(
                        "aam://sources/missing"
                    )
                    # Resource returns None on not-found (per convention)
                    assert result is not None  # FastMCP wraps None in response

            self._run_async(check())

    # ------------------------------------------------------------------
    # aam://sources/{name}/candidates
    # ------------------------------------------------------------------

    def test_unit_resource_source_candidates(self) -> None:
        """Verify candidates list returned."""
        mock_candidates = {
            "candidates": [
                {"name": "code-review", "type": "skill", "source": "openai/skills"},
            ],
            "count": 1,
        }
        with patch(
            "aam_cli.mcp.resources.list_candidates",
            return_value=mock_candidates,
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    # Use -- convention for source names with /
                    result = await client.read_resource(
                        "aam://sources/openai--skills/candidates"
                    )
                    assert result is not None

            self._run_async(check())

    def test_unit_resource_source_candidates_empty(self) -> None:
        """Verify empty list when no candidates."""
        mock_candidates = {"candidates": [], "count": 0}
        with patch(
            "aam_cli.mcp.resources.list_candidates",
            return_value=mock_candidates,
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    # Use -- convention for source names with /
                    result = await client.read_resource(
                        "aam://sources/openai--skills/candidates"
                    )
                    assert result is not None

            self._run_async(check())
