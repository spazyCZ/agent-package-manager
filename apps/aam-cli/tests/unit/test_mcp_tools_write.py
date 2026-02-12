"""Unit tests for MCP write tools."""

import logging
from unittest.mock import patch

import pytest

from aam_cli.mcp.server import create_mcp_server
from fastmcp import Client

logger = logging.getLogger(__name__)


class TestWriteTools:
    """Tests for write MCP tools with mocked services."""

    def _run_async(self, coro):
        import asyncio
        return asyncio.run(coro)

    def test_unit_aam_install_success(self) -> None:
        """Mock install_service, verify result dict."""
        mock_result = {
            "installed": [{"name": "test-pkg", "version": "1.0.0"}],
            "already_installed": [],
            "failed": [],
            "dependencies_resolved": 1
        }
        with patch("aam_cli.mcp.tools_write.install_packages", return_value=mock_result):
            with patch("aam_cli.mcp.tools_write.load_config"):
                server = create_mcp_server(allow_write=True)
                async def check():
                    async with Client(server) as client:
                        result = await client.call_tool("aam_install", {"packages": ["test-pkg"]})
                        assert result is not None
                self._run_async(check())

    def test_unit_aam_uninstall_success(self) -> None:
        """Mock package_service, verify result."""
        mock_result = {
            "package_name": "test-pkg", "version": "1.0.0",
            "files_removed": 3, "dependents_warning": []
        }
        with patch("aam_cli.mcp.tools_write.uninstall_package", return_value=mock_result):
            server = create_mcp_server(allow_write=True)
            async def check():
                async with Client(server) as client:
                    result = await client.call_tool("aam_uninstall", {"package_name": "test-pkg"})
                    assert result is not None
            self._run_async(check())

    def test_unit_aam_publish_success(self) -> None:
        """Mock publish_service, verify result."""
        mock_result = {
            "package_name": "test-pkg", "version": "1.0.0",
            "registry": "local", "archive_size": 1024, "checksum": "abc123"
        }
        with patch("aam_cli.mcp.tools_write.publish_package", return_value=mock_result):
            server = create_mcp_server(allow_write=True)
            async def check():
                async with Client(server) as client:
                    result = await client.call_tool("aam_publish", {})
                    assert result is not None
            self._run_async(check())

    def test_unit_aam_create_package_success(self) -> None:
        """Mock package_service, verify result."""
        mock_result = {
            "manifest_path": "/tmp/aam.yaml", "package_name": "test",
            "version": "1.0.0", "artifacts_included": {"skills": 1}, "total_artifacts": 1
        }
        with patch("aam_cli.mcp.tools_write.create_package", return_value=mock_result):
            server = create_mcp_server(allow_write=True)
            async def check():
                async with Client(server) as client:
                    result = await client.call_tool("aam_create_package", {"path": "."})
                    assert result is not None
            self._run_async(check())

    def test_unit_aam_config_set_success(self) -> None:
        """Mock config_service, verify updated value."""
        mock_result = {"key": "default_platform", "value": "cursor", "source": "global"}
        with patch("aam_cli.mcp.tools_write.set_config", return_value=mock_result):
            server = create_mcp_server(allow_write=True)
            async def check():
                async with Client(server) as client:
                    result = await client.call_tool("aam_config_set", {"key": "default_platform", "value": "cursor"})
                    assert result is not None
            self._run_async(check())

    def test_unit_aam_registry_add_success(self) -> None:
        """Mock registry_service, verify result."""
        mock_result = {
            "name": "new-reg", "url": "file:///tmp/reg",
            "type": "local", "is_default": False, "accessible": None
        }
        with patch("aam_cli.mcp.tools_write.add_registry", return_value=mock_result):
            server = create_mcp_server(allow_write=True)
            async def check():
                async with Client(server) as client:
                    result = await client.call_tool("aam_registry_add", {"name": "new-reg", "url": "file:///tmp/reg"})
                    assert result is not None
            self._run_async(check())

    def test_unit_aam_init_package_success(self) -> None:
        """Mock init_service, verify result."""
        mock_result = {
            "package_name": "new-pkg",
            "package_dir": "/tmp/new-pkg",
            "manifest_path": "/tmp/new-pkg/aam.yaml",
            "artifact_types": ["skills", "agents", "prompts", "instructions"],
            "platforms": ["cursor"],
            "directories_created": ["/tmp/new-pkg", "/tmp/new-pkg/skills"],
        }
        with patch("aam_cli.mcp.tools_write.init_package", return_value=mock_result):
            server = create_mcp_server(allow_write=True)
            async def check():
                async with Client(server) as client:
                    result = await client.call_tool(
                        "aam_init_package", {"name": "new-pkg"}
                    )
                    assert result is not None
            self._run_async(check())

    def test_unit_write_tools_hidden_in_read_only(self) -> None:
        """Verify write tools not listed when allow_write=False."""
        server = create_mcp_server(allow_write=False)
        async def check():
            async with Client(server) as client:
                tools = await client.list_tools()
                tool_names = [t.name for t in tools]
                assert "aam_install" not in tool_names
                assert "aam_uninstall" not in tool_names
                assert "aam_publish" not in tool_names
                assert "aam_create_package" not in tool_names
                assert "aam_config_set" not in tool_names
                assert "aam_registry_add" not in tool_names
                assert "aam_init_package" not in tool_names
        self._run_async(check())
