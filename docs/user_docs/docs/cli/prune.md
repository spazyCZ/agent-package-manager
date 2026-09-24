# aam prune

**Dependency Management**

## Synopsis

```bash
aam prune [OPTIONS]
```

## Description

Remove package directories from `.agent-packages/` that are not
tracked in `package.agent.lock`. Useful for cleaning up after failed
installs, manual modifications, or removing packages that are no
longer declared in the dependency tree.

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--dry-run` | false | Show what would be removed without making changes |
| `--project` | current directory | Project directory path |

## Examples

### Example 1: Preview pruning

```bash
aam prune --dry-run
```

**Output:**
```
Would remove 2 unlisted director(ies):
  • old-package
  • temp-install

Run 'aam prune' (without --dry-run) to apply.
```

### Example 2: Run pruning

```bash
aam prune
```

**Output:**
```
✓ Pruned 2 unlisted director(ies):
  • old-package
  • temp-install
```

### Example 3: Nothing to prune

```bash
aam prune
```

**Output:**
```
✓ No unlisted directories found. Package tree is clean.
```

### Example 4: Prune a specific project

```bash
aam prune --project ./my-project
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success (directories removed or none found) |

## Related commands

- [`aam dedupe`](dedupe.md) — Flatten duplicate packages
- [`aam check`](check.md) — Verify all dependencies are present
- [`aam tree`](tree.md) — Display the dependency tree
- [`aam uninstall`](uninstall.md) — Remove a specific package

## Notes

### When to use `aam prune`

- After manually deleting entries from `package.agent.lock`
- After a failed install left partial directories
- When `.agent-packages/` contains directories from experiments

### Safe operation

`aam prune` only removes directories not tracked in the lock file.
It never touches packages that are properly locked. Always use
`--dry-run` first to preview changes.

### Difference from `aam uninstall`

`aam uninstall` removes a specific package by name and updates the
lock file. `aam prune` removes all directories that are already
absent from the lock file — the cleanup counterpart.
