# aam search

**Package Management**

## Synopsis

```bash
aam search [QUERY] [OPTIONS]
```

## Description

Search configured registries and git sources for packages matching
a query. AAM uses **relevance-ranked scoring** with tiered matching
on package name, keywords, and description. Results appear in a
scannable table sorted by relevance score by default.

Each result displays its origin (registry name or git source name)
so you can identify where it comes from at a glance.

Use this command to discover packages before installation.

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| QUERY | No | Search query (case-insensitive). Omit for browse mode. |

## Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--limit` | `-l` | 255 | Maximum results to display (1--255) |
| `--type` | `-t` | all | Filter by artifact type. Repeatable for OR logic. |
| `--source` | `-s` | all | Limit results to a specific git source name |
| `--registry` | `-r` | all | Limit results to a specific registry name |
| `--sort` | | relevance | Sort order: `relevance`, `name`, or `recent` |
| `--json` | | false | Output results as JSON envelope |

## Examples

### Basic search

```bash
aam search chatbot
```

**Output:**

```
        Search results for "chatbot" (3 matches)
 Name              Version   Type    Source  Description
 chatbot           1.0.0     agent   local   Conversational AI agent
 chatbot-agent     1.2.0     skill   local   Customer support chatbot
 my-chatbot-skill  0.5.0     skill   local   Reusable chatbot skills
```

Results are ranked by relevance: exact name match first, then
prefix, then substring, then keyword, then description matches.

### Filter by artifact type

```bash
aam search audit --type skill
```

Only packages with artifact type `skill` are shown.

### Multiple type filters

```bash
aam search data --type skill --type agent
```

This shows packages that have artifact type `skill` **or** `agent`
(OR logic). Repeat `--type` for each type you want to include.

### Filter by source

```bash
aam search doc --source google-gemini
```

Only results from the `google-gemini` git source are shown.
Registry results are excluded. To install a result from a specific source,
use the qualified name `source/artifact` (e.g., `google-gemini/gemini-skills/doc-writer`) — see [`aam install`](install.md) (qualified name format: `source/artifact`).

### Sort alphabetically

```bash
aam search agent --sort name
```

Results are sorted alphabetically by package name instead of by
relevance score.

### Sort by most recent

```bash
aam search agent --sort recent
```

Results are sorted by most recently updated first.

### JSON output

```bash
aam search chatbot --json
```

**Output:**

```json
{
  "results": [
    {
      "name": "chatbot",
      "version": "1.0.0",
      "description": "Conversational AI agent",
      "keywords": ["chatbot", "ai"],
      "artifact_types": ["agent"],
      "origin": "local",
      "origin_type": "registry",
      "score": 100,
      "updated_at": "2026-01-15T10:30:00Z"
    }
  ],
  "total_count": 1,
  "warnings": []
}
```

!!! warning "Breaking change (v0.1.0)"
    The `--json` output format changed from a flat array to an
    envelope object with `results`, `total_count`, and `warnings`
    keys.

### No results with suggestions

```bash
aam search chatbt
```

**Output:**

```
No packages found matching "chatbt".

Did you mean: chatbot, chatbot-agent, chatbot-skills
```

When no results match, AAM checks for similar package names and
displays up to 3 suggestions.

### Browse all packages

```bash
aam search
```

Omitting the query returns all packages up to the limit, sorted by
name. This is useful for exploring what's available.

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (no registries or sources configured, invalid arguments) |

## Search behavior

### Relevance scoring

AAM uses a **tiered scoring algorithm** where each result receives
the score of its highest matching tier:

| Tier | Match type | Score | Example (query: `audit`) |
|------|-----------|-------|--------------------------|
| 1 | Exact name match | 100 | Package named `audit` |
| 2 | Name starts with query | 80 | `audit-agent` |
| 3 | Name contains query | 60 | `security-audit` |
| 4 | Keyword exact match | 50 | Keyword `audit` |
| 5 | Description contains query | 30 | "ASVS audit tool" |

Results that don't match any tier are excluded. All matching is
case-insensitive.

### Result ordering

By default, results are sorted by **relevance score** (highest
first). When two results have the same score, they are sub-sorted
alphabetically by name for deterministic output.

Alternative sort orders:

- `--sort name` -- alphabetical by package name
- `--sort recent` -- most recently updated first

### "Did you mean?" suggestions

When a search returns zero results, AAM compares the query against
all known package and artifact names using fuzzy matching. If any
name is sufficiently similar (at least 60% similarity), up to 3
suggestions are displayed.

This catches common typos:

- `chatbt` becomes chatbot
- `audiit` becomes audit
- `skil` becomes skill

### Filtering

You can narrow results with these options:

- **`--type`** -- repeatable. Filters results to packages that
  contain at least one of the specified artifact types. Unknown
  types generate a warning but don't cause an error.
- **`--source`** -- limits results to a specific git source.
  Registry results are excluded entirely.
- **`--registry`** -- limits results to a specific registry.
  Source results are excluded entirely.

### Browse mode

When you omit the query (`aam search`), all packages are returned
up to the limit, each with equal relevance score. This provides a
"browse all" capability.

### Origin display

Every result shows its origin in the Source column:

- **Registry packages** display the registry name (for example,
  `local`).
- **Source artifacts** display the git source name (for example,
  `google-gemini/gemini-skills`). The version column shows
  `source@<sha>` to indicate it comes from a git commit rather
  than a numbered release.

### Warning display

If a registry or source fails during search (for example, a
corrupted index or unreachable source), a warning is displayed but
search continues with the remaining sources. Warnings appear before
the results table.

## Related commands

- [`aam install`](install.md) -- install a package found via search
- [`aam info`](info.md) -- show details about an installed package
- [`aam registry list`](registry-list.md) -- list configured
  registries
- [`aam source list`](source-list.md) -- list configured git
  sources

## Notes

### No registries or sources configured

If you haven't configured any registries or sources:

```
Error: [AAM_NO_SOURCES] No registries or sources configured.
Run 'aam registry init' or 'aam source add' to get started.
```

### Case sensitivity

All searches are case-insensitive:

- `aam search Agent` finds "agent," "AGENT," and "Agent"
- `aam search CHATBOT` finds "chatbot," "ChatBot," and
  "chatbot-agent"

### Partial matches

The search uses substring matching, not prefix matching:

- Query `"bot"` matches "chatbot," "robot," and "bot-skill"
- Query `"chat"` matches "chatbot," "chat-agent," and
  "chat-utility"

### Performance

Search completes within 2 seconds for up to 500 indexed packages
across local registries and cached sources.
