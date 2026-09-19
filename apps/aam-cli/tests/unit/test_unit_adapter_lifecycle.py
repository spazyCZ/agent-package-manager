"""Unit tests for adapter undeploy() and list_deployed() — all 8 artifact types.

Tests all four adapters (Claude, Cursor, Copilot, Codex) for:
  - undeploy: removes the correct files/entries for all 8 artifact types
  - list_deployed: discovers all deployed artifact types correctly
  - unknown artifact types: logs warning and does not raise
"""
################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import json
import logging
from pathlib import Path

from aam_cli.adapters.claude import ClaudeAdapter
from aam_cli.adapters.codex import CodexAdapter
from aam_cli.adapters.copilot import CopilotAdapter
from aam_cli.adapters.cursor import CursorAdapter
from aam_cli.converters.mappings import (
    HOOK_EVENT_TO_PLATFORM,
    SUPPORTED_HOOK_EVENTS,
)

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# HELPERS                                                                      #
#                                                                              #
################################################################################

_UTF8 = "utf-8"


def _setup_cursor(tmp_path: Path) -> CursorAdapter:
    """Create a CursorAdapter with standard directories."""
    adapter = CursorAdapter(tmp_path)
    for d in ("skills", "rules", "prompts"):
        (tmp_path / ".cursor" / d).mkdir(parents=True, exist_ok=True)
    return adapter


def _setup_claude(tmp_path: Path) -> ClaudeAdapter:
    """Create a ClaudeAdapter with standard directories."""
    adapter = ClaudeAdapter(tmp_path)
    for d in ("skills", "agents", "prompts", "commands"):
        (tmp_path / ".claude" / d).mkdir(parents=True, exist_ok=True)
    return adapter


def _setup_copilot(tmp_path: Path) -> CopilotAdapter:
    """Create a CopilotAdapter with standard directories."""
    adapter = CopilotAdapter(tmp_path)
    for d in ("skills", "agents", "prompts", "instructions"):
        (tmp_path / ".github" / d).mkdir(parents=True, exist_ok=True)
    return adapter


def _setup_codex(tmp_path: Path) -> CodexAdapter:
    """Create a CodexAdapter with home dirs redirected under tmp_path."""
    adapter = CodexAdapter(tmp_path)
    adapter.codex_dir = tmp_path / ".codex"
    adapter.agents_user_dir = tmp_path / ".agents-user"
    for d in ("skills", "prompts"):
        (adapter.codex_dir / d).mkdir(parents=True, exist_ok=True)
    (tmp_path / ".agents" / "skills").mkdir(parents=True, exist_ok=True)
    (adapter.agents_user_dir / "skills").mkdir(parents=True, exist_ok=True)
    return adapter


def _write_json(path: Path, data: dict) -> None:
    """Write a dict as JSON to the given path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding=_UTF8)


################################################################################
#                                                                              #
# TEST: CursorAdapter                                                          #
#                                                                              #
################################################################################


class TestCursorAdapterLifecycle:
    """Tests for CursorAdapter undeploy() and list_deployed()."""

    def test_unit_undeploy_skill(self, tmp_path: Path) -> None:
        """undeploy removes .cursor/skills/<name>/ directory."""
        adapter = _setup_cursor(tmp_path)
        d = tmp_path / ".cursor" / "skills" / "test-skill"
        d.mkdir()
        (d / "SKILL.md").write_text("# Skill", encoding=_UTF8)
        adapter.undeploy("test-skill", "skill")
        assert not d.exists()

    def test_unit_undeploy_agent(self, tmp_path: Path) -> None:
        """undeploy removes .cursor/rules/agent-<name>.mdc."""
        adapter = _setup_cursor(tmp_path)
        f = tmp_path / ".cursor" / "rules" / "agent-foo.mdc"
        f.write_text("---\ndescription: agent\n---\n", encoding=_UTF8)
        adapter.undeploy("foo", "agent")
        assert not f.exists()

    def test_unit_undeploy_prompt(self, tmp_path: Path) -> None:
        """undeploy removes .cursor/prompts/<name>.md."""
        adapter = _setup_cursor(tmp_path)
        f = tmp_path / ".cursor" / "prompts" / "foo.md"
        f.write_text("# Prompt", encoding=_UTF8)
        adapter.undeploy("foo", "prompt")
        assert not f.exists()

    def test_unit_undeploy_instruction(self, tmp_path: Path) -> None:
        """undeploy removes .cursor/rules/<name>.mdc instruction file."""
        adapter = _setup_cursor(tmp_path)
        f = tmp_path / ".cursor" / "rules" / "foo.mdc"
        f.write_text("---\ndescription: instr\n---\n", encoding=_UTF8)
        adapter.undeploy("foo", "instruction")
        assert not f.exists()

    def test_unit_undeploy_command(self, tmp_path: Path) -> None:
        """undeploy removes .cursor/skills/<name>/ command directory."""
        adapter = _setup_cursor(tmp_path)
        d = tmp_path / ".cursor" / "skills" / "pkg:my-cmd"
        d.mkdir()
        (d / "SKILL.md").write_text("# Cmd", encoding=_UTF8)
        adapter.undeploy("pkg:my-cmd", "command")
        assert not d.exists()

    def test_unit_undeploy_rule(self, tmp_path: Path) -> None:
        """undeploy removes .cursor/rules/<name>.mdc rule file."""
        adapter = _setup_cursor(tmp_path)
        f = tmp_path / ".cursor" / "rules" / "foo.mdc"
        f.write_text("---\ndescription: rule\n---\n", encoding=_UTF8)
        adapter.undeploy("foo", "rule")
        assert not f.exists()

    def test_unit_undeploy_hook(self, tmp_path: Path) -> None:
        """undeploy removes AAM-tagged entries from .cursor/hooks.json."""
        adapter = _setup_cursor(tmp_path)
        hp = tmp_path / ".cursor" / "hooks.json"
        _write_json(hp, {
            "PreToolUse": [{"command": "lint", "_aam_package": "test-pkg"}],
        })
        adapter.undeploy("test-pkg", "hook")
        hooks = json.loads(hp.read_text(encoding=_UTF8))
        remaining = hooks.get("PreToolUse", [])
        assert not any(e.get("_aam_package") == "test-pkg" for e in remaining)

    def test_unit_undeploy_mcp(self, tmp_path: Path) -> None:
        """undeploy removes namespaced entries from .cursor/mcp.json."""
        adapter = _setup_cursor(tmp_path)
        mp = tmp_path / ".cursor" / "mcp.json"
        _write_json(mp, {
            "mcpServers": {"test-pkg:server1": {"command": "node"}},
        })
        adapter.undeploy("test-pkg", "mcp")
        mcp = json.loads(mp.read_text(encoding=_UTF8))
        assert "test-pkg:server1" not in mcp["mcpServers"]

    def test_unit_undeploy_unknown_type_logs_warning(self, tmp_path: Path, caplog) -> None:
        """undeploy with unknown artifact type logs warning, does not raise."""
        adapter = _setup_cursor(tmp_path)
        with caplog.at_level(logging.WARNING):
            adapter.undeploy("foo", "banana")
        assert any("Unknown artifact type" in r.message for r in caplog.records)

    def test_unit_list_deployed_discovers_all_types(self, tmp_path: Path) -> None:
        """list_deployed discovers skill, command, agent, instruction, hook, mcp."""
        adapter = _setup_cursor(tmp_path)
        b = tmp_path / ".cursor"
        (b / "skills" / "my-skill").mkdir()
        (b / "skills" / "my-skill" / "SKILL.md").write_text("x", encoding=_UTF8)
        (b / "skills" / "pkg:my-cmd").mkdir()
        (b / "skills" / "pkg:my-cmd" / "SKILL.md").write_text("x", encoding=_UTF8)
        (b / "rules" / "agent-my-agent.mdc").write_text("x", encoding=_UTF8)
        (b / "rules" / "my-instr.mdc").write_text("x", encoding=_UTF8)
        (b / "prompts" / "my-prompt.md").write_text("x", encoding=_UTF8)
        _write_json(b / "hooks.json", {
            "PreToolUse": [{"command": "lint", "_aam_package": "pkg"}],
        })
        _write_json(b / "mcp.json", {
            "mcpServers": {"pkg:server1": {"command": "node", "_aam_package": "pkg"}},
        })
        types_found = {d[1] for d in adapter.list_deployed()}
        # v0.5.0: prompts merged into commands — "prompt" no longer a separate type
        assert types_found >= {"skill", "command", "agent", "instruction", "hook", "mcp"}


################################################################################
#                                                                              #
# TEST: ClaudeAdapter                                                          #
#                                                                              #
################################################################################


class TestClaudeAdapterLifecycle:
    """Tests for ClaudeAdapter undeploy() and list_deployed()."""

    def test_unit_undeploy_skill(self, tmp_path: Path) -> None:
        """undeploy removes .claude/skills/<name>/ directory."""
        adapter = _setup_claude(tmp_path)
        d = tmp_path / ".claude" / "skills" / "test-skill"
        d.mkdir()
        (d / "SKILL.md").write_text("# Skill", encoding=_UTF8)
        adapter.undeploy("test-skill", "skill")
        assert not d.exists()

    def test_unit_undeploy_agent(self, tmp_path: Path) -> None:
        """undeploy removes .claude/agents/<name>.md."""
        adapter = _setup_claude(tmp_path)
        f = tmp_path / ".claude" / "agents" / "foo.md"
        f.write_text("# Agent", encoding=_UTF8)
        adapter.undeploy("foo", "agent")
        assert not f.exists()

    def test_unit_undeploy_prompt(self, tmp_path: Path) -> None:
        """undeploy removes .claude/prompts/<name>.md."""
        adapter = _setup_claude(tmp_path)
        f = tmp_path / ".claude" / "prompts" / "foo.md"
        f.write_text("# Prompt", encoding=_UTF8)
        adapter.undeploy("foo", "prompt")
        assert not f.exists()

    def test_unit_undeploy_instruction(self, tmp_path: Path) -> None:
        """undeploy removes marker section from CLAUDE.md."""
        adapter = _setup_claude(tmp_path)
        md = tmp_path / "CLAUDE.md"
        md.write_text(
            "# Project\n\n"
            "<!-- BEGIN AAM: test-artifact instruction -->\n"
            "Some content\n"
            "<!-- END AAM: test-artifact instruction -->\n",
            encoding=_UTF8,
        )
        adapter.undeploy("test-artifact", "instruction")
        assert "test-artifact" not in md.read_text(encoding=_UTF8)

    def test_unit_undeploy_command(self, tmp_path: Path) -> None:
        """undeploy removes .claude/commands/<name>.md."""
        adapter = _setup_claude(tmp_path)
        f = tmp_path / ".claude" / "commands" / "foo.md"
        f.write_text("# Command", encoding=_UTF8)
        adapter.undeploy("foo", "command")
        assert not f.exists()

    def test_unit_undeploy_rule(self, tmp_path: Path) -> None:
        """undeploy removes rule marker section from CLAUDE.md."""
        adapter = _setup_claude(tmp_path)
        md = tmp_path / "CLAUDE.md"
        md.write_text(
            "# Project\n\n"
            "<!-- BEGIN AAM: test-artifact rule -->\n"
            "Rule content\n"
            "<!-- END AAM: test-artifact rule -->\n",
            encoding=_UTF8,
        )
        adapter.undeploy("test-artifact", "rule")
        assert "test-artifact" not in md.read_text(encoding=_UTF8)

    def test_unit_undeploy_hook(self, tmp_path: Path) -> None:
        """undeploy removes AAM-tagged entries from .claude/hooks.json."""
        adapter = _setup_claude(tmp_path)
        hp = tmp_path / ".claude" / "hooks.json"
        _write_json(hp, {
            "PreToolUse": [{"command": "lint", "_aam_package": "test-pkg"}],
        })
        adapter.undeploy("test-pkg", "hook")
        hooks = json.loads(hp.read_text(encoding=_UTF8))
        remaining = hooks.get("PreToolUse", [])
        assert not any(e.get("_aam_package") == "test-pkg" for e in remaining)

    def test_unit_undeploy_mcp(self, tmp_path: Path) -> None:
        """undeploy removes namespaced entries from .mcp.json at project root."""
        adapter = _setup_claude(tmp_path)
        mp = tmp_path / ".mcp.json"
        _write_json(mp, {
            "mcpServers": {"test-pkg:server1": {"command": "node"}},
        })
        adapter.undeploy("test-pkg", "mcp")
        mcp = json.loads(mp.read_text(encoding=_UTF8))
        assert "test-pkg:server1" not in mcp["mcpServers"]

    def test_unit_undeploy_unknown_type_logs_warning(self, tmp_path: Path, caplog) -> None:
        """undeploy with unknown artifact type logs warning."""
        adapter = _setup_claude(tmp_path)
        with caplog.at_level(logging.WARNING):
            adapter.undeploy("foo", "banana")
        assert any("Unknown artifact type" in r.message for r in caplog.records)

    def test_unit_list_deployed_discovers_all_types(self, tmp_path: Path) -> None:
        """list_deployed discovers all artifact types including instruction and rule."""
        adapter = _setup_claude(tmp_path)
        b = tmp_path / ".claude"
        (b / "skills" / "my-skill").mkdir()
        (b / "skills" / "my-skill" / "SKILL.md").write_text("x", encoding=_UTF8)
        (b / "agents" / "my-agent.md").write_text("x", encoding=_UTF8)
        (b / "prompts" / "my-prompt.md").write_text("x", encoding=_UTF8)
        (b / "commands" / "my-cmd.md").write_text("x", encoding=_UTF8)
        (tmp_path / "CLAUDE.md").write_text(
            "<!-- BEGIN AAM: my-instr instruction -->\ncontent\n"
            "<!-- END AAM: my-instr instruction -->\n"
            "<!-- BEGIN AAM: my-rule rule -->\ncontent\n"
            "<!-- END AAM: my-rule rule -->\n",
            encoding=_UTF8,
        )
        _write_json(b / "hooks.json", {
            "PreToolUse": [{"command": "lint", "_aam_package": "pkg"}],
        })
        _write_json(tmp_path / ".mcp.json", {
            "mcpServers": {"pkg:server1": {"command": "node"}},
        })
        types_found = {d[1] for d in adapter.list_deployed()}
        # v0.5.0: prompts merged into commands — "prompt" no longer a separate type
        assert types_found >= {
            "skill", "agent", "command",
            "instruction", "rule", "hook", "mcp",
        }


################################################################################
#                                                                              #
# TEST: CopilotAdapter                                                         #
#                                                                              #
################################################################################


class TestCopilotAdapterLifecycle:
    """Tests for CopilotAdapter undeploy() and list_deployed()."""

    def test_unit_undeploy_skill(self, tmp_path: Path) -> None:
        """undeploy removes .github/skills/<name>/ directory."""
        adapter = _setup_copilot(tmp_path)
        d = tmp_path / ".github" / "skills" / "test-skill"
        d.mkdir()
        (d / "SKILL.md").write_text("# Skill", encoding=_UTF8)
        adapter.undeploy("test-skill", "skill")
        assert not d.exists()

    def test_unit_undeploy_agent(self, tmp_path: Path) -> None:
        """undeploy removes .github/agents/<name>.agent.md."""
        adapter = _setup_copilot(tmp_path)
        f = tmp_path / ".github" / "agents" / "foo.agent.md"
        f.write_text("# Agent", encoding=_UTF8)
        adapter.undeploy("foo", "agent")
        assert not f.exists()

    def test_unit_undeploy_prompt(self, tmp_path: Path) -> None:
        """undeploy removes .github/prompts/<name>.md."""
        adapter = _setup_copilot(tmp_path)
        f = tmp_path / ".github" / "prompts" / "foo.md"
        f.write_text("# Prompt", encoding=_UTF8)
        adapter.undeploy("foo", "prompt")
        assert not f.exists()

    def test_unit_undeploy_instruction(self, tmp_path: Path) -> None:
        """undeploy removes .github/instructions/<name>.instructions.md."""
        adapter = _setup_copilot(tmp_path)
        f = tmp_path / ".github" / "instructions" / "foo.instructions.md"
        f.write_text("# Instruction", encoding=_UTF8)
        adapter.undeploy("foo", "instruction")
        assert not f.exists()

    def test_unit_undeploy_command(self, tmp_path: Path) -> None:
        """undeploy removes .github/prompts/<name>.prompt.md."""
        adapter = _setup_copilot(tmp_path)
        f = tmp_path / ".github" / "prompts" / "foo.prompt.md"
        f.write_text("# Command", encoding=_UTF8)
        adapter.undeploy("foo", "command")
        assert not f.exists()

    def test_unit_undeploy_rule(self, tmp_path: Path) -> None:
        """undeploy removes .github/instructions/<name>.instructions.md rule."""
        adapter = _setup_copilot(tmp_path)
        f = tmp_path / ".github" / "instructions" / "foo.instructions.md"
        f.write_text("# Rule", encoding=_UTF8)
        adapter.undeploy("foo", "rule")
        assert not f.exists()

    def test_unit_undeploy_hook(self, tmp_path: Path) -> None:
        """undeploy removes AAM-tagged entries from .github/copilot-hooks.json."""
        adapter = _setup_copilot(tmp_path)
        hp = tmp_path / ".github" / "copilot-hooks.json"
        _write_json(hp, {
            "preToolUse": [{"command": "lint", "_aam_package": "test-pkg"}],
        })
        adapter.undeploy("test-pkg", "hook")
        hooks = json.loads(hp.read_text(encoding=_UTF8))
        remaining = hooks.get("preToolUse", [])
        assert not any(e.get("_aam_package") == "test-pkg" for e in remaining)

    def test_unit_undeploy_mcp(self, tmp_path: Path) -> None:
        """undeploy removes namespaced entries from .vscode/mcp.json."""
        adapter = _setup_copilot(tmp_path)
        mp = tmp_path / ".vscode" / "mcp.json"
        _write_json(mp, {
            "servers": {"test-pkg:server1": {"command": "node"}},
        })
        adapter.undeploy("test-pkg", "mcp")
        mcp = json.loads(mp.read_text(encoding=_UTF8))
        servers = mcp.get("mcpServers", mcp.get("servers", {}))
        assert "test-pkg:server1" not in servers

    def test_unit_undeploy_unknown_type_logs_warning(self, tmp_path: Path, caplog) -> None:
        """undeploy with unknown artifact type logs warning."""
        adapter = _setup_copilot(tmp_path)
        with caplog.at_level(logging.WARNING):
            adapter.undeploy("foo", "banana")
        assert any("Unknown artifact type" in r.message for r in caplog.records)

    def test_unit_list_deployed_discovers_all_types(self, tmp_path: Path) -> None:
        """list_deployed discovers skill, agent, command, instruction, hook, mcp."""
        adapter = _setup_copilot(tmp_path)
        b = tmp_path / ".github"
        (b / "skills" / "my-skill").mkdir()
        (b / "skills" / "my-skill" / "SKILL.md").write_text("x", encoding=_UTF8)
        (b / "agents" / "my-agent.agent.md").write_text("x", encoding=_UTF8)
        (b / "prompts" / "my-prompt.md").write_text("x", encoding=_UTF8)
        (b / "prompts" / "pkg:my-cmd.prompt.md").write_text("x", encoding=_UTF8)
        (b / "instructions" / "my-instr.instructions.md").write_text("x", encoding=_UTF8)
        _write_json(b / "copilot-hooks.json", {
            "preToolUse": [{"command": "lint", "_aam_package": "pkg"}],
        })
        _write_json(tmp_path / ".vscode" / "mcp.json", {
            "servers": {"pkg:server1": {"command": "node"}},
        })
        types_found = {d[1] for d in adapter.list_deployed()}
        # v0.5.0: prompts merged into commands — "prompt" no longer a separate type
        assert types_found >= {"skill", "agent", "command", "instruction", "hook", "mcp"}


################################################################################
#                                                                              #
# TEST: CodexAdapter                                                           #
#                                                                              #
################################################################################


class TestCodexAdapterLifecycle:
    """Tests for CodexAdapter undeploy() and list_deployed()."""

    def test_unit_undeploy_skill(self, tmp_path: Path) -> None:
        """undeploy removes .agents/skills/<name>/ directory."""
        adapter = _setup_codex(tmp_path)
        d = tmp_path / ".agents" / "skills" / "test-skill"
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text("# Skill", encoding=_UTF8)
        adapter.undeploy("test-skill", "skill")
        assert not d.exists()

    def test_unit_undeploy_legacy_codex_skill(self, tmp_path: Path) -> None:
        """undeploy still removes legacy ~/.codex/skills/<name>/."""
        adapter = _setup_codex(tmp_path)
        d = adapter.codex_dir / "skills" / "legacy-skill"
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text("# Legacy", encoding=_UTF8)
        adapter.undeploy("legacy-skill", "skill")
        assert not d.exists()

    def test_unit_undeploy_agent(self, tmp_path: Path) -> None:
        """undeploy removes agent marker section from AGENTS.md."""
        adapter = _setup_codex(tmp_path)
        md = tmp_path / "AGENTS.md"
        md.write_text(
            "# Project\n\n"
            "<!-- BEGIN AAM: test-agent agent -->\n"
            "Agent content\n"
            "<!-- END AAM: test-agent agent -->\n",
            encoding=_UTF8,
        )
        adapter.undeploy("test-agent", "agent")
        assert "test-agent" not in md.read_text(encoding=_UTF8)

    def test_unit_undeploy_prompt(self, tmp_path: Path) -> None:
        """undeploy removes codex_dir/prompts/<name>.md."""
        adapter = _setup_codex(tmp_path)
        f = adapter.codex_dir / "prompts" / "foo.md"
        f.write_text("# Prompt", encoding=_UTF8)
        adapter.undeploy("foo", "prompt")
        assert not f.exists()

    def test_unit_undeploy_instruction(self, tmp_path: Path) -> None:
        """undeploy removes instruction marker section from AGENTS.md."""
        adapter = _setup_codex(tmp_path)
        md = tmp_path / "AGENTS.md"
        md.write_text(
            "# Project\n\n"
            "<!-- BEGIN AAM: test-instr instruction -->\n"
            "Instruction content\n"
            "<!-- END AAM: test-instr instruction -->\n",
            encoding=_UTF8,
        )
        adapter.undeploy("test-instr", "instruction")
        assert "test-instr" not in md.read_text(encoding=_UTF8)

    def test_unit_undeploy_command(self, tmp_path: Path) -> None:
        """undeploy removes .agents/skills/<name>/ command directory."""
        adapter = _setup_codex(tmp_path)
        d = tmp_path / ".agents" / "skills" / "pkg:my-cmd"
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text("# Cmd", encoding=_UTF8)
        adapter.undeploy("pkg:my-cmd", "command")
        assert not d.exists()

    def test_unit_undeploy_rule(self, tmp_path: Path) -> None:
        """undeploy removes rule marker section from AGENTS.md."""
        adapter = _setup_codex(tmp_path)
        md = tmp_path / "AGENTS.md"
        md.write_text(
            "# Project\n\n"
            "<!-- BEGIN AAM: test-rule rule -->\n"
            "Rule content\n"
            "<!-- END AAM: test-rule rule -->\n",
            encoding=_UTF8,
        )
        adapter.undeploy("test-rule", "rule")
        assert "test-rule" not in md.read_text(encoding=_UTF8)

    def test_unit_undeploy_hook_logs_warning(self, tmp_path: Path, caplog) -> None:
        """undeploy for hook logs warning since Codex has no hook support."""
        adapter = _setup_codex(tmp_path)
        with caplog.at_level(logging.WARNING):
            adapter.undeploy("test-pkg", "hook")
        assert any("Codex" in r.message and "hook" in r.message for r in caplog.records)

    def test_unit_undeploy_mcp_logs_warning(self, tmp_path: Path, caplog) -> None:
        """undeploy for mcp logs warning since Codex has limited MCP support."""
        adapter = _setup_codex(tmp_path)
        with caplog.at_level(logging.WARNING):
            adapter.undeploy("test-pkg", "mcp")
        assert any("Codex" in r.message and "mcp" in r.message for r in caplog.records)

    def test_unit_undeploy_unknown_type_logs_warning(self, tmp_path: Path, caplog) -> None:
        """undeploy with unknown artifact type logs warning."""
        adapter = _setup_codex(tmp_path)
        with caplog.at_level(logging.WARNING):
            adapter.undeploy("foo", "banana")
        assert any("Unknown artifact type" in r.message for r in caplog.records)

    def test_unit_list_deployed_discovers_all_types(self, tmp_path: Path) -> None:
        """list_deployed discovers skill, command, agent, instruction, rule."""
        adapter = _setup_codex(tmp_path)
        agents_skills = tmp_path / ".agents" / "skills"
        (agents_skills / "my-skill").mkdir(parents=True)
        (agents_skills / "my-skill" / "SKILL.md").write_text("x", encoding=_UTF8)
        (agents_skills / "pkg:my-cmd").mkdir()
        (agents_skills / "pkg:my-cmd" / "SKILL.md").write_text("x", encoding=_UTF8)
        (adapter.codex_dir / "prompts" / "my-prompt.md").write_text("x", encoding=_UTF8)
        (tmp_path / "AGENTS.md").write_text(
            "<!-- BEGIN AAM: my-agent agent -->\ncontent\n"
            "<!-- END AAM: my-agent agent -->\n"
            "<!-- BEGIN AAM: my-instr instruction -->\ncontent\n"
            "<!-- END AAM: my-instr instruction -->\n"
            "<!-- BEGIN AAM: my-rule rule -->\ncontent\n"
            "<!-- END AAM: my-rule rule -->\n",
            encoding=_UTF8,
        )
        types_found = {d[1] for d in adapter.list_deployed()}
        # v0.5.0: prompts merged into commands — "prompt" no longer a separate type
        assert types_found >= {
            "skill", "command", "agent", "instruction", "rule",
        }

    def test_unit_list_deployed_includes_legacy_codex_skills(
        self, tmp_path: Path
    ) -> None:
        """list_deployed still finds skills under legacy ~/.codex/skills/."""
        adapter = _setup_codex(tmp_path)
        legacy = adapter.codex_dir / "skills" / "legacy-skill"
        legacy.mkdir(parents=True)
        (legacy / "SKILL.md").write_text("x", encoding=_UTF8)
        names = {d[0] for d in adapter.list_deployed() if d[1] == "skill"}
        assert "legacy-skill" in names


################################################################################
#                                                                              #
# TEST: Hook Event Mappings (v0.5.0)                                           #
#                                                                              #
################################################################################


class TestHookEventMappings:
    """Tests for v0.5.0 hook event mapping updates."""

    def test_unit_copilot_supports_5_events(self) -> None:
        """Copilot supports exactly 5 hook events (pre_compact added in v0.5.0)."""
        assert len(SUPPORTED_HOOK_EVENTS["copilot"]) == 5

    def test_unit_sub_agent_start_removed(self) -> None:
        """sub_agent_start event is removed in v0.5.0."""
        assert "sub_agent_start" not in HOOK_EVENT_TO_PLATFORM

    def test_unit_copilot_uses_pascal_case_for_most_events(self) -> None:
        """Most Copilot events use PascalCase; camelCase events are exceptions."""
        pascal_case_events = {"PreToolUse", "PreCompact"}
        camel_case_events = {"userPromptSubmitted", "sessionStart", "sessionEnd"}
        copilot_events = {
            ev_map["copilot"]
            for ev_map in HOOK_EVENT_TO_PLATFORM.values()
            if "copilot" in ev_map
        }
        for event in copilot_events:
            assert event in pascal_case_events or event in camel_case_events, (
                f"Copilot event '{event}' is neither PascalCase nor known camelCase"
            )

    def test_unit_session_end_has_copilot(self) -> None:
        """session_end event now has Copilot support."""
        assert "copilot" in HOOK_EVENT_TO_PLATFORM["session_end"]
        assert HOOK_EVENT_TO_PLATFORM["session_end"]["copilot"] == "sessionEnd"
