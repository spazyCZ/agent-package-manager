"""Path resolution helpers for AAM CLI.

Provides consistent resolution of global (``~/.aam/``), project (``.aam/``),
and platform-specific directories, plus ``file://`` URL parsing.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from pathlib import Path
from urllib.parse import urlparse

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

# Global AAM configuration directory
GLOBAL_AAM_DIR_NAME: str = ".aam"

# Project-level workspace directory
PROJECT_WORKSPACE_DIR_NAME: str = ".aam"

# Global config file name
GLOBAL_CONFIG_FILE: str = "config.yaml"

# Lock file name
LOCK_FILE_NAME: str = "aam-lock.yaml"

# Packages directory within workspace
PACKAGES_DIR_NAME: str = "packages"

# Sources registry directory name (auto-created by `aam source update`)
SOURCES_REGISTRY_DIR_NAME: str = "sources-registry"

################################################################################
#                                                                              #
# FUNCTIONS                                                                    #
#                                                                              #
################################################################################


def resolve_project_dir(is_global: bool = False) -> Path:
    """Return the effective project directory for workspace operations.

    When ``is_global`` is True, returns ``Path.home()`` so that all
    workspace paths (packages, lock file) resolve under ``~/.aam/``
    instead of the project-local ``.aam/`` directory.

    This mirrors npm's ``-g`` / ``--global`` flag behaviour: global
    installs live in the user's home directory and are available
    across all projects.

    Args:
        is_global: If True, use the global home directory.

    Returns:
        Effective project root directory.
    """
    if is_global:
        home = Path.home()
        logger.debug(f"Global mode: project_dir resolved to home='{home}'")
        return home

    cwd = Path.cwd()
    logger.debug(f"Local mode: project_dir resolved to cwd='{cwd}'")
    return cwd


def get_global_aam_dir() -> Path:
    """Return the global AAM directory (``~/.aam/``).

    Creates the directory if it does not exist.

    Returns:
        Absolute path to the global AAM directory.
    """
    global_dir = Path.home() / GLOBAL_AAM_DIR_NAME
    global_dir.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Global AAM directory: path='{global_dir}'")
    return global_dir


def get_global_config_path() -> Path:
    """Return the path to the global config file (``~/.aam/config.yaml``).

    Returns:
        Absolute path to the global config file (may not exist yet).
    """
    return get_global_aam_dir() / GLOBAL_CONFIG_FILE


def get_project_workspace(project_dir: Path | None = None) -> Path:
    """Return the project-level workspace directory (``.aam/``).

    Args:
        project_dir: Project root. Defaults to the current working directory.

    Returns:
        Absolute path to the project workspace directory.
    """
    root = (project_dir or Path.cwd()).resolve()
    workspace = root / PROJECT_WORKSPACE_DIR_NAME
    logger.debug(f"Project workspace: path='{workspace}'")
    return workspace


def get_project_config_path(project_dir: Path | None = None) -> Path:
    """Return the path to the project config (``<project>/.aam/config.yaml``).

    Args:
        project_dir: Project root directory.

    Returns:
        Absolute path to the project config file.
    """
    return get_project_workspace(project_dir) / GLOBAL_CONFIG_FILE


def get_lock_file_path(project_dir: Path | None = None) -> Path:
    """Return the lock file path (``.aam/aam-lock.yaml``).

    Args:
        project_dir: Project root directory.

    Returns:
        Absolute path to the lock file.
    """
    return get_project_workspace(project_dir) / LOCK_FILE_NAME


def get_packages_dir(project_dir: Path | None = None) -> Path:
    """Return the installed packages directory (``.aam/packages/``).

    Args:
        project_dir: Project root directory.

    Returns:
        Absolute path to the packages directory.
    """
    return get_project_workspace(project_dir) / PACKAGES_DIR_NAME


def ensure_project_workspace(project_dir: Path | None = None) -> Path:
    """Create the project workspace directory if it does not exist.

    Args:
        project_dir: Project root directory.

    Returns:
        Absolute path to the created/existing workspace directory.
    """
    workspace = get_project_workspace(project_dir)
    workspace.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Ensured project workspace exists: path='{workspace}'")
    return workspace


def get_sources_registry_dir() -> Path:
    """Return the sources registry directory (``~/.aam/sources-registry/``).

    This directory contains a local registry auto-populated by
    ``aam source update`` with packages materialized from git sources.

    Returns:
        Absolute path to the sources registry directory.
    """
    sources_dir = get_global_aam_dir() / SOURCES_REGISTRY_DIR_NAME
    logger.debug(f"Sources registry directory: path='{sources_dir}'")
    return sources_dir


def parse_file_url(url: str) -> Path:
    """Parse a ``file://`` URL into a local filesystem path.

    Args:
        url: URL string, e.g. ``"file:///home/user/my-packages"``.

    Returns:
        Resolved :class:`Path` object.

    Raises:
        ValueError: If the URL scheme is not ``file``.
    """
    parsed = urlparse(url)

    if parsed.scheme != "file":
        raise ValueError(f"Expected file:// URL, got '{parsed.scheme}://' in '{url}'")

    # -----
    # urlparse stores the path in parsed.path
    # On Unix, file:///home/user → path="/home/user"
    # -----
    local_path = Path(parsed.path).resolve()
    logger.debug(f"Parsed file URL: url='{url}', path='{local_path}'")
    return local_path


def to_file_url(path: Path) -> str:
    """Convert a local path to a ``file://`` URL.

    Args:
        path: Local filesystem path.

    Returns:
        A ``file://`` URL string.
    """
    resolved = path.resolve()
    return f"file://{resolved}"
