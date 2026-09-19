"""Unit tests for skill_scope deploy paths (Cursor and Codex) and installer."""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from aam_cli.adapters.codex import CodexAdapter
from aam_cli.adapters.cursor import CursorAdapter
from aam_cli.core.installer import _deploy_package
from aam_cli.core.manifest import (
    ArtifactRef,
    ArtifactsDeclaration,
    PackageManifest,
    PlatformConfig,
)

################################################################################
#                                                                              #
# HELPERS                                                                      #
#                                                                              #
################################################################################


def _make_skill_dir(tmp_path: Path, name: str = "my-skill") -> Path:
    """Create a minimal skill directory with SKILL.md."""
    skill_dir = tmp_path / "pkg-skills" / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(f"# {name}\n", encoding="utf-8")
    return skill_dir


################################################################################
#                                                                              #
# CURSOR SKILL_SCOPE                                                           #
#                                                                              #
################################################################################


class TestCursorSkillScope:
    """CursorAdapter honors platforms.cursor.skill_scope."""

    def test_unit_project_scope_deploys_to_cursor_skills(
        self, tmp_path: Path
    ) -> None:
        """project scope writes to .cursor/skills/<name>/."""
        adapter = CursorAdapter(tmp_path)
        skill_dir = _make_skill_dir(tmp_path)
        ref = ArtifactRef(name="my-skill", path="skills/my-skill", description="t")

        dest = adapter.deploy_skill(skill_dir, ref, {"skill_scope": "project"})

        assert dest == tmp_path / ".cursor" / "skills" / "my-skill"
        assert (dest / "SKILL.md").is_file()

    def test_unit_user_scope_deploys_to_home_cursor_skills(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """user scope writes to ~/.cursor/skills/<name>/."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        project = tmp_path / "project"
        project.mkdir()
        adapter = CursorAdapter(project)
        skill_dir = _make_skill_dir(tmp_path)
        ref = ArtifactRef(name="my-skill", path="skills/my-skill", description="t")

        dest = adapter.deploy_skill(skill_dir, ref, {"skill_scope": "user"})

        assert dest == fake_home / ".cursor" / "skills" / "my-skill"
        assert (dest / "SKILL.md").is_file()


################################################################################
#                                                                              #
# CODEX SKILL_SCOPE                                                            #
#                                                                              #
################################################################################


class TestCodexSkillScope:
    """CodexAdapter honors platforms.codex.skill_scope."""

    def test_unit_default_scope_is_project(self, tmp_path: Path) -> None:
        """Missing skill_scope defaults to project .agents/skills/."""
        adapter = CodexAdapter(tmp_path)
        skill_dir = _make_skill_dir(tmp_path)
        ref = ArtifactRef(name="my-skill", path="skills/my-skill", description="t")

        dest = adapter.deploy_skill(skill_dir, ref, {})

        assert dest == tmp_path / ".agents" / "skills" / "my-skill"


################################################################################
#                                                                              #
# INSTALLER PASSES SKILL_SCOPE                                                 #
#                                                                              #
################################################################################


class TestInstallerSkillScope:
    """_deploy_package passes skill_scope from the package manifest."""

    def test_unit_deploy_package_passes_skill_scope_from_manifest(
        self, tmp_path: Path
    ) -> None:
        """Installer includes skill_scope from platforms.<adapter.name>."""
        package_dir = tmp_path / "pkg"
        package_dir.mkdir()
        skill_dir = package_dir / "skills" / "demo"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Demo\n", encoding="utf-8")

        manifest = PackageManifest(
            name="demo-pkg",
            version="1.0.0",
            description="test",
            platforms={
                "codex": PlatformConfig(skill_scope="user"),
            },
            artifacts=ArtifactsDeclaration(
                skills=[
                    ArtifactRef(
                        name="demo",
                        path="skills/demo",
                        description="demo skill",
                    )
                ]
            ),
        )

        adapter = MagicMock()
        adapter.name = "codex"
        captured: dict[str, str] = {}

        def _capture_deploy(
            _path: Path, _ref: ArtifactRef, config: dict[str, str]
        ) -> Path:
            captured.update(config)
            return tmp_path / "out"

        adapter.deploy_skill.side_effect = _capture_deploy

        with (
            patch(
                "aam_cli.core.installer.load_manifest_universal",
                return_value=manifest,
            ),
            patch(
                "aam_cli.core.installer.discover_artifacts",
                return_value=manifest.artifacts,
            ),
        ):
            _deploy_package(package_dir, adapter)

        assert captured.get("skill_scope") == "user"
        assert captured.get("package_name") == "demo-pkg"

    def test_unit_deploy_package_defaults_skill_scope_project(
        self, tmp_path: Path
    ) -> None:
        """Installer defaults skill_scope to project when platform block missing."""
        package_dir = tmp_path / "pkg"
        package_dir.mkdir()
        skill_dir = package_dir / "skills" / "demo"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Demo\n", encoding="utf-8")

        manifest = PackageManifest(
            name="demo-pkg",
            version="1.0.0",
            description="test",
            platforms={},
            artifacts=ArtifactsDeclaration(
                skills=[
                    ArtifactRef(
                        name="demo",
                        path="skills/demo",
                        description="demo skill",
                    )
                ]
            ),
        )

        adapter = MagicMock()
        adapter.name = "cursor"
        captured: dict[str, str] = {}

        def _capture_deploy(
            _path: Path, _ref: ArtifactRef, config: dict[str, str]
        ) -> Path:
            captured.update(config)
            return tmp_path / "out"

        adapter.deploy_skill.side_effect = _capture_deploy

        with (
            patch(
                "aam_cli.core.installer.load_manifest_universal",
                return_value=manifest,
            ),
            patch(
                "aam_cli.core.installer.discover_artifacts",
                return_value=manifest.artifacts,
            ),
        ):
            _deploy_package(package_dir, adapter)

        assert captured.get("skill_scope") == "project"
