"""Platform Adapter Protocol — abstract interface for deployment targets.

All platform adapters (Cursor, Claude, Copilot, Codex) conform to this
Protocol so that the installer can deploy artifacts to any platform
through a unified API.  UAAPS v0.5.0 merged prompts into commands.

Contracts reference: cli-commands.md Section 9.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from pathlib import Path
from typing import Protocol, runtime_checkable

from aam_cli.core.manifest import ArtifactRef

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# PLATFORM ADAPTER PROTOCOL                                                    #
#                                                                              #
################################################################################


@runtime_checkable
class PlatformAdapter(Protocol):
    """Abstract platform adapter interface.

    Each platform adapter knows how to deploy AAM artifacts into the
    filesystem structure expected by a specific AI coding platform.
    """

    name: str

    def deploy_skill(
        self,
        skill_path: Path,
        skill_ref: ArtifactRef,
        config: dict[str, str],
    ) -> Path:
        """Deploy a skill artifact.

        Args:
            skill_path: Path to the extracted skill directory.
            skill_ref: Artifact reference from the manifest.
            config: Platform-specific configuration.

        Returns:
            Path where the skill was deployed.
        """
        ...

    def deploy_agent(
        self,
        agent_path: Path,
        agent_ref: ArtifactRef,
        config: dict[str, str],
    ) -> Path:
        """Deploy an agent artifact.

        Args:
            agent_path: Path to the extracted agent directory.
            agent_ref: Artifact reference from the manifest.
            config: Platform-specific configuration.

        Returns:
            Path where the agent was deployed.
        """
        ...

    def deploy_instruction(
        self,
        instr_path: Path,
        instr_ref: ArtifactRef,
        config: dict[str, str],
    ) -> Path:
        """Deploy an instruction artifact.

        Args:
            instr_path: Path to the extracted instruction file.
            instr_ref: Artifact reference from the manifest.
            config: Platform-specific configuration.

        Returns:
            Path where the instruction was deployed.
        """
        ...

    def deploy_command(
        self,
        cmd_path: Path,
        cmd_ref: ArtifactRef,
        config: dict[str, str],
    ) -> Path:
        """Deploy a slash-command artifact.

        Args:
            cmd_path: Path to the command markdown file.
            cmd_ref: Artifact reference from the manifest.
            config: Platform-specific configuration.

        Returns:
            Path where the command was deployed.
        """
        ...

    def deploy_rule(
        self,
        rule_path: Path,
        rule_ref: ArtifactRef,
        config: dict[str, str],
    ) -> Path:
        """Deploy a rule artifact.

        Args:
            rule_path: Path to the rule markdown file (may have frontmatter).
            rule_ref: Artifact reference from the manifest.
            config: Platform-specific configuration.

        Returns:
            Path where the rule was deployed.
        """
        ...

    def deploy_hook(
        self,
        hooks_json_path: Path,
        config: dict[str, str],
    ) -> Path:
        """Deploy lifecycle hooks from a hooks.json file.

        Args:
            hooks_json_path: Path to the package ``hooks/hooks.json`` file.
            config: Platform-specific configuration including ``package_name``.

        Returns:
            Path to the platform hooks config file written/updated.
        """
        ...

    def deploy_mcp(
        self,
        servers_json_path: Path,
        config: dict[str, str],
    ) -> Path:
        """Deploy MCP server configuration from a servers.json file.

        Args:
            servers_json_path: Path to the package ``mcp/servers.json`` file.
            config: Platform-specific configuration including ``package_name``.

        Returns:
            Path to the platform MCP config file written/updated.
        """
        ...

    def undeploy(self, artifact_name: str, artifact_type: str) -> None:
        """Remove a deployed artifact.

        Args:
            artifact_name: Name of the artifact to remove.
            artifact_type: Type of artifact (skill, agent, command, instruction).
        """
        ...

    def list_deployed(self) -> list[tuple[str, str, Path]]:
        """List all deployed artifacts.

        Returns:
            List of ``(name, type, path)`` tuples.
        """
        ...
