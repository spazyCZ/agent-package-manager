# aam search

**Package Management**

## Synopsis

```bash
aam search QUERY [OPTIONS]
```

## Description

Search configured registries for packages matching a query. Uses case-insensitive substring matching on package name, description, and keywords. Returns packages from all configured registries, with latest version information.

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

### Example 1: Basic Search

```bash
aam search chatbot
```

**Output:**
```
Search results for "chatbot" (3 packages):

  chatbot-agent  1.2.0
    Conversational AI agent for customer support
    [skill, agent, prompt]

  @author/advanced-chatbot  2.0.0
    Advanced chatbot with context awareness
    [agent, prompt, instruction]

  chatbot-skills  0.5.0
    Reusable skills for chatbot development
    [skill]
```

### Example 2: Search with Type Filter

```bash
aam search audit --type skill
```

**Output:**
```
Search results for "audit" (2 packages):

  asvc-audit-skill  1.0.0
    ASVC compliance audit skill
    [skill]

  security-audit  0.8.0
    Security audit automation skill
    [skill]
```

### Example 3: Limit Results

```bash
aam search agent --limit 3
```

**Output:**
```
Search results for "agent" (3 packages):

  my-agent  1.0.0
    General purpose automation agent
    [agent, skill]

  code-review-agent  2.1.0
    Agent for automated code reviews
    [agent, prompt]

  data-agent  1.5.0
    Data analysis and reporting agent
    [agent, skill, prompt]
```

### Example 4: JSON Output

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
    "name": "@author/advanced-chatbot",
    "version": "2.0.0",
    "description": "Advanced chatbot with context awareness",
    "keywords": ["chatbot", "context", "advanced"],
    "artifact_types": ["agent", "prompt", "instruction"],
    "registry": "local"
  }
]
```

### Example 5: No Results

```bash
aam search nonexistent-package-xyz
```

**Output:**
```
No packages found matching "nonexistent-package-xyz".
```

### Example 6: Search in Multiple Registries

```bash
aam search analytics
```

If you have multiple registries configured, results from all registries are shown:

**Output:**
```
Search results for "analytics" (4 packages):

  data-analytics  2.0.0
    Data analytics and visualization tools
    [skill, prompt]

  @company/analytics-agent  1.5.0      [registry: company-registry]
    Internal analytics automation agent
    [agent, skill]

  analytics-prompts  0.3.0
    Reusable prompts for analytics tasks
    [prompt]

  @author/ml-analytics  3.0.0          [registry: aam-central]
    Machine learning analytics suite
    [skill, agent]
```

### Example 7: Filter Multiple Types

Currently filtering multiple types requires multiple searches:

```bash
aam search data --type skill
aam search data --type agent
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error - no registries configured |

## Search Behavior

### Matching Algorithm

Search uses case-insensitive substring matching on:

- **Package name** - Matches anywhere in the name
- **Description** - Matches anywhere in the description
- **Keywords** - Matches any keyword exactly

Example: Query `"audit"` matches:

- `audit-agent` (name)
- `security-auditor` (name)
- Package with description "ASVC audit tool" (description)
- Package with keyword `audit` (keyword)

### Result Ordering

Results are returned in order discovered from registries. If you have multiple registries, results from the first configured registry appear first.

### Registry Source

When multiple registries are configured, the registry name is shown in brackets for packages from non-default registries.

## Related Commands

- [`aam install`](install.md) - Install a package found via search
- [`aam info`](info.md) - Show details about an installed package
- [`aam registry list`](registry-list.md) - List configured registries

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
