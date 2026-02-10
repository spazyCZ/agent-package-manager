# aam upgrade

**Package Management**

## Synopsis

```bash
aam upgrade [PACKAGE] [OPTIONS]
```

## Description

Upgrade outdated packages that were installed from git sources. Without arguments, upgrades all outdated packages. Specify a package name to upgrade a single package.

Before overwriting files, AAM checks for local modifications. If modifications are detected, you'll be prompted to choose: backup and continue, skip the package, view a diff, or force overwrite.

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| PACKAGE | No | Name of a specific package to upgrade (default: all outdated) |

## Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--dry-run` | | false | Preview changes without applying |
| `--force` | `-f` | false | Skip local modification warnings |
| `--global` | `-g` | false | Upgrade packages in global `~/.aam/` directory |

## Examples

### Example 1: Upgrade All

```bash
aam upgrade
```

**Output:**
```
Upgrading outdated packages...

  ✓ code-review     abc1234 → def5678  (community)
  ✓ prompt-lib      111aaaa → 222bbbb  (awesome-prompts)

2 packages upgraded.
```

### Example 2: Upgrade Single Package

```bash
aam upgrade code-review
```

### Example 3: Dry Run

```bash
aam upgrade --dry-run
```

**Output:**
```
Dry run — no changes will be made.

  Would upgrade: code-review     abc1234 → def5678
  Would upgrade: prompt-lib      111aaaa → 222bbbb

2 packages would be upgraded.
```

### Example 4: Force Upgrade (Skip Modification Check)

```bash
aam upgrade --force
```

Skips local modification checks and overwrites all files.

### Example 5: Upgrade Global Packages

```bash
aam upgrade -g
```

**Output:**
```
Operating in global mode (~/.aam/)

  ✓ Upgraded code-review (abc1234 → def5678)

  1 upgraded, 0 skipped, 0 failed
```

Upgrades outdated packages in `~/.aam/packages/` instead of the project-local directory.

### Example 6: Handling Local Modifications

```bash
aam upgrade code-review
```

**Output (with modifications detected):**
```
⚠ code-review has local modifications:
  Modified: skills/code-review/SKILL.md

  [b]ackup and continue  [s]kip  [d]iff  [f]orce
  Choice [s]:
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (all targeted packages upgraded or skipped) |
| 1 | Error during upgrade |

## Related Commands

- [`aam outdated`](outdated.md) - Check which packages are outdated
- [`aam source update`](source-update.md) - Fetch latest from sources
- [`aam verify`](verify.md) - Check package file integrity
- [`aam diff`](diff.md) - View file modifications

## Notes

### Hidden Alias

`aam update` is a hidden alias for `aam upgrade`. It works identically but is not shown in `aam --help`.

### Source-Only

`aam upgrade` only works with packages installed from git sources. Registry-installed packages should be upgraded by running `aam install <package>@<version>` with the desired version.
