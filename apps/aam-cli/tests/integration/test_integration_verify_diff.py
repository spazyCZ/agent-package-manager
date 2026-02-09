"""Integration tests for verify and diff commands.

Tests package integrity verification and diff generation
using real temporary file structures.

Reference: tasks.md T057.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from pathlib import Path

import pytest

from aam_cli.core.workspace import (
    FileChecksums,
    LockedPackage,
    LockFile,
    write_lock_file,
)
from aam_cli.services.checksum_service import (
    check_modifications,
    compute_file_checksums,
    create_backup,
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


@pytest.fixture()
def installed_package(tmp_path: Path) -> tuple[Path, str]:
    """Create a fake installed package with checksums in lock file.

    Creates:
    - .aam/packages/test-pkg/ with files
    - .aam/aam-lock.yaml with file checksums

    Returns:
        Tuple of (project_dir, package_name).
    """
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    # -----
    # Create package directory
    # -----
    pkg_dir = project_dir / ".aam" / "packages" / "test-pkg"
    pkg_dir.mkdir(parents=True)

    skill_dir = pkg_dir / "skills" / "my-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# My Skill\nOriginal content.")
    (pkg_dir / "aam.yaml").write_text("name: test-pkg\nversion: 1.0.0\n")

    # -----
    # Compute real checksums
    # -----
    checksums = compute_file_checksums(pkg_dir)

    # -----
    # Write lock file with checksums
    # -----
    lock = LockFile(
        packages={
            "test-pkg": LockedPackage(
                version="1.0.0",
                source="local",
                checksum="sha256:dummy",
                file_checksums=FileChecksums(
                    algorithm="sha256",
                    files=checksums,
                ),
            ),
        },
    )
    write_lock_file(lock, project_dir)

    return project_dir, "test-pkg"


################################################################################
#                                                                              #
# VERIFY TESTS                                                                 #
#                                                                              #
################################################################################


class TestVerifyIntegration:
    """Integration tests for package verification."""

    @pytest.mark.integration
    def test_integration_verify_clean_package(
        self, installed_package: tuple[Path, str]
    ) -> None:
        """Verify a clean package reports no modifications."""
        project_dir, pkg_name = installed_package

        result = verify_package(pkg_name, project_dir)

        assert result["has_checksums"] is True
        assert result["is_clean"] is True
        assert len(result["modified_files"]) == 0
        assert len(result["missing_files"]) == 0

    @pytest.mark.integration
    def test_integration_verify_modified_file(
        self, installed_package: tuple[Path, str]
    ) -> None:
        """Verify detects a modified file correctly."""
        project_dir, pkg_name = installed_package

        # Modify a file
        skill_path = (
            project_dir / ".aam" / "packages" / pkg_name
            / "skills" / "my-skill" / "SKILL.md"
        )
        skill_path.write_text("# My Skill\nModified content!!")

        result = verify_package(pkg_name, project_dir)

        assert result["is_clean"] is False
        assert "skills/my-skill/SKILL.md" in result["modified_files"]

    @pytest.mark.integration
    def test_integration_verify_missing_file(
        self, installed_package: tuple[Path, str]
    ) -> None:
        """Verify detects a missing file correctly."""
        project_dir, pkg_name = installed_package

        # Delete a file
        skill_path = (
            project_dir / ".aam" / "packages" / pkg_name
            / "skills" / "my-skill" / "SKILL.md"
        )
        skill_path.unlink()

        result = verify_package(pkg_name, project_dir)

        assert result["is_clean"] is False
        assert "skills/my-skill/SKILL.md" in result["missing_files"]


################################################################################
#                                                                              #
# CHECK MODIFICATIONS TESTS                                                    #
#                                                                              #
################################################################################


class TestCheckModificationsIntegration:
    """Integration tests for modification detection."""

    @pytest.mark.integration
    def test_integration_check_mods_clean(
        self, installed_package: tuple[Path, str]
    ) -> None:
        """Clean package reports no modifications."""
        project_dir, pkg_name = installed_package

        result = check_modifications(pkg_name, project_dir)

        assert result["has_modifications"] is False
        assert result["has_checksums"] is True

    @pytest.mark.integration
    def test_integration_check_mods_modified(
        self, installed_package: tuple[Path, str]
    ) -> None:
        """Modified package reports changes."""
        project_dir, pkg_name = installed_package

        # Modify a file
        skill_path = (
            project_dir / ".aam" / "packages" / pkg_name
            / "skills" / "my-skill" / "SKILL.md"
        )
        skill_path.write_text("Modified!")

        result = check_modifications(pkg_name, project_dir)

        assert result["has_modifications"] is True
        assert "skills/my-skill/SKILL.md" in result["modified_files"]


################################################################################
#                                                                              #
# BACKUP TESTS                                                                 #
#                                                                              #
################################################################################


class TestBackupIntegration:
    """Integration tests for backup creation."""

    @pytest.mark.integration
    def test_integration_backup_modified_files(
        self, installed_package: tuple[Path, str]
    ) -> None:
        """Backup copies modified files to backup directory."""
        project_dir, pkg_name = installed_package

        # Modify a file
        skill_path = (
            project_dir / ".aam" / "packages" / pkg_name
            / "skills" / "my-skill" / "SKILL.md"
        )
        skill_path.write_text("Modified content for backup test!")

        result = create_backup(
            pkg_name,
            ["skills/my-skill/SKILL.md"],
            project_dir,
        )

        assert result["package_name"] == pkg_name
        assert len(result["backed_up_files"]) == 1

        # Verify backup file exists and has correct content
        backup_dir = Path(result["backup_dir"])
        backup_file = backup_dir / "skills" / "my-skill" / "SKILL.md"
        assert backup_file.is_file()
        assert backup_file.read_text() == "Modified content for backup test!"
