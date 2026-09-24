"""Unit tests for artifact auto-discovery.

Tests ``discover_artifacts()`` scanning logic and fallback behaviour.

Reference: tasks.md T080.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from pathlib import Path

from aam_cli.core.autodiscovery import discover_artifacts
from aam_cli.core.manifest import ArtifactRef, ArtifactsDeclaration, PackageManifest

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


def _minimal_manifest(**kwargs) -> PackageManifest:
    """Return a minimal PackageManifest with no artifacts."""
    base = {
        "name": "@test/pkg",
        "version": "1.0.0",
        "description": "Test package",
    }
    base.update(kwargs)
    return PackageManifest.model_validate(base)


def _manifest_with_explicit_artifacts(**kwargs) -> PackageManifest:
    """Return a manifest with an explicit ArtifactsDeclaration."""
    manifest = _minimal_manifest()
    manifest.artifacts = ArtifactsDeclaration(**kwargs)
    return manifest


################################################################################
#                                                                              #
# TESTS                                                                        #
#                                                                              #
################################################################################


class TestDiscoverArtifacts:
    """Tests for ``discover_artifacts()``."""

    def test_unit_explicit_artifacts_returned_unchanged(self, tmp_path: Path) -> None:
        """If manifest.artifacts is not None, return it without scanning."""
        explicit = ArtifactsDeclaration(
            skills=[ArtifactRef(name="my-skill", path="skills/my-skill/SKILL.md", description="")]
        )
        manifest = _minimal_manifest()
        manifest.artifacts = explicit

        result = discover_artifacts(tmp_path, manifest)

        assert result is explicit
        assert len(result.skills) == 1

    def test_unit_no_artifacts_section_triggers_scan(self, tmp_path: Path) -> None:
        """If manifest.artifacts is None, scan the filesystem."""
        # Create a skill directory
        skill_dir = tmp_path / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# My Skill")

        manifest = _minimal_manifest()
        result = discover_artifacts(tmp_path, manifest)

        skill_names = [ref.name for ref in result.skills]
        assert "my-skill" in skill_names

    def test_unit_discovers_skills_from_skills_dir(self, tmp_path: Path) -> None:
        """Scans ``skills/*/SKILL.md`` and returns ArtifactRef per skill."""
        (tmp_path / "skills" / "code-review").mkdir(parents=True)
        (tmp_path / "skills" / "code-review" / "SKILL.md").write_text("# Code Review")
        (tmp_path / "skills" / "debug").mkdir(parents=True)
        (tmp_path / "skills" / "debug" / "SKILL.md").write_text("# Debug")

        manifest = _minimal_manifest()
        result = discover_artifacts(tmp_path, manifest)

        skill_names = [ref.name for ref in result.skills]
        assert "code-review" in skill_names
        assert "debug" in skill_names

    def test_unit_discovers_agents_structured_format(self, tmp_path: Path) -> None:
        """Scans ``agents/*/agent.yaml`` for structured agents."""
        agent_dir = tmp_path / "agents" / "my-agent"
        agent_dir.mkdir(parents=True)
        (agent_dir / "agent.yaml").write_text("name: my-agent\ndescription: Agent desc")
        (agent_dir / "system-prompt.md").write_text("You are a helpful agent.")

        manifest = _minimal_manifest()
        result = discover_artifacts(tmp_path, manifest)

        agent_names = [ref.name for ref in result.agents]
        assert "my-agent" in agent_names

    def test_unit_discovers_commands_from_commands_dir(self, tmp_path: Path) -> None:
        """Scans ``commands/*.md`` and returns ArtifactRef per command file."""
        (tmp_path / "commands").mkdir()
        (tmp_path / "commands" / "review.md").write_text("# Review command")
        (tmp_path / "commands" / "deploy.md").write_text("# Deploy command")

        manifest = _minimal_manifest()
        result = discover_artifacts(tmp_path, manifest)

        command_names = [ref.name for ref in result.commands]
        assert "review" in command_names
        assert "deploy" in command_names

    def test_unit_discovers_rules_from_rules_dir(self, tmp_path: Path) -> None:
        """Scans ``rules/*/RULE.md`` and returns ArtifactRef per rule."""
        rule_dir = tmp_path / "rules" / "ts-standards"
        rule_dir.mkdir(parents=True)
        (rule_dir / "RULE.md").write_text("# TypeScript standards")

        manifest = _minimal_manifest()
        result = discover_artifacts(tmp_path, manifest)

        rule_names = [ref.name for ref in result.rules]
        assert "ts-standards" in rule_names

    def test_unit_hooks_path_set_when_hooks_json_exists(self, tmp_path: Path) -> None:
        """hooks_path is set in ArtifactsDeclaration when hooks/hooks.json exists."""
        (tmp_path / "hooks").mkdir()
        (tmp_path / "hooks" / "hooks.json").write_text("{}")

        manifest = _minimal_manifest()
        result = discover_artifacts(tmp_path, manifest)

        assert result.hooks_path is not None

    def test_unit_mcp_path_set_when_mcp_servers_json_exists(
        self, tmp_path: Path
    ) -> None:
        """mcp_path is set when mcp/servers.json exists."""
        (tmp_path / "mcp").mkdir()
        (tmp_path / "mcp" / "servers.json").write_text("{}")

        manifest = _minimal_manifest()
        result = discover_artifacts(tmp_path, manifest)

        assert result.mcp_path is not None

    def test_unit_empty_package_returns_empty_declarations(
        self, tmp_path: Path
    ) -> None:
        """Package with no artifact directories returns empty ArtifactsDeclaration."""
        manifest = _minimal_manifest()
        result = discover_artifacts(tmp_path, manifest)

        assert result.skills == []
        assert result.agents == []
        assert result.commands == []
        assert result.rules == []
        assert result.hooks_path is None
        assert result.mcp_path is None

    def test_unit_custom_skills_path_override(self, tmp_path: Path) -> None:
        """Custom skills_path override is used for discovery."""
        custom_dir = tmp_path / "custom_skills"
        custom_dir.mkdir()
        (custom_dir / "my-skill").mkdir()
        (custom_dir / "my-skill" / "SKILL.md").write_text("# Skill")

        # Manifest with skills_path override pointing to custom location
        manifest = PackageManifest.model_validate({
            "name": "@test/pkg",
            "version": "1.0.0",
            "description": "Test",
            "skills": "custom_skills",
        })
        result = discover_artifacts(tmp_path, manifest)
        skill_names = [ref.name for ref in result.skills]
        assert "my-skill" in skill_names
