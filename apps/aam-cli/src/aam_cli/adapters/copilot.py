"""GitHub Copilot platform adapter.

Deploys AAM artifacts into the GitHub Copilot filesystem structure:
  - Skills       → ``.github/skills/<fs-name>/``
  - Agents       → ``.github/agents/<fs-name>.agent.md``
  - Prompts      → ``.github/prompts/<fs-name>.md``
  - Instructions → ``.github/instructions/<fs-name>.instructions.md``

Decision reference: DESIGN.md Section 8.2.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
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
# COPILOT ADAPTER                                                              #
#                                                                              #
################################################################################


class CopilotAdapter:
    """GitHub Copilot platform adapter.

    Deploys artifacts to the ``.github/`` directory within the project root:
      - Skills to ``.github/skills/<name>/``
      - Agents to ``.github/agents/<name>.agent.md``
      - Prompts to ``.github/prompts/<name>.md``
      - Instructions to ``.github/instructions/<name>.instructions.md``
    """

    def __init__(self, project_root: Path) -> None:
        """Initialize the Copilot adapter.

        Args:
            project_root: Root directory of the user's project.
        """
        self.name = "copilot"
        self.project_root = project_root.resolve()
        self.github_dir = self.project_root / ".github"

    # ------------------------------------------------------------------
    # Deploy methods
    # ------------------------------------------------------------------

    def deploy_skill(
        self,
        skill_path: Path,
        skill_ref: ArtifactRef,
        _config: dict[str, str],
    ) -> Path:
        """Deploy a skill to ``.github/skills/<fs-name>/``.

        Copies the entire skill directory (including SKILL.md).

        Args:
            skill_path: Path to the extracted skill directory.
            skill_ref: Artifact reference from the manifest.
            _config: Platform config (unused currently).

        Returns:
            Destination path.
        """
        fs_name = self._artifact_fs_name(skill_ref.name)
        dest = self.github_dir / "skills" / fs_name

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
        """Deploy an agent to ``.github/agents/<fs-name>.agent.md``.

        Reads the agent's system-prompt.md (or agent.yaml → system_prompt
        reference) and writes it as a discrete ``.agent.md`` file.

        Args:
            agent_path: Path to the extracted agent directory.
            agent_ref: Artifact reference from the manifest.
            _config: Platform config.

        Returns:
            Path to the created agent file.
        """
        fs_name = self._artifact_fs_name(agent_ref.name)
        dest = self.github_dir / "agents" / f"{fs_name}.agent.md"

        logger.info(f"Deploying agent '{agent_ref.name}' -> {dest}")

        # -----
        # Read the system prompt content
        # -----
        content = self._read_agent_content(agent_path, agent_ref)

        # -----
        # Write discrete agent file
        # -----
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")

        logger.info(f"Agent deployed: {dest}")
        return dest

    def deploy_prompt(
        self,
        prompt_path: Path,
        prompt_ref: ArtifactRef,
        _config: dict[str, str],
    ) -> Path:
        """Deploy a prompt to ``.github/prompts/<fs-name>.md``.

        Args:
            prompt_path: Path to the prompt file.
            prompt_ref: Artifact reference from the manifest.
            _config: Platform config.

        Returns:
            Destination path.
        """
        fs_name = self._artifact_fs_name(prompt_ref.name)
        dest = self.github_dir / "prompts" / f"{fs_name}.md"

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
        """Deploy an instruction to ``.github/instructions/<fs-name>.instructions.md``.

        Copies the instruction markdown as a discrete ``.instructions.md`` file
        in the ``.github/instructions/`` directory.

        Args:
            instr_path: Path to the instruction file.
            instr_ref: Artifact reference from the manifest.
            _config: Platform config.

        Returns:
            Path to the created instruction file.
        """
        fs_name = self._artifact_fs_name(instr_ref.name)
        dest = self.github_dir / "instructions" / f"{fs_name}.instructions.md"

        logger.info(f"Deploying instruction '{instr_ref.name}' -> {dest}")

        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(instr_path, dest)

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

        logger.info(f"Undeploying {artifact_type} '{artifact_name}' from copilot")

        if artifact_type == "skill":
            path = self.github_dir / "skills" / fs_name
            if path.is_dir():
                shutil.rmtree(path)
                logger.info(f"Removed skill directory: {path}")

        elif artifact_type == "agent":
            path = self.github_dir / "agents" / f"{fs_name}.agent.md"
            if path.is_file():
                path.unlink()
                logger.info(f"Removed agent file: {path}")

        elif artifact_type == "instruction":
            path = self.github_dir / "instructions" / f"{fs_name}.instructions.md"
            if path.is_file():
                path.unlink()
                logger.info(f"Removed instruction file: {path}")

        elif artifact_type == "prompt":
            path = self.github_dir / "prompts" / f"{fs_name}.md"
            if path.is_file():
                path.unlink()
                logger.info(f"Removed prompt: {path}")

    def list_deployed(self) -> list[tuple[str, str, Path]]:
        """List all deployed artifacts.

        Returns:
            List of ``(name, type, path)`` tuples.
        """
        deployed: list[tuple[str, str, Path]] = []

        # Skills
        skills_dir = self.github_dir / "skills"
        if skills_dir.is_dir():
            for entry in skills_dir.iterdir():
                if entry.is_dir():
                    deployed.append((entry.name, "skill", entry))

        # Agents
        agents_dir = self.github_dir / "agents"
        if agents_dir.is_dir():
            for entry in agents_dir.iterdir():
                if entry.name.endswith(".agent.md"):
                    # Strip the .agent.md suffix to get the artifact name
                    name = entry.name.removesuffix(".agent.md")
                    deployed.append((name, "agent", entry))

        # Prompts
        prompts_dir = self.github_dir / "prompts"
        if prompts_dir.is_dir():
            for entry in prompts_dir.iterdir():
                if entry.suffix == ".md":
                    deployed.append((entry.stem, "prompt", entry))

        # Instructions
        instructions_dir = self.github_dir / "instructions"
        if instructions_dir.is_dir():
            for entry in instructions_dir.iterdir():
                if entry.name.endswith(".instructions.md"):
                    name = entry.name.removesuffix(".instructions.md")
                    deployed.append((name, "instruction", entry))

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

    def _read_agent_content(self, agent_path: Path, agent_ref: ArtifactRef) -> str:
        """Read agent content for the ``.agent.md`` file.

        Reads the system-prompt.md file from the agent directory.

        Args:
            agent_path: Path to the extracted agent directory.
            agent_ref: Artifact reference from the manifest.

        Returns:
            Markdown content string.
        """
        # -----
        # Try system-prompt.md first, then fall back to agent.yaml reference
        # -----
        system_prompt_path = agent_path / "system-prompt.md"
        if system_prompt_path.is_file():
            return system_prompt_path.read_text(encoding="utf-8")

        # Check agent.yaml for system_prompt path reference
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
