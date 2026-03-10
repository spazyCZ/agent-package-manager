# aam dedupe

**Dependency Management**

## Synopsis

```bash
aam dedupe [OPTIONS]
```

## Description

Detect and remove duplicate package installations. Scans
`.agent-packages/` for packages that appear in multiple sub-namespace
directories (typically from pre-update or migrated installs) and
hoists compatible versions to the root level.

Use this command after migrations or when you suspect redundant copies
of the same package exist in your install tree.

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--dry-run` | false | Show what would be deduped without making changes |
| `--project` | current directory | Project directory path |

## Examples

### Example 1: Preview deduplication

```bash
aam dedupe --dry-run
```

**Output:**
```
Would dedupe 2 package(s):
  • report-templates
  • shared-prompts

Run 'aam dedupe' (without --dry-run) to apply.
```

### Example 2: Run deduplication

```bash
aam dedupe
```

**Output:**
```
✓ Deduped 2 package(s):
  • report-templates
  • shared-prompts
```

### Example 3: No duplicates found

```bash
aam dedupe
```

**Output:**
```
✓ No duplicate packages found. Package layout is already flat.
```

### Example 4: Dedupe a specific project

```bash
aam dedupe --project ./my-project
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success (duplicates resolved or none found) |

## Related commands

- [`aam prune`](prune.md) — Remove unlisted package directories
- [`aam tree`](tree.md) — Display the dependency tree
- [`aam check`](check.md) — Verify all dependencies are present
- [`aam install`](install.md) — Reinstall packages

## Notes

### When to use `aam dedupe`

- After migrating from `.aam/packages/` to `.agent-packages/`
- After resolving dependency conflicts that left redundant copies
- When `aam tree` shows the same package at multiple levels

### Safe operation

`aam dedupe` keeps the root-level copy of each package and removes
nested duplicates. Always use `--dry-run` first to preview changes.
