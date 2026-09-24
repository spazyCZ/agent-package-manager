# aam check

**Dependency Management**

## Synopsis

```bash
aam check [OPTIONS]
```

## Description

Verify that all packages in the lock file have corresponding
directories in `.agent-packages/` and that all dependencies are
present and compatible.

With `--system`, runs pre-flight checks against system dependencies
(Python, Node, binaries, pip/npm/cargo packages, MCP servers) declared
by all currently installed packages.

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--system` | false | Check system dependencies instead of packages |
| `--project` | current directory | Project directory path |

## Examples

### Example 1: Check package installation status

```bash
aam check
```

**Output:**
```
          Package Installation Check
┏━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Package                  ┃ Version ┃ Status     ┃ Directory     ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ @author/asvc-auditor     │ 1.0.0   │ ✓ present  │ .agent-pack…  │
│ report-templates         │ 2.1.0   │ ✓ present  │ .agent-pack…  │
│ broken-package           │ 0.5.0   │ ✗ missing  │ .agent-pack…  │
└──────────────────────────┴─────────┴────────────┴───────────────┘

2/3 packages present

✗ 1 package(s) missing from `.agent-packages/`. Run `aam install` to restore.
```

### Example 2: Check system dependencies

```bash
aam check --system
```

**Output:**
```
          System Dependency Check
┏━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ Name         ┃ Type    ┃ Status                  ┃ Version ┃ Hint                ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ python       │ runtime │ ✓ found                 │ 3.12.1  │                     │
│ node         │ runtime │ ✓ found                 │ 20.11.0 │                     │
│ ruff         │ binary  │ ✓ found                 │ 0.3.0   │                     │
│ jq           │ binary  │ ✗ missing               │         │ brew install jq     │
│ boto3        │ pip     │ ⚠ missing (optional)    │         │ pip install boto3   │
└──────────────┴─────────┴─────────────────────────┴─────────┴─────────────────────┘

3/5 checks passed

✓ All required dependencies satisfied
```

### Example 3: All packages present

```bash
aam check
```

**Output:**
```
3/3 packages present

✓ All packages present
```

### Example 4: No system dependencies declared

```bash
aam check --system
```

**Output:**
```
✓ No system dependencies declared by installed packages
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | All checks passed |
| 1 | One or more required items are missing |

## Related commands

- [`aam install`](install.md) — Install missing packages
- [`aam tree`](tree.md) — Display the dependency tree
- [`aam audit`](audit.md) — Check package integrity
- [`aam doctor`](doctor.md) — Run environment diagnostics

## Notes

### Package check vs. system check

Without `--system`, `aam check` verifies that package directories
exist on disk. With `--system`, it runs pre-flight checks against
OS-level requirements like runtimes, binaries, and package manager
packages.

### Fixing missing packages

If `aam check` reports missing packages, run `aam install` to
restore them from the lock file.

### Fixing missing system dependencies

If `aam check --system` reports missing items, you can install them
manually using the hint column, or use `aam install --install-system-deps`
for pip and npm packages.
