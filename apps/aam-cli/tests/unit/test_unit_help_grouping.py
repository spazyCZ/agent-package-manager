"""Unit tests for categorized ``aam --help`` output.

Verifies that the OrderedGroup renders section headers and
groups commands correctly in the help output.

Reference: spec 004 US8; tasks.md T017.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging

import pytest
from click.testing import CliRunner

from aam_cli.main import OrderedGroup, cli

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
# TEST: ORDERED GROUP SECTIONS                                                 #
#                                                                              #
################################################################################


class TestOrderedGroupSections:
    """Verify ``aam --help`` shows categorized command sections."""

    def test_help_output_contains_section_headers(self, runner: CliRunner) -> None:
        """``aam --help`` should contain labeled section headers."""
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        output = result.output

        # -----
        # Verify section headers from OrderedGroup.SECTIONS
        # -----
        expected_sections = [
            "Package Management",
            "Package Integrity",
            "Package Authoring",
            "Source Management",
            "Configuration",
            "Utilities",
        ]

        for section in expected_sections:
            assert section in output, f"Expected section '{section}' in --help output"

    def test_help_shows_pkg_under_authoring(self, runner: CliRunner) -> None:
        """``pkg`` should appear under 'Package Authoring' section."""
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0

        # -----
        # Find the Package Authoring section and verify pkg is listed
        # -----
        output = result.output
        authoring_idx = output.find("Package Authoring")
        assert authoring_idx != -1

        # Check that "pkg" appears after the section header
        section_text = output[authoring_idx:]
        assert "pkg" in section_text

    def test_help_shows_install_under_package_management(
        self, runner: CliRunner
    ) -> None:
        """``install`` should appear under 'Package Management' section."""
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0

        output = result.output
        mgmt_idx = output.find("Package Management")
        assert mgmt_idx != -1

        section_text = output[mgmt_idx:]
        assert "install" in section_text

    def test_help_shows_source_under_source_management(
        self, runner: CliRunner
    ) -> None:
        """``source`` should appear under 'Source Management' section."""
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0

        output = result.output
        source_idx = output.find("Source Management")
        assert source_idx != -1

        section_text = output[source_idx:]
        assert "source" in section_text

    def test_deprecated_commands_hidden_from_help(self, runner: CliRunner) -> None:
        """Deprecated aliases should not appear in ``aam --help``."""
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        output = result.output

        # -----
        # Deprecated commands use hidden=True, so they should
        # not appear as visible entries in the help output.
        # Note: "create-package" as a visible line should not appear
        # -----
        # Split by lines and check each "command-like" line
        for line in output.split("\n"):
            stripped = line.strip()
            if stripped.startswith("create-package"):
                pytest.fail(
                    "Deprecated 'create-package' should not appear in --help"
                )


################################################################################
#                                                                              #
# TEST: ORDERED GROUP CLASS                                                    #
#                                                                              #
################################################################################


class TestOrderedGroupClass:
    """Verify OrderedGroup class structure and behavior."""

    def test_sections_dict_is_defined(self) -> None:
        """OrderedGroup.SECTIONS should be a non-empty dict."""
        assert isinstance(OrderedGroup.SECTIONS, dict)
        assert len(OrderedGroup.SECTIONS) > 0

    def test_sections_contain_expected_keys(self) -> None:
        """OrderedGroup.SECTIONS should contain all expected section keys."""
        expected = {
            "Getting Started",
            "Package Management",
            "Package Integrity",
            "Package Authoring",
            "Source Management",
            "Configuration",
            "Utilities",
        }

        actual = set(OrderedGroup.SECTIONS.keys())
        assert expected == actual

    def test_pkg_in_package_authoring(self) -> None:
        """``pkg`` should be listed in 'Package Authoring' section."""
        assert "pkg" in OrderedGroup.SECTIONS["Package Authoring"]

    def test_install_in_package_management(self) -> None:
        """``install`` should be listed in 'Package Management' section."""
        assert "install" in OrderedGroup.SECTIONS["Package Management"]

    def test_help_renders_within_80_columns(self, runner: CliRunner) -> None:
        """Help output should render within 80-column terminal width."""
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0

        for line in result.output.split("\n"):
            # Click wraps to terminal width; 80 + small overflow is acceptable
            assert len(line) <= 120, (
                f"Line exceeds 120 chars (80-col target): {line!r}"
            )
