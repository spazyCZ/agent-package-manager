"""Platform adapter factory.

Creates the appropriate :class:`PlatformAdapter` implementation based
on the platform name string from configuration or CLI flags.

Supported platforms: ``cursor``, ``copilot``, ``claude-code``, ``codex``.

Legacy alias ``claude`` is accepted and maps to ``claude-code``.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from pathlib import Path

from aam_cli.adapters.base import PlatformAdapter

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

# Canonical platform identifiers (UAAPS v0.6.0)
SUPPORTED_PLATFORMS: tuple[str, ...] = ("cursor", "copilot", "claude-code", "codex")

# Legacy aliases accepted for backward compatibility
PLATFORM_ALIASES: dict[str, str] = {
    "claude": "claude-code",
}

################################################################################
#                                                                              #
# HELPERS                                                                      #
#                                                                              #
################################################################################


def normalize_platform(platform_name: str) -> str:
    """Resolve legacy aliases to canonical platform identifiers.

    Args:
        platform_name: Platform name (may be a legacy alias).

    Returns:
        Canonical platform identifier.
    """
    return PLATFORM_ALIASES.get(platform_name, platform_name)


################################################################################
#                                                                              #
# FACTORY FUNCTION                                                             #
#                                                                              #
################################################################################


def create_adapter(platform_name: str, project_root: Path) -> PlatformAdapter:
    """Create a platform adapter instance for the given platform name.

    Accepts both canonical identifiers (``"claude-code"``) and legacy
    aliases (``"claude"``).

    Args:
        platform_name: One of ``"cursor"``, ``"copilot"``, ``"claude-code"``,
            or ``"codex"`` (legacy ``"claude"`` also accepted).
        project_root: Root directory of the user's project.

    Returns:
        A :class:`PlatformAdapter` implementation for the requested platform.

    Raises:
        ValueError: If the platform name is not supported.
    """
    canonical = normalize_platform(platform_name)
    logger.info(
        f"Creating adapter: platform='{canonical}'"
        f"{f' (alias from {platform_name!r})' if canonical != platform_name else ''}"
        f", root='{project_root}'"
    )

    if canonical == "cursor":
        from aam_cli.adapters.cursor import CursorAdapter

        return CursorAdapter(project_root)

    if canonical == "copilot":
        from aam_cli.adapters.copilot import CopilotAdapter

        return CopilotAdapter(project_root)

    if canonical == "claude-code":
        from aam_cli.adapters.claude import ClaudeAdapter

        return ClaudeAdapter(project_root)

    if canonical == "codex":
        from aam_cli.adapters.codex import CodexAdapter

        return CodexAdapter(project_root)

    raise ValueError(
        f"Unsupported platform '{platform_name}'. "
        f"Supported platforms: {', '.join(SUPPORTED_PLATFORMS)}"
    )


def is_supported_platform(platform_name: str) -> bool:
    """Check if a platform name is supported (including legacy aliases).

    Args:
        platform_name: Platform name to check.

    Returns:
        ``True`` if the platform is supported.
    """
    return normalize_platform(platform_name) in SUPPORTED_PLATFORMS
