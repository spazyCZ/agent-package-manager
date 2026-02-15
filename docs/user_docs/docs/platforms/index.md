# Platform Support Overview

AAM deploys AI agent artifacts to multiple platforms through **platform adapters**. Each adapter translates AAM's abstract artifact definitions (skills, agents, prompts, instructions) into platform-specific formats and locations.

## Supported Platforms

AAM supports 4 major AI coding platforms:

| Platform | Type | Strengths | Deployment Target |
|----------|------|-----------|-------------------|
| **[Cursor](cursor.md)** | Code editor | Native skill support, rule-based configuration | `.cursor/` directory |
| **[Claude Desktop](claude.md)** | AI assistant | Project-based instructions, skill support | `CLAUDE.md` file |
| **[GitHub Copilot](copilot.md)** | AI pair programmer | GitHub integration, instruction merging | `.github/` directory |
| **[OpenAI Codex](codex.md)** | Code generation | Native SKILL.md format, user-level skills | `AGENTS.md` file |

## Platform Comparison

### Feature Matrix

| Feature | Cursor | Copilot | Claude | Codex |
|---------|--------|---------|--------|-------|
| **Skills** | Native SKILL.md | SKILL.md | SKILL.md | Native SKILL.md |
| **Agents** | Converted to rules | Merged sections | Merged sections | Merged sections |
| **Prompts** | Separate files | Separate files | Separate files | Separate files |
| **Instructions** | Converted to rules | Merged sections | Merged sections | Merged sections |
| **Merging strategy** | Separate files | Marker-based | Marker-based | Marker-based |
| **Skill scope** | Project or user | Project | Project | Project or user |
| **Configuration complexity** | Medium | Low | Low | Low |

### Deployment Strategies

**Separate files (Cursor):**
- Each artifact deployed as a separate file
- Clear file organization
- Easy to manage individual artifacts
- Rules system for agents and instructions

**Marker-based merging (Copilot, Claude, Codex):**
- Agents and instructions merge into single file
- Uses `<!-- BEGIN AAM -->` / `<!-- END AAM -->` markers
- Preserves user-written content
- Clean updates and removals

## Configuring Platforms

### Default Platform

Set the default platform for new projects:

```bash
aam config set default_platform cursor
```

Or configure in `~/.aam/config.yaml`:

```yaml
# Default platform for deployment
default_platform: cursor
```

### Active Platforms

Deploy to multiple platforms simultaneously:

```bash
# Set active platforms via CLI
aam config set active_platforms cursor,claude,copilot
```

Or in `~/.aam/config.yaml`:

```yaml
# Active platforms (deploy to all listed platforms)
active_platforms:
  - cursor
  - claude
  - copilot
```

When you run `aam install`, artifacts deploy to **all active platforms**.

### Platform-Specific Configuration

Each platform has its own configuration options:

```yaml
# ~/.aam/config.yaml or .aam/config.yaml

platforms:
  cursor:
    skill_scope: project              # "project" or "user"
    deploy_instructions_as: rules     # Always "rules"

  copilot:
    merge_instructions: true          # Merge into copilot-instructions.md

  claude:
    merge_instructions: true          # Merge into CLAUDE.md

  codex:
    skill_scope: user                 # "project" or "user"
```

See each platform's documentation for detailed configuration options.

## Multi-Platform Deployment

### Deploy to All Active Platforms

```bash
# Install package and deploy to all active platforms
aam install @author/asvc-auditor

# Result:
# - Cursor: .cursor/skills/, .cursor/rules/
# - Claude: CLAUDE.md, .claude/skills/
# - Copilot: .github/copilot-instructions.md, .github/skills/
```

### Deploy to Specific Platform

```bash
# Deploy only to Cursor
aam deploy --platform cursor

# Deploy only to Claude
aam deploy --platform claude

# Deploy to multiple specific platforms
aam deploy --platform cursor --platform copilot
```

### Verify Deployment

Check where artifacts were deployed:

```bash
# List all deployed artifacts
aam list

# Output shows deployment locations per platform:
# cursor: .cursor/skills/author--asvc-report/
# claude: .claude/skills/author--asvc-report/
# copilot: .github/skills/author--asvc-report/
```

## Choosing the Right Platform

### Use Cursor if you:
- Want native skill support with script execution
- Prefer rule-based agent configuration
- Need file-level or glob-based instruction scoping
- Use Cursor as your primary editor

### Use Claude Desktop if you:
- Work with Anthropic's Claude AI
- Prefer project-based instruction files
- Want marker-based content merging
- Need clear separation of AAM vs manual content

### Use GitHub Copilot if you:
- Use GitHub Copilot for pair programming
- Want instructions in `.github/` directory
- Need GitHub integration
- Prefer marker-based merging

### Use OpenAI Codex if you:
- Work with OpenAI's code generation tools
- Want native SKILL.md support
- Prefer user-level skill storage
- Use AGENTS.md for agent definitions

## Scoped Package Names

All platforms use the **double-hyphen convention** for scoped package names:

| Package Name | Filesystem Name |
|-------------|-----------------|
| `asvc-report` | `asvc-report` |
| `@author/asvc-report` | `author--asvc-report` |
| `@my-org/code-reviewer` | `my-org--code-reviewer` |

This ensures filesystem compatibility across all platforms while preserving package scope information.

## Common Workflows

### Single Platform Development

```yaml
# ~/.aam/config.yaml
default_platform: cursor
active_platforms:
  - cursor
```

```bash
aam install @author/asvc-auditor
# Deploys only to Cursor
```

### Multi-Platform Publishing

```yaml
# ~/.aam/config.yaml
active_platforms:
  - cursor
  - claude
  - copilot
  - codex
```

```bash
aam install @author/asvc-auditor
# Deploys to all 4 platforms
```

### Platform-Specific Projects

```yaml
# .aam/config.yaml (project-level)
default_platform: claude
active_platforms:
  - claude

platforms:
  claude:
    merge_instructions: true
```

### Testing Across Platforms

```bash
# Test on each platform individually
aam deploy --platform cursor
aam deploy --platform claude
aam deploy --platform copilot
aam deploy --platform codex

# Verify each deployment
ls -R .cursor/
cat CLAUDE.md
cat .github/copilot-instructions.md
cat AGENTS.md
```

## Troubleshooting

### Artifacts Not Deploying

**Check active platforms:**

```bash
aam config get active_platforms
```

**Verify platform is active:**

```bash
# Add platform to active list
aam config set active_platforms cursor,claude
```

### Wrong Deployment Location

**Check platform configuration:**

```bash
aam config get platforms
```

**Verify skill scope settings:**

```yaml
platforms:
  cursor:
    skill_scope: project  # or "user"
```

### Merge Conflicts

**Marker-based platforms (Copilot, Claude, Codex):**

If you manually edit content between AAM markers, it will be overwritten on next deploy.

**Solution:**
- Keep AAM-managed content within markers
- Add your own content outside markers
- Never edit content between `<!-- BEGIN AAM -->` and `<!-- END AAM -->`

### Platform Not Found

**Error:** `Platform 'xyz' not found`

**Cause:** Platform adapter not implemented or typo in platform name.

**Solution:**

```bash
# List available platforms
aam platforms

# Valid platforms: cursor, copilot, claude, codex
```

## Converting Between Platforms

Use `aam convert` to migrate existing platform configurations between any two platforms:

```bash
# Convert Cursor configs to Copilot format
aam convert -s cursor -t copilot

# Preview conversion without writing files
aam convert -s copilot -t claude --dry-run

# Convert only instructions
aam convert -s cursor -t claude --type instruction
```

The convert command handles field mapping (e.g. Cursor `globs` ↔ Copilot `applyTo`),
strips unsupported metadata, and warns about lossy conversions. Skills use a
universal format and are directly copied.

See [`aam convert`](../cli/convert.md) for the full reference.

## Next Steps

Explore each platform's detailed deployment guide:

- **[Cursor](cursor.md)** - Cursor editor deployment guide
- **[Claude Desktop](claude.md)** - Claude Desktop deployment guide
- **[GitHub Copilot](copilot.md)** - GitHub Copilot deployment guide
- **[OpenAI Codex](codex.md)** - OpenAI Codex deployment guide

Or continue learning:

- [Platform Adapters Concept](../concepts/platform-adapters.md) - Deep dive into adapter architecture
- [`aam convert` CLI Reference](../cli/convert.md) - Cross-platform conversion command
- [Configuration: Project config](../configuration/project.md) - Platform settings in config
- [Getting Started: Quick Start](../getting-started/quickstart.md) - Hands-on package installation
