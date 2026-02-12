# aam source enable-defaults

**Source Management**

## Synopsis

```bash
aam source enable-defaults [OPTIONS]
```

## Description

Enable all default community skill sources shipped with AAM. This
command registers the 4 curated default sources that provide immediate
access to popular skills, agents, and prompts from the community.

If any default sources were previously removed with
`aam source remove`, this command re-enables them by clearing their
entries from the `removed_defaults` list. Sources that are already
configured are skipped.

After enabling defaults, run `aam source update --all` to clone the
repositories and scan for artifacts.

## Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--json` | | false | Output as JSON |

## Default sources

AAM ships with 4 curated community sources:

| # | Name | Repository | Path |
|---|------|------------|------|
| 1 | `github/awesome-copilot` | github.com/github/awesome-copilot | `skills` |
| 2 | `openai/skills:.curated` | github.com/openai/skills | `skills/.curated` |
| 3 | `cursor/community-skills` | github.com/cursor/community-skills | `skills` |
| 4 | `anthropic/claude-prompts` | github.com/anthropic/claude-prompts | `prompts` |

## Examples

### Example 1: Enable all defaults

```bash
aam source enable-defaults
```

**Output:**
```
  ✓ github/awesome-copilot — added
  ✓ openai/skills:.curated — added
  ✓ cursor/community-skills — added
  ✓ anthropic/claude-prompts — added

  4 source(s) enabled, 0 already configured (out of 4 defaults)

  Run aam source update --all to clone and scan.

                   Default Skill Sources
  ┏━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┓
  ┃ # ┃ Name                      ┃ URL                                  ┃ Path            ┃
  ┡━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━┩
  │ 1 │ github/awesome-copilot    │ https://github.com/github/awesome-…  │ skills          │
  │ 2 │ openai/skills:.curated    │ https://github.com/openai/skills.…   │ skills/.curated │
  │ 3 │ cursor/community-skills   │ https://github.com/cursor/communit…  │ skills          │
  │ 4 │ anthropic/claude-prompts  │ https://github.com/anthropic/claud…  │ prompts         │
  └───┴───────────────────────────┴──────────────────────────────────────┴─────────────────┘
```

### Example 2: Re-enable after removing defaults

```bash
# Remove a default source
aam source remove openai/skills:.curated

# Later, re-enable all defaults
aam source enable-defaults
```

**Output:**
```
  ✓ openai/skills:.curated — re-enabled
  – github/awesome-copilot — already configured
  – cursor/community-skills — already configured
  – anthropic/claude-prompts — already configured

  1 source(s) enabled, 3 already configured (out of 4 defaults)

  Run aam source update --all to clone and scan.
```

### Example 3: JSON output

```bash
aam source enable-defaults --json
```

**Output:**
```json
{
  "registered": ["github/awesome-copilot", "openai/skills:.curated",
    "cursor/community-skills", "anthropic/claude-prompts"],
  "re_enabled": [],
  "skipped": [],
  "total": 4
}
```

## Behavior

1. AAM loads the current configuration.
2. For each of the 4 default sources:
    - If the source is already configured, it is skipped.
    - If the source was previously removed, it is cleared from
      `removed_defaults` and re-registered.
    - Otherwise, a new source entry is created with `default: true`.
3. Sources are registered without cloning. Run
   `aam source update --all` to clone and scan.

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error enabling defaults |

## See also

- [aam init](init.md) - Initial setup (also registers defaults)
- [aam source add](source-add.md) - Add a custom source
- [aam source list](source-list.md) - List configured sources
- [aam source remove](source-remove.md) - Remove a source
- [aam source update](source-update.md) - Fetch upstream changes
