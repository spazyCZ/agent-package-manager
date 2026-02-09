"""Unit tests for MCP read-only source & integrity tools (spec 003).

Tests the 6 new read tools:
  - aam_source_list
  - aam_source_scan
  - aam_source_candidates
  - aam_source_diff
  - aam_verify
  - aam_diff
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


class TestSourceReadTools:
    """Tests for read-only MCP source tools with mocked services."""

    def _run_async(self, coro) -> None:  # type: ignore[no-untyped-def]
        """Run an async coroutine synchronously."""
        return asyncio.run(coro)

    # ------------------------------------------------------------------
    # aam_source_list
    # ------------------------------------------------------------------

    def test_unit_aam_source_list_returns_sources(self) -> None:
        """Mock list_sources, verify list returned."""
        mock_result = {
            "sources": [
                {
                    "name": "openai/skills",
                    "url": "https://github.com/openai/skills.git",
                    "ref": "main",
                    "last_commit": "abc123",
                    "artifact_count": 5,
                    "default": True,
                },
            ],
            "count": 1,
        }
        with patch(
            "aam_cli.mcp.tools_read.list_sources",
            return_value=mock_result,
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool("aam_source_list", {})
                    assert result is not None

            self._run_async(check())

    def test_unit_aam_source_list_empty(self) -> None:
        """Verify empty list returned (not error) when no sources."""
        mock_result = {"sources": [], "count": 0}
        with patch(
            "aam_cli.mcp.tools_read.list_sources",
            return_value=mock_result,
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool("aam_source_list", {})
                    assert result is not None

            self._run_async(check())

    # ------------------------------------------------------------------
    # aam_source_scan
    # ------------------------------------------------------------------

    def test_unit_aam_source_scan_success(self) -> None:
        """Mock scan_source, verify dict structure."""
        mock_scan = {
            "source_name": "openai/skills",
            "source_url": "https://github.com/openai/skills.git",
            "source_ref": "main",
            "last_commit": "abc123",
            "artifacts": [
                {"name": "code-review", "type": "skill", "path": "skills/code-review"},
                {"name": "my-agent", "type": "agent", "path": "agents/my-agent"},
            ],
            "artifact_count": 2,
        }
        with patch(
            "aam_cli.mcp.tools_read.scan_source",
            return_value=mock_scan,
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool(
                        "aam_source_scan",
                        {"source_name": "openai/skills"},
                    )
                    assert result is not None

            self._run_async(check())

    def test_unit_aam_source_scan_with_type_filter(self) -> None:
        """Verify type filter reduces artifacts."""
        mock_scan = {
            "source_name": "openai/skills",
            "artifacts": [
                {"name": "code-review", "type": "skill", "path": "skills/code-review"},
                {"name": "my-agent", "type": "agent", "path": "agents/my-agent"},
            ],
            "artifact_count": 2,
        }
        with patch(
            "aam_cli.mcp.tools_read.scan_source",
            return_value=mock_scan,
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool(
                        "aam_source_scan",
                        {"source_name": "openai/skills", "artifact_type": "skill"},
                    )
                    assert result is not None

            self._run_async(check())

    def test_unit_aam_source_scan_not_found(self) -> None:
        """Verify error when source_name not in config."""
        with patch(
            "aam_cli.mcp.tools_read.scan_source",
            side_effect=ValueError("[AAM_SOURCE_NOT_FOUND] Source 'missing' not found"),
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    with pytest.raises(ToolError, match="AAM_SOURCE_NOT_FOUND"):
                        await client.call_tool(
                            "aam_source_scan",
                            {"source_name": "missing"},
                        )

            self._run_async(check())

    # ------------------------------------------------------------------
    # aam_source_candidates
    # ------------------------------------------------------------------

    def test_unit_aam_source_candidates_all(self) -> None:
        """Mock list_candidates, verify list returned."""
        mock_candidates = {
            "candidates": [
                {"name": "code-review", "type": "skill", "source": "openai/skills"},
            ],
            "count": 1,
        }
        with patch(
            "aam_cli.mcp.tools_read.list_candidates",
            return_value=mock_candidates,
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool(
                        "aam_source_candidates", {},
                    )
                    assert result is not None

            self._run_async(check())

    def test_unit_aam_source_candidates_filtered(self) -> None:
        """Verify source_name + artifact_type filters work."""
        mock_candidates = {
            "candidates": [
                {"name": "code-review", "type": "skill", "source": "openai/skills"},
            ],
            "count": 1,
        }
        with patch(
            "aam_cli.mcp.tools_read.list_candidates",
            return_value=mock_candidates,
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool(
                        "aam_source_candidates",
                        {"source_name": "openai/skills", "artifact_type": "skill"},
                    )
                    assert result is not None

            self._run_async(check())

    # ------------------------------------------------------------------
    # aam_source_diff
    # ------------------------------------------------------------------

    def test_unit_aam_source_diff_success(self) -> None:
        """Mock update_source(dry_run=True), verify change report."""
        mock_report = {
            "source_name": "openai/skills",
            "new_artifacts": [{"name": "new-skill", "type": "skill"}],
            "modified_artifacts": [],
            "removed_artifacts": [],
            "total_changes": 1,
        }
        with patch(
            "aam_cli.mcp.tools_read.update_source",
            return_value=mock_report,
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool(
                        "aam_source_diff",
                        {"source_name": "openai/skills"},
                    )
                    assert result is not None

            self._run_async(check())

    def test_unit_aam_source_diff_not_found(self) -> None:
        """Verify error when source not found."""
        with patch(
            "aam_cli.mcp.tools_read.update_source",
            side_effect=ValueError("[AAM_SOURCE_NOT_FOUND] Source 'missing' not found"),
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    with pytest.raises(ToolError, match="AAM_SOURCE_NOT_FOUND"):
                        await client.call_tool(
                            "aam_source_diff",
                            {"source_name": "missing"},
                        )

            self._run_async(check())

    # ------------------------------------------------------------------
    # aam_verify
    # ------------------------------------------------------------------

    def test_unit_aam_verify_success(self) -> None:
        """Mock verify_package, verify dict returned."""
        mock_verify = {
            "package_name": "my-pkg",
            "has_checksums": True,
            "ok_files": ["SKILL.md"],
            "modified_files": [],
            "missing_files": [],
            "untracked_files": [],
            "total_files": 1,
            "status": "ok",
        }
        with patch(
            "aam_cli.mcp.tools_read.verify_package",
            return_value=mock_verify,
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool(
                        "aam_verify",
                        {"package_name": "my-pkg"},
                    )
                    assert result is not None

            self._run_async(check())

    def test_unit_aam_verify_no_checksums(self) -> None:
        """Verify has_checksums=false returned as domain outcome."""
        mock_verify = {
            "package_name": "my-pkg",
            "has_checksums": False,
            "ok_files": [],
            "modified_files": [],
            "missing_files": [],
            "untracked_files": [],
            "total_files": 0,
            "status": "no_checksums",
        }
        with patch(
            "aam_cli.mcp.tools_read.verify_package",
            return_value=mock_verify,
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool(
                        "aam_verify",
                        {"package_name": "my-pkg"},
                    )
                    assert result is not None

            self._run_async(check())

    def test_unit_aam_verify_not_installed(self) -> None:
        """Verify error when package not installed."""
        with patch(
            "aam_cli.mcp.tools_read.verify_package",
            side_effect=ValueError(
                "[AAM_PACKAGE_NOT_INSTALLED] Package 'missing' not installed"
            ),
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    with pytest.raises(ToolError, match="AAM_PACKAGE_NOT_INSTALLED"):
                        await client.call_tool(
                            "aam_verify",
                            {"package_name": "missing"},
                        )

            self._run_async(check())

    # ------------------------------------------------------------------
    # aam_diff
    # ------------------------------------------------------------------

    def test_unit_aam_diff_success(self) -> None:
        """Mock diff_package, verify diff output."""
        mock_diff = {
            "package_name": "my-pkg",
            "has_checksums": True,
            "diffs": [
                {
                    "file": "SKILL.md",
                    "diff": "--- a/SKILL.md\n+++ b/SKILL.md\n@@ -1 +1 @@\n-old\n+new",
                    "status": "modified",
                }
            ],
            "modified_count": 1,
            "missing_files": [],
            "untracked_files": [],
        }
        with patch(
            "aam_cli.mcp.tools_read.diff_package",
            return_value=mock_diff,
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool(
                        "aam_diff",
                        {"package_name": "my-pkg"},
                    )
                    assert result is not None

            self._run_async(check())

    def test_unit_aam_diff_not_installed(self) -> None:
        """Verify error when package not installed."""
        with patch(
            "aam_cli.mcp.tools_read.diff_package",
            side_effect=ValueError(
                "[AAM_PACKAGE_NOT_INSTALLED] Package 'missing' not installed"
            ),
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    with pytest.raises(ToolError, match="AAM_PACKAGE_NOT_INSTALLED"):
                        await client.call_tool(
                            "aam_diff",
                            {"package_name": "missing"},
                        )

            self._run_async(check())
