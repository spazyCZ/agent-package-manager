"""Unit tests for MCP resources."""

import logging
from unittest.mock import patch

import pytest

from aam_cli.mcp.server import create_mcp_server
from fastmcp import Client

logger = logging.getLogger(__name__)


class TestMCPResources:

    def _run_async(self, coro):
        import asyncio
        return asyncio.run(coro)

    def test_unit_resource_config(self) -> None:
        mock_config = {"key": None, "value": {"default_platform": "cursor"}, "source": "merged"}
        with patch("aam_cli.mcp.resources.get_config", return_value=mock_config):
            server = create_mcp_server()
            async def check():
                async with Client(server) as client:
                    resources = await client.list_resources()
                    assert len(resources) >= 4
            self._run_async(check())

    def test_unit_resource_packages_installed(self) -> None:
        with patch("aam_cli.mcp.resources.list_installed_packages", return_value=[]):
            server = create_mcp_server()
            async def check():
                async with Client(server) as client:
                    result = await client.read_resource("aam://packages/installed")
                    assert result is not None
            self._run_async(check())

    def test_unit_resource_registries(self) -> None:
        with patch("aam_cli.mcp.resources.list_registries", return_value=[]):
            server = create_mcp_server()
            async def check():
                async with Client(server) as client:
                    result = await client.read_resource("aam://registries")
                    assert result is not None
            self._run_async(check())
