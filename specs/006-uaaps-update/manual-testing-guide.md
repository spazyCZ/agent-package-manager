# Manual Testing Guide: UAAPS v0.4.0

**Feature**: 006-uaaps-update
**Date**: 2026-02-21
**Audience**: QA / Developer performing manual validation

---

## Prerequisites

### Environment Setup

```bash
# 1. Navigate to the CLI project
cd apps/aam-cli

# 2. Install in editable mode (if not already)
pip install -e ".[dev]"

# 3. Verify the CLI is accessible
aam --version
# Expected: aam, version 0.1.0

# 4. Verify all commands are registered
aam --help
# Expected: all sections visible (Getting Started, Package Management, etc.)
```

### Create a Clean Workspace

For each test session, start with an isolated workspace:

```bash
# Create a fresh test workspace
mkdir -p /tmp/aam-test-workspace && cd /tmp/aam-test-workspace

# Clear any leftover state
rm -rf .agent-packages/ .aam/ package.agent.lock aam-lock.yaml
rm -rf .cursor/ .claude/ .github/ .codex/ CLAUDE.md AGENTS.md
```

---

## Part 1: Package Creator Workflows

### TC-C01: Scaffold a New Package (`aam pkg init`)

**Goal**: Verify that `pkg init` generates a valid `package.agent.json`.

```bash
cd /tmp/aam-test-workspace
mkdir tc-c01 && cd tc-c01

# Run init with a package name
aam pkg init my-test-skill
```

**Verify**:

- [ ] `package.agent.json` file is created (NOT `aam.yaml`)
- [ ] File is valid JSON — run: `python -m json.tool package.agent.json`
- [ ] Contains required fields: `name`, `version`, `description`, `author`, `artifacts`
- [ ] `name` matches "my-test-skill"
- [ ] `version` defaults to "0.1.0"
- [ ] Artifact directories are created: `skills/`, `agents/`, `prompts/`, `instructions/`

```bash
# Inspect the generated manifest
cat package.agent.json

# Validate the generated manifest
aam pkg validate .
```

- [ ] `aam pkg validate` reports the package as valid

---

### TC-C02: Scaffold a Scoped Package

```bash
cd /tmp/aam-test-workspace
mkdir tc-c02 && cd tc-c02

aam pkg init @myorg/code-review
```

**Verify**:

- [ ] `package.agent.json` is created
- [ ] `name` field is `"@myorg/code-review"`

---

### TC-C03: Migrate Legacy `aam.yaml` to `package.agent.json`

**Goal**: Verify backward-compatible migration.

```bash
cd /tmp/aam-test-workspace
mkdir tc-c03 && cd tc-c03

# Create a legacy aam.yaml
cat > aam.yaml << 'YAML'
name: legacy-pkg
version: 1.0.0
description: A legacy package
author: Test Author
artifacts:
  skills:
    - name: my-skill
      path: skills/my-skill/
      description: A test skill
  agents: []
  prompts: []
  instructions: []
dependencies: {}
platforms:
  cursor:
    skill_scope: project
    deploy_instructions_as: rules
YAML

# Create the artifact file
mkdir -p skills/my-skill
echo "# My Skill" > skills/my-skill/SKILL.md

# Run migration
aam pkg init --migrate
```

**Verify**:

- [ ] `package.agent.json` is created alongside `aam.yaml`
- [ ] JSON manifest contains the same package name, version, description
- [ ] Artifacts section is populated with the skill entry
- [ ] Run: `aam pkg validate .` — should pass

---

### TC-C04: Create Package from Existing Project (Auto-Detection)

**Goal**: Verify artifact scanning and package creation.

```bash
cd /tmp/aam-test-workspace
mkdir tc-c04 && cd tc-c04

# Simulate a Cursor project with artifacts
mkdir -p .cursor/skills/code-review
cat > .cursor/skills/code-review/SKILL.md << 'MD'
# Code Review Skill
Helps review code for quality and best practices.
MD

mkdir -p .cursor/rules
cat > .cursor/rules/python-style.mdc << 'MD'
---
applyTo: '**/*.py'
---
# Python Style Rules
Use type hints on all functions.
MD

mkdir -p .cursor/commands
cat > .cursor/commands/run-tests.md << 'MD'
# Run Tests
Execute the test suite for the current project.
MD

# Create a package from auto-detected artifacts
aam pkg create . --all --name my-cursor-pkg --version 1.0.0 --author "Tester" -y
```

**Verify**:

- [ ] CLI detects the skill, rule, and command artifacts
- [ ] `package.agent.json` is generated with all detected artifacts
- [ ] The `artifacts.skills` array contains "code-review"
- [ ] Run: `aam pkg validate .` (or the output directory)

---

### TC-C05: Create Package — Filter by Type

```bash
cd /tmp/aam-test-workspace/tc-c04

# Create with only skills
aam pkg create . --type skill --name skills-only --version 1.0.0 --author "Tester" -y --output-dir /tmp/aam-test-workspace/tc-c05
```

**Verify**:

- [ ] Only skills are included (no rules, commands, or prompts)
- [ ] Manifest `artifacts` section only has skill entries

---

### TC-C06: Create Package — Filter by Platform

```bash
cd /tmp/aam-test-workspace/tc-c04

# Create with only Cursor-detected artifacts
aam pkg create . --platform cursor --all --name cursor-only --version 1.0.0 --author "Tester" -y --output-dir /tmp/aam-test-workspace/tc-c06
```

**Verify**:

- [ ] Only Cursor-platform artifacts are included
- [ ] Artifacts from other platforms (e.g., `.github/prompts/`) are excluded

---

### TC-C07: Create Package — Dry Run

```bash
cd /tmp/aam-test-workspace/tc-c04

aam pkg create . --all --name dry-test --dry-run
```

**Verify**:

- [ ] CLI shows what would be created without writing any files
- [ ] No `package.agent.json` or artifact directories are created in the output

---

### TC-C08: Validate Package Manifest

```bash
cd /tmp/aam-test-workspace
mkdir tc-c08 && cd tc-c08

# Create a minimal valid package
cat > package.agent.json << 'JSON'
{
  "name": "valid-pkg",
  "version": "1.0.0",
  "description": "A valid package",
  "author": "Tester",
  "artifacts": {
    "skills": [
      {"name": "my-skill", "path": "skills/my-skill/", "description": "A skill"}
    ],
    "agents": [],
    "prompts": [],
    "instructions": []
  },
  "dependencies": {}
}
JSON

mkdir -p skills/my-skill
echo "# My Skill" > skills/my-skill/SKILL.md

aam pkg validate .
```

**Verify**:

- [ ] Reports "valid" or "1 artifact(s) verified" (or similar success message)

```bash
# Now test with a broken manifest (missing artifact path)
rm -rf skills/

aam pkg validate .
```

- [ ] Reports error about missing artifact path

---

### TC-C09: Create a Full Multi-Artifact Package

**Goal**: Build a realistic package containing all artifact types.

```bash
cd /tmp/aam-test-workspace
mkdir tc-c09 && cd tc-c09

# Scaffold the package
aam pkg init @test/full-package

# Create skill artifact
mkdir -p skills/code-review
cat > skills/code-review/SKILL.md << 'MD'
# Code Review Skill
Reviews code for quality, security, and performance.

## Triggers
- "review this code"
- "check for bugs"

## Steps
1. Read the file
2. Analyze for issues
3. Return findings
MD

# Create agent artifact
mkdir -p agents/qa-agent
cat > agents/qa-agent/agent.yaml << 'YAML'
name: qa-agent
description: Quality assurance agent
model: gpt-5
tools:
  - run-tests
  - lint-check
YAML

# Create prompt artifact
mkdir -p prompts
cat > prompts/summarize.md << 'MD'
# Summarize
Summarize the selected code in plain English.
MD

# Create instruction artifact
mkdir -p instructions
cat > instructions/security-rules.md << 'MD'
# Security Rules
- Never commit secrets to version control.
- Always validate user input.
- Use parameterized queries for database operations.
MD

# Create command artifact
mkdir -p commands
cat > commands/deploy-check.md << 'MD'
# Deploy Check
Verify the deployment readiness of the current project.
MD

# Create rule artifact
mkdir -p rules
cat > rules/naming-conventions.md << 'MD'
---
applyTo: '**/*.py'
---
# Naming Conventions
- Functions: snake_case
- Classes: PascalCase
- Constants: UPPER_CASE
MD

# Create hooks config
cat > hooks.json << 'JSON'
[
  {
    "event": "pre_tool_use",
    "command": "python scripts/validate_tool.py",
    "description": "Validate tool calls before execution"
  }
]
JSON

# Create MCP config
cat > mcp.json << 'JSON'
{
  "servers": {
    "my-db": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sqlite", "data.db"]
    }
  }
}
JSON
```

Now update the manifest to include all artifacts:

```bash
cat > package.agent.json << 'JSON'
{
  "name": "@test/full-package",
  "version": "1.0.0",
  "description": "A comprehensive test package with all artifact types",
  "author": "Test Author",
  "license": "MIT",
  "artifacts": {
    "skills": [
      {"name": "code-review", "path": "skills/code-review/", "description": "Reviews code"}
    ],
    "agents": [
      {"name": "qa-agent", "path": "agents/qa-agent/", "description": "QA agent"}
    ],
    "prompts": [
      {"name": "summarize", "path": "prompts/summarize.md", "description": "Summarize code"}
    ],
    "instructions": [
      {"name": "security-rules", "path": "instructions/security-rules.md", "description": "Security rules"}
    ],
    "commands": [
      {"name": "deploy-check", "path": "commands/deploy-check.md", "description": "Deploy check"}
    ],
    "rules": [
      {"name": "naming-conventions", "path": "rules/naming-conventions.md", "description": "Naming rules"}
    ],
    "hooks_path": "hooks.json",
    "mcp_path": "mcp.json"
  },
  "dependencies": {},
  "platforms": {
    "cursor": {
      "skill_scope": "project"
    }
  }
}
JSON

# Validate the full package
aam pkg validate .
```

**Verify**:

- [ ] Final directory tree looks like:

```
tc-c09/
├── package.agent.json
├── hooks.json
├── mcp.json
├── skills/
│   └── code-review/
│       └── SKILL.md
├── agents/
│   └── qa-agent/
│       └── agent.yaml
├── prompts/
│   └── summarize.md
├── instructions/
│   └── security-rules.md
├── commands/
│   └── deploy-check.md
└── rules/
    └── naming-conventions.md
```

- [ ] `aam pkg validate .` passes with all artifacts recognized

---

## Part 2: Package Consumer Workflows

### TC-P01: Install from Local Directory (Cursor Platform)

**Goal**: Verify the full install + deploy cycle on Cursor.

```bash
cd /tmp/aam-test-workspace
mkdir tc-p01 && cd tc-p01

# Install the full package from TC-C09
aam install /tmp/aam-test-workspace/tc-c09 --platform cursor
```

**Verify**:

- [ ] Package files are copied to `.agent-packages/@test/full-package/` (or `.aam/packages/`)
- [ ] Lock file is created: `aam-lock.yaml` or `package.agent.lock`
- [ ] Cursor deployment files are created:
  - [ ] `.cursor/skills/` — contains the deployed skill directory
  - [ ] `.cursor/rules/` — contains `.mdc` rule files
  - [ ] `.cursor/commands/` — contains command prompt files (if supported)
- [ ] No errors in CLI output

```bash
# List installed packages
aam list

# Verify package integrity
aam verify @test/full-package
```

- [ ] `aam list` shows `@test/full-package` as installed
- [ ] `aam verify` reports all files as intact

---

### TC-P02: Install from Local Directory (Claude Platform)

```bash
cd /tmp/aam-test-workspace
mkdir tc-p02 && cd tc-p02

aam install /tmp/aam-test-workspace/tc-c09 --platform claude
```

**Verify**:

- [ ] Package is installed
- [ ] Claude deployment files are created:
  - [ ] `CLAUDE.md` — contains embedded skill/agent/instruction marker sections
  - [ ] `.claude/commands/` — contains command files
  - [ ] `.mcp.json` — contains MCP server entries (if applicable)
  - [ ] `.claude/hooks.json` — contains hook entries (if applicable)
- [ ] `aam list` shows the package

---

### TC-P03: Install from Local Directory (Copilot Platform)

```bash
cd /tmp/aam-test-workspace
mkdir tc-p03 && cd tc-p03

aam install /tmp/aam-test-workspace/tc-c09 --platform copilot
```

**Verify**:

- [ ] Package is installed
- [ ] Copilot deployment files are created:
  - [ ] `.github/copilot-instructions.md` — instructions embedded
  - [ ] `.github/prompts/` — prompt files deployed
  - [ ] `.github/hooks/` — hook JSON files (PascalCase event names)
  - [ ] `.vscode/mcp.json` — MCP server entries
- [ ] Hook event names use PascalCase (e.g., `PreToolUse`, not `pre_tool_use`)

---

### TC-P04: Install from Local Directory (Codex Platform)

```bash
cd /tmp/aam-test-workspace
mkdir tc-p04 && cd tc-p04

aam install /tmp/aam-test-workspace/tc-c09 --platform codex
```

**Verify**:

- [ ] Package is installed
- [ ] Codex deployment files are created:
  - [ ] `AGENTS.md` — contains embedded skill/agent/instruction marker sections
  - [ ] `.codex/skills/` — skill directories deployed

---

### TC-P05: Install with `--no-deploy`

```bash
cd /tmp/aam-test-workspace
mkdir tc-p05 && cd tc-p05

aam install /tmp/aam-test-workspace/tc-c09 --no-deploy
```

**Verify**:

- [ ] Package files are downloaded/copied to the packages directory
- [ ] Lock file is updated
- [ ] **No** platform deployment files are created (no `.cursor/`, no `CLAUDE.md`, etc.)

---

### TC-P06: Install with `--dry-run`

```bash
cd /tmp/aam-test-workspace
mkdir tc-p06 && cd tc-p06

aam install /tmp/aam-test-workspace/tc-c09 --dry-run
```

**Verify**:

- [ ] CLI shows what would be installed
- [ ] **No** files are written to disk (no packages dir, no lock file, no platform files)

---

### TC-P07: Force Reinstall

```bash
cd /tmp/aam-test-workspace/tc-p01

# Already installed from TC-P01
# Try installing again without --force
aam install /tmp/aam-test-workspace/tc-c09 --platform cursor
```

**Verify**:

- [ ] CLI reports package is already installed (or skips)

```bash
# Now force reinstall
aam install /tmp/aam-test-workspace/tc-c09 --platform cursor --force
```

- [ ] CLI reinstalls the package, overwriting existing files

---

### TC-P08: Uninstall a Package

```bash
cd /tmp/aam-test-workspace/tc-p01

aam uninstall @test/full-package
```

**Verify**:

- [ ] Package directory is removed from `.agent-packages/`
- [ ] Lock file is updated (package entry removed)
- [ ] Platform deployment files are removed:
  - [ ] Cursor skills directory removed
  - [ ] Rule `.mdc` files removed
  - [ ] Command files removed
  - [ ] Hook entries removed
  - [ ] MCP entries removed
- [ ] `aam list` no longer shows the package

---

### TC-P09: Verify Package Integrity (Clean)

```bash
cd /tmp/aam-test-workspace
mkdir tc-p09 && cd tc-p09

# Install a package
aam install /tmp/aam-test-workspace/tc-c09 --platform cursor

# Verify integrity
aam verify @test/full-package
```

**Verify**:

- [ ] All files show checksum match — no modifications detected

---

### TC-P10: Verify Package Integrity (Tampered)

```bash
cd /tmp/aam-test-workspace/tc-p09

# Tamper with an installed file
echo "MODIFIED" >> .agent-packages/@test/full-package/skills/code-review/SKILL.md

# Re-verify
aam verify @test/full-package
```

**Verify**:

- [ ] CLI detects the modification and reports the changed file
- [ ] Exit code is non-zero

---

### TC-P11: Diff Modified Package

```bash
cd /tmp/aam-test-workspace/tc-p09

aam diff @test/full-package
```

**Verify**:

- [ ] Shows a unified diff for the modified `SKILL.md` file
- [ ] Unmodified files are not listed

---

## Part 3: Dependency & Lock File Workflows

### TC-D01: Dependency Tree Display

```bash
cd /tmp/aam-test-workspace
mkdir tc-d01 && cd tc-d01

# Create a lock file with a dependency tree
cat > package.agent.lock << 'JSON'
{
  "lockVersion": 2,
  "packages": {
    "@test/main-pkg": {
      "version": "1.0.0",
      "resolved": "local",
      "integrity": "sha256-abc123",
      "dependencies": {
        "utils-pkg": "^1.0.0"
      }
    },
    "utils-pkg": {
      "version": "1.2.0",
      "resolved": "local",
      "integrity": "sha256-def456",
      "dependencies": {}
    }
  }
}
JSON

aam tree
```

**Verify**:

- [ ] Displays a tree with `@test/main-pkg` as root
- [ ] Shows `utils-pkg` as a child dependency

```bash
# Test depth limiting
aam tree --depth 1
```

- [ ] Tree is limited to 1 level deep

---

### TC-D02: Why Is a Package Installed

```bash
cd /tmp/aam-test-workspace/tc-d01

aam why utils-pkg
```

**Verify**:

- [ ] Shows that `utils-pkg` is required by `@test/main-pkg`
- [ ] Displays the version constraint (`^1.0.0`)

---

### TC-D03: Check Installation Status

```bash
cd /tmp/aam-test-workspace/tc-d01

# Without actual package directories, check should report missing
mkdir -p .agent-packages/@test/main-pkg
# Don't create utils-pkg directory

aam check
```

**Verify**:

- [ ] `@test/main-pkg` shows OK
- [ ] `utils-pkg` shows FAIL (directory not found)

---

### TC-D04: Check System Dependencies

```bash
cd /tmp/aam-test-workspace
mkdir tc-d04 && cd tc-d04

# Create a lock file with system dependencies
cat > package.agent.lock << 'JSON'
{
  "lockVersion": 2,
  "packages": {
    "my-pkg": {
      "version": "1.0.0",
      "resolved": "local",
      "integrity": "sha256-abc",
      "dependencies": {},
      "systemDependencies": {
        "runtimes": {
          "python": ">=3.10",
          "node": ">=18"
        },
        "binaries": ["git", "curl"],
        "packages": {
          "pip": ["pytest"],
          "npm": ["typescript"]
        }
      }
    }
  }
}
JSON

mkdir -p .agent-packages/my-pkg

aam check --system
```

**Verify**:

- [ ] Python version check is shown (pass/fail based on local Python)
- [ ] Node version check is shown
- [ ] Binary checks for `git` and `curl` are shown
- [ ] pip package `pytest` is checked
- [ ] npm package `typescript` is checked

---

## Part 4: Platform Conversion Workflows

### TC-V01: Convert Cursor → Copilot

```bash
cd /tmp/aam-test-workspace
mkdir tc-v01 && cd tc-v01

# Create Cursor artifacts
mkdir -p .cursor/rules
cat > .cursor/rules/lint-rules.mdc << 'MD'
---
applyTo: '**/*.py'
---
# Lint Rules
Always use type hints.
MD

mkdir -p .cursor/skills/helper
echo "# Helper Skill" > .cursor/skills/helper/SKILL.md

# Convert
aam convert -s cursor -t copilot --dry-run
```

**Verify**:

- [ ] Shows what would be converted
- [ ] Instructions/rules would go to `.github/copilot-instructions.md`
- [ ] Skills would go to `.github/prompts/` area

```bash
# Now do it for real
aam convert -s cursor -t copilot
```

- [ ] Copilot files are created

---

### TC-V02: Convert Copilot → Claude

```bash
cd /tmp/aam-test-workspace
mkdir tc-v02 && cd tc-v02

# Create Copilot artifacts
mkdir -p .github/prompts
echo "# Review Prompt" > .github/prompts/review.md
echo "# Copilot Instructions" > .github/copilot-instructions.md

# Convert
aam convert -s copilot -t claude
```

**Verify**:

- [ ] `CLAUDE.md` is created with embedded instructions
- [ ] `.claude/commands/` contains prompt files (if applicable)

---

### TC-V03: Convert Hooks Between Platforms

```bash
cd /tmp/aam-test-workspace
mkdir tc-v03 && cd tc-v03

# Create Claude hooks
mkdir -p .claude
cat > .claude/hooks.json << 'JSON'
[
  {
    "event": "pre_tool_use",
    "command": "echo 'validating'",
    "description": "Pre-tool validation"
  }
]
JSON

# Convert to Copilot
aam convert -s claude -t copilot --type hooks --dry-run
```

**Verify**:

- [ ] Hook event name is translated from `pre_tool_use` to `PreToolUse` (PascalCase)
- [ ] Output would go to `.github/hooks/PreToolUse.json`

---

### TC-V04: Convert MCP Config Between Platforms

```bash
cd /tmp/aam-test-workspace
mkdir tc-v04 && cd tc-v04

# Create Claude MCP config
cat > .mcp.json << 'JSON'
{
  "mcpServers": {
    "sqlite": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sqlite", "data.db"]
    }
  }
}
JSON

# Convert to Cursor
aam convert -s claude -t cursor --type mcp --dry-run
```

**Verify**:

- [ ] Would create `.cursor/mcp.json` with the server entries
- [ ] JSON structure matches Cursor's expected format

---

## Part 5: Health & Diagnostics

### TC-H01: Doctor Command

```bash
cd /tmp/aam-test-workspace
mkdir tc-h01 && cd tc-h01

aam doctor
```

**Verify**:

- [ ] Reports Python version check
- [ ] Reports configuration status
- [ ] Reports installed packages status
- [ ] No unhandled exceptions

---

### TC-H02: Audit Installed Packages

```bash
cd /tmp/aam-test-workspace/tc-p09

aam audit
```

**Verify**:

- [ ] Scans installed packages for integrity issues
- [ ] Reports results in a table format

---

### TC-H03: Prune Orphaned Packages

```bash
cd /tmp/aam-test-workspace
mkdir tc-h03 && cd tc-h03

# Create a package directory without a lock file entry
mkdir -p .agent-packages/orphan-pkg
echo "orphan" > .agent-packages/orphan-pkg/README.md

# Create a lock file without that package
cat > package.agent.lock << 'JSON'
{
  "lockVersion": 2,
  "packages": {}
}
JSON

aam prune --dry-run
```

**Verify**:

- [ ] Reports `orphan-pkg` as pruneable
- [ ] Does not actually delete with `--dry-run`

```bash
aam prune
```

- [ ] `orphan-pkg` directory is removed
- [ ] Other tracked packages are untouched

---

### TC-H04: Dedupe Duplicate Packages

```bash
cd /tmp/aam-test-workspace
mkdir tc-h04 && cd tc-h04

aam dedupe --dry-run
```

**Verify**:

- [ ] Command runs without error
- [ ] Reports deduplication results (or "no duplicates found")

---

## Part 6: Edge Cases & Error Handling

### TC-E01: Install with Unsupported Platform

```bash
cd /tmp/aam-test-workspace
mkdir tc-e01 && cd tc-e01

aam install /tmp/aam-test-workspace/tc-c09 --platform nonexistent
```

**Verify**:

- [ ] CLI prints an error about unsupported platform
- [ ] Lists supported platforms: cursor, copilot, claude, codex
- [ ] Exit code is non-zero

---

### TC-E02: Validate Invalid Manifest

```bash
cd /tmp/aam-test-workspace
mkdir tc-e02 && cd tc-e02

# Create an invalid manifest (missing required fields)
cat > package.agent.json << 'JSON'
{
  "name": "",
  "artifacts": {}
}
JSON

aam pkg validate .
```

**Verify**:

- [ ] CLI reports validation errors (missing version, empty name, etc.)
- [ ] Exit code is non-zero

---

### TC-E03: Validate with No Manifest

```bash
cd /tmp/aam-test-workspace
mkdir tc-e03 && cd tc-e03

aam pkg validate .
```

**Verify**:

- [ ] CLI reports "no manifest found" (or similar)
- [ ] Checks for `package.agent.json`, `package.agent.yaml`, and `aam.yaml` in order

---

### TC-E04: Tree with No Lock File

```bash
cd /tmp/aam-test-workspace
mkdir tc-e04 && cd tc-e04

aam tree
```

**Verify**:

- [ ] CLI reports no lock file found
- [ ] Exit code is 1

---

### TC-E05: Why with Non-Existent Package

```bash
cd /tmp/aam-test-workspace/tc-d01

aam why nonexistent-pkg
```

**Verify**:

- [ ] CLI reports package not found in lock file
- [ ] Exit code is 1

---

### TC-E06: Verify Non-Installed Package

```bash
cd /tmp/aam-test-workspace
mkdir tc-e06 && cd tc-e06

aam verify does-not-exist
```

**Verify**:

- [ ] CLI reports package not installed
- [ ] Exit code is non-zero

---

## Part 7: Legacy Backward Compatibility

### TC-L01: Legacy `aam.yaml` Still Works for Validate

```bash
cd /tmp/aam-test-workspace
mkdir tc-l01 && cd tc-l01

# Create a legacy aam.yaml (no package.agent.json)
cat > aam.yaml << 'YAML'
name: legacy-test
version: 1.0.0
description: Legacy format package
author: Tester
artifacts:
  skills:
    - name: my-skill
      path: skills/my-skill/
      description: A skill
  agents: []
  prompts: []
  instructions: []
dependencies: {}
YAML

mkdir -p skills/my-skill
echo "# My Skill" > skills/my-skill/SKILL.md

aam pkg validate .
```

**Verify**:

- [ ] Legacy `aam.yaml` is recognized and validated
- [ ] No error about missing `package.agent.json`

---

### TC-L02: Legacy `aam-lock.yaml` Still Readable

```bash
cd /tmp/aam-test-workspace
mkdir tc-l02 && cd tc-l02

# Create a legacy lock file
cat > aam-lock.yaml << 'YAML'
packages:
  test-pkg:
    version: "1.0.0"
    source: local
    checksum: "sha256:abc123"
    artifacts:
      skills:
        - name: my-skill
          path: skills/my-skill/
          checksum: "sha256:def456"
YAML

mkdir -p .agent-packages/test-pkg/skills/my-skill
echo "# My Skill" > .agent-packages/test-pkg/skills/my-skill/SKILL.md

aam list
```

**Verify**:

- [ ] `test-pkg` appears in the list
- [ ] Legacy lock file is readable by the updated codebase

---

### TC-L03: Universal Lock File Takes Priority

```bash
cd /tmp/aam-test-workspace
mkdir tc-l03 && cd tc-l03

# Create BOTH lock files with different packages
cat > aam-lock.yaml << 'YAML'
packages:
  legacy-pkg:
    version: "1.0.0"
    source: local
    checksum: "sha256:aaa"
    artifacts:
      skills: []
YAML

cat > package.agent.lock << 'JSON'
{
  "lockVersion": 2,
  "packages": {
    "universal-pkg": {
      "version": "2.0.0",
      "resolved": "local",
      "integrity": "sha256-bbb",
      "dependencies": {}
    }
  }
}
JSON

mkdir -p .agent-packages/universal-pkg
aam list
```

**Verify**:

- [ ] `universal-pkg` appears (from `package.agent.lock`)
- [ ] `legacy-pkg` does NOT appear (universal lock takes priority)

---

### TC-L04: Deprecated Command Aliases

```bash
# These deprecated aliases should still work with a warning
aam validate /tmp/aam-test-workspace/tc-c09 2>&1
aam create-package --help 2>&1
```

**Verify**:

- [ ] Commands still function
- [ ] Deprecation warning is displayed

---

## Checklist Summary

| ID | Test | Role | Status |
|----|------|------|--------|
| TC-C01 | Scaffold new package | Creator | ☐ |
| TC-C02 | Scaffold scoped package | Creator | ☐ |
| TC-C03 | Migrate aam.yaml | Creator | ☐ |
| TC-C04 | Create from project (auto-detect) | Creator | ☐ |
| TC-C05 | Create — filter by type | Creator | ☐ |
| TC-C06 | Create — filter by platform | Creator | ☐ |
| TC-C07 | Create — dry run | Creator | ☐ |
| TC-C08 | Validate manifest | Creator | ☐ |
| TC-C09 | Full multi-artifact package | Creator | ☐ |
| TC-P01 | Install → Cursor | Consumer | ☐ |
| TC-P02 | Install → Claude | Consumer | ☐ |
| TC-P03 | Install → Copilot | Consumer | ☐ |
| TC-P04 | Install → Codex | Consumer | ☐ |
| TC-P05 | Install --no-deploy | Consumer | ☐ |
| TC-P06 | Install --dry-run | Consumer | ☐ |
| TC-P07 | Force reinstall | Consumer | ☐ |
| TC-P08 | Uninstall | Consumer | ☐ |
| TC-P09 | Verify (clean) | Consumer | ☐ |
| TC-P10 | Verify (tampered) | Consumer | ☐ |
| TC-P11 | Diff modified package | Consumer | ☐ |
| TC-D01 | Dependency tree | Consumer | ☐ |
| TC-D02 | Why is package installed | Consumer | ☐ |
| TC-D03 | Check installation status | Consumer | ☐ |
| TC-D04 | Check system dependencies | Consumer | ☐ |
| TC-V01 | Convert Cursor → Copilot | Both | ☐ |
| TC-V02 | Convert Copilot → Claude | Both | ☐ |
| TC-V03 | Convert hooks between platforms | Both | ☐ |
| TC-V04 | Convert MCP config | Both | ☐ |
| TC-H01 | Doctor diagnostics | Consumer | ☐ |
| TC-H02 | Audit packages | Consumer | ☐ |
| TC-H03 | Prune orphaned packages | Consumer | ☐ |
| TC-H04 | Dedupe duplicates | Consumer | ☐ |
| TC-E01 | Unsupported platform error | Consumer | ☐ |
| TC-E02 | Invalid manifest error | Creator | ☐ |
| TC-E03 | No manifest error | Creator | ☐ |
| TC-E04 | Tree with no lock file | Consumer | ☐ |
| TC-E05 | Why — non-existent package | Consumer | ☐ |
| TC-E06 | Verify non-installed package | Consumer | ☐ |
| TC-L01 | Legacy aam.yaml validate | Compat | ☐ |
| TC-L02 | Legacy aam-lock.yaml readable | Compat | ☐ |
| TC-L03 | Universal lock priority | Compat | ☐ |
| TC-L04 | Deprecated aliases | Compat | ☐ |

---

## Running Notes

Use this section to record observations, bugs found, and unexpected behaviors during manual testing.

| Date | TC | Observation | Severity |
|------|----|-------------|----------|
| | | | |
| | | | |
| | | | |
