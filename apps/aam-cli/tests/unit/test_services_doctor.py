"""Unit tests for doctor service."""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import yaml

from aam_cli.services.doctor_service import (
    _check_config_files,
    _check_default_platform,
    _check_uaaps_conformance,
    run_diagnostics,
)

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# HELPERS                                                                      #
#                                                                              #
################################################################################

# Patch targets within the doctor_service module
_SVC = "aam_cli.services.doctor_service"


def _write_yaml(path: Path, data: dict | str) -> None:
    """Write YAML content to a file, creating parents as needed.

    Args:
        path: Target file path.
        data: Dictionary to serialize, or raw string for invalid-YAML tests.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        path.write_text(data, encoding="utf-8")
    else:
        path.write_text(
            yaml.safe_dump(data, default_flow_style=False),
            encoding="utf-8",
        )


################################################################################
#                                                                              #
# EXISTING TESTS                                                               #
#                                                                              #
################################################################################


class TestDoctorService:
    """Tests for the top-level ``run_diagnostics`` function."""

    def test_unit_doctor_all_healthy(self, tmp_path) -> None:
        """All checks pass when config, lock, and packages are valid."""
        mock_config = MagicMock()
        mock_config.registries = []
        mock_config.default_platform = "cursor"
        mock_config.active_platforms = ["cursor"]

        mock_lock = MagicMock()
        mock_lock.packages = {}

        global_cfg = tmp_path / "global" / "config.yaml"
        project_cfg = tmp_path / "project" / ".aam" / "config.yaml"

        # Neither config file exists — should report "not found, using defaults"
        with (
            patch(f"{_SVC}.load_config", return_value=mock_config),
            patch(f"{_SVC}.read_lock_file", return_value=mock_lock),
            patch(f"{_SVC}.get_packages_dir", return_value=tmp_path / "packages"),
            patch(f"{_SVC}.get_global_config_path", return_value=global_cfg),
            patch(f"{_SVC}.get_project_config_path", return_value=project_cfg),
        ):
            (tmp_path / "packages").mkdir()
            report = run_diagnostics(tmp_path)
            assert report["healthy"] is True

    def test_unit_doctor_config_error(self, tmp_path) -> None:
        """Report failure when merged config cannot be loaded."""
        global_cfg = tmp_path / "global" / "config.yaml"
        project_cfg = tmp_path / "project" / ".aam" / "config.yaml"

        with (
            patch(f"{_SVC}.load_config", side_effect=Exception("bad config")),
            patch(f"{_SVC}.read_lock_file", return_value=MagicMock(packages={})),
            patch(f"{_SVC}.get_packages_dir", return_value=tmp_path / "packages"),
            patch(f"{_SVC}.get_global_config_path", return_value=global_cfg),
            patch(f"{_SVC}.get_project_config_path", return_value=project_cfg),
        ):
            (tmp_path / "packages").mkdir()
            report = run_diagnostics(tmp_path)
            config_check = next(
                c for c in report["checks"] if c["name"] == "config_valid"
            )
            assert config_check["status"] == "fail"

    def test_unit_doctor_report_includes_config_file_checks(
        self, tmp_path
    ) -> None:
        """Verify that run_diagnostics includes global_config and project_config checks."""
        mock_config = MagicMock()
        mock_config.registries = []
        mock_config.default_platform = "cursor"
        mock_config.active_platforms = ["cursor"]

        mock_lock = MagicMock()
        mock_lock.packages = {}

        global_cfg = tmp_path / "global" / "config.yaml"
        project_cfg = tmp_path / "project" / ".aam" / "config.yaml"

        with (
            patch(f"{_SVC}.load_config", return_value=mock_config),
            patch(f"{_SVC}.read_lock_file", return_value=mock_lock),
            patch(f"{_SVC}.get_packages_dir", return_value=tmp_path / "packages"),
            patch(f"{_SVC}.get_global_config_path", return_value=global_cfg),
            patch(f"{_SVC}.get_project_config_path", return_value=project_cfg),
        ):
            (tmp_path / "packages").mkdir()
            report = run_diagnostics(tmp_path)

            check_names = [c["name"] for c in report["checks"]]
            assert "global_config" in check_names
            assert "project_config" in check_names

            # Config file checks appear before config_valid
            gc_idx = check_names.index("global_config")
            pc_idx = check_names.index("project_config")
            cv_idx = check_names.index("config_valid")
            assert gc_idx < cv_idx
            assert pc_idx < cv_idx


################################################################################
#                                                                              #
# CONFIG FILE CHECK TESTS                                                      #
#                                                                              #
################################################################################


class TestCheckConfigFiles:
    """Tests for the ``_check_config_files`` diagnostic check."""

    def test_unit_doctor_config_files_both_exist_valid(
        self, tmp_path
    ) -> None:
        """Both global and project config exist with valid YAML and schema."""
        global_cfg = tmp_path / "global" / "config.yaml"
        project_cfg = tmp_path / "project" / ".aam" / "config.yaml"

        valid_config = {"default_platform": "cursor", "active_platforms": ["cursor"]}
        _write_yaml(global_cfg, valid_config)
        _write_yaml(project_cfg, valid_config)

        with (
            patch(f"{_SVC}.get_global_config_path", return_value=global_cfg),
            patch(f"{_SVC}.get_project_config_path", return_value=project_cfg),
        ):
            checks = _check_config_files(tmp_path)

        assert len(checks) == 2

        # -----
        # Global config: pass with path in message
        # -----
        gc = checks[0]
        assert gc["name"] == "global_config"
        assert gc["status"] == "pass"
        assert str(global_cfg) in gc["message"]
        assert "(valid)" in gc["message"]

        # -----
        # Project config: pass with path in message
        # -----
        pc = checks[1]
        assert pc["name"] == "project_config"
        assert pc["status"] == "pass"
        assert str(project_cfg) in pc["message"]
        assert "(valid)" in pc["message"]

    def test_unit_doctor_config_files_global_only(self, tmp_path) -> None:
        """Only global config exists; project reports pass (not found is normal)."""
        global_cfg = tmp_path / "global" / "config.yaml"
        project_cfg = tmp_path / "project" / ".aam" / "config.yaml"

        _write_yaml(global_cfg, {"default_platform": "claude-code"})

        with (
            patch(f"{_SVC}.get_global_config_path", return_value=global_cfg),
            patch(f"{_SVC}.get_project_config_path", return_value=project_cfg),
        ):
            checks = _check_config_files(tmp_path)

        assert len(checks) == 2

        gc = checks[0]
        assert gc["status"] == "pass"
        assert "(valid)" in gc["message"]

        pc = checks[1]
        assert pc["status"] == "pass"
        assert "not found, using defaults" in pc["message"]
        assert str(project_cfg) in pc["message"]

    def test_unit_doctor_config_files_project_only(self, tmp_path) -> None:
        """Only project config exists; global reports not found."""
        global_cfg = tmp_path / "global" / "config.yaml"
        project_cfg = tmp_path / "project" / ".aam" / "config.yaml"

        _write_yaml(project_cfg, {"default_platform": "copilot"})

        with (
            patch(f"{_SVC}.get_global_config_path", return_value=global_cfg),
            patch(f"{_SVC}.get_project_config_path", return_value=project_cfg),
        ):
            checks = _check_config_files(tmp_path)

        assert len(checks) == 2

        gc = checks[0]
        assert gc["status"] == "pass"
        assert "not found, using defaults" in gc["message"]

        pc = checks[1]
        assert pc["status"] == "pass"
        assert "(valid)" in pc["message"]

    def test_unit_doctor_config_files_neither_exists(self, tmp_path) -> None:
        """Neither config file exists; both pass (missing config is normal)."""
        global_cfg = tmp_path / "global" / "config.yaml"
        project_cfg = tmp_path / "project" / ".aam" / "config.yaml"

        with (
            patch(f"{_SVC}.get_global_config_path", return_value=global_cfg),
            patch(f"{_SVC}.get_project_config_path", return_value=project_cfg),
        ):
            checks = _check_config_files(tmp_path)

        assert len(checks) == 2

        gc, pc = checks[0], checks[1]
        assert gc["status"] == "pass"
        assert "not found, using defaults" in gc["message"]
        assert pc["status"] == "pass"
        assert "not found, using defaults" in pc["message"]

    def test_unit_doctor_config_files_invalid_yaml(self, tmp_path) -> None:
        """Config file with broken YAML reports fail status."""
        global_cfg = tmp_path / "global" / "config.yaml"
        project_cfg = tmp_path / "project" / ".aam" / "config.yaml"

        # Write syntactically invalid YAML
        _write_yaml(global_cfg, "  invalid:\nyaml: [unterminated")

        with (
            patch(f"{_SVC}.get_global_config_path", return_value=global_cfg),
            patch(f"{_SVC}.get_project_config_path", return_value=project_cfg),
        ):
            checks = _check_config_files(tmp_path)

        gc = checks[0]
        assert gc["name"] == "global_config"
        assert gc["status"] == "fail"
        assert "invalid YAML" in gc["message"]
        assert gc["suggestion"] is not None

        # Project config does not exist — pass (missing config is normal)
        pc = checks[1]
        assert pc["status"] == "pass"
        assert "not found, using defaults" in pc["message"]

    def test_unit_doctor_config_files_invalid_schema(self, tmp_path) -> None:
        """Config file with valid YAML but invalid schema reports fail."""
        global_cfg = tmp_path / "global" / "config.yaml"
        project_cfg = tmp_path / "project" / ".aam" / "config.yaml"

        # Valid YAML but wrong types for AamConfig fields
        bad_schema = {
            "default_platform": 12345,  # should be str, but Pydantic coerces
            "active_platforms": "not-a-list",  # should be list[str]
        }
        _write_yaml(global_cfg, bad_schema)

        with (
            patch(f"{_SVC}.get_global_config_path", return_value=global_cfg),
            patch(f"{_SVC}.get_project_config_path", return_value=project_cfg),
        ):
            checks = _check_config_files(tmp_path)

        gc = checks[0]
        assert gc["name"] == "global_config"
        assert gc["status"] == "fail"
        assert "schema error" in gc["message"]
        assert gc["suggestion"] is not None

    def test_unit_doctor_config_files_empty_file(self, tmp_path) -> None:
        """Empty config file is valid — defaults will be used."""
        global_cfg = tmp_path / "global" / "config.yaml"
        project_cfg = tmp_path / "project" / ".aam" / "config.yaml"

        # Create an empty file
        global_cfg.parent.mkdir(parents=True, exist_ok=True)
        global_cfg.write_text("", encoding="utf-8")

        with (
            patch(f"{_SVC}.get_global_config_path", return_value=global_cfg),
            patch(f"{_SVC}.get_project_config_path", return_value=project_cfg),
        ):
            checks = _check_config_files(tmp_path)

        gc = checks[0]
        assert gc["name"] == "global_config"
        assert gc["status"] == "pass"
        assert "empty, using defaults" in gc["message"]


################################################################################
#                                                                              #
# UAAPS CONFORMANCE CHECK TESTS                                               #
#                                                                              #
################################################################################


class TestCheckUaapsConformance:
    """Tests for the ``_check_uaaps_conformance`` informational check."""

    def test_unit_doctor_uaaps_conformance_pass(self) -> None:
        """Reports pass with spec version and conformance level."""
        result = _check_uaaps_conformance()

        assert result["name"] == "uaaps_conformance"
        assert result["status"] == "pass"
        assert "0.6.0" in result["message"]
        assert "Level 2" in result["message"]
        assert "Installer" in result["message"]


################################################################################
#                                                                              #
# DEFAULT PLATFORM CHECK TESTS                                                 #
#                                                                              #
################################################################################


class TestCheckDefaultPlatform:
    """Tests for the ``_check_default_platform`` diagnostic check."""

    def test_unit_doctor_default_platform_cursor(self, tmp_path) -> None:
        """Reports pass for the default 'cursor' platform."""
        mock_config = MagicMock()
        mock_config.default_platform = "cursor"
        mock_config.active_platforms = ["cursor"]

        with patch(f"{_SVC}.load_config", return_value=mock_config):
            result = _check_default_platform(tmp_path)

        assert result["name"] == "default_platform"
        assert result["status"] == "pass"
        assert "cursor" in result["message"]
        assert "active:" in result["message"]

    def test_unit_doctor_default_platform_multiple_active(
        self, tmp_path
    ) -> None:
        """Reports all active platforms in the message."""
        mock_config = MagicMock()
        mock_config.default_platform = "copilot"
        mock_config.active_platforms = ["copilot", "cursor", "claude-code"]

        with patch(f"{_SVC}.load_config", return_value=mock_config):
            result = _check_default_platform(tmp_path)

        assert result["status"] == "pass"
        assert "copilot" in result["message"]
        assert "cursor" in result["message"]
        assert "claude-code" in result["message"]

    def test_unit_doctor_default_platform_unrecognised(
        self, tmp_path
    ) -> None:
        """Warns when default platform is not a supported value."""
        mock_config = MagicMock()
        mock_config.default_platform = "unknown-ide"
        mock_config.active_platforms = ["unknown-ide"]

        with patch(f"{_SVC}.load_config", return_value=mock_config):
            result = _check_default_platform(tmp_path)

        assert result["status"] == "warn"
        assert "unknown-ide" in result["message"]
        assert "not recognised" in result["message"]

    def test_unit_doctor_default_platform_not_in_active(
        self, tmp_path
    ) -> None:
        """Warns when default_platform is missing from active_platforms."""
        mock_config = MagicMock()
        mock_config.default_platform = "claude-code"
        mock_config.active_platforms = ["cursor"]

        with patch(f"{_SVC}.load_config", return_value=mock_config):
            result = _check_default_platform(tmp_path)

        assert result["status"] == "warn"
        assert "claude-code" in result["message"]
        assert "not in active_platforms" in result["message"]
        assert result["suggestion"] is not None

    def test_unit_doctor_default_platform_legacy_alias(
        self, tmp_path
    ) -> None:
        """Legacy alias 'claude' is normalized to 'claude-code'."""
        mock_config = MagicMock()
        mock_config.default_platform = "claude"
        mock_config.active_platforms = ["claude"]

        with patch(f"{_SVC}.load_config", return_value=mock_config):
            result = _check_default_platform(tmp_path)

        assert result["status"] == "pass"
        assert "claude-code" in result["message"]
        assert "legacy alias" in result["message"]

    def test_unit_doctor_default_platform_config_failure(
        self, tmp_path
    ) -> None:
        """Reports warn when config cannot be loaded."""
        with patch(f"{_SVC}.load_config", side_effect=Exception("boom")):
            result = _check_default_platform(tmp_path)

        assert result["status"] == "warn"
        assert "Could not determine" in result["message"]
