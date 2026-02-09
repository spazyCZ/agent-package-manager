# Configuration Overview

AAM uses a layered configuration system that allows you to customize behavior at different levels, from global user preferences to per-project overrides and command-line flags.

## Configuration Sources

AAM loads configuration from multiple sources with a well-defined precedence order:

1. **CLI flags** - Highest precedence (e.g., `--platform cursor`)
2. **Project config** - `.aam/config.yaml` in your project directory
3. **Global config** - `~/.aam/config.yaml` in your home directory
4. **Defaults** - Built-in defaults when nothing is configured

Each layer is merged with lower layers, with higher-precedence values overriding lower ones.

## Configuration Files

| File | Location | Purpose | Commit to Git? |
|------|----------|---------|----------------|
| [global.md](global.md) | `~/.aam/config.yaml` | User-level preferences and defaults | No |
| [project.md](project.md) | `.aam/config.yaml` | Project-specific overrides | Yes |
| [manifest.md](manifest.md) | `aam.yaml` | Package definition and metadata | Yes |
| [lock-files.md](lock-files.md) | `.aam/aam-lock.yaml` | Resolved dependency versions | Yes |

## Configuration Precedence

When AAM needs a configuration value, it follows this precedence order (highest to lowest):

```
CLI flags  >  Project config  >  Global config  >  Defaults
```

### Example: Platform Selection

Given:
- Global config: `default_platform: cursor`
- Project config: `default_platform: copilot`
- CLI flag: `--platform claude`

The CLI flag wins, and AAM uses `claude`.

### Example: Registry Configuration

Given:
- Global config defines 3 registries
- Project config adds 1 additional registry
- Result: All 4 registries are available (deep merge)

Deep merging applies to nested structures like `registries`, `security`, and `platforms`.

## Configuration File Locations

### Global Configuration (`~/.aam/config.yaml`)

| Operating System | Default Location |
|-----------------|------------------|
| Linux | `~/.aam/config.yaml` |
| macOS | `~/.aam/config.yaml` |
| Windows | `%USERPROFILE%\.aam\config.yaml` |

### Project Configuration (`.aam/config.yaml`)

Located in the `.aam/` directory at your project root. Created automatically by `aam init`.

## Quick Reference: All Configuration Keys

### Global/Project Config Keys

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `default_platform` | string | `"cursor"` | Platform to deploy to by default |
| `active_platforms` | list[string] | `["cursor"]` | Platforms to deploy to with `aam deploy --all` |
| `registries` | list[RegistrySource] | `[]` | Registry sources to search for packages |
| `security` | SecurityConfig | See [security.md](security.md) | Security and verification policies |
| `author` | AuthorConfig | `{}` | Default author info for `aam init` |
| `publish` | PublishConfig | `{}` | Publishing defaults |

### Manifest Keys (`aam.yaml`)

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `name` | string | Yes | Package name (scoped or unscoped) |
| `version` | string | Yes | Semver version |
| `description` | string | Yes | Package description (max 256 chars) |
| `artifacts` | ArtifactsDeclaration | Yes | Artifact declarations |
| `dependencies` | dict[string, string] | No | Package dependencies |
| `platforms` | dict[string, PlatformConfig] | No | Platform-specific config |
| `quality` | QualityConfig | No | Tests and evaluations |

See [manifest.md](manifest.md) for complete schema reference.

## Common Configuration Tasks

### Set Your Default Platform

```bash
aam config set default_platform cursor
```

### Add a Registry

```bash
aam config set registries[0].name "my-registry"
aam config set registries[0].url "https://registry.example.com"
aam config set registries[0].type "http"
```

Or edit `~/.aam/config.yaml` directly:

```yaml
registries:
  - name: my-registry
    url: https://registry.example.com
    type: http
```

### Set Author Defaults

```yaml
author:
  name: "Your Name"
  email: "you@example.com"
```

These values are used by `aam init` to pre-populate package metadata.

### Configure Security Policies

```yaml
security:
  require_checksum: true
  require_signature: false
  on_signature_failure: warn
```

See [security.md](security.md) for complete security configuration.

## Configuration Workflow

### For Individual Developers

1. Set global preferences in `~/.aam/config.yaml`:
   - Default platform
   - Author information
   - Personal registries

2. Use project config sparingly for project-specific overrides

### For Teams

1. Commit `.aam/config.yaml` to define team-wide settings:
   - Required registries
   - Platform configurations
   - Security policies

2. Team members inherit these settings automatically

3. Individual developers can still override with global config or CLI flags

## Environment Variables

AAM respects the following environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `AAM_HOME` | Override default `~/.aam/` directory | `/custom/path` |
| `AAM_CONFIG` | Override config file path | `/etc/aam/config.yaml` |
| `AAM_NO_COLOR` | Disable colored output | `1` |
| `AAM_REGISTRY_TOKEN` | Registry authentication token | `aam_tok_abc123...` |

## Validation and Errors

AAM validates configuration files on load. Common errors:

- **Invalid YAML syntax**: Use a YAML validator to check syntax
- **Unknown fields**: AAM ignores unrecognized keys (logged as warnings)
- **Type mismatches**: e.g., `default_platform: 123` (string expected)
- **Invalid values**: e.g., `on_signature_failure: invalid` (must be warn/error/ignore)

Run `aam config validate` to check your configuration:

```bash
# Validate global config
aam config validate

# Validate project config
aam config validate --project
```

## Next Steps

- [Global Configuration Reference](global.md) - Complete `~/.aam/config.yaml` schema
- [Project Configuration Reference](project.md) - Project-level overrides
- [Manifest Reference](manifest.md) - Package definition (`aam.yaml`)
- [Lock Files](lock-files.md) - Understanding `aam-lock.yaml`
- [Security Configuration](security.md) - Security policies and verification
