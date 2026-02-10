# aam search

**Package Management**

## Synopsis

```bash
aam search QUERY [OPTIONS]
```

## Description

Search configured registries and git sources for packages matching a
query. Uses case-insensitive substring matching on package name,
description, and keywords. Returns packages from all configured
registries and sources, with version and **publisher** information.

Each result displays the publisher (the organization or registry that
provides the package) so you can identify the origin at a glance.

Use this to discover packages before installation.

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| QUERY | Yes | Search query (case-insensitive substring) |

## Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--limit` | `-l` | 10 | Maximum number of results to display |
| `--type` | `-t` | all | Filter by artifact type (skill, agent, prompt, instruction) |
| `--json` | | false | Output results as JSON |

## Examples

### Example 1: Basic search

```bash
aam search chatbot
```

**Output:**
```
Search results for "chatbot" (3 matches):

  chatbot-agent  1.2.0  local
    Conversational AI agent for customer support
    [skill, agent, prompt]

  advanced-chatbot  2.0.0  local
    Advanced chatbot with context awareness
    [agent, prompt, instruction]

  chatbot-skills  0.5.0  local
    Reusable skills for chatbot development
    [skill]
```

The publisher name appears after the version (for example, `local` for
packages from a local registry).

### Example 2: Search with type filter

```bash
aam search audit --type skill
```

**Output:**
```
Search results for "audit" (2 matches):

  asvc-audit-skill  1.0.0  local
    ASVC compliance audit skill
    [skill]

  security-audit  0.8.0  local
    Security audit automation skill
    [skill]
```

### Example 3: Limit results

```bash
aam search agent --limit 3
```

**Output:**
```
Search results for "agent" (3 matches):

  my-agent  1.0.0  local
    General purpose automation agent
    [agent, skill]

  code-review-agent  2.1.0  local
    Agent for automated code reviews
    [agent, prompt]

  data-agent  1.5.0  local
    Data analysis and reporting agent
    [agent, skill, prompt]
```

### Example 4: JSON output

```bash
aam search chatbot --json
```

**Output:**
```json
[
  {
    "name": "chatbot-agent",
    "version": "1.2.0",
    "description": "Conversational AI agent for customer support",
    "keywords": ["chatbot", "support", "ai"],
    "artifact_types": ["skill", "agent", "prompt"],
    "registry": "local"
  },
  {
    "name": "advanced-chatbot",
    "version": "2.0.0",
    "description": "Advanced chatbot with context awareness",
    "keywords": ["chatbot", "context", "advanced"],
    "artifact_types": ["agent", "prompt", "instruction"],
    "registry": "local"
  }
]
```

### Example 5: No results

```bash
aam search nonexistent-package-xyz
```

**Output:**
```
No packages found matching "nonexistent-package-xyz".
```

### Example 6: Search across registries and git sources

```bash
aam search doc
```

Results from both registries and git sources are combined. Source
artifacts display the publisher and full source name so you can tell
where each result originates.

**Output:**
```
Search results for "doc" (5 matches):

  docs-changelog  source@da66c7c  google-gemini (google-gemini/gemini-cli:skills)
    Generate changelog files from release information
    [skill]

  docs-writer  source@da66c7c  google-gemini (google-gemini/gemini-cli:skills)
    Write and review documentation files
    [skill]

  notion-research-documentation  source@4ab6e0f  openai (openai/skills:.curated)
    Research documentation via Notion
    [skill]

  openai-docs  source@4ab6e0f  openai (openai/skills:.curated)
    OpenAI documentation reference
    [skill]

  doc  source@4ab6e0f  openai (openai/skills:.curated)
    General documentation skill
    [skill]
```

The publisher name (for example, `google-gemini` or `openai`) appears
in magenta, followed by the full source name in parentheses.

### Example 7: Filter multiple types

Currently filtering multiple types requires separate searches:

```bash
aam search data --type skill
aam search data --type agent
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error - no registries configured |

## Search behavior

### Matching algorithm

Search uses case-insensitive substring matching on:

- **Package name** — matches anywhere in the name
- **Description** — matches anywhere in the description
- **Keywords** — matches any keyword exactly

Example: Query `"audit"` matches:

- `audit-agent` (name)
- `security-auditor` (name)
- Package with description "ASVC audit tool" (description)
- Package with keyword `audit` (keyword)

### Result ordering

Registry results appear first, followed by git-source results. Within
each group, results are returned in the order they are discovered.

### Publisher display

Every result shows its publisher or origin:

- **Registry packages** display the registry name (for example, `local`
  or `company-registry`).
- **Source artifacts** display the publisher organization and the full
  source name. For example, `openai (openai/skills:.curated)` tells you
  the artifact comes from the `openai` organization, specifically the
  `openai/skills:.curated` source.

## Related commands

- [`aam install`](install.md) - Install a package found via search
- [`aam info`](info.md) - Show details about an installed package
- [`aam registry list`](registry-list.md) - List configured registries
- [`aam source list`](source-list.md) - List configured git sources

## Notes

### No Registries Configured

If you haven't configured any registries:

```
Error: No registries configured. Run 'aam registry init' to create one.
```

### Keyword Matching

Packages can specify keywords in their `aam.yaml` manifest:

```yaml
keywords:
  - chatbot
  - automation
  - customer-support
```

These are indexed by the registry for better search results.

### Case Sensitivity

All searches are case-insensitive:

- `aam search Agent` finds "agent", "AGENT", "Agent"
- `aam search CHATBOT` finds "chatbot", "ChatBot", "chatbot-agent"

### Partial Matches

The search uses substring matching, not prefix matching:

- Query `"bot"` matches "chatbot", "robot", "bot-skill"
- Query `"chat"` matches "chatbot", "chat-agent", "chat-utility"

### Performance

Search performance depends on registry size. Local registries are typically fast. HTTP registries may have server-side indexing for faster results.

### Future Enhancements

Planned features for future versions:

- Fuzzy matching for typo tolerance
- Relevance scoring and ranking
- Multiple type filters (`--type skill --type agent`)
- Sorting options (`--sort downloads`, `--sort recent`)
