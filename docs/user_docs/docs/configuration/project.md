# Project Configuration Reference

The project configuration file (`.aam/config.yaml`) defines project-specific settings that override global configuration and are shared with your team via version control.

## File Location

```
my-project/
└── .aam/
    └── config.yaml  ← Project configuration
```

Created automatically by `aam init`.

## When to Use Project Config

Use `.aam/config.yaml` to define settings that should apply to all team members working on the project:

- **Platform overrides** - Force a specific platform for this project
- **Registry additions** - Add project-specific package sources
- **Platform-specific config** - Override skill deployment scope, instruction merging, etc.
- **Security policies** - Enforce stricter verification for sensitive projects

**Do NOT use for:**
- Personal preferences (use global config instead)
- Credentials or tokens (use `~/.aam/credentials.yaml`)

## Version Control

**Always commit `.aam/config.yaml` to Git.**

This ensures all team members use consistent configuration when working on the project.

```bash
git add .aam/config.yaml
git commit -m "Add AAM project configuration"
```

## Schema Reference

Project config supports the same schema as global config, with a focus on project-specific overrides.

### Supported Fields

| Field | Type | Description |
|-------|------|-------------|
| `default_platform` | string | Override default platform for this project |
| `active_platforms` | list[string] | Override active platforms |
| `registries` | list[RegistrySource] | Additional registries (merged with global) |
| `platforms` | dict[string, PlatformConfig] | Platform-specific deployment config |
| `security` | SecurityConfig | Project security policies |

**Note:** `author` and `publish` are typically not set in project config (they're personal preferences).

## Configuration Precedence

Project config overrides global config:

```
Project (.aam/config.yaml)  >  Global (~/.aam/config.yaml)  >  Defaults
```

### Merging Behavior

**Simple values** (strings, booleans): Project config replaces global config

```yaml
# Global config
default_platform: cursor

# Project config
default_platform: copilot

# Result: copilot
```

**Lists and nested objects**: Deep merge (combined, not replaced)

```yaml
# Global config
registries:
  - name: aam-central
    url: https://registry.aam.dev
    type: http

# Project config
registries:
  - name: company
    url: https://github.com/mycompany/aam-registry
    type: git

# Result: Both registries available
#   1. aam-central
#   2. company
```

## Section: `default_platform`

**Type:** `string`
**Valid values:** `"cursor"`, `"copilot"`, `"claude"`, `"codex"`

Override the default platform for this project:

```yaml
default_platform: copilot
```

**Use case:** Your team uses GitHub Copilot, but AAM defaults to Cursor globally.

## Section: `active_platforms`

**Type:** `list[string]`

Override which platforms to deploy to with `aam deploy --all`:

```yaml
active_platforms:
  - cursor
  - claude
```

**Use case:** Project needs artifacts deployed to multiple platforms, regardless of individual developer preferences.

## Section: `registries`

**Type:** `list[RegistrySource]`

Add project-specific registries. These are **merged** with global registries.

```yaml
registries:
  - name: project-packages
    url: file:///path/to/project/packages
    type: local
```

**Use case:** Project has local packages not published to a registry.

### Example: Private Company Registry

```yaml
registries:
  - name: company-private
    url: https://github.com/mycompany/private-aam-registry
    type: git
    default: false
```

All team members will automatically have access to company packages when they clone the repo.

## Section: `platforms`

**Type:** `dict[string, PlatformConfig]`

Platform-specific deployment configuration. Overrides platform defaults.

### PlatformConfig Schema

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `skill_scope` | string | `"project"` | Where to deploy skills: `project` or `user` |
| `deploy_instructions_as` | string | `"rules"` | How to deploy instructions: `rules` or `instructions` |
| `merge_instructions` | bool | `false` | Merge all instructions into one file |

### Example: Cursor Platform Config

```yaml
platforms:
  cursor:
    skill_scope: project        # Deploy to .cursor/skills/ (not ~/.cursor/skills/)
    deploy_instructions_as: rules  # Deploy instructions as .mdc rule files
```

### Example: Claude Platform Config

```yaml
platforms:
  claude:
    merge_instructions: true    # Merge all instructions into CLAUDE.md
```

### Example: Multiple Platforms

```yaml
platforms:
  cursor:
    skill_scope: project
    deploy_instructions_as: rules
  copilot:
    merge_instructions: true
  claude:
    merge_instructions: true
```

### Field: `skill_scope`

**Type:** `string`
**Default:** `"project"`
**Valid values:** `"project"`, `"user"`

Controls where skills are deployed:

- `project`: Deploy to `.cursor/skills/` (project-local, committed to git)
- `user`: Deploy to `~/.cursor/skills/` (user-global, not committed)

```yaml
platforms:
  cursor:
    skill_scope: user  # Deploy to ~/.cursor/skills/
```

**Recommendation:** Use `project` for team projects (default).

### Field: `deploy_instructions_as`

**Type:** `string`
**Default:** `"rules"`
**Valid values:** `"rules"`, `"instructions"`

Cursor-specific: How to deploy instruction artifacts:

- `rules`: Deploy as `.mdc` rule files in `.cursor/rules/`
- `instructions`: Deploy as `.md` files in `.cursor/instructions/`

```yaml
platforms:
  cursor:
    deploy_instructions_as: instructions
```

### Field: `merge_instructions`

**Type:** `bool`
**Default:** `false`

Whether to merge all instruction artifacts into a single file:

- Claude: Merge into `CLAUDE.md`
- Copilot: Merge into `.github/copilot-instructions.md`

```yaml
platforms:
  claude:
    merge_instructions: true
```

## Section: `security`

**Type:** `SecurityConfig`

Project-level security policies. Overrides global security settings.

```yaml
security:
  require_signature: true
  on_signature_failure: error
  trusted_identities:
    - "*@mycompany.com"
```

**Use case:** Enforce stricter verification for production projects.

### Example: High-Security Project

```yaml
security:
  require_checksum: true       # Always enforced
  require_signature: true      # Reject unsigned packages
  on_signature_failure: error  # Fail on bad signature
  trusted_identities:
    - "*@trustedorg.com"       # Only trust packages from trustedorg.com
```

## Complete Example: Project Config

```yaml
# .aam/config.yaml — Project-level configuration

# Force Cursor for this project (overrides global default)
default_platform: cursor

# Deploy to Cursor and Claude
active_platforms:
  - cursor
  - claude

# Add project-specific registry
registries:
  - name: company-private
    url: https://github.com/mycompany/private-aam-registry
    type: git

# Platform-specific configuration
platforms:
  cursor:
    skill_scope: project        # Deploy to .cursor/skills/
    deploy_instructions_as: rules  # Use .mdc rules
  claude:
    merge_instructions: true    # Merge into CLAUDE.md

# Enforce strict security
security:
  require_signature: true
  on_signature_failure: error
  trusted_identities:
    - "*@mycompany.com"
```

## Common Project Configurations

### Configuration: Cursor-Only Project

Deploy only to Cursor with project-local skills:

```yaml
default_platform: cursor
active_platforms:
  - cursor

platforms:
  cursor:
    skill_scope: project
```

### Configuration: Multi-Platform Project

Deploy to Cursor, Claude, and Copilot:

```yaml
active_platforms:
  - cursor
  - claude
  - copilot

platforms:
  cursor:
    skill_scope: project
  claude:
    merge_instructions: true
  copilot:
    merge_instructions: true
```

### Configuration: Private Package Registry

Use a company-specific registry:

```yaml
registries:
  - name: company
    url: https://github.com/mycompany/aam-registry
    type: git
    default: true  # Prefer company packages

security:
  require_signature: true
  trusted_identities:
    - "*@mycompany.com"
```

### Configuration: Local Development

Use a local registry for testing packages before publishing:

```yaml
registries:
  - name: local-dev
    url: file:///path/to/local/packages
    type: local
    default: true
```

## Creating Project Config

### Automatic Creation

Created automatically by `aam init`:

```bash
cd my-project
aam init
# Creates .aam/config.yaml with defaults
```

### Manual Creation

```bash
mkdir -p .aam
touch .aam/config.yaml
```

Edit with your preferred editor:

```yaml
default_platform: cursor
```

### Using CLI

```bash
# Set project-level values (from project root)
aam config set --project default_platform cursor
aam config set --project platforms.cursor.skill_scope project
```

## Validating Project Config

```bash
# Validate project config
aam config validate --project

# Show merged config (global + project)
aam config show
```

## Team Workflow

### For Project Maintainers

1. Create `.aam/config.yaml` with team-wide settings:

```yaml
default_platform: cursor
active_platforms:
  - cursor
  - claude

platforms:
  cursor:
    skill_scope: project
```

2. Commit to version control:

```bash
git add .aam/config.yaml
git commit -m "Add AAM project configuration"
git push
```

### For Team Members

1. Clone the repository:

```bash
git clone https://github.com/myteam/project
cd project
```

2. Install AAM packages:

```bash
aam install
# Uses .aam/config.yaml automatically
```

3. Personal overrides (optional):

If you prefer a different platform locally, use global config or CLI flags:

```bash
# Override with global config
aam config set default_platform copilot

# Or use CLI flag
aam deploy --platform copilot
```

Project config still applies for `aam install` and other operations.

## Troubleshooting

### Configuration Not Applied

Check precedence order:
```bash
aam config show
# Shows merged configuration from all sources
```

### Registry Not Found

Ensure registry URL is correct:
```bash
aam config get registries
```

Test registry connectivity:
```bash
aam search test --registry company
```

### Platform Config Ignored

Verify platform name spelling:
```yaml
# Correct
platforms:
  cursor:
    skill_scope: project

# Incorrect (typo)
platforms:
  curser:  # ← typo
    skill_scope: project
```

Valid platform names: `cursor`, `copilot`, `claude`, `codex`

## Migration

### From Global to Project Config

Move team-wide settings from global to project config:

```bash
# 1. Copy relevant settings from global config
aam config show --global > temp.yaml

# 2. Edit temp.yaml, remove personal preferences

# 3. Create project config
mkdir -p .aam
cp temp.yaml .aam/config.yaml

# 4. Commit to git
git add .aam/config.yaml
git commit -m "Add project configuration"
```

### From Project to Global Config

Move personal preferences to global config:

```bash
# Set in global config
aam config set --global default_platform cursor

# Remove from project config
aam config unset --project default_platform
```

## Next Steps

- [Global Configuration](global.md) - User-level preferences
- [Configuration Overview](index.md) - Precedence and merging
- [Security Configuration](security.md) - Advanced security policies
- [CLI Reference: config](../cli/config-list.md) - `aam config` commands
