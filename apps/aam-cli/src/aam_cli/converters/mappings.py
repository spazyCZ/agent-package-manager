"""Platform-to-platform field mapping tables and conversion constants.

Defines which fields are supported per platform per artifact type,
and how fields map between platforms during conversion.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# PLATFORM IDENTIFIERS                                                         #
#                                                                              #
################################################################################

PLATFORMS = ("cursor", "copilot", "claude", "codex")

################################################################################
#                                                                              #
# INSTRUCTION FILE PATHS                                                       #
#                                                                              #
################################################################################

# Platform instruction file paths (source patterns for scanning)
INSTRUCTION_PATHS: dict[str, list[str]] = {
    "cursor": [".cursor/rules/*.mdc", ".cursorrules"],
    "copilot": [
        ".github/copilot-instructions.md",
        ".github/instructions/*.instructions.md",
    ],
    "claude": ["CLAUDE.md", ".claude/CLAUDE.md"],
    "codex": ["AGENTS.md", "AGENTS.override.md"],
}

# Single-file instruction targets (always-on, no per-file frontmatter)
SINGLE_FILE_INSTRUCTION_TARGETS: dict[str, str] = {
    "claude": "CLAUDE.md",
    "codex": "AGENTS.md",
}

################################################################################
#                                                                              #
# AGENT FILE PATHS                                                             #
#                                                                              #
################################################################################

AGENT_PATHS: dict[str, list[str]] = {
    "cursor": [".cursor/rules/agent-*.mdc", ".cursor/agents/*.md"],
    "copilot": [".github/agents/*.agent.md"],
    "claude": [".claude/agents/*.md"],
    "codex": [],  # Codex uses sections within AGENTS.md
}

AGENT_TARGET_DIRS: dict[str, str] = {
    "cursor": ".cursor/agents",
    "copilot": ".github/agents",
    "claude": ".claude/agents",
}

AGENT_TARGET_EXTENSIONS: dict[str, str] = {
    "cursor": ".md",
    "copilot": ".agent.md",
    "claude": ".md",
}

################################################################################
#                                                                              #
# PROMPT FILE PATHS                                                            #
#                                                                              #
################################################################################

PROMPT_PATHS: dict[str, list[str]] = {
    "cursor": [".cursor/prompts/*.md", ".cursor/commands/*.md"],
    "copilot": [".github/prompts/*.prompt.md"],
    "claude": [".claude/prompts/*.md"],
    "codex": [],  # Codex has no prompt file concept
}

PROMPT_TARGET_DIRS: dict[str, str] = {
    "cursor": ".cursor/commands",
    "copilot": ".github/prompts",
    "claude": ".claude/prompts",
}

PROMPT_TARGET_EXTENSIONS: dict[str, str] = {
    "cursor": ".md",
    "copilot": ".prompt.md",
    "claude": ".md",
}

################################################################################
#                                                                              #
# SKILL FILE PATHS                                                             #
#                                                                              #
################################################################################

SKILL_PATHS: dict[str, list[str]] = {
    "cursor": [".cursor/skills/*/SKILL.md"],
    "copilot": [".github/skills/*/SKILL.md"],
    "claude": [".claude/skills/*/SKILL.md"],
    "codex": [".agents/skills/*/SKILL.md"],
}

SKILL_TARGET_DIRS: dict[str, str] = {
    "cursor": ".cursor/skills",
    "copilot": ".github/skills",
    "claude": ".claude/skills",
    "codex": ".agents/skills",
}

################################################################################
#                                                                              #
# AGENT FIELD SUPPORT                                                          #
#                                                                              #
################################################################################

# Fields supported per platform for agent files
AGENT_SUPPORTED_FIELDS: dict[str, set[str]] = {
    "cursor": {"name", "description", "model", "readonly", "is_background"},
    "copilot": {
        "name", "description", "tools", "model", "agents",
        "handoffs", "user-invokable", "target",
    },
    "claude": {"name", "description"},
    "codex": set(),  # Codex agents are just markdown sections
}

################################################################################
#                                                                              #
# PROMPT FIELD SUPPORT                                                         #
#                                                                              #
################################################################################

# Fields supported per platform for prompt files
PROMPT_SUPPORTED_FIELDS: dict[str, set[str]] = {
    "cursor": set(),  # Cursor prompts/commands are plain markdown
    "copilot": {"description", "name", "agent", "model", "tools", "argument-hint"},
    "claude": set(),  # Claude prompts are plain markdown
    "codex": set(),
}

################################################################################
#                                                                              #
# INSTRUCTION FIELD SUPPORT                                                    #
#                                                                              #
################################################################################

# Fields supported per platform for instruction files
INSTRUCTION_SUPPORTED_FIELDS: dict[str, set[str]] = {
    "cursor": {"description", "alwaysApply", "globs"},
    "copilot": {"name", "description", "applyTo"},
    "claude": set(),  # Claude instructions are plain markdown
    "codex": set(),  # Codex instructions are plain markdown
}

################################################################################
#                                                                              #
# GLOB FIELD MAPPING                                                           #
#                                                                              #
################################################################################

# Mapping between glob/scope field names across platforms
GLOB_FIELD_MAP: dict[str, str] = {
    "cursor": "globs",    # list of globs
    "copilot": "applyTo",  # single glob string
}

################################################################################
#                                                                              #
# WARNING MESSAGES                                                             #
#                                                                              #
################################################################################

# Verbose workaround messages for lossy conversions
VERBOSE_WORKAROUNDS: dict[str, str] = {
    "alwaysApply": (
        "The alwaysApply field controls whether a Cursor rule is always active. "
        "Other platforms do not have this concept. If the rule should be "
        "conditional, add context in the instruction text."
    ),
    "globs_lost": (
        "The target platform does not support file-scoped instructions. "
        "The instruction will apply globally. Consider adding file-path "
        "references in the instruction text to indicate intended scope."
    ),
    "tools_removed": (
        "Tool bindings are platform-specific. Configure tools manually "
        "on the target platform."
    ),
    "handoffs_removed": (
        "Handoff workflows are a Copilot-specific feature. Implement "
        "equivalent logic manually on the target platform."
    ),
    "model_removed": (
        "Model identifiers differ between platforms. Set the model "
        "manually on the target platform."
    ),
    "readonly_removed": (
        "The readonly flag is not supported on the target platform. "
        "Enforce read-only behavior via instruction text."
    ),
    "is_background_removed": (
        "The is_background flag is not supported on the target platform."
    ),
    "user_invokable_removed": (
        "The user-invokable flag is a Copilot-specific visibility control. "
        "Not applicable on the target platform."
    ),
    "target_removed": (
        "The target field (vscode/github-copilot) is Copilot-specific. "
        "Not applicable on the target platform."
    ),
    "agent_binding_removed": (
        "Prompt agent bindings are Copilot-specific. Bind the prompt "
        "to an agent manually on the target platform."
    ),
    "mcp_servers_removed": (
        "MCP server configuration must be configured separately. "
        "See target platform documentation."
    ),
}
