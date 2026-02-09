"""Unit tests for doctor service."""

import logging
import sys
from unittest.mock import MagicMock, patch

import pytest

from aam_cli.services.doctor_service import run_diagnostics

logger = logging.getLogger(__name__)


class TestDoctorService:

    def test_unit_doctor_all_healthy(self, tmp_path) -> None:
        mock_config = MagicMock()
        mock_config.registries = []

        mock_lock = MagicMock()
        mock_lock.packages = {}

        with patch("aam_cli.services.doctor_service.load_config", return_value=mock_config):
            with patch("aam_cli.services.doctor_service.read_lock_file", return_value=mock_lock):
                with patch("aam_cli.services.doctor_service.get_packages_dir", return_value=tmp_path / "packages"):
                    (tmp_path / "packages").mkdir()
                    report = run_diagnostics(tmp_path)
                    assert report["healthy"] is True

    def test_unit_doctor_config_error(self, tmp_path) -> None:
        with patch("aam_cli.services.doctor_service.load_config", side_effect=Exception("bad config")):
            with patch("aam_cli.services.doctor_service.read_lock_file", return_value=MagicMock(packages={})):
                with patch("aam_cli.services.doctor_service.get_packages_dir", return_value=tmp_path / "packages"):
                    (tmp_path / "packages").mkdir()
                    report = run_diagnostics(tmp_path)
                    config_check = next(c for c in report["checks"] if c["name"] == "config_valid")
                    assert config_check["status"] == "fail"
