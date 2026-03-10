"""Cursor platform adapter.

Deploys AAM artifacts into the Cursor IDE filesystem structure:
  - Skills       → ``.cursor/skills/<fs-name>/``
  - Agents       → ``.cursor/rules/agent-<fs-name>.mdc``
  - Commands     → ``.cursor/skills/<pkg>:<name>/`` (simple) or
                   ``.cursor/prompts/<name>.md`` (parameterized/template)
  - Instructions → ``.cursor/rules/<fs-name>.mdc``

UAAPS v0.5.0: prompts merged into commands.

Decision reference: plan.md Key Decision 5, R-008.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import json
import logging
import shutil
from pathlib import Path
from typing import Any

from aam_cli.core.manifest import AgentDefinition, ArtifactRef
from aam_cli.utils.naming import parse_package_name, to_filesystem_name
from aam_cli.utils.yaml_utils import load_yaml

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# CURSOR ADAPTER                                                               #
#                                                                              #
################################################################################


class CursorAdapter:
    """Cursor IDE platform adapter.

    All deploy methods write to a ``.cursor/`` directory within
    the project root.
    """

    def __init__(self, project_root: Path) -> None:
        """Initialize the Cursor adapter.

        Args:
            project_root: Root directory of the user's project.
        """
        self.name = "cursor"
        self.project_root = project_root.resolve()
        self.cursor_dir = self.project_root / ".cursor"

    # ------------------------------------------------------------------
    # Deploy methods
    # ------------------------------------------------------------------

    def deploy_skill(
        self,
        skill_path: Path,
        skill_ref: ArtifactRef,
        _config: dict[str, str],
    ) -> Path:
        """Deploy a skill to ``.cursor/skills/<fs-name>/``.

        Copies the entire skill directory.

        Args:
            skill_path: Path to the extracted skill directory.
            skill_ref: Artifact reference from the manifest.
            config: Platform config (e.g. skill_scope).

        Returns:
            Destination path.
        """
        fs_name = self._artifact_fs_name(skill_ref.name)
        dest = self.cursor_dir / "skills" / fs_name

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
        """Deploy an agent as ``.cursor/rules/agent-<fs-name>.mdc``.

        Reads ``agent.yaml`` and ``system-prompt.md`` to generate a Cursor
        rule file with YAML frontmatter.

        Args:
            agent_path: Path to the extracted agent directory.
            agent_ref: Artifact reference from the manifest.
            config: Platform config.

        Returns:
            Destination path.
        """
        fs_name = self._artifact_fs_name(agent_ref.name)
        dest = self.cursor_dir / "rules" / f"agent-{fs_name}.mdc"

        logger.info(f"Deploying agent '{agent_ref.name}' -> {dest}")
        dest.parent.mkdir(parents=True, exist_ok=True)

        # -----
        # Read agent.yaml and system-prompt.md
        # -----
        agent_yaml_path = agent_path / "agent.yaml"
        system_prompt_path = agent_path / "system-prompt.md"

        if agent_yaml_path.is_file():
            agent_data = load_yaml(agent_yaml_path)
            agent_def = AgentDefinition(**agent_data)
        else:
            # Fallback: create minimal agent definition
            agent_def = AgentDefinition(
                name=agent_ref.name,
                description=agent_ref.description,
                system_prompt="system-prompt.md",
            )

        # -----
        # Read system prompt content
        # -----
        system_prompt = ""
        if system_prompt_path.is_file():
            system_prompt = system_prompt_path.read_text(encoding="utf-8")
        else:
            # Check if agent_def.system_prompt points to a different file
            alt_prompt = agent_path / agent_def.system_prompt
            if alt_prompt.is_file():
                system_prompt = alt_prompt.read_text(encoding="utf-8")

        # -----
        # Generate .mdc content
        # -----
        mdc_content = self._generate_agent_mdc(agent_def, system_prompt)
        dest.write_text(mdc_content, encoding="utf-8")

        logger.info(f"Agent deployed: {dest}")
        return dest

    def deploy_instruction(
        self,
        instr_path: Path,
        instr_ref: ArtifactRef,
        _config: dict[str, str],
    ) -> Path:
        """Deploy an instruction as ``.cursor/rules/<fs-name>.mdc``.

        Converts markdown to Cursor rule format with YAML frontmatter.

        Args:
            instr_path: Path to the instruction file.
            instr_ref: Artifact reference from the manifest.
            config: Platform config.

        Returns:
            Destination path.
        """
        fs_name = self._artifact_fs_name(instr_ref.name)
        dest = self.cursor_dir / "rules" / f"{fs_name}.mdc"

        logger.info(f"Deploying instruction '{instr_ref.name}' -> {dest}")
        dest.parent.mkdir(parents=True, exist_ok=True)

        # -----
        # Read instruction content
        # -----
        content = instr_path.read_text(encoding="utf-8")

        # -----
        # Generate .mdc with frontmatter
        # -----
        mdc_content = self._generate_instruction_mdc(instr_ref, content)
        dest.write_text(mdc_content, encoding="utf-8")

        logger.info(f"Instruction deployed: {dest}")
        return dest

    def deploy_command(
        self,
        cmd_path: Path,
        cmd_ref: ArtifactRef,
        config: dict[str, str],
    ) -> Path:
        """Deploy a command to Cursor.

        Simple commands are deployed as skills with ``disable-model-invocation: true``.
        Parameterized commands (templates with variables) go to ``.cursor/prompts/``.

        Args:
            cmd_path: Path to the command markdown file.
            cmd_ref: Artifact reference from the manifest.
            config: Platform config; ``package_name`` key used for namespacing.

        Returns:
            Destination path.
        """
        if self._has_variables(cmd_path):
            fs_name = self._artifact_fs_name(cmd_ref.name)
            dest = self.cursor_dir / "prompts" / f"{fs_name}.md"
            logger.info(f"Deploying parameterized command '{cmd_ref.name}' -> {dest}")
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(cmd_path, dest)
            logger.info(f"Command deployed: {dest}")
            return dest

        pkg_name = config.get("package_name", "unknown")
        safe_pkg = pkg_name.lstrip("@").replace("/", "--")
        safe_name = self._artifact_fs_name(cmd_ref.name)
        skill_dir = self.cursor_dir / "skills" / f"{safe_pkg}:{safe_name}"

        logger.info(f"Deploying command '{cmd_ref.name}' -> {skill_dir}")
        skill_dir.mkdir(parents=True, exist_ok=True)

        content = cmd_path.read_text(encoding="utf-8")
        frontmatter = (
            "---\n"
            f"description: \"{cmd_ref.description}\"\n"
            "disable-model-invocation: true\n"
            "---\n\n"
        )
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(frontmatter + content, encoding="utf-8")

        logger.info(f"Command deployed: {skill_dir}")
        return skill_dir

    def deploy_rule(
        self,
        rule_path: Path,
        rule_ref: ArtifactRef,
        _config: dict[str, str],
    ) -> Path:
        """Deploy a rule by converting it to a ``.cursor/rules/<name>.mdc`` file.

        Reads the rule markdown, strips any existing frontmatter, and writes
        a new ``.mdc`` file with Cursor-compatible frontmatter (``description``
        and ``alwaysApply``).

        Args:
            rule_path: Path to the rule markdown file.
            rule_ref: Artifact reference from the manifest.
            _config: Platform config (unused).

        Returns:
            Destination path.
        """
        from aam_cli.converters.frontmatter import parse_frontmatter

        fs_name = self._artifact_fs_name(rule_ref.name)
        dest = self.cursor_dir / "rules" / f"{fs_name}.mdc"

        logger.info(f"Deploying rule '{rule_ref.name}' -> {dest}")
        dest.parent.mkdir(parents=True, exist_ok=True)

        # -----
        # Read rule content and strip existing frontmatter if any
        # -----
        raw = rule_path.read_text(encoding="utf-8")
        _, body = parse_frontmatter(raw)
        mdc_content = self._generate_instruction_mdc(rule_ref, body)
        dest.write_text(mdc_content, encoding="utf-8")

        logger.info(f"Rule deployed: {dest}")
        return dest

    def deploy_hook(
        self,
        hooks_json_path: Path,
        config: dict[str, str],
    ) -> Path:
        """Merge lifecycle hooks into ``.cursor/hooks.json``.

        Translates canonical UAAPS hook event names to Cursor-specific names
        and merges into the platform hooks config.  Unsupported events are
        logged as warnings and skipped.

        Args:
            hooks_json_path: Path to the package ``hooks/hooks.json``.
            config: Platform config; ``package_name`` key for namespacing.

        Returns:
            Path to ``.cursor/hooks.json``.
        """
        from aam_cli.converters.mappings import translate_hook_event

        pkg_name = config.get("package_name", "unknown")
        dest = self.cursor_dir / "hooks.json"
        dest.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Merging hooks from '{hooks_json_path}' -> {dest}")

        source_hooks: dict[str, Any] = json.loads(hooks_json_path.read_text(encoding="utf-8"))

        existing: dict[str, Any] = {}
        if dest.is_file():
            existing = json.loads(dest.read_text(encoding="utf-8"))

        for canonical_event, hook_entries in source_hooks.items():
            platform_event = translate_hook_event(canonical_event, "cursor")
            if not platform_event:
                logger.warning(
                    f"Hook event '{canonical_event}' is not supported in Cursor — skipping"
                )
                continue

            if platform_event not in existing:
                existing[platform_event] = []

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
        """Write MCP server config to ``.cursor/mcp.json``.

        Reads a UAAPS ``mcp/servers.json`` and merges namespaced server entries
        into ``.cursor/mcp.json``.

        Args:
            servers_json_path: Path to the package ``mcp/servers.json``.
            config: Platform config; ``package_name`` key for namespacing.

        Returns:
            Path to ``.cursor/mcp.json``.
        """
        pkg_name = config.get("package_name", "unknown")
        safe_pkg = pkg_name.lstrip("@").replace("/", "--")
        dest = self.cursor_dir / "mcp.json"
        dest.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Merging MCP servers from '{servers_json_path}' -> {dest}")

        source: dict[str, Any] = json.loads(servers_json_path.read_text(encoding="utf-8"))
        servers: dict[str, Any] = source.get("mcpServers", source)

        existing: dict[str, Any] = {"mcpServers": {}}
        if dest.is_file():
            existing = json.loads(dest.read_text(encoding="utf-8"))
        existing.setdefault("mcpServers", {})

        for server_key, server_cfg in servers.items():
            namespaced_key = f"{safe_pkg}:{server_key}"
            existing["mcpServers"][namespaced_key] = server_cfg
            logger.debug(f"Added MCP server: {namespaced_key}")

        dest.write_text(json.dumps(existing, indent=2), encoding="utf-8")
        logger.info(f"MCP config written: {dest}")
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

        logger.info(f"Undeploying {artifact_type} '{artifact_name}' from cursor")

        if artifact_type == "skill":
            path = self.cursor_dir / "skills" / fs_name
            if path.is_dir():
                shutil.rmtree(path)
                logger.info(f"Removed skill directory: {path}")

        elif artifact_type == "agent":
            path = self.cursor_dir / "rules" / f"agent-{fs_name}.mdc"
            if path.is_file():
                path.unlink()
                logger.info(f"Removed agent rule: {path}")

        elif artifact_type == "instruction":
            path = self.cursor_dir / "rules" / f"{fs_name}.mdc"
            if path.is_file():
                path.unlink()
                logger.info(f"Removed instruction rule: {path}")

        elif artifact_type in ("prompt", "command"):
            prompt_path = self.cursor_dir / "prompts" / f"{fs_name}.md"
            if prompt_path.is_file():
                prompt_path.unlink()
                logger.info(f"Removed command (template): {prompt_path}")
            skill_path = self.cursor_dir / "skills" / fs_name
            if skill_path.is_dir():
                shutil.rmtree(skill_path)
                logger.info(f"Removed command directory: {skill_path}")

        elif artifact_type == "rule":
            path = self.cursor_dir / "rules" / f"{fs_name}.mdc"
            if path.is_file():
                path.unlink()
                logger.info(f"Removed rule: {path}")

        elif artifact_type == "hook":
            self._remove_json_entries(
                self.cursor_dir / "hooks.json", artifact_name
            )

        elif artifact_type == "mcp":
            self._remove_json_entries(
                self.cursor_dir / "mcp.json", artifact_name,
                container_key="mcpServers",
            )

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
        # Skills and commands (commands use ':' in directory name)
        # -----
        skills_dir = self.cursor_dir / "skills"
        if skills_dir.is_dir():
            for entry in skills_dir.iterdir():
                if entry.is_dir():
                    kind = "command" if ":" in entry.name else "skill"
                    deployed.append((entry.name, kind, entry))

        # -----
        # Rules (agents, instructions, and rules)
        # -----
        rules_dir = self.cursor_dir / "rules"
        if rules_dir.is_dir():
            for entry in rules_dir.iterdir():
                if entry.suffix == ".mdc":
                    if entry.name.startswith("agent-"):
                        name = entry.stem.removeprefix("agent-")
                        deployed.append((name, "agent", entry))
                    else:
                        deployed.append((entry.stem, "instruction", entry))

        # -----
        # Commands (templates) from prompts dir
        # -----
        prompts_dir = self.cursor_dir / "prompts"
        if prompts_dir.is_dir():
            for entry in prompts_dir.iterdir():
                if entry.suffix == ".md":
                    deployed.append((entry.stem, "command", entry))

        # -----
        # Hooks (AAM-namespaced entries in hooks.json)
        # -----
        hooks_path = self.cursor_dir / "hooks.json"
        deployed.extend(self._list_json_entries(hooks_path, "hook"))

        # -----
        # MCP (AAM-namespaced entries in mcp.json)
        # -----
        mcp_path = self.cursor_dir / "mcp.json"
        deployed.extend(
            self._list_json_entries(mcp_path, "mcp", container_key="mcpServers")
        )

        return deployed

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _remove_json_entries(
        self,
        json_path: Path,
        package_name: str,
        container_key: str | None = None,
    ) -> None:
        """Remove AAM-namespaced entries from a JSON config file.

        Entries whose key starts with ``<package_name>:`` or whose
        ``_aam_package`` field matches are removed.

        Args:
            json_path: Path to the JSON file.
            package_name: Package name used for namespace matching.
            container_key: Optional top-level key containing the entries.
        """
        if not json_path.is_file():
            return

        data: dict[str, Any] = json.loads(
            json_path.read_text(encoding="utf-8")
        )
        target = data.get(container_key, data) if container_key else data

        keys_to_remove: list[str] = []
        for key, value in target.items():
            if key.startswith(f"{package_name}:"):
                keys_to_remove.append(key)
            elif isinstance(value, list):
                # Filter list entries by _aam_package tag
                target[key] = [
                    e for e in value
                    if not (isinstance(e, dict) and e.get("_aam_package") == package_name)
                ]
                if not target[key]:
                    keys_to_remove.append(key)
            elif isinstance(value, dict) and value.get("_aam_package") == package_name:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del target[key]

        json_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        logger.info(
            f"Removed {len(keys_to_remove)} entries from {json_path} "
            f"for package '{package_name}'"
        )

    def _list_json_entries(
        self,
        json_path: Path,
        artifact_type: str,
        container_key: str | None = None,
    ) -> list[tuple[str, str, Path]]:
        """List AAM-namespaced entries in a JSON config file.

        Args:
            json_path: Path to the JSON file.
            artifact_type: Artifact type label for results.
            container_key: Optional top-level key containing the entries.

        Returns:
            List of ``(name, type, path)`` tuples.
        """
        if not json_path.is_file():
            return []

        data: dict[str, Any] = json.loads(
            json_path.read_text(encoding="utf-8")
        )
        target = data.get(container_key, data) if container_key else data
        results: list[tuple[str, str, Path]] = []

        for key, value in target.items():
            if isinstance(value, list):
                for entry in value:
                    if isinstance(entry, dict) and "_aam_package" in entry:
                        results.append((key, artifact_type, json_path))
                        break
            elif isinstance(value, dict) and "_aam_package" in value:
                results.append((key, artifact_type, json_path))

        return results

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

    def _generate_agent_mdc(
        self,
        agent_def: AgentDefinition,
        system_prompt: str,
    ) -> str:
        """Generate a Cursor ``.mdc`` rule file for an agent.

        Format per R-008:
          ---
          description: "..."
          alwaysApply: true
          ---
          # Agent: <name>
          <system prompt content>
          ## Available Skills
          ...
        """
        lines: list[str] = [
            "---",
            f'description: "{agent_def.description}"',
            "alwaysApply: true",
            "---",
            "",
            f"# Agent: {agent_def.name}",
            "",
        ]

        if system_prompt:
            lines.append(system_prompt.rstrip())
            lines.append("")

        if agent_def.skills:
            lines.append("## Available Skills")
            lines.append("")
            for skill in agent_def.skills:
                lines.append(f"- {skill}")
            lines.append("")

        if agent_def.commands:
            lines.append("## Available Commands")
            lines.append("")
            for cmd in agent_def.commands:
                lines.append(f"- {cmd}")
            lines.append("")

        return "\n".join(lines)

    def _generate_instruction_mdc(
        self,
        instr_ref: ArtifactRef,
        content: str,
    ) -> str:
        """Generate a Cursor ``.mdc`` rule file for an instruction.

        Format per R-008:
          ---
          description: "..."
          alwaysApply: true
          ---
          <instruction content>
        """
        lines: list[str] = [
            "---",
            f'description: "{instr_ref.description}"',
            "alwaysApply: true",
            "---",
            "",
            content.rstrip(),
            "",
        ]

        return "\n".join(lines)
