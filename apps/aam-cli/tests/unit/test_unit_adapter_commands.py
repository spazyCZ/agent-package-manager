"""Unit tests for adapter deploy_command, deploy_rule, deploy_hook, deploy_mcp.

Tests all four adapters (Claude, Cursor, Copilot, Codex) for each new method:
  - deploy_command: correct target paths and file transformations
  - deploy_rule: correct target paths and frontmatter conversion
  - deploy_hook: event name translation, unsupported event warnings
  - deploy_mcp: namespace server keys, correct config file location
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
from aam_cli.core.manifest import ArtifactRef

################################################################################
#                                                                              #
# HELPERS                                                                      #
#                                                                              #
################################################################################


def _make_artifact_ref(name: str, path: str, description: str = "Test artifact") -> ArtifactRef:
    """Create a minimal ArtifactRef."""
    return ArtifactRef(name=name, path=path, description=description)


def _make_cmd_file(tmp_path: Path, name: str, content: str = "Do something useful.") -> Path:
    """Write a command markdown file and return its path."""
    cmd_file = tmp_path / f"{name}.md"
    cmd_file.write_text(f"# {name}\n\n{content}", encoding="utf-8")
    return cmd_file


def _make_rule_file(tmp_path: Path, name: str, globs: str | None = None) -> Path:
    """Write a rule markdown file and return its path."""
    if globs:
        # Quote the glob pattern to avoid YAML alias interpretation of '*'
        content = f'---\ndescription: Rule {name}\nglobs: "{globs}"\n---\n\nRule body.'
    else:
        content = f"# {name}\n\nRule body."
    rule_file = tmp_path / f"{name}.md"
    rule_file.write_text(content, encoding="utf-8")
    return rule_file


def _make_hooks_json(tmp_path: Path, events: dict) -> Path:
    """Write a hooks.json file with canonical UAAPS event names."""
    hooks_file = tmp_path / "hooks.json"
    hooks_file.write_text(json.dumps(events), encoding="utf-8")
    return hooks_file


def _make_servers_json(tmp_path: Path, servers: dict) -> Path:
    """Write a servers.json file with MCP server definitions."""
    servers_file = tmp_path / "servers.json"
    servers_file.write_text(json.dumps({"mcpServers": servers}), encoding="utf-8")
    return servers_file


################################################################################
#                                                                              #
# TEST: ClaudeAdapter                                                          #
#                                                                              #
################################################################################


class TestClaudeAdapterCommands:
    """Tests for ClaudeAdapter new deploy methods."""

    def test_unit_deploy_command_correct_path(self, tmp_path: Path):
        """deploy_command writes to .claude/commands/<pkg>:<name>.md."""
        adapter = ClaudeAdapter(tmp_path)
        cmd_file = _make_cmd_file(tmp_path, "my-cmd")
        ref = _make_artifact_ref("my-cmd", "commands/my-cmd.md")
        config = {"package_name": "@myorg/mypkg"}

        dest = adapter.deploy_command(cmd_file, ref, config)

        assert dest.name == "myorg--mypkg:my-cmd.md"
        assert dest.parent.name == "commands"
        assert dest.exists()

    def test_unit_deploy_rule_appended_to_claude_md(self, tmp_path: Path):
        """deploy_rule appends rule content to CLAUDE.md with markers."""
        adapter = ClaudeAdapter(tmp_path)
        rule_file = _make_rule_file(tmp_path, "my-rule")
        ref = _make_artifact_ref("my-rule", "rules/my-rule.md")

        dest = adapter.deploy_rule(rule_file, ref, {})

        assert dest.name == "CLAUDE.md"
        content = dest.read_text(encoding="utf-8")
        assert "my-rule" in content
        assert "BEGIN AAM" in content

    def test_unit_deploy_hook_translates_event_names(self, tmp_path: Path):
        """deploy_hook translates pre_tool_use → PreToolUse in .claude/hooks.json."""
        adapter = ClaudeAdapter(tmp_path)
        hooks_json = _make_hooks_json(
            tmp_path,
            {"pre_tool_use": [{"type": "command", "command": "echo hi"}]},
        )
        config = {"package_name": "@myorg/pkg"}

        dest = adapter.deploy_hook(hooks_json, config)

        assert dest.name == "hooks.json"
        hooks = json.loads(dest.read_text(encoding="utf-8"))
        assert "PreToolUse" in hooks
        assert len(hooks["PreToolUse"]) == 1

    def test_unit_deploy_hook_skips_unsupported_events(self, tmp_path: Path, caplog):
        """deploy_hook logs warning and skips events with no Claude equivalent."""
        adapter = ClaudeAdapter(tmp_path)
        # Create a fake canonical event that has no Claude mapping
        hooks_json = _make_hooks_json(
            tmp_path,
            {"unknown_event": [{"type": "command", "command": "echo"}]},
        )

        with caplog.at_level(logging.WARNING):
            adapter.deploy_hook(hooks_json, {"package_name": "mypkg"})

        assert any("unknown_event" in r.message for r in caplog.records)

    def test_unit_deploy_mcp_namespaces_server_keys(self, tmp_path: Path):
        """deploy_mcp writes namespaced server keys to .mcp.json."""
        adapter = ClaudeAdapter(tmp_path)
        servers_json = _make_servers_json(tmp_path, {"my-server": {"command": "my-cmd"}})
        config = {"package_name": "@myorg/pkg"}

        dest = adapter.deploy_mcp(servers_json, config)

        assert dest.name == ".mcp.json"
        mcp = json.loads(dest.read_text(encoding="utf-8"))
        assert "myorg--pkg:my-server" in mcp["mcpServers"]

    def test_unit_deploy_mcp_merges_existing_config(self, tmp_path: Path):
        """deploy_mcp merges new server into existing .mcp.json."""
        adapter = ClaudeAdapter(tmp_path)

        # Write existing .mcp.json
        existing_mcp = tmp_path / ".mcp.json"
        existing_mcp.write_text(
            json.dumps({"mcpServers": {"existing:server": {"command": "old"}}}),
            encoding="utf-8",
        )

        servers_json = _make_servers_json(tmp_path, {"new-server": {"command": "new-cmd"}})
        config = {"package_name": "mypkg"}

        adapter.deploy_mcp(servers_json, config)

        mcp = json.loads(existing_mcp.read_text(encoding="utf-8"))
        assert "existing:server" in mcp["mcpServers"]
        assert "mypkg:new-server" in mcp["mcpServers"]


################################################################################
#                                                                              #
# TEST: CursorAdapter                                                          #
#                                                                              #
################################################################################


class TestCursorAdapterCommands:
    """Tests for CursorAdapter new deploy methods."""

    def test_unit_deploy_command_creates_skill_with_flag(self, tmp_path: Path):
        """deploy_command creates .cursor/skills/<pkg>:<name>/SKILL.md with disable-model-invocation."""
        adapter = CursorAdapter(tmp_path)
        cmd_file = _make_cmd_file(tmp_path, "my-cmd")
        ref = _make_artifact_ref("my-cmd", "commands/my-cmd.md", "My command")
        config = {"package_name": "@scope/pkg"}

        dest = adapter.deploy_command(cmd_file, ref, config)

        assert dest.is_dir()
        skill_md = dest / "SKILL.md"
        assert skill_md.exists()
        content = skill_md.read_text(encoding="utf-8")
        assert "disable-model-invocation: true" in content

    def test_unit_deploy_rule_creates_mdc_in_rules_dir(self, tmp_path: Path):
        """deploy_rule creates .cursor/rules/<name>.mdc with frontmatter."""
        adapter = CursorAdapter(tmp_path)
        rule_file = _make_rule_file(tmp_path, "my-rule")
        ref = _make_artifact_ref("my-rule", "rules/my-rule.md", "My rule")

        dest = adapter.deploy_rule(rule_file, ref, {})

        assert dest.suffix == ".mdc"
        assert dest.parent.name == "rules"
        content = dest.read_text(encoding="utf-8")
        assert "---" in content  # Has frontmatter
        assert "alwaysApply: true" in content

    def test_unit_deploy_hook_translates_to_cursor_events(self, tmp_path: Path):
        """deploy_hook translates pre_tool_use → beforeShellCommand."""
        adapter = CursorAdapter(tmp_path)
        hooks_json = _make_hooks_json(
            tmp_path,
            {"pre_tool_use": [{"type": "command", "command": "lint"}]},
        )

        dest = adapter.deploy_hook(hooks_json, {"package_name": "mypkg"})

        assert dest.name == "hooks.json"
        hooks = json.loads(dest.read_text(encoding="utf-8"))
        assert "beforeShellCommand" in hooks

    def test_unit_deploy_hook_warns_for_unsupported_cursor_events(
        self, tmp_path: Path, caplog
    ):
        """deploy_hook logs warning for Claude-only events like pre_compact."""
        adapter = CursorAdapter(tmp_path)
        hooks_json = _make_hooks_json(
            tmp_path,
            {"pre_compact": [{"type": "command", "command": "compact"}]},
        )

        with caplog.at_level(logging.WARNING):
            adapter.deploy_hook(hooks_json, {"package_name": "mypkg"})

        # pre_compact is not supported in Cursor
        assert any("pre_compact" in r.message for r in caplog.records)

    def test_unit_deploy_mcp_writes_cursor_mcp_json(self, tmp_path: Path):
        """deploy_mcp writes namespaced servers to .cursor/mcp.json."""
        adapter = CursorAdapter(tmp_path)
        servers_json = _make_servers_json(tmp_path, {"server1": {"url": "http://localhost"}})
        config = {"package_name": "mypkg"}

        dest = adapter.deploy_mcp(servers_json, config)

        assert str(dest).endswith(".cursor/mcp.json")
        mcp = json.loads(dest.read_text(encoding="utf-8"))
        assert "mypkg:server1" in mcp["mcpServers"]


################################################################################
#                                                                              #
# TEST: CopilotAdapter                                                         #
#                                                                              #
################################################################################


class TestCopilotAdapterCommands:
    """Tests for CopilotAdapter new deploy methods."""

    def test_unit_deploy_command_to_github_prompts(self, tmp_path: Path):
        """deploy_command writes to .github/prompts/<pkg>:<name>.prompt.md."""
        adapter = CopilotAdapter(tmp_path)
        cmd_file = _make_cmd_file(tmp_path, "my-cmd")
        ref = _make_artifact_ref("my-cmd", "commands/my-cmd.md")
        config = {"package_name": "@scope/pkg"}

        dest = adapter.deploy_command(cmd_file, ref, config)

        assert dest.name.endswith(".prompt.md")
        assert "scope--pkg:my-cmd" in dest.name
        assert dest.parent.name == "prompts"

    def test_unit_deploy_rule_translates_globs_to_apply_to(self, tmp_path: Path):
        """deploy_rule converts globs → applyTo for Copilot instructions."""
        adapter = CopilotAdapter(tmp_path)
        rule_file = _make_rule_file(tmp_path, "my-rule", globs="*.ts")
        ref = _make_artifact_ref("my-rule", "rules/my-rule.md")

        dest = adapter.deploy_rule(rule_file, ref, {})

        assert dest.name.endswith(".instructions.md")
        content = dest.read_text(encoding="utf-8")
        assert "applyTo" in content
        assert "*.ts" in content

    def test_unit_deploy_hook_supported_events_written(self, tmp_path: Path, caplog):
        """deploy_hook writes supported events and warns for unsupported ones."""
        adapter = CopilotAdapter(tmp_path)
        hooks_json = _make_hooks_json(
            tmp_path,
            {
                "pre_tool_use": [{"type": "command", "command": "lint"}],
                "pre_compact": [{"type": "command", "command": "compact"}],
                "notification": [{"type": "command", "command": "notify"}],
            },
        )

        with caplog.at_level(logging.WARNING):
            dest = adapter.deploy_hook(hooks_json, {"package_name": "mypkg"})

        hooks = json.loads(dest.read_text(encoding="utf-8"))
        # Both pre_tool_use and pre_compact are now supported by Copilot (PascalCase)
        assert "PreToolUse" in hooks
        assert "PreCompact" in hooks
        # notification is NOT supported by Copilot — should be warned and skipped
        assert "Notification" not in hooks
        assert any("notification" in r.message for r in caplog.records)

    def test_unit_deploy_mcp_writes_vscode_mcp_json(self, tmp_path: Path):
        """deploy_mcp writes to .vscode/mcp.json with 'servers' key."""
        adapter = CopilotAdapter(tmp_path)
        servers_json = _make_servers_json(tmp_path, {"copilot-server": {"url": "..."}})
        config = {"package_name": "mypkg"}

        dest = adapter.deploy_mcp(servers_json, config)

        assert str(dest).endswith(".vscode/mcp.json")
        mcp = json.loads(dest.read_text(encoding="utf-8"))
        assert "servers" in mcp
        assert "mypkg:copilot-server" in mcp["servers"]


################################################################################
#                                                                              #
# TEST: CodexAdapter                                                           #
#                                                                              #
################################################################################


class TestCodexAdapterCommands:
    """Tests for CodexAdapter new deploy methods."""

    def test_unit_deploy_command_to_codex_skills(self, tmp_path: Path):
        """deploy_command writes to .agents/skills/<pkg>:<name>/SKILL.md."""
        adapter = CodexAdapter(tmp_path)
        # Override home-based dirs to keep tests isolated
        adapter.codex_dir = tmp_path / ".codex"
        adapter.agents_user_dir = tmp_path / ".agents-user"

        cmd_file = _make_cmd_file(tmp_path, "my-cmd")
        ref = _make_artifact_ref("my-cmd", "commands/my-cmd.md", "My cmd")
        config = {"package_name": "@scope/pkg", "skill_scope": "project"}

        dest = adapter.deploy_command(cmd_file, ref, config)

        assert dest == tmp_path / ".agents" / "skills" / "scope--pkg:my-cmd"
        assert dest.is_dir()
        skill_md = dest / "SKILL.md"
        assert skill_md.exists()
        content = skill_md.read_text(encoding="utf-8")
        assert "disable-model-invocation: true" in content

    def test_unit_deploy_rule_appended_to_agents_md(self, tmp_path: Path):
        """deploy_rule appends rule content to AGENTS.md with markers."""
        adapter = CodexAdapter(tmp_path)
        rule_file = _make_rule_file(tmp_path, "my-rule")
        ref = _make_artifact_ref("my-rule", "rules/my-rule.md")

        dest = adapter.deploy_rule(rule_file, ref, {})

        assert dest.name == "AGENTS.md"
        content = dest.read_text(encoding="utf-8")
        assert "BEGIN AAM" in content
        assert "my-rule" in content

    def test_unit_deploy_hook_logs_warning_not_supported(
        self, tmp_path: Path, caplog
    ):
        """deploy_hook logs a warning because Codex has no hook support."""
        adapter = CodexAdapter(tmp_path)
        hooks_json = _make_hooks_json(tmp_path, {"pre_tool_use": []})

        with caplog.at_level(logging.WARNING):
            dest = adapter.deploy_hook(hooks_json, {"package_name": "mypkg"})

        # No file should be written; sentinel path returned
        assert dest == hooks_json
        assert any("Codex" in r.message and "hook" in r.message.lower() for r in caplog.records)

    def test_unit_deploy_mcp_logs_warning_limited_support(
        self, tmp_path: Path, caplog
    ):
        """deploy_mcp logs a warning because Codex has limited MCP support."""
        adapter = CodexAdapter(tmp_path)
        servers_json = _make_servers_json(tmp_path, {"my-server": {}})

        with caplog.at_level(logging.WARNING):
            dest = adapter.deploy_mcp(servers_json, {"package_name": "mypkg"})

        # No file should be written; sentinel path returned
        assert dest == servers_json
        assert any("Codex" in r.message and "MCP" in r.message for r in caplog.records)


################################################################################
#                                                                              #
# TEST: Hook event mappings (UAAPS v0.4.0 parity)                             #
#                                                                              #
################################################################################


class TestHookEventMappings:
    """Tests for HOOK_EVENT_TO_PLATFORM covering all canonical events."""

    def test_unit_copilot_has_5_supported_events(self):
        """Copilot platform has exactly 5 mapped hook events (pre_compact added)."""
        from aam_cli.converters.mappings import HOOK_EVENT_TO_PLATFORM

        copilot_events = {
            canonical
            for canonical, platforms in HOOK_EVENT_TO_PLATFORM.items()
            if "copilot" in platforms
        }
        assert len(copilot_events) == 5

    def test_unit_copilot_uses_pascal_case_for_pre_tool_use(self):
        """Copilot pre_tool_use event uses PascalCase (PreToolUse)."""
        from aam_cli.converters.mappings import HOOK_EVENT_TO_PLATFORM

        assert HOOK_EVENT_TO_PLATFORM["pre_tool_use"]["copilot"] == "PreToolUse"

    def test_unit_sub_agent_start_removed_in_v050(self):
        """sub_agent_start canonical event was removed in UAAPS v0.5.0."""
        from aam_cli.converters.mappings import HOOK_EVENT_TO_PLATFORM

        assert "sub_agent_start" not in HOOK_EVENT_TO_PLATFORM

    def test_unit_post_tool_use_bug_fixed(self):
        """post_tool_use mapping has 'claude-code' key (not 'post_tool_use')."""
        from aam_cli.converters.mappings import HOOK_EVENT_TO_PLATFORM

        mapping = HOOK_EVENT_TO_PLATFORM["post_tool_use"]
        assert "claude-code" in mapping
        assert "post_tool_use" not in mapping

    def test_unit_translate_hook_event_copilot_pre_tool_use(self):
        """translate_hook_event translates pre_tool_use to Copilot PascalCase."""
        from aam_cli.converters.mappings import translate_hook_event

        result = translate_hook_event("pre_tool_use", "copilot")
        assert result == "PreToolUse"

    def test_unit_translate_hook_event_copilot_stop_not_supported(self):
        """stop event is not supported by Copilot in v0.5.0."""
        from aam_cli.converters.mappings import translate_hook_event

        result = translate_hook_event("stop", "copilot")
        assert result is None

    def test_unit_session_end_supported_by_copilot(self):
        """session_end event now has a Copilot mapping in v0.5.0."""
        from aam_cli.converters.mappings import translate_hook_event

        result = translate_hook_event("session_end", "copilot")
        assert result == "sessionEnd"

    def test_unit_supported_hook_events_generated_correctly(self):
        """SUPPORTED_HOOK_EVENTS is auto-generated from HOOK_EVENT_TO_PLATFORM."""
        from aam_cli.converters.mappings import SUPPORTED_HOOK_EVENTS

        assert "copilot" in SUPPORTED_HOOK_EVENTS
        assert "claude-code" in SUPPORTED_HOOK_EVENTS
        assert "cursor" in SUPPORTED_HOOK_EVENTS
        assert len(SUPPORTED_HOOK_EVENTS["copilot"]) == 5
