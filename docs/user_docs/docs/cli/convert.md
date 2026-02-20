# aam convert

**Utilities**

## Synopsis

```bash
aam convert --source-platform <platform> --target-platform <platform> [OPTIONS]
```

## Description

Convert AI agent configurations between platforms. Reads artifacts from one
platform's format (instructions, agents, prompts, skills) and writes them in
another platform's format, with clear warnings about metadata that cannot be
directly converted.

Supported platforms: **cursor**, **copilot**, **claude**, **codex**.

This is useful when:

- Migrating between AI coding agents (Cursor, VS Code Copilot, Claude Code, Codex)
- Using multiple platforms simultaneously and wanting consistent configuration
- Onboarding a team that uses different editors

## Options

| Option | Short | Required | Description |
|--------|-------|----------|-------------|
| `--source-platform` | `-s` | Yes | Source platform: `cursor`, `copilot`, `claude`, `codex` |
| `--target-platform` | `-t` | Yes | Target platform: `cursor`, `copilot`, `claude`, `codex` |
| `--type` | | No | Filter by artifact type: `instruction`, `agent`, `prompt`, `skill` |
| `--dry-run` | | No | Show what would be converted without writing files |
| `--force` | | No | Overwrite existing target files (creates `.bak` backup) |
| `--verbose` | | No | Show detailed workaround instructions for warnings |

## Examples

### Example 1: Convert all Cursor configs to Copilot

```bash
aam convert -s cursor -t copilot
```

**Output:**
```
Converting Cursor → Copilot...

INSTRUCTIONS:
  ✓ .cursor/rules/python-style.mdc → .github/instructions/python-style.instructions.md
    ⚠ alwaysApply field dropped
  ✓ .cursor/rules/general.mdc → .github/copilot-instructions.md (appended)

AGENTS:
  ✓ .cursor/agents/reviewer.md → .github/agents/reviewer.agent.md
    ⚠ model 'fast' is cursor-specific, removed
    ⚠ readonly=true not supported on target. Enforce via instruction text.

SKILLS:
  ✓ .cursor/skills/code-review/ → .github/skills/code-review/ (direct copy)

SUMMARY: 4 converted, 0 failed, 3 warnings
```

### Example 2: Dry-run instructions only

```bash
aam convert -s copilot -t claude --type instruction --dry-run
```

**Output:**
```
[DRY RUN] Converting Copilot → Claude...

INSTRUCTIONS:
  ✓ .github/copilot-instructions.md → CLAUDE.md (appended)
  ✓ .github/instructions/react.instructions.md → CLAUDE.md (appended)
    ⚠ Conditional instruction converted to always-on. Original applyTo: **/*.tsx

SUMMARY: 2 converted, 0 failed, 1 warnings
```

### Example 3: Force overwrite with backup

```bash
aam convert -s codex -t cursor --force
```

When `--force` is used, existing target files are backed up to `.bak` before
being overwritten.

### Example 4: Verbose output with workarounds

```bash
aam convert -s cursor -t copilot --verbose
```

Verbose mode includes detailed workaround text for each warning:

```
  ⚠ model 'fast' is cursor-specific, removed
      Model identifiers differ between platforms. Set the model
      manually on the target platform.
```

## What gets converted

### Instructions

| Source → Target | Behavior |
|-----------------|----------|
| Cursor `.mdc` → Copilot | `globs` mapped to `applyTo`; `alwaysApply` dropped |
| Cursor `.mdc` → Claude/Codex | Appended with markers; `globs` lost (warning) |
| Cursor `.cursorrules` → Any | Direct content copy |
| Copilot `.instructions.md` → Cursor | `applyTo` mapped to `globs` |
| Copilot → Claude/Codex | Direct content copy; `applyTo` lost (warning) |
| Claude `CLAUDE.md` → Codex | Direct content copy |

### Agents

| Source → Target | Behavior |
|-----------------|----------|
| Any → Codex | Appended as section in `AGENTS.md` (no discrete files) |
| Copilot `.agent.md` → Cursor/Claude | `tools`, `handoffs`, `model` dropped (warning) |
| Cursor subagent → Claude | `readonly`, `is_background`, `model` dropped (warning) |

### Prompts

| Source → Target | Behavior |
|-----------------|----------|
| Any → Codex | Appended to `AGENTS.md` (no prompt files in Codex) |
| Copilot `.prompt.md` → Cursor/Claude | `agent`, `model`, `tools` dropped (warning) |
| Cursor → Copilot | Plain markdown gets `.prompt.md` extension |

### Skills

Skills use a universal `SKILL.md` format and are **directly copied** between
all platforms. Only the deployment path changes.

## Conflict handling

| Scenario | Behavior |
|----------|----------|
| Target file already exists | Skip with warning: "Target exists, use --force to overwrite" |
| Target file exists + `--force` | Overwrite; original saved as `.bak` file |
| Multiple sources → single target (e.g. → `CLAUDE.md`) | Append with `<!-- AAM CONVERTED -->` section markers |
| Source and target are same platform | Error: "Source and target platform cannot be the same" |

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | All conversions succeeded (warnings are allowed) |
| 1 | One or more conversions failed |

## See also

- [Platform Support Overview](../platforms/index.md) -- Platform comparison and configuration
- [Migration Guide](../troubleshooting/migration.md) -- Migrating between platforms
- [aam doctor](doctor.md) -- Diagnose environment issues
