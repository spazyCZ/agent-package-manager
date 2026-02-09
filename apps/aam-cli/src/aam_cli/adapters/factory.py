"""Platform adapter factory.

Creates the appropriate :class:`PlatformAdapter` implementation based
on the platform name string from configuration or CLI flags.

Supported platforms: ``cursor``, ``copilot``, ``claude``, ``codex``.
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

# All supported platform names
SUPPORTED_PLATFORMS: tuple[str, ...] = ("cursor", "copilot", "claude", "codex")

################################################################################
#                                                                              #
# FACTORY FUNCTION                                                             #
#                                                                              #
################################################################################


def create_adapter(platform_name: str, project_root: Path) -> PlatformAdapter:
    """Create a platform adapter instance for the given platform name.

    Args:
        platform_name: One of ``"cursor"``, ``"copilot"``, ``"claude"``,
            or ``"codex"``.
        project_root: Root directory of the user's project.

    Returns:
        A :class:`PlatformAdapter` implementation for the requested platform.

    Raises:
        ValueError: If the platform name is not supported.
    """
    logger.info(f"Creating adapter: platform='{platform_name}', root='{project_root}'")

    if platform_name == "cursor":
        from aam_cli.adapters.cursor import CursorAdapter

        return CursorAdapter(project_root)

    if platform_name == "copilot":
        from aam_cli.adapters.copilot import CopilotAdapter

        return CopilotAdapter(project_root)

    if platform_name == "claude":
        from aam_cli.adapters.claude import ClaudeAdapter

        return ClaudeAdapter(project_root)

    if platform_name == "codex":
        from aam_cli.adapters.codex import CodexAdapter

        return CodexAdapter(project_root)

    raise ValueError(
        f"Unsupported platform '{platform_name}'. "
        f"Supported platforms: {', '.join(SUPPORTED_PLATFORMS)}"
    )


def is_supported_platform(platform_name: str) -> bool:
    """Check if a platform name is supported.

    Args:
        platform_name: Platform name to check.

    Returns:
        ``True`` if the platform is supported.
    """
    return platform_name in SUPPORTED_PLATFORMS
