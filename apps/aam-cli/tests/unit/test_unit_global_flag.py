"""Unit tests for the ``-g`` / ``--global`` flag across CLI commands.

Verifies that:
  - ``resolve_project_dir()`` returns ``Path.home()`` for global mode
    and ``Path.cwd()`` for local (default) mode.
  - Each command that supports ``-g`` accepts the flag without errors
    and includes it in its ``--help`` output.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from aam_cli.main import cli
from aam_cli.utils.paths import resolve_project_dir

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


@pytest.fixture
def runner() -> CliRunner:
    """Create a Click test runner."""
    return CliRunner()


################################################################################
#                                                                              #
# TEST: resolve_project_dir                                                    #
#                                                                              #
################################################################################


class TestResolveProjectDir:
    """Verify ``resolve_project_dir()`` path resolution logic."""

    def test_local_mode_returns_cwd(self, tmp_path: Path) -> None:
        """Default (local) mode should return the current working directory."""
        with patch("aam_cli.utils.paths.Path.cwd", return_value=tmp_path):
            result = resolve_project_dir(is_global=False)

        assert result == tmp_path

    def test_global_mode_returns_home(self, tmp_path: Path) -> None:
        """Global mode should return ``Path.home()``."""
        with patch("aam_cli.utils.paths.Path.home", return_value=tmp_path):
            result = resolve_project_dir(is_global=True)

        assert result == tmp_path

    def test_default_is_local(self, tmp_path: Path) -> None:
        """Calling without arguments should default to local mode."""
        with patch("aam_cli.utils.paths.Path.cwd", return_value=tmp_path):
            result = resolve_project_dir()

        assert result == tmp_path

    def test_global_and_local_differ(self) -> None:
        """Global and local paths should differ (home != cwd in general)."""
        # -----
        # Use two distinct sentinel paths to verify the branch logic
        # -----
        home_sentinel = Path("/mock/home")
        cwd_sentinel = Path("/mock/project")

        with patch("aam_cli.utils.paths.Path.home", return_value=home_sentinel):
            global_dir = resolve_project_dir(is_global=True)

        with patch("aam_cli.utils.paths.Path.cwd", return_value=cwd_sentinel):
            local_dir = resolve_project_dir(is_global=False)

        assert global_dir == home_sentinel
        assert local_dir == cwd_sentinel
        assert global_dir != local_dir


################################################################################
#                                                                              #
# TEST: --global flag in --help output                                         #
#                                                                              #
################################################################################


class TestGlobalFlagInHelp:
    """Verify ``-g`` / ``--global`` appears in each command's help output."""

    @pytest.mark.parametrize(
        "command",
        ["install", "uninstall", "list", "upgrade", "outdated"],
    )
    def test_help_shows_global_option(
        self, runner: CliRunner, command: str
    ) -> None:
        """``aam <command> --help`` should list the ``--global`` / ``-g`` flag."""
        result = runner.invoke(cli, [command, "--help"])

        assert result.exit_code == 0
        assert "--global" in result.output, (
            f"Expected '--global' in 'aam {command} --help' output"
        )
        assert "-g" in result.output, (
            f"Expected '-g' in 'aam {command} --help' output"
        )


################################################################################
#                                                                              #
# TEST: --global flag acceptance (no crash)                                    #
#                                                                              #
################################################################################


class TestGlobalFlagAcceptance:
    """Verify commands accept ``-g`` without crashing.

    These tests invoke each command with ``-g`` and ``--dry-run``
    (where available) in an isolated temp directory. We only check
    that Click does not reject the flag; actual behaviour is tested
    at the integration level.
    """

    def test_install_accepts_global_flag(self, runner: CliRunner) -> None:
        """``aam install <pkg> -g --dry-run`` should not raise a Click error."""
        with runner.isolated_filesystem():
            result = runner.invoke(
                cli, ["install", "test-pkg", "-g", "--dry-run"]
            )

        # -----
        # The command may fail (no registry), but it should NOT fail
        # because of an unrecognised option.
        # -----
        assert "No such option" not in (result.output or "")
        assert "Error: Missing option" not in (result.output or "")

    def test_uninstall_accepts_global_flag(self, runner: CliRunner) -> None:
        """``aam uninstall <pkg> -g`` should not raise a Click error."""
        with runner.isolated_filesystem():
            result = runner.invoke(
                cli, ["uninstall", "test-pkg", "-g"]
            )

        assert "No such option" not in (result.output or "")

    def test_list_accepts_global_flag(self, runner: CliRunner) -> None:
        """``aam list -g`` should not raise a Click error."""
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["list", "-g"])

        assert "No such option" not in (result.output or "")

    def test_upgrade_accepts_global_flag(self, runner: CliRunner) -> None:
        """``aam upgrade -g --dry-run`` should not raise a Click error."""
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["upgrade", "-g", "--dry-run"])

        assert "No such option" not in (result.output or "")

    def test_outdated_accepts_global_flag(self, runner: CliRunner) -> None:
        """``aam outdated -g`` should not raise a Click error."""
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["outdated", "-g"])

        assert "No such option" not in (result.output or "")


################################################################################
#                                                                              #
# TEST: global mode banner                                                     #
#                                                                              #
################################################################################


class TestGlobalModeBanner:
    """Verify the global mode visual indicator is printed when ``-g`` is set."""

    def test_list_global_shows_banner(self, runner: CliRunner) -> None:
        """``aam list -g`` should print the global mode banner."""
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["list", "-g"])

        assert "Operating in global mode" in result.output

    def test_list_local_no_banner(self, runner: CliRunner) -> None:
        """``aam list`` (without ``-g``) should not print the global banner."""
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["list"])

        assert "Operating in global mode" not in result.output
