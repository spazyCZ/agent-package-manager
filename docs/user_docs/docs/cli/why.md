# aam why

**Dependency Management**

## Synopsis

```bash
aam why PACKAGE_NAME [OPTIONS]
```

## Description

Show why a package is installed. Traces dependency provenance to
explain which packages require the named package and via what version
constraint. Useful for understanding transitive dependencies and
deciding whether a package can be removed.

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| PACKAGE_NAME | Yes | Name of the package to trace |

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--project` | current directory | Project directory path |

## Examples

### Example 1: Trace a transitive dependency

```bash
aam why report-templates
```

**Output:**
```
╭─── aam why report-templates ───╮
│ report-templates@2.1.0         │
│                                │
│ Required by 1 package(s):      │
│   • @author/asvc-auditor@1.0.0 │
│     (^2.0.0)                   │
╰────────────────────────────────╯
```

### Example 2: Trace a direct dependency

```bash
aam why @author/asvc-auditor
```

**Output:**
```
╭──── aam why @author/asvc-auditor ────╮
│ @author/asvc-auditor@1.0.0           │
│                                      │
│ Direct dependency (not required by   │
│ any other package)                   │
╰──────────────────────────────────────╯
```

### Example 3: Package not found

```bash
aam why nonexistent-package
```

**Output:**
```
Package 'nonexistent-package' is not in the lock file.
```

Exit code: 1

### Example 4: Scoped package

```bash
aam why @scope/some-dep --project ./my-project
```

Works the same way with scoped package names.

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Package found and provenance displayed |
| 1 | Package not found in lock file |

## Related commands

- [`aam tree`](tree.md) — Display the full dependency tree
- [`aam check`](check.md) — Verify all dependencies are present
- [`aam list`](list.md) — List installed packages
- [`aam info`](info.md) — Show detailed package information

## Notes

### When to use `aam why`

- Before removing a package — check if anything else depends on it
- When debugging dependency conflicts — understand the chain
- When auditing what is installed — trace unexpected packages
