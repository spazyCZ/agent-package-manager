# CLI Command Contracts: Spec 004

**Feature Branch**: `004-npm-style-source-workflow`
**Date**: 2026-02-09

This document defines the CLI contract for all new and modified commands.

---

## New Commands

### `aam init` — Client Initialization

```
Usage: aam init [OPTIONS]

  Set up AAM: choose platform, configure registries and sources.

Options:
  --yes / -y        Apply defaults without prompting
  --help            Show this message and exit.

Exit codes:
  0    Success
  1    Config write failure
```

**Interactive Flow** (when not `--yes`):
1. Platform selection: `cursor` | `copilot` | `claude` | `codex`
2. Registry setup: create local | add existing | skip
3. Community sources: multi-select from defaults
4. Write `~/.aam/config.yaml`
5. Display "Next steps" summary

**Non-Interactive** (`--yes`):
- Platform: first detected from project files, fallback to `cursor`
- Registry: skip
- Sources: add all defaults

---

### `aam outdated` — Show Packages with Updates

```
Usage: aam outdated [OPTIONS]

  Show packages with available updates.

Options:
  --json            Output as JSON
  --help            Show this message and exit.

Exit codes:
  0    Success (even if outdated packages found)
  1    Lock file read error
```

**Table Output**:
```
Package         Current    Latest     Source              Status
code-review     abc123f    def456a    openai/skills       outdated
architect       abc123f    abc123f    openai/skills       up to date
@org/my-pkg     1.0.0      —          local-registry      (no source)

1 package outdated. Run 'aam upgrade' to update.
```

**JSON Output** (`--json`):
```json
{
  "outdated": [{"name": "code-review", "current_commit": "abc123f", "latest_commit": "def456a", "source_name": "openai/skills", "has_local_modifications": false}],
  "up_to_date": ["architect"],
  "no_source": ["@org/my-pkg"],
  "total_outdated": 1,
  "stale_sources": []
}
```

---

### `aam upgrade` — Upgrade Installed Packages

```
Usage: aam upgrade [OPTIONS] [PACKAGE]

  Upgrade installed packages to latest version from sources.

Arguments:
  PACKAGE           Specific package to upgrade (optional — all if omitted)

Options:
  --dry-run         Preview changes without applying
  --force           Skip local modification warnings
  --help            Show this message and exit.

Exit codes:
  0    Success (all requested upgrades completed)
  1    One or more upgrades failed
```

**Output**:
```
Upgraded 2 packages:
  ✓ code-review (abc123f → def456a)
  ✓ gh-fix-ci (789abcd → 901efgh)

Skipped 1 package (local modifications):
  ⊘ data-analyzer — use 'aam diff data-analyzer' or '--force'

1 package failed:
  ✗ broken-pkg: Source cache corrupted
```

**Dry-Run Output**:
```
Dry run — no changes will be made

Would upgrade 2 packages:
  code-review: abc123f → def456a
  gh-fix-ci:   789abcd → 901efgh
```

---

### `aam pkg` — Package Authoring Group

```
Usage: aam pkg [OPTIONS] COMMAND [ARGS]...

  Package authoring commands.

  Create, validate, pack, and publish AAM packages.
  For installing packages, use 'aam install'.

Options:
  --help  Show this message and exit.

Commands:
  init       Scaffold a new AAM package
  create     Create package from existing artifacts
  validate   Validate package manifest
  pack       Build distributable .aam archive
  publish    Publish to registry
  build      Build portable platform bundle
```

Subcommands mirror their current root-level counterparts exactly (same options, same output).

---

## Modified Commands

### `aam install` — Extended with Source Resolution

```
Usage: aam install [OPTIONS] PACKAGES...

  Install a package and deploy artifacts.

  (unchanged options — same as current)
```

**New Behavior**:
- After registry lookup fails, attempts source resolution
- Qualified names supported: `aam install openai/skills/code-review`
- Auto-generates manifest, computes checksums, deploys
- Lock file gains `source_name` and `source_commit`

**New Error Messages**:
```
Package 'code-review' not found in registries or sources.
Run 'aam source update' to refresh source indexes.
```
```
Package 'code-review' found in 2 sources. Using: openai/skills.
For explicit selection: aam install openai/skills/code-review
```

---

### `aam list --available` — New Flag

```
Usage: aam list [OPTIONS]

  List installed packages.

Options:
  --tree              Show dependency tree
  --available         Show all installable packages from sources    ← NEW
  --help              Show this message and exit.
```

**`--available` Output**:
```
openai/skills (12 packages):
  code-review         skill     Review code changes
  architect           agent     Design system architectures
  ...

github/awesome-copilot (8 packages):
  gh-fix-ci           skill     Fix CI pipeline issues
  ...

20 packages available from 2 sources.
```

---

### `aam search` — Extended with Source Results

```
Usage: aam search [OPTIONS] QUERY

  Search registries and sources for packages.

  (unchanged options)
```

**New Behavior**:
- Results include source artifacts alongside registry results
- Source results tagged with `[source]` indicator

---

### `aam uninstall` — Bug Fix

No interface change. Internal fix: replace `CursorAdapter` with `create_adapter()` factory.

---

### `aam source` — Console Standardization

No interface change. Internal fix: replace `Console()` with `ctx.obj["console"]`, `sys.exit(1)` with `ctx.exit(1)`.

---

## Deprecated Aliases

| Old Command | New Command | Warning Message |
|-------------|-------------|-----------------|
| `aam create-package` | `aam pkg create` | "Use 'aam pkg create' instead" |
| `aam validate` | `aam pkg validate` | "Use 'aam pkg validate' instead" |
| `aam pack` | `aam pkg pack` | "Use 'aam pkg pack' instead" |
| `aam publish` | `aam pkg publish` | "Use 'aam pkg publish' instead" |
| `aam build` | `aam pkg build` | "Use 'aam pkg build' instead" |
| `aam init [name]` | `aam pkg init [name]` | "Use 'aam pkg init' for package scaffolding" |

**Silent Alias** (no warning):
| Old Command | New Command | Notes |
|-------------|-------------|-------|
| `aam update` | `aam upgrade` | npm convention alias, permanent |

---

## MCP Tool Contracts

### `aam_outdated` (Read Tool)

```python
@mcp.tool(tags={"read"})
def aam_outdated() -> dict[str, Any]:
    """Show packages with available updates from sources.

    Returns:
        Dict with keys: outdated (list), up_to_date (list),
        no_source (list), total_outdated (int), stale_sources (list).
    """
```

### `aam_available` (Read Tool)

```python
@mcp.tool(tags={"read"})
def aam_available(source_name: str | None = None) -> dict[str, Any]:
    """List all installable artifacts from sources.

    Args:
        source_name: Filter to a specific source (optional).

    Returns:
        Dict with keys: sources (list of dicts with name + artifacts),
        total_count (int).
    """
```

### `aam_upgrade` (Write Tool)

```python
@mcp.tool(tags={"write"})
def aam_upgrade(
    package_name: str | None = None,
    dry_run: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    """Upgrade packages to latest versions from sources.

    Args:
        package_name: Specific package to upgrade (optional — all if None).
        dry_run: Preview changes without applying.
        force: Skip local modification warnings.

    Returns:
        Dict with keys: upgraded (list), skipped (list),
        failed (list), total_upgraded (int).
    """
```

---

## Help Text Contract

### `aam --help` (OrderedGroup)

```
Usage: aam [OPTIONS] COMMAND [ARGS]...

  AAM - Agent Package Manager.
  A package manager for AI agents, skills, and tools.

Options:
  -v, --verbose  Enable verbose output
  --version      Show the version and exit.
  --help         Show this message and exit.

Getting Started:
  init        Set up AAM: choose platform, configure registries and sources

Package Management:
  install     Install a package and deploy artifacts
  uninstall   Remove an installed package
  upgrade     Upgrade installed packages to latest version
  outdated    Show packages with available updates
  search      Search registries and sources for packages
  list        List installed packages (--available for all)
  info        Show package details

Package Integrity:
  verify      Verify installed file checksums
  diff        Show modifications in installed packages

Package Authoring:
  pkg         Package creation and publishing commands

Source Management:
  source      Manage remote git artifact sources

Configuration:
  config      Manage AAM configuration
  registry    Manage registry connections

Utilities:
  mcp         MCP server for IDE integration
  doctor      Environment diagnostics
```
