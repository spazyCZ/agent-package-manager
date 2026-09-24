# Universal Agentic Artifact Package Specification (UAAPS)

> **Version**: 0.4.0-draft (DESIGN.md merge)  
> **Date**: 2026-02-19 (revised)  
> **Purpose**: Define a universal, portable package standard for AI agent artifacts — analogous to Docker for containers or npm for JavaScript packages.  
> **Goal**: Write once, deploy to any agent platform. Simplify migration. Eliminate vendor lock-in.

---

## 1. Design Principles

| Principle | Description |
|-----------|-------------|
| **Portability** | A single package works across Claude Code, Cursor, Copilot, Codex, and any compliant platform. |
| **Progressive Disclosure** | Metadata loads first; full instructions load on activation; resources load on-demand. |
| **Convention over Configuration** | Standard directory names eliminate per-platform mapping; overrides are optional. |
| **Filesystem-First** | All artifacts are files on disk — no databases, no APIs required, no binary formats. |
| **Composability** | Packages can be installed together; namespacing prevents conflicts. |
| **Deterministic Resolution** | Lock files ensure reproducible installs across machines and CI. |
| **Backward Compatibility** | Existing Claude Code plugins and Cursor plugins work with minimal changes. |

---

## 2. Package Directory Structure

```
package-name/
├── package.agent.json            # Package manifest (REQUIRED)
├── package.agent.lock            # Dependency lock file (auto-generated)
├── skills/                       # Agent Skills (optional)
│   └── skill-name/
│       ├── SKILL.md              # Skill instructions (REQUIRED per skill)
│       ├── scripts/              # Executable scripts
│       ├── references/           # Documentation files
│       └── assets/               # Templates, data, images
├── commands/                     # Slash commands (optional)
│   └── command-name.md
├── agents/                       # Sub-agent definitions (optional)
│   └── agent-name/
│       ├── agent.yaml            # Agent definition (name, skills, tools, params)
│       └── system-prompt.md      # Agent system prompt
├── rules/                        # Project rules / instructions (optional)
│   └── rule-name/
│       └── RULE.md
├── hooks/                        # Lifecycle hooks (optional)
│   └── hooks.json
├── mcp/                          # MCP server configs (optional)
│   └── servers.json
├── evals/                        # Quality evals (optional)
│   └── eval-name.yaml
├── AGENTS.md                     # Universal agent instructions (optional)
├── README.md                     # Human documentation
├── CHANGELOG.md                  # Version history
└── LICENSE                       # License file
```

---

## 3. Package Manifest — `package.agent.json`

The manifest is the **single required file**. It identifies the package and declares its contents.

### Schema

```jsonc
{
  // === REQUIRED ===
  "name": "my-package",                        // [a-z0-9-] or @scope/name, max 64/130 chars
  "version": "1.0.0",                          // SemVer

  // === RECOMMENDED ===
  "description": "Brief description",          // Max 1024 chars
  "author": "org-or-user",
  "license": "Apache-2.0",
  "repository": "https://github.com/org/repo",
  "homepage": "https://docs.example.com",      // Project homepage or docs URL

  // === OPTIONAL ===
  "category": "Developer Tools",               // Marketplace category
  "keywords": ["testing", "python"],            // Discovery tags
  "engines": {                                  // Platform compatibility
    "claude-code": ">=1.0",
    "cursor": ">=2.2",
    "copilot": "*",
    "codex": "*"
  },

  // === ARTIFACT DECLARATIONS (optional, explicit registry; auto-discovered if omitted) ===
  // Declaring artifacts explicitly enables richer registry metadata and description per artifact.
  "artifacts": {
    "skills": [
      { "name": "pdf-tools", "path": "skills/pdf-tools/", "description": "Extract text from PDFs" }
    ],
    "agents": [
      { "name": "code-auditor", "path": "agents/code-auditor/", "description": "Security audit agent" }
    ],
    "prompts": [
      { "name": "audit-finding", "path": "prompts/audit-finding.md", "description": "Finding template" }
    ],
    "commands": [
      { "name": "review", "path": "commands/review.md", "description": "Code review command" }
    ]
  },

  // === DEPENDENCIES (optional) ===
  "dependencies": {                             // Other agent packages required
    "code-review": "^1.0.0",                   //   SemVer range
    "testing-utils": ">=2.1.0 <3.0.0"
  },
  "optionalDependencies": {                     // Nice-to-have, install doesn't fail
    "ai-image-gen": "^1.0.0"
  },
  "peerDependencies": {                         // Must be provided by host environment
    "eslint-rules": ">=3.0.0"
  },
  "systemDependencies": {                       // OS-level / runtime requirements
    "python": ">=3.10",
    "node": ">=18",
    "packages": {                               //   Package manager installs
      "pip": ["pypdf", "pdfplumber>=0.10"],
      "npm": ["prettier", "eslint"],
      "brew": ["graphviz"],
      "apt": ["poppler-utils"]
    },
    "binaries": ["git", "docker"],              //   Must exist on $PATH
    "mcp-servers": ["filesystem"]              //   Required MCP servers
  },

  // === ENVIRONMENT & SECRETS (optional) ===
  "env": {                                      // Required environment variables
    "GITHUB_TOKEN": { "description": "Required for PR creation", "required": true },
    "DEBUG_MODE": { "description": "Enable verbose logging", "required": false, "default": "false" }
  },

  // === PERMISSIONS (optional) ===
  "permissions": {                              // Requested agent capabilities
    "fs": ["read", "write"],                    // Filesystem access scope
    "network": ["api.github.com"],              // Allowed network hosts
    "shell": false                              // Allow arbitrary shell execution
  },

  // === QUALITY (optional) ===
  "quality": {
    "tests": [
      { "name": "unit-tests", "command": "pytest tests/", "description": "Unit tests" }
    ],
    "evals": [
      {
        "name": "accuracy-eval",
        "path": "evals/accuracy.yaml",
        "description": "Measures accuracy against benchmark",
        "metrics": [
          { "name": "accuracy", "type": "percentage" }
        ]
      }
    ]
  },

  // === COMPONENT OVERRIDES (optional, defaults use convention) ===
  "skills": "./skills",                         // Default: ./skills
  "commands": "./commands",                     // Default: ./commands
  "agents": "./agents",                         // Default: ./agents
  "rules": "./rules",                           // Default: ./rules
  "hooks": "./hooks/hooks.json",                // Default: ./hooks/hooks.json
  "mcp": "./mcp/servers.json",                  // Default: ./mcp/servers.json

  // === VENDOR EXTENSIONS (optional) ===
  "x-claude": {
    "marketplace": "anthropics/skills"
  },
  "x-cursor": {
    "category": "Developer Tools"
  }
}
```

### Format Support

The canonical format is **JSON** (`package.agent.json`), but tools SHOULD also accept **YAML** (`package.agent.yaml`) for author convenience:

```yaml
# package.agent.yaml (equivalent to JSON, author-friendly)
name: my-package           # or @scope/my-package for scoped
version: 1.0.0
description: Brief description
author: org-or-user
license: Apache-2.0
homepage: https://docs.example.com

skills: ./skills
commands: ./commands
agents: ./agents


dependencies:
  code-review: "^1.0.0"

x-claude:
  marketplace: anthropics/skills

x-cursor:
  category: Developer Tools
```

**Rules**:
- If both `.json` and `.yaml` exist, **JSON takes precedence**.
- CLI tools (`aam install`, etc.) generate `package.agent.json` as the canonical output.
- Lock files (`package.agent.lock`) are always JSON.

### Vendor Mapping

| Manifest Field | Claude Code (`plugin.json`) | Cursor (`.cursor-plugin/plugin.json`) |
|----------------|----------------------------|---------------------------------------|
| `name` | `name` | `name` |
| `version` | `version` | `version` |
| `description` | `description` | `description` |
| `homepage` | N/A | N/A |
| `skills` | (auto-discovered in `skills/`) | (auto-discovered in `skills/`) |
| `commands` | `commands` | N/A (uses rules) |
| `agents` | `agents` | N/A (uses rules/agents) |
| `hooks` | `hooks` path | `.cursor/hooks.json` |
| `mcp` | `mcpServers` | `mcp.json` |
| `dependencies` | N/A (no native equivalent) | N/A (no native equivalent) |
| `systemDependencies` | Skill `compatibility` field | N/A |
| `quality` | N/A | N/A |

---

## 4. Skills — `SKILL.md`

Skills are the **primary portable artifact** — already standardized via the Agent Skills Open Standard (agentskills.io) and adopted by Claude Code, Cursor, Copilot, Codex, and others.

### SKILL.md Format

```markdown
---
# === REQUIRED ===
name: skill-name                    # [a-z0-9-], max 64 chars
description: >                      # Max 1024 chars. WHAT it does + WHEN to use it.
  Extract text and tables from PDF files, fill forms, merge documents.
  Use when working with PDF files or when the user mentions PDFs.

# === OPTIONAL (Open Standard) ===
license: Apache-2.0
compatibility:                      # Only if skill has special requirements
  requires:
    - python>=3.10
    - pypdf
metadata:                           # Arbitrary key-value extensions
  author: my-org
  version: "1.0"

# === OPTIONAL (Platform Extensions) ===
allowed-tools: Read Grep Glob Bash  # Pre-approved tools (experimental)
context: fork                       # Claude Code: run in isolated sub-agent
agent: Explore                      # Claude Code: sub-agent config
disable-model-invocation: true      # Claude Code: user-only invocation
---

# Skill Title

## Instructions
Step-by-step guidance...

## Examples
Concrete usage examples...
```

### Frontmatter Field Reference

| Field | Type | Required | Standard | Description |
|-------|------|----------|----------|-------------|
| `name` | `string` | **Yes** | agentskills.io | `[a-z0-9-]`, max 64 chars |
| `description` | `string` | **Yes** | agentskills.io | What + When. Max 1024 chars. |
| `license` | `string` | No | agentskills.io | License identifier or filename |
| `compatibility` | `map` | No | agentskills.io | Environment requirements |
| `metadata` | `map<str,str>` | No | agentskills.io | Extension key-value pairs |
| `allowed-tools` | `string` | No | Extension | Space-delimited tool whitelist |
| `context` | `string` | No | Claude ext. | `"fork"` for isolated execution |
| `agent` | `string` | No | Claude ext. | Sub-agent config name |
| `disable-model-invocation` | `bool` | No | Claude ext. | Restrict to user-only invocation |

### Skill Directory

```
skill-name/
├── SKILL.md         # REQUIRED
├── scripts/         # Executable code (Python, Bash, JS)
├── references/      # Additional documentation
├── assets/          # Templates, images, data
└── examples/        # Example inputs/outputs
```

### Progressive Disclosure

| Phase | What Loads | Token Cost |
|-------|-----------|------------|
| 1. Metadata | `name` + `description` from all skills | ~50 tokens/skill |
| 2. Activation | Full `SKILL.md` body | ~2,000–5,000 tokens |
| 3. Execution | `scripts/`, `references/`, `assets/` on-demand | Variable |

### Skills Discovery & Precedence

Skills can exist at multiple scopes. The universal resolver follows this precedence:

| Scope | Location | Precedence | Namespaced? |
|-------|----------|-----------|-------------|
| **Managed / Enterprise** | Admin-deployed | Highest | No |
| **Project** | `./skills/` (in package or `.claude/skills/` or `.github/skills/`) | Overrides personal | No |
| **Personal** | `~/.claude/skills/` or `~/.github/skills/` or user profile | Lowest non-plugin | No |
| **Plugin / Package** | `<package>/skills/` | Always namespaced | Yes (`pkg:skill`) |

**Resolution rules**:
- When project and personal skills share the same `name`, **project wins**.
- Plugin/package skills are **always namespaced** (`package-name:skill-name`) so they never conflict.
- Enterprise/managed rules override all other scopes.
- Monorepo support: skills in nested subdirectory `.claude/skills/` or `.github/skills/` are auto-discovered.

> **Disputed precedence**: ChatGPT investigation claimed enterprise > personal > project. Our investigation (verified against community guides) found enterprise > project > personal. The enterprise tier being highest is agreed; the project > personal ordering is confirmed by Claude Code behavior where `.claude/skills/` in the project overrides `~/.claude/skills/` for same-named skills.

### Platform Compatibility

| Platform | Skill Location | Status |
|----------|---------------|--------|
| Claude Code | `~/.claude/skills/`, `.claude/skills/`, plugin `skills/` | ✅ Full support |
| Cursor | Plugin `skills/`, imported as agent-decided rules | ✅ Supported (v2.2+) |
| GitHub Copilot | `.github/skills/`, `.claude/skills/` (also supported), user profile | ✅ Supported |
| OpenAI Codex | `~/.codex/skills/`, `.agents/skills/` | ✅ Supported |
| Amp, Goose, OpenCode, Letta | Various paths | ✅ Supported |

---

## 5. Commands (Slash Commands)

Commands are **user-invoked** prompts triggered by typing `/command-name`.

### Format

```markdown
---
description: Run a comprehensive code review on the current file
---

Review the current file for:
1. Code organization and structure
2. Error handling patterns
3. Performance implications
4. Security vulnerabilities
5. Test coverage gaps

Provide specific, actionable feedback with line references.
```

### Frontmatter Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | `string` | Recommended | Shown in command listings and help. |

### Platform Mapping

| Platform | Native Support | Location | Invocation |
|----------|---------------|----------|------------|
| Claude Code | ✅ Yes | `commands/` (.md files) | `/plugin:command` |
| Cursor | ⚠️ Partial | Rules can serve similar purpose | No native `/command` from plugins |
| Codex | ⚠️ Via skills | Skills with `disable-model-invocation` | `$skill-name` |

### Migration Strategy
For platforms without native command support, commands can be **converted to skills** with `disable-model-invocation: true` to achieve similar user-initiated behavior.

---

## 5.5 Prompts (Reusable Prompt Templates)

Prompts are **parameterized prompt templates** with variable interpolation. Unlike commands (which are user-invoked) and skills (which are model-invoked), prompts are **reusable fragments** referenced by skills and agents.

### Format

```markdown
---
name: audit-finding
description: "Structured prompt for documenting a single audit finding"
variables:
  - name: control_id
    description: "Control identifier"
    required: true
  - name: severity
    description: "Finding severity level"
    required: true
    enum: [critical, high, medium, low]
    default: medium
  - name: evidence
    description: "Supporting evidence"
    required: false
    default: "No evidence provided"
---

# Audit Finding: {{control_id}}

## Severity: {{severity}}

Analyze the following evidence and produce a structured finding:

{{evidence}}
```

### Frontmatter Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | **Yes** | Identifier, `[a-z0-9-]`. |
| `description` | `string` | Recommended | Shown in listings. |
| `variables` | `Variable[]` | No | Template variables with optional defaults and enums. |

### Platform Mapping

| Platform | Native Support | Location |
|----------|---------------|----------|
| Claude Code | ✅ `.claude/prompts/` | `.claude/prompts/<name>.md` |
| Cursor | ✅ `.cursor/prompts/` | `.cursor/prompts/<name>.md` |
| GitHub Copilot | ✅ `.github/prompts/` | `.github/prompts/<name>.prompt.md` |
| Codex | ⚠️ Via skills | Embedded in SKILL.md |

---

## 6. Agents (Sub-agent Definitions)

Agents are **specialized personas** with domain expertise that can be selected automatically or manually. *(Note: This is distinct from `AGENTS.md`, which provides project-wide instructions).*

Agents are defined as a **directory** containing two files, which provides richer structured configuration than a single markdown file.

### Directory Structure

```
agents/
└── code-auditor/
    ├── agent.yaml        # REQUIRED — structured agent definition
    └── system-prompt.md  # REQUIRED — the agent's full system prompt
```

### `agent.yaml` Format

```yaml
name: code-auditor
description: "Security-focused code review agent"
version: 1.0.0

system_prompt: system-prompt.md    # Path to the system prompt file

# Skills this agent uses (resolved from package or dependencies)
skills:
  - pdf-tools                      # from this package
  - code-review                    # from dependency

# Prompts this agent references
prompts:
  - audit-finding                  # from this package

# Tool access (platform-dependent)
tools:
  - file_read
  - file_write
  - shell

# Behavioral parameters
parameters:
  temperature: 0.3
  style: professional
  output_format: markdown
```

### `system-prompt.md` Format

```markdown
---
description: Security review specialist for vulnerability analysis
capabilities:
  - OWASP Top 10 detection
  - Dependency vulnerability scanning
  - Secret detection
  - Cryptographic implementation review
---

You are a security review specialist. When analyzing code:

1. Check for injection vulnerabilities
2. Verify authentication patterns
3. Review cryptographic implementations
4. Scan for hardcoded secrets
5. Assess dependency security

Provide severity ratings (Critical/High/Medium/Low) with remediation.
```

### `agent.yaml` Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | **Yes** | Agent identifier. |
| `description` | `string` | **Yes** | Role summary for automatic selection. |
| `system_prompt` | `string` | **Yes** | Relative path to `system-prompt.md`. |
| `skills` | `string[]` | No | Skills this agent activates. |
| `prompts` | `string[]` | No | Prompt templates this agent uses. |
| `tools` | `string[]` | No | Tool whitelist (platform-dependent). |
| `parameters` | `map` | No | Behavioral parameters (temperature, style, etc.). |

> **Legacy format**: A single `agent-name.md` file (without a separate `agent.yaml`) is also accepted for backward compatibility. In this case the frontmatter fields from the `system-prompt.md` table below apply directly to the single file.

### Platform Mapping

| Platform | Native Support | Migration |
|----------|---------------|-----------|
| Claude Code | ✅ Yes (`agents/` dir) | Direct |
| Cursor | ⚠️ No native `agents/` | Convert `system-prompt.md` → RULE.md with `alwaysApply: true` |
| GitHub Copilot | ✅ `.github/agents/*.agent.md` | Convert to `.agent.md` |
| Codex | ⚠️ Via skills | Convert to skill |

---

## 7. Rules (Project Rules / Instructions)

Rules provide **persistent context** — coding standards, architecture conventions, and project-specific guidance.

### Universal Format: `RULE.md`

```markdown
---
description: "TypeScript coding standards for this project"
globs: "src/**/*.{ts,tsx}"
alwaysApply: false
---

# TypeScript Standards

- Use strict mode
- Prefer `const` over `let`
- Use early returns
- Named exports only
- Co-locate tests as `*.test.ts`
```

### Frontmatter Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | `string` | **Yes** | Purpose of rule. Used for agent auto-selection. |
| `globs` | `string` | No | File patterns for auto-attachment. |
| `alwaysApply` | `boolean` | No | Always include in context. Default: `false`. |

### Platform Mapping

| Platform | Native Format | Migration |
|----------|--------------|-----------|
| Claude Code | `CLAUDE.md` (freeform) | Copy content into `CLAUDE.md` |
| Cursor | `.mdc` / `RULE.md` in `.cursor/rules/` | Copy to `.cursor/rules/` |
| Codex | `AGENTS.md` | Copy into `AGENTS.md` sections |
| Universal | `AGENTS.md` (project root) | Direct (supported everywhere) |

### `AGENTS.md` as Universal Fallback
`AGENTS.md` at the project root is the **most portable instruction format** — supported by Claude Code, Cursor, Codex, Copilot, Gemini CLI, Jules, Amp, and others. Every universal package SHOULD include an `AGENTS.md` for maximum compatibility.

---

## 8. Hooks (Lifecycle Event Handlers)

Hooks execute shell commands at specific points in the agent lifecycle. They run **outside** the context window with zero token overhead.

### Universal `hooks.json` Format

```json
{
  "version": 1,
  "hooks": {
    "pre-tool-use": [
      {
        "matcher": "Write|Edit",
        "hooks": [{
          "type": "command",
          "command": "bash ${PACKAGE_ROOT}/hooks/scripts/validate.sh",
          "timeout": 30
        }]
      }
    ],
    "post-tool-use": [
      {
        "matcher": "Write|Edit",
        "hooks": [{
          "type": "command",
          "command": "npx prettier --write ${file}"
        }]
      }
    ],
    "stop": [
      {
        "hooks": [{
          "type": "prompt",
          "prompt": "Check if all tasks are complete. Context: $ARGUMENTS",
          "timeout": 30
        }]
      }
    ],
    "session-start": [
      {
        "hooks": [{
          "type": "command",
          "command": "bash ${PACKAGE_ROOT}/hooks/scripts/setup.sh"
        }]
      }
    ]
  }
}
```

### Unified Hook Events

| Universal Event | Claude Code | Cursor | Copilot | Can Block? | Description |
|----------------|-------------|--------|---------|------------|-------------|
| `pre-tool-use` | `PreToolUse` | `beforeShellCommand` / `beforeMcpCall` | `PreToolUse` | **Yes** | Before tool execution |
| `permission-request` | `PermissionRequest` | N/A | N/A | **Yes** | Permission dialog shown |
| `post-tool-use` | `PostToolUse` | `afterFileEdit` | `PostToolUse` | Feedback | After tool execution |
| `pre-prompt` | `UserPromptSubmit` | `beforeSubmitPrompt` | `UserPromptSubmit` | **Yes** / Copilot: logging | Before prompt processed |
| `session-start` | `SessionStart` | N/A | `SessionStart` | Context inject | New session begins |
| `session-end` | `SessionEnd` | N/A | N/A | Cleanup | Session terminates |
| `stop` | `Stop` | `stop` | `Stop` | **Yes** | Agent finishes responding |
| `sub-agent-start` | `SubagentStart` | N/A | `SubagentStart` | No | Sub-agent spawned |
| `sub-agent-end` | `SubagentStop` | N/A | `SubagentStop` | **Yes** | Sub-agent finishes |
| `pre-compact` | `PreCompact` | N/A | `PreCompact` | No | Before context compaction |
| `notification` | `Notification` | N/A | N/A | No | System notification |

> **Copilot hook parity (Feb 2026)**: VS Code 1.109+ supports 8 of 11 universal hook events, achieving near-parity with Claude Code. Missing events: `permission-request`, `session-end`, `notification`. VS Code uses PascalCase naming (same as Claude Code) and auto-converts lowerCamelCase from Copilot CLI format. Hook files can be placed in `.github/hooks/*.json`. Source: [VS Code Hooks docs](https://code.visualstudio.com/docs/copilot/customization/hooks).

### Hook Types

| Type | Description | Use Case |
|------|-------------|----------|
| `command` | Execute a shell command | Deterministic rules (lint, format, validate) |
| `prompt` | Query an LLM for context-aware decision | Stop/continue decisions, complex validation |

### Blocking Response Schema

For hooks that support blocking (`pre-tool-use`, `permission-request`, `pre-prompt`, `stop`):

```json
{
  "hookSpecificOutput": {
    "hookEventName": "pre-tool-use",
    "permissionDecision": "allow|deny|ask",
    "permissionDecisionReason": "Reason shown to user or agent",
    "updatedInput": {}
  }
}
```

For `stop` / `sub-agent-end`:

```json
{
  "decision": "block",
  "reason": "Tests not yet executed"
}
```

#### Exit Code Convention

| Code | Behavior |
|------|----------|
| `0` | Success. JSON on stdout parsed for structured control. |
| `2` | Blocking error. `stderr` fed back to agent. |
| Other | Non-blocking error. Logged only. |

### Hook Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `matcher` | `string` | No | Regex pattern for filtering by tool name. |
| `hooks[].type` | `string` | **Yes** | `"command"` or `"prompt"`. |
| `hooks[].command` | `string` | For `command` | Shell command. Receives JSON on stdin. |
| `hooks[].prompt` | `string` | For `prompt` | LLM prompt. `$ARGUMENTS` for input. |
| `hooks[].timeout` | `number` | No | Timeout in seconds. |
| `hooks[].windows` | `string` | No | Windows-specific command override. |
| `hooks[].linux` | `string` | No | Linux-specific command override. |
| `hooks[].osx` | `string` | No | macOS-specific command override. |

---

## 9. MCP Server Configuration

Model Context Protocol servers extend agent capabilities with external tool access.

### Universal `servers.json` Format

```json
{
  "servers": {
    "my-service": {
      "command": "node",
      "args": ["${PACKAGE_ROOT}/mcp-server/index.js"],
      "env": {
        "API_KEY": "${API_KEY}"
      }
    }
  }
}
```

### Platform Mapping

| Platform | Plugin Location | Project Location | Global Location | Root Variable |
|----------|----------------|-----------------|----------------|---------------|
| Claude Code | `.mcp.json` at plugin root | `.mcp.json` at project root | `~/.claude/.mcp.json` | `${CLAUDE_PLUGIN_ROOT}` |
| Cursor | `mcp.json` at plugin root | `.cursor/mcp.json` | `~/.cursor/mcp.json` | Working dir relative |
| Universal | `mcp/servers.json` | `mcp/servers.json` | N/A | `${PACKAGE_ROOT}` |

> **Critical**: Cursor plugin MCP uses `mcp.json` (no dot prefix, no `.cursor/` wrapper). Project/global MCP uses `.cursor/mcp.json`. Claude Code always uses `.mcp.json` (leading dot).

---

## 10. Cross-Platform Compatibility Matrix

### Artifact Support by Platform

| Artifact | Claude Code | Cursor | Copilot | Codex | Standard | Confidence |
|----------|------------|--------|---------|-------|----------|------------|
| **Skills (SKILL.md)** | ✅ Native | ✅ v2.2+ | ✅ `.github/skills/` | ✅ CLI+App | agentskills.io | Official |
| **Commands / Prompts** | ✅ Native | ⚠️ Via rules | ✅ `.prompt.md` | ⚠️ Via skills | Package-defined | Official |
| **Agents** | ✅ Native (`agents/*.md`) | ⚠️ Via rules | ✅ `.agent.md` | ⚠️ Via skills | Package-defined | Official |
| **Rules / Instructions** | ✅ `CLAUDE.md` | ✅ `.mdc`/`RULE.md` | ✅ `.instructions.md` | ⚠️ `AGENTS.md` | Package-defined | Official |
| **AGENTS.md** | ✅ | ✅ | ✅ | ✅ | agents.md | Official |
| **Hooks** | ✅ 10 events | ✅ 5 events | ✅ 8 events | ❌ | Package-defined | Official |
| **MCP Servers** | ✅ Native | ✅ Native | ✅ CCA + VS Code | ⚠️ Limited | MCP Protocol | Official |

### Instruction File Compatibility

| File | Claude Code | Cursor | Copilot | Codex | Jules | Confidence |
|------|------------|--------|---------|-------|-------|------------|
| `AGENTS.md` | ✅ | ✅ | ✅ | ✅ | ✅ | Official |
| `CLAUDE.md` | ✅ | ✅* | ❌ | ❌ | ❌ | Official |
| `GEMINI.md` | ❌ | ✅* | ❌ | ❌ | ❌ | Community |
| `.cursor/rules/*.mdc` | ❌ | ✅ | ❌ | ❌ | ❌ | Official |
| `.github/copilot-instructions.md` | ❌ | ❌ | ✅ | ❌ | ❌ | Official |
| `.github/instructions/*.instructions.md` | ❌ | ❌ | ✅ | ❌ | ❌ | Official |
| `.github/agents/*.agent.md` | ❌ | ❌ | ✅ | ❌ | ❌ | Official |

> *Cursor reads `CLAUDE.md` and `GEMINI.md` as agent-specific instruction files alongside `AGENTS.md`.

### GitHub Copilot Artifact Types

| Artifact | Location | Format | Description |
|----------|----------|--------|-------------|
| **Repo instructions** | `.github/copilot-instructions.md` | Plain Markdown | Repository-wide guidance |
| **Path instructions** | `.github/instructions/*.instructions.md` | YAML frontmatter (`applyTo` glob) + Markdown | Path-scoped rules |
| **Custom agents** | `.github/agents/*.agent.md` | Markdown | Agent definitions (VS Code) |
| **Agent instructions** | `AGENTS.md` / `CLAUDE.md` / `GEMINI.md` | Plain Markdown | Agent-specific instructions |

#### Path Instructions Example

```markdown
---
applyTo: "src/**/*.ts"
---

# TypeScript Standards
- Use strict mode
- Prefer interfaces over type aliases
```

---

## 11. Migration Guides

### From Claude Code Plugin → Universal Package

```
.claude-plugin/plugin.json    →  package.agent.json
commands/*.md                 →  commands/*.md (unchanged)
agents/*.md                   →  agents/<name>/system-prompt.md + agent.yaml (add structured def)
skills/*/SKILL.md             →  skills/*/SKILL.md (unchanged)
.claude/prompts/*.md          →  prompts/*.md (unchanged)
hooks/hooks.json              →  hooks/hooks.json (rename events)
.mcp.json                     →  mcp/servers.json (restructure)
CLAUDE.md                     →  AGENTS.md (rename)
```

### From Cursor Plugin → Universal Package

```
.cursor-plugin/plugin.json    →  package.agent.json
skills/*/SKILL.md             →  skills/*/SKILL.md (unchanged)
.cursor/prompts/*.md          →  prompts/*.md (unchanged)
rules/*.mdc                   →  rules/*/RULE.md (restructure frontmatter)
mcp.json                      →  mcp/servers.json (restructure)
.cursor/hooks.json            →  hooks/hooks.json (rename events)
AGENTS.md                     →  AGENTS.md (unchanged)
```

### From GitHub Copilot → Universal Package

```
.github/copilot-instructions.md    →  AGENTS.md (rename + restructure)
.github/instructions/*.instructions.md  →  rules/*/RULE.md (applyTo → globs)
.github/agents/*.agent.md          →  agents/*.md (remove .agent suffix)
AGENTS.md                          →  AGENTS.md (unchanged)
```

#### `.instructions.md` to `RULE.md` Frontmatter Mapping

```yaml
# Copilot (.instructions.md)        # Universal (RULE.md)
---                                  ---
applyTo: "src/**/*.ts"              globs: "src/**/*.ts"
---                                  alwaysApply: false
                                     description: "TypeScript standards"
                                     ---
```

### From `.mdc` Rule → `RULE.md`

```yaml
# .mdc (Cursor native)                    # RULE.md (Universal)
---                                        ---
description: React standards               description: React standards
globs: src/**/*.tsx                        globs: src/**/*.tsx
alwaysApply: false                         alwaysApply: false
---                                        ---
# Content...                               # Content...
```

The formats are functionally identical. Only the file extension changes.

---

## 12. Packaging & Distribution

### UAAPS Registry

Packages are published to and installed from a **UAAPS registry** — an HTTP server implementing the UAAPS registry protocol. The official public registry is `registry.agentpkg.io`; organizations can self-host a private registry.

```bash
# Install from the default registry
aam install @myorg/code-review

# Install from a private registry
aam install @myorg/code-review --registry https://pkg.myorg.internal/aam

# Publish to a registry
aam pkg publish --registry https://pkg.myorg.internal/aam
```

Registry configuration is managed in `~/.aam/config.yaml` or `.aam/config.yaml`:

```yaml
registries:
  default: https://registry.agentpkg.io
  sources:
    - name: myorg
      url: https://pkg.myorg.internal/aam
```

> Other distribution channels (Git marketplace, npm bridge, direct install, project-bundled) are supported by the `aam` CLI — see `aam_cli_new.md`.

### 12.1 Archive Distribution Format

Packages are distributed as **`.aam` archives** (gzipped tar), providing a binary-safe, single-file distribution unit.

```
my-package-1.0.0.aam   # produced by: aam pkg pack
```

**Archive constraints:**
- Maximum size: **50 MB**
- Must contain `package.agent.json` at root
- No symlinks outside the package directory
- No absolute paths
- SHA-256 checksum stored in `package.agent.lock` post-install

### 12.2 Scoped Package Names

Following npm convention, packages support a `@scope/name` format for namespacing under an organization or author:

| Format | Example | Use Case |
|--------|---------|----------|
| Unscoped | `code-review` | Community / public packages |
| Scoped | `@myorg/code-review` | Organization packages |

**Name rules:**
- Unscoped: `[a-z0-9-]`, max 64 chars
- Scope: `@[a-z0-9][a-z0-9_-]{0,63}`
- Full scoped name: max 130 chars

**Filesystem mapping** — the `@scope/name` format is converted using double-hyphen:

| Package Name | Filesystem Name |
|-------------|-----------------|
| `code-review` | `code-review` |
| `@myorg/code-review` | `myorg--code-review` |

The `--` separator is reversible and unambiguous because valid name segments cannot start with hyphens.

### 12.3 Dist-Tags

Dist-tags are **named aliases for package versions**, enabling installs like `aam install @org/agent@stable` or enterprise gates like `bank-approved`.

#### Default Tags

| Tag | Behavior |
|-----|----------|
| `latest` | Automatically set to the newest published version |
| `stable` | Opt-in; set manually via `aam dist-tag add` |

#### Custom Tags

Organizations can define arbitrary tags (e.g., `staging`, `bank-approved`, `qa-passed`).

**Tag rules:**
- Lowercase alphanumeric + hyphens only
- Max 32 characters
- Cannot be a valid SemVer string (prevents ambiguity)

#### Manifest Declaration (optional)

```jsonc
// package.agent.json
{
  "name": "@myorg/agent",
  "version": "1.2.0",
  "dist-tags": {
    "stable": "1.1.0",     // Maintained by publisher
    "latest": "1.2.0"
  }
}
```

### 12.4 Portable Bundles

A portable bundle is a **self-contained, pre-compiled archive** for a specific target platform. It contains artifacts already transformed to the platform's native format — no install-time resolution needed.

**Use case:** Distributing packages via Slack, email, or air-gapped environments without a registry.

```bash
aam pkg build --target cursor
# → dist/my-package-1.0.0-cursor.bundle.aam

aam pkg build --target copilot
# → dist/my-package-1.0.0-copilot.bundle.aam

aam pkg build --target all
# → one bundle per configured platform
```

**Bundle structure (tar.gz internally):**

```
my-package-1.0.0-cursor.bundle.aam
├── bundle.json               # Bundle manifest
├── .cursor/
│   ├── skills/...            # Pre-compiled platform artifacts
│   ├── rules/...
│   └── prompts/...
└── package.agent.json        # Original manifest for reference
```

**`bundle.json` schema:**

```json
{
  "format": "uaaps-bundle",
  "version": "1.0",
  "package": "@author/my-agent",
  "package_version": "1.2.0",
  "target": "cursor",
  "built_at": "2026-02-19T14:30:00Z",
  "checksum": "sha256:...",
  "artifacts": [
    { "type": "skill", "name": "my-skill", "path": ".cursor/skills/author--my-skill/" },
    { "type": "agent", "name": "my-agent", "path": ".cursor/rules/agent-author--my-agent.mdc" }
  ]
}
```

**Installing from a bundle:**

```bash
aam install ./dist/my-package-1.0.0-cursor.bundle.aam
# Deploys immediately — no dependency resolution needed
```

---

## 13. Dependency Resolution

Dependency resolution is a core differentiator of UAAPS over raw vendor plugin systems. Like npm, pip, or Cargo, the package manager must resolve a directed acyclic graph (DAG) of requirements before installation.

### 13.1 Dependency Types

| Type | Manifest Key | Required to Install? | Semantics |
|------|-------------|---------------------|-----------|
| **Direct** | `dependencies` | **Yes** — install fails | Other agent packages this package requires to function. |
| **Optional** | `optionalDependencies` | No — install succeeds | Enhances functionality if present. Graceful degradation if absent. |
| **Peer** | `peerDependencies` | **Yes** — warn/fail | Must be provided by the host project or another top-level install. Not auto-installed. |
| **System** | `systemDependencies` | **Yes** — pre-flight check | OS binaries, language runtimes, pip/npm packages, MCP servers. |

### 13.2 Version Constraint Syntax

UAAPS uses **SemVer 2.0** with npm-style range operators:

| Syntax | Meaning | Example |
|--------|---------|---------|
| `1.2.3` | Exact version | Only `1.2.3` |
| `^1.2.3` | Compatible with (`>=1.2.3 <2.0.0`) | Minor + patch updates OK |
| `~1.2.3` | Approximately (`>=1.2.3 <1.3.0`) | Patch updates only |
| `>=1.2.0` | Minimum version | `1.2.0` or higher |
| `>=1.0.0 <3.0.0` | Range | Between `1.0.0` and `2.x.x` |
| `*` | Any version | No constraint |

### 13.3 Lock File — `package.agent.lock`

After resolution, the solver writes a deterministic **lock file** pinning exact versions:

```jsonc
{
  "lockVersion": 1,
  "resolved": {
    "code-review": {
      "version": "1.3.2",
      "source": "marketplace:anthropics/skills",
      "integrity": "sha256-abc123...",
      "dependencies": {
        "git-utils": "1.0.1"
      }
    },
    "testing-utils": {
      "version": "2.4.0",
      "source": "npm:@agentpkg/testing-utils",
      "integrity": "sha256-def456..."
    },
    "git-utils": {
      "version": "1.0.1",
      "source": "marketplace:anthropics/skills",
      "integrity": "sha256-ghi789..."
    }
  },
  "systemChecks": {
    "python": "3.12.1",
    "binaries": {
      "git": "/usr/bin/git",
      "docker": "/usr/local/bin/docker"
    },
    "pip": {
      "pypdf": "4.1.0",
      "pdfplumber": "0.11.4"
    }
  }
}
```

**Behavior**:
- If `package.agent.lock` exists, install uses **locked versions** (reproducible builds).
- `aam install` reads the lock file; `aam update` regenerates it.
- Lock files SHOULD be committed to version control for deterministic environments.

### 13.4 Resolution Algorithm

```
1. Parse root package.agent.json
2. Build initial requirement graph from dependencies + peerDependencies
3. For each unresolved requirement:
   a. Fetch available versions from source (marketplace, npm, local)
   b. Filter by version constraint
   c. Select highest compatible version (prefer stable over pre-release)
   d. Recursively resolve transitive dependencies
4. Detect conflicts:
   a. If two packages require incompatible versions of the same dependency → ERROR
   b. If peerDependency is unmet by root or any ancestor → WARN (or ERROR if strict)
5. Flatten dependency tree (hoist where possible, like npm)
6. Run system dependency pre-flight checks
7. Write package.agent.lock
8. Install resolved packages to install directory
```

### 13.5 Resolution Strategies

| Strategy | Flag | Behavior |
|----------|------|----------|
| **Default** | (none) | Highest compatible version per constraint. |
| **Locked** | `--frozen` | Only use versions from lock file. Fail if lock is stale. |
| **Minimal** | `--minimal` | Lowest version satisfying each constraint (CI reproducibility). |
| **Latest** | `--latest` | Ignore constraints, install latest of everything (dangerous). |
| **Dry-run** | `--dry-run` | Resolve and display tree without installing. |

### 13.6 Package Dependencies (Agent-to-Agent)

Agent packages can depend on other agent packages. This enables composition:

```jsonc
// package.agent.json for "full-stack-review"
{
  "name": "full-stack-review",
  "version": "1.0.0",
  "dependencies": {
    "code-review": "^1.0.0",           // Reuse code review skills
    "security-scanning": "^2.0.0",     // Reuse security agents
    "testing-utils": "^1.5.0"          // Reuse test generation
  }
}
```

**Transitive resolution**: If `code-review@1.3.2` itself depends on `git-utils@^1.0.0`, the solver installs `git-utils` automatically.

**Namespace isolation**: Each installed dependency's skills, commands, and agents are namespaced under `dependency-name:artifact-name` to prevent collisions.

### 13.7 System Dependencies

System dependencies are **not installed** by the package manager — they are **verified** via pre-flight checks.

```jsonc
"systemDependencies": {
  // === Runtime requirements ===
  "python": ">=3.10",                  // Check: python3 --version
  "node": ">=18",                      // Check: node --version

  // === Package manager installs ===
  "packages": {
    "pip": ["pypdf>=4.0", "pdfplumber"],
    "npm": ["prettier@^3.0", "eslint"],
    "brew": ["graphviz", "poppler"],
    "apt": ["poppler-utils", "tesseract-ocr"],
    "cargo": ["ripgrep"]
  },

  // === Binary availability ===
  "binaries": ["git", "docker", "gh"],  // Must exist on $PATH

  // === MCP server requirements ===
  "mcp-servers": ["filesystem", "github"]
}
```

#### Pre-flight Check Flow

```
aam install my-package
  → Checking system dependencies...
  ✓ python 3.12.1 (>=3.10)
  ✓ node 20.11.0 (>=18)
  ✓ git found at /usr/bin/git
  ✗ docker not found on $PATH
  ✓ pip: pypdf 4.1.0 installed
  ✗ pip: pdfplumber not installed
  
  ⚠ Missing system dependencies:
    • docker: Install via https://docs.docker.com/get-docker/
    • pdfplumber: Run `pip install pdfplumber`
  
  Install package anyway? [y/N/auto-install]
```

#### Auto-Install Behavior

| Package Manager | Auto-install | Flag |
|----------------|-------------|------|
| `pip` | ✅ Supported | `--install-system-deps` |
| `npm` | ✅ Supported | `--install-system-deps` |
| `brew` / `apt` | ⚠️ Prompt only | Requires `--install-system-deps --allow-sudo` |
| `binaries` | ❌ Never | Manual install instructions provided |
| `mcp-servers` | ✅ Via MCP registry | `--install-system-deps` |

### 13.8 Skill-Level Dependencies

Individual skills can declare their own dependencies in SKILL.md frontmatter, complementing the package-level manifest:

```yaml
---
name: pdf-processing
description: Extract text and fill forms in PDFs.
compatibility:
  requires:
    - python>=3.10
    - pypdf>=4.0
    - pdfplumber
  packages:                          # UAAPS extension
    - code-review/git-utils          # Depends on another skill
  optional:
    - tesseract-ocr                  # For OCR, graceful degradation
---
```

**Resolution order**:
1. Package-level `systemDependencies` checked first (covers most skills).
2. Skill-level `compatibility.requires` checked on activation (lazy check).
3. Skill-level `compatibility.packages` resolved transitively if referencing other skills.

### 13.9 Conflict Resolution

#### Version Conflicts

When two packages require incompatible versions of the same dependency:

```
my-app
├── code-review@1.3.2
│   └── git-utils@^1.0.0  →  resolves to 1.0.5
└── deployment@2.0.0
    └── git-utils@^2.0.0  →  resolves to 2.1.0   ← CONFLICT
```

**Resolution strategies**:

| Strategy | Behavior | When to Use |
|----------|----------|-------------|
| **Fail** (default) | Error, refuse to install | Safety-first environments |
| **Duplicate** | Install both versions, isolate namespaces | When skills don't share state |
| **Override** | Use `resolutions` field to force a version | When you know compatibility holds |
| **Peer promote** | Lift to `peerDependencies`, let host decide | Library packages |

#### Resolution Overrides

```jsonc
// package.agent.json
{
  "resolutions": {
    "git-utils": "2.1.0"              // Force all transitive refs to this version
  }
}
```

#### Skill Name Conflicts

When two installed packages export skills with the same `name`:

- Skills are **namespaced** by package: `code-review:lint-check` vs `testing:lint-check`.
- If a skill is referenced without namespace, the **closest scope wins** (project > personal > plugin).
- Explicit disambiguation: `aam resolve skill lint-check` lists all matches.

### 13.10 Dependency Tree Commands

| Command | Description |
|---------|-------------|
| `aam install` | Install all dependencies from manifest (or lock file). |
| `aam install <pkg>` | Add a package and resolve. |
| `aam update` | Re-resolve all dependencies, update lock file. |
| `aam update <pkg>` | Update a single package within constraints. |
| `aam tree` | Display the full resolved dependency tree. |
| `aam tree --depth=1` | Show only direct dependencies. |
| `aam why <pkg>` | Explain why a package is installed (which parent requires it). |
| `aam check` | Verify all dependencies are installed and compatible. |
| `aam check --system` | Run system dependency pre-flight checks only. |
| `aam outdated` | List packages with newer versions available. |
| `aam audit` | Check dependencies for known security issues. |
| `aam dedupe` | Flatten tree, remove unnecessary duplicates. |
| `aam prune` | Remove installed packages not in the dependency tree. |

### 13.11 Install Directory Layout

```
.agent-packages/                       # Install root (analogous to node_modules/)
├── .lock                              # package.agent.lock (symlink or copy)
├── code-review/                       # Installed package
│   ├── package.agent.json
│   ├── skills/
│   │   └── lint-review/
│   │       └── SKILL.md
│   └── commands/
│       └── review.md
├── testing-utils/                     # Transitive dependency
│   ├── package.agent.json
│   └── skills/
│       └── test-gen/
│           └── SKILL.md
└── git-utils/                         # Shared dependency (hoisted)
    ├── package.agent.json
    └── skills/
        └── git-diff/
            └── SKILL.md
```

**Hoisting**: Like npm, shared dependencies are hoisted to the top level of `.agent-packages/` when version-compatible. This reduces duplication and simplifies skill discovery.

### 13.12 Dependency Resolution in CI/CD

For reproducible builds in CI environments:

```yaml
# .github/workflows/agent-check.yml
- name: Install agent packages (frozen)
  run: aam install --frozen

- name: Verify system dependencies
  run: aam check --system

- name: Audit for security issues
  run: aam audit --severity=high
```

The `--frozen` flag ensures CI uses exactly the versions from `package.agent.lock`, failing if the lock file is out of date.

---

## 14. Package Signing & Verification

AAM supports multiple levels of integrity and authenticity verification for packages.

### 14.1 Signing Methods

| Method | Description | When to Use |
|--------|-------------|-------------|
| **Checksum** | SHA-256 hash of archive, always applied | Automatic — all packages |
| **Sigstore** | Keyless, identity-based via OIDC | Recommended for public packages |
| **GPG** | Traditional key-based signing | Teams with existing GPG infrastructure |
| **Registry Attestation** | Server-side signatures | Automated trust for verified registries |

### 14.2 Signing Flow

```
Author                          Registry                         User
  │  aam pkg publish --sign       │                               │
  ├──────────────────────────────►│                               │
  │  1. Calculate SHA-256         │                               │
  │  2. Sign with Sigstore / GPG  │  Verify signature             │
  │  3. Upload archive+signature  │  Store attestation            │
  │                               │         aam install pkg       │
  │                               │◄──────────────────────────────┤
  │                               │  1. Download archive          │
  │                               ├──────────────────────────────►│
  │                               │  2. Verify checksum           │
  │                               │  3. Verify signature          │
  │                               │  4. Check trust policy        │
```

### 14.3 Verification Policy

Configure in global `~/.aam/config.yaml` or project `.aam/config.yaml`:

```yaml
security:
  require_checksum: true           # Always enforced (non-configurable)
  require_signature: false         # Require signed packages
  trusted_identities:              # Sigstore OIDC identities to trust
    - "*@myorg.com"
  trusted_keys:                    # GPG key fingerprints to trust
    - "ABCD1234..."
  on_signature_failure: warn       # warn | error | ignore
```

### 14.4 Lock File Integrity

The `package.agent.lock` stores SHA-256 hashes for every resolved package. On `--frozen` install, hashes are re-verified — any mismatch aborts with an error, preventing supply-chain tampering.

---

## 15. Governance & Policy Gates

Governance controls who can install what, and provides a tamper-evident record of actions. Policy gates are **client-side** (no server required); approval workflows require an HTTP registry.

### 15.1 Client-Side Policy Gates

Configured in `config.yaml`, enforced by the CLI **before** any install or publish:

```yaml
governance:
  install_policy:
    allowed_scopes: ["@myorg", "@trusted-vendor"] # only allow these scopes
    require_signature: true                        # block unsigned packages
    require_tag: "stable"                          # only install tagged versions
    blocked_packages: ["@sketchy/*"]               # glob-matched block list
  publish_policy:
    require_signature: true                        # must sign before publishing
```

| Gate | Trigger | Effect |
|------|---------|--------|
| `allowed_scopes` | `aam install` | Block packages outside listed scopes |
| `require_signature` | `aam install` | Block unsigned packages |
| `require_tag` | `aam install` | Only allow versions with a specific tag |
| `blocked_packages` | `aam install` | Block specific packages (glob patterns) |
| `require_signature` | `aam pkg publish` | Require signing before publish |

### 15.2 Approval Workflows (HTTP Registry)

When `require_approval: true` is set and publishing to an HTTP registry:

1. `aam pkg publish` → uploads with `approval_status: pending`
2. Approvers receive notification
3. Approver runs `aam approve @org/agent@1.2.0`
4. Only approved packages appear in search/install

### 15.3 Audit Events

Every registry mutation is logged immutably:

| Event | Description |
|-------|-------------|
| `package.publish` | New version published |
| `version.yank` | Version marked as yanked |
| `tag.set` | Dist-tag added or updated |
| `tag.remove` | Dist-tag removed |
| `version.approve` | Version approved |
| `version.reject` | Version rejected |
| `ownership.transfer` | Package ownership transferred |

---

## 16. Validation Rules

| Rule | Constraint |
|------|-----------|
| Package `name` | `[a-z0-9-]`, max 64 chars |
| Package `version` | Valid SemVer 2.0 |
| Skill `description` | Max 1024 chars, must describe WHAT + WHEN |
| SKILL.md body | Recommended < 5,000 tokens / 500 lines |
| Frontmatter | Valid YAML, no tabs |
| Scripts | Must be self-contained or document dependencies |
| Hook commands | Must handle JSON on stdin |
| File references | Forward slashes only, relative paths |
| Dependency versions | Valid SemVer range syntax (`^`, `~`, `>=`, exact) |
| Dependency graph | Must be acyclic — circular dependencies are an error |
| Peer dependencies | Must be satisfied by root or ancestor package |
| System dependencies | Pre-flight check must pass (or explicit `--skip-checks`) |
| Lock file integrity | Hash must match on `--frozen` install |
| Namespace uniqueness | No two skills with same `name` within a single package |
| Resolution overrides | `resolutions` entries must reference packages in the tree |

---

## 17. Security Considerations

1. **Only install packages from trusted sources** — skills can execute code and access the filesystem.
2. **Audit all scripts** before enabling — look for network calls, file access, and unexpected operations.
3. **Use `allowed-tools`** to restrict skill capabilities where possible.
4. **Hook commands** run as the user — apply least-privilege principles.
5. **MCP servers** should not expose secrets; use environment variable injection.
6. **Environment Variables**: Packages must explicitly declare required environment variables in the `env` manifest field. Host platforms should prompt users securely for these values rather than storing them in plaintext.
7. **Permissions Model**: Platforms should enforce the `permissions` manifest field, restricting filesystem, network, and shell access to declared scopes.
8. **Sandbox** untrusted packages before production deployment.
9. **Verify lock file integrity** — `package.agent.lock` hashes prevent supply-chain tampering.
10. **Run `aam audit`** regularly to check dependencies for known vulnerabilities.
11. **System dependency auto-install** never uses `sudo` without explicit `--allow-sudo` flag.
12. **Transitive dependencies** should be audited — `aam tree` reveals the full graph.

---

## 18. Glossary

| Term | Definition |
|------|-----------|
| **Prompt** | A parameterized markdown template with `{{variable}}` interpolation. Referenced by skills and agents. |
| **Skill** | A folder with `SKILL.md` that teaches an agent a specific capability. Model-invoked. |
| **Command** | A markdown prompt triggered by user typing `/name`. User-invoked. |
| **Agent** | A specialized persona definition with `agent.yaml` + `system-prompt.md`. Model or user-invoked. |
| **Rule** | Persistent context (coding standards, conventions). Applied by scope rules. |
| **Hook** | A shell command triggered by a lifecycle event. Always executed, zero token cost. |
| **MCP Server** | An external tool server using the Model Context Protocol. |
| **AGENTS.md** | Universal, freeform instruction file for any agent. |
| **Progressive Disclosure** | Loading strategy: metadata → instructions → resources, on-demand. |
| **Dependency** | Another agent package required for this package to function. |
| **Peer Dependency** | A package that must be provided by the host environment, not auto-installed. |
| **Optional Dependency** | A package that enhances functionality but isn't required. |
| **System Dependency** | An OS binary, runtime, or package-manager package required on the host. |
| **Lock File** | `package.agent.lock` — pins exact resolved versions for reproducible installs. |
| **Hoisting** | Flattening shared dependencies to the top of the install tree to reduce duplication. |
| **Resolution Override** | A `resolutions` entry that forces a specific version for a transitive dependency. |
| **Pre-flight Check** | Verification that system dependencies exist before package installation. |
| **SemVer** | Semantic Versioning 2.0 — `MAJOR.MINOR.PATCH` with defined compatibility rules. |
| **DAG** | Directed Acyclic Graph — the dependency tree structure. Cycles are forbidden. |
| **Permissions** | Declared scopes (fs, network, shell) that restrict what a package can do. |
| **Env** | Environment variables and secrets required by the package to function. |
| **Scope** | The `@org` namespace prefix in `@org/package-name` for organizational grouping. |
| **Archive** | A `.aam` gzipped tar file containing a distributable package. |
| **Bundle** | A pre-compiled, platform-specific archive requiring no install-time resolution. |
| **Dist-tag** | A named alias for a specific package version (e.g., `stable`, `bank-approved`). |
| **Policy Gate** | A client-side governance rule enforced before install or publish operations. |

---

## Appendix: Confidence Legend

| Level | Meaning | Example |
|-------|---------|---------|
| **Official** | Verified against vendor documentation | Hook event names, manifest schema |
| **Community** | Confirmed by multiple community sources | Pseudo-XML rule structure, Cursor RULE.md folders |
| **Inferred** | Derived from behavior or early previews | Parallel agent counts, some adoption claims |

Claims marked as Inferred should be validated before building production tooling.

---

## Appendix A: Comparison of Key Differences

| Aspect | Claude Code | Cursor |
|--------|------------|--------|
| Manifest location | `.claude-plugin/plugin.json` | `.cursor-plugin/plugin.json` |
| Rule format | `CLAUDE.md` (freeform) | `.mdc` / `RULE.md` (YAML frontmatter) |
| Rule scoping | File-based hierarchy | `globs`, `alwaysApply`, agent-decided |
| Hook config | `hooks/hooks.json` | `.cursor/hooks.json` |
| Hook events | `PreToolUse`, `PostToolUse`, `Stop`... | `beforeShellCommand`, `afterFileEdit`, `stop`... |
| Skill standard | agentskills.io (creator) | agentskills.io (adopter, v2.2+) |
| Commands | Native `commands/` dir | Via rules or skills |
| Sub-agents | Native `agents/` dir | Via rules or imported |
| Team rules | N/A (org-wide via API) | Dashboard-managed (Team/Enterprise) |
| Distribution | `/plugin marketplace`, npm, git | Plugin marketplace, git |
| Root variable | `${CLAUDE_PLUGIN_ROOT}` | Working directory relative |
| MCP config (plugin) | `.mcp.json` (leading dot) | `mcp.json` (no dot) |
| MCP config (project) | `.mcp.json` | `.cursor/mcp.json` |
| MCP config (global) | `~/.claude/.mcp.json` | `~/.cursor/mcp.json` |
| Instruction files | `CLAUDE.md` | `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` |
| Dependency resolution | N/A (no native resolver) | N/A (no native resolver) |
| System dep checks | Via skill `compatibility` field | N/A |
| Lock file | N/A | N/A |

---

*This specification is a living document. Contributions welcome at [github.com/spazyCZ/agent-package-manager](https://github.com/spazyCZ/agent-package-manager).*
