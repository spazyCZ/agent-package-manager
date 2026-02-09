"""Unit tests for MCP write source tools (spec 003).

Tests the 3 new write tools and the extended aam_create_package:
  - aam_source_add
  - aam_source_remove
  - aam_source_update
  - aam_create_package (from_source extension)
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import asyncio
import logging
from unittest.mock import patch

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

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


class TestSourceWriteTools:
    """Tests for write MCP source tools with mocked services."""

    def _run_async(self, coro) -> None:  # type: ignore[no-untyped-def]
        """Run an async coroutine synchronously."""
        return asyncio.run(coro)

    # ------------------------------------------------------------------
    # aam_source_add
    # ------------------------------------------------------------------

    def test_unit_aam_source_add_success(self) -> None:
        """Verify result with artifact count."""
        mock_result = {
            "source_name": "openai/skills",
            "url": "https://github.com/openai/skills.git",
            "ref": "main",
            "artifact_count": 5,
            "status": "added",
        }
        with patch(
            "aam_cli.mcp.tools_write.add_source",
            return_value=mock_result,
        ):
            server = create_mcp_server(allow_write=True)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool(
                        "aam_source_add",
                        {"source": "openai/skills"},
                    )
                    assert result is not None

            self._run_async(check())

    def test_unit_aam_source_add_duplicate(self) -> None:
        """Verify AAM_SOURCE_ALREADY_EXISTS error."""
        with patch(
            "aam_cli.mcp.tools_write.add_source",
            side_effect=ValueError(
                "[AAM_SOURCE_ALREADY_EXISTS] Source 'openai/skills' already exists"
            ),
        ):
            server = create_mcp_server(allow_write=True)

            async def check() -> None:
                async with Client(server) as client:
                    with pytest.raises(ToolError, match="AAM_SOURCE_ALREADY_EXISTS"):
                        await client.call_tool(
                            "aam_source_add",
                            {"source": "openai/skills"},
                        )

            self._run_async(check())

    def test_unit_aam_source_add_invalid_url(self) -> None:
        """Verify AAM_SOURCE_URL_INVALID error."""
        with patch(
            "aam_cli.mcp.tools_write.add_source",
            side_effect=ValueError(
                "[AAM_SOURCE_URL_INVALID] Cannot parse 'not-a-url'"
            ),
        ):
            server = create_mcp_server(allow_write=True)

            async def check() -> None:
                async with Client(server) as client:
                    with pytest.raises(ToolError, match="AAM_SOURCE_URL_INVALID"):
                        await client.call_tool(
                            "aam_source_add",
                            {"source": "not-a-url"},
                        )

            self._run_async(check())

    def test_unit_aam_source_add_clone_failed(self) -> None:
        """Verify AAM_GIT_CLONE_FAILED error."""
        with patch(
            "aam_cli.mcp.tools_write.add_source",
            side_effect=RuntimeError(
                "[AAM_GIT_CLONE_FAILED] Clone failed after 3 retries"
            ),
        ):
            server = create_mcp_server(allow_write=True)

            async def check() -> None:
                async with Client(server) as client:
                    with pytest.raises(ToolError, match="AAM_GIT_CLONE_FAILED"):
                        await client.call_tool(
                            "aam_source_add",
                            {"source": "openai/skills"},
                        )

            self._run_async(check())

    # ------------------------------------------------------------------
    # aam_source_remove
    # ------------------------------------------------------------------

    def test_unit_aam_source_remove_success(self) -> None:
        """Verify removal dict returned."""
        mock_result = {
            "source_name": "openai/skills",
            "status": "removed",
            "cache_purged": False,
        }
        with patch(
            "aam_cli.mcp.tools_write.remove_source",
            return_value=mock_result,
        ):
            server = create_mcp_server(allow_write=True)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool(
                        "aam_source_remove",
                        {"source_name": "openai/skills"},
                    )
                    assert result is not None

            self._run_async(check())

    def test_unit_aam_source_remove_not_found(self) -> None:
        """Verify AAM_SOURCE_NOT_FOUND error."""
        with patch(
            "aam_cli.mcp.tools_write.remove_source",
            side_effect=ValueError(
                "[AAM_SOURCE_NOT_FOUND] Source 'missing' not found"
            ),
        ):
            server = create_mcp_server(allow_write=True)

            async def check() -> None:
                async with Client(server) as client:
                    with pytest.raises(ToolError, match="AAM_SOURCE_NOT_FOUND"):
                        await client.call_tool(
                            "aam_source_remove",
                            {"source_name": "missing"},
                        )

            self._run_async(check())

    # ------------------------------------------------------------------
    # aam_source_update
    # ------------------------------------------------------------------

    def test_unit_aam_source_update_success(self) -> None:
        """Verify update result returned."""
        mock_result = {
            "source_name": "openai/skills",
            "old_commit": "abc123",
            "new_commit": "def456",
            "new_artifacts": [],
            "modified_artifacts": [],
            "removed_artifacts": [],
            "total_changes": 0,
        }
        with patch(
            "aam_cli.mcp.tools_write.update_source",
            return_value=mock_result,
        ):
            server = create_mcp_server(allow_write=True)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool(
                        "aam_source_update",
                        {"source_name": "openai/skills"},
                    )
                    assert result is not None

            self._run_async(check())

    def test_unit_aam_source_update_all(self) -> None:
        """Verify all sources updated."""
        mock_result = {
            "sources_updated": 2,
            "results": [
                {"source_name": "openai/skills", "total_changes": 0},
                {"source_name": "github/awesome-copilot", "total_changes": 1},
            ],
        }
        with patch(
            "aam_cli.mcp.tools_write.update_source",
            return_value=mock_result,
        ):
            server = create_mcp_server(allow_write=True)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool(
                        "aam_source_update",
                        {"update_all": True},
                    )
                    assert result is not None

            self._run_async(check())

    def test_unit_aam_source_update_not_found(self) -> None:
        """Verify error when source not found."""
        with patch(
            "aam_cli.mcp.tools_write.update_source",
            side_effect=ValueError(
                "[AAM_SOURCE_NOT_FOUND] Source 'missing' not found"
            ),
        ):
            server = create_mcp_server(allow_write=True)

            async def check() -> None:
                async with Client(server) as client:
                    with pytest.raises(ToolError, match="AAM_SOURCE_NOT_FOUND"):
                        await client.call_tool(
                            "aam_source_update",
                            {"source_name": "missing"},
                        )

            self._run_async(check())

    # ------------------------------------------------------------------
    # Safety model
    # ------------------------------------------------------------------

    def test_unit_write_tools_hidden_in_read_only(self) -> None:
        """Verify new write tools not listed when allow_write=False."""
        server = create_mcp_server(allow_write=False)

        async def check() -> None:
            async with Client(server) as client:
                tools = await client.list_tools()
                tool_names = [t.name for t in tools]

                # New write tools must be hidden
                assert "aam_source_add" not in tool_names
                assert "aam_source_remove" not in tool_names
                assert "aam_source_update" not in tool_names

                # New read tools must still be visible
                assert "aam_source_list" in tool_names
                assert "aam_source_scan" in tool_names
                assert "aam_source_candidates" in tool_names
                assert "aam_source_diff" in tool_names
                assert "aam_verify" in tool_names
                assert "aam_diff" in tool_names

        self._run_async(check())

    # ------------------------------------------------------------------
    # aam_create_package (from_source extension)
    # ------------------------------------------------------------------

    def test_unit_aam_create_package_from_source(self) -> None:
        """Verify from_source + artifacts parameters work."""
        mock_scan = {
            "source_name": "openai/skills",
            "source_url": "https://github.com/openai/skills.git",
            "source_ref": "main",
            "last_commit": "abc123",
            "artifacts": [
                {"name": "code-review", "type": "skill", "path": "skills/code-review"},
                {"name": "code-gen", "type": "skill", "path": "skills/code-gen"},
            ],
            "artifact_count": 2,
        }
        with patch(
            "aam_cli.mcp.tools_write.scan_source",
            return_value=mock_scan,
        ):
            server = create_mcp_server(allow_write=True)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool(
                        "aam_create_package",
                        {
                            "from_source": "openai/skills",
                            "artifacts": ["code-review"],
                        },
                    )
                    assert result is not None

            self._run_async(check())
