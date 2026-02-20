# GitHub Copilot

## Overview

**GitHub Copilot** is GitHub's AI pair programming tool. It uses `.github/copilot-instructions.md` for project-specific instructions and coding guidelines. AAM integrates with Copilot by merging agents and instructions into `copilot-instructions.md` using marker-based sections, while deploying skills and prompts to the `.github/` directory.

**Key features:**
- Marker-based merging into `copilot-instructions.md`
- Preserves user-written content outside markers
- SKILL.md support in `.github/skills/`
- GitHub-native directory structure
- Clean separation of AAM-managed vs manual content

## Deployment Mapping

| Artifact Type | Copilot Location | Format | Merging |
|---------------|-----------------|--------|---------|
| **Skill** | `.github/skills/<fs-name>/SKILL.md` | SKILL.md (as-is) | No |
| **Agent** | `.github/copilot-instructions.md` | Markdown section | Yes (markers) |
| **Prompt** | `.github/prompts/<fs-name>.md` | Markdown (as-is) | No |
| **Instruction** | `.github/copilot-instructions.md` | Markdown section | Yes (markers) |

> **Note:** `<fs-name>` uses the double-hyphen convention for scoped packages: `@author/name` becomes `author--name`.

## Detailed Conversion Rules

### Skills

Skills are copied as-is to `.github/skills/`. The entire skill directory structure is preserved.

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
.github/skills/author--asvc-report/
├── SKILL.md
├── scripts/
│   └── generate-report.py
├── references/
│   └── asvc-spec.md
└── assets/
    └── template.md
```

**Note:** GitHub Copilot has experimental support for SKILL.md files in `.github/skills/`.

### Agents

Agents are merged into `.github/copilot-instructions.md` as markdown sections with AAM markers. The system prompt content is included directly between markers.

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

**Merged into `.github/copilot-instructions.md`:**

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

Prompts are copied as markdown files to `.github/prompts/`.

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

**Deployed to** (`.github/prompts/author--audit-finding.md`):

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

Instructions are merged into `.github/copilot-instructions.md` as markdown sections with AAM markers.

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

**Merged into `.github/copilot-instructions.md`:**

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

AAM uses HTML comment markers to manage sections in `copilot-instructions.md`:

```markdown
<!-- BEGIN AAM: artifact-name artifact-type -->
...content...
<!-- END AAM: artifact-name artifact-type -->
```

### How It Works

1. **First deployment:** If `copilot-instructions.md` doesn't exist, AAM creates it with AAM sections
2. **Subsequent deployments:** AAM finds existing markers and updates only the content between them
3. **User content preserved:** Any content outside AAM markers is never modified
4. **Undeploy:** AAM removes the entire marked section, including markers

### Example copilot-instructions.md

```markdown
# Coding Guidelines for This Project

Our team follows these standards when writing code...

## General Principles

- Write clean, readable code
- Test thoroughly
- Document complex logic

<!-- BEGIN AAM: asvc-audit agent -->
# ASVC Compliance Auditor

You are an ASVC compliance auditor...
<!-- END AAM: asvc-audit agent -->

## Project-Specific Context

This is a compliance auditing tool built for enterprise clients...

<!-- BEGIN AAM: python-standards instruction -->
# Python Coding Standards

- Use type hints on all functions...
<!-- END AAM: python-standards instruction -->

## Additional Resources

- [Internal wiki](https://wiki.example.com)
- [Architecture docs](./docs/architecture.md)
```

### Benefits

- **Coexistence:** AAM-managed and user-written content live together
- **Clean updates:** Re-deploying updates only AAM sections
- **Clear boundaries:** Easy to see what AAM manages vs what you wrote
- **Safe removal:** Undeploying removes only AAM sections
- **GitHub integration:** Lives in `.github/` with other GitHub configs

## Platform-Specific Configuration

```yaml
# ~/.aam/config.yaml or .aam/config.yaml

platforms:
  copilot:
    merge_instructions: true          # Merge into copilot-instructions.md (default)
```

### Configuration Options

| Option | Values | Default | Description |
|--------|--------|---------|-------------|
| `merge_instructions` | `true`, `false` | `true` | Whether to merge agents/instructions into copilot-instructions.md |

**merge_instructions:**

- `true`: Agents and instructions merge into `copilot-instructions.md` (recommended)
- `false`: Would deploy as separate files (not typical for Copilot)

## Installation Example

Let's install the `@author/asvc-auditor` package and see how it deploys to GitHub Copilot.

### Before Installation

```bash
# Check if copilot-instructions.md exists
cat .github/copilot-instructions.md
# File might not exist or contains only user content

# Check .github/ directory
ls -R .github/
# Directory might not exist or contains only GitHub workflows
```

### Install Package

```bash
# Configure Copilot as active platform
aam config set active_platforms copilot

# Install package
aam install @author/asvc-auditor
```

### After Installation

**.github/copilot-instructions.md** (created or updated):

```markdown
# Project Instructions

This project implements ASVC compliance auditing...

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
├── .github/
│   ├── copilot-instructions.md      # Merged agents + instructions
│   ├── skills/
│   │   ├── author--asvc-report/
│   │   │   ├── SKILL.md
│   │   │   ├── scripts/
│   │   │   └── references/
│   │   └── author--generic-auditor/
│   │       └── SKILL.md
│   ├── prompts/
│   │   ├── author--audit-finding.md
│   │   └── author--audit-summary.md
│   └── workflows/                    # Existing GitHub Actions (untouched)
│       └── ci.yml
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

Deployed to copilot:
  skill: author--asvc-report -> .github/skills/author--asvc-report/
  skill: author--generic-auditor -> .github/skills/author--generic-auditor/
  agent: asvc-audit -> .github/copilot-instructions.md (merged)
  prompt: audit-finding -> .github/prompts/author--audit-finding.md
  prompt: audit-summary -> .github/prompts/author--audit-summary.md
  instruction: python-standards -> .github/copilot-instructions.md (merged)

Successfully installed @author/asvc-auditor@1.0.0
```

## Verification

After deployment, verify that artifacts are correctly placed:

### Check copilot-instructions.md

```bash
# View copilot-instructions.md
cat .github/copilot-instructions.md

# Should contain AAM markers:
# <!-- BEGIN AAM: asvc-audit agent -->
# <!-- END AAM: asvc-audit agent -->
# <!-- BEGIN AAM: python-standards instruction -->
# <!-- END AAM: python-standards instruction -->
```

### Check Markers

```bash
# Find all AAM markers
grep "BEGIN AAM" .github/copilot-instructions.md

# Expected output:
# <!-- BEGIN AAM: asvc-audit agent -->
# <!-- BEGIN AAM: python-standards instruction -->
```

### Check Skills

```bash
# List deployed skills
ls .github/skills/

# Expected output:
# author--asvc-report
# author--generic-auditor
```

### Check Prompts

```bash
# List deployed prompts
ls .github/prompts/

# Expected output:
# author--audit-finding.md
# author--audit-summary.md
```

### Test in GitHub Copilot

1. Open project in VS Code or your IDE
2. Ensure GitHub Copilot extension is installed
3. Copilot automatically reads `.github/copilot-instructions.md`
4. Test Copilot suggestions reflect the deployed instructions

## Tips & Best Practices

### Preserve User Content

**Always write your own content outside AAM markers:**

```markdown
# Our Team's Coding Guidelines

<!-- Your custom instructions here -->

<!-- BEGIN AAM: asvc-audit agent -->
...AAM-managed content...
<!-- END AAM: asvc-audit agent -->

<!-- More custom instructions here -->
```

**Never edit content between markers:**

AAM will overwrite any manual changes inside markers on the next deployment.

### GitHub Integration

Copilot's `.github/` directory coexists with other GitHub features:

```
.github/
├── copilot-instructions.md    # AAM-managed + custom instructions
├── skills/                     # AAM-deployed skills
├── prompts/                    # AAM-deployed prompts
├── workflows/                  # GitHub Actions (unrelated to AAM)
│   ├── ci.yml
│   └── deploy.yml
├── CODEOWNERS                  # GitHub code ownership (unrelated)
└── pull_request_template.md   # PR templates (unrelated)
```

AAM only touches `copilot-instructions.md`, `skills/`, and `prompts/`.

### Organize copilot-instructions.md

Structure your instructions logically:

```markdown
# Project Instructions

## Overview
Project description and general guidelines...

## AAM Agents
<!-- BEGIN AAM: agent1 agent -->
...
<!-- END AAM: agent1 agent -->

<!-- BEGIN AAM: agent2 agent -->
...
<!-- END AAM: agent2 agent -->

## AAM Coding Standards
<!-- BEGIN AAM: python-standards instruction -->
...
<!-- END AAM: python-standards instruction -->

<!-- BEGIN AAM: typescript-standards instruction -->
...
<!-- END AAM: typescript-standards instruction -->

## Team-Specific Guidelines
Your custom guidelines that aren't managed by AAM...
```

### Multiple Instruction Sets

Install multiple language-specific instructions:

```bash
aam install @standards/python
aam install @standards/typescript
aam install @standards/rust
```

Each gets its own marked section in `copilot-instructions.md`:

```markdown
<!-- BEGIN AAM: python-standards instruction -->
...Python guidelines...
<!-- END AAM: python-standards instruction -->

<!-- BEGIN AAM: typescript-standards instruction -->
...TypeScript guidelines...
<!-- END AAM: typescript-standards instruction -->

<!-- BEGIN AAM: rust-standards instruction -->
...Rust guidelines...
<!-- END AAM: rust-standards instruction -->
```

### Copilot Instruction Processing

GitHub Copilot reads `copilot-instructions.md` and uses it to guide code suggestions. Instructions are most effective when:

- **Clear and specific:** Concrete rules work better than vague guidelines
- **Well-structured:** Use headings to organize by topic
- **Example-driven:** Include code examples where appropriate
- **Focused:** Instructions should be relevant to your project

### Backup Before Major Changes

Before significant updates, backup your instructions:

```bash
cp .github/copilot-instructions.md .github/copilot-instructions.md.backup
```

AAM should never touch content outside markers, but it's good practice.

## Troubleshooting

### copilot-instructions.md Not Created

**Symptom:** `aam install` succeeds but `copilot-instructions.md` doesn't exist.

**Cause:** No agents or instructions in the package.

**Solution:**

Check what was deployed:

```bash
aam list

# If only skills/prompts are deployed, copilot-instructions.md won't be created
```

### Copilot Not Following Instructions

**Symptom:** Copilot suggestions don't reflect deployed instructions.

**Possible causes:**

1. **Copilot cache:** Copilot might cache instructions
2. **Content location:** Instructions must be in `.github/copilot-instructions.md`
3. **Instruction clarity:** Vague instructions are harder for Copilot to follow

**Solutions:**

1. **Reload VS Code/IDE:**
   - Close and reopen VS Code
   - Or restart the Copilot extension

2. **Verify file location:**
   ```bash
   ls -la .github/copilot-instructions.md
   ```

3. **Check instruction clarity:**
   - Instructions should be clear and specific
   - Use concrete examples
   - Focus on actionable guidelines

### Markers Appear in Copilot Context

**Symptom:** HTML comments visible in Copilot's context window.

**Cause:** This is expected - HTML comments are standard markdown.

**Solution:** Copilot typically ignores HTML comments. If they're affecting behavior, it's a Copilot issue, not AAM.

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
# Edit copilot-instructions.md and remove duplicate marker pairs
code .github/copilot-instructions.md
```

### Skills Not Recognized

**Symptom:** Skills in `.github/skills/` not available in Copilot.

**Cause:** GitHub Copilot's skill support is experimental and may not be fully functional.

**Note:** As of early 2024, Copilot's SKILL.md support is limited. AAM deploys skills to `.github/skills/` for future compatibility, but Copilot may not use them yet.

**Workaround:**

Reference skills in `copilot-instructions.md`:

```markdown
## Available Skills

Skills are located in `.github/skills/`:

- **asvc-report**: Generate ASVC audit reports
  - Location: `.github/skills/author--asvc-report/`
  - Usage: See SKILL.md for instructions
```

### Cannot Undeploy

**Symptom:** `aam undeploy` fails to remove markers.

**Cause:** Markers manually edited or deleted.

**Solution:**

Manually remove AAM sections from `copilot-instructions.md`:

```bash
# Edit and remove:
# <!-- BEGIN AAM: artifact-name artifact-type -->
# ...content...
# <!-- END AAM: artifact-name artifact-type -->
code .github/copilot-instructions.md
```

## Next Steps

- [Platform Overview](index.md) - Compare all platforms
- [Claude Desktop](claude.md) - Similar marker-based platform
- [Configuration: Project config](../configuration/project.md) - Platform settings
- [Getting Started: Quick Start](../getting-started/quickstart.md) - Hands-on installation guide
- [Concepts: Platform Adapters](../concepts/platform-adapters.md) - Deep dive into adapter architecture
