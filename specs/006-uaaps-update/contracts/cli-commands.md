# CLI Command Contracts: UAAPS v0.4.0

**Feature**: 006-uaaps-update
**Date**: 2026-02-20

This document defines the complete CLI command interface — signatures, flags, outputs, and exit codes — for all new and modified commands in the UAAPS v0.4.0 update.

---

## New Commands

### `aam tree`

Display the resolved dependency tree for the current project.

```
Usage: aam tree [OPTIONS]

  Display the full resolved dependency tree.

Options:
  --depth INTEGER   Limit display to N levels (0 = unlimited).  [default: 0]
  --project PATH    Project directory.  [default: .]
  --help            Show this message and exit.
```

**Output** (Rich Tree panel):
```
my-project
├── code-review@1.3.2 (direct)
│   └── git-utils@1.0.1 (transitive)
├── testing-utils@2.4.0 (direct)
└── ai-image-gen@1.0.0 (optional)
```

**Exit codes**: 0 success, 1 no lock file found

---

### `aam why <package>`

Explain why a package is installed — which parent(s) require it.

```
Usage: aam why [OPTIONS] PACKAGE

  Explain why PACKAGE is installed.

Arguments:
  PACKAGE  Package name to look up.  [required]

Options:
  --project PATH    Project directory.  [default: .]
  --help            Show this message and exit.
```

**Output**:
```
git-utils@1.0.1 is required by:
  └── code-review@1.3.2 (constraint: ^1.0.0)
```

**Exit codes**: 0 found, 1 package not in lock file, 2 lock file missing

---

### `aam check`

Verify all installed dependencies are present and compatible.

```
Usage: aam check [OPTIONS]

  Verify all installed dependencies are present and compatible.

Options:
  --system      Run system dependency pre-flight checks only.
  --project PATH  Project directory.  [default: .]
  --help        Show this message and exit.
```

**Output** (Rich table):
```
┌─────────────────┬─────────┬────────┬──────────────────────┐
│ Package         │ Version │ Status │ Note                 │
├─────────────────┼─────────┼────────┼──────────────────────┤
│ code-review     │ 1.3.2   │ ✓ OK   │                      │
│ testing-utils   │ 2.4.0   │ ✓ OK   │                      │
│ git-utils       │ missing │ ✗ FAIL │ Directory not found  │
└─────────────────┴─────────┴────────┴──────────────────────┘
```

With `--system`:
```
┌───────────────┬─────────┬────────┬──────────────────────────────┐
│ Dependency    │ Found   │ Status │ Note                         │
├───────────────┼─────────┼────────┼──────────────────────────────┤
│ python        │ 3.12.1  │ ✓ OK   │ (>=3.10)                     │
│ git           │ /usr/bin│ ✓ OK   │                              │
│ pdfplumber    │ missing │ ✗ FAIL │ Run: pip install pdfplumber  │
└───────────────┴─────────┴────────┴──────────────────────────────┘
```

**Exit codes**: 0 all pass, 1 one or more failures, 2 no lock file

---

### `aam audit`

Check installed packages for security issues.

```
Usage: aam audit [OPTIONS]

  Check installed packages for security issues.

Options:
  --severity [critical|high|medium|low|all]
                    Filter findings by minimum severity.  [default: all]
  --project PATH    Project directory.  [default: .]
  --help            Show this message and exit.
```

**Output** (Rich table):
```
┌───────────────┬─────────┬──────────┬─────────────────────────────────────────────┐
│ Package       │ Version │ Severity │ Issue                                       │
├───────────────┼─────────┼──────────┼─────────────────────────────────────────────┤
│ code-review   │ 1.2.0   │ CRITICAL │ Integrity: hash mismatch (archive tampered) │
└───────────────┴─────────┴──────────┴─────────────────────────────────────────────┘

1 finding (1 critical, 0 high, 0 medium, 0 low)
```

**Exit codes**: 0 no findings, 1 findings at or above `--severity`, 2 no lock file

---

### `aam dedupe`

Flatten compatible duplicate package versions to reduce redundancy.

```
Usage: aam dedupe [OPTIONS]

  Flatten compatible duplicate package versions.

Options:
  --dry-run     Show what would change without making changes.
  --project PATH  Project directory.  [default: .]
  --help        Show this message and exit.
```

**Output**:
```
Deduplication complete:
  Hoisted git-utils@1.0.1 (was in code-review/ and testing-utils/)
  No changes needed for other packages.

Result: 1 package deduplicated, 0 conflicts skipped.
```

**Exit codes**: 0 success, 1 unresolvable conflicts found

---

### `aam prune`

Remove installed packages no longer in the dependency tree.

```
Usage: aam prune [OPTIONS]

  Remove packages not present in package.agent.lock.

Options:
  --dry-run     Show what would be removed without removing.
  --project PATH  Project directory.  [default: .]
  --help        Show this message and exit.
```

**Output**:
```
Pruning 2 unused packages:
  Removed: old-tool@0.9.0
  Removed: legacy-utils@1.1.0

Result: 2 packages removed, 47 MB freed.
```

**Exit codes**: 0 success (even if nothing pruned), 1 error during removal

---

## Modified Commands

### `aam install` — new flags

```
Usage: aam install [OPTIONS] [PACKAGES]...

Options:
  --frozen                 Use exact versions from lock file; fail if stale.
  --minimal                Install lowest version satisfying each constraint.
  --latest                 Install newest available versions (ignores constraints).
  --dry-run                Resolve and display without installing.
  --install-system-deps    Automatically install missing pip/npm/MCP dependencies.
  --allow-sudo             Allow elevated-privilege installs (brew, apt).
  --skip-checks            Skip system dependency pre-flight check (for CI environments).
  --no-deploy              Download and extract only; skip platform deployment.
  --force                  Reinstall even if already installed.
  --platform TEXT          Target platform adapter.  [default: from config]
  -g, --global             Install to global (~/.aam) directory.
  --project PATH           Project directory.  [default: .]
  --help                   Show this message and exit.
```

**New behaviors**:
- Runs governance policy check before resolution (new)
- Displays system dependency pre-flight check results (new); `--skip-checks` bypasses for CI (UAAPS §16)
- Prompts for required `env` vars during installation (new)
- Displays `permissions` and requires confirmation if declared (new)
- Generates `package.agent.lock` (new, replaces `aam-lock.yaml`)
- Installs to `.agent-packages/` (new, was `.aam/packages/`)

---

### `aam pkg init` — generates `package.agent.json`

```
Usage: aam pkg init [OPTIONS]

Options:
  --name TEXT       Package name.
  --version TEXT    Initial version.  [default: 0.1.0]
  --migrate         Migrate existing aam.yaml to package.agent.json.
  --help            Show this message and exit.
```

**New behavior**: Default output is `package.agent.json` (JSON). `--migrate` reads `aam.yaml` and writes `package.agent.json`.

---

### `aam pkg create` — generates `package.agent.json`

Default manifest format changed to `package.agent.json`. No flag change required.

---

### `aam pkg validate` — validates new schema

```
Usage: aam pkg validate [OPTIONS] [PATH]

Options:
  --help  Show this message and exit.
```

**New behavior**: Validates against UAAPS schema. Reports errors for new fields (`env`, `permissions`, `systemDependencies`). Accepts `package.agent.json`, `package.agent.yaml`, or `aam.yaml`.

---

### `aam convert` — new conversion rules

```
Usage: aam convert [OPTIONS]

Options:
  --from [cursor|claude|copilot|codex]   Source platform.  [required]
  --to [cursor|claude|copilot|codex]     Target platform.  [required]
  --help                                 Show this message and exit.
```

**New conversions supported**:
- `.instructions.md` → `RULE.md` (frontmatter: `applyTo` → `globs`)
- `hooks.json` with Cursor events → `hooks.json` with Claude Code events (and vice versa)
- `mcp.json` (Cursor) ↔ `.mcp.json` (Claude Code)
- `rules/*.mdc` → `rules/*/RULE.md`

---

## Exit Code Conventions

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Domain error (not found, validation failure, audit findings) |
| 2 | Missing prerequisite (no lock file, no manifest) |
| 3 | Governance policy violation |
| 4 | System dependency failure (required dep missing, install failed) |
| 5 | Conflict error (dependency conflict, circular dependency) |

---

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `AAM_PROJECT_DIR` | Override project root directory | cwd |
| `AAM_GLOBAL_CONFIG_DIR` | Override `~/.aam/` location | `~/.aam/` |
| `AAM_NO_COLOR` | Disable Rich color output | unset |
| `AAM_LOG_LEVEL` | Logging verbosity | `WARNING` |
