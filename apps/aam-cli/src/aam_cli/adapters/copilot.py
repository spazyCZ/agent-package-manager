"""GitHub Copilot platform adapter.

Deploys AAM artifacts into the GitHub Copilot filesystem structure:
  - Skills       → ``.github/skills/<fs-name>/``
  - Agents       → ``.github/copilot-instructions.md`` (marker-delimited section)
  - Prompts      → ``.github/prompts/<fs-name>.md``
  - Instructions → ``.github/copilot-instructions.md`` (marker-delimited section)

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
# CONSTANTS                                                                    #
#                                                                              #
################################################################################

# Marker templates used to delimit AAM-managed sections inside shared files.
# Copilot agents and instructions are merged into copilot-instructions.md.
BEGIN_MARKER_TEMPLATE: str = "<!-- BEGIN AAM: {name} {kind} -->"
END_MARKER_TEMPLATE: str = "<!-- END AAM: {name} {kind} -->"

################################################################################
#                                                                              #
# COPILOT ADAPTER                                                              #
#                                                                              #
################################################################################


class CopilotAdapter:
    """GitHub Copilot platform adapter.

    All deploy methods write to a ``.github/`` directory within the
    project root, except agents and instructions which are appended
    to ``.github/copilot-instructions.md`` using HTML comment markers.
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
        """Deploy an agent section into ``.github/copilot-instructions.md``.

        Reads the agent's system-prompt.md (or agent.yaml → system_prompt
        reference) and appends it as a marker-delimited section.

        Args:
            agent_path: Path to the extracted agent directory.
            agent_ref: Artifact reference from the manifest.
            _config: Platform config.

        Returns:
            Path to the copilot-instructions.md file.
        """
        logger.info(f"Deploying agent '{agent_ref.name}' -> copilot-instructions.md")

        # -----
        # Read the system prompt content
        # -----
        content = self._read_agent_content(agent_path, agent_ref)

        # -----
        # Merge into copilot-instructions.md
        # -----
        instructions_path = self.github_dir / "copilot-instructions.md"
        self._upsert_marker_section(instructions_path, agent_ref.name, "agent", content)

        logger.info(f"Agent deployed to: {instructions_path}")
        return instructions_path

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
        """Deploy an instruction section into ``.github/copilot-instructions.md``.

        Reads the instruction markdown and appends it as a marker-delimited
        section alongside any agents already present.

        Args:
            instr_path: Path to the instruction file.
            instr_ref: Artifact reference from the manifest.
            _config: Platform config.

        Returns:
            Path to the copilot-instructions.md file.
        """
        logger.info(
            f"Deploying instruction '{instr_ref.name}' -> copilot-instructions.md"
        )

        content = instr_path.read_text(encoding="utf-8")

        instructions_path = self.github_dir / "copilot-instructions.md"
        self._upsert_marker_section(
            instructions_path, instr_ref.name, "instruction", content
        )

        logger.info(f"Instruction deployed to: {instructions_path}")
        return instructions_path

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

        elif artifact_type in ("agent", "instruction"):
            # Remove marker-delimited section from copilot-instructions.md
            instructions_path = self.github_dir / "copilot-instructions.md"
            self._remove_marker_section(instructions_path, artifact_name, artifact_type)

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

        # Prompts
        prompts_dir = self.github_dir / "prompts"
        if prompts_dir.is_dir():
            for entry in prompts_dir.iterdir():
                if entry.suffix == ".md":
                    deployed.append((entry.stem, "prompt", entry))

        # Agents and instructions from copilot-instructions.md markers
        instructions_path = self.github_dir / "copilot-instructions.md"
        if instructions_path.is_file():
            deployed.extend(self._list_marker_sections(instructions_path))

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

            # -----
            # Check if a section for this artifact already exists
            # -----
            if begin_marker in existing and end_marker in existing:
                # Replace existing section
                before = existing[: existing.index(begin_marker)]
                after = existing[existing.index(end_marker) + len(end_marker) :]
                # Strip leading newline from the remainder
                after = after.lstrip("\n")
                new_content = before.rstrip("\n") + "\n\n" + section_block
                if after.strip():
                    new_content += "\n" + after
            else:
                # Append new section
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

        import re

        pattern = re.compile(r"<!-- BEGIN AAM: (.+?) (agent|instruction) -->")
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
        """Read agent content for embedding in copilot-instructions.md.

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
