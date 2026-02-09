# aam source scan

**Source Management**

## Synopsis

```bash
aam source scan SOURCE_NAME [OPTIONS]
```

## Description

Scan a registered source for artifacts. Runs the artifact scanner on the
cached clone and displays discovered skills, agents, prompts, and
instructions.

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| SOURCE_NAME | Yes | Display name of the registered source |

## Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--type` | `-t` | (all) | Filter by artifact type (repeatable) |
| `--json` | | false | Output as JSON |

## Examples

### Example 1: Scan all artifacts

```bash
aam source scan openai/skills
```

**Output:**
```
  openai/skills — 12 artifacts

  Skills (8):
    code-review      Review code changes for quality issues
    code-gen         Generate code from natural language
    test-writer      Write unit tests for functions
    ...

  Agents (3):
    architect        Design system architectures
    ...

  Prompts (1):
    summarize        Summarize long documents
```

### Example 2: Filter by type

```bash
aam source scan openai/skills --type skill
```

## See also

- [aam source add](source-add.md) - Add a source
- [aam source candidates](source-candidates.md) - List unpackaged candidates
