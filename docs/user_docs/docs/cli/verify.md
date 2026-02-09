# aam verify

**Package Integrity**

## Synopsis

```bash
aam verify [PACKAGE] [OPTIONS]
```

## Description

Verify the integrity of installed package files by comparing current file
checksums against the recorded checksums in the lock file. Reports files
as ok, modified, missing, or untracked.

Use this command to check if you or a teammate have made local changes to
installed package files.

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| PACKAGE | No | Package name to verify (required unless `--all`) |

## Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--all` | `-a` | false | Verify all installed packages |
| `--json` | | false | Output as JSON |

## Examples

### Example 1: Verify a specific package

```bash
aam verify my-package
```

**Output:**
```
  my-package — 3 files verified

  ✓ SKILL.md                   ok
  ✗ prompts/system.md          modified
  ✓ agent.yaml                 ok

  1 modified, 0 missing, 0 untracked
```

### Example 2: Verify all packages

```bash
aam verify --all
```

**Output:**
```
  my-package        ✓ clean (3 files)
  code-review       ✗ 1 modified (5 files)
  my-agent          ⚠ no checksums available

  2 packages verified, 1 with changes
```

### Example 3: JSON output

```bash
aam verify my-package --json
```

## Behavior

AAM stores per-file SHA-256 checksums in `aam-lock.yaml` during
installation. The `verify` command recomputes checksums for installed
files and compares them against the recorded values.

If a package was installed before checksum support was added, the
command reports "no checksums available" instead of an error.

## See also

- [aam diff](diff.md) - Show file differences
- [aam install](install.md) - Install packages (stores checksums)
