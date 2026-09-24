"""Unit tests for workspace universal/legacy lock file reading functions.

Tests ``get_installed_packages()``, ``get_installed_packages_universal()``,
and ``is_package_installed()`` which read from both the universal lock file
(``package.agent.lock``) and the legacy lock file (``aam-lock.yaml``).
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

from aam_cli.core.workspace import (
    LockedPackage,
    LockedPackageV2,
    LockFile,
    UniversalLockFile,
    get_installed_packages,
    get_installed_packages_universal,
    is_package_installed,
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


def _universal_lock_with_packages() -> UniversalLockFile:
    """Build a universal lock file containing one LockedPackageV2."""
    return UniversalLockFile(
        packages={
            "test-pkg": LockedPackageV2(
                version="1.0.0",
                source="test",
                integrity="sha256-abc123",
            ),
        },
    )


def _legacy_lock_with_packages() -> LockFile:
    """Build a legacy lock file containing one LockedPackage."""
    return LockFile(
        packages={
            "legacy-pkg": LockedPackage(
                version="0.9.0",
                source="local",
                checksum="sha256:def456",
            ),
        },
    )


def _empty_universal_lock() -> UniversalLockFile:
    """Build an empty universal lock file (no packages)."""
    return UniversalLockFile()


def _empty_legacy_lock() -> LockFile:
    """Build an empty legacy lock file (no packages)."""
    return LockFile()


################################################################################
#                                                                              #
# GET INSTALLED PACKAGES UNIVERSAL TESTS                                       #
#                                                                              #
################################################################################


class TestGetInstalledPackagesUniversal:
    """Tests for ``get_installed_packages_universal()``."""

    @patch("aam_cli.core.workspace.read_lock_file")
    @patch("aam_cli.core.workspace.read_universal_lock_file")
    def test_unit_returns_universal_lock_packages_when_exists(
        self,
        mock_read_universal: MagicMock,
        mock_read_legacy: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Returns packages from the universal lock file when it has entries."""
        mock_read_universal.return_value = _universal_lock_with_packages()
        mock_read_legacy.return_value = _empty_legacy_lock()

        result = get_installed_packages_universal(tmp_path)

        assert "test-pkg" in result
        assert isinstance(result["test-pkg"], LockedPackageV2)
        assert result["test-pkg"].version == "1.0.0"
        assert result["test-pkg"].integrity == "sha256-abc123"
        mock_read_legacy.assert_not_called()

    @patch("aam_cli.core.workspace.read_lock_file")
    @patch("aam_cli.core.workspace.read_universal_lock_file")
    def test_unit_falls_back_to_legacy_when_universal_empty(
        self,
        mock_read_universal: MagicMock,
        mock_read_legacy: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Converts legacy LockedPackage entries to LockedPackageV2 when
        the universal lock file is empty."""
        mock_read_universal.return_value = _empty_universal_lock()
        mock_read_legacy.return_value = _legacy_lock_with_packages()

        result = get_installed_packages_universal(tmp_path)

        assert "legacy-pkg" in result
        assert isinstance(result["legacy-pkg"], LockedPackageV2)
        assert result["legacy-pkg"].version == "0.9.0"
        # Legacy checksum is mapped to integrity field
        assert result["legacy-pkg"].integrity == "sha256:def456"

    @patch("aam_cli.core.workspace.read_lock_file")
    @patch("aam_cli.core.workspace.read_universal_lock_file")
    def test_unit_returns_empty_when_no_lock_files(
        self,
        mock_read_universal: MagicMock,
        mock_read_legacy: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Returns an empty dict when neither lock file has packages."""
        mock_read_universal.return_value = _empty_universal_lock()
        mock_read_legacy.return_value = _empty_legacy_lock()

        result = get_installed_packages_universal(tmp_path)

        assert result == {}

    @patch("aam_cli.core.workspace.read_lock_file")
    @patch("aam_cli.core.workspace.read_universal_lock_file")
    def test_unit_universal_takes_priority_over_legacy(
        self,
        mock_read_universal: MagicMock,
        mock_read_legacy: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Universal lock file takes priority; legacy is never read."""
        mock_read_universal.return_value = _universal_lock_with_packages()
        mock_read_legacy.return_value = _legacy_lock_with_packages()

        result = get_installed_packages_universal(tmp_path)

        # Only the universal package should appear
        assert "test-pkg" in result
        assert "legacy-pkg" not in result
        mock_read_legacy.assert_not_called()


################################################################################
#                                                                              #
# GET INSTALLED PACKAGES TESTS                                                 #
#                                                                              #
################################################################################


class TestGetInstalledPackages:
    """Tests for ``get_installed_packages()``."""

    @patch("aam_cli.core.workspace.read_lock_file")
    @patch("aam_cli.core.workspace.read_universal_lock_file")
    def test_unit_converts_universal_to_locked_package(
        self,
        mock_read_universal: MagicMock,
        mock_read_legacy: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Converts LockedPackageV2 from universal lock to LockedPackage."""
        mock_read_universal.return_value = _universal_lock_with_packages()
        mock_read_legacy.return_value = _empty_legacy_lock()

        result = get_installed_packages(tmp_path)

        assert "test-pkg" in result
        assert isinstance(result["test-pkg"], LockedPackage)
        assert result["test-pkg"].version == "1.0.0"
        # V2 integrity is mapped to checksum
        assert result["test-pkg"].checksum == "sha256-abc123"
        mock_read_legacy.assert_not_called()

    @patch("aam_cli.core.workspace.read_lock_file")
    @patch("aam_cli.core.workspace.read_universal_lock_file")
    def test_unit_falls_back_to_legacy_lock_file(
        self,
        mock_read_universal: MagicMock,
        mock_read_legacy: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Returns legacy LockedPackage entries when universal is empty."""
        mock_read_universal.return_value = _empty_universal_lock()
        mock_read_legacy.return_value = _legacy_lock_with_packages()

        result = get_installed_packages(tmp_path)

        assert "legacy-pkg" in result
        assert isinstance(result["legacy-pkg"], LockedPackage)
        assert result["legacy-pkg"].version == "0.9.0"
        assert result["legacy-pkg"].checksum == "sha256:def456"

    @patch("aam_cli.core.workspace.read_lock_file")
    @patch("aam_cli.core.workspace.read_universal_lock_file")
    def test_unit_returns_empty_when_no_packages(
        self,
        mock_read_universal: MagicMock,
        mock_read_legacy: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Returns an empty dict when neither lock file has packages."""
        mock_read_universal.return_value = _empty_universal_lock()
        mock_read_legacy.return_value = _empty_legacy_lock()

        result = get_installed_packages(tmp_path)

        assert result == {}


################################################################################
#                                                                              #
# IS PACKAGE INSTALLED TESTS                                                   #
#                                                                              #
################################################################################


class TestIsPackageInstalled:
    """Tests for ``is_package_installed()``."""

    @patch("aam_cli.core.workspace.read_lock_file")
    @patch("aam_cli.core.workspace.read_universal_lock_file")
    def test_unit_finds_package_in_universal_lock(
        self,
        mock_read_universal: MagicMock,
        mock_read_legacy: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Returns True when the package exists in the universal lock file."""
        mock_read_universal.return_value = _universal_lock_with_packages()
        mock_read_legacy.return_value = _empty_legacy_lock()

        result = is_package_installed("test-pkg", tmp_path)

        assert result is True
        mock_read_legacy.assert_not_called()

    @patch("aam_cli.core.workspace.read_lock_file")
    @patch("aam_cli.core.workspace.read_universal_lock_file")
    def test_unit_finds_package_in_legacy_lock(
        self,
        mock_read_universal: MagicMock,
        mock_read_legacy: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Returns True when the package exists only in the legacy lock file."""
        mock_read_universal.return_value = _empty_universal_lock()
        mock_read_legacy.return_value = _legacy_lock_with_packages()

        result = is_package_installed("legacy-pkg", tmp_path)

        assert result is True

    @patch("aam_cli.core.workspace.read_lock_file")
    @patch("aam_cli.core.workspace.read_universal_lock_file")
    def test_unit_returns_false_when_not_installed(
        self,
        mock_read_universal: MagicMock,
        mock_read_legacy: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Returns False when the package is not in either lock file."""
        mock_read_universal.return_value = _empty_universal_lock()
        mock_read_legacy.return_value = _empty_legacy_lock()

        result = is_package_installed("nonexistent-pkg", tmp_path)

        assert result is False

    @patch("aam_cli.core.workspace.read_lock_file")
    @patch("aam_cli.core.workspace.read_universal_lock_file")
    def test_unit_universal_checked_first(
        self,
        mock_read_universal: MagicMock,
        mock_read_legacy: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Universal lock file is checked first; legacy is skipped when
        the universal file has packages (even if the package is absent)."""
        mock_read_universal.return_value = _universal_lock_with_packages()
        mock_read_legacy.return_value = _legacy_lock_with_packages()

        # "test-pkg" is in universal, so universal.packages is non-empty
        # and the function returns based on the universal lookup alone.
        result = is_package_installed("test-pkg", tmp_path)

        assert result is True
        mock_read_legacy.assert_not_called()

        # Even when searching for a package only in legacy, the function
        # will NOT fall back because universal.packages is non-empty.
        mock_read_universal.reset_mock()
        mock_read_legacy.reset_mock()

        result = is_package_installed("legacy-pkg", tmp_path)

        assert result is False
        mock_read_legacy.assert_not_called()
