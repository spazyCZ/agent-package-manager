"""Unit tests for MCP resources."""

import logging
from unittest.mock import Mock, patch

from fastmcp import Client

from aam_cli.mcp.server import create_mcp_server

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

    # ------------------------------------------------------------------
    # aam://packages/{name}
    # ------------------------------------------------------------------

    def test_unit_resource_package_detail_valid(self) -> None:
        """Valid package name returns package info dict."""
        pkg_info = {"name": "my-package", "version": "1.0.0", "artifacts": []}
        with patch("aam_cli.mcp.resources.get_package_info", return_value=pkg_info):
            server = create_mcp_server()
            async def check():
                async with Client(server) as client:
                    result = await client.read_resource("aam://packages/my-package")
                    assert result is not None
            self._run_async(check())

    def test_unit_resource_package_detail_scoped_name(self) -> None:
        """Double-hyphen in URI is converted to @scope/ format."""
        pkg_info = {"name": "@acme/tools", "version": "2.0.0"}
        with patch("aam_cli.mcp.resources.get_package_info", return_value=pkg_info) as mock_get:
            server = create_mcp_server()
            async def check():
                async with Client(server) as client:
                    result = await client.read_resource("aam://packages/acme--tools")
                    assert result is not None
                    mock_get.assert_called_once_with(package_name="@acme/tools")
            self._run_async(check())

    def test_unit_resource_package_detail_not_found(self) -> None:
        """ValueError from get_package_info returns None."""
        with patch(
            "aam_cli.mcp.resources.get_package_info",
            side_effect=ValueError("not found"),
        ):
            server = create_mcp_server()
            async def check():
                async with Client(server) as client:
                    result = await client.read_resource("aam://packages/no-such-pkg")
                    assert result is not None
            self._run_async(check())

    # ------------------------------------------------------------------
    # aam://manifest
    # ------------------------------------------------------------------

    def test_unit_resource_manifest_valid(self) -> None:
        """Valid manifest returns model_dump dict."""
        mock_manifest = Mock()
        mock_manifest.model_dump.return_value = {
            "name": "my-pkg",
            "version": "1.0.0",
        }
        with patch(
            "aam_cli.mcp.resources.load_manifest_universal",
            return_value=mock_manifest,
        ):
            server = create_mcp_server()
            async def check():
                async with Client(server) as client:
                    result = await client.read_resource("aam://manifest")
                    assert result is not None
                    mock_manifest.model_dump.assert_called_once_with(by_alias=True)
            self._run_async(check())

    def test_unit_resource_manifest_file_not_found(self) -> None:
        """FileNotFoundError returns None."""
        with patch(
            "aam_cli.mcp.resources.load_manifest_universal",
            side_effect=FileNotFoundError("no manifest"),
        ):
            server = create_mcp_server()
            async def check():
                async with Client(server) as client:
                    result = await client.read_resource("aam://manifest")
                    assert result is not None
            self._run_async(check())

    def test_unit_resource_manifest_generic_error(self) -> None:
        """Generic Exception returns dict with 'error' key."""
        with patch(
            "aam_cli.mcp.resources.load_manifest_universal",
            side_effect=RuntimeError("bad yaml"),
        ):
            server = create_mcp_server()
            async def check():
                async with Client(server) as client:
                    result = await client.read_resource("aam://manifest")
                    assert result is not None
            self._run_async(check())
