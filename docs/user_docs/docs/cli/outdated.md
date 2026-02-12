# aam outdated

**Package Management**

## Synopsis

```bash
aam outdated [OPTIONS]
```

## Description

Check for outdated source-installed packages. Compares installed package commit SHAs against the source HEAD. Packages not installed from sources are shown as "(no source)".

Use `-g` / `--global` to check packages in the user-wide `~/.aam/` directory instead of the project-local `.aam/` workspace.

## Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--json` | | false | Output as JSON |
| `--global` | `-g` | false | Check global `~/.aam/` packages for updates |

## Examples

### Example 1: Check Outdated Packages

```bash
aam outdated
```

**Output:**
```
  Package      Current   Latest    Source     Status
  ───────────  ────────  ────────  ─────────  ─────────────
  code-review  abc1234   def5678   community  outdated
  prompt-lib   111aaaa   111aaaa   awesome    up to date
  my-agent    -         -         -          (no source)

  1 outdated, 1 up to date, 1 from registry
```

### Example 2: JSON Output

```bash
aam outdated --json
```

**Output:**
```json
{
  "outdated": [
    {
      "name": "code-review",
      "current_commit": "abc1234",
      "latest_commit": "def5678",
      "source_name": "community",
      "has_local_modifications": false
    }
  ],
  "up_to_date": ["prompt-lib"],
  "no_source": ["my-agent"],
  "stale_sources": []
}
```

### Example 3: Check Global Packages

```bash
aam outdated -g
```

Checks packages in `~/.aam/packages/` instead of project-local `.aam/packages/`.

### Example 4: Stale Source Warning

```bash
aam outdated
```

**Output (when source not updated in 7+ days):**
```
⚠ Source 'community' not updated in 7+ days. Run 'aam source update community'.

  Package      Current   Latest    Source     Status
  ...
```

Run `aam source update` to fetch the latest from sources.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error during check |

## Related Commands

- [`aam upgrade`](upgrade.md) - Upgrade outdated packages
- [`aam source update`](source-update.md) - Fetch latest from sources
- [`aam verify`](verify.md) - Check package file integrity
- [`aam diff`](diff.md) - View file modifications

## Notes

### Source-Only

`aam outdated` only reports updates for packages installed from git sources. Registry-installed packages are shown as "(no source)" because they use fixed versions.

### Local Modifications

Packages with local modifications are flagged as "outdated (modified)". Run `aam diff <package>` to inspect changes before upgrading with `aam upgrade`.
