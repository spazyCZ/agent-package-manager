"""Safe YAML loading and dumping utilities.

Wraps PyYAML's ``safe_load`` / ``safe_dump`` with consistent error handling
and file I/O.  All AAM modules that read or write YAML must go through these
helpers — never call ``yaml.load()`` directly.

Decision reference: R-001 in research.md.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from pathlib import Path
from typing import Any

import yaml

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# FUNCTIONS                                                                    #
#                                                                              #
################################################################################


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file and return its contents as a dictionary.

    Uses ``yaml.safe_load`` exclusively to prevent arbitrary code execution.

    Args:
        path: Absolute or relative path to the YAML file.

    Returns:
        Parsed YAML content as a dictionary.  Returns an empty dict if the
        file is empty.

    Raises:
        FileNotFoundError: If *path* does not exist.
        yaml.YAMLError: If the file contains invalid YAML.
    """
    logger.debug(f"Loading YAML file: path='{path}'")

    # -----
    # Step 1: Read file content
    # -----
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.error(f"YAML file not found: path='{path}'")
        raise

    # -----
    # Step 2: Parse YAML safely
    # -----
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        logger.error(f"Invalid YAML in '{path}': {exc}")
        raise

    # -----
    # Step 3: Handle empty files (safe_load returns None)
    # -----
    if data is None:
        logger.debug(f"YAML file is empty or null: path='{path}'")
        return {}

    if not isinstance(data, dict):
        logger.warning(
            f"YAML file does not contain a mapping: path='{path}', type={type(data).__name__}"
        )
        return {"_root": data}

    logger.debug(f"YAML loaded successfully: path='{path}', keys={list(data.keys())}")
    return data


def dump_yaml(data: dict[str, Any], path: Path) -> None:
    """Dump a dictionary to a YAML file.

    Uses ``yaml.safe_dump`` with sensible defaults for human-readable output.

    Args:
        data: Dictionary to serialize.
        path: Target file path (parent directories must exist).

    Raises:
        OSError: If the file cannot be written.
    """
    logger.debug(f"Dumping YAML to file: path='{path}'")

    # -----
    # Ensure parent directory exists
    # -----
    path.parent.mkdir(parents=True, exist_ok=True)

    # -----
    # Serialize and write
    # -----
    content = yaml.safe_dump(
        data,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )

    path.write_text(content, encoding="utf-8")
    logger.debug(f"YAML dumped successfully: path='{path}'")


def load_yaml_optional(path: Path) -> dict[str, Any]:
    """Load a YAML file, returning an empty dict if the file does not exist.

    Convenience wrapper around :func:`load_yaml` that silently handles
    missing files — useful for optional config files.

    Args:
        path: Path to the YAML file.

    Returns:
        Parsed content or empty dict.
    """
    if not path.exists():
        logger.debug(f"Optional YAML file not found (ok): path='{path}'")
        return {}
    return load_yaml(path)
