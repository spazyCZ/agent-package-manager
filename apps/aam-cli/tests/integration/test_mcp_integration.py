"""Integration tests for MCP server with real filesystem.

Tests end-to-end flows using the FastMCP in-memory Client with
real local registries and filesystem operations.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import asyncio
import logging
from pathlib import Path
from unittest.mock import patch

from fastmcp import Client

from aam_cli.mcp.server import create_mcp_server
from aam_cli.services.validate_service import validate_package

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# HELPERS                                                                      #
#                                                                              #
################################################################################


def _run_async(coro):  # type: ignore[no-untyped-def]
    """Run an async coroutine synchronously."""
    return asyncio.run(coro)


################################################################################
#                                                                              #
# INTEGRATION TESTS                                                            #
#                                                                              #
################################################################################


class TestMCPIntegration:
    """Integration tests using real filesystem and MCP server."""

    def test_integration_validate_via_mcp(
        self,
        sample_package: Path,
    ) -> None:
        """Validate sample package via MCP tool."""
        server = create_mcp_server(allow_write=False)

        async def check() -> None:
            async with Client(server) as client:
                result = await client.call_tool(
                    "aam_validate",
                    {"path": str(sample_package)},
                )
                assert result is not None

        _run_async(check())

    def test_integration_safety_model_blocks_writes(self) -> None:
        """Read-only server should not list write tools."""
        server = create_mcp_server(allow_write=False)

        async def check() -> None:
            async with Client(server) as client:
                tools = await client.list_tools()
                tool_names = [t.name for t in tools]
                assert "aam_install" not in tool_names
                assert "aam_uninstall" not in tool_names

        _run_async(check())

    def test_integration_full_access_has_all_tools(self) -> None:
        """Full-access server should list all 29 tools (spec 002–005)."""
        server = create_mcp_server(allow_write=True)

        async def check() -> None:
            async with Client(server) as client:
                tools = await client.list_tools()
                assert len(tools) == 29

        _run_async(check())

    def test_integration_doctor_healthy(
        self,
        tmp_workspace: Path,
    ) -> None:
        """Doctor should report healthy on clean workspace."""
        server = create_mcp_server(allow_write=False)

        async def check() -> None:
            async with Client(server) as client:
                result = await client.call_tool("aam_doctor", {})
                assert result is not None

        _run_async(check())

    def test_integration_validate_sample_package(
        self,
        sample_package: Path,
    ) -> None:
        """Validate a real sample package through the service layer."""
        report = validate_package(sample_package)
        assert report["valid"] is True
        assert report["package_name"] == "sample-pkg"
        assert report["artifact_count"] == 1

    def test_integration_validate_missing_manifest(
        self,
        tmp_path: Path,
    ) -> None:
        """Validate directory without aam.yaml returns invalid report."""
        report = validate_package(tmp_path)
        assert report["valid"] is False
        assert len(report["errors"]) > 0

    def test_integration_detect_incomplete_install(
        self,
        tmp_workspace: Path,
    ) -> None:
        """Doctor detects leftover staging directories."""
        from aam_cli.services.doctor_service import run_diagnostics

        # -----
        # Create leftover staging directory
        # -----
        staging = tmp_workspace / ".aam" / ".tmp"
        staging.mkdir()
        (staging / "partial-pkg").mkdir()

        with patch(
            "aam_cli.services.doctor_service.get_packages_dir",
            return_value=tmp_workspace / ".aam" / "packages",
        ):
            report = run_diagnostics(tmp_workspace)

        incomplete_check = next(
            (c for c in report["checks"] if c["name"] == "incomplete_install"),
            None,
        )
        assert incomplete_check is not None
        assert incomplete_check["status"] == "warn"
        assert "partial-pkg" in incomplete_check["message"]
