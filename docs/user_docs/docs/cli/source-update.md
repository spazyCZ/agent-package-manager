# aam source update

**Source Management**

## Synopsis

```bash
aam source update [SOURCE_NAME] [OPTIONS]
```

## Description

Fetch upstream changes for one or all sources. Produces a change report
showing new, modified, and removed artifacts compared to the last fetch.

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| SOURCE_NAME | No | Specific source to update (or use `--all`) |

## Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--all` | `-a` | false | Update all configured sources |
| `--dry-run` | | false | Preview changes without fetching |

## Examples

### Example 1: Update a specific source

```bash
aam source update openai/skills
```

**Output:**
```
  openai/skills — updated (abc123 → def456)

  New artifacts (2):
    + debugging-assistant  (skill)
    + prompt-optimizer     (prompt)

  Modified (1):
    ~ code-review          (skill)

  No changes: 0 removed
```

### Example 2: Update all sources

```bash
aam source update --all
```

### Example 3: Dry-run preview

```bash
aam source update openai/skills --dry-run
```

## See also

- [aam source add](source-add.md) - Add a source
- [aam source scan](source-scan.md) - Scan for artifacts
- [aam source enable-defaults](source-enable-defaults.md) - Enable
  default community sources
