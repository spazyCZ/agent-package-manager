"""Tests for main CLI module.

Covers command registration, help output, and basic invocation
of all commands. Tests that interact with the filesystem or
configuration use Click's isolated_filesystem context.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from pathlib import Path

import pytest
from click.testing import CliRunner

from aam_cli.main import cli
from aam_cli.utils.naming import (
    format_package_name,
    parse_package_name,
    parse_package_spec,
    to_filesystem_name,
    validate_package_name,
)

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# CLI ROOT TESTS                                                               #
#                                                                              #
################################################################################


class TestCLI:
    """Test CLI root group and global options."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_unit_cli_version(self) -> None:
        """Test --version flag displays version string."""
        result = self.runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_unit_cli_help(self) -> None:
        """Test --help flag displays usage and description."""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "AAM - Agent Package Manager" in result.output

    def test_unit_cli_verbose_flag(self) -> None:
        """Test --verbose flag is accepted without error."""
        result = self.runner.invoke(cli, ["--verbose", "--help"])
        assert result.exit_code == 0


################################################################################
#                                                                              #
# COMMAND REGISTRATION TESTS                                                   #
#                                                                              #
################################################################################


class TestCommandRegistration:
    """Test that all expected commands are registered."""

    EXPECTED_COMMANDS = [
        "build",
        "config",
        "create-package",
        "info",
        "init",
        "install",
        "list",
        "pack",
        "publish",
        "registry",
        "search",
        "uninstall",
        "validate",
    ]

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_unit_all_commands_listed_in_help(self) -> None:
        """Test all expected commands appear in help output."""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        for cmd in self.EXPECTED_COMMANDS:
            assert cmd in result.output, f"Command '{cmd}' not found in help output"

    @pytest.mark.parametrize("command", EXPECTED_COMMANDS)
    def test_unit_command_has_help(self, command: str) -> None:
        """Test each command accepts --help without error."""
        result = self.runner.invoke(cli, [command, "--help"])
        assert result.exit_code == 0, (
            f"'{command} --help' returned exit code {result.exit_code}: {result.output}"
        )


################################################################################
#                                                                              #
# VALIDATE COMMAND TESTS                                                       #
#                                                                              #
################################################################################


class TestValidateCommand:
    """Test validate command."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_unit_validate_no_manifest(self) -> None:
        """Test validate shows error when aam.yaml not found."""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ["validate"])
            assert result.exit_code != 0
            assert "No aam.yaml found" in result.output

    def test_unit_validate_valid_package(self) -> None:
        """Test validate succeeds on a valid aam.yaml with existing artifacts."""
        with self.runner.isolated_filesystem():
            # -----
            # Create a minimal valid package
            # -----
            Path("aam.yaml").write_text(
                "name: test-pkg\n"
                "version: 1.0.0\n"
                "aam_version: '1'\n"
                "description: A test package\n"
                "platforms:\n"
                "  cursor:\n"
                "    skill_scope: project\n"
                "artifacts:\n"
                "  skills:\n"
                "    - name: test-skill\n"
                "      path: skills/test\n"
                "      description: A test skill\n",
                encoding="utf-8",
            )
            Path("skills/test").mkdir(parents=True)

            result = self.runner.invoke(cli, ["validate"])
            assert result.exit_code == 0
            assert "valid" in result.output.lower()

    def test_unit_validate_missing_artifact(self) -> None:
        """Test validate reports missing artifact paths."""
        with self.runner.isolated_filesystem():
            Path("aam.yaml").write_text(
                "name: test-pkg\n"
                "version: 1.0.0\n"
                "aam_version: '1'\n"
                "description: A test\n"
                "platforms:\n"
                "  cursor:\n"
                "    skill_scope: project\n"
                "artifacts:\n"
                "  skills:\n"
                "    - name: missing-skill\n"
                "      path: skills/missing\n"
                "      description: Not here\n",
                encoding="utf-8",
            )

            result = self.runner.invoke(cli, ["validate"])
            assert result.exit_code != 0
            assert "not found" in result.output.lower()


################################################################################
#                                                                              #
# LIST COMMAND TESTS                                                           #
#                                                                              #
################################################################################


class TestListCommand:
    """Test list command."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_unit_list_no_packages(self) -> None:
        """Test list shows empty message when no packages installed."""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ["list"])
            assert result.exit_code == 0
            assert "No packages installed" in result.output


################################################################################
#                                                                              #
# INFO COMMAND TESTS                                                           #
#                                                                              #
################################################################################


class TestInfoCommand:
    """Test info (show_package) command."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_unit_info_not_installed(self) -> None:
        """Test info shows error when package is not installed."""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ["info", "nonexistent-pkg"])
            assert result.exit_code != 0
            assert "not installed" in result.output.lower()


################################################################################
#                                                                              #
# INSTALL COMMAND TESTS                                                        #
#                                                                              #
################################################################################


class TestInstallCommand:
    """Test install command."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_unit_install_no_registries(self) -> None:
        """Test install shows error when no registries are configured."""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ["install", "my-agent"])
            assert result.exit_code != 0
            assert "No registries configured" in result.output

    def test_unit_install_invalid_package_name(self) -> None:
        """Test that install with invalid package name reports an error."""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ["install", "@/pkg"])
            assert "Error" in result.output

    def test_unit_install_dry_run_no_registry(self) -> None:
        """Test install dry-run mode still fails without registries."""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(
                cli,
                ["install", "my-agent", "--dry-run"],
            )
            # Dry run still needs registries for registry-based installs
            assert "Dry run" in result.output or "No registries" in result.output


################################################################################
#                                                                              #
# SEARCH COMMAND TESTS                                                         #
#                                                                              #
################################################################################


class TestSearchCommand:
    """Test search command."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_unit_search_no_registries(self) -> None:
        """Test search shows error when no registries configured."""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ["search", "chatbot"])
            assert result.exit_code != 0
            assert "No registries configured" in result.output


################################################################################
#                                                                              #
# CONFIG COMMAND TESTS                                                         #
#                                                                              #
################################################################################


class TestConfigCommand:
    """Test config commands."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_unit_config_list(self) -> None:
        """Test config list displays configuration."""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ["config", "list"])
            assert result.exit_code == 0
            assert "AAM Configuration" in result.output

    def test_unit_config_get_default_platform(self) -> None:
        """Test config get for known key."""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(
                cli,
                ["config", "get", "default_platform"],
            )
            assert result.exit_code == 0
            assert "default_platform" in result.output

    def test_unit_config_get_unknown_key(self) -> None:
        """Test config get for unknown key returns error."""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(
                cli,
                ["config", "get", "nonexistent_key"],
            )
            assert result.exit_code != 0
            assert "Unknown config key" in result.output

    def test_unit_config_set_default_platform(self) -> None:
        """Test config set for a valid key."""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(
                cli,
                ["config", "set", "default_platform", "cursor"],
            )
            assert result.exit_code == 0
            assert "Set default_platform" in result.output


################################################################################
#                                                                              #
# REGISTRY COMMAND TESTS                                                       #
#                                                                              #
################################################################################


class TestRegistryCommand:
    """Test registry subcommands."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_unit_registry_help(self) -> None:
        """Test registry group shows subcommands."""
        result = self.runner.invoke(cli, ["registry", "--help"])
        assert result.exit_code == 0
        assert "init" in result.output
        assert "add" in result.output
        assert "list" in result.output
        assert "remove" in result.output

    def test_unit_registry_init(self) -> None:
        """Test registry init creates directory structure."""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(
                cli,
                ["registry", "init", "./test-reg"],
            )
            assert result.exit_code == 0
            assert Path("test-reg").is_dir()

    def test_unit_registry_list_empty(self) -> None:
        """Test registry list when no registries configured."""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ["registry", "list"])
            assert result.exit_code == 0


################################################################################
#                                                                              #
# UNINSTALL COMMAND TESTS                                                      #
#                                                                              #
################################################################################


class TestUninstallCommand:
    """Test uninstall command."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_unit_uninstall_not_installed(self) -> None:
        """Test uninstall shows error when package is not installed."""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ["uninstall", "nonexistent"])
            assert result.exit_code != 0
            assert "not installed" in result.output.lower()


################################################################################
#                                                                              #
# PACK COMMAND TESTS                                                           #
#                                                                              #
################################################################################


class TestPackCommand:
    """Test pack command."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_unit_pack_no_manifest(self) -> None:
        """Test pack shows error when no aam.yaml found."""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ["pack"])
            assert result.exit_code != 0

    def test_unit_pack_valid_package(self) -> None:
        """Test pack creates .aam archive from a valid package."""
        with self.runner.isolated_filesystem():
            # -----
            # Create a minimal valid package
            # -----
            Path("aam.yaml").write_text(
                "name: test-pkg\n"
                "version: 1.0.0\n"
                "aam_version: '1'\n"
                "description: A test package\n"
                "platforms:\n"
                "  cursor:\n"
                "    skill_scope: project\n"
                "artifacts:\n"
                "  skills:\n"
                "    - name: test-skill\n"
                "      path: skills/test\n"
                "      description: A test skill\n",
                encoding="utf-8",
            )
            Path("skills/test").mkdir(parents=True)
            Path("skills/test/SKILL.md").write_text(
                "# Test Skill\n",
                encoding="utf-8",
            )

            result = self.runner.invoke(cli, ["pack"])
            assert result.exit_code == 0
            assert "test-pkg-1.0.0.aam" in result.output


################################################################################
#                                                                              #
# NAMING UTILITY TESTS                                                         #
#                                                                              #
################################################################################


class TestNamingParseName:
    """Test parse_package_name utility."""

    def test_unit_parse_unscoped(self) -> None:
        """Test parsing an unscoped package name."""
        scope, name = parse_package_name("my-package")
        assert scope == ""
        assert name == "my-package"

    def test_unit_parse_scoped(self) -> None:
        """Test parsing a scoped package name."""
        scope, name = parse_package_name("@author/my-package")
        assert scope == "author"
        assert name == "my-package"

    def test_unit_parse_empty_rejects(self) -> None:
        """Test that empty string is rejected."""
        with pytest.raises(ValueError, match="must not be empty"):
            parse_package_name("")

    def test_unit_parse_empty_scope_rejects(self) -> None:
        """Test that @/pkg (empty scope) is rejected."""
        with pytest.raises(ValueError, match="Scope must not be empty"):
            parse_package_name("@/pkg")

    def test_unit_parse_invalid_scope_rejects(self) -> None:
        """Test that @@bad/pkg (invalid scope) is rejected."""
        with pytest.raises(ValueError, match="Invalid scope"):
            parse_package_name("@@bad/pkg")

    def test_unit_scope_allows_underscores(self) -> None:
        """Test that scope allows underscores (npm convention)."""
        scope, name = parse_package_name("@my_org/my-package")
        assert scope == "my_org"
        assert name == "my-package"

    def test_unit_name_rejects_underscores(self) -> None:
        """Test that name part rejects underscores."""
        with pytest.raises(ValueError, match="Invalid name"):
            parse_package_name("@author/my_package")

    def test_unit_parse_missing_slash(self) -> None:
        """Test that @scopename (no slash) is rejected."""
        with pytest.raises(ValueError, match="missing '/' separator"):
            parse_package_name("@scopename")


class TestNamingParseSpec:
    """Test parse_package_spec utility."""

    def test_unit_unscoped_no_version(self) -> None:
        """Test: my-pkg -> ('my-pkg', None)."""
        name, version = parse_package_spec("my-pkg")
        assert name == "my-pkg"
        assert version is None

    def test_unit_unscoped_with_version(self) -> None:
        """Test: my-pkg@1.0.0 -> ('my-pkg', '1.0.0')."""
        name, version = parse_package_spec("my-pkg@1.0.0")
        assert name == "my-pkg"
        assert version == "1.0.0"

    def test_unit_scoped_no_version(self) -> None:
        """Test: @author/my-pkg -> ('@author/my-pkg', None)."""
        name, version = parse_package_spec("@author/my-pkg")
        assert name == "@author/my-pkg"
        assert version is None

    def test_unit_scoped_with_version(self) -> None:
        """Test: @author/my-pkg@1.0.0 -> ('@author/my-pkg', '1.0.0')."""
        name, version = parse_package_spec("@author/my-pkg@1.0.0")
        assert name == "@author/my-pkg"
        assert version == "1.0.0"

    def test_unit_rejects_empty_version(self) -> None:
        """Test: @author/pkg@ -> rejected (empty version)."""
        with pytest.raises(ValueError, match="Empty version"):
            parse_package_spec("@author/pkg@")

    def test_unit_rejects_empty_scope(self) -> None:
        """Test: @/pkg -> rejected (empty scope)."""
        with pytest.raises(ValueError, match="Scope must not be empty"):
            parse_package_spec("@/pkg")

    def test_unit_rejects_empty_spec(self) -> None:
        """Test: '' -> rejected (empty spec)."""
        with pytest.raises(ValueError, match="must not be empty"):
            parse_package_spec("")

    def test_unit_unscoped_empty_version_rejects(self) -> None:
        """Test: pkg@ -> rejected (empty version for unscoped)."""
        with pytest.raises(ValueError, match="Empty version"):
            parse_package_spec("pkg@")


class TestNamingValidate:
    """Test validate_package_name utility."""

    def test_unit_valid_unscoped(self) -> None:
        """Test that valid unscoped names pass."""
        assert validate_package_name("my-package") is True
        assert validate_package_name("a") is True
        assert validate_package_name("abc123") is True

    def test_unit_valid_scoped(self) -> None:
        """Test that valid scoped names pass."""
        assert validate_package_name("@author/my-package") is True
        assert validate_package_name("@my_org/pkg") is True

    def test_unit_invalid_names(self) -> None:
        """Test that invalid names are rejected."""
        assert validate_package_name("") is False
        assert validate_package_name("UPPERCASE") is False
        assert validate_package_name("-starts-with-hyphen") is False
        assert validate_package_name("@/name") is False


class TestNamingFormat:
    """Test format_package_name and to_filesystem_name utilities."""

    def test_unit_format_scoped(self) -> None:
        """Test formatting a scoped name."""
        assert format_package_name("author", "pkg") == "@author/pkg"

    def test_unit_format_unscoped(self) -> None:
        """Test formatting an unscoped name."""
        assert format_package_name("", "pkg") == "pkg"

    def test_unit_filesystem_scoped(self) -> None:
        """Test filesystem name for scoped packages."""
        assert to_filesystem_name("author", "asvc-report") == "author--asvc-report"

    def test_unit_filesystem_unscoped(self) -> None:
        """Test filesystem name for unscoped packages."""
        assert to_filesystem_name("", "asvc-report") == "asvc-report"
