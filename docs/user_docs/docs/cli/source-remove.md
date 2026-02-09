# aam source remove

**Source Management**

## Synopsis

```bash
aam source remove SOURCE_NAME [OPTIONS]
```

## Description

Remove a configured remote source from your configuration. If the source
was a default (added during `aam init`), it's recorded in
`removed_defaults` so it won't be re-added on future initializations.

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| SOURCE_NAME | Yes | Display name of the source to remove |

## Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--purge-cache` | | false | Also delete the cached clone directory |

## Examples

### Example 1: Remove a source

```bash
aam source remove openai/skills
```

**Output:**
```
  Source removed: openai/skills
```

### Example 2: Remove and purge cache

```bash
aam source remove openai/skills --purge-cache
```

**Output:**
```
  Source removed: openai/skills
  Cache purged: ~/.aam/cache/git/github.com/openai/skills/
```

## See also

- [aam source list](source-list.md) - List sources
- [aam source add](source-add.md) - Add a source
