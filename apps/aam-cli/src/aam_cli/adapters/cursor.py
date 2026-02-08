"""Cursor platform adapter.

Deploys AAM artifacts into the Cursor IDE filesystem structure:
  - Skills  → ``.cursor/skills/<fs-name>/``
  - Agents  → ``.cursor/rules/agent-<fs-name>.mdc``
  - Prompts → ``.cursor/prompts/<fs-name>.md``
  - Instructions → ``.cursor/rules/<fs-name>.mdc``

Decision reference: plan.md Key Decision 5, R-008.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
import shutil
from pathlib import Path

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

    def deploy_prompt(
        self,
        prompt_path: Path,
        prompt_ref: ArtifactRef,
        _config: dict[str, str],
    ) -> Path:
        """Deploy a prompt to ``.cursor/prompts/<fs-name>.md``.

        Args:
            prompt_path: Path to the prompt file.
            prompt_ref: Artifact reference from the manifest.
            config: Platform config.

        Returns:
            Destination path.
        """
        fs_name = self._artifact_fs_name(prompt_ref.name)
        dest = self.cursor_dir / "prompts" / f"{fs_name}.md"

        logger.info(f"Deploying prompt '{prompt_ref.name}' -> {dest}")
        dest.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(prompt_path, dest)

        logger.info(f"Prompt deployed: {dest}")
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

    # ------------------------------------------------------------------
    # Undeploy and list
    # ------------------------------------------------------------------

    def undeploy(self, artifact_name: str, artifact_type: str) -> None:
        """Remove a deployed artifact.

        Args:
            artifact_name: Name of the artifact.
            artifact_type: Type (skill, agent, prompt, instruction).
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

        elif artifact_type == "prompt":
            path = self.cursor_dir / "prompts" / f"{fs_name}.md"
            if path.is_file():
                path.unlink()
                logger.info(f"Removed prompt: {path}")

        elif artifact_type == "instruction":
            path = self.cursor_dir / "rules" / f"{fs_name}.mdc"
            if path.is_file():
                path.unlink()
                logger.info(f"Removed instruction rule: {path}")

    def list_deployed(self) -> list[tuple[str, str, Path]]:
        """List all deployed artifacts.

        Returns:
            List of ``(name, type, path)`` tuples.
        """
        deployed: list[tuple[str, str, Path]] = []

        # Skills
        skills_dir = self.cursor_dir / "skills"
        if skills_dir.is_dir():
            for entry in skills_dir.iterdir():
                if entry.is_dir():
                    deployed.append((entry.name, "skill", entry))

        # Rules (agents and instructions)
        rules_dir = self.cursor_dir / "rules"
        if rules_dir.is_dir():
            for entry in rules_dir.iterdir():
                if entry.suffix == ".mdc":
                    if entry.name.startswith("agent-"):
                        name = entry.stem.removeprefix("agent-")
                        deployed.append((name, "agent", entry))
                    else:
                        deployed.append((entry.stem, "instruction", entry))

        # Prompts
        prompts_dir = self.cursor_dir / "prompts"
        if prompts_dir.is_dir():
            for entry in prompts_dir.iterdir():
                if entry.suffix == ".md":
                    deployed.append((entry.stem, "prompt", entry))

        return deployed

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

        if agent_def.prompts:
            lines.append("## Available Prompts")
            lines.append("")
            for prompt in agent_def.prompts:
                lines.append(f"- {prompt}")
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
