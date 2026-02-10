# aam source candidates

**Source Management**

## Synopsis

```bash
aam source candidates [OPTIONS]
```

## Description

List unpackaged artifact candidates across all (or a specific) registered
sources. Candidates are artifacts discovered in source repositories that
have not yet been packaged in the current workspace.

Use this to find artifacts you can package with
`aam pkg create --from-source`.

## Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--source` | `-s` | (all) | Filter by source name |
| `--type` | `-t` | (all) | Filter by artifact type (repeatable) |
| `--json` | | false | Output as JSON |

## Examples

### Example 1: List all candidates

```bash
aam source candidates
```

**Output:**
```
  Unpackaged candidates (15):

  openai/skills (12):
    code-review       skill   skills/code-review/SKILL.md
    code-gen          skill   skills/code-gen/SKILL.md
    architect         agent   agents/architect/agent.yaml
    ...

  github/awesome-copilot (3):
    copilot-helper    skill   skills/copilot-helper/SKILL.md
    ...
```

### Example 2: Filter by source and type

```bash
aam source candidates --source openai/skills --type skill
```

## See also

- [aam pkg create](create-package.md) - Create a package (supports
  `--from-source`)
- [aam source scan](source-scan.md) - Scan a source for artifacts
