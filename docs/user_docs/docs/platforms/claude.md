# Claude Desktop

## Overview

**Claude Desktop** is Anthropic's AI assistant application. Projects using Claude Desktop use a `CLAUDE.md` file for project-specific instructions and a `.claude/agents/` directory for custom subagents. AAM integrates with Claude by deploying agents as discrete files in `.claude/agents/`, merging instructions into `CLAUDE.md` using marker-based sections, and deploying skills and prompts to the `.claude/` directory.

**Key features:**
- Discrete agent files in `.claude/agents/`
- Marker-based merging of instructions into `CLAUDE.md`
- Preserves user-written content outside markers
- Native SKILL.md support
- Project-based instruction organization

## Deployment Mapping

| Artifact Type | Claude Location | Format | Merging |
|---------------|----------------|--------|---------|
| **Skill** | `.claude/skills/<fs-name>/SKILL.md` | SKILL.md (as-is) | No |
| **Agent** | `.claude/agents/<fs-name>.md` | Markdown file | No |
| **Prompt** | `.claude/prompts/<fs-name>.md` | Markdown (as-is) | No |
| **Instruction** | `CLAUDE.md` | Markdown section | Yes (markers) |

> **Note:** `<fs-name>` uses the double-hyphen convention for scoped packages: `@author/name` becomes `author--name`.

## Detailed Conversion Rules

### Skills

Skills are copied as-is to `.claude/skills/`. The entire skill directory structure is preserved.

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
.claude/skills/author--asvc-report/
├── SKILL.md
├── scripts/
│   └── generate-report.py
├── references/
│   └── asvc-spec.md
└── assets/
    └── template.md
```

### Agents

Agents are deployed as discrete `.md` files in `.claude/agents/`. Each agent gets its own file following Claude Code's [custom subagents convention](https://code.claude.com/docs/en/sub-agents).

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

**Deployed to** `.claude/agents/asvc-audit.md`:

```markdown
You are an ASVC compliance auditor. Your role is to analyze codebases,
configurations, and documentation against ASVC framework requirements.

## Core Responsibilities

- Identify compliance gaps against ASVC standards
- Generate structured audit findings
- Provide remediation recommendations
```

**Conversion rules:**
1. Each agent is a separate `.md` file in `.claude/agents/`
2. System prompt content written directly to the file
3. File naming: `<fs-name>.md`
4. Re-deploying overwrites the existing agent file
5. `CLAUDE.md` is not modified by agent deployments

### Prompts

Prompts are copied as markdown files to `.claude/prompts/`.

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

**Deployed to** (`.claude/prompts/author--audit-finding.md`):

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

### Instructions

Instructions are merged into `CLAUDE.md` as markdown sections with AAM markers.

**Source** (`instructions/python-standards.md`):

```markdown
---
name: python-standards
description: "Python coding standards"
scope: project
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

**Merged into `CLAUDE.md`:**

```markdown
<!-- BEGIN AAM: python-standards instruction -->
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
<!-- END AAM: python-standards instruction -->
```

## Marker-Based Merging

AAM uses HTML comment markers to manage sections in `CLAUDE.md`:

```markdown
<!-- BEGIN AAM: artifact-name artifact-type -->
...content...
<!-- END AAM: artifact-name artifact-type -->
```

### How It Works

1. **First deployment:** If `CLAUDE.md` doesn't exist, AAM creates it with AAM sections
2. **Subsequent deployments:** AAM finds existing markers and updates only the content between them
3. **User content preserved:** Any content outside AAM markers is never modified
4. **Undeploy:** AAM removes the entire marked section, including markers

### Example CLAUDE.md

```markdown
# Project: ASVC Compliance Tool

This project implements ASVC compliance auditing for software systems.

## Overview

Our custom project guidelines and architecture...

<!-- BEGIN AAM: asvc-audit agent -->
# ASVC Compliance Auditor

You are an ASVC compliance auditor...
<!-- END AAM: asvc-audit agent -->

## Our Team's Best Practices

Some team-specific instructions that we wrote manually...

<!-- BEGIN AAM: python-standards instruction -->
# Python Coding Standards

- Use type hints on all functions...
<!-- END AAM: python-standards instruction -->

## Additional Notes

More custom content...
```

### Benefits

- **Coexistence:** AAM-managed and user-written content live together
- **Clean updates:** Re-deploying updates only AAM sections
- **Clear boundaries:** Easy to see what AAM manages vs what you wrote
- **Safe removal:** Undeploying removes only AAM sections

## Platform-Specific Configuration

```yaml
# ~/.aam/config.yaml or .aam/config.yaml

platforms:
  claude:
    merge_instructions: true          # Merge into CLAUDE.md (default)
```

### Configuration Options

| Option | Values | Default | Description |
|--------|--------|---------|-------------|
| `merge_instructions` | `true`, `false` | `true` | Whether to merge instructions into CLAUDE.md |

**merge_instructions:**

- `true`: Instructions merge into `CLAUDE.md` (recommended)
- `false`: Would deploy instructions as separate files (not typical for Claude)

> **Note:** Agents are always deployed as discrete files in `.claude/agents/` regardless of this setting.

## Installation Example

Let's install the `@author/asvc-auditor` package and see how it deploys to Claude.

### Before Installation

```bash
# Check if CLAUDE.md exists
cat CLAUDE.md
# File might not exist or contains only user content

# Check .claude/ directory
ls -R .claude/
# Directory might not exist
```

### Install Package

```bash
# Configure Claude as active platform
aam config set active_platforms claude

# Install package
aam install @author/asvc-auditor
```

### After Installation

**CLAUDE.md** (instructions merged):

```markdown
# My Project

This is my custom project description...

<!-- BEGIN AAM: python-standards instruction -->
# Python Coding Standards

## Type Hints

- Use type hints on all functions
- Import from `typing` for complex types

## Style

- Follow PEP 8 style guide
- Use 4 spaces for indentation
- Maximum line length: 88 characters
<!-- END AAM: python-standards instruction -->
```

**Directory structure:**

```
my-project/
├── CLAUDE.md                        # Instructions (marker-based)
├── .claude/
│   ├── agents/
│   │   └── asvc-audit.md           # Agent file
│   ├── skills/
│   │   ├── author--asvc-report/
│   │   │   ├── SKILL.md
│   │   │   ├── scripts/
│   │   │   └── references/
│   │   └── author--generic-auditor/
│   │       └── SKILL.md
│   └── prompts/
│       ├── author--audit-finding.md
│       └── author--audit-summary.md
└── .aam/
    ├── packages/
    └── aam-lock.yaml
```

### Installation Output

```
Installing @author/asvc-auditor...

Resolved dependencies:
  @author/asvc-auditor@1.0.0
  └── @author/generic-auditor@0.5.0

Downloaded 2 packages (145 KB)

Deployed to claude:
  skill: author--asvc-report -> .claude/skills/author--asvc-report/
  skill: author--generic-auditor -> .claude/skills/author--generic-auditor/
  agent: asvc-audit -> .claude/agents/asvc-audit.md
  prompt: audit-finding -> .claude/prompts/author--audit-finding.md
  prompt: audit-summary -> .claude/prompts/author--audit-summary.md
  instruction: python-standards -> CLAUDE.md (merged)

Successfully installed @author/asvc-auditor@1.0.0
```

## Verification

After deployment, verify that artifacts are correctly placed:

### Check Agents

```bash
# List deployed agents
ls .claude/agents/

# Expected output:
# asvc-audit.md
```

### Check CLAUDE.md

```bash
# View CLAUDE.md (instructions only)
cat CLAUDE.md

# Should contain instruction markers:
# <!-- BEGIN AAM: python-standards instruction -->
# <!-- END AAM: python-standards instruction -->
```

### Check Markers

```bash
# Find all AAM markers in CLAUDE.md
grep "BEGIN AAM" CLAUDE.md

# Expected output:
# <!-- BEGIN AAM: asvc-audit agent -->
# <!-- BEGIN AAM: python-standards instruction -->
```

### Check Skills

```bash
# List deployed skills
ls .claude/skills/

# Expected output:
# author--asvc-report
# author--generic-auditor
```

### Check Prompts

```bash
# List deployed prompts
ls .claude/prompts/

# Expected output:
# author--audit-finding.md
# author--audit-summary.md
```

### Test in Claude Desktop

1. Open project in Claude Desktop
2. Claude automatically reads `CLAUDE.md`
3. Skills in `.claude/skills/` are available
4. Prompts in `.claude/prompts/` can be referenced

## Tips & Best Practices

### Preserve User Content in CLAUDE.md

**Always write your own content outside AAM markers:**

```markdown
# My Project Instructions

<!-- Your custom instructions here -->

<!-- BEGIN AAM: python-standards instruction -->
...AAM-managed content...
<!-- END AAM: python-standards instruction -->

<!-- More custom instructions here -->
```

**Never edit content between markers:**

AAM will overwrite any manual changes inside markers on the next deployment.

### Organize CLAUDE.md

Structure your `CLAUDE.md` logically:

```markdown
# Project: My Application

## Overview
Project description...

## AAM Instructions
<!-- BEGIN AAM: standards1 instruction -->
...
<!-- END AAM: standards1 instruction -->

## Custom Instructions
Your team's specific guidelines...
```

### Multiple Agents

You can have multiple agents in the same project:

```bash
aam install @author/asvc-auditor
aam install @author/code-reviewer
aam install @author/doc-writer
```

Each agent gets its own file in `.claude/agents/`:

```
.claude/agents/
├── asvc-audit.md
├── code-reviewer.md
└── doc-writer.md
```

### Skill References

Claude can access skills in `.claude/skills/` by referencing them in instructions:

```markdown
When auditing code, use the asvc-report skill located in .claude/skills/author--asvc-report/.
```

### Backup CLAUDE.md

Before major updates, backup your `CLAUDE.md`:

```bash
cp CLAUDE.md CLAUDE.md.backup
```

AAM should never touch content outside markers, but it's good practice.

## Troubleshooting

### CLAUDE.md Not Created

**Symptom:** `aam install` succeeds but `CLAUDE.md` doesn't exist.

**Cause:** No instructions in the package (agents go to `.claude/agents/`, not `CLAUDE.md`).

**Solution:**

Check what was deployed:

```bash
aam list

# If only skills/prompts/agents are deployed, CLAUDE.md won't be created
# CLAUDE.md is only created when instructions are deployed
```

### Markers Appear in Claude Output

**Symptom:** HTML comments visible in Claude's responses.

**Cause:** This is expected - HTML comments are standard markdown.

**Solution:** Claude typically ignores HTML comments. If they're visible, it's a display issue, not a deployment issue.

### Content Between Markers Disappears

**Symptom:** Manual edits inside AAM instruction markers are lost.

**Cause:** AAM overwrites content between markers on deployment.

**Solution:**

Move your custom content outside AAM markers:

```markdown
<!-- Your custom content here -->

<!-- BEGIN AAM: python-standards instruction -->
...AAM content...
<!-- END AAM: python-standards instruction -->

<!-- More custom content here -->
```

### Duplicate Markers

**Symptom:** Multiple `<!-- BEGIN AAM: python-standards instruction -->` sections.

**Cause:** Manual duplication or AAM deployment bug.

**Solution:**

Manually remove duplicate sections, keeping only one:

```bash
# Edit CLAUDE.md and remove duplicate marker pairs
nano CLAUDE.md
```

### Skills Not Found

**Symptom:** Claude can't find skills in `.claude/skills/`.

**Cause:** Path mismatch or skill not deployed.

**Solutions:**

1. **Check skill location:**
   ```bash
   ls .claude/skills/
   ```

2. **Verify SKILL.md exists:**
   ```bash
   cat .claude/skills/author--asvc-report/SKILL.md
   ```

3. **Redeploy:**
   ```bash
   aam deploy --platform claude
   ```

### Cannot Undeploy

**Symptom:** `aam undeploy` fails to remove an artifact.

**Cause:** File or markers manually edited or deleted.

**Solution:**

For agents, manually delete the file:

```bash
rm .claude/agents/artifact-name.md
```

For instructions, manually remove AAM sections from `CLAUDE.md`:

```bash
# Edit CLAUDE.md and remove:
# <!-- BEGIN AAM: artifact-name instruction -->
# ...content...
# <!-- END AAM: artifact-name instruction -->
```

## Next Steps

- [Platform Overview](index.md) - Compare all platforms
- [GitHub Copilot](copilot.md) - Similar marker-based platform
- [Configuration: Project config](../configuration/project.md) - Platform settings
- [Getting Started: Quick Start](../getting-started/quickstart.md) - Hands-on installation guide
- [Concepts: Platform Adapters](../concepts/platform-adapters.md) - Deep dive into adapter architecture
