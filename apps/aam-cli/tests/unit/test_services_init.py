"""Unit tests for init_service — package scaffolding."""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging

import pytest

from aam_cli.services.init_service import init_package

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


class TestInitService:
    """Tests for the init_package service function."""

    def test_unit_init_creates_directories(self, tmp_path: object) -> None:
        """Verify package dir and artifact subdirectories are created."""
        result = init_package(
            name="test-pkg",
            path=str(tmp_path),
        )

        pkg_dir = tmp_path / "test-pkg"  # type: ignore[operator]
        assert pkg_dir.exists()
        assert (pkg_dir / "skills").exists()
        assert (pkg_dir / "agents").exists()
        assert (pkg_dir / "prompts").exists()
        assert (pkg_dir / "instructions").exists()
        assert (pkg_dir / "aam.yaml").exists()
        assert result["package_name"] == "test-pkg"
        assert len(result["artifact_types"]) == 4
        assert len(result["directories_created"]) == 5  # root + 4 artifact dirs

    def test_unit_init_custom_artifact_types(self, tmp_path: object) -> None:
        """Verify only requested artifact directories are created."""
        result = init_package(
            name="custom-pkg",
            path=str(tmp_path),
            artifact_types=["skills", "prompts"],
        )

        pkg_dir = tmp_path / "custom-pkg"  # type: ignore[operator]
        assert (pkg_dir / "skills").exists()
        assert (pkg_dir / "prompts").exists()
        assert not (pkg_dir / "agents").exists()
        assert not (pkg_dir / "instructions").exists()
        assert result["artifact_types"] == ["skills", "prompts"]

    def test_unit_init_custom_platforms(self, tmp_path: object) -> None:
        """Verify platforms list is respected in the manifest."""
        result = init_package(
            name="plat-pkg",
            path=str(tmp_path),
            platforms=["cursor", "claude"],
        )

        assert result["platforms"] == ["cursor", "claude"]

    def test_unit_init_scoped_name(self, tmp_path: object) -> None:
        """Verify scoped name creates directory using bare name."""
        result = init_package(
            name="@myorg/cool-skills",
            path=str(tmp_path),
        )

        pkg_dir = tmp_path / "cool-skills"  # type: ignore[operator]
        assert pkg_dir.exists()
        assert result["package_name"] == "@myorg/cool-skills"

    def test_unit_init_with_metadata(self, tmp_path: object) -> None:
        """Verify description, author, licence are included in result."""
        result = init_package(
            name="meta-pkg",
            path=str(tmp_path),
            version="2.0.0",
            description="A test package",
            author="Test Author",
            license_name="Apache-2.0",
        )

        assert result["package_name"] == "meta-pkg"
        # Manifest was written — check it exists
        assert result["manifest_path"].endswith("aam.yaml")

    def test_unit_init_invalid_name(self, tmp_path: object) -> None:
        """Verify ValueError raised for an invalid package name."""
        with pytest.raises(ValueError, match="AAM_INVALID_ARGUMENT"):
            init_package(name="INVALID NAME!!", path=str(tmp_path))

    def test_unit_init_invalid_artifact_type(self, tmp_path: object) -> None:
        """Verify ValueError raised for unrecognised artifact type."""
        with pytest.raises(ValueError, match="AAM_INVALID_ARGUMENT"):
            init_package(
                name="bad-type",
                path=str(tmp_path),
                artifact_types=["skills", "bananas"],
            )

    def test_unit_init_invalid_platform(self, tmp_path: object) -> None:
        """Verify ValueError raised for unrecognised platform."""
        with pytest.raises(ValueError, match="AAM_INVALID_ARGUMENT"):
            init_package(
                name="bad-plat",
                path=str(tmp_path),
                platforms=["cursor", "notepad"],
            )
