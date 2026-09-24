"""Claude platform adapter.

Deploys AAM artifacts into the Claude Code filesystem structure:
  - Skills       → ``.claude/skills/<fs-name>/``
  - Agents       → ``.claude/agents/<fs-name>.md``
  - Commands     → ``.claude/commands/<pkg>:<name>.md`` (simple) or
                   ``.claude/prompts/<name>.md`` (parameterized/template)
  - Instructions → ``CLAUDE.md`` (marker-delimited section)

UAAPS v0.5.0: prompts merged into commands.

Decision reference: DESIGN.md Section 8.3.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import json
import logging
import re
import shutil
from pathlib import Path
from typing import Any

from aam_cli.core.manifest import ArtifactRef
from aam_cli.utils.naming import parse_package_name, to_filesystem_name

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# CONSTANTS                                                                    #
#                                                                              #
################################################################################

# Marker templates for AAM-managed sections inside CLAUDE.md.
# Only used for instructions — agents are now discrete files.
BEGIN_MARKER_TEMPLATE: str = "<!-- BEGIN AAM: {name} {kind} -->"
END_MARKER_TEMPLATE: str = "<!-- END AAM: {name} {kind} -->"

################################################################################
#                                                                              #
# CLAUDE ADAPTER                                                               #
#                                                                              #
################################################################################


class ClaudeAdapter:
    """Claude Code platform adapter.

    Skills, agents, and commands are deployed to a ``.claude/`` directory.
    Instructions are merged into ``CLAUDE.md`` at the project root using
    HTML comment markers.
    """

    def __init__(self, project_root: Path) -> None:
        """Initialize the Claude adapter.

        Args:
            project_root: Root directory of the user's project.
        """
        self.name = "claude-code"
        self.project_root = project_root.resolve()
        self.claude_dir = self.project_root / ".claude"

    # ------------------------------------------------------------------
    # Deploy methods
    # ------------------------------------------------------------------

    def deploy_skill(
        self,
        skill_path: Path,
        skill_ref: ArtifactRef,
        _config: dict[str, str],
    ) -> Path:
        """Deploy a skill to ``.claude/skills/<fs-name>/``.

        Copies the entire skill directory (including SKILL.md).

        Args:
            skill_path: Path to the extracted skill directory.
            skill_ref: Artifact reference from the manifest.
            _config: Platform config (unused currently).

        Returns:
            Destination path.
        """
        fs_name = self._artifact_fs_name(skill_ref.name)
        dest = self.claude_dir / "skills" / fs_name

        logger.info(f"Deploying skill '{skill_ref.name}' -> {dest}")

        # -----
        # Remove existing deployment, then copy
        # -----
        if dest.exists():
            shutil.rmtree(dest)

        dest.mkdir(parents=True, exist_ok=True)

        if skill_path.is_dir():
            shutil.copytree(skill_path, dest, dirs_exist_ok=True)
        else:
            # Single file skill
            shutil.copy2(skill_path, dest / skill_path.name)

        logger.info(f"Skill deployed: {dest}")
        return dest

    def deploy_agent(
        self,
        agent_path: Path,
        agent_ref: ArtifactRef,
        _config: dict[str, str],
    ) -> Path:
        """Deploy an agent to ``.claude/agents/<fs-name>.md``.

        Reads the agent's system-prompt.md and writes it as a discrete
        markdown file in the ``.claude/agents/`` directory.

        Args:
            agent_path: Path to the extracted agent directory.
            agent_ref: Artifact reference from the manifest.
            _config: Platform config.

        Returns:
            Path to the created agent file.
        """
        fs_name = self._artifact_fs_name(agent_ref.name)
        dest = self.claude_dir / "agents" / f"{fs_name}.md"

        logger.info(f"Deploying agent '{agent_ref.name}' -> {dest}")

        content = self._read_agent_content(agent_path, agent_ref)

        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")

        logger.info(f"Agent deployed: {dest}")
        return dest

    def deploy_instruction(
        self,
        instr_path: Path,
        instr_ref: ArtifactRef,
        _config: dict[str, str],
    ) -> Path:
        """Deploy an instruction section into ``CLAUDE.md``.

        Reads the instruction markdown and appends it as a
        marker-delimited section in the project-root ``CLAUDE.md``.

        Args:
            instr_path: Path to the instruction file.
            instr_ref: Artifact reference from the manifest.
            _config: Platform config.

        Returns:
            Path to CLAUDE.md.
        """
        logger.info(f"Deploying instruction '{instr_ref.name}' -> CLAUDE.md")

        content = instr_path.read_text(encoding="utf-8")

        claude_md = self.project_root / "CLAUDE.md"
        self._upsert_marker_section(claude_md, instr_ref.name, "instruction", content)

        logger.info(f"Instruction deployed to: {claude_md}")
        return claude_md

    def deploy_command(
        self,
        cmd_path: Path,
        cmd_ref: ArtifactRef,
        config: dict[str, str],
    ) -> Path:
        """Deploy a command to Claude.

        Simple commands go to ``.claude/commands/<pkg>:<name>.md``.
        Parameterized commands (templates with variables) go to
        ``.claude/prompts/<fs-name>.md`` for Claude's native prompt support.

        Args:
            cmd_path: Path to the command markdown file.
            cmd_ref: Artifact reference from the manifest.
            config: Platform config; ``package_name`` key used for namespacing.

        Returns:
            Destination path.
        """
        if self._has_variables(cmd_path):
            fs_name = self._artifact_fs_name(cmd_ref.name)
            dest = self.claude_dir / "prompts" / f"{fs_name}.md"
            logger.info(f"Deploying parameterized command '{cmd_ref.name}' -> {dest}")
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(cmd_path, dest)
        else:
            pkg_name = config.get("package_name", "unknown")
            safe_pkg = pkg_name.lstrip("@").replace("/", "--")
            safe_name = self._artifact_fs_name(cmd_ref.name)
            dest = self.claude_dir / "commands" / f"{safe_pkg}:{safe_name}.md"
            logger.info(f"Deploying command '{cmd_ref.name}' -> {dest}")
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(cmd_path, dest)

        logger.info(f"Command deployed: {dest}")
        return dest

    def deploy_rule(
        self,
        rule_path: Path,
        rule_ref: ArtifactRef,
        _config: dict[str, str],
    ) -> Path:
        """Deploy a rule by appending it to ``CLAUDE.md``.

        Rules are merged into ``CLAUDE.md`` using the same marker-delimited
        section mechanism used for instructions.

        Args:
            rule_path: Path to the rule markdown file.
            rule_ref: Artifact reference from the manifest.
            _config: Platform config (unused).

        Returns:
            Path to CLAUDE.md.
        """
        logger.info(f"Deploying rule '{rule_ref.name}' -> CLAUDE.md")

        content = rule_path.read_text(encoding="utf-8")

        claude_md = self.project_root / "CLAUDE.md"
        self._upsert_marker_section(claude_md, rule_ref.name, "rule", content)

        logger.info(f"Rule deployed to: {claude_md}")
        return claude_md

    def deploy_prompt(
        self,
        prompt_path: Path,
        prompt_ref: ArtifactRef,
        _config: dict[str, str],
    ) -> Path:
        """Deploy a prompt to ``.claude/prompts/<name>.md``.

        Args:
            prompt_path: Path to the prompt markdown file.
            prompt_ref: Artifact reference from the manifest.
            _config: Platform config (unused).

        Returns:
            Destination path.
        """
        fs_name = self._artifact_fs_name(prompt_ref.name)
        dest = self.claude_dir / "prompts" / f"{fs_name}.md"

        logger.info(f"Deploying prompt '{prompt_ref.name}' -> {dest}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(prompt_path, dest)

        logger.info(f"Prompt deployed: {dest}")
        return dest

    def deploy_hook(
        self,
        hooks_json_path: Path,
        config: dict[str, str],
    ) -> Path:
        """Merge lifecycle hooks into ``.claude/hooks.json``.

        Reads a UAAPS ``hooks/hooks.json`` (keyed by canonical event names)
        and merges the hooks into the Claude ``hooks.json`` file, translating
        event names and namespacing hook keys with the package name.

        Args:
            hooks_json_path: Path to the package ``hooks/hooks.json``.
            config: Platform config; ``package_name`` key used for namespacing.

        Returns:
            Path to ``.claude/hooks.json``.
        """
        from aam_cli.converters.mappings import translate_hook_event

        pkg_name = config.get("package_name", "unknown")
        dest = self.claude_dir / "hooks.json"
        dest.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Merging hooks from '{hooks_json_path}' -> {dest}")

        # -----
        # Load source hooks
        # -----
        source_hooks: dict[str, Any] = json.loads(hooks_json_path.read_text(encoding="utf-8"))

        # -----
        # Load existing Claude hooks.json or start fresh
        # -----
        existing: dict[str, Any] = {}
        if dest.is_file():
            existing = json.loads(dest.read_text(encoding="utf-8"))

        # -----
        # Translate and merge each event
        # -----
        for canonical_event, hook_entries in source_hooks.items():
            platform_event = translate_hook_event(canonical_event, "claude-code")
            if not platform_event:
                logger.warning(
                    f"Hook event '{canonical_event}' has no Claude equivalent — skipping"
                )
                continue

            if platform_event not in existing:
                existing[platform_event] = []

            # Namespace each hook entry's ID/description with the package name
            for entry in hook_entries if isinstance(hook_entries, list) else [hook_entries]:
                namespaced = dict(entry)
                namespaced.setdefault("_aam_package", pkg_name)
                existing[platform_event].append(namespaced)

        dest.write_text(json.dumps(existing, indent=2), encoding="utf-8")
        logger.info(f"Hooks merged into: {dest}")
        return dest

    def deploy_mcp(
        self,
        servers_json_path: Path,
        config: dict[str, str],
    ) -> Path:
        """Merge MCP server config into ``.mcp.json``.

        Reads a UAAPS ``mcp/servers.json`` and merges server entries into
        the project-root ``.mcp.json``, namespacing server keys with the
        package name to prevent collisions.

        Args:
            servers_json_path: Path to the package ``mcp/servers.json``.
            config: Platform config; ``package_name`` key used for namespacing.

        Returns:
            Path to ``.mcp.json``.
        """
        pkg_name = config.get("package_name", "unknown")
        safe_pkg = pkg_name.lstrip("@").replace("/", "--")
        dest = self.project_root / ".mcp.json"

        logger.info(f"Merging MCP servers from '{servers_json_path}' -> {dest}")

        # -----
        # Load source servers
        # -----
        source: dict[str, Any] = json.loads(servers_json_path.read_text(encoding="utf-8"))
        servers: dict[str, Any] = source.get("mcpServers", source)

        # -----
        # Load existing .mcp.json or start fresh
        # -----
        existing: dict[str, Any] = {"mcpServers": {}}
        if dest.is_file():
            existing = json.loads(dest.read_text(encoding="utf-8"))
        existing.setdefault("mcpServers", {})

        # -----
        # Namespace and merge each server key
        # -----
        for server_key, server_cfg in servers.items():
            namespaced_key = f"{safe_pkg}:{server_key}"
            existing["mcpServers"][namespaced_key] = server_cfg
            logger.debug(f"Added MCP server: {namespaced_key}")

        dest.write_text(json.dumps(existing, indent=2), encoding="utf-8")
        logger.info(f"MCP servers merged into: {dest}")
        return dest

    # ------------------------------------------------------------------
    # Undeploy and list
    # ------------------------------------------------------------------

    def undeploy(self, artifact_name: str, artifact_type: str) -> None:
        """Remove a deployed artifact.

        Args:
            artifact_name: Name of the artifact.
            artifact_type: One of skill, agent, prompt, instruction,
                command, rule, hook, mcp.
        """
        fs_name = self._artifact_fs_name(artifact_name)

        logger.info(f"Undeploying {artifact_type} '{artifact_name}' from claude")

        if artifact_type == "skill":
            path = self.claude_dir / "skills" / fs_name
            if path.is_dir():
                shutil.rmtree(path)
                logger.info(f"Removed skill directory: {path}")

        elif artifact_type == "agent":
            path = self.claude_dir / "agents" / f"{fs_name}.md"
            if path.is_file():
                path.unlink()
                logger.info(f"Removed agent file: {path}")

        elif artifact_type == "instruction":
            claude_md = self.project_root / "CLAUDE.md"
            self._remove_marker_section(claude_md, artifact_name, "instruction")

        elif artifact_type in ("prompt", "command"):
            # v0.5.0: prompts merged into commands; check both locations
            prompt_path = self.claude_dir / "prompts" / f"{fs_name}.md"
            if prompt_path.is_file():
                prompt_path.unlink()
                logger.info(f"Removed command (template): {prompt_path}")
            cmd_path = self.claude_dir / "commands" / f"{fs_name}.md"
            if cmd_path.is_file():
                cmd_path.unlink()
                logger.info(f"Removed command: {cmd_path}")

        elif artifact_type == "rule":
            claude_md = self.project_root / "CLAUDE.md"
            self._remove_marker_section(claude_md, artifact_name, "rule")

        elif artifact_type == "hook":
            self._remove_hook_entries(artifact_name)

        elif artifact_type == "mcp":
            self._remove_mcp_entries(artifact_name)

        else:
            logger.warning(
                f"Unknown artifact type '{artifact_type}' for undeploy, skipping"
            )

    def list_deployed(self) -> list[tuple[str, str, Path]]:
        """List all deployed artifacts.

        Returns:
            List of ``(name, type, path)`` tuples.
        """
        deployed: list[tuple[str, str, Path]] = []

        # -----
        # Skills
        # -----
        skills_dir = self.claude_dir / "skills"
        if skills_dir.is_dir():
            for entry in skills_dir.iterdir():
                if entry.is_dir():
                    deployed.append((entry.name, "skill", entry))

        # -----
        # Agents
        # -----
        agents_dir = self.claude_dir / "agents"
        if agents_dir.is_dir():
            for entry in agents_dir.iterdir():
                if entry.suffix == ".md":
                    deployed.append((entry.stem, "agent", entry))

        # -----
        # Commands (templates) from prompts dir
        # -----
        prompts_dir = self.claude_dir / "prompts"
        if prompts_dir.is_dir():
            for entry in prompts_dir.iterdir():
                if entry.suffix == ".md":
                    deployed.append((entry.stem, "command", entry))

        # -----
        # Commands
        # -----
        commands_dir = self.claude_dir / "commands"
        if commands_dir.is_dir():
            for entry in commands_dir.iterdir():
                if entry.suffix == ".md":
                    deployed.append((entry.stem, "command", entry))

        # -----
        # Instructions and rules from CLAUDE.md markers
        # -----
        claude_md = self.project_root / "CLAUDE.md"
        if claude_md.is_file():
            deployed.extend(self._list_marker_sections(claude_md))

        # -----
        # Hooks (AAM-namespaced entries in .claude/hooks.json)
        # -----
        hooks_path = self.claude_dir / "hooks.json"
        if hooks_path.is_file():
            deployed.extend(self._list_hook_entries(hooks_path))

        # -----
        # MCP (AAM-namespaced entries in .mcp.json)
        # -----
        mcp_path = self.project_root / ".mcp.json"
        if mcp_path.is_file():
            deployed.extend(self._list_mcp_entries(mcp_path))

        return deployed

    # ------------------------------------------------------------------
    # Marker-based section management (instructions only)
    # ------------------------------------------------------------------

    def _upsert_marker_section(
        self,
        file_path: Path,
        name: str,
        kind: str,
        content: str,
    ) -> None:
        """Insert or replace a marker-delimited section in a file.

        If the file does not exist it is created. Existing user content
        outside AAM markers is preserved.

        Args:
            file_path: Path to the target markdown file.
            name: Artifact name (used in markers).
            kind: Artifact kind (``"instruction"``).
            content: Markdown body to place between the markers.
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)

        begin_marker = BEGIN_MARKER_TEMPLATE.format(name=name, kind=kind)
        end_marker = END_MARKER_TEMPLATE.format(name=name, kind=kind)

        section_block = f"{begin_marker}\n{content.rstrip()}\n{end_marker}\n"

        if file_path.is_file():
            existing = file_path.read_text(encoding="utf-8")

            if begin_marker in existing and end_marker in existing:
                before = existing[: existing.index(begin_marker)]
                after = existing[existing.index(end_marker) + len(end_marker) :]
                after = after.lstrip("\n")
                new_content = before.rstrip("\n") + "\n\n" + section_block
                if after.strip():
                    new_content += "\n" + after
            else:
                new_content = existing.rstrip("\n") + "\n\n" + section_block
        else:
            new_content = section_block

        file_path.write_text(new_content, encoding="utf-8")
        logger.debug(f"Upserted section '{name}' ({kind}) in {file_path}")

    def _remove_marker_section(
        self,
        file_path: Path,
        name: str,
        kind: str,
    ) -> None:
        """Remove a marker-delimited section from a file.

        Args:
            file_path: Path to the target markdown file.
            name: Artifact name used in markers.
            kind: Artifact kind (``"instruction"``).
        """
        if not file_path.is_file():
            return

        begin_marker = BEGIN_MARKER_TEMPLATE.format(name=name, kind=kind)
        end_marker = END_MARKER_TEMPLATE.format(name=name, kind=kind)

        existing = file_path.read_text(encoding="utf-8")

        if begin_marker not in existing or end_marker not in existing:
            return

        before = existing[: existing.index(begin_marker)]
        after = existing[existing.index(end_marker) + len(end_marker) :]

        new_content = (before.rstrip("\n") + "\n" + after.lstrip("\n")).strip()

        if new_content:
            file_path.write_text(new_content + "\n", encoding="utf-8")
        else:
            file_path.unlink()
            logger.info(f"Removed empty file: {file_path}")

        logger.info(f"Removed section '{name}' ({kind}) from {file_path}")

    def _list_marker_sections(
        self,
        file_path: Path,
    ) -> list[tuple[str, str, Path]]:
        """Parse marker-delimited sections from a file.

        Returns:
            List of ``(name, type, path)`` tuples for each AAM section found.
        """
        content = file_path.read_text(encoding="utf-8")
        results: list[tuple[str, str, Path]] = []

        pattern = re.compile(r"<!-- BEGIN AAM: (.+?) (instruction|rule) -->")
        for match in pattern.finditer(content):
            name = match.group(1)
            kind = match.group(2)
            results.append((name, kind, file_path))

        return results

    # ------------------------------------------------------------------
    # Hook / MCP JSON helpers
    # ------------------------------------------------------------------

    def _remove_hook_entries(self, package_name: str) -> None:
        """Remove AAM-namespaced hook entries from ``.claude/hooks.json``.

        Args:
            package_name: Package name to match against ``_aam_package``.
        """
        hooks_path = self.claude_dir / "hooks.json"
        if not hooks_path.is_file():
            return

        data: dict[str, Any] = json.loads(
            hooks_path.read_text(encoding="utf-8")
        )
        removed = 0
        for event_key in list(data.keys()):
            entries = data[event_key]
            if isinstance(entries, list):
                filtered = [
                    e for e in entries
                    if not (isinstance(e, dict) and e.get("_aam_package") == package_name)
                ]
                removed += len(entries) - len(filtered)
                data[event_key] = filtered

        hooks_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        logger.info(f"Removed {removed} hook entries for '{package_name}' from {hooks_path}")

    def _remove_mcp_entries(self, package_name: str) -> None:
        """Remove AAM-namespaced MCP entries from ``.mcp.json``.

        Args:
            package_name: Package name used for namespace prefix matching.
        """
        mcp_path = self.project_root / ".mcp.json"
        if not mcp_path.is_file():
            return

        data: dict[str, Any] = json.loads(
            mcp_path.read_text(encoding="utf-8")
        )
        servers = data.get("mcpServers", {})
        safe_pkg = package_name.replace("@", "").replace("/", "-")
        keys_to_remove = [
            k for k in servers if k.startswith(f"{safe_pkg}:")
        ]
        for key in keys_to_remove:
            del servers[key]

        mcp_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        logger.info(f"Removed {len(keys_to_remove)} MCP entries for '{package_name}' from {mcp_path}")

    def _list_hook_entries(
        self, hooks_path: Path,
    ) -> list[tuple[str, str, Path]]:
        """List AAM-tagged hook entries.

        Args:
            hooks_path: Path to hooks JSON file.

        Returns:
            List of ``(event_name, "hook", path)`` tuples.
        """
        data: dict[str, Any] = json.loads(
            hooks_path.read_text(encoding="utf-8")
        )
        results: list[tuple[str, str, Path]] = []
        for event_key, entries in data.items():
            if isinstance(entries, list):
                for entry in entries:
                    if isinstance(entry, dict) and "_aam_package" in entry:
                        results.append((event_key, "hook", hooks_path))
                        break
        return results

    def _list_mcp_entries(
        self, mcp_path: Path,
    ) -> list[tuple[str, str, Path]]:
        """List AAM-namespaced MCP server entries.

        Args:
            mcp_path: Path to MCP JSON file.

        Returns:
            List of ``(server_key, "mcp", path)`` tuples.
        """
        data: dict[str, Any] = json.loads(
            mcp_path.read_text(encoding="utf-8")
        )
        results: list[tuple[str, str, Path]] = []
        servers = data.get("mcpServers", {})
        for key in servers:
            if ":" in key:
                results.append((key, "mcp", mcp_path))
        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _has_variables(self, cmd_path: Path) -> bool:
        """Check if a command file has variables in its frontmatter."""
        from aam_cli.converters.frontmatter import parse_frontmatter

        content = cmd_path.read_text(encoding="utf-8")
        fm, _ = parse_frontmatter(content)
        return bool(fm.get("variables"))

    def _artifact_fs_name(self, artifact_name: str) -> str:
        """Convert an artifact name to a filesystem-safe name.

        If the name looks like a scoped package ref (``@scope/name``),
        convert to ``scope--name``. Otherwise, return as-is.
        """
        if artifact_name.startswith("@") and "/" in artifact_name:
            scope, base = parse_package_name(artifact_name)
            return to_filesystem_name(scope, base)
        return artifact_name

    def _read_agent_content(self, agent_path: Path, agent_ref: ArtifactRef) -> str:
        """Read agent content for the agent file.

        Reads the system-prompt.md file from the agent directory.

        Args:
            agent_path: Path to the extracted agent directory.
            agent_ref: Artifact reference from the manifest.

        Returns:
            Markdown content string.
        """
        system_prompt_path = agent_path / "system-prompt.md"
        if system_prompt_path.is_file():
            return system_prompt_path.read_text(encoding="utf-8")

        agent_yaml_path = agent_path / "agent.yaml"
        if agent_yaml_path.is_file():
            from aam_cli.utils.yaml_utils import load_yaml

            agent_data = load_yaml(agent_yaml_path)
            prompt_file: str = agent_data.get("system_prompt", "system-prompt.md")
            alt_path = agent_path / prompt_file
            if alt_path.is_file():
                return alt_path.read_text(encoding="utf-8")

        logger.warning(
            f"No system prompt found for agent '{agent_ref.name}' at {agent_path}"
        )
        return f"# {agent_ref.name}\n\n{agent_ref.description}\n"
