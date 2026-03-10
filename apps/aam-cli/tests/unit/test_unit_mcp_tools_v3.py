"""Unit tests for MCP tools v3 — client-level testing through FastMCP Client.

Tests all previously-untested MCP tools by calling them through the MCP
client protocol, mocking service functions at the module boundary level.

Covers:
  - Read tools: aam_outdated, aam_available, aam_tree, aam_why, aam_check,
    aam_audit
  - Write tools: aam_upgrade, aam_test, aam_eval, aam_cache_clean
  - Error boundary: ValueError → structured error dict,
    FileNotFoundError → FILE_NOT_FOUND error code
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import asyncio
import json
import logging
from typing import Any
from unittest.mock import Mock, patch

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


def _parse_mcp_result(result: Any) -> dict[str, Any]:
    """Extract a dict from the MCP call_tool result.

    FastMCP's ``Client.call_tool`` returns a ``CallToolResult`` with a
    ``.data`` attribute containing the deserialized tool return value.
    Falls back to parsing ``.content[0].text`` if ``.data`` is absent.

    Args:
        result: Raw ``CallToolResult`` from ``client.call_tool``.

    Returns:
        Parsed dict from the tool response.
    """
    # -----
    # Prefer .data (structured_content) when available
    # -----
    if hasattr(result, "data") and isinstance(result.data, dict):
        return result.data

    # -----
    # Fallback: parse JSON from .content list
    # -----
    content = getattr(result, "content", result)
    if isinstance(content, list) and len(content) > 0:
        item = content[0]
        if hasattr(item, "text"):
            return json.loads(item.text)

    return {}


################################################################################
#                                                                              #
# MOCK DATA CONSTANTS                                                          #
#                                                                              #
################################################################################

_OUTDATED_DICT: dict[str, Any] = {
    "outdated": [
        {"name": "pkg-a", "installed_sha": "abc123", "latest_sha": "def456"}
    ],
    "up_to_date": [],
    "no_source": [],
    "stale_sources": [],
    "total_outdated": 1,
}

_AVAILABLE_DICT: dict[str, Any] = {
    "by_source": {"community": [{"name": "pkg-a", "type": "skill"}]},
    "total_count": 1,
    "sources_indexed": 1,
}

_TREE_DICT: dict[str, Any] = {
    "tree": [{"name": "pkg-a", "version": "1.0.0", "children": []}],
    "total_packages": 1,
    "lock_file": "package.agent.lock",
}

_WHY_DICT: dict[str, Any] = {
    "package_name": "pkg-a",
    "found": True,
    "is_direct": True,
    "version": "1.0.0",
    "required_by": [{"name": "root", "constraint": ">=1.0.0"}],
}

_CHECK_DICT: dict[str, Any] = {
    "check_type": "packages",
    "results": [{"name": "pkg-a", "present": True, "status": "ok"}],
    "all_passed": True,
    "total": 1,
}

_AUDIT_DICT: dict[str, Any] = {
    "findings": [
        {"package": "pkg-a", "severity": "info", "detail": "No integrity hash"}
    ],
    "total_checked": 1,
    "findings_count": 1,
    "severity_filter": "all",
}

_UPGRADE_DICT: dict[str, Any] = {
    "upgraded": [
        {"name": "pkg-a", "from_sha": "abc123", "to_sha": "def456"}
    ],
    "skipped": [],
    "failed": [],
    "total_upgraded": 1,
}

_TEST_SUITE_DICT: dict[str, Any] = {
    "skill": "test-skill",
    "passed": 3,
    "failed": 0,
    "total": 3,
    "cases": [],
}

_EVAL_SUITE_DICT: dict[str, Any] = {
    "skill": "test-skill",
    "engine": "claude-code",
    "passed": 2,
    "failed": 0,
    "total": 2,
    "cases": [],
}


def _make_suite_mock(suite_dict: dict[str, Any]) -> Mock:
    """Create a Mock object with a ``to_dict`` method returning *suite_dict*.

    Args:
        suite_dict: The dict that ``to_dict()`` should return.

    Returns:
        Mock with configured ``to_dict``.
    """
    m = Mock()
    m.to_dict.return_value = suite_dict
    return m


################################################################################
#                                                                              #
# TEST: aam_outdated (read)                                                    #
#                                                                              #
################################################################################


class TestAamOutdatedMcp:
    """Tests for the aam_outdated MCP tool via FastMCP Client."""

    def _run_async(self, coro: Any) -> Any:
        """Run an async coroutine synchronously."""
        return asyncio.run(coro)

    def test_unit_aam_outdated_happy_path(self) -> None:
        """aam_outdated returns outdated packages count through MCP."""
        mock_result = Mock()
        mock_result.to_dict.return_value = _OUTDATED_DICT

        with (
            patch(
                "aam_cli.mcp.tools_read.check_outdated",
                return_value=mock_result,
            ),
            patch("aam_cli.mcp.tools_read.load_config"),
            patch(
                "aam_cli.mcp.tools_read.read_lock_file",
                return_value={},
            ),
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool("aam_outdated", {})
                    assert result is not None
                    data = _parse_mcp_result(result)
                    assert data["total_outdated"] == 1

            self._run_async(check())

    def test_unit_aam_outdated_response_structure(self) -> None:
        """aam_outdated response contains outdated and total_outdated keys."""
        mock_result = Mock()
        mock_result.to_dict.return_value = _OUTDATED_DICT

        with (
            patch(
                "aam_cli.mcp.tools_read.check_outdated",
                return_value=mock_result,
            ),
            patch("aam_cli.mcp.tools_read.load_config"),
            patch(
                "aam_cli.mcp.tools_read.read_lock_file",
                return_value={},
            ),
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool("aam_outdated", {})
                    data = _parse_mcp_result(result)
                    assert "outdated" in data
                    assert "total_outdated" in data

            self._run_async(check())


################################################################################
#                                                                              #
# TEST: aam_available (read)                                                   #
#                                                                              #
################################################################################


class TestAamAvailableMcp:
    """Tests for the aam_available MCP tool via FastMCP Client."""

    def _run_async(self, coro: Any) -> Any:
        """Run an async coroutine synchronously."""
        return asyncio.run(coro)

    def test_unit_aam_available_happy_path(self) -> None:
        """aam_available returns available artifacts from configured sources."""
        with (
            patch(
                "aam_cli.mcp.tools_read.list_available",
                return_value=_AVAILABLE_DICT,
            ),
            patch("aam_cli.mcp.tools_read.load_config"),
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool("aam_available", {})
                    assert result is not None
                    data = _parse_mcp_result(result)
                    assert data["total_count"] == 1

            self._run_async(check())

    def test_unit_aam_available_response_structure(self) -> None:
        """aam_available response contains by_source and total_count keys."""
        with (
            patch(
                "aam_cli.mcp.tools_read.list_available",
                return_value=_AVAILABLE_DICT,
            ),
            patch("aam_cli.mcp.tools_read.load_config"),
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool("aam_available", {})
                    data = _parse_mcp_result(result)
                    assert "by_source" in data
                    assert "total_count" in data

            self._run_async(check())


################################################################################
#                                                                              #
# TEST: aam_tree (read)                                                        #
#                                                                              #
################################################################################


class TestAamTreeMcp:
    """Tests for the aam_tree MCP tool via FastMCP Client."""

    def _run_async(self, coro: Any) -> Any:
        """Run an async coroutine synchronously."""
        return asyncio.run(coro)

    def test_unit_aam_tree_happy_path(self) -> None:
        """aam_tree returns dependency tree through MCP client."""
        with patch(
            "aam_cli.mcp.tools_read.get_tree",
            return_value=_TREE_DICT,
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool(
                        "aam_tree", {"depth": 0, "project": "."}
                    )
                    assert result is not None
                    data = _parse_mcp_result(result)
                    assert data["total_packages"] == 1

            self._run_async(check())

    def test_unit_aam_tree_response_structure(self) -> None:
        """aam_tree response contains tree and total_packages keys."""
        with patch(
            "aam_cli.mcp.tools_read.get_tree",
            return_value=_TREE_DICT,
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool(
                        "aam_tree", {"depth": 0, "project": "."}
                    )
                    data = _parse_mcp_result(result)
                    assert "tree" in data
                    assert "total_packages" in data

            self._run_async(check())


################################################################################
#                                                                              #
# TEST: aam_why (read)                                                         #
#                                                                              #
################################################################################


class TestAamWhyMcp:
    """Tests for the aam_why MCP tool via FastMCP Client."""

    def _run_async(self, coro: Any) -> Any:
        """Run an async coroutine synchronously."""
        return asyncio.run(coro)

    def test_unit_aam_why_happy_path(self) -> None:
        """aam_why returns dependency trace for a package."""
        with patch(
            "aam_cli.mcp.tools_read.get_why",
            return_value=_WHY_DICT,
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool(
                        "aam_why",
                        {"package_name": "pkg-a", "project": "."},
                    )
                    assert result is not None
                    data = _parse_mcp_result(result)
                    assert data["package_name"] == "pkg-a"
                    assert data["found"] is True

            self._run_async(check())

    def test_unit_aam_why_response_structure(self) -> None:
        """aam_why response contains required_by key."""
        with patch(
            "aam_cli.mcp.tools_read.get_why",
            return_value=_WHY_DICT,
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool(
                        "aam_why",
                        {"package_name": "pkg-a", "project": "."},
                    )
                    data = _parse_mcp_result(result)
                    assert "required_by" in data
                    assert isinstance(data["required_by"], list)

            self._run_async(check())


################################################################################
#                                                                              #
# TEST: aam_check (read)                                                       #
#                                                                              #
################################################################################


class TestAamCheckMcp:
    """Tests for the aam_check MCP tool via FastMCP Client."""

    def _run_async(self, coro: Any) -> Any:
        """Run an async coroutine synchronously."""
        return asyncio.run(coro)

    def test_unit_aam_check_happy_path(self) -> None:
        """aam_check returns package check results through MCP client."""
        with patch(
            "aam_cli.mcp.tools_read.check_deps",
            return_value=_CHECK_DICT,
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool(
                        "aam_check",
                        {"system_only": False, "project": "."},
                    )
                    assert result is not None
                    data = _parse_mcp_result(result)
                    assert data["all_passed"] is True

            self._run_async(check())

    def test_unit_aam_check_response_structure(self) -> None:
        """aam_check response contains all_passed key."""
        with patch(
            "aam_cli.mcp.tools_read.check_deps",
            return_value=_CHECK_DICT,
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool(
                        "aam_check",
                        {"system_only": False, "project": "."},
                    )
                    data = _parse_mcp_result(result)
                    assert "all_passed" in data
                    assert "check_type" in data
                    assert "results" in data

            self._run_async(check())


################################################################################
#                                                                              #
# TEST: aam_audit (read)                                                       #
#                                                                              #
################################################################################


class TestAamAuditMcp:
    """Tests for the aam_audit MCP tool via FastMCP Client."""

    def _run_async(self, coro: Any) -> Any:
        """Run an async coroutine synchronously."""
        return asyncio.run(coro)

    def test_unit_aam_audit_happy_path(self) -> None:
        """aam_audit returns integrity findings through MCP client."""
        with patch(
            "aam_cli.mcp.tools_read.audit_deps",
            return_value=_AUDIT_DICT,
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool(
                        "aam_audit",
                        {"severity": "all", "project": "."},
                    )
                    assert result is not None
                    data = _parse_mcp_result(result)
                    assert data["findings_count"] == 1

            self._run_async(check())

    def test_unit_aam_audit_response_structure(self) -> None:
        """aam_audit response contains findings key."""
        with patch(
            "aam_cli.mcp.tools_read.audit_deps",
            return_value=_AUDIT_DICT,
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool(
                        "aam_audit",
                        {"severity": "all", "project": "."},
                    )
                    data = _parse_mcp_result(result)
                    assert "findings" in data
                    assert isinstance(data["findings"], list)

            self._run_async(check())


################################################################################
#                                                                              #
# TEST: aam_upgrade (write)                                                    #
#                                                                              #
################################################################################


class TestAamUpgradeMcp:
    """Tests for the aam_upgrade MCP tool via FastMCP Client."""

    def _run_async(self, coro: Any) -> Any:
        """Run an async coroutine synchronously."""
        return asyncio.run(coro)

    def test_unit_aam_upgrade_happy_path(self) -> None:
        """aam_upgrade returns upgraded packages through MCP client."""
        with patch(
            "aam_cli.mcp.tools_write.run_upgrade",
            return_value=_UPGRADE_DICT,
        ):
            server = create_mcp_server(allow_write=True)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool(
                        "aam_upgrade",
                        {"dry_run": False, "force": False},
                    )
                    assert result is not None
                    data = _parse_mcp_result(result)
                    assert data["total_upgraded"] == 1

            self._run_async(check())

    def test_unit_aam_upgrade_response_structure(self) -> None:
        """aam_upgrade response contains upgraded and total_upgraded keys."""
        with patch(
            "aam_cli.mcp.tools_write.run_upgrade",
            return_value=_UPGRADE_DICT,
        ):
            server = create_mcp_server(allow_write=True)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool(
                        "aam_upgrade",
                        {"dry_run": True},
                    )
                    data = _parse_mcp_result(result)
                    assert "upgraded" in data
                    assert "total_upgraded" in data

            self._run_async(check())


################################################################################
#                                                                              #
# TEST: aam_test (write)                                                       #
#                                                                              #
################################################################################


class TestAamTestMcp:
    """Tests for the aam_test MCP tool via FastMCP Client."""

    def _run_async(self, coro: Any) -> Any:
        """Run an async coroutine synchronously."""
        return asyncio.run(coro)

    def test_unit_aam_test_happy_path(self) -> None:
        """aam_test returns skill test suites through MCP client."""
        mock_suite = _make_suite_mock(_TEST_SUITE_DICT)

        with patch(
            "aam_cli.mcp.tools_write.run_skill_tests",
            return_value=[mock_suite],
        ):
            server = create_mcp_server(allow_write=True)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool("aam_test", {})
                    assert result is not None
                    data = _parse_mcp_result(result)
                    assert len(data["suites"]) == 1
                    assert data["suites"][0]["passed"] == 3

            self._run_async(check())

    def test_unit_aam_test_response_structure(self) -> None:
        """aam_test response is a dict with suites key."""
        mock_suite = _make_suite_mock(_TEST_SUITE_DICT)

        with patch(
            "aam_cli.mcp.tools_write.run_skill_tests",
            return_value=[mock_suite],
        ):
            server = create_mcp_server(allow_write=True)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool("aam_test", {})
                    data = _parse_mcp_result(result)
                    assert isinstance(data, dict)
                    assert "suites" in data
                    assert isinstance(data["suites"], list)

            self._run_async(check())


################################################################################
#                                                                              #
# TEST: aam_eval (write)                                                       #
#                                                                              #
################################################################################


class TestAamEvalMcp:
    """Tests for the aam_eval MCP tool via FastMCP Client."""

    def _run_async(self, coro: Any) -> Any:
        """Run an async coroutine synchronously."""
        return asyncio.run(coro)

    def test_unit_aam_eval_happy_path(self) -> None:
        """aam_eval returns evaluation suites through MCP client."""
        mock_suite = _make_suite_mock(_EVAL_SUITE_DICT)

        with patch(
            "aam_cli.mcp.tools_write.run_evals",
            return_value=[mock_suite],
        ):
            server = create_mcp_server(allow_write=True)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool(
                        "aam_eval",
                        {"dry_run": True},
                    )
                    assert result is not None
                    data = _parse_mcp_result(result)
                    assert len(data["suites"]) == 1
                    assert data["suites"][0]["engine"] == "claude-code"

            self._run_async(check())

    def test_unit_aam_eval_response_structure(self) -> None:
        """aam_eval response is a dict with suites key."""
        mock_suite = _make_suite_mock(_EVAL_SUITE_DICT)

        with patch(
            "aam_cli.mcp.tools_write.run_evals",
            return_value=[mock_suite],
        ):
            server = create_mcp_server(allow_write=True)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool(
                        "aam_eval",
                        {"dry_run": True},
                    )
                    data = _parse_mcp_result(result)
                    assert isinstance(data, dict)
                    assert "suites" in data
                    assert isinstance(data["suites"], list)

            self._run_async(check())


################################################################################
#                                                                              #
# TEST: aam_cache_clean (write)                                                #
#                                                                              #
################################################################################


class TestAamCacheCleanMcp:
    """Tests for the aam_cache_clean MCP tool via FastMCP Client."""

    def _run_async(self, coro: Any) -> Any:
        """Run an async coroutine synchronously."""
        return asyncio.run(coro)

    def test_unit_aam_cache_clean_happy_path(self) -> None:
        """aam_cache_clean removes all cached packages through MCP client."""
        mock_cache = Mock()
        mock_cache.clean.return_value = 5

        with patch(
            "aam_cli.mcp.tools_write.cache_service",
            mock_cache,
        ):
            server = create_mcp_server(allow_write=True)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool(
                        "aam_cache_clean", {}
                    )
                    assert result is not None
                    data = _parse_mcp_result(result)
                    assert data["removed"] == 5
                    assert data["target"] == "all"

            self._run_async(check())

    def test_unit_aam_cache_clean_response_structure(self) -> None:
        """aam_cache_clean response is a dict with removed key."""
        mock_cache = Mock()
        mock_cache.clean.return_value = 0

        with patch(
            "aam_cli.mcp.tools_write.cache_service",
            mock_cache,
        ):
            server = create_mcp_server(allow_write=True)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool(
                        "aam_cache_clean", {}
                    )
                    data = _parse_mcp_result(result)
                    assert isinstance(data, dict)
                    assert "removed" in data

            self._run_async(check())


################################################################################
#                                                                              #
# TEST: ERROR BOUNDARY — ValueError                                           #
#                                                                              #
################################################################################


class TestErrorBoundaryValueError:
    """Verify that ValueError from a service yields a structured error dict."""

    def _run_async(self, coro: Any) -> Any:
        """Run an async coroutine synchronously."""
        return asyncio.run(coro)

    def test_unit_error_boundary_value_error(self) -> None:
        """ValueError returns {error, error_code} through MCP error boundary."""
        with patch(
            "aam_cli.mcp.tools_read.get_tree",
            side_effect=ValueError(
                "[AAM_TEST_ERROR] something went wrong"
            ),
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool(
                        "aam_tree",
                        {"depth": 0, "project": "."},
                    )
                    data = _parse_mcp_result(result)
                    assert "error" in data
                    assert "error_code" in data
                    assert data["error_code"] == "AAM_TEST_ERROR"

            self._run_async(check())


################################################################################
#                                                                              #
# TEST: ERROR BOUNDARY — FileNotFoundError                                     #
#                                                                              #
################################################################################


class TestErrorBoundaryFileNotFound:
    """Verify that FileNotFoundError yields FILE_NOT_FOUND error code."""

    def _run_async(self, coro: Any) -> Any:
        """Run an async coroutine synchronously."""
        return asyncio.run(coro)

    def test_unit_error_boundary_file_not_found(self) -> None:
        """FileNotFoundError returns error_code FILE_NOT_FOUND via MCP."""
        with patch(
            "aam_cli.mcp.tools_read.get_tree",
            side_effect=FileNotFoundError("lock file not found"),
        ):
            server = create_mcp_server(allow_write=False)

            async def check() -> None:
                async with Client(server) as client:
                    result = await client.call_tool(
                        "aam_tree",
                        {"depth": 0, "project": "."},
                    )
                    data = _parse_mcp_result(result)
                    assert "error" in data
                    assert data["error_code"] == "FILE_NOT_FOUND"

            self._run_async(check())
