# GitHub Copilot

## Overview

**GitHub Copilot** is GitHub's AI pair programming tool. It supports custom agents via `.github/agents/*.agent.md`, conditional instructions via `.github/instructions/*.instructions.md`, and reusable prompts via `.github/prompts/`. AAM integrates with Copilot by deploying discrete files into the `.github/` directory structure.

**Key features:**
- Discrete agent files in `.github/agents/`
- Conditional instruction files in `.github/instructions/`
- SKILL.md support in `.github/skills/`
- GitHub-native directory structure
- Prompt files in `.github/prompts/`

## Deployment Mapping

| Artifact Type | Copilot Location | Format | Merging |
|---------------|-----------------|--------|---------|
| **Skill** | `.github/skills/<fs-name>/SKILL.md` | SKILL.md (as-is) | No |
| **Agent** | `.github/agents/<fs-name>.agent.md` | Markdown file | No |
| **Prompt** | `.github/prompts/<fs-name>.md` | Markdown (as-is) | No |
| **Instruction** | `.github/instructions/<fs-name>.instructions.md` | Markdown file | No |

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

Agents are deployed as discrete `.agent.md` files in `.github/agents/`. Each agent gets its own file following Copilot's [custom agents convention](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/create-custom-agents).

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

**Deployed to** `.github/agents/asvc-audit.agent.md`:

```markdown
You are an ASVC compliance auditor. Your role is to analyze codebases,
configurations, and documentation against ASVC framework requirements.

## Core Responsibilities

- Identify compliance gaps against ASVC standards
- Generate structured audit findings
- Provide remediation recommendations
```

**Conversion rules:**
1. Each agent is a separate `.agent.md` file in `.github/agents/`
2. System prompt content written directly to the file
3. File naming: `<fs-name>.agent.md`
4. Re-deploying overwrites the existing agent file

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

Instructions are deployed as discrete `.instructions.md` files in `.github/instructions/`. This follows Copilot's [custom instructions convention](https://code.visualstudio.com/docs/copilot/customization/custom-instructions), which supports conditional application via glob patterns.

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

**Deployed to** `.github/instructions/python-standards.instructions.md`:

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

## File-Based Deployment

AAM deploys agents and instructions as discrete files in the `.github/` directory:

- **Agents:** `.github/agents/<name>.agent.md`
- **Instructions:** `.github/instructions/<name>.instructions.md`

### How It Works

1. **First deployment:** AAM creates the target directory and writes the file
2. **Subsequent deployments:** AAM overwrites the existing file with updated content
3. **Undeploy:** AAM deletes the file

### Example Directory Structure

```
.github/
├── agents/
│   └── asvc-audit.agent.md
├── instructions/
│   └── python-standards.instructions.md
├── skills/
│   └── author--asvc-report/
│       └── SKILL.md
├── prompts/
│   └── author--audit-finding.md
└── workflows/                    # Existing GitHub Actions (untouched)
    └── ci.yml
```

### Benefits

- **Discrete files:** Each agent and instruction is a separate file
- **Conditional instructions:** `.instructions.md` files support glob-based conditional application
- **GitHub-native:** Follows official Copilot directory conventions
- **Clean updates:** Re-deploying overwrites only the specific file
- **Easy management:** Standard file operations for adding/removing artifacts

## Platform-Specific Configuration

```yaml
# ~/.aam/config.yaml or .aam/config.yaml

platforms:
  copilot:
    enabled: true
```

### Configuration Options

| Option | Values | Default | Description |
|--------|--------|---------|-------------|
| `enabled` | `true`, `false` | `true` | Whether to deploy artifacts for Copilot |

## Installation Example

Let's install the `@author/asvc-auditor` package and see how it deploys to GitHub Copilot.

### Before Installation

```bash
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

**Directory structure:**

```
my-project/
├── .github/
│   ├── agents/
│   │   └── asvc-audit.agent.md      # Agent definition
│   ├── instructions/
│   │   └── python-standards.instructions.md  # Instruction file
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
  agent: asvc-audit -> .github/agents/asvc-audit.agent.md
  prompt: audit-finding -> .github/prompts/author--audit-finding.md
  prompt: audit-summary -> .github/prompts/author--audit-summary.md
  instruction: python-standards -> .github/instructions/python-standards.instructions.md

Successfully installed @author/asvc-auditor@1.0.0
```

## Verification

After deployment, verify that artifacts are correctly placed:

### Check Agents

```bash
# List deployed agents
ls .github/agents/

# Expected output:
# asvc-audit.agent.md
```

### Check Instructions

```bash
# List deployed instructions
ls .github/instructions/

# Expected output:
# python-standards.instructions.md
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
3. Copilot automatically reads `.github/agents/` and `.github/instructions/`
4. Test Copilot suggestions reflect the deployed instructions

## Tips & Best Practices

### GitHub Integration

Copilot's `.github/` directory coexists with other GitHub features:

```
.github/
├── agents/                     # AAM-deployed agents
│   └── asvc-audit.agent.md
├── instructions/               # AAM-deployed instructions
│   └── python-standards.instructions.md
├── skills/                     # AAM-deployed skills
├── prompts/                    # AAM-deployed prompts
├── workflows/                  # GitHub Actions (unrelated to AAM)
│   ├── ci.yml
│   └── deploy.yml
├── CODEOWNERS                  # GitHub code ownership (unrelated)
└── pull_request_template.md   # PR templates (unrelated)
```

AAM only touches `agents/`, `instructions/`, `skills/`, and `prompts/`.

### Multiple Instruction Sets

Install multiple language-specific instructions:

```bash
aam install @standards/python
aam install @standards/typescript
aam install @standards/rust
```

Each gets its own file in `.github/instructions/`:

```
.github/instructions/
├── python-standards.instructions.md
├── typescript-standards.instructions.md
└── rust-standards.instructions.md
```

### Copilot Instruction Processing

GitHub Copilot reads `.github/instructions/` files and uses them to guide code suggestions. Instructions are most effective when:

- **Clear and specific:** Concrete rules work better than vague guidelines
- **Well-structured:** Use headings to organize by topic
- **Example-driven:** Include code examples where appropriate
- **Focused:** Instructions should be relevant to your project
- **Conditionally scoped:** Use `applyTo` frontmatter for file-type-specific instructions

## Troubleshooting

### Copilot Not Following Instructions

**Symptom:** Copilot suggestions don't reflect deployed instructions.

**Possible causes:**

1. **Copilot cache:** Copilot might cache instructions
2. **Content location:** Instructions must be in `.github/instructions/`
3. **Instruction clarity:** Vague instructions are harder for Copilot to follow

**Solutions:**

1. **Reload VS Code/IDE:**
   - Close and reopen VS Code
   - Or restart the Copilot extension

2. **Verify file locations:**
   ```bash
   ls -la .github/agents/
   ls -la .github/instructions/
   ```

3. **Check instruction clarity:**
   - Instructions should be clear and specific
   - Use concrete examples
   - Focus on actionable guidelines

### Skills Not Recognized

**Symptom:** Skills in `.github/skills/` not available in Copilot.

**Cause:** GitHub Copilot's skill support is experimental and may not be fully functional.

**Note:** Copilot's SKILL.md support is limited. AAM deploys skills to `.github/skills/` for future compatibility, but Copilot may not use them yet.

**Workaround:**

Reference skills in an instruction file in `.github/instructions/`:

```markdown
## Available Skills

Skills are located in `.github/skills/`:

- **asvc-report**: Generate ASVC audit reports
  - Location: `.github/skills/author--asvc-report/`
  - Usage: See SKILL.md for instructions
```

### Cannot Undeploy

**Symptom:** `aam undeploy` fails to remove an agent or instruction.

**Cause:** File may have been manually renamed or deleted.

**Solution:**

Manually delete the file:

```bash
# Remove agent file
rm .github/agents/artifact-name.agent.md

# Remove instruction file
rm .github/instructions/artifact-name.instructions.md
```

## Next Steps

- [Platform Overview](index.md) - Compare all platforms
- [Claude Desktop](claude.md) - Similar marker-based platform
- [Configuration: Project config](../configuration/project.md) - Platform settings
- [Getting Started: Quick Start](../getting-started/quickstart.md) - Hands-on installation guide
- [Concepts: Platform Adapters](../concepts/platform-adapters.md) - Deep dive into adapter architecture
