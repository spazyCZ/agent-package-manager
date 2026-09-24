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

PLATFORMS = ("cursor", "copilot", "claude-code", "codex")

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
    "claude-code": ["CLAUDE.md", ".claude/CLAUDE.md"],
    "codex": ["AGENTS.md", "AGENTS.override.md"],
}

# Single-file instruction targets (always-on, no per-file frontmatter)
SINGLE_FILE_INSTRUCTION_TARGETS: dict[str, str] = {
    "claude-code": "CLAUDE.md",
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
    "claude-code": [".claude/agents/*.md"],
    "codex": [],  # Codex uses sections within AGENTS.md
}

AGENT_TARGET_DIRS: dict[str, str] = {
    "cursor": ".cursor/agents",
    "copilot": ".github/agents",
    "claude-code": ".claude/agents",
}

AGENT_TARGET_EXTENSIONS: dict[str, str] = {
    "cursor": ".md",
    "copilot": ".agent.md",
    "claude-code": ".md",
}

################################################################################
#                                                                              #
# COMMAND FILE PATHS                                                           #
#                                                                              #
################################################################################

COMMAND_PATHS: dict[str, list[str]] = {
    "cursor": [".cursor/prompts/*.md", ".cursor/commands/*.md"],
    "copilot": [".github/prompts/*.prompt.md"],
    "claude-code": [".claude/commands/*.md", ".claude/prompts/*.md"],
    "codex": [],
}

COMMAND_TARGET_DIRS: dict[str, str] = {
    "cursor": ".cursor/commands",
    "copilot": ".github/prompts",
    "claude-code": ".claude/commands",
}

COMMAND_TARGET_EXTENSIONS: dict[str, str] = {
    "cursor": ".md",
    "copilot": ".prompt.md",
    "claude-code": ".md",
}

PROMPT_TARGET_DIRS: dict[str, str] = {
    "cursor": ".cursor/commands",
    "copilot": ".github/prompts",
    "claude-code": ".claude/prompts",
}

################################################################################
#                                                                              #
# SKILL FILE PATHS                                                             #
#                                                                              #
################################################################################

SKILL_PATHS: dict[str, list[str]] = {
    "cursor": [".cursor/skills/*/SKILL.md"],
    "copilot": [".github/skills/*/SKILL.md"],
    "claude-code": [".claude/skills/*/SKILL.md"],
    "codex": [".agents/skills/*/SKILL.md"],
}

SKILL_TARGET_DIRS: dict[str, str] = {
    "cursor": ".cursor/skills",
    "copilot": ".github/skills",
    "claude-code": ".claude/skills",
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
    "claude-code": {"name", "description"},
    "codex": set(),  # Codex agents are just markdown sections
}

################################################################################
#                                                                              #
# COMMAND FIELD SUPPORT                                                        #
#                                                                              #
################################################################################

# Fields supported per platform for command files
COMMAND_SUPPORTED_FIELDS: dict[str, set[str]] = {
    "cursor": set(),
    "copilot": {"description", "name", "agent", "model", "tools", "argument-hint"},
    "claude-code": set(),
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
    "claude-code": set(),  # Claude instructions are plain markdown
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
# HOOK EVENT NAME TRANSLATION                                                  #
#                                                                              #
################################################################################

# Canonical UAAPS hook event names (keys) and their platform-specific
# equivalents.  Each platform dict maps canonical → platform event name.
# Platforms with no hook support are excluded from the inner dicts.
#
# UAAPS v0.5.0 cross-platform hook table (§ hooks):
#   Canonical           Claude            Cursor                    Copilot
#   ─────────────────   ───────────────   ─────────────────────     ─────────────────
#   pre_tool_use        PreToolUse        beforeShellCommand        PreToolUse
#   post_tool_use       PostToolUse       afterShellCommand         (not supported)
#   pre_prompt          UserPromptSubmit  (not supported)           userPromptSubmitted
#   session_start       SessionStart      (not supported)           sessionStart
#   session_end         SessionEnd        (not supported)           sessionEnd
#   stop                Stop              stop                      (not supported)
#   sub_agent_end       SubagentStop      (not supported)           (not supported)
#   pre_compact         PreCompact        (not supported)           PreCompact
#   notification        Notification      (not supported)           (not supported)
#   permission_request  PermissionRequest (not supported)           (not supported)
#
# Codex does not support hooks at all.
# Copilot uses PascalCase naming for most events (VS Code 1.109+).

HOOK_EVENT_TO_PLATFORM: dict[str, dict[str, str]] = {
    "pre_tool_use": {
        "claude-code": "PreToolUse",
        "cursor": "beforeShellCommand",
        "copilot": "PreToolUse",
    },
    "post_tool_use": {
        "claude-code": "PostToolUse",
        "cursor": "afterShellCommand",
    },
    "pre_prompt": {
        "claude-code": "UserPromptSubmit",
        "copilot": "userPromptSubmitted",
    },
    "session_start": {
        "claude-code": "SessionStart",
        "copilot": "sessionStart",
    },
    "session_end": {
        "claude-code": "SessionEnd",
        "copilot": "sessionEnd",
    },
    "stop": {
        "claude-code": "Stop",
        "cursor": "stop",
    },
    "sub_agent_end": {
        "claude-code": "SubagentStop",
    },
    "pre_compact": {
        "claude-code": "PreCompact",
        "copilot": "PreCompact",
    },
    "notification": {
        "claude-code": "Notification",
    },
    "permission_request": {
        "claude-code": "PermissionRequest",
    },
}

# Reverse mapping: platform event name → canonical UAAPS name.
# Generated from HOOK_EVENT_TO_PLATFORM for import efficiency.
HOOK_PLATFORM_TO_CANONICAL: dict[str, dict[str, str]] = {}

for _canonical, _platform_map in HOOK_EVENT_TO_PLATFORM.items():
    for _platform, _event in _platform_map.items():
        if _platform not in HOOK_PLATFORM_TO_CANONICAL:
            HOOK_PLATFORM_TO_CANONICAL[_platform] = {}
        HOOK_PLATFORM_TO_CANONICAL[_platform][_event] = _canonical

# Events supported per platform (for validation / filtering)
SUPPORTED_HOOK_EVENTS: dict[str, set[str]] = {
    platform: set(events.keys())
    for platform, events in {
        p: {
            canonical: ev_map[p]
            for canonical, ev_map in HOOK_EVENT_TO_PLATFORM.items()
            if p in ev_map
        }
        for p in ("claude-code", "cursor", "copilot")
    }.items()
}


def translate_hook_event(canonical: str, platform: str) -> str | None:
    """Translate a canonical UAAPS hook event name to a platform event name.

    Args:
        canonical: Canonical UAAPS event name (e.g. ``"pre_tool_use"``).
        platform: Target platform (``"claude-code"``, ``"cursor"``, ``"copilot"``).

    Returns:
        Platform-specific event name, or ``None`` if not supported.
    """
    return HOOK_EVENT_TO_PLATFORM.get(canonical, {}).get(platform)


def translate_hook_event_from_platform(platform_event: str, platform: str) -> str | None:
    """Translate a platform hook event name to the canonical UAAPS name.

    Args:
        platform_event: Platform-specific event name (e.g. ``"PreToolUse"``).
        platform: Source platform (``"claude-code"``, ``"cursor"``, ``"copilot"``).

    Returns:
        Canonical UAAPS event name, or ``None`` if unknown.
    """
    return HOOK_PLATFORM_TO_CANONICAL.get(platform, {}).get(platform_event)


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
    "command_binding_removed": (
        "Command agent bindings are Copilot-specific. Bind the command "
        "to an agent manually on the target platform."
    ),
    "mcp_servers_removed": (
        "MCP server configuration must be configured separately. "
        "See target platform documentation."
    ),
}
