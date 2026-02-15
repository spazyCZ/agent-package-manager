"""Unit tests for MCP init tools and resources (spec 004, US11).

Tests cover:
  - aam_init write tool
  - aam_init_info read tool
  - aam://init_status resource
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from aam_cli.services.client_init_service import ClientInitResult

################################################################################
#                                                                              #
# FIXTURES                                                                     #
#                                                                              #
################################################################################


@pytest.fixture()
def mock_mcp() -> MagicMock:
    """Create a mock FastMCP instance that captures tool/resource registrations."""
    mcp = MagicMock()

    # -----
    # Capture decorated functions so we can call them directly
    # -----
    mcp._tools: dict = {}
    mcp._resources: dict = {}

    def tool_decorator(**kwargs):
        def wrapper(fn):
            mcp._tools[fn.__name__] = fn
            return fn
        return wrapper

    def resource_decorator(uri: str):
        def wrapper(fn):
            mcp._resources[uri] = fn
            return fn
        return wrapper

    mcp.tool = tool_decorator
    mcp.resource = resource_decorator

    return mcp


################################################################################
#                                                                              #
# WRITE TOOL TESTS — aam_init                                                 #
#                                                                              #
################################################################################


class TestAamInitWriteTool:
    """Tests for the aam_init MCP write tool."""

    def _register(self, mcp: MagicMock) -> None:
        """Helper to register write tools on mock MCP."""
        from aam_cli.mcp.tools_write import register_write_tools

        register_write_tools(mcp)

    @patch("aam_cli.mcp.tools_write.load_config")
    def test_unit_init_valid_platform(self, mock_config: MagicMock, mock_mcp: MagicMock) -> None:
        """aam_init with a valid platform delegates to orchestrate_init."""
        self._register(mock_mcp)
        tool_fn = mock_mcp._tools["aam_init"]

        fake_result = ClientInitResult(
            platform="cursor",
            registry_created=False,
            registry_name=None,
            sources_added=["anthropics/skills"],
            config_path=Path("/home/user/.aam/config.yaml"),
            is_reconfigure=False,
        )

        # -----
        # Patch the orchestrate_init at the service module level
        # (the tool imports it lazily inside the function body)
        # -----
        with patch(
            "aam_cli.services.client_init_service.orchestrate_init",
            return_value=fake_result,
        ) as mock_orchestrate:
            result = tool_fn(platform="cursor", skip_sources=False)

        assert result["platform"] == "cursor"
        assert result["sources_added"] == ["anthropics/skills"]
        assert result["is_reconfigure"] is False
        mock_orchestrate.assert_called_once_with(
            platform="cursor",
            skip_sources=False,
        )

    @patch("aam_cli.mcp.tools_write.load_config")
    def test_unit_init_invalid_platform(self, mock_config: MagicMock, mock_mcp: MagicMock) -> None:
        """aam_init with an unsupported platform returns an error."""
        self._register(mock_mcp)
        tool_fn = mock_mcp._tools["aam_init"]

        result = tool_fn(platform="vscode", skip_sources=False)

        assert "error" in result
        assert "vscode" in result["error"]

    @patch("aam_cli.mcp.tools_write.load_config")
    def test_unit_init_skip_sources(self, mock_config: MagicMock, mock_mcp: MagicMock) -> None:
        """aam_init with skip_sources=True passes flag to orchestrate_init."""
        self._register(mock_mcp)
        tool_fn = mock_mcp._tools["aam_init"]

        fake_result = ClientInitResult(
            platform="claude",
            registry_created=False,
            registry_name=None,
            sources_added=[],
            config_path=Path("/home/user/.aam/config.yaml"),
            is_reconfigure=True,
        )

        with patch(
            "aam_cli.services.client_init_service.orchestrate_init",
            return_value=fake_result,
        ) as mock_orchestrate:
            result = tool_fn(platform="claude", skip_sources=True)

        assert result["platform"] == "claude"
        assert result["sources_added"] == []
        assert result["is_reconfigure"] is True
        mock_orchestrate.assert_called_once_with(
            platform="claude",
            skip_sources=True,
        )


################################################################################
#                                                                              #
# READ TOOL TESTS — aam_init_info                                             #
#                                                                              #
################################################################################


class TestAamInitInfoReadTool:
    """Tests for the aam_init_info MCP read tool."""

    def _register(self, mcp: MagicMock) -> None:
        """Helper to register read tools on mock MCP."""
        from aam_cli.mcp.tools_read import register_read_tools

        register_read_tools(mcp)

    @patch("aam_cli.mcp.tools_read.load_config")
    def test_unit_init_info_with_detected_platform(
        self, mock_config: MagicMock, mock_mcp: MagicMock
    ) -> None:
        """aam_init_info returns detected platform when available."""
        self._register(mock_mcp)
        tool_fn = mock_mcp._tools["aam_init_info"]

        # -----
        # Configure mock config with a default platform
        # -----
        config = MagicMock()
        config.default_platform = "cursor"
        mock_config.return_value = config

        with patch(
            "aam_cli.services.client_init_service.detect_platform",
            return_value="cursor",
        ):
            result = tool_fn()

        assert result["detected_platform"] == "cursor"
        assert result["current_platform"] == "cursor"
        assert "cursor" in result["supported_platforms"]
        assert result["has_config"] is True
        assert result["recommended_platform"] == "cursor"

    @patch("aam_cli.mcp.tools_read.load_config")
    def test_unit_init_info_no_detection(
        self, mock_config: MagicMock, mock_mcp: MagicMock
    ) -> None:
        """aam_init_info returns cursor as default when no platform detected."""
        self._register(mock_mcp)
        tool_fn = mock_mcp._tools["aam_init_info"]

        config = MagicMock()
        config.default_platform = None
        mock_config.return_value = config

        with patch(
            "aam_cli.services.client_init_service.detect_platform",
            return_value=None,
        ):
            result = tool_fn()

        assert result["detected_platform"] is None
        assert result["has_config"] is False
        assert result["recommended_platform"] == "cursor"


################################################################################
#                                                                              #
# READ TOOL TESTS — aam_recommend_skills                                       #
#                                                                              #
################################################################################


class TestAamRecommendSkillsReadTool:
    """Tests for the aam_recommend_skills MCP read tool."""

    def _register(self, mcp: MagicMock) -> None:
        """Helper to register read tools on mock MCP."""
        from aam_cli.mcp.tools_read import register_read_tools

        register_read_tools(mcp)

    def test_unit_recommend_skills_returns_structure(
        self, mock_mcp: MagicMock, tmp_path
    ) -> None:
        """aam_recommend_skills returns repo_context and recommendations."""
        (tmp_path / "package.json").write_text('{"dependencies": {"react": "18"}}')
        self._register(mock_mcp)
        tool_fn = mock_mcp._tools["aam_recommend_skills"]

        with patch(
            "aam_cli.mcp.tools_read.recommend_skills_for_repo",
            return_value={
                "repo_context": {"frontend_frameworks": ["react"], "keywords": ["react"]},
                "recommendations": [{"qualified_name": "src/code-review", "score": 50}],
                "install_hint": "aam install <qualified_name>",
            },
        ):
            result = tool_fn(path=str(tmp_path), limit=5)

        assert "repo_context" in result
        assert "recommendations" in result
        assert "install_hint" in result
        assert result["repo_context"]["frontend_frameworks"] == ["react"]


################################################################################
#                                                                              #
# RESOURCE TESTS — aam://init_status                                           #
#                                                                              #
################################################################################


class TestInitStatusResource:
    """Tests for the aam://init_status MCP resource."""

    def _register(self, mcp: MagicMock) -> None:
        """Helper to register resources on mock MCP."""
        from aam_cli.mcp.resources import register_resources

        register_resources(mcp)

    def test_unit_init_status_initialized(self, mock_mcp: MagicMock) -> None:
        """aam://init_status returns is_initialized=True when platform is set."""
        with patch(
            "aam_cli.mcp.resources.get_config",
            return_value={
                "value": {
                    "default_platform": "cursor",
                    "sources": {"community": {"url": "https://example.com"}},
                },
            },
        ), patch(
            "aam_cli.services.client_init_service.detect_platform",
            return_value="cursor",
        ):
            self._register(mock_mcp)
            resource_fn = mock_mcp._resources["aam://init_status"]
            result = resource_fn()

        assert result["is_initialized"] is True
        assert result["current_platform"] == "cursor"
        assert result["detected_platform"] == "cursor"
        assert result["sources_configured"] == 1
        assert result["source_names"] == ["community"]

    def test_unit_init_status_not_initialized(self, mock_mcp: MagicMock) -> None:
        """aam://init_status returns is_initialized=False when no platform set."""
        with patch(
            "aam_cli.mcp.resources.get_config",
            return_value={
                "value": {},
            },
        ), patch(
            "aam_cli.services.client_init_service.detect_platform",
            return_value=None,
        ):
            self._register(mock_mcp)
            resource_fn = mock_mcp._resources["aam://init_status"]
            result = resource_fn()

        assert result["is_initialized"] is False
        assert result["current_platform"] is None
        assert result["detected_platform"] is None
        assert result["sources_configured"] == 0
        assert result["source_names"] == []
