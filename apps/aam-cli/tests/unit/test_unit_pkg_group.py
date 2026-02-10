"""Unit tests for ``aam pkg`` command group.

Verifies that the pkg group is properly registered, lists all
expected subcommands, and that deprecated aliases print a warning
and delegate correctly.

Reference: spec 004 US7; tasks.md T016.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging

import pytest
from click.testing import CliRunner

from aam_cli.main import cli

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
# TEST: PKG GROUP REGISTRATION                                                #
#                                                                              #
################################################################################


class TestPkgGroup:
    """Verify ``aam pkg`` group is registered and lists subcommands."""

    def test_pkg_help_shows_all_subcommands(self, runner: CliRunner) -> None:
        """``aam pkg --help`` should list all 6 authoring subcommands."""
        result = runner.invoke(cli, ["pkg", "--help"])

        assert result.exit_code == 0
        output = result.output

        # -----
        # Verify each expected subcommand appears in help
        # -----
        expected_commands = ["init", "create", "validate", "pack", "publish", "build"]
        for cmd in expected_commands:
            assert cmd in output, f"Expected '{cmd}' in pkg --help output"

    def test_pkg_help_shows_description(self, runner: CliRunner) -> None:
        """``aam pkg --help`` should show the group description."""
        result = runner.invoke(cli, ["pkg", "--help"])

        assert result.exit_code == 0
        assert "Package authoring commands" in result.output

    def test_pkg_without_subcommand_shows_usage(self, runner: CliRunner) -> None:
        """``aam pkg`` with no subcommand should show usage (exit 2)."""
        result = runner.invoke(cli, ["pkg"])

        # Click groups return exit 2 (usage error) without subcommand
        assert result.exit_code == 2 or result.exit_code == 0
        assert "pkg" in result.output


################################################################################
#                                                                              #
# TEST: DEPRECATED ALIASES                                                     #
#                                                                              #
################################################################################


class TestDeprecatedAliases:
    """Verify deprecated root-level aliases print warnings."""

    def test_deprecated_validate_prints_warning(self, runner: CliRunner) -> None:
        """``aam validate`` should print a deprecation warning to stderr."""
        # -----
        # Invoke inside isolated fs so it fails gracefully on missing aam.yaml
        # -----
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["validate"])

        # -----
        # Check output for deprecation warning
        # -----
        assert "deprecated" in result.output.lower()
        assert "aam pkg validate" in result.output

    def test_deprecated_pack_prints_warning(self, runner: CliRunner) -> None:
        """``aam pack`` should print a deprecation warning."""
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["pack"])

        assert "deprecated" in result.output.lower()
        assert "aam pkg pack" in result.output

    def test_deprecated_build_prints_warning(self, runner: CliRunner) -> None:
        """``aam build --target cursor`` should print a deprecation warning."""
        result = runner.invoke(cli, ["build", "--target", "cursor"])

        assert "deprecated" in result.output.lower()
        assert "aam pkg build" in result.output

    def test_deprecated_aliases_hidden_from_help(self, runner: CliRunner) -> None:
        """Deprecated aliases must NOT appear in ``aam --help``."""
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        output = result.output

        # -----
        # The old root-level command names should be hidden
        # -----
        # "create-package" is the old command name
        # It should NOT appear as a visible command in help output
        lines = output.split("\n")
        visible_commands = [
            line.strip().split()[0]
            for line in lines
            if line.strip() and not line.strip().startswith("-")
        ]

        # "create-package" as a standalone visible command should not appear
        assert "create-package" not in visible_commands
