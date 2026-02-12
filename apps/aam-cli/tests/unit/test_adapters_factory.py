"""Unit tests for platform adapter factory and all platform adapters."""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from pathlib import Path

import pytest

from aam_cli.adapters.claude import ClaudeAdapter
from aam_cli.adapters.codex import CodexAdapter
from aam_cli.adapters.copilot import CopilotAdapter
from aam_cli.adapters.cursor import CursorAdapter
from aam_cli.adapters.factory import (
    SUPPORTED_PLATFORMS,
    create_adapter,
    is_supported_platform,
)
from aam_cli.core.manifest import ArtifactRef

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# FACTORY TESTS                                                                #
#                                                                              #
################################################################################


class TestAdapterFactory:
    """Tests for the create_adapter factory function."""

    def test_unit_create_cursor_adapter(self, tmp_path: Path) -> None:
        """Factory returns CursorAdapter for 'cursor' platform."""
        adapter = create_adapter("cursor", tmp_path)
        assert isinstance(adapter, CursorAdapter)
        assert adapter.name == "cursor"

    def test_unit_create_copilot_adapter(self, tmp_path: Path) -> None:
        """Factory returns CopilotAdapter for 'copilot' platform."""
        adapter = create_adapter("copilot", tmp_path)
        assert isinstance(adapter, CopilotAdapter)
        assert adapter.name == "copilot"

    def test_unit_create_claude_adapter(self, tmp_path: Path) -> None:
        """Factory returns ClaudeAdapter for 'claude' platform."""
        adapter = create_adapter("claude", tmp_path)
        assert isinstance(adapter, ClaudeAdapter)
        assert adapter.name == "claude"

    def test_unit_create_codex_adapter(self, tmp_path: Path) -> None:
        """Factory returns CodexAdapter for 'codex' platform."""
        adapter = create_adapter("codex", tmp_path)
        assert isinstance(adapter, CodexAdapter)
        assert adapter.name == "codex"

    def test_unit_create_unsupported_raises(self, tmp_path: Path) -> None:
        """Factory raises ValueError for unsupported platform."""
        with pytest.raises(ValueError, match="Unsupported platform"):
            create_adapter("unknown-platform", tmp_path)

    def test_unit_is_supported_platform(self) -> None:
        """is_supported_platform returns True for all supported names."""
        for name in SUPPORTED_PLATFORMS:
            assert is_supported_platform(name) is True

    def test_unit_is_not_supported_platform(self) -> None:
        """is_supported_platform returns False for unknown names."""
        assert is_supported_platform("vscode") is False
        assert is_supported_platform("") is False


################################################################################
#                                                                              #
# COPILOT ADAPTER TESTS                                                        #
#                                                                              #
################################################################################


class TestCopilotAdapter:
    """Tests for the CopilotAdapter."""

    def _make_skill_dir(self, tmp_path: Path) -> Path:
        """Create a minimal skill directory for testing."""
        skill_dir = tmp_path / "src-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# My Skill\nDoes things.\n")
        return skill_dir

    def _make_agent_dir(self, tmp_path: Path) -> Path:
        """Create a minimal agent directory for testing."""
        agent_dir = tmp_path / "src-agent"
        agent_dir.mkdir()
        (agent_dir / "system-prompt.md").write_text("You are a helpful agent.\n")
        return agent_dir

    def _make_prompt_file(self, tmp_path: Path) -> Path:
        """Create a minimal prompt file for testing."""
        prompt = tmp_path / "my-prompt.md"
        prompt.write_text("# My Prompt\nDo something.\n")
        return prompt

    def _make_instruction_file(self, tmp_path: Path) -> Path:
        """Create a minimal instruction file for testing."""
        instr = tmp_path / "my-instruction.md"
        instr.write_text("# Coding Standards\nFollow PEP 8.\n")
        return instr

    def test_unit_deploy_skill(self, tmp_path: Path) -> None:
        """Skill is deployed to .github/skills/<name>/."""
        project = tmp_path / "project"
        project.mkdir()
        skill_dir = self._make_skill_dir(tmp_path)
        adapter = CopilotAdapter(project)

        ref = ArtifactRef(name="my-skill", path="skills/my-skill", description="test")
        dest = adapter.deploy_skill(skill_dir, ref, {})

        assert dest == project / ".github" / "skills" / "my-skill"
        assert (dest / "SKILL.md").is_file()

    def test_unit_deploy_agent_to_copilot_instructions(self, tmp_path: Path) -> None:
        """Agent is merged into .github/copilot-instructions.md with markers."""
        project = tmp_path / "project"
        project.mkdir()
        agent_dir = self._make_agent_dir(tmp_path)
        adapter = CopilotAdapter(project)

        ref = ArtifactRef(name="my-agent", path="agents/my-agent", description="test")
        dest = adapter.deploy_agent(agent_dir, ref, {})

        assert dest == project / ".github" / "copilot-instructions.md"
        content = dest.read_text()
        assert "<!-- BEGIN AAM: my-agent agent -->" in content
        assert "You are a helpful agent." in content
        assert "<!-- END AAM: my-agent agent -->" in content

    def test_unit_deploy_prompt(self, tmp_path: Path) -> None:
        """Prompt is deployed to .github/prompts/<name>.md."""
        project = tmp_path / "project"
        project.mkdir()
        prompt_file = self._make_prompt_file(tmp_path)
        adapter = CopilotAdapter(project)

        ref = ArtifactRef(name="my-prompt", path="prompts/my-prompt.md", description="test")
        dest = adapter.deploy_prompt(prompt_file, ref, {})

        assert dest == project / ".github" / "prompts" / "my-prompt.md"
        assert dest.is_file()

    def test_unit_deploy_instruction_to_copilot_instructions(self, tmp_path: Path) -> None:
        """Instruction is merged into .github/copilot-instructions.md."""
        project = tmp_path / "project"
        project.mkdir()
        instr_file = self._make_instruction_file(tmp_path)
        adapter = CopilotAdapter(project)

        ref = ArtifactRef(
            name="coding-standards",
            path="instructions/coding-standards.md",
            description="test",
        )
        dest = adapter.deploy_instruction(instr_file, ref, {})

        content = dest.read_text()
        assert "<!-- BEGIN AAM: coding-standards instruction -->" in content
        assert "Follow PEP 8." in content
        assert "<!-- END AAM: coding-standards instruction -->" in content

    def test_unit_upsert_replaces_existing_section(self, tmp_path: Path) -> None:
        """Re-deploying an agent replaces the existing section."""
        project = tmp_path / "project"
        project.mkdir()
        adapter = CopilotAdapter(project)

        # Deploy first version
        agent_dir_v1 = tmp_path / "agent-v1"
        agent_dir_v1.mkdir()
        (agent_dir_v1 / "system-prompt.md").write_text("Version 1 content.\n")

        ref = ArtifactRef(name="my-agent", path="agents/my-agent", description="test")
        adapter.deploy_agent(agent_dir_v1, ref, {})

        # Deploy second version
        agent_dir_v2 = tmp_path / "agent-v2"
        agent_dir_v2.mkdir()
        (agent_dir_v2 / "system-prompt.md").write_text("Version 2 content.\n")

        adapter.deploy_agent(agent_dir_v2, ref, {})

        content = (project / ".github" / "copilot-instructions.md").read_text()
        assert "Version 2 content." in content
        assert "Version 1 content." not in content
        # Only one begin marker
        assert content.count("<!-- BEGIN AAM: my-agent agent -->") == 1

    def test_unit_undeploy_skill(self, tmp_path: Path) -> None:
        """Undeploying a skill removes its directory."""
        project = tmp_path / "project"
        project.mkdir()
        skill_dir = self._make_skill_dir(tmp_path)
        adapter = CopilotAdapter(project)

        ref = ArtifactRef(name="my-skill", path="skills/my-skill", description="test")
        adapter.deploy_skill(skill_dir, ref, {})
        assert (project / ".github" / "skills" / "my-skill").is_dir()

        adapter.undeploy("my-skill", "skill")
        assert not (project / ".github" / "skills" / "my-skill").exists()

    def test_unit_undeploy_agent_section(self, tmp_path: Path) -> None:
        """Undeploying an agent removes its marker section."""
        project = tmp_path / "project"
        project.mkdir()
        agent_dir = self._make_agent_dir(tmp_path)
        adapter = CopilotAdapter(project)

        ref = ArtifactRef(name="my-agent", path="agents/my-agent", description="test")
        adapter.deploy_agent(agent_dir, ref, {})

        adapter.undeploy("my-agent", "agent")

        instructions_path = project / ".github" / "copilot-instructions.md"
        # File should be removed if it was the only section
        assert not instructions_path.exists()

    def test_unit_list_deployed(self, tmp_path: Path) -> None:
        """list_deployed returns all deployed artifact tuples."""
        project = tmp_path / "project"
        project.mkdir()
        adapter = CopilotAdapter(project)

        # Deploy a skill
        skill_dir = self._make_skill_dir(tmp_path)
        ref_skill = ArtifactRef(name="s1", path="skills/s1", description="test")
        adapter.deploy_skill(skill_dir, ref_skill, {})

        # Deploy an agent
        agent_dir = self._make_agent_dir(tmp_path)
        ref_agent = ArtifactRef(name="a1", path="agents/a1", description="test")
        adapter.deploy_agent(agent_dir, ref_agent, {})

        deployed = adapter.list_deployed()
        names = [d[0] for d in deployed]
        types = [d[1] for d in deployed]

        assert "s1" in names
        assert "a1" in names
        assert "skill" in types
        assert "agent" in types


################################################################################
#                                                                              #
# CLAUDE ADAPTER TESTS                                                         #
#                                                                              #
################################################################################


class TestClaudeAdapter:
    """Tests for the ClaudeAdapter."""

    def test_unit_deploy_skill_to_claude_dir(self, tmp_path: Path) -> None:
        """Skill is deployed to .claude/skills/<name>/."""
        project = tmp_path / "project"
        project.mkdir()
        skill_dir = tmp_path / "src-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Skill\n")

        adapter = ClaudeAdapter(project)
        ref = ArtifactRef(name="my-skill", path="skills/my-skill", description="test")
        dest = adapter.deploy_skill(skill_dir, ref, {})

        assert dest == project / ".claude" / "skills" / "my-skill"
        assert (dest / "SKILL.md").is_file()

    def test_unit_deploy_agent_to_claude_md(self, tmp_path: Path) -> None:
        """Agent is merged into CLAUDE.md with markers."""
        project = tmp_path / "project"
        project.mkdir()
        agent_dir = tmp_path / "src-agent"
        agent_dir.mkdir()
        (agent_dir / "system-prompt.md").write_text("You help with audits.\n")

        adapter = ClaudeAdapter(project)
        ref = ArtifactRef(name="audit-agent", path="agents/audit-agent", description="test")
        dest = adapter.deploy_agent(agent_dir, ref, {})

        assert dest == project / "CLAUDE.md"
        content = dest.read_text()
        assert "<!-- BEGIN AAM: audit-agent agent -->" in content
        assert "You help with audits." in content

    def test_unit_deploy_prompt_to_claude_dir(self, tmp_path: Path) -> None:
        """Prompt is deployed to .claude/prompts/<name>.md."""
        project = tmp_path / "project"
        project.mkdir()
        prompt = tmp_path / "my-prompt.md"
        prompt.write_text("Do the thing.\n")

        adapter = ClaudeAdapter(project)
        ref = ArtifactRef(name="my-prompt", path="prompts/my-prompt.md", description="test")
        dest = adapter.deploy_prompt(prompt, ref, {})

        assert dest == project / ".claude" / "prompts" / "my-prompt.md"

    def test_unit_deploy_instruction_to_claude_md(self, tmp_path: Path) -> None:
        """Instruction is merged into CLAUDE.md."""
        project = tmp_path / "project"
        project.mkdir()
        instr = tmp_path / "standards.md"
        instr.write_text("Follow PEP 8.\n")

        adapter = ClaudeAdapter(project)
        ref = ArtifactRef(
            name="standards", path="instructions/standards.md", description="test"
        )
        dest = adapter.deploy_instruction(instr, ref, {})

        content = dest.read_text()
        assert "<!-- BEGIN AAM: standards instruction -->" in content

    def test_unit_preserves_existing_claude_md(self, tmp_path: Path) -> None:
        """Deploying an agent preserves existing user content in CLAUDE.md."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "CLAUDE.md").write_text("# My Project\n\nUser content here.\n")

        agent_dir = tmp_path / "src-agent"
        agent_dir.mkdir()
        (agent_dir / "system-prompt.md").write_text("Agent content.\n")

        adapter = ClaudeAdapter(project)
        ref = ArtifactRef(name="my-agent", path="agents/my-agent", description="test")
        adapter.deploy_agent(agent_dir, ref, {})

        content = (project / "CLAUDE.md").read_text()
        assert "# My Project" in content
        assert "User content here." in content
        assert "Agent content." in content


################################################################################
#                                                                              #
# CODEX ADAPTER TESTS                                                          #
#                                                                              #
################################################################################


class TestCodexAdapter:
    """Tests for the CodexAdapter."""

    def test_unit_deploy_agent_to_agents_md(self, tmp_path: Path) -> None:
        """Agent is merged into AGENTS.md with markers."""
        project = tmp_path / "project"
        project.mkdir()
        agent_dir = tmp_path / "src-agent"
        agent_dir.mkdir()
        (agent_dir / "system-prompt.md").write_text("You are a code reviewer.\n")

        adapter = CodexAdapter(project)
        ref = ArtifactRef(name="reviewer", path="agents/reviewer", description="test")
        dest = adapter.deploy_agent(agent_dir, ref, {})

        assert dest == project / "AGENTS.md"
        content = dest.read_text()
        assert "<!-- BEGIN AAM: reviewer agent -->" in content
        assert "You are a code reviewer." in content

    def test_unit_deploy_instruction_to_agents_md(self, tmp_path: Path) -> None:
        """Instruction is merged into AGENTS.md."""
        project = tmp_path / "project"
        project.mkdir()
        instr = tmp_path / "standards.md"
        instr.write_text("Always use type hints.\n")

        adapter = CodexAdapter(project)
        ref = ArtifactRef(
            name="type-hints", path="instructions/type-hints.md", description="test"
        )
        dest = adapter.deploy_instruction(instr, ref, {})

        content = dest.read_text()
        assert "<!-- BEGIN AAM: type-hints instruction -->" in content
        assert "Always use type hints." in content

    def test_unit_deploy_skill_to_codex_home(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Skill is deployed to ~/.codex/skills/<name>/."""
        project = tmp_path / "project"
        project.mkdir()
        fake_home = tmp_path / "home"
        fake_home.mkdir()

        # Override Path.home() to use our temp directory
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        skill_dir = tmp_path / "src-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Skill\n")

        adapter = CodexAdapter(project)
        ref = ArtifactRef(name="my-skill", path="skills/my-skill", description="test")
        dest = adapter.deploy_skill(skill_dir, ref, {})

        assert dest == fake_home / ".codex" / "skills" / "my-skill"
        assert (dest / "SKILL.md").is_file()

    def test_unit_deploy_prompt_to_codex_home(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Prompt is deployed to ~/.codex/prompts/<name>.md."""
        project = tmp_path / "project"
        project.mkdir()
        fake_home = tmp_path / "home"
        fake_home.mkdir()

        monkeypatch.setattr(Path, "home", lambda: fake_home)

        prompt = tmp_path / "my-prompt.md"
        prompt.write_text("Do the thing.\n")

        adapter = CodexAdapter(project)
        ref = ArtifactRef(name="my-prompt", path="prompts/my-prompt.md", description="test")
        dest = adapter.deploy_prompt(prompt, ref, {})

        assert dest == fake_home / ".codex" / "prompts" / "my-prompt.md"
        assert dest.is_file()
