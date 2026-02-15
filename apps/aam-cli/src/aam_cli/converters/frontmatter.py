"""YAML frontmatter parsing and generation utilities.

Handles reading and writing YAML frontmatter delimited by ``---`` markers
in markdown files, as used by Cursor (.mdc), Copilot (.instructions.md,
.agent.md, .prompt.md), and Claude/Cursor subagent files.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
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
# FRONTMATTER PARSING                                                          #
#                                                                              #
################################################################################


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter from a markdown/MDC string.

    Expects content in the form::

        ---
        key: value
        ---
        body content here

    Args:
        text: Full file content.

    Returns:
        Tuple of (frontmatter_dict, body_content). If no frontmatter
        is found, returns an empty dict and the original text.
    """
    stripped = text.lstrip("\n")
    if not stripped.startswith("---"):
        return {}, text

    # Find the closing ---
    end_idx = stripped.find("---", 3)
    if end_idx == -1:
        return {}, text

    yaml_block = stripped[3:end_idx].strip()
    body = stripped[end_idx + 3:].lstrip("\n")

    try:
        frontmatter = yaml.safe_load(yaml_block)
        if not isinstance(frontmatter, dict):
            frontmatter = {}
    except yaml.YAMLError:
        logger.warning("Failed to parse YAML frontmatter")
        return {}, text

    return frontmatter, body


def generate_frontmatter(metadata: dict[str, Any], body: str) -> str:
    """Generate a markdown string with YAML frontmatter.

    Args:
        metadata: Dictionary of frontmatter fields.
        body: Markdown body content.

    Returns:
        Combined string with ``---`` delimited frontmatter and body.
    """
    if not metadata:
        return body

    yaml_str = yaml.safe_dump(
        metadata, default_flow_style=False, sort_keys=False
    ).rstrip("\n")

    return f"---\n{yaml_str}\n---\n{body}"
