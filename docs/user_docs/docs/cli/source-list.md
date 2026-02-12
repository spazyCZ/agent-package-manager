# aam source list

**Source Management**

## Synopsis

```bash
aam source list [OPTIONS]
```

## Description

List all configured remote git sources with their status, publisher,
URL, tracked ref, sub-path, artifact count, and last-fetched date.

The **Publisher** column shows the GitHub organization or owner that
maintains the source repository. It is extracted automatically from the
source name (the segment before the first `/`).

## Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--json` | | false | Output as JSON |

## Examples

### Example 1: List sources

```bash
aam source list
```

**Output:**
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Name                            ┃ Publisher      ┃ URL                       ┃ Ref  ┃ Path            ┃ Artifacts ┃ Last Fetched ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ google-gemini/gemini-cli:skills │ google-gemini  │ github.com/google-gemini… │ main │ .gemini/skills  │         4 │ 2026-02-09   │
│ openai/skills:.curated          │ openai         │ github.com/openai/skills  │ main │ skills/.curated │        30 │ 2026-02-10   │
└─────────────────────────────────┴────────────────┴───────────────────────────┴──────┴─────────────────┴───────────┴──────────────┘

  Total: 2 source(s)
```

The **Publisher** column (`google-gemini`, `openai`) lets you quickly
identify who maintains each source. Sources marked `(default)` were
automatically registered during `aam init`. You can remove them with
`aam source remove`.

### Example 2: JSON output

```bash
aam source list --json
```

The JSON output includes all fields shown in the table, plus `type`,
`last_commit`, and `default` flags.

## See also

- [aam source add](source-add.md) - Add a source
- [aam source remove](source-remove.md) - Remove a source
- [aam source enable-defaults](source-enable-defaults.md) - Enable
  default community sources
