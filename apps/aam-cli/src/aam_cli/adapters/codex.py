"""Codex (OpenAI) platform adapter.

Deploys AAM artifacts into the OpenAI Codex filesystem structure:
  - Skills       → ``.agents/skills/<fs-name>/`` (project) or
                   ``~/.agents/skills/<fs-name>/`` (user)
  - Agents       → ``AGENTS.md`` (marker-delimited section)
  - Commands     → scoped skills root as ``<pkg>:<name>/``
  - Instructions → ``AGENTS.md`` (marker-delimited section)

Legacy ``~/.codex/skills/`` is still scanned on undeploy/list for cleanup.
Prompts remain under ``~/.codex/prompts/``.

UAAPS v0.5.0: prompts merged into commands.

Decision reference: DESIGN.md Section 8.4.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
import re
import shutil
from pathlib import Path

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

# Marker templates for AAM-managed sections inside AGENTS.md
BEGIN_MARKER_TEMPLATE: str = "<!-- BEGIN AAM: {name} {kind} -->"
END_MARKER_TEMPLATE: str = "<!-- END AAM: {name} {kind} -->"

################################################################################
#                                                                              #
# CODEX ADAPTER                                                                #
#                                                                              #
################################################################################


class CodexAdapter:
    """OpenAI Codex platform adapter.

    Skills and commands deploy to ``.agents/skills/`` (project scope) or
    ``~/.agents/skills/`` (user scope). Agents and instructions are merged
    into ``AGENTS.md`` at the project root using HTML comment markers.
    """

    def __init__(self, project_root: Path) -> None:
        """Initialize the Codex adapter.

        Args:
            project_root: Root directory of the user's project.
        """
        self.name = "codex"
        self.project_root = project_root.resolve()
        # Legacy Codex home (prompts still use this; skills may remain here)
        self.codex_dir = Path.home() / ".codex"
        self.agents_user_dir = Path.home() / ".agents"

    def _skills_base(self, config: dict[str, str]) -> Path:
        """Resolve the skills root from ``skill_scope``.

        Args:
            config: Deploy config; ``skill_scope`` is ``project`` or ``user``.

        Returns:
            Absolute path to the skills directory root.
        """
        scope = config.get("skill_scope", "project")
        if scope == "user":
            return self.agents_user_dir / "skills"
        return self.project_root / ".agents" / "skills"

    def _skill_search_roots(self) -> list[Path]:
        """Return skill roots to check for undeploy/list (incl. legacy).

        Returns:
            Ordered list of skill directory roots that may contain artifacts.
        """
        return [
            self.project_root / ".agents" / "skills",
            self.agents_user_dir / "skills",
            self.codex_dir / "skills",  # legacy
        ]

    # ------------------------------------------------------------------
    # Deploy methods
    # ------------------------------------------------------------------

    def deploy_skill(
        self,
        skill_path: Path,
        skill_ref: ArtifactRef,
        config: dict[str, str],
    ) -> Path:
        """Deploy a skill to ``.agents/skills/`` or ``~/.agents/skills/``.

        Copies the entire skill directory. Scope comes from
        ``config["skill_scope"]`` (default ``project``).

        Args:
            skill_path: Path to the extracted skill directory.
            skill_ref: Artifact reference from the manifest.
            config: Platform config including ``skill_scope``.

        Returns:
            Destination path.
        """
        fs_name = self._artifact_fs_name(skill_ref.name)
        dest = self._skills_base(config) / fs_name

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
        """Deploy an agent section into ``AGENTS.md``.

        Reads the agent's system-prompt.md and appends it as a
        marker-delimited section in the project-root ``AGENTS.md``.

        Args:
            agent_path: Path to the extracted agent directory.
            agent_ref: Artifact reference from the manifest.
            _config: Platform config.

        Returns:
            Path to AGENTS.md.
        """
        logger.info(f"Deploying agent '{agent_ref.name}' -> AGENTS.md")

        content = self._read_agent_content(agent_path, agent_ref)

        agents_md = self.project_root / "AGENTS.md"
        self._upsert_marker_section(agents_md, agent_ref.name, "agent", content)

        logger.info(f"Agent deployed to: {agents_md}")
        return agents_md

    def deploy_instruction(
        self,
        instr_path: Path,
        instr_ref: ArtifactRef,
        _config: dict[str, str],
    ) -> Path:
        """Deploy an instruction section into ``AGENTS.md``.

        Reads the instruction markdown and appends it as a
        marker-delimited section in the project-root ``AGENTS.md``.

        Args:
            instr_path: Path to the instruction file.
            instr_ref: Artifact reference from the manifest.
            _config: Platform config.

        Returns:
            Path to AGENTS.md.
        """
        logger.info(f"Deploying instruction '{instr_ref.name}' -> AGENTS.md")

        content = instr_path.read_text(encoding="utf-8")

        agents_md = self.project_root / "AGENTS.md"
        self._upsert_marker_section(agents_md, instr_ref.name, "instruction", content)

        logger.info(f"Instruction deployed to: {agents_md}")
        return agents_md

    def deploy_prompt(
        self,
        prompt_path: Path,
        prompt_ref: ArtifactRef,
        _config: dict[str, str],
    ) -> Path:
        """Deploy a prompt to ``~/.codex/prompts/<name>.md``.

        Args:
            prompt_path: Path to the prompt markdown file.
            prompt_ref: Artifact reference from the manifest.
            _config: Platform config (unused).

        Returns:
            Destination path.
        """
        fs_name = self._artifact_fs_name(prompt_ref.name)
        dest = self.codex_dir / "prompts" / f"{fs_name}.md"

        logger.info(f"Deploying prompt '{prompt_ref.name}' -> {dest}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(prompt_path, dest)

        logger.info(f"Prompt deployed: {dest}")
        return dest

    def deploy_command(
        self,
        cmd_path: Path,
        cmd_ref: ArtifactRef,
        config: dict[str, str],
    ) -> Path:
        """Deploy a slash-command as a Codex skill with ``disable-model-invocation``.

        Codex uses skills as its primary reusable context mechanism.
        Commands are stored under the scoped skills root as ``<pkg>:<name>/``.

        Args:
            cmd_path: Path to the command markdown file.
            cmd_ref: Artifact reference from the manifest.
            config: Platform config; ``package_name`` and ``skill_scope``.

        Returns:
            Destination skill directory path.
        """
        pkg_name = config.get("package_name", "unknown")
        safe_pkg = pkg_name.lstrip("@").replace("/", "--")
        safe_name = self._artifact_fs_name(cmd_ref.name)
        skill_dir = self._skills_base(config) / f"{safe_pkg}:{safe_name}"

        logger.info(f"Deploying command '{cmd_ref.name}' -> {skill_dir}")
        skill_dir.mkdir(parents=True, exist_ok=True)

        content = cmd_path.read_text(encoding="utf-8")
        frontmatter = (
            "---\n"
            f"description: \"{cmd_ref.description}\"\n"
            "disable-model-invocation: true\n"
            "---\n\n"
        )
        (skill_dir / "SKILL.md").write_text(frontmatter + content, encoding="utf-8")

        logger.info(f"Command deployed: {skill_dir}")
        return skill_dir

    def deploy_rule(
        self,
        rule_path: Path,
        rule_ref: ArtifactRef,
        _config: dict[str, str],
    ) -> Path:
        """Deploy a rule by appending it to ``AGENTS.md``.

        Rules for Codex are merged into ``AGENTS.md`` using marker-delimited
        sections (same mechanism as instructions).

        Args:
            rule_path: Path to the rule markdown file.
            rule_ref: Artifact reference from the manifest.
            _config: Platform config (unused).

        Returns:
            Path to AGENTS.md.
        """
        logger.info(f"Deploying rule '{rule_ref.name}' -> AGENTS.md")

        content = rule_path.read_text(encoding="utf-8")

        agents_md = self.project_root / "AGENTS.md"
        self._upsert_marker_section(agents_md, rule_ref.name, "rule", content)

        logger.info(f"Rule deployed to: {agents_md}")
        return agents_md

    def deploy_hook(
        self,
        hooks_json_path: Path,
        config: dict[str, str],
    ) -> Path:
        """Log a warning that Codex does not support lifecycle hooks.

        Codex has no hook mechanism.  This method always emits a warning and
        returns a sentinel path without writing any files.

        Args:
            hooks_json_path: Path to the package ``hooks/hooks.json``.
            config: Platform config (unused).

        Returns:
            The ``hooks_json_path`` unchanged (no file written).
        """
        pkg_name = config.get("package_name", "unknown")
        logger.warning(
            f"[{pkg_name}] Codex does not support lifecycle hooks. "
            f"Hook file '{hooks_json_path.name}' will not be deployed."
        )
        return hooks_json_path

    def deploy_mcp(
        self,
        servers_json_path: Path,
        config: dict[str, str],
    ) -> Path:
        """Log a warning that Codex has limited MCP support.

        Codex MCP support is limited.  This method logs a warning and
        returns a sentinel path without writing any files.

        Args:
            servers_json_path: Path to the package ``mcp/servers.json``.
            config: Platform config (unused).

        Returns:
            The ``servers_json_path`` unchanged (no file written).
        """
        pkg_name = config.get("package_name", "unknown")
        logger.warning(
            f"[{pkg_name}] Codex has limited MCP server support. "
            f"MCP config '{servers_json_path.name}' will not be automatically deployed. "
            "Configure MCP servers manually per Codex documentation."
        )
        return servers_json_path

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

        logger.info(f"Undeploying {artifact_type} '{artifact_name}' from codex")

        if artifact_type == "skill":
            # Check project, user, and legacy roots so old installs can be removed
            for skills_root in self._skill_search_roots():
                path = skills_root / fs_name
                if path.is_dir():
                    shutil.rmtree(path)
                    logger.info(f"Removed skill directory: {path}")

        elif artifact_type in ("agent", "instruction"):
            agents_md = self.project_root / "AGENTS.md"
            self._remove_marker_section(agents_md, artifact_name, artifact_type)

        elif artifact_type in ("prompt", "command"):
            for skills_root in self._skill_search_roots():
                path = skills_root / fs_name
                if path.is_dir():
                    shutil.rmtree(path)
                    logger.info(f"Removed command directory: {path}")
            prompt_path = self.codex_dir / "prompts" / f"{fs_name}.md"
            if prompt_path.is_file():
                prompt_path.unlink()
                logger.info(f"Removed command (legacy prompt): {prompt_path}")

        elif artifact_type == "rule":
            agents_md = self.project_root / "AGENTS.md"
            self._remove_marker_section(agents_md, artifact_name, "rule")

        elif artifact_type in ("hook", "mcp"):
            logger.warning(
                f"Codex does not support '{artifact_type}' artifacts — "
                f"skipping undeploy for '{artifact_name}'"
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
        seen_names: set[tuple[str, str]] = set()

        # -----
        # Skills and commands across project, user, and legacy roots
        # -----
        for skills_dir in self._skill_search_roots():
            if not skills_dir.is_dir():
                continue
            for entry in skills_dir.iterdir():
                if not entry.is_dir():
                    continue
                kind = "command" if ":" in entry.name else "skill"
                key = (entry.name, kind)
                if key in seen_names:
                    continue
                seen_names.add(key)
                deployed.append((entry.name, kind, entry))

        # -----
        # Commands (legacy prompts) from ~/.codex/prompts/
        # -----
        prompts_dir = self.codex_dir / "prompts"
        if prompts_dir.is_dir():
            for entry in prompts_dir.iterdir():
                if entry.suffix == ".md":
                    deployed.append((entry.stem, "command", entry))

        # -----
        # Agents, instructions, and rules from AGENTS.md markers
        # -----
        agents_md = self.project_root / "AGENTS.md"
        if agents_md.is_file():
            deployed.extend(self._list_marker_sections(agents_md))

        return deployed

    # ------------------------------------------------------------------
    # Marker-based section management
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
            kind: Artifact kind (``"agent"`` or ``"instruction"``).
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
            kind: Artifact kind (``"agent"`` or ``"instruction"``).
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

        pattern = re.compile(r"<!-- BEGIN AAM: (.+?) (agent|instruction|rule) -->")
        for match in pattern.finditer(content):
            name = match.group(1)
            kind = match.group(2)
            results.append((name, kind, file_path))

        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

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
        """Read agent content for embedding in AGENTS.md.

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
