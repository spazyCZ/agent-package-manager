# aam config get

**Configuration**

## Synopsis

```bash
aam config get KEY
```

## Description

Get a configuration value from the global AAM configuration. Supports both top-level and nested configuration keys using dot notation.

Reads from `~/.aam/config.yaml` and displays the current value.

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| KEY | Yes | Configuration key (dot-notation for nested keys) |

## Options

This command has no command-specific options.

## Examples

### Example 1: Get Default Platform

```bash
aam config get default_platform
```

**Output:**
```
default_platform = cursor
```

### Example 2: Get Author Name

```bash
aam config get author.name
```

**Output:**
```
author.name = John Doe
```

### Example 3: Get Author Email

```bash
aam config get author.email
```

**Output:**
```
author.email = john@example.com
```

### Example 4: Get Security Setting

```bash
aam config get security.require_checksum
```

**Output:**
```
security.require_checksum = True
```

### Example 5: Invalid Key

```bash
aam config get nonexistent_key
```

**Output:**
```
Error: Unknown config key: nonexistent_key
```

### Example 6: Get Multiple Values

```bash
aam config get default_platform
aam config get author.name
aam config get author.email
```

**Output:**
```
default_platform = cursor
author.name = John Doe
author.email = john@example.com
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - value retrieved |
| 1 | Error - key not found |

## Available Keys

### Top-Level Keys

| Key | Description |
|-----|-------------|
| `default_platform` | Default deployment platform |
| `active_platforms` | List of active platforms |

### Author Section

| Key | Description |
|-----|-------------|
| `author.name` | Default author name |
| `author.email` | Default author email |

### Security Section

| Key | Description |
|-----|-------------|
| `security.require_checksum` | Checksum verification requirement |
| `security.require_signature` | Signature verification requirement |

## Related Commands

- [`aam config set`](config-set.md) - Set configuration values
- [`aam config list`](config-list.md) - List all configuration

## Notes

### Dot Notation

Use dots to access nested configuration:

```bash
aam config get author.name    # Gets config.author.name
aam config get security.require_checksum
```

### Configuration Source

This command reads from:

1. Global config: `~/.aam/config.yaml`
2. Built-in defaults (if key not in global config)

Project-level config (`./.aam/config.yaml`) is merged in the background but not directly accessible via this command.

### Default Values

If a key is not set in the config file, the built-in default is returned:

```bash
# Key not set in config.yaml
aam config get default_platform
# Output: default_platform = cursor  (default)
```

### Boolean Representation

Boolean values are displayed as Python booleans:

```bash
aam config get security.require_checksum
# Output: security.require_checksum = True
```

### Scripting Usage

Use in scripts to read configuration:

```bash
#!/bin/bash
PLATFORM=$(aam config get default_platform | cut -d= -f2 | tr -d ' ')
echo "Current platform: $PLATFORM"
```

### Checking if Key Exists

If a key doesn't exist, the command exits with code 1:

```bash
if aam config get custom_key 2>/dev/null; then
    echo "Key exists"
else
    echo "Key not found"
fi
```

### Registry Configuration

Registry configuration is not accessible via `config get`:

```bash
aam config get registries  # Error
```

Use instead:

```bash
aam registry list
```

### Environment Variable Override

Configuration values can be overridden by environment variables:

```bash
export AAM_DEFAULT_PLATFORM=copilot
aam config get default_platform
# May show 'cursor' from config, but commands use 'copilot' from env
```

To see effective configuration including environment overrides:

```bash
aam config list  # Shows all effective values
```

### Getting All Values

To see all configuration at once:

```bash
aam config list
```

### Unknown Section

If you query a valid section name without a field:

```bash
aam config get author
```

**Output:**
```
Error: Unknown config key: author
```

Specify the field:

```bash
aam config get author.name
```

### Case Sensitivity

Keys are case-sensitive:

```bash
aam config get default_platform   # Correct
aam config get Default_Platform   # Error
```

### Max Depth

Configuration keys support up to 2 levels:

- ✓ `default_platform`
- ✓ `author.name`
- ✗ `section.subsection.key`

### Verification After Set

Verify changes after setting:

```bash
aam config set default_platform copilot
aam config get default_platform
# Output: default_platform = copilot
```

### Programmatic Access

For programmatic access in other languages:

```bash
# JSON output (planned feature)
aam config get default_platform --json
# {"key": "default_platform", "value": "cursor"}
```

Current workaround:

```bash
value=$(aam config get default_platform | cut -d= -f2 | xargs)
```
