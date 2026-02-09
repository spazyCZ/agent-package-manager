# Claude Desktop

## Overview

**Claude Desktop** is Anthropic's AI assistant application. Projects using Claude Desktop use a `CLAUDE.md` file for project-specific instructions. AAM integrates with Claude by merging agents and instructions into `CLAUDE.md` using marker-based sections, while deploying skills and prompts to the `.claude/` directory.

**Key features:**
- Marker-based merging into `CLAUDE.md`
- Preserves user-written content outside markers
- Native SKILL.md support
- Clean separation of AAM-managed vs manual content
- Project-based instruction organization

## Deployment Mapping

| Artifact Type | Claude Location | Format | Merging |
|---------------|----------------|--------|---------|
| **Skill** | `.claude/skills/<fs-name>/SKILL.md` | SKILL.md (as-is) | No |
| **Agent** | `CLAUDE.md` | Markdown section | Yes (markers) |
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

Agents are merged into `CLAUDE.md` as markdown sections with AAM markers. The system prompt content is included directly between markers.

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

**Merged into `CLAUDE.md`:**

```markdown
<!-- BEGIN AAM: asvc-audit agent -->
# ASVC Compliance Auditor

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
<!-- END AAM: asvc-audit agent -->
```

**Conversion rules:**
1. Content wrapped in `<!-- BEGIN AAM: ... -->` and `<!-- END AAM: ... -->` markers
2. Marker includes artifact name and type (e.g., `asvc-audit agent`)
3. System prompt content included directly
4. Skills and prompts listed as references
5. No YAML frontmatter in merged content

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
| `merge_instructions` | `true`, `false` | `true` | Whether to merge agents/instructions into CLAUDE.md |

**merge_instructions:**

- `true`: Agents and instructions merge into `CLAUDE.md` (recommended)
- `false`: Would deploy as separate files (not typical for Claude)

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

**CLAUDE.md** (created or updated):

```markdown
# My Project

This is my custom project description...

<!-- BEGIN AAM: asvc-audit agent -->
# ASVC Compliance Auditor

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
<!-- END AAM: asvc-audit agent -->

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
├── CLAUDE.md                        # Merged agents + instructions
├── .claude/
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
  agent: asvc-audit -> CLAUDE.md (merged)
  prompt: audit-finding -> .claude/prompts/author--audit-finding.md
  prompt: audit-summary -> .claude/prompts/author--audit-summary.md
  instruction: python-standards -> CLAUDE.md (merged)

Successfully installed @author/asvc-auditor@1.0.0
```

## Verification

After deployment, verify that artifacts are correctly placed:

### Check CLAUDE.md

```bash
# View CLAUDE.md
cat CLAUDE.md

# Should contain AAM markers:
# <!-- BEGIN AAM: asvc-audit agent -->
# <!-- END AAM: asvc-audit agent -->
# <!-- BEGIN AAM: python-standards instruction -->
# <!-- END AAM: python-standards instruction -->
```

### Check Markers

```bash
# Find all AAM markers
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

### Preserve User Content

**Always write your own content outside AAM markers:**

```markdown
# My Project Instructions

<!-- Your custom instructions here -->

<!-- BEGIN AAM: asvc-audit agent -->
...AAM-managed content...
<!-- END AAM: asvc-audit agent -->

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

## AAM Agents
<!-- BEGIN AAM: agent1 agent -->
...
<!-- END AAM: agent1 agent -->

<!-- BEGIN AAM: agent2 agent -->
...
<!-- END AAM: agent2 agent -->

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

Each agent gets its own marked section in `CLAUDE.md`:

```markdown
<!-- BEGIN AAM: asvc-audit agent -->
...
<!-- END AAM: asvc-audit agent -->

<!-- BEGIN AAM: code-reviewer agent -->
...
<!-- END AAM: code-reviewer agent -->

<!-- BEGIN AAM: doc-writer agent -->
...
<!-- END AAM: doc-writer agent -->
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

**Cause:** No agents or instructions in the package.

**Solution:**

Check what was deployed:

```bash
aam list

# If only skills/prompts are deployed, CLAUDE.md won't be created
```

### Markers Appear in Claude Output

**Symptom:** HTML comments visible in Claude's responses.

**Cause:** This is expected - HTML comments are standard markdown.

**Solution:** Claude typically ignores HTML comments. If they're visible, it's a display issue, not a deployment issue.

### Content Between Markers Disappears

**Symptom:** Manual edits inside AAM markers are lost.

**Cause:** AAM overwrites content between markers on deployment.

**Solution:**

Move your custom content outside AAM markers:

```markdown
<!-- Your custom content here -->

<!-- BEGIN AAM: asvc-audit agent -->
...AAM content...
<!-- END AAM: asvc-audit agent -->

<!-- More custom content here -->
```

### Duplicate Markers

**Symptom:** Multiple `<!-- BEGIN AAM: asvc-audit agent -->` sections.

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

**Symptom:** `aam undeploy` fails to remove markers.

**Cause:** Markers manually edited or deleted.

**Solution:**

Manually remove AAM sections from `CLAUDE.md`:

```bash
# Edit CLAUDE.md and remove:
# <!-- BEGIN AAM: artifact-name artifact-type -->
# ...content...
# <!-- END AAM: artifact-name artifact-type -->
```

## Next Steps

- [Platform Overview](index.md) - Compare all platforms
- [GitHub Copilot](copilot.md) - Similar marker-based platform
- [Configuration: Claude](../configuration/platforms.md#claude) - Detailed configuration reference
- [Tutorial: Install a Package](../tutorials/install-package.md) - Hands-on installation guide
- [Concepts: Platform Adapters](../concepts/platform-adapters.md) - Deep dive into adapter architecture
