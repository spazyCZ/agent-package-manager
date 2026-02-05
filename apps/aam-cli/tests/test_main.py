"""Tests for main CLI module."""

from click.testing import CliRunner

from aam_cli.main import cli


class TestCLI:
    """Test CLI commands."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_cli_version(self) -> None:
        """Test --version flag."""
        result = self.runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_cli_help(self) -> None:
        """Test --help flag."""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "AAM - Agent Package Manager" in result.output

    def test_info_command(self) -> None:
        """Test info command."""
        result = self.runner.invoke(cli, ["info"])
        assert result.exit_code == 0
        assert "AAM CLI" in result.output

    def test_list_command(self) -> None:
        """Test list command."""
        result = self.runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        assert "Installed Packages" in result.output

    def test_show_command(self) -> None:
        """Test show command."""
        result = self.runner.invoke(cli, ["show", "test-package"])
        assert result.exit_code == 0
        assert "test-package" in result.output


class TestInstallCommand:
    """Test install command."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_install_single_package(self) -> None:
        """Test installing a single package."""
        result = self.runner.invoke(cli, ["install", "my-agent"])
        assert result.exit_code == 0
        assert "Installed" in result.output
        assert "my-agent" in result.output

    def test_install_with_version(self) -> None:
        """Test installing a package with version."""
        result = self.runner.invoke(cli, ["install", "my-agent@1.0.0"])
        assert result.exit_code == 0
        assert "@1.0.0" in result.output

    def test_install_dry_run(self) -> None:
        """Test dry run mode."""
        result = self.runner.invoke(cli, ["install", "my-agent", "--dry-run"])
        assert result.exit_code == 0
        assert "Dry run" in result.output


class TestSearchCommand:
    """Test search command."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_search(self) -> None:
        """Test basic search."""
        result = self.runner.invoke(cli, ["search", "chatbot"])
        assert result.exit_code == 0
        assert "Search Results" in result.output


class TestConfigCommand:
    """Test config commands."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_config_get_all(self) -> None:
        """Test getting all config."""
        result = self.runner.invoke(cli, ["config", "get"])
        assert result.exit_code == 0
        assert "registry" in result.output

    def test_config_set(self) -> None:
        """Test setting config."""
        result = self.runner.invoke(cli, ["config", "set", "timeout", "60"])
        assert result.exit_code == 0
        assert "Set timeout=60" in result.output
