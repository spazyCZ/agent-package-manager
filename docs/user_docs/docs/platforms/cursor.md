# Cursor

## Overview

**Cursor** is an AI-powered code editor built on VSCode. It features native support for skills, rules, and prompts. AAM integrates with Cursor by deploying artifacts to the `.cursor/` directory, converting agents and instructions into Cursor's `.mdc` rule format.

**Key features:**
- Native SKILL.md support with script execution
- Rule-based agent and instruction configuration
- File-level and glob-based instruction scoping
- Separate file organization for each artifact
- Project-level and user-level skill deployment

## Deployment Mapping

| Artifact Type | Cursor Location | Format | Naming |
|---------------|----------------|--------|--------|
| **Skill** | `.cursor/skills/<fs-name>/` or `~/.cursor/skills/<fs-name>/` | SKILL.md (as-is) | `author--skill-name` |
| **Agent** | `.cursor/rules/agent-<fs-name>.mdc` | Converted to rule | `agent-author--agent-name.mdc` |
| **Prompt** | `.cursor/prompts/<fs-name>.md` | Markdown (as-is) | `author--prompt-name.md` |
| **Instruction** | `.cursor/rules/<fs-name>.mdc` | Converted to `.mdc` rule | `author--instruction-name.mdc` |

> **Note:** `<fs-name>` uses the double-hyphen convention for scoped packages: `@author/name` becomes `author--name`.

## Detailed Conversion Rules

### Skills

Skills are copied as-is to `.cursor/skills/`. The entire skill directory structure is preserved.

**Source structure:**

```
.aam/packages/author--asvc-report/1.0.0/skills/asvc-report/
├── SKILL.md
├── scripts/
│   └── generate-report.py
├── references/
│   └── asvc-spec.md
└── assets/
    └── template.md
```

**Deployed to:**

```
.cursor/skills/author--asvc-report/
├── SKILL.md
├── scripts/
│   └── generate-report.py
├── references/
│   └── asvc-spec.md
└── assets/
    └── template.md
```

**Configuration:**

```yaml
platforms:
  cursor:
    skill_scope: project  # Deploy to .cursor/skills/
    # OR
    skill_scope: user     # Deploy to ~/.cursor/skills/
```

### Agents

Agents are converted to Cursor rules with `alwaysApply: true`. The system prompt, skill references, and prompt references are combined into a single `.mdc` file.

**Source** (`agents/asvc-audit/`):

```yaml
# agent.yaml
name: asvc-audit
description: "ASVC compliance auditor"
version: 1.0.0
system_prompt: system-prompt.md
skills:
  - asvc-report
  - generic-auditor
prompts:
  - audit-finding
  - audit-summary
```

```markdown
<!-- system-prompt.md -->
You are an ASVC compliance auditor. Your role is to analyze codebases,
configurations, and documentation against ASVC framework requirements.

## Core Responsibilities

- Identify compliance gaps against ASVC standards
- Generate structured audit findings
- Provide remediation recommendations
```

**Deployed to** (`.cursor/rules/agent-author--asvc-audit.mdc`):

```markdown
---
description: "ASVC compliance auditor"
alwaysApply: true
---

# Agent: asvc-audit

You are an ASVC compliance auditor. Your role is to analyze codebases,
configurations, and documentation against ASVC framework requirements.

## Core Responsibilities

- Identify compliance gaps against ASVC standards
- Generate structured audit findings
- Provide remediation recommendations

## Available Skills

- asvc-report: Generate ASVC audit reports
- generic-auditor: General-purpose code auditing

## Available Prompts

- audit-finding: Use for documenting individual findings
- audit-summary: Use for executive summaries
```

**Conversion rules:**
1. Frontmatter includes `description` and `alwaysApply: true`
2. System prompt content is included directly
3. Skills and prompts are listed as references
4. Agent name prefixes the filename: `agent-<fs-name>.mdc`

### Prompts

Prompts are copied as markdown files to `.cursor/prompts/`.

**Source** (`prompts/audit-finding.md`):

```markdown
---
name: audit-finding
description: "Template for documenting audit findings"
---

# Audit Finding: {finding_title}

## Severity
{severity}

## Description
{description}

## Evidence
{evidence}

## Recommendation
{recommendation}
```

**Deployed to** (`.cursor/prompts/author--audit-finding.md`):

```markdown
---
name: audit-finding
description: "Template for documenting audit findings"
---

# Audit Finding: {finding_title}

## Severity
{severity}

## Description
{description}

## Evidence
{evidence}

## Recommendation
{recommendation}
```

Prompts are referenced by skills and agents but can also be used independently in Cursor.

### Instructions

Instructions are converted to Cursor rules with appropriate `globs` patterns for file scoping.

**Source** (`instructions/python-standards.md`):

```markdown
---
name: python-standards
description: "Python coding standards"
scope: project
globs: "**/*.py"
---

# Python Coding Standards

## Type Hints

- Use type hints on all functions
- Import from `typing` for complex types

## Style

- Follow PEP 8 style guide
- Use 4 spaces for indentation
- Maximum line length: 88 characters

## Documentation

- Docstrings for all public functions
- Use Google-style docstring format
```

**Deployed to** (`.cursor/rules/author--python-standards.mdc`):

```markdown
---
description: "Python coding standards"
globs: "**/*.py"
alwaysApply: false
---

# Python Coding Standards

## Type Hints

- Use type hints on all functions
- Import from `typing` for complex types

## Style

- Follow PEP 8 style guide
- Use 4 spaces for indentation
- Maximum line length: 88 characters

## Documentation

- Docstrings for all public functions
- Use Google-style docstring format
```

**Conversion rules:**
1. Frontmatter includes `description`, `globs`, and `alwaysApply`
2. `alwaysApply` is `false` if `globs` is specified, `true` otherwise
3. Instruction body is preserved as-is
4. No prefix added to filename: `<fs-name>.mdc`

## Platform-Specific Configuration

```yaml
# ~/.aam/config.yaml or .aam/config.yaml

platforms:
  cursor:
    skill_scope: project              # "project" or "user"
    deploy_instructions_as: rules     # Always "rules" (default)
```

### Configuration Options

| Option | Values | Default | Description |
|--------|--------|---------|-------------|
| `skill_scope` | `project`, `user` | `project` | Where to deploy skills |
| `deploy_instructions_as` | `rules` | `rules` | How to deploy instructions (always rules) |

**skill_scope:**

- `project`: Deploy to `.cursor/skills/` (project-specific)
- `user`: Deploy to `~/.cursor/skills/` (available in all projects)

## Installation Example

Let's install the `@author/asvc-auditor` package and see how it deploys to Cursor.

### Before Installation

```bash
# Check current project structure
ls -R .cursor/
# .cursor/ directory doesn't exist yet
```

### Install Package

```bash
# Configure Cursor as active platform
aam config set active_platforms cursor

# Install package
aam install @author/asvc-auditor
```

### After Installation

```
my-project/
├── .cursor/
│   ├── skills/
│   │   ├── author--asvc-report/
│   │   │   ├── SKILL.md
│   │   │   ├── scripts/
│   │   │   │   └── generate-report.py
│   │   │   └── references/
│   │   │       └── asvc-spec.md
│   │   └── author--generic-auditor/
│   │       └── SKILL.md
│   ├── rules/
│   │   ├── agent-author--asvc-audit.mdc
│   │   └── author--python-standards.mdc
│   └── prompts/
│       ├── author--audit-finding.md
│       └── author--audit-summary.md
└── .aam/
    ├── packages/
    │   └── author--asvc-auditor/
    │       └── 1.0.0/
    └── aam-lock.yaml
```

### Installation Output

```
Installing @author/asvc-auditor...

Resolved dependencies:
  @author/asvc-auditor@1.0.0
  └── @author/generic-auditor@0.5.0

Downloaded 2 packages (145 KB)

Deployed to cursor:
  skill: author--asvc-report -> .cursor/skills/author--asvc-report/
  skill: author--generic-auditor -> .cursor/skills/author--generic-auditor/
  agent: asvc-audit -> .cursor/rules/agent-author--asvc-audit.mdc
  prompt: audit-finding -> .cursor/prompts/author--audit-finding.md
  prompt: audit-summary -> .cursor/prompts/author--audit-summary.md
  instruction: python-standards -> .cursor/rules/author--python-standards.mdc

Successfully installed @author/asvc-auditor@1.0.0
```

## Verification

After deployment, verify that artifacts are correctly placed:

### Check Deployed Files

```bash
# List all deployed artifacts
ls -R .cursor/

# Expected output:
# .cursor/skills/:
# author--asvc-report  author--generic-auditor
#
# .cursor/rules/:
# agent-author--asvc-audit.mdc  author--python-standards.mdc
#
# .cursor/prompts/:
# author--audit-finding.md  author--audit-summary.md
```

### Verify Skill Content

```bash
# Check skill SKILL.md
cat .cursor/skills/author--asvc-report/SKILL.md

# Should show the skill definition with:
# - Skill name and description
# - Usage instructions
# - Dependencies
# - Scripts and references
```

### Verify Agent Rule

```bash
# Check agent rule
cat .cursor/rules/agent-author--asvc-audit.mdc

# Should show:
# - Frontmatter with description and alwaysApply: true
# - System prompt content
# - Available skills section
# - Available prompts section
```

### Verify Instruction Rule

```bash
# Check instruction rule
cat .cursor/rules/author--python-standards.mdc

# Should show:
# - Frontmatter with description, globs, and alwaysApply
# - Instruction content
```

### Test in Cursor

1. Open project in Cursor
2. Cursor automatically loads rules from `.cursor/rules/`
3. Skills are discoverable in Cursor's skill palette
4. Prompts are available for use in Cursor's prompt system

## Tips & Best Practices

### Skill Organization

**Project-specific skills:**

```yaml
platforms:
  cursor:
    skill_scope: project
```

Use for skills that are specific to this project or team.

**User-level skills:**

```yaml
platforms:
  cursor:
    skill_scope: user
```

Use for skills you want available across all projects (e.g., personal utilities).

### Rule Priority

Cursor applies rules in this order:
1. Always-apply rules (agents)
2. Glob-matched rules (instructions)
3. User-created rules

AAM agents use `alwaysApply: true`, so they're always active.

### Skill Discovery

Cursor automatically discovers skills in:
- `.cursor/skills/` (project)
- `~/.cursor/skills/` (user)

No additional configuration needed.

### Naming Conventions

AAM uses clear naming for deployed files:

- **Agents**: `agent-<name>.mdc` (e.g., `agent-author--asvc-audit.mdc`)
- **Instructions**: `<name>.mdc` (e.g., `author--python-standards.mdc`)
- **Skills**: `<name>/` (e.g., `author--asvc-report/`)
- **Prompts**: `<name>.md` (e.g., `author--audit-finding.md`)

This makes it easy to distinguish AAM-managed files from user-created files.

### Glob Patterns

Use glob patterns in instructions for file-specific rules:

```yaml
globs: "**/*.py"           # All Python files
globs: "src/**/*.ts"       # TypeScript files in src/
globs: "tests/**/*"        # All files in tests/
```

### Multiple Instructions

Deploy multiple instructions for different file types:

```bash
# Install language-specific instructions
aam install @author/python-standards
aam install @author/typescript-standards
aam install @author/rust-standards

# Each deploys as separate .mdc rule with appropriate globs
```

## Troubleshooting

### Skills Not Appearing in Cursor

**Symptom:** Skills are deployed but not visible in Cursor.

**Solutions:**

1. **Reload Cursor window:**
   - Command Palette > "Reload Window"

2. **Check skill scope:**
   ```bash
   # If using user scope, skills should be in ~/.cursor/skills/
   aam config get platforms.cursor.skill_scope
   ```

3. **Verify SKILL.md exists:**
   ```bash
   ls .cursor/skills/*/SKILL.md
   ```

### Rules Not Applying

**Symptom:** Agents or instructions don't seem active.

**Solutions:**

1. **Check rule syntax:**
   ```bash
   cat .cursor/rules/agent-author--asvc-audit.mdc
   ```

   Ensure frontmatter is valid YAML with `---` delimiters.

2. **Check alwaysApply:**
   ```yaml
   ---
   alwaysApply: true  # Should be true for agents
   ---
   ```

3. **Check glob patterns:**
   ```yaml
   ---
   globs: "**/*.py"  # Should match your file types
   alwaysApply: false
   ---
   ```

### Wrong Deployment Location

**Symptom:** Skills deploy to `~/.cursor/` instead of `.cursor/`.

**Solution:**

```bash
# Set project scope
aam config set platforms.cursor.skill_scope project

# Re-deploy
aam deploy --platform cursor
```

### Scoped Package Names Not Resolving

**Symptom:** Package `@author/name` deploys to wrong location.

**Cause:** AAM automatically converts scoped names to filesystem-safe names.

**Expected behavior:**

```
@author/asvc-report -> author--asvc-report/
```

This is correct and intentional.

### Cannot Undeploy

**Symptom:** `aam undeploy` fails to remove artifacts.

**Solution:**

```bash
# Undeploy specific package
aam undeploy @author/asvc-auditor --platform cursor

# Or manually remove files
rm -rf .cursor/skills/author--asvc-report/
rm .cursor/rules/agent-author--asvc-audit.mdc
```

## Next Steps

- [Platform Overview](index.md) - Compare all platforms
- [Configuration: Cursor](../configuration/platforms.md#cursor) - Detailed configuration reference
- [Tutorial: Install a Package](../tutorials/install-package.md) - Hands-on installation guide
- [Concepts: Platform Adapters](../concepts/platform-adapters.md) - Deep dive into adapter architecture
