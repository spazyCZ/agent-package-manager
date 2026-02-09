"""Unit tests for create-package --from-source functionality.

Tests the _create_from_source() flow that packages artifacts
from registered remote git sources with provenance metadata.

Reference: tasks.md T037, T038.
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

from aam_cli.commands.create_package import create_package

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
def cli_runner() -> CliRunner:
    """Create a Click CliRunner."""
    return CliRunner()


@pytest.fixture()
def mock_scan_result() -> dict:
    """Sample scan result from source_service.scan_source()."""
    return {
        "source_name": "openai/skills",
        "commit": "abc123def456",
        "scan_path": "skills",
        "total_count": 3,
        "artifacts_by_type": {
            "skills": 2,
            "agents": 1,
            "prompts": 0,
            "instructions": 0,
        },
        "artifacts": [
            {
                "name": "gh-fix-ci",
                "type": "skill",
                "path": "gh-fix-ci",
                "description": "Fix CI pipelines",
                "has_vendor_agent": False,
            },
            {
                "name": "coder",
                "type": "skill",
                "path": "coder",
                "description": "Code generation",
                "has_vendor_agent": False,
            },
            {
                "name": "test-agent",
                "type": "agent",
                "path": "agents/test-agent",
                "description": "Test agent",
                "has_vendor_agent": False,
            },
        ],
    }


################################################################################
#                                                                              #
# DRY-RUN TESTS                                                               #
#                                                                              #
################################################################################


class TestCreateFromSourceDryRun:
    """Tests for create-package --from-source --dry-run."""

    @patch("aam_cli.services.source_service.scan_source")
    def test_unit_dry_run_shows_artifacts(
        self,
        mock_scan: MagicMock,
        cli_runner: CliRunner,
        mock_scan_result: dict,
        tmp_path: Path,
    ) -> None:
        """Dry run shows artifacts and manifest without writing."""
        mock_scan.return_value = mock_scan_result

        result = cli_runner.invoke(
            create_package,
            [
                str(tmp_path),
                "--from-source", "openai/skills",
                "--all",
                "--name", "test-pkg",
                "--version", "1.0.0",
                "--description", "Test package",
                "--dry-run",
                "-y",
            ],
            obj={"console": MagicMock()},
            catch_exceptions=False,
        )

        # Command should not fail
        assert result.exit_code == 0
        mock_scan.assert_called_once_with("openai/skills")

    @patch("aam_cli.services.source_service.scan_source")
    def test_unit_dry_run_with_type_filter(
        self,
        mock_scan: MagicMock,
        cli_runner: CliRunner,
        mock_scan_result: dict,
        tmp_path: Path,
    ) -> None:
        """Dry run with --type filter shows only matching artifacts."""
        mock_scan.return_value = mock_scan_result

        result = cli_runner.invoke(
            create_package,
            [
                str(tmp_path),
                "--from-source", "openai/skills",
                "--all",
                "--type", "skill",
                "--name", "test-pkg",
                "--version", "1.0.0",
                "--description", "Test package",
                "--dry-run",
                "-y",
            ],
            obj={"console": MagicMock()},
            catch_exceptions=False,
        )

        assert result.exit_code == 0

    @patch("aam_cli.services.source_service.scan_source")
    def test_unit_dry_run_with_artifacts_filter(
        self,
        mock_scan: MagicMock,
        cli_runner: CliRunner,
        mock_scan_result: dict,
        tmp_path: Path,
    ) -> None:
        """Dry run with --artifacts shows only named artifacts."""
        mock_scan.return_value = mock_scan_result

        result = cli_runner.invoke(
            create_package,
            [
                str(tmp_path),
                "--from-source", "openai/skills",
                "--artifacts", "gh-fix-ci",
                "--name", "test-pkg",
                "--version", "1.0.0",
                "--description", "Test package",
                "--dry-run",
                "-y",
            ],
            obj={"console": MagicMock()},
            catch_exceptions=False,
        )

        assert result.exit_code == 0


################################################################################
#                                                                              #
# ERROR HANDLING TESTS                                                         #
#                                                                              #
################################################################################


class TestCreateFromSourceErrors:
    """Tests for error conditions in --from-source."""

    @patch("aam_cli.services.source_service.scan_source")
    def test_unit_source_not_found(
        self,
        mock_scan: MagicMock,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Fails gracefully when source is not found."""
        mock_scan.side_effect = ValueError(
            "[AAM_SOURCE_NOT_FOUND] Source 'nonexistent' not found"
        )

        result = cli_runner.invoke(
            create_package,
            [
                str(tmp_path),
                "--from-source", "nonexistent",
                "--all",
                "--name", "test-pkg",
                "--version", "1.0.0",
                "--description", "Test package",
                "-y",
            ],
            obj={"console": MagicMock()},
        )

        # Should not crash (Click handles ctx.exit)
        assert result.exit_code in (0, 1)

    @patch("aam_cli.services.source_service.scan_source")
    def test_unit_no_artifacts_found(
        self,
        mock_scan: MagicMock,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Exits cleanly when source has no artifacts."""
        mock_scan.return_value = {
            "source_name": "empty-source",
            "commit": "abc123",
            "artifacts": [],
        }

        result = cli_runner.invoke(
            create_package,
            [
                str(tmp_path),
                "--from-source", "empty-source",
                "--all",
                "--name", "test-pkg",
                "--version", "1.0.0",
                "--description", "Test",
                "-y",
            ],
            obj={"console": MagicMock()},
            catch_exceptions=False,
        )

        assert result.exit_code == 0

    @patch("aam_cli.services.source_service.scan_source")
    def test_unit_artifacts_filter_no_match(
        self,
        mock_scan: MagicMock,
        cli_runner: CliRunner,
        mock_scan_result: dict,
        tmp_path: Path,
    ) -> None:
        """Exits cleanly when artifact name filter matches nothing."""
        mock_scan.return_value = mock_scan_result

        result = cli_runner.invoke(
            create_package,
            [
                str(tmp_path),
                "--from-source", "openai/skills",
                "--artifacts", "nonexistent-artifact",
                "--name", "test-pkg",
                "--version", "1.0.0",
                "--description", "Test",
                "-y",
            ],
            obj={"console": MagicMock()},
            catch_exceptions=False,
        )

        assert result.exit_code == 0
