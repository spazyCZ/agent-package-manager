"""Client initialization service for ``aam init``.

Provides business logic for the interactive client setup flow:
platform detection, registry configuration, and default source
registration.

Reference: spec 004 User Story 1; data-model.md entity 7.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from dataclasses import dataclass, field
from pathlib import Path

from aam_cli.core.config import (
    AamConfig,
    load_config,
    save_global_config,
)

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# DATA MODELS                                                                  #
#                                                                              #
################################################################################


@dataclass
class ClientInitResult:
    """Result of ``aam init`` client setup.

    Attributes:
        platform: Selected AI platform (e.g., ``cursor``).
        registry_created: True if a local registry was created.
        registry_name: Name of created or added registry, if any.
        sources_added: Names of added community sources.
        config_path: Path to written config file.
        is_reconfigure: True if config already existed.
    """

    platform: str
    registry_created: bool
    registry_name: str | None
    sources_added: list[str] = field(default_factory=list)
    config_path: Path = Path("~/.aam/config.yaml")
    is_reconfigure: bool = False


################################################################################
#                                                                              #
# CONSTANTS                                                                    #
#                                                                              #
################################################################################

SUPPORTED_PLATFORMS: list[str] = ["cursor", "copilot", "claude", "codex"]

################################################################################
#                                                                              #
# PLATFORM DETECTION                                                           #
#                                                                              #
################################################################################


def detect_platform(project_dir: Path | None = None) -> str | None:
    """Detect the AI platform from project directory indicators.

    Checks for platform-specific directories and files:
      - ``.cursor/`` → cursor
      - ``.github/copilot/`` → copilot
      - ``CLAUDE.md`` → claude
      - ``.codex/`` → codex

    Args:
        project_dir: Project root to scan. Defaults to cwd.

    Returns:
        Detected platform name, or ``None`` if no indicators found.
    """
    root = project_dir or Path.cwd()
    logger.debug(f"Detecting platform: root='{root}'")

    if (root / ".cursor").is_dir():
        logger.info("Detected platform: cursor")
        return "cursor"

    if (root / ".github" / "copilot").is_dir():
        logger.info("Detected platform: copilot")
        return "copilot"

    if (root / "CLAUDE.md").is_file():
        logger.info("Detected platform: claude")
        return "claude"

    if (root / ".codex").is_dir():
        logger.info("Detected platform: codex")
        return "codex"

    logger.debug("No platform detected")
    return None


################################################################################
#                                                                              #
# SETUP FUNCTIONS                                                              #
#                                                                              #
################################################################################


def setup_default_sources() -> list[str]:
    """Register default community sources.

    Delegates to the existing ``register_default_sources()`` function.

    Returns:
        List of registered source names.
    """
    from aam_cli.services.source_service import register_default_sources

    logger.info("Setting up default sources")

    result = register_default_sources()
    return result.get("registered", [])


################################################################################
#                                                                              #
# ORCHESTRATOR                                                                 #
#                                                                              #
################################################################################


def orchestrate_init(
    platform: str,
    skip_sources: bool = False,
) -> ClientInitResult:
    """Coordinate the full client initialization flow.

    Saves the selected platform to global config and optionally
    registers default community sources.

    Args:
        platform: Selected AI platform.
        skip_sources: If True, do not register default sources.

    Returns:
        :class:`ClientInitResult` with summary of actions taken.
    """
    from aam_cli.utils.paths import get_global_aam_dir

    logger.info(f"Orchestrating client init: platform='{platform}'")

    config_path = get_global_aam_dir() / "config.yaml"
    is_reconfigure = config_path.exists()

    # -----
    # Step 1: Load or create config
    # -----
    config = load_config()

    # -----
    # Step 2: Set default platform
    # -----
    config.default_platform = platform

    # -----
    # Step 3: Save config
    # -----
    save_global_config(config)

    # -----
    # Step 4: Register default sources
    # -----
    sources_added: list[str] = []
    if not skip_sources:
        sources_added = setup_default_sources()

    result = ClientInitResult(
        platform=platform,
        registry_created=False,
        registry_name=None,
        sources_added=sources_added,
        config_path=config_path,
        is_reconfigure=is_reconfigure,
    )

    logger.info(
        f"Client init complete: platform='{platform}', "
        f"sources_added={len(sources_added)}, "
        f"is_reconfigure={is_reconfigure}"
    )

    return result
