# aam source list

**Source Management**

## Synopsis

```bash
aam source list [OPTIONS]
```

## Description

List all configured remote git sources with their status, URL, tracked
ref, last commit, and artifact count.

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
  Configured sources (3):

  Name                      URL                                    Ref    Artifacts
  openai/skills (default)   github.com/openai/skills               main   12
  github/awesome-copilot    github.com/github/awesome-copilot      main   8
  myorg/internal-skills     github.com/myorg/internal-skills       v2     5
```

Sources marked `(default)` were automatically registered during
`aam init`. You can remove them with `aam source remove`.

## See also

- [aam source add](source-add.md) - Add a source
- [aam source remove](source-remove.md) - Remove a source
