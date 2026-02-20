# aam list

**Package Management**

## Synopsis

```bash
aam list [OPTIONS]
```

## Description

List all installed packages in the current project. Displays package names, versions, source origin, and artifact counts in a formatted table. Use `--tree` to view the dependency tree showing how packages depend on each other.

This command reads from the lock file (`.aam/aam-lock.yaml`) and installed package manifests.

## Arguments

This command takes no arguments.

## Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--tree` | | false | Show dependency tree instead of flat list |
| `--global` | `-g` | false | List packages from global `~/.aam/` directory |

## Examples

### Example 1: Basic List

```bash
aam list
```

**Output:**
```
Installed packages:

┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ Name                ┃ Version ┃ Source                      ┃ Artifacts           ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ my-agent            │ 1.2.0   │ registry                    │ 4 (2 skills, 1 age… │
│ docs-writer         │ 0.0.0   │ google-gemini/gemini-skills │ 1 (1 skill)         │
│ @author/dep-package │ 2.0.1   │ local                       │ 2 (1 skills, 1 pro… │
│ shared-prompts      │ 1.0.0   │ registry                    │ 3 (3 prompts)       │
└─────────────────────┴─────────┴────────────────────────────┴─────────────────────┘
```

### Example 2: Dependency Tree

```bash
aam list --tree
```

**Output:**
```
my-agent@1.2.0 (registry)
├── @author/dep-package@2.0.1
│   └── shared-prompts@1.0.0
└── utility-skills@0.5.0

docs-writer@0.0.0 (google-gemini/gemini-skills)

standalone-package@3.0.0 (local)
```

This shows:

- `my-agent` depends on `@author/dep-package` and `utility-skills`
- `@author/dep-package` depends on `shared-prompts`
- `standalone-package` has no dependencies

### Example 3: No Packages Installed

```bash
aam list
```

**Output:**
```
No packages installed.
```

### Example 4: Source-installed packages

When packages are installed from git sources, the Source column
shows the repository they came from:

```bash
aam list
```

**Output:**
```
Installed packages:

┏━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ Name          ┃ Version ┃ Source                      ┃ Artifacts           ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ docs-writer   │ 0.0.0   │ google-gemini/gemini-skills │ 1 (1 skill)         │
│ code-reviewer │ 0.0.0   │ anthropics/skills          │ 1 (1 skill)         │
└───────────────┴─────────┴────────────────────────────┴─────────────────────┘
```

### Example 5: List Global Packages

```bash
aam list -g
```

**Output:**
```
Operating in global mode (~/.aam/)

Installed packages:

┏━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ Name          ┃ Version ┃ Source                      ┃ Artifacts           ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ shared-agent  │ 1.0.0   │ registry                    │ 2 (1 skill, 1 age…  │
└───────────────┴─────────┴────────────────────────────┴─────────────────────┘
```

Lists packages installed globally in `~/.aam/packages/` rather than in the current project.

### Example 6: Tree with Missing Dependencies

```bash
aam list --tree
```

**Output:**
```
my-agent@1.2.0 (registry)
├── @author/dep-package@2.0.1
├── missing-dependency (not installed)
└── utility-skills@0.5.0
```

Shows dependencies that are declared but not installed (indicates a corrupted environment).

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |

## Output Details

### Table Columns

- **Name** - Package name (scoped or unscoped)
- **Version** - Installed version from lock file
- **Source** - Where the package came from. For packages installed
  from git sources this shows the source name (for example,
  `google-gemini/gemini-skills`). For registry or local installs
  it shows `registry` or `local`.
- **Artifacts** - Total count and breakdown by type

### Artifact Types

The artifact count shows:

- Total number of artifacts
- Breakdown by type (skills, agents, prompts, instructions)

Example: `4 (2 skill, 1 agent, 1 instruction)`

### Tree Format

The dependency tree shows:

- Root packages (packages not depended on by others)
- Direct dependencies indented with `├──` or `└──`
- Recursive dependencies shown with proper indentation
- Missing dependencies shown as `(not installed)`

## Related Commands

- [`aam info`](info.md) - Show detailed information about a package
- [`aam install`](install.md) - Install packages
- [`aam uninstall`](uninstall.md) - Remove packages

## Notes

### Lock File

This command reads from `.aam/aam-lock.yaml`. If the lock file is out of sync with installed packages, you may see incomplete or incorrect information.

### Artifact Count Accuracy

Artifact counts are read from each package's `aam.yaml` manifest. If a package directory is missing or corrupted, the count will show as `?`.

### Root Packages

In tree mode, "root packages" are packages that no other installed package depends on. These are typically packages you explicitly installed with `aam install`.

### Performance

The `--tree` option requires analyzing all package dependencies, which may take longer for projects with many packages. The flat table view is faster.

### Filtering

Currently, there is no built-in filtering. To filter output, use standard Unix tools:

```bash
aam list | grep my-pattern
```
