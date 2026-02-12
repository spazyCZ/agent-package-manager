# OpenAI Codex

## Overview

**OpenAI Codex** is OpenAI's code generation platform that powers tools like GitHub Copilot. Projects using Codex typically use an `AGENTS.md` file for agent and instruction definitions. AAM integrates with Codex by merging agents and instructions into `AGENTS.md` using marker-based sections, while deploying skills to `.codex/skills/` or `~/.codex/skills/`.

**Key features:**
- Native SKILL.md support
- Marker-based merging into `AGENTS.md`
- Preserves user-written content outside markers
- Project-level and user-level skill deployment
- Clean separation of AAM-managed vs manual content

## Deployment Mapping

| Artifact Type | Codex Location | Format | Merging |
|---------------|----------------|--------|---------|
| **Skill** | `.codex/skills/<fs-name>/` or `~/.codex/skills/<fs-name>/` | SKILL.md (as-is) | No |
| **Agent** | `AGENTS.md` | Markdown section | Yes (markers) |
| **Prompt** | `.codex/prompts/<fs-name>.md` | Markdown (as-is) | No |
| **Instruction** | `AGENTS.md` | Markdown section | Yes (markers) |

> **Note:** `<fs-name>` uses the double-hyphen convention for scoped packages: `@author/name` becomes `author--name`.

## Detailed Conversion Rules

### Skills

Skills are copied as-is to `.codex/skills/` or `~/.codex/skills/`. The entire skill directory structure is preserved.

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

**Deployed to (project scope):**

```
.codex/skills/author--asvc-report/
├── SKILL.md
├── scripts/
│   └── generate-report.py
├── references/
│   └── asvc-spec.md
└── assets/
    └── template.md
```

**Deployed to (user scope):**

```
~/.codex/skills/author--asvc-report/
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
  codex:
    skill_scope: project  # Deploy to .codex/skills/
    # OR
    skill_scope: user     # Deploy to ~/.codex/skills/
```

### Agents

Agents are merged into `AGENTS.md` as markdown sections with AAM markers. The system prompt content is included directly between markers.

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

**Merged into `AGENTS.md`:**

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

Prompts are copied as markdown files to `.codex/prompts/`.

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

**Deployed to** (`.codex/prompts/author--audit-finding.md`):

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

Instructions are merged into `AGENTS.md` as markdown sections with AAM markers.

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

**Merged into `AGENTS.md`:**

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

AAM uses HTML comment markers to manage sections in `AGENTS.md`:

```markdown
<!-- BEGIN AAM: artifact-name artifact-type -->
...content...
<!-- END AAM: artifact-name artifact-type -->
```

### How It Works

1. **First deployment:** If `AGENTS.md` doesn't exist, AAM creates it with AAM sections
2. **Subsequent deployments:** AAM finds existing markers and updates only the content between them
3. **User content preserved:** Any content outside AAM markers is never modified
4. **Undeploy:** AAM removes the entire marked section, including markers

### Example AGENTS.md

```markdown
# My Project Agents

This project uses AI agents for various development tasks.

## Custom Agent Instructions

Our team-specific agent configuration and guidelines...

<!-- BEGIN AAM: asvc-audit agent -->
# ASVC Compliance Auditor

You are an ASVC compliance auditor...
<!-- END AAM: asvc-audit agent -->

## Development Guidelines

Additional team guidelines that we wrote manually...

<!-- BEGIN AAM: python-standards instruction -->
# Python Coding Standards

- Use type hints on all functions...
<!-- END AAM: python-standards instruction -->

## Additional Resources

Links to internal documentation...
```

### Benefits

- **Coexistence:** AAM-managed and user-written content live together
- **Clean updates:** Re-deploying updates only AAM sections
- **Clear boundaries:** Easy to see what AAM manages vs what you wrote
- **Safe removal:** Undeploying removes only AAM sections
- **Standardized format:** Follows Codex conventions

## Platform-Specific Configuration

```yaml
# ~/.aam/config.yaml or .aam/config.yaml

platforms:
  codex:
    skill_scope: user                 # "project" or "user"
    merge_instructions: true          # Merge into AGENTS.md (default)
```

### Configuration Options

| Option | Values | Default | Description |
|--------|--------|---------|-------------|
| `skill_scope` | `project`, `user` | `user` | Where to deploy skills |
| `merge_instructions` | `true`, `false` | `true` | Whether to merge agents/instructions into AGENTS.md |

**skill_scope:**

- `project`: Deploy to `.codex/skills/` (project-specific)
- `user`: Deploy to `~/.codex/skills/` (available in all projects)

**merge_instructions:**

- `true`: Agents and instructions merge into `AGENTS.md` (recommended)
- `false`: Would deploy as separate files (not typical for Codex)

## Installation Example

Let's install the `@author/asvc-auditor` package and see how it deploys to Codex.

### Before Installation

```bash
# Check if AGENTS.md exists
cat AGENTS.md
# File might not exist or contains only user content

# Check .codex/ directory
ls -R .codex/
# Directory might not exist
```

### Install Package

```bash
# Configure Codex as active platform
aam config set active_platforms codex

# Install package
aam install @author/asvc-auditor
```

### After Installation

**AGENTS.md** (created or updated):

```markdown
# My Project

Custom project description and agent instructions...

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
├── AGENTS.md                        # Merged agents + instructions
├── .codex/
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

Deployed to codex:
  skill: author--asvc-report -> .codex/skills/author--asvc-report/
  skill: author--generic-auditor -> .codex/skills/author--generic-auditor/
  agent: asvc-audit -> AGENTS.md (merged)
  prompt: audit-finding -> .codex/prompts/author--audit-finding.md
  prompt: audit-summary -> .codex/prompts/author--audit-summary.md
  instruction: python-standards -> AGENTS.md (merged)

Successfully installed @author/asvc-auditor@1.0.0
```

## Verification

After deployment, verify that artifacts are correctly placed:

### Check AGENTS.md

```bash
# View AGENTS.md
cat AGENTS.md

# Should contain AAM markers:
# <!-- BEGIN AAM: asvc-audit agent -->
# <!-- END AAM: asvc-audit agent -->
# <!-- BEGIN AAM: python-standards instruction -->
# <!-- END AAM: python-standards instruction -->
```

### Check Markers

```bash
# Find all AAM markers
grep "BEGIN AAM" AGENTS.md

# Expected output:
# <!-- BEGIN AAM: asvc-audit agent -->
# <!-- BEGIN AAM: python-standards instruction -->
```

### Check Skills

```bash
# List deployed skills
ls .codex/skills/

# Expected output:
# author--asvc-report
# author--generic-auditor
```

### Check Prompts

```bash
# List deployed prompts
ls .codex/prompts/

# Expected output:
# author--audit-finding.md
# author--audit-summary.md
```

### Test in Codex

1. Codex automatically reads `AGENTS.md`
2. Skills in `.codex/skills/` (or `~/.codex/skills/`) are available
3. Prompts in `.codex/prompts/` can be referenced

## Tips & Best Practices

### Preserve User Content

**Always write your own content outside AAM markers:**

```markdown
# My Agent Configuration

<!-- Your custom instructions here -->

<!-- BEGIN AAM: asvc-audit agent -->
...AAM-managed content...
<!-- END AAM: asvc-audit agent -->

<!-- More custom instructions here -->
```

**Never edit content between markers:**

AAM will overwrite any manual changes inside markers on the next deployment.

### Organize AGENTS.md

Structure your `AGENTS.md` logically:

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

### User-Level vs Project-Level Skills

**Project-level skills:**

```yaml
platforms:
  codex:
    skill_scope: project
```

Use for skills specific to this project or team.

**User-level skills:**

```yaml
platforms:
  codex:
    skill_scope: user
```

Use for skills you want available across all projects (e.g., personal utilities).

### Multiple Agents

You can have multiple agents in the same project:

```bash
aam install @author/asvc-auditor
aam install @author/code-reviewer
aam install @author/doc-writer
```

Each agent gets its own marked section in `AGENTS.md`:

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

Codex can access skills in `.codex/skills/` or `~/.codex/skills/` by referencing them in `AGENTS.md`:

```markdown
When auditing code, use the asvc-report skill located in .codex/skills/author--asvc-report/.
```

### Backup AGENTS.md

Before major updates, backup your `AGENTS.md`:

```bash
cp AGENTS.md AGENTS.md.backup
```

AAM should never touch content outside markers, but it's good practice.

## Troubleshooting

### AGENTS.md Not Created

**Symptom:** `aam install` succeeds but `AGENTS.md` doesn't exist.

**Cause:** No agents or instructions in the package.

**Solution:**

Check what was deployed:

```bash
aam list

# If only skills/prompts are deployed, AGENTS.md won't be created
```

### Markers Appear in Codex Output

**Symptom:** HTML comments visible in Codex's responses.

**Cause:** This is expected - HTML comments are standard markdown.

**Solution:** Codex typically ignores HTML comments. If they're visible, it's a display issue, not a deployment issue.

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
# Edit AGENTS.md and remove duplicate marker pairs
nano AGENTS.md
```

### Skills Not Found

**Symptom:** Codex can't find skills in `.codex/skills/` or `~/.codex/skills/`.

**Cause:** Path mismatch or skill not deployed.

**Solutions:**

1. **Check skill location:**
   ```bash
   ls .codex/skills/
   ls ~/.codex/skills/
   ```

2. **Verify SKILL.md exists:**
   ```bash
   cat .codex/skills/author--asvc-report/SKILL.md
   ```

3. **Check skill scope configuration:**
   ```bash
   aam config get platforms.codex.skill_scope
   ```

4. **Redeploy:**
   ```bash
   aam deploy --platform codex
   ```

### Wrong Deployment Location

**Symptom:** Skills deploy to wrong location.

**Solution:**

```bash
# Set skill scope
aam config set platforms.codex.skill_scope project  # or "user"

# Re-deploy
aam deploy --platform codex
```

### Cannot Undeploy

**Symptom:** `aam undeploy` fails to remove markers.

**Cause:** Markers manually edited or deleted.

**Solution:**

Manually remove AAM sections from `AGENTS.md`:

```bash
# Edit AGENTS.md and remove:
# <!-- BEGIN AAM: artifact-name artifact-type -->
# ...content...
# <!-- END AAM: artifact-name artifact-type -->
nano AGENTS.md
```

## Next Steps

- [Platform Overview](index.md) - Compare all platforms
- [Claude Desktop](claude.md) - Similar marker-based platform
- [Configuration: Codex](../configuration/platforms.md#codex) - Detailed configuration reference
- [Tutorial: Install a Package](../tutorials/install-package.md) - Hands-on installation guide
- [Concepts: Platform Adapters](../concepts/platform-adapters.md) - Deep dive into adapter architecture
