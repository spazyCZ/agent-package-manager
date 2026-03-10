# aam tree

**Dependency Management**

## Synopsis

```bash
aam tree [OPTIONS]
```

## Description

Display the full resolved dependency tree for your project. Reads
`package.agent.lock` and renders a nested tree showing all installed
packages with their transitive dependencies.

Use this command to understand what is installed and how packages
relate to each other.

## Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--depth` | `-d` | `0` (unlimited) | Maximum tree depth to display |
| `--project` | | current directory | Project directory path |

## Examples

### Example 1: Show full dependency tree

```bash
aam tree
```

**Output:**
```
project (5 packages)
├── @author/asvc-auditor@1.0.0
│   ├── @author/generic-auditor@1.2.3
│   └── report-templates@2.1.0
├── code-reviewer@1.5.0
│   ├── python-linter@2.3.0
│   └── js-linter@3.1.0
└── shared-prompts@1.0.0

5 packages total
```

### Example 2: Limit depth to direct dependencies

```bash
aam tree --depth 1
```

**Output:**
```
project (5 packages)
├── @author/asvc-auditor@1.0.0
├── code-reviewer@1.5.0
└── shared-prompts@1.0.0

5 packages total
```

### Example 3: Show tree for a specific project

```bash
aam tree --project ./my-project
```

Displays the dependency tree for the project at the specified path
instead of the current directory.

### Example 4: No packages installed

```bash
aam tree
```

**Output:**
```
No packages installed.
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |

## Related commands

- [`aam why`](why.md) — Explain why a specific package is installed
- [`aam check`](check.md) — Verify all dependencies are present
- [`aam list`](list.md) — List installed packages
- [`aam dedupe`](dedupe.md) — Flatten duplicate packages
- [`aam prune`](prune.md) — Remove unlisted packages

## Notes

### Lock file required

`aam tree` reads from `package.agent.lock`. If no lock file exists,
run `aam install` first to generate one.

### Optional dependencies

Optional dependencies are marked in the tree output:

```
├── my-package@1.0.0
│   └── optional-helper@2.0.0 (optional)
```
