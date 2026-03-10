"""Artifact auto-discovery for AAM packages.

When a package manifest does not declare an ``artifacts`` section,
this module scans the package directory using UAAPS v0.4.0 conventions
to find skills, agents, commands, and rules automatically.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from pathlib import Path

from aam_cli.core.manifest import ArtifactRef, ArtifactsDeclaration, PackageManifest

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# AUTO-DISCOVERY                                                               #
#                                                                              #
################################################################################


def discover_artifacts(
    package_dir: Path,
    manifest: PackageManifest,
) -> ArtifactsDeclaration:
    """Discover all artifacts for a package, using conventions when needed.

    If ``manifest.artifacts`` is not None, returns it as-is (explicit
    declaration takes precedence). Otherwise, scans ``package_dir``
    using the path overrides from the manifest (or UAAPS defaults):

    - ``manifest.skills_path`` (default ``./skills``) for ``*/SKILL.md``
    - ``manifest.agents_path`` (default ``./agents``) for structured agents
      (``*/agent.yaml`` present) and legacy single-file agents (``*.md``)
    - ``manifest.commands_path`` (default ``./commands``) for ``*.md``
    - ``manifest.rules_path`` (default ``./rules``) for ``*/RULE.md``
    - ``manifest.hooks_path`` (default ``./hooks/hooks.json``) presence check
    - ``manifest.mcp_path`` (default ``./mcp/servers.json``) presence check

    Backward compatibility: ``instructions`` entries from ``manifest.artifacts``
    are passed through as-is with a deprecation warning.

    Args:
        package_dir: Absolute path to the package root directory.
        manifest: Loaded package manifest.

    Returns:
        An :class:`ArtifactsDeclaration` containing all discovered artifacts.
    """
    # -----
    # If manifest explicitly declares artifacts, return them unchanged
    # -----
    if manifest.artifacts is not None:
        logger.debug(
            f"Using explicit artifacts from manifest for '{manifest.name}'"
        )
        _warn_instructions_deprecated(manifest)
        return manifest.artifacts

    logger.info(
        f"No artifacts section in manifest '{manifest.name}' — "
        f"running auto-discovery from '{package_dir}'"
    )

    skills: list[ArtifactRef] = _discover_skills(package_dir, manifest)
    agents: list[ArtifactRef] = _discover_agents(package_dir, manifest)
    commands: list[ArtifactRef] = _discover_commands(package_dir, manifest)
    rules: list[ArtifactRef] = _discover_rules(package_dir, manifest)
    hooks_path: str | None = _discover_hooks(package_dir, manifest)
    mcp_path: str | None = _discover_mcp(package_dir, manifest)

    logger.info(
        f"Auto-discovery complete for '{manifest.name}': "
        f"skills={len(skills)}, agents={len(agents)}, "
        f"commands={len(commands)}, rules={len(rules)}, "
        f"hooks={'yes' if hooks_path else 'no'}, "
        f"mcp={'yes' if mcp_path else 'no'}"
    )

    return ArtifactsDeclaration(
        skills=skills,
        agents=agents,
        commands=commands,
        rules=rules,
        hooks_path=hooks_path,
        mcp_path=mcp_path,
    )


################################################################################
#                                                                              #
# DISCOVERY HELPERS                                                            #
#                                                                              #
################################################################################


def _discover_skills(
    package_dir: Path,
    manifest: PackageManifest,
) -> list[ArtifactRef]:
    """Scan the skills directory for ``*/SKILL.md`` files.

    Args:
        package_dir: Package root directory.
        manifest: Package manifest with path overrides.

    Returns:
        List of skill :class:`ArtifactRef` instances.
    """
    skills_dir = _resolve_path(package_dir, manifest.skills_path)
    refs: list[ArtifactRef] = []

    if not skills_dir.is_dir():
        return refs

    for skill_file in skills_dir.glob("*/SKILL.md"):
        skill_name = skill_file.parent.name
        rel_path = skill_file.relative_to(package_dir)
        refs.append(
            ArtifactRef(
                name=skill_name,
                path=str(rel_path),
                description="",
            )
        )
        logger.debug(f"Discovered skill: name='{skill_name}', path='{rel_path}'")

    return refs


def _discover_agents(
    package_dir: Path,
    manifest: PackageManifest,
) -> list[ArtifactRef]:
    """Scan the agents directory for both structured and legacy agents.

    Structured agents: ``*/agent.yaml`` present. Description sourced
    from the YAML ``description`` field.

    Legacy agents: ``*.md`` at top level of agents directory.

    Args:
        package_dir: Package root directory.
        manifest: Package manifest with path overrides.

    Returns:
        List of agent :class:`ArtifactRef` instances.
    """
    agents_dir = _resolve_path(package_dir, manifest.agents_path)
    refs: list[ArtifactRef] = []

    if not agents_dir.is_dir():
        return refs

    # -----
    # Structured agents: subdirectory with agent.yaml
    # -----
    for agent_yaml in agents_dir.glob("*/agent.yaml"):
        agent_name = agent_yaml.parent.name
        rel_path = agent_yaml.relative_to(package_dir)

        # -----
        # Read description from agent.yaml if available
        # -----
        description: str | None = None
        try:
            from aam_cli.utils.yaml_utils import load_yaml

            yaml_data = load_yaml(agent_yaml)
            description = yaml_data.get("description")
        except Exception as exc:
            logger.debug(
                f"Could not read description from '{agent_yaml}': {exc}"
            )

        refs.append(
            ArtifactRef(
                name=agent_name,
                path=str(rel_path),
                description=description or "",
            )
        )
        logger.debug(
            f"Discovered structured agent: name='{agent_name}', "
            f"path='{rel_path}'"
        )

    # -----
    # Legacy single-file agents: *.md at the top level of agents_dir
    # -----
    discovered_names = {r.name for r in refs}
    for legacy_md in agents_dir.glob("*.md"):
        agent_name = legacy_md.stem
        if agent_name in discovered_names:
            continue  # Already discovered as structured agent
        rel_path = legacy_md.relative_to(package_dir)
        refs.append(
            ArtifactRef(
                name=agent_name,
                path=str(rel_path),
                description="",
            )
        )
        logger.debug(
            f"Discovered legacy agent: name='{agent_name}', "
            f"path='{rel_path}'"
        )

    return refs


def _discover_commands(
    package_dir: Path,
    manifest: PackageManifest,
) -> list[ArtifactRef]:
    """Scan the commands directory for ``*.md`` files.

    Args:
        package_dir: Package root directory.
        manifest: Package manifest with path overrides.

    Returns:
        List of command :class:`ArtifactRef` instances.
    """
    commands_dir = _resolve_path(package_dir, manifest.commands_path)
    refs: list[ArtifactRef] = []

    if not commands_dir.is_dir():
        return refs

    for cmd_file in commands_dir.glob("*.md"):
        cmd_name = cmd_file.stem
        rel_path = cmd_file.relative_to(package_dir)
        refs.append(
            ArtifactRef(
                name=cmd_name,
                path=str(rel_path),
                description="",
            )
        )
        logger.debug(
            f"Discovered command: name='{cmd_name}', path='{rel_path}'"
        )

    return refs


def _discover_rules(
    package_dir: Path,
    manifest: PackageManifest,
) -> list[ArtifactRef]:
    """Scan the rules directory for ``*/RULE.md`` files.

    Args:
        package_dir: Package root directory.
        manifest: Package manifest with path overrides.

    Returns:
        List of rule :class:`ArtifactRef` instances.
    """
    rules_dir = _resolve_path(package_dir, manifest.rules_path)
    refs: list[ArtifactRef] = []

    if not rules_dir.is_dir():
        return refs

    for rule_file in rules_dir.glob("*/RULE.md"):
        rule_name = rule_file.parent.name
        rel_path = rule_file.relative_to(package_dir)
        refs.append(
            ArtifactRef(
                name=rule_name,
                path=str(rel_path),
                description="",
            )
        )
        logger.debug(
            f"Discovered rule: name='{rule_name}', path='{rel_path}'"
        )

    return refs


def _discover_hooks(
    package_dir: Path,
    manifest: PackageManifest,
) -> str | None:
    """Check whether ``hooks/hooks.json`` exists.

    Args:
        package_dir: Package root directory.
        manifest: Package manifest with hooks path override.

    Returns:
        Relative path string if the hooks file exists, else None.
    """
    hooks_file = _resolve_path(package_dir, manifest.hooks_path)
    if hooks_file.is_file():
        rel = hooks_file.relative_to(package_dir)
        logger.debug(f"Discovered hooks config: path='{rel}'")
        return str(rel)
    return None


def _discover_mcp(
    package_dir: Path,
    manifest: PackageManifest,
) -> str | None:
    """Check whether ``mcp/servers.json`` exists.

    Args:
        package_dir: Package root directory.
        manifest: Package manifest with MCP path override.

    Returns:
        Relative path string if the MCP servers file exists, else None.
    """
    mcp_file = _resolve_path(package_dir, manifest.mcp_path)
    if mcp_file.is_file():
        rel = mcp_file.relative_to(package_dir)
        logger.debug(f"Discovered MCP config: path='{rel}'")
        return str(rel)
    return None


def _resolve_path(package_dir: Path, path_str: str) -> Path:
    """Resolve a potentially relative path against the package directory.

    Args:
        package_dir: Package root directory.
        path_str: Path string (may start with ``./``).

    Returns:
        Resolved absolute :class:`Path`.
    """
    if path_str.startswith("./"):
        path_str = path_str[2:]
    return package_dir / path_str


def _warn_instructions_deprecated(manifest: PackageManifest) -> None:
    """Log a deprecation warning if the manifest uses ``instructions`` type.

    Args:
        manifest: Package manifest to check.
    """
    from aam_cli.utils.deprecation import log_deprecation

    if manifest.artifacts and manifest.artifacts.instructions:
        log_deprecation(
            feature="artifacts.instructions",
            replacement="artifacts.rules",
            package_name=manifest.name,
        )
