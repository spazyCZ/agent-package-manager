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

# Lock file name (legacy)
LOCK_FILE_NAME: str = "aam-lock.yaml"

# Packages directory within workspace (legacy)
PACKAGES_DIR_NAME: str = "packages"

# UAAPS v0.4.0 manifest file names (in precedence order)
MANIFEST_JSON: str = "package.agent.json"
MANIFEST_YAML: str = "package.agent.yaml"
MANIFEST_LEGACY: str = "aam.yaml"

# UAAPS v0.4.0 packages directory (replaces .aam/packages/)
PACKAGES_DIR_NAME_V2: str = ".agent-packages"

# UAAPS v0.4.0 lock file (replaces aam-lock.yaml)
LOCK_FILE_JSON: str = "package.agent.lock"

# Sources registry directory name (auto-created by `aam source update`)
SOURCES_REGISTRY_DIR_NAME: str = "sources-registry"

# Global lock file name (UAAPS v0.5.0)
GLOBAL_LOCK_FILE: str = "global.lock"

################################################################################
#                                                                              #
# FUNCTIONS                                                                    #
#                                                                              #
################################################################################


def resolve_project_dir(is_global: bool = False) -> Path:
    """Return the effective project directory for workspace operations.

    When ``is_global`` is True, returns ``Path.home()`` so global installs
    operate from the user's home directory.

    Args:
        is_global: If True, use the user's home directory.

    Returns:
        Effective project root directory.
    """
    if is_global:
        home = Path.home()
        logger.debug(f"Global mode: project_dir resolved to '{home}'")
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


def get_universal_lock_file_path(project_dir: Path | None = None) -> Path:
    """Return the UAAPS v0.4.0 lock file path (``package.agent.lock``).

    The lock file lives at the project root alongside ``package.agent.json``,
    not inside ``.aam/`` or ``.agent-packages/``.

    Args:
        project_dir: Project root directory.

    Returns:
        Absolute path to the universal lock file.
    """
    root = (project_dir or Path.cwd()).resolve()
    return root / LOCK_FILE_JSON


def resolve_lock_path(is_global: bool = False, project_dir: Path | None = None) -> Path:
    """Return the appropriate lock file path for local or global installs.

    For global installs, returns ``~/.aam/global.lock``.
    For local installs, returns ``<project>/package.agent.lock``.

    Args:
        is_global: If True, return the global lock file path.
        project_dir: Project root directory (ignored when ``is_global`` is True).

    Returns:
        Absolute path to the lock file.
    """
    if is_global:
        global_dir = Path.home() / GLOBAL_AAM_DIR_NAME
        global_dir.mkdir(parents=True, exist_ok=True)
        lock_path = global_dir / GLOBAL_LOCK_FILE
        logger.debug(f"Global lock path: '{lock_path}'")
        return lock_path

    root = (project_dir or Path.cwd()).resolve()
    lock_path = root / LOCK_FILE_JSON
    logger.debug(f"Local lock path: '{lock_path}'")
    return lock_path


def get_packages_dir(project_dir: Path | None = None) -> Path:
    """Return the installed packages directory (``.agent-packages/``).

    Updated in UAAPS v0.4.0 to use ``.agent-packages/`` at the project root
    instead of ``.aam/packages/``.

    Args:
        project_dir: Project root directory.

    Returns:
        Absolute path to the packages directory.
    """
    root = (project_dir or Path.cwd()).resolve()
    return root / PACKAGES_DIR_NAME_V2


def get_legacy_packages_dir(project_dir: Path | None = None) -> Path:
    """Return the legacy packages directory (``.aam/packages/``).

    Used for migration detection — checks if the old directory layout exists.

    Args:
        project_dir: Project root directory.

    Returns:
        Absolute path to the legacy packages directory.
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
