"""Unit tests for ``aam init`` client initialization.

Covers:
  - Platform detection logic
  - Interactive flow with mocked click.prompt
  - --yes flag defaults
  - Existing config detection (reconfigure)
  - [name] argument delegation to ``pkg init``

Reference: spec 004 T034.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from aam_cli.services.client_init_service import (
    SUPPORTED_PLATFORMS,
    ClientInitResult,
    detect_platform,
    orchestrate_init,
)

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# FIXTURES                                                                     #
#                                                                              #
################################################################################


@pytest.fixture()
def runner() -> CliRunner:
    """Click CLI test runner."""
    return CliRunner()


################################################################################
#                                                                              #
# PLATFORM DETECTION TESTS                                                     #
#                                                                              #
################################################################################


class TestDetectPlatform:
    """Tests for :func:`detect_platform`."""

    def test_detect_cursor(self, tmp_path: Path) -> None:
        """Detect cursor when .cursor/ dir exists."""
        (tmp_path / ".cursor").mkdir()
        assert detect_platform(tmp_path) == "cursor"

    def test_detect_copilot(self, tmp_path: Path) -> None:
        """Detect copilot when .github/copilot/ dir exists."""
        (tmp_path / ".github" / "copilot").mkdir(parents=True)
        assert detect_platform(tmp_path) == "copilot"

    def test_detect_claude(self, tmp_path: Path) -> None:
        """Detect claude when CLAUDE.md file exists."""
        (tmp_path / "CLAUDE.md").write_text("# Claude\n")
        assert detect_platform(tmp_path) == "claude"

    def test_detect_codex(self, tmp_path: Path) -> None:
        """Detect codex when .codex/ dir exists."""
        (tmp_path / ".codex").mkdir()
        assert detect_platform(tmp_path) == "codex"

    def test_detect_none(self, tmp_path: Path) -> None:
        """Return None when no indicators found."""
        assert detect_platform(tmp_path) is None

    def test_detect_priority_cursor_over_claude(self, tmp_path: Path) -> None:
        """Cursor takes priority when both .cursor/ and CLAUDE.md exist."""
        (tmp_path / ".cursor").mkdir()
        (tmp_path / "CLAUDE.md").write_text("# Claude\n")
        assert detect_platform(tmp_path) == "cursor"


################################################################################
#                                                                              #
# CLIENT INIT RESULT TESTS                                                     #
#                                                                              #
################################################################################


class TestClientInitResult:
    """Tests for :class:`ClientInitResult` dataclass."""

    def test_default_values(self) -> None:
        """Verify default field values."""
        result = ClientInitResult(
            platform="cursor",
            registry_created=False,
            registry_name=None,
        )
        assert result.platform == "cursor"
        assert result.registry_created is False
        assert result.registry_name is None
        assert result.sources_added == []
        assert result.config_path == Path("~/.aam/config.yaml")
        assert result.is_reconfigure is False

    def test_full_result(self) -> None:
        """Verify all fields can be set."""
        result = ClientInitResult(
            platform="copilot",
            registry_created=True,
            registry_name="my-registry",
            sources_added=["anthropics/skills", "awesome-prompts"],
            config_path=Path("/tmp/test/config.yaml"),
            is_reconfigure=True,
        )
        assert result.platform == "copilot"
        assert result.registry_created is True
        assert result.registry_name == "my-registry"
        assert len(result.sources_added) == 2
        assert result.is_reconfigure is True


################################################################################
#                                                                              #
# SUPPORTED PLATFORMS TESTS                                                    #
#                                                                              #
################################################################################


class TestSupportedPlatforms:
    """Tests for supported platform list."""

    def test_all_platforms_present(self) -> None:
        """Verify all expected platforms are listed."""
        expected = {"cursor", "copilot", "claude", "codex"}
        assert set(SUPPORTED_PLATFORMS) == expected

    def test_platforms_is_list(self) -> None:
        """Verify the constant is a list."""
        assert isinstance(SUPPORTED_PLATFORMS, list)


################################################################################
#                                                                              #
# ORCHESTRATE INIT TESTS                                                       #
#                                                                              #
################################################################################


class TestOrchestrateInit:
    """Tests for :func:`orchestrate_init`."""

    @patch("aam_cli.services.client_init_service.setup_default_sources")
    @patch("aam_cli.services.client_init_service.save_global_config")
    @patch("aam_cli.services.client_init_service.load_config")
    @patch("aam_cli.utils.paths.get_global_aam_dir")
    def test_basic_init(
        self,
        mock_aam_dir: MagicMock,
        mock_load: MagicMock,
        mock_save: MagicMock,
        mock_sources: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Orchestrate init saves config and registers sources."""
        mock_aam_dir.return_value = tmp_path
        mock_load.return_value = MagicMock(default_platform="cursor")
        mock_sources.return_value = ["anthropics/skills"]

        result = orchestrate_init(platform="copilot")

        assert result.platform == "copilot"
        assert result.sources_added == ["anthropics/skills"]
        assert result.is_reconfigure is False
        mock_save.assert_called_once()

    @patch("aam_cli.services.client_init_service.setup_default_sources")
    @patch("aam_cli.services.client_init_service.save_global_config")
    @patch("aam_cli.services.client_init_service.load_config")
    @patch("aam_cli.utils.paths.get_global_aam_dir")
    def test_skip_sources(
        self,
        mock_aam_dir: MagicMock,
        mock_load: MagicMock,
        mock_save: MagicMock,
        mock_sources: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Skip sources when skip_sources=True."""
        mock_aam_dir.return_value = tmp_path
        mock_load.return_value = MagicMock(default_platform="cursor")

        result = orchestrate_init(platform="claude", skip_sources=True)

        assert result.sources_added == []
        mock_sources.assert_not_called()

    @patch("aam_cli.services.client_init_service.setup_default_sources")
    @patch("aam_cli.services.client_init_service.save_global_config")
    @patch("aam_cli.services.client_init_service.load_config")
    @patch("aam_cli.utils.paths.get_global_aam_dir")
    def test_reconfigure_detected(
        self,
        mock_aam_dir: MagicMock,
        mock_load: MagicMock,
        mock_save: MagicMock,
        mock_sources: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Detect reconfiguration when config already exists."""
        # Create existing config
        config_file = tmp_path / "config.yaml"
        config_file.write_text("default_platform: cursor\n")

        mock_aam_dir.return_value = tmp_path
        mock_load.return_value = MagicMock(default_platform="cursor")
        mock_sources.return_value = []

        result = orchestrate_init(platform="codex")

        assert result.is_reconfigure is True


################################################################################
#                                                                              #
# CLIENT INIT COMMAND TESTS                                                    #
#                                                                              #
################################################################################


class TestClientInitCommand:
    """Tests for the ``aam init`` Click command."""

    @patch("aam_cli.commands.client_init.orchestrate_init")
    @patch("aam_cli.commands.client_init.detect_platform")
    @patch("aam_cli.utils.paths.get_global_aam_dir")
    def test_yes_flag_uses_defaults(
        self,
        mock_aam_dir: MagicMock,
        mock_detect: MagicMock,
        mock_orchestrate: MagicMock,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """--yes flag uses detected platform or cursor default."""
        from aam_cli.main import cli

        mock_aam_dir.return_value = tmp_path
        mock_detect.return_value = "claude"
        mock_orchestrate.return_value = ClientInitResult(
            platform="claude",
            registry_created=False,
            registry_name=None,
            config_path=tmp_path / "config.yaml",
        )

        result = runner.invoke(cli, ["init", "--yes"])
        assert result.exit_code == 0
        mock_orchestrate.assert_called_once_with(
            platform="claude",
            skip_sources=False,
        )

    @patch("aam_cli.commands.client_init.orchestrate_init")
    @patch("aam_cli.commands.client_init.detect_platform")
    @patch("aam_cli.utils.paths.get_global_aam_dir")
    def test_yes_flag_cursor_default_no_detection(
        self,
        mock_aam_dir: MagicMock,
        mock_detect: MagicMock,
        mock_orchestrate: MagicMock,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """--yes flag defaults to cursor when no platform detected."""
        from aam_cli.main import cli

        mock_aam_dir.return_value = tmp_path
        mock_detect.return_value = None
        mock_orchestrate.return_value = ClientInitResult(
            platform="cursor",
            registry_created=False,
            registry_name=None,
            config_path=tmp_path / "config.yaml",
        )

        result = runner.invoke(cli, ["init", "--yes"])
        assert result.exit_code == 0
        mock_orchestrate.assert_called_once_with(
            platform="cursor",
            skip_sources=False,
        )

    def test_name_arg_delegates_to_pkg_init(
        self,
        runner: CliRunner,
    ) -> None:
        """Passing a [name] arg prints deprecation warning and delegates."""
        from aam_cli.main import cli

        result = runner.invoke(cli, ["init", "my-package"])

        # Should show deprecation warning in output
        assert "deprecated" in result.output.lower()

    def test_init_appears_in_help(self, runner: CliRunner) -> None:
        """``init`` appears in ``aam --help`` under Getting Started."""
        from aam_cli.main import cli

        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "init" in result.output
        assert "Getting Started" in result.output

    @patch("aam_cli.commands.client_init.orchestrate_init")
    @patch("aam_cli.commands.client_init.detect_platform")
    @patch("aam_cli.utils.paths.get_global_aam_dir")
    def test_reconfigure_summary(
        self,
        mock_aam_dir: MagicMock,
        mock_detect: MagicMock,
        mock_orchestrate: MagicMock,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Display 'reconfigured' message when is_reconfigure is True."""
        from aam_cli.main import cli

        mock_aam_dir.return_value = tmp_path
        mock_detect.return_value = "cursor"
        mock_orchestrate.return_value = ClientInitResult(
            platform="cursor",
            registry_created=False,
            registry_name=None,
            config_path=tmp_path / "config.yaml",
            is_reconfigure=True,
        )

        result = runner.invoke(cli, ["init", "--yes"])
        assert result.exit_code == 0
        assert "reconfigured" in result.output.lower()

    @patch("aam_cli.commands.client_init.orchestrate_init")
    @patch("aam_cli.commands.client_init.detect_platform")
    @patch("aam_cli.utils.paths.get_global_aam_dir")
    def test_next_steps_displayed(
        self,
        mock_aam_dir: MagicMock,
        mock_detect: MagicMock,
        mock_orchestrate: MagicMock,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Display 'Next steps' guidance after init."""
        from aam_cli.main import cli

        mock_aam_dir.return_value = tmp_path
        mock_detect.return_value = "cursor"
        mock_orchestrate.return_value = ClientInitResult(
            platform="cursor",
            registry_created=False,
            registry_name=None,
            config_path=tmp_path / "config.yaml",
        )

        result = runner.invoke(cli, ["init", "--yes"])
        assert result.exit_code == 0
        assert "Next steps" in result.output
        assert "aam search" in result.output
        assert "aam install" in result.output
