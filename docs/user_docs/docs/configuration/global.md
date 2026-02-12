# Global Configuration Reference

The global configuration file (`~/.aam/config.yaml`) defines user-level preferences and defaults that apply to all AAM projects on your system.

## File Location

| Operating System | Default Path |
|-----------------|--------------|
| Linux/macOS | `~/.aam/config.yaml` |
| Windows | `%USERPROFILE%\.aam\config.yaml` |

Override with `AAM_CONFIG` environment variable:

```bash
export AAM_CONFIG=/custom/path/config.yaml
aam install my-package  # Uses custom config
```

## Creating the Global Config

The global config is created automatically when you first run `aam config set`:

```bash
aam config set default_platform cursor
```

Or create it manually:

```bash
mkdir -p ~/.aam
touch ~/.aam/config.yaml
```

## Complete Schema Reference

### Top-Level Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `default_platform` | string | `"cursor"` | Default platform for deployment |
| `active_platforms` | list[string] | `["cursor"]` | Platforms to deploy to with `--all` |
| `registries` | list[RegistrySource] | `[]` | Registry sources for package resolution |
| `security` | SecurityConfig | See below | Security and verification policies |
| `author` | AuthorConfig | `{}` | Default author information |
| `publish` | PublishConfig | `{}` | Publishing defaults |

## Section: `default_platform`

**Type:** `string`
**Default:** `"cursor"`
**Valid values:** `"cursor"`, `"copilot"`, `"claude"`, `"codex"`

The platform used when no `--platform` flag is specified:

```yaml
default_platform: cursor
```

Used by:
- `aam deploy` (if no `--platform` specified)
- `aam pkg build` (if no `--target` specified)

## Section: `active_platforms`

**Type:** `list[string]`
**Default:** `["cursor"]`

List of platforms to deploy to when using `aam deploy --all`:

```yaml
active_platforms:
  - cursor
  - claude
  - copilot
```

**Validation:**
- All platform names must be valid: `cursor`, `copilot`, `claude`, `codex`
- Duplicates are automatically removed
- Empty list is allowed (but `deploy --all` will do nothing)

## Section: `registries`

**Type:** `list[RegistrySource]`
**Default:** `[]`

Defines registry sources where AAM searches for packages. Registries are searched in order.

### RegistrySource Schema

| Field | Type | Default | Required | Description |
|-------|------|---------|----------|-------------|
| `name` | string | - | Yes | Unique registry identifier |
| `url` | string | - | Yes | Registry URL or file path |
| `type` | string | `"local"` | No | Registry type: `local`, `git`, `http` |
| `default` | bool | `false` | No | Mark as default for `aam pkg publish` |

### Example: Multiple Registries

```yaml
registries:
  # HTTP registry (recommended for teams)
  - name: aam-central
    url: https://registry.aam.dev
    type: http
    default: true  # Used by aam pkg publish

  # Git-based registry (no server needed)
  - name: company-registry
    url: https://github.com/myorg/aam-registry
    type: git

  # Local registry (offline/private)
  - name: local
    url: file:///home/user/my-packages
    type: local
```

### Registry Types

#### HTTP Registry (`type: http`)

Connects to an AAM HTTP registry server.

```yaml
- name: aam-central
  url: https://registry.aam.dev
  type: http
```

**Authentication:** Store tokens in `~/.aam/credentials.yaml` (see [Authentication](#authentication))

#### Git Registry (`type: git`)

Uses a Git repository as a registry (no server required).

```yaml
- name: company
  url: https://github.com/myorg/aam-registry
  type: git
```

**Requirements:**
- `git` CLI must be installed
- Repository must follow AAM registry structure
- Authentication via SSH keys or Git credential helpers

#### Local Registry (`type: local`)

Points to a local directory.

```yaml
- name: local
  url: file:///home/user/my-packages
  type: local
```

**Path formats:**
- Linux/macOS: `file:///absolute/path`
- Windows: `file:///C:/Users/user/packages`

### Default Registry

The registry marked `default: true` is used by:
- `aam pkg publish` (if no `--registry` specified)
- `aam search` (searches default registry first)

If no registry is marked default, the first registry in the list is used.

## Section: `security`

**Type:** `SecurityConfig`

Controls package verification and security policies.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `require_checksum` | bool | `true` | Enforce SHA-256 checksum verification (always true) |
| `require_signature` | bool | `false` | Require package signatures |
| `on_signature_failure` | string | `"warn"` | Action when signature fails: `warn`, `error`, `ignore` |
| `trusted_identities` | list[string] | `[]` | Sigstore OIDC identities to trust |
| `trusted_keys` | list[string] | `[]` | GPG key fingerprints to trust |

### Example: Strict Security

```yaml
security:
  require_checksum: true       # Always enforced
  require_signature: true      # Reject unsigned packages
  on_signature_failure: error  # Fail installation on bad signature
  trusted_identities:
    - "*@mycompany.com"       # Trust all emails from mycompany.com
    - "user@example.com"      # Trust specific user
  trusted_keys:
    - "ABCD1234EFGH5678..."   # GPG key fingerprint
```

### Example: Permissive Security

```yaml
security:
  require_checksum: true       # Always enforced
  require_signature: false     # Don't require signatures
  on_signature_failure: warn   # Warn but continue
```

### Field: `require_checksum`

**Type:** `bool`
**Default:** `true`
**Non-configurable:** This field always defaults to `true` and cannot be disabled

All packages must include a SHA-256 checksum, and it is always verified.

### Field: `require_signature`

**Type:** `bool`
**Default:** `false`

When `true`, AAM rejects unsigned packages during installation.

```yaml
security:
  require_signature: true
```

### Field: `on_signature_failure`

**Type:** `string`
**Default:** `"warn"`
**Valid values:** `"warn"`, `"error"`, `"ignore"`

Controls behavior when signature verification fails:

- `warn`: Log warning but continue installation
- `error`: Fail installation immediately
- `ignore`: Skip signature verification entirely

```yaml
security:
  on_signature_failure: error  # Fail on bad signature
```

### Field: `trusted_identities`

**Type:** `list[string]`
**Default:** `[]`

List of Sigstore OIDC identities (email patterns) to trust.

Supports wildcards:
- `*@company.com` - Trust all emails from company.com
- `user@example.com` - Trust specific user

```yaml
security:
  trusted_identities:
    - "*@myorg.com"
    - "external-contractor@example.com"
```

### Field: `trusted_keys`

**Type:** `list[string]`
**Default:** `[]`

List of GPG key fingerprints to trust for signature verification.

```yaml
security:
  trusted_keys:
    - "ABCD1234EFGH5678IJKL9012MNOP3456QRST7890"
```

**Format:** 40-character hexadecimal fingerprint (spaces optional)

## Section: `author`

**Type:** `AuthorConfig`

Default author information used by `aam pkg init` when creating new packages.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | string | `null` | Author name |
| `email` | string | `null` | Author email |

### Example

```yaml
author:
  name: "Jane Smith"
  email: "jane@example.com"
```

When you run `aam pkg init`, these values pre-populate the `author` field in `aam.yaml`:

```yaml
# Generated aam.yaml
name: my-package
version: 1.0.0
author: "Jane Smith <jane@example.com>"
```

**Override per-package:** Edit `aam.yaml` directly to use different author info for specific packages.

## Section: `publish`

**Type:** `PublishConfig`

Controls default behavior for `aam pkg publish`.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `default_scope` | string | `""` | Default scope for package names |

### Field: `default_scope`

**Type:** `string`
**Default:** `""`

When set, `aam pkg init` defaults to scoped package names.

```yaml
publish:
  default_scope: "myorg"
```

With this setting:
- `aam pkg init my-package` creates `@myorg/my-package`
- `aam pkg publish` publishes to the `@myorg` scope by default

**Without scope:**
```yaml
publish:
  default_scope: ""
```

`aam pkg init my-package` creates unscoped package `my-package`.

## Complete Example: Global Config

```yaml
# ~/.aam/config.yaml — User-level AAM configuration

# Default platform for deployment
default_platform: cursor

# Active platforms (deploy to all listed platforms)
active_platforms:
  - cursor
  - claude

# Registry sources (searched in order)
registries:
  - name: aam-central
    url: https://registry.aam.dev
    type: http
    default: true
  - name: company
    url: https://github.com/mycompany/aam-registry
    type: git
  - name: local
    url: file:///home/user/my-aam-packages
    type: local

# Security and verification policy
security:
  require_checksum: true
  require_signature: false
  on_signature_failure: warn
  trusted_identities:
    - "*@mycompany.com"
  trusted_keys:
    - "ABCD1234EFGH5678IJKL9012MNOP3456QRST7890"

# Author defaults (used by aam pkg init)
author:
  name: "Jane Smith"
  email: "jane@example.com"

# Publishing defaults
publish:
  default_scope: "myorg"
```

## Managing Configuration with CLI

### View Current Configuration

```bash
# Show merged configuration (all sources)
aam config show

# Show only global config
aam config show --global
```

### Set Configuration Values

```bash
# Set a simple value
aam config set default_platform copilot

# Set nested values
aam config set author.name "Jane Smith"
aam config set author.email "jane@example.com"

# Add to a list
aam config set active_platforms[0] cursor
aam config set active_platforms[1] claude
```

### Unset Configuration Values

```bash
# Remove a key
aam config unset default_platform

# Remove from a list
aam config unset active_platforms[1]
```

### Edit Configuration Manually

```bash
# Open in default editor
aam config edit

# Open in specific editor
EDITOR=vim aam config edit
```

## Common Configurations

### Configuration: Multi-Platform Developer

Deploy to Cursor and Claude by default:

```yaml
default_platform: cursor
active_platforms:
  - cursor
  - claude
```

### Configuration: Team with Private Registry

Use company registry and enforce signatures:

```yaml
registries:
  - name: company
    url: https://github.com/mycompany/aam-registry
    type: git
    default: true

security:
  require_signature: true
  on_signature_failure: error
  trusted_identities:
    - "*@mycompany.com"
```

### Configuration: Offline/Air-Gapped Environment

Use only local registry:

```yaml
registries:
  - name: local
    url: file:///opt/aam-packages
    type: local
    default: true

security:
  require_signature: false
```

### Configuration: Package Author

Set author defaults and preferred scope:

```yaml
author:
  name: "Jane Smith"
  email: "jane@example.com"

publish:
  default_scope: "jsmith"
```

## Authentication

Store registry tokens in `~/.aam/credentials.yaml` (separate from config):

```yaml
# ~/.aam/credentials.yaml — DO NOT COMMIT
registries:
  aam-central:
    token: "aam_tok_abc123..."
    expires: "2026-12-31T23:59:59Z"
```

**Permissions:** Automatically set to `600` (owner read/write only)

**Generate tokens:**
```bash
aam login aam-central
# Opens browser for OAuth, saves token automatically
```

## Validation

Validate your configuration:

```bash
aam config validate
```

Common errors:
- Invalid platform names
- Malformed URLs
- Unknown registry types
- Invalid security policy values

## Migration from Old Versions

If upgrading from AAM v0.x, run:

```bash
aam config migrate
```

This updates deprecated fields and validates the schema.

## Next Steps

- [Project Configuration](project.md) - Override global settings per-project
- [Security Configuration](security.md) - Advanced security policies
- [CLI Reference: config](../cli/config-list.md) - `aam config` commands
