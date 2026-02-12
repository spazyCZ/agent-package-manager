# aam diff

**Package Integrity**

## Synopsis

```bash
aam diff PACKAGE [OPTIONS]
```

## Description

Show unified diff output for modified files in an installed package.
Compares current file contents against the original to display exactly
what changed. Also lists missing and untracked files.

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| PACKAGE | Yes | Name of the installed package to diff |

## Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--json` | | false | Output as JSON |

## Examples

### Example 1: Show differences

```bash
aam diff my-package
```

**Output:**
```
  my-package — 1 modified file(s)

    prompts/system.md
    --- a/prompts/system.md (original)
    +++ b/prompts/system.md (modified)
    @@ -1 +1 @@
    -You are a helpful assistant.
    +You are a senior code review assistant.
```

### Example 2: No changes

```bash
aam diff my-package
```

**Output:**
```
  ✓ 'my-package' — No changes
```

## Behavior

The `diff` command first runs `verify` to identify modified files, then
generates unified diffs using Python's `difflib`. Missing and untracked
files are listed separately.

## See also

- [aam verify](verify.md) - Verify package integrity
- [aam install](install.md) - Install packages
