"""Unit tests for checksum verification and backup service.

Tests verify, verify_all, backup creation, and file checksum
computation.

Reference: tasks.md T048, T053, T056.
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

from aam_cli.core.workspace import FileChecksums, LockedPackage
from aam_cli.services.checksum_service import (
    check_modifications,
    compute_file_checksums,
    create_backup,
    verify_all,
    verify_package,
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


def _create_package_dir(tmp_path: Path, pkg_name: str = "test-pkg") -> Path:
    """Create a fake installed package directory with files."""
    pkg_dir = tmp_path / ".aam" / "packages" / pkg_name
    pkg_dir.mkdir(parents=True)

    skills_dir = pkg_dir / "skills" / "my-skill"
    skills_dir.mkdir(parents=True)
    (skills_dir / "SKILL.md").write_text("# My Skill\nOriginal content.")
    (pkg_dir / "aam.yaml").write_text("name: test-pkg\nversion: 1.0.0\n")

    return pkg_dir


def _compute_hex_digest(content: str) -> str:
    """Compute SHA-256 hex digest for a string."""
    import hashlib
    return hashlib.sha256(content.encode()).hexdigest()


################################################################################
#                                                                              #
# VERIFY PACKAGE TESTS                                                         #
#                                                                              #
################################################################################


class TestVerifyPackage:
    """Tests for checksum_service.verify_package()."""

    @patch("aam_cli.services.checksum_service.get_packages_dir")
    @patch("aam_cli.services.checksum_service.get_installed_packages")
    def test_unit_verify_clean_package(
        self,
        mock_installed: MagicMock,
        mock_pkgs_dir: MagicMock,
        tmp_path: Path,
    ) -> None:
        """All files match their recorded checksums."""
        _create_package_dir(tmp_path)
        mock_pkgs_dir.return_value = tmp_path / ".aam" / "packages"

        # Compute actual checksums for the files
        skill_content = "# My Skill\nOriginal content."
        yaml_content = "name: test-pkg\nversion: 1.0.0\n"

        mock_installed.return_value = {
            "test-pkg": LockedPackage(
                version="1.0.0",
                source="local",
                checksum="sha256:abc",
                file_checksums=FileChecksums(
                    algorithm="sha256",
                    files={
                        "skills/my-skill/SKILL.md": _compute_hex_digest(skill_content),
                        "aam.yaml": _compute_hex_digest(yaml_content),
                    },
                ),
            ),
        }

        result = verify_package("test-pkg", tmp_path)

        assert result["has_checksums"] is True
        assert result["is_clean"] is True
        assert len(result["ok_files"]) == 2
        assert len(result["modified_files"]) == 0

    @patch("aam_cli.services.checksum_service.get_packages_dir")
    @patch("aam_cli.services.checksum_service.get_installed_packages")
    def test_unit_verify_modified_file(
        self,
        mock_installed: MagicMock,
        mock_pkgs_dir: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Detects a modified file with different checksum."""
        _create_package_dir(tmp_path)
        mock_pkgs_dir.return_value = tmp_path / ".aam" / "packages"

        mock_installed.return_value = {
            "test-pkg": LockedPackage(
                version="1.0.0",
                source="local",
                checksum="sha256:abc",
                file_checksums=FileChecksums(
                    algorithm="sha256",
                    files={
                        "skills/my-skill/SKILL.md": "wrong_hash_should_not_match",
                    },
                ),
            ),
        }

        result = verify_package("test-pkg", tmp_path)

        assert result["is_clean"] is False
        assert "skills/my-skill/SKILL.md" in result["modified_files"]

    @patch("aam_cli.services.checksum_service.get_packages_dir")
    @patch("aam_cli.services.checksum_service.get_installed_packages")
    def test_unit_verify_missing_file(
        self,
        mock_installed: MagicMock,
        mock_pkgs_dir: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Detects a file recorded in checksums but missing from disk."""
        _create_package_dir(tmp_path)
        mock_pkgs_dir.return_value = tmp_path / ".aam" / "packages"

        mock_installed.return_value = {
            "test-pkg": LockedPackage(
                version="1.0.0",
                source="local",
                checksum="sha256:abc",
                file_checksums=FileChecksums(
                    algorithm="sha256",
                    files={
                        "nonexistent-file.md": "some_hash",
                    },
                ),
            ),
        }

        result = verify_package("test-pkg", tmp_path)

        assert result["is_clean"] is False
        assert "nonexistent-file.md" in result["missing_files"]

    @patch("aam_cli.services.checksum_service.get_installed_packages")
    def test_unit_verify_no_checksums(
        self, mock_installed: MagicMock
    ) -> None:
        """Package without file_checksums reports has_checksums=False."""
        mock_installed.return_value = {
            "test-pkg": LockedPackage(
                version="1.0.0",
                source="local",
                checksum="sha256:abc",
                file_checksums=None,  # No checksums
            ),
        }

        result = verify_package("test-pkg")

        assert result["has_checksums"] is False
        assert result["is_clean"] is True

    @patch("aam_cli.services.checksum_service.get_installed_packages")
    def test_unit_verify_not_installed_raises(
        self, mock_installed: MagicMock
    ) -> None:
        """Verifying a non-installed package raises ValueError."""
        mock_installed.return_value = {}

        with pytest.raises(ValueError, match="AAM_PACKAGE_NOT_INSTALLED"):
            verify_package("nonexistent-pkg")


################################################################################
#                                                                              #
# VERIFY ALL TESTS                                                             #
#                                                                              #
################################################################################


class TestVerifyAll:
    """Tests for checksum_service.verify_all()."""

    @patch("aam_cli.services.checksum_service.verify_package")
    @patch("aam_cli.services.checksum_service.get_installed_packages")
    def test_unit_verify_all_aggregates(
        self,
        mock_installed: MagicMock,
        mock_verify: MagicMock,
    ) -> None:
        """verify_all aggregates results from all packages."""
        mock_installed.return_value = {
            "pkg-a": MagicMock(),
            "pkg-b": MagicMock(),
        }
        mock_verify.side_effect = [
            {"is_clean": True, "package_name": "pkg-a"},
            {"is_clean": False, "package_name": "pkg-b"},
        ]

        result = verify_all()

        assert result["total_packages"] == 2
        assert result["clean_packages"] == 1
        assert result["modified_packages"] == 1


################################################################################
#                                                                              #
# COMPUTE CHECKSUMS TESTS                                                      #
#                                                                              #
################################################################################


class TestComputeFileChecksums:
    """Tests for checksum_service.compute_file_checksums()."""

    def test_unit_compute_checksums_for_directory(
        self, tmp_path: Path
    ) -> None:
        """Computes SHA-256 for all files in a directory."""
        (tmp_path / "file1.md").write_text("content1")
        (tmp_path / "file2.md").write_text("content2")

        checksums = compute_file_checksums(tmp_path)

        assert "file1.md" in checksums
        assert "file2.md" in checksums
        assert len(checksums["file1.md"]) == 64  # SHA-256 hex length

    def test_unit_compute_checksums_specific_files(
        self, tmp_path: Path
    ) -> None:
        """Computes checksums only for specified files."""
        (tmp_path / "file1.md").write_text("content1")
        (tmp_path / "file2.md").write_text("content2")
        (tmp_path / "file3.md").write_text("content3")

        checksums = compute_file_checksums(tmp_path, files=["file1.md", "file3.md"])

        assert "file1.md" in checksums
        assert "file3.md" in checksums
        assert "file2.md" not in checksums


################################################################################
#                                                                              #
# BACKUP TESTS                                                                 #
#                                                                              #
################################################################################


class TestCreateBackup:
    """Tests for checksum_service.create_backup()."""

    @patch("aam_cli.services.checksum_service.get_packages_dir")
    @patch("aam_cli.services.checksum_service.get_global_aam_dir")
    def test_unit_backup_creates_directory(
        self,
        mock_global: MagicMock,
        mock_pkgs_dir: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Backup creates directory and copies modified files."""
        # Set up package directory with files
        pkg_dir = tmp_path / "packages" / "test-pkg"
        pkg_dir.mkdir(parents=True)
        skill_file = pkg_dir / "skills" / "my-skill" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text("Modified content")

        mock_global.return_value = tmp_path / "global"
        mock_pkgs_dir.return_value = tmp_path / "packages"

        result = create_backup(
            "test-pkg",
            ["skills/my-skill/SKILL.md"],
            tmp_path,
        )

        assert result["package_name"] == "test-pkg"
        assert len(result["backed_up_files"]) == 1

        # Verify backup file exists
        backup_dir = Path(result["backup_dir"])
        assert backup_dir.exists()
        assert (backup_dir / "skills" / "my-skill" / "SKILL.md").is_file()


################################################################################
#                                                                              #
# CHECK MODIFICATIONS TESTS                                                    #
#                                                                              #
################################################################################


class TestCheckModifications:
    """Tests for checksum_service.check_modifications()."""

    @patch("aam_cli.services.checksum_service.get_installed_packages")
    def test_unit_check_mods_not_installed(
        self, mock_installed: MagicMock
    ) -> None:
        """Non-installed package returns no modifications."""
        mock_installed.return_value = {}

        result = check_modifications("nonexistent-pkg")

        assert result["has_modifications"] is False
        assert result["has_checksums"] is False

    @patch("aam_cli.services.checksum_service.get_installed_packages")
    def test_unit_check_mods_no_checksums(
        self, mock_installed: MagicMock
    ) -> None:
        """Package without checksums returns has_checksums=False."""
        mock_installed.return_value = {
            "test-pkg": LockedPackage(
                version="1.0.0",
                source="local",
                checksum="sha256:abc",
                file_checksums=None,
            ),
        }

        result = check_modifications("test-pkg")

        assert result["has_modifications"] is False
        assert result["has_checksums"] is False

    @patch("aam_cli.services.checksum_service.get_packages_dir")
    @patch("aam_cli.services.checksum_service.get_installed_packages")
    def test_unit_check_mods_with_modifications(
        self,
        mock_installed: MagicMock,
        mock_pkgs_dir: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Detects modifications when file checksums differ."""
        _create_package_dir(tmp_path)
        mock_pkgs_dir.return_value = tmp_path / ".aam" / "packages"

        mock_installed.return_value = {
            "test-pkg": LockedPackage(
                version="1.0.0",
                source="local",
                checksum="sha256:abc",
                file_checksums=FileChecksums(
                    algorithm="sha256",
                    files={
                        "skills/my-skill/SKILL.md": "wrong_checksum",
                    },
                ),
            ),
        }

        result = check_modifications("test-pkg", tmp_path)

        assert result["has_modifications"] is True
        assert result["has_checksums"] is True
        assert "skills/my-skill/SKILL.md" in result["modified_files"]

    @patch("aam_cli.services.checksum_service.get_packages_dir")
    @patch("aam_cli.services.checksum_service.get_installed_packages")
    def test_unit_check_mods_clean(
        self,
        mock_installed: MagicMock,
        mock_pkgs_dir: MagicMock,
        tmp_path: Path,
    ) -> None:
        """No modifications when all checksums match."""
        _create_package_dir(tmp_path)
        mock_pkgs_dir.return_value = tmp_path / ".aam" / "packages"

        skill_content = "# My Skill\nOriginal content."
        yaml_content = "name: test-pkg\nversion: 1.0.0\n"

        mock_installed.return_value = {
            "test-pkg": LockedPackage(
                version="1.0.0",
                source="local",
                checksum="sha256:abc",
                file_checksums=FileChecksums(
                    algorithm="sha256",
                    files={
                        "skills/my-skill/SKILL.md": _compute_hex_digest(skill_content),
                        "aam.yaml": _compute_hex_digest(yaml_content),
                    },
                ),
            ),
        }

        result = check_modifications("test-pkg", tmp_path)

        assert result["has_modifications"] is False
        assert result["has_checksums"] is True
