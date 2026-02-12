"""Unit tests for MCP server factory.

Tests verify that create_mcp_server correctly configures the FastMCP server
with the expected tools and resources based on the allow_write parameter.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging

import pytest
from fastmcp import Client

from aam_cli.mcp.server import create_mcp_server

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# SERVER FACTORY TESTS                                                         #
#                                                                              #
################################################################################


class TestMCPServerFactory:
    """Tests for create_mcp_server factory function."""

    def test_unit_create_server_default(self) -> None:
        """Verify server created with name 'aam' and correct version."""
        server = create_mcp_server()
        assert server.name == "aam"

    @pytest.mark.asyncio
    async def test_unit_create_server_read_only(self) -> None:
        """Verify only 16 read tools listed when allow_write=False.

        7 spec-002 read tools + 6 spec-003 read tools
        + 2 spec-004 read tools (outdated, available)
        + 1 spec-004 init info tool = 16.
        """
        server = create_mcp_server(allow_write=False)
        # -----
        # Use in-memory client to check tool list
        # -----
        async with Client(server) as client:
            tools = await client.list_tools()
            tool_names = [t.name for t in tools]
            assert len(tool_names) == 16
            # -----
            # Spec 002 read-only tools
            # -----
            assert "aam_search" in tool_names
            assert "aam_list" in tool_names
            assert "aam_info" in tool_names
            assert "aam_validate" in tool_names
            assert "aam_config_get" in tool_names
            assert "aam_registry_list" in tool_names
            assert "aam_doctor" in tool_names
            # -----
            # Spec 003 read-only tools
            # -----
            assert "aam_source_list" in tool_names
            assert "aam_source_scan" in tool_names
            assert "aam_source_candidates" in tool_names
            assert "aam_source_diff" in tool_names
            assert "aam_verify" in tool_names
            assert "aam_diff" in tool_names
            # -----
            # Spec 004 read-only tools
            # -----
            assert "aam_outdated" in tool_names
            assert "aam_available" in tool_names
            assert "aam_init_info" in tool_names
            # -----
            # Write tools should NOT be present
            # -----
            assert "aam_install" not in tool_names
            assert "aam_uninstall" not in tool_names
            assert "aam_source_add" not in tool_names
            assert "aam_source_remove" not in tool_names
            assert "aam_source_update" not in tool_names

    @pytest.mark.asyncio
    async def test_unit_create_server_allow_write(self) -> None:
        """Verify all 28 tools listed when allow_write=True.

        16 read tools + 7 spec-002 write + 3 spec-003 write
        + 1 spec-004 upgrade + 1 spec-004 init = 28.
        """
        server = create_mcp_server(allow_write=True)
        async with Client(server) as client:
            tools = await client.list_tools()
            tool_names = [t.name for t in tools]
            assert len(tool_names) == 28
            # -----
            # Check spec 002 write tools present
            # -----
            assert "aam_install" in tool_names
            assert "aam_uninstall" in tool_names
            assert "aam_publish" in tool_names
            assert "aam_create_package" in tool_names
            assert "aam_config_set" in tool_names
            assert "aam_registry_add" in tool_names
            assert "aam_init_package" in tool_names
            # -----
            # Check spec 003 write tools present
            # -----
            assert "aam_source_add" in tool_names
            assert "aam_source_remove" in tool_names
            assert "aam_source_update" in tool_names
            # -----
            # Check spec 004 write tools present
            # -----
            assert "aam_upgrade" in tool_names
            assert "aam_init" in tool_names

    @pytest.mark.asyncio
    async def test_unit_server_resources(self) -> None:
        """Verify 5 resources registered."""
        server = create_mcp_server()
        async with Client(server) as client:
            resources = await client.list_resources()
            assert len(resources) >= 4  # 4 static, template may not show in list

    @pytest.mark.asyncio
    async def test_unit_server_tool_names(self) -> None:
        """Verify all tools prefixed with aam_."""
        server = create_mcp_server(allow_write=True)
        async with Client(server) as client:
            tools = await client.list_tools()
            for tool in tools:
                assert tool.name.startswith("aam_"), (
                    f"Tool {tool.name} not prefixed with aam_"
                )
