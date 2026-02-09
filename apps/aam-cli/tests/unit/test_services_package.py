"""Unit tests for package service."""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from unittest.mock import MagicMock, patch

import pytest

from aam_cli.services.package_service import (
    get_package_info,
    list_installed_packages,
)

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# TESTS                                                                        #
#                                                                              #
################################################################################


class TestPackageService:
    """Tests for package service functions."""

    def test_unit_list_packages_empty(self) -> None:
        """Verify empty list when no packages installed."""
        mock_lock = MagicMock()
        mock_lock.packages = {}

        with patch(
            "aam_cli.services.package_service.read_lock_file",
            return_value=mock_lock,
        ):
            result = list_installed_packages()
            assert result == []

    def test_unit_list_packages_with_installed(self, tmp_path: "Path") -> None:
        """Verify list structure when packages are installed."""
        mock_locked = MagicMock()
        mock_locked.version = "1.0.0"
        mock_locked.source = "local"
        mock_locked.checksum = "sha256:abc123"

        mock_lock = MagicMock()
        mock_lock.packages = {"test-pkg": mock_locked}

        packages_dir = tmp_path / "packages"
        packages_dir.mkdir()

        with patch(
            "aam_cli.services.package_service.read_lock_file",
            return_value=mock_lock,
        ):
            with patch(
                "aam_cli.services.package_service.get_packages_dir",
                return_value=packages_dir,
            ):
                result = list_installed_packages(tmp_path)
                assert len(result) == 1
                assert result[0]["name"] == "test-pkg"
                assert result[0]["version"] == "1.0.0"

    def test_unit_get_package_info_not_found(self) -> None:
        """Verify error when package not installed."""
        mock_lock = MagicMock()
        mock_lock.packages = {}

        with patch(
            "aam_cli.services.package_service.read_lock_file",
            return_value=mock_lock,
        ):
            with pytest.raises(ValueError, match="AAM_PACKAGE_NOT_FOUND"):
                get_package_info("nonexistent")
