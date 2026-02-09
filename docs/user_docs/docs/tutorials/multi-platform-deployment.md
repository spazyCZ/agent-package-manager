# Tutorial: Multi-Platform Deployment

**Difficulty:** Intermediate
**Time:** 15 minutes

## What You'll Learn

In this tutorial, you'll learn how to configure AAM to deploy packages simultaneously to multiple AI platforms. Install once, deploy everywhere!

Topics covered:

- Configuring `active_platforms` for simultaneous deployment
- Platform-specific install commands
- Understanding the deployment mapping table
- Verifying deployment across platforms
- Platform-specific configuration options

## Prerequisites

- AAM installed (`aam --version` works)
- At least one AAM package to install
- (Optional) Multiple AI platforms installed (Cursor, Claude Desktop, GitHub Copilot)

## The Scenario

You use multiple AI coding assistants:

- **Cursor** for daily development
- **Claude Desktop** for brainstorming and documentation
- **GitHub Copilot** in VS Code for open source projects

You want to install `@author/python-best-practices` and have it available in **all three platforms** without running three separate commands.

Let's configure multi-platform deployment.

---

## Understanding Platform Deployment

### Default Behavior (Single Platform)

By default, AAM deploys to a single platform:

```bash
# Install to the default platform only
aam install @author/python-best-practices
```

If your default platform is `cursor`, artifacts deploy only to `.cursor/` directories.

### Multi-Platform Deployment

With `active_platforms` configured, AAM deploys to all listed platforms:

```bash
# Install to all active platforms
aam install @author/python-best-practices
```

Artifacts deploy to `.cursor/`, `CLAUDE.md`, `.github/`, etc. — all at once.

---

## Step 1: Check Current Platform Configuration

View your current configuration:

```bash
aam config get default_platform
# cursor

aam config get active_platforms
# (not set)
```

By default, only `default_platform` is set.

---

## Step 2: Configure Active Platforms

Enable multi-platform deployment:

```bash
# Set active platforms
aam config set active_platforms cursor claude copilot

# Verify
aam config get active_platforms
# cursor, claude, copilot
```

This tells AAM to deploy to all three platforms on every install.

!!! tip "Alternative: Edit Config File"
    You can also edit `~/.aam/config.yaml` directly:

    ```yaml
    default_platform: cursor
    active_platforms:
      - cursor
      - claude
      - copilot
    ```

---

## Step 3: Install a Package (Multi-Platform)

Now install a package:

```bash
aam install @author/python-best-practices
```

Expected output:

```
Resolving @author/python-best-practices@1.0.0...
  + @author/python-best-practices@1.0.0

Deploying to 3 platforms...

Deploying to cursor...
  → skill: python-reviewer     → .cursor/skills/author--python-reviewer/
  → agent: python-mentor       → .cursor/rules/agent-author--python-mentor.mdc
  → prompt: refactor-function  → .cursor/prompts/refactor-function.md
  → instruction: python-standards → .cursor/rules/python-standards.mdc

Deploying to claude...
  → skill: python-reviewer     → .aam/packages/author--python-best-practices/skills/python-reviewer/
  → agent: python-mentor       → CLAUDE.md (appended section)
  → prompt: refactor-function  → .aam/packages/author--python-best-practices/prompts/refactor-function.md
  → instruction: python-standards → CLAUDE.md (appended section)

Deploying to copilot...
  → skill: python-reviewer     → .github/skills/author--python-reviewer/
  → agent: python-mentor       → .github/copilot-instructions.md (appended section)
  → prompt: refactor-function  → .github/prompts/refactor-function.md
  → instruction: python-standards → .github/copilot-instructions.md (appended section)

✓ Installed 1 package (1 skill, 1 agent, 1 prompt, 1 instruction)
✓ Deployed to 3 platforms
```

The same package is now available in Cursor, Claude Desktop, and GitHub Copilot!

---

## Step 4: Verify Deployment

Check that artifacts were deployed to each platform:

### Cursor

```bash
# Skills
ls .cursor/skills/
# author--python-reviewer/

# Agent (as .mdc rule)
ls .cursor/rules/
# agent-author--python-mentor.mdc

# Prompts
ls .cursor/prompts/
# refactor-function.md

# Instructions (as .mdc rule)
ls .cursor/rules/
# python-standards.mdc
```

### Claude Desktop

```bash
# Instructions merged into CLAUDE.md
cat CLAUDE.md
```

You should see:

```markdown
<!-- BEGIN AAM: python-mentor agent -->
# Python Mentor Agent

You are a Python expert focused on teaching best practices...

## Available Skills
- python-reviewer: Review Python code for best practices

## Available Prompts
- refactor-function: Template for refactoring functions
<!-- END AAM: python-mentor agent -->

<!-- BEGIN AAM: python-standards instruction -->
# Python Standards

- Use type hints for all functions
- Follow PEP 8
- Maximum line length: 100 characters
...
<!-- END AAM: python-standards instruction -->
```

### GitHub Copilot (VS Code)

```bash
# Skills
ls .github/skills/
# author--python-reviewer/

# Agent and instructions merged into copilot-instructions.md
cat .github/copilot-instructions.md
```

You should see:

```markdown
<!-- BEGIN AAM: python-mentor agent -->
# Python Mentor

You are a Python expert focused on teaching best practices...
<!-- END AAM: python-mentor agent -->

<!-- BEGIN AAM: python-standards instruction -->
# Python Standards

- Use type hints for all functions
...
<!-- END AAM: python-standards instruction -->
```

---

## Platform Deployment Mapping

Here's where each artifact type deploys on each platform:

### Skills

| Platform | Deployment Location | Format |
|----------|-------------------|--------|
| **Cursor** | `.cursor/skills/<name>/` | SKILL.md (native) |
| **Claude** | `.aam/packages/<pkg>/skills/<name>/` | SKILL.md (referenced) |
| **Copilot** | `.github/skills/<name>/` | SKILL.md (native) |
| **Codex** | `.codex/skills/<name>/` | SKILL.md (native) |

### Agents

| Platform | Deployment Location | Format |
|----------|-------------------|--------|
| **Cursor** | `.cursor/rules/agent-<name>.mdc` | Converted to .mdc rule |
| **Claude** | `CLAUDE.md` (appended section) | Merged into instructions |
| **Copilot** | `.github/copilot-instructions.md` | Merged into instructions |
| **Codex** | `.codex/agents/<name>/` | Native agent.yaml |

### Prompts

| Platform | Deployment Location | Format |
|----------|-------------------|--------|
| **Cursor** | `.cursor/prompts/<name>.md` | Markdown |
| **Claude** | `.aam/packages/<pkg>/prompts/<name>.md` | Markdown (referenced) |
| **Copilot** | `.github/prompts/<name>.md` | Markdown |
| **Codex** | `.codex/prompts/<name>.md` | Markdown |

### Instructions

| Platform | Deployment Location | Format |
|----------|-------------------|--------|
| **Cursor** | `.cursor/rules/<name>.mdc` | Converted to .mdc rule |
| **Claude** | `CLAUDE.md` (appended section) | Merged |
| **Copilot** | `.github/copilot-instructions.md` | Merged |
| **Codex** | `.codex/instructions/<name>.md` | Markdown |

!!! info "Merge vs. Separate"
    Some platforms (Claude, Copilot) **merge** agents and instructions into a single file. Others (Cursor, Codex) keep them as **separate files**.

    AAM handles this automatically based on the platform's conventions.

---

## Step 5: Platform-Specific Install

Sometimes you only want to deploy to one platform:

```bash
# Install to Cursor only (ignore active_platforms)
aam install @author/tool --platform cursor

# Install to Claude only
aam install @author/tool --platform claude

# Install to Copilot only
aam install @author/tool --platform copilot
```

This is useful when:

- Testing on a specific platform
- Installing a platform-specific package
- Fixing deployment issues on one platform

---

## Step 6: Platform-Specific Configuration

Each platform has configuration options in `aam.yaml` and your global config.

### Package-Level Configuration (aam.yaml)

When creating a package, you can customize how it deploys to each platform:

```yaml
# aam.yaml
platforms:
  cursor:
    skill_scope: project              # Deploy skills to .cursor/skills/ (not ~/.cursor/skills/)
    deploy_instructions_as: rules     # Convert instructions to .mdc rules

  claude:
    merge_instructions: true          # Merge into CLAUDE.md (default: true)
    instruction_heading_level: 2      # Use ## headings (default: 1)

  copilot:
    merge_instructions: true          # Merge into copilot-instructions.md
    skill_location: .github/skills    # Where to deploy skills (default)

  codex:
    skill_scope: user                 # Deploy skills to ~/.codex/skills/ (not project)
```

### User-Level Configuration (~/.aam/config.yaml)

You can override defaults globally:

```yaml
# ~/.aam/config.yaml
platforms:
  cursor:
    skill_scope: user                 # Always deploy to ~/.cursor/skills/

  claude:
    merge_instructions: false         # Never merge, keep separate files
```

**Precedence:** Package config > User config > AAM defaults

---

## Step 7: Update Across Platforms

When you update a package, all platforms are updated:

```bash
aam update @author/python-best-practices
```

```
Resolving updates...
  @author/python-best-practices: 1.0.0 → 1.1.0

Update 1 package across 3 platforms? [Y/n] y

Undeploying from cursor...
  ✓ Removed old version

Undeploying from claude...
  ✓ Removed old version from CLAUDE.md

Undeploying from copilot...
  ✓ Removed old version from .github/copilot-instructions.md

Deploying to cursor...
  → skill: python-reviewer (updated)
  → agent: python-mentor (updated)
  ...

Deploying to claude...
  ...

Deploying to copilot...
  ...

✓ Updated @author/python-best-practices to 1.1.0 across 3 platforms
```

---

## Step 8: Uninstall Across Platforms

Uninstalling removes from all active platforms:

```bash
aam uninstall @author/python-best-practices
```

```
Removing @author/python-best-practices@1.1.0 from 3 platforms...

Undeploying from cursor...
  ✓ Removed .cursor/skills/author--python-reviewer/
  ✓ Removed .cursor/rules/agent-author--python-mentor.mdc
  ✓ Removed .cursor/prompts/refactor-function.md
  ✓ Removed .cursor/rules/python-standards.mdc

Undeploying from claude...
  ✓ Removed sections from CLAUDE.md

Undeploying from copilot...
  ✓ Removed .github/skills/author--python-reviewer/
  ✓ Removed sections from .github/copilot-instructions.md
  ✓ Removed .github/prompts/refactor-function.md

✓ Uninstalled @author/python-best-practices
```

---

## Advanced: Per-Project Platform Configuration

You can override global platform settings per project:

```yaml
# .aam/config.yaml (project-level)
default_platform: cursor

active_platforms:
  - cursor
  - claude
  # Note: copilot not included for this project

platforms:
  cursor:
    skill_scope: project      # Override global user scope
```

This lets you:

- Use different platforms in different projects
- Customize deployment per project
- Keep work projects separate from personal projects

---

## Use Cases

### Use Case 1: Daily Driver + Documentation

```yaml
# Global config: Use Cursor for coding, Claude for docs
active_platforms:
  - cursor      # Daily development
  - claude      # Writing documentation, brainstorming
```

### Use Case 2: Full Stack Developer

```yaml
# Deploy to all platforms for maximum coverage
active_platforms:
  - cursor      # Primary IDE
  - copilot     # VS Code for web development
  - claude      # Design discussions
  - codex       # Legacy projects
```

### Use Case 3: Team Lead (Read-Only Platforms)

```yaml
# Install everywhere for testing/validation
active_platforms:
  - cursor
  - claude
  - copilot
  - codex

# But only publish from Cursor
default_platform: cursor
```

---

## Troubleshooting

### "Platform not supported" error

**Problem:**

```
ERROR: Platform 'cursor' is not installed or not found
```

**Solution:**

1. Verify the platform is installed:
   ```bash
   # Check if .cursor/ directory exists
   ls -la ~/.cursor/
   ```

2. If missing, AAM will skip that platform with a warning:
   ```
   ⚠ Platform 'cursor' not found, skipping deployment
   ```

3. Remove from `active_platforms` if you don't use it:
   ```bash
   aam config set active_platforms claude copilot
   ```

### Merged instructions not appearing

**Problem:** Instructions deployed to Claude/Copilot don't show up in the IDE

**Solution:**

1. Verify the file was updated:
   ```bash
   cat CLAUDE.md | grep "BEGIN AAM"
   # Should show AAM sections
   ```

2. Restart the IDE to pick up changes

3. Check platform-specific config:
   ```bash
   aam config get platforms.claude.merge_instructions
   # Should be: true
   ```

### Duplicate deployments

**Problem:** Installing multiple times creates duplicate entries

**Solution:**

```bash
# Uninstall and reinstall cleanly
aam uninstall @author/package
aam install @author/package

# Or rebuild merged files
aam deploy --rebuild
```

---

## Best Practices

### 1. Start with One Platform, Expand Gradually

```bash
# Week 1: Just Cursor
aam config set default_platform cursor

# Week 2: Add Claude
aam config set active_platforms cursor claude

# Week 3: Add Copilot
aam config set active_platforms cursor claude copilot
```

### 2. Test Platform-Specific Installs First

```bash
# Test each platform individually
aam install @author/tool --platform cursor
aam install @author/tool --platform claude
aam install @author/tool --platform copilot

# Then enable multi-platform
aam config set active_platforms cursor claude copilot
```

### 3. Document Platform Requirements in Packages

```yaml
# aam.yaml
platforms:
  cursor:
    skill_scope: project
  claude:
    merge_instructions: true
  # Note: This package is optimized for Cursor and Claude
  # Copilot support is experimental
```

### 4. Use Platform-Specific Overrides Sparingly

Over-customizing per platform makes packages harder to maintain. Prefer defaults unless you have a specific need.

---

## Summary

You've learned how to:

- **Configure `active_platforms`** for simultaneous deployment
- **Install to specific platforms** with `--platform`
- **Understand deployment mappings** for each platform
- **Verify deployments** across multiple platforms
- **Customize platform behavior** in package and user configs

**Key Commands:**

```bash
# Configure multi-platform deployment
aam config set active_platforms cursor claude copilot

# Install to all active platforms
aam install <package>

# Install to specific platform only
aam install <package> --platform cursor

# View platform configuration
aam config get active_platforms
aam config get platforms
```

**Platform Deployment Quick Reference:**

| Artifact | Cursor | Claude | Copilot | Codex |
|----------|--------|--------|---------|-------|
| Skill | `.cursor/skills/` | Referenced | `.github/skills/` | `.codex/skills/` |
| Agent | `.cursor/rules/*.mdc` | `CLAUDE.md` | `.github/copilot-instructions.md` | `.codex/agents/` |
| Prompt | `.cursor/prompts/` | Referenced | `.github/prompts/` | `.codex/prompts/` |
| Instruction | `.cursor/rules/*.mdc` | `CLAUDE.md` | `.github/copilot-instructions.md` | `.codex/instructions/` |

---

## Next Steps

- **[Working with Dependencies](working-with-dependencies.md)** - Manage package dependencies
- **[Platform Guides](../platforms/index.md)** - Platform-specific configuration details
- **[Configuration Guide](../configuration/index.md)** - Advanced configuration options

Now you can seamlessly work across multiple AI platforms with a single package installation!
