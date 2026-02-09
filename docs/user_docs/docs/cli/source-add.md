# aam source add

**Source Management**

## Synopsis

```bash
aam source add SOURCE [OPTIONS]
```

## Description

Register a remote git repository as an artifact source. AAM clones the
repository, scans it for artifacts (skills, agents, prompts, instructions),
and saves the source entry to your configuration.

After adding a source, use `aam source scan` to list discovered artifacts
or `aam source candidates` to see what you can package.

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| SOURCE | Yes | Git source URL or shorthand (see formats below) |

### Source URL formats

- `owner/repo` - GitHub shorthand (for example, `openai/skills`)
- `https://github.com/owner/repo` - HTTPS URL
- `git@github.com:owner/repo` - SSH URL
- `git+https://github.com/owner/repo` - Explicit git+https
- `https://github.com/owner/repo/tree/main/path` - HTTPS tree URL with
  path and ref

### Inline modifiers

- `owner/repo@branch` - Track specific branch or tag
- `owner/repo#sha` - Pin to specific commit SHA
- `owner/repo:subdir` - Scan a subdirectory only

## Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--ref` | | `main` | Branch, tag, or commit SHA to track |
| `--path` | | (root) | Subdirectory within the repo to scan |
| `--name` | | (auto) | Custom display name for the source |

## Examples

### Example 1: Add with GitHub shorthand

```bash
aam source add openai/skills
```

**Output:**
```
  Source added: openai/skills
  URL:          https://github.com/openai/skills.git
  Ref:          main
  Artifacts:    12 discovered (8 skills, 3 agents, 1 prompt)
```

### Example 2: Add with subdirectory and branch

```bash
aam source add openai/skills --ref v2 --path skills/.curated
```

### Example 3: Add with custom name

```bash
aam source add https://github.com/myorg/private-skills.git --name myorg/skills
```

### Example 4: Add using inline modifiers

```bash
aam source add openai/skills@v2:.curated
```

## Behavior

1. AAM parses the source URL and validates the format.
2. A shallow clone of the repository is created in `~/.aam/cache/git/`.
3. The scanner runs over the cloned directory to discover artifacts.
4. The source entry is saved to `~/.aam/config.yaml`.

If a source with the same name already exists, the command fails with an
error. Use `aam source remove` first to replace an existing source.

## See also

- [aam source scan](source-scan.md) - Scan a source for artifacts
- [aam source list](source-list.md) - List configured sources
- [aam source remove](source-remove.md) - Remove a source
- [aam source update](source-update.md) - Fetch upstream changes
