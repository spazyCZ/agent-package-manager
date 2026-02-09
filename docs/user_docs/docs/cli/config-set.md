# aam config set

**Configuration**

## Synopsis

```bash
aam config set KEY VALUE
```

## Description

Set a configuration value in the global AAM configuration file. Supports both top-level and nested configuration keys using dot notation.

Changes are saved to `~/.aam/config.yaml` and apply immediately to all subsequent commands.

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| KEY | Yes | Configuration key (dot-notation for nested keys) |
| VALUE | Yes | Value to set |

## Options

This command has no command-specific options.

## Examples

### Example 1: Set Default Platform

```bash
aam config set default_platform cursor
```

**Output:**
```
✓ Set default_platform = cursor
```

### Example 2: Set Author Name

```bash
aam config set author.name "John Doe"
```

**Output:**
```
✓ Set author.name = John Doe
```

### Example 3: Set Author Email

```bash
aam config set author.email "john@example.com"
```

**Output:**
```
✓ Set author.email = john@example.com
```

### Example 4: Enable Security Feature

```bash
aam config set security.require_checksum true
```

**Output:**
```
✓ Set security.require_checksum = true
```

### Example 5: Set Multiple Values

```bash
aam config set default_platform cursor
aam config set author.name "Jane Smith"
aam config set author.email "jane@example.com"
```

**Output:**
```
✓ Set default_platform = cursor
✓ Set author.name = Jane Smith
✓ Set author.email = jane@example.com
```

### Example 6: Invalid Key

```bash
aam config set nonexistent_key value
```

**Output:**
```
Error: Unknown config key: nonexistent_key
```

### Example 7: Nested Key Error

```bash
aam config set author.invalid_field value
```

**Output:**
```
Error: Unknown config key: author.invalid_field
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - value set |
| 1 | Error - invalid key or unsupported depth |

## Configuration Keys

### Top-Level Keys

| Key | Type | Description |
|-----|------|-------------|
| `default_platform` | string | Default deployment platform (cursor, copilot, claude, codex) |

### Author Section

| Key | Type | Description |
|-----|------|-------------|
| `author.name` | string | Default author name for new packages |
| `author.email` | string | Default author email |

### Security Section

| Key | Type | Description |
|-----|------|-------------|
| `security.require_checksum` | boolean | Require checksum verification for installs |
| `security.require_signature` | boolean | Require package signatures (future) |

## Value Types

The command automatically converts values to the appropriate type:

### Boolean Values

```bash
aam config set security.require_checksum true
aam config set security.require_checksum false
aam config set security.require_checksum 1     # Converted to true
aam config set security.require_checksum 0     # Converted to false
aam config set security.require_checksum yes   # Converted to true
```

### String Values

```bash
aam config set default_platform cursor
aam config set author.name "John Doe"
```

Quotes are optional but recommended for values with spaces.

### Integer Values

```bash
aam config set cache.max_size_mb 1024  # Future feature
```

## Related Commands

- [`aam config get`](config-get.md) - Get configuration values
- [`aam config list`](config-list.md) - List all configuration

## Notes

### Configuration File

Changes are saved to `~/.aam/config.yaml`:

```yaml
default_platform: cursor
author:
  name: John Doe
  email: john@example.com
security:
  require_checksum: true
  require_signature: false
```

### Dot Notation

Use dots to access nested keys:

- `author.name` → `config.author.name`
- `security.require_checksum` → `config.security.require_checksum`

### Project vs. Global Config

`aam config set` modifies the **global** configuration in `~/.aam/config.yaml`.

Project-level configuration (`./.aam/config.yaml`) is not currently supported via CLI but can be created manually.

### Quoting Values

Quote values containing spaces or special characters:

```bash
aam config set author.name "John Doe"
aam config set author.name John\ Doe  # Alternative
```

### Boolean Conversion

Boolean values accept multiple formats:

- `true`, `false`
- `1`, `0`
- `yes`, `no`
- Case insensitive

### Verification

After setting, verify the change:

```bash
aam config set default_platform cursor
aam config get default_platform
# Output: default_platform = cursor
```

Or list all config:

```bash
aam config list
```

### Resetting to Defaults

To reset a value, set it back to the default:

```bash
aam config set default_platform cursor  # Default
aam config set security.require_checksum false  # Default
```

Or edit `~/.aam/config.yaml` and remove the line.

### Configuration Precedence

Configuration sources (highest to lowest priority):

1. Command-line flags
2. Environment variables
3. Project config (`./.aam/config.yaml`)
4. Global config (`~/.aam/config.yaml`)
5. Built-in defaults

### Common Settings

**Set default platform:**
```bash
aam config set default_platform cursor
```

**Set author for new packages:**
```bash
aam config set author.name "Your Name"
aam config set author.email "you@example.com"
```

**Enable security features:**
```bash
aam config set security.require_checksum true
```

### Unsupported Keys

Some configuration cannot be set via CLI:

- `registries` - Use `aam registry add/remove` instead
- `active_platforms` - Planned for future versions

### Max Depth

Configuration keys support up to 2 levels:

- ✓ `key` - Valid
- ✓ `section.key` - Valid
- ✗ `section.subsection.key` - Not supported

### Team Configuration

For team setups, document recommended settings:

```bash
# Team configuration script
aam config set default_platform cursor
aam config set author.name "$USER"
aam config set author.email "$USER@company.com"
aam config set security.require_checksum true
```
