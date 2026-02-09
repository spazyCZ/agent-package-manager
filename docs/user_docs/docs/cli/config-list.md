# aam config list

**Configuration**

## Synopsis

```bash
aam config list
```

## Description

List all AAM configuration values. Displays the global configuration from `~/.aam/config.yaml`, including defaults for unset values. Shows key-value pairs in a formatted table with source information.

Use this to review your complete AAM configuration.

## Arguments

This command takes no arguments.

## Options

This command has no command-specific options.

## Examples

### Example 1: List All Configuration

```bash
aam config list
```

**Output:**
```
AAM Configuration:

┌──────────────────────────────┬─────────────────────┬─────────┐
│ Key                          │ Value               │ Source  │
├──────────────────────────────┼─────────────────────┼─────────┤
│ default_platform             │ cursor              │ config  │
│ active_platforms             │ cursor              │ config  │
│ registries.0.name            │ local               │ config  │
│ registries.0.url             │ file:///home/user/… │ config  │
│ registries.0.default         │ True                │ config  │
│ security.require_checksum    │ False               │ default │
│ security.require_signature   │ False               │ default │
│ author.name                  │ John Doe            │ config  │
│ author.email                 │ john@example.com    │ config  │
└──────────────────────────────┴─────────────────────┴─────────┘
```

### Example 2: Minimal Configuration

```bash
aam config list
```

**Output (newly initialized):**
```
AAM Configuration:

┌──────────────────────────────┬─────────┬─────────┐
│ Key                          │ Value   │ Source  │
├──────────────────────────────┼─────────┼─────────┤
│ default_platform             │ cursor  │ default │
│ active_platforms             │ cursor  │ default │
│ security.require_checksum    │ False   │ default │
│ security.require_signature   │ False   │ default │
└──────────────────────────────┴─────────┴─────────┘
```

### Example 3: Full Configuration

```bash
aam config list
```

**Output (fully configured):**
```
AAM Configuration:

┌──────────────────────────────┬─────────────────────────────┬─────────┐
│ Key                          │ Value                       │ Source  │
├──────────────────────────────┼─────────────────────────────┼─────────┤
│ default_platform             │ cursor                      │ config  │
│ active_platforms             │ cursor, copilot             │ config  │
│ registries.0.name            │ local                       │ config  │
│ registries.0.url             │ file:///home/user/packages  │ config  │
│ registries.0.default         │ True                        │ config  │
│ registries.1.name            │ aam-central                 │ config  │
│ registries.1.url             │ https://registry.aam.dev    │ config  │
│ registries.1.default         │ False                       │ config  │
│ security.require_checksum    │ True                        │ config  │
│ security.require_signature   │ False                       │ default │
│ author.name                  │ John Doe                    │ config  │
│ author.email                 │ john@example.com            │ config  │
└──────────────────────────────┴─────────────────────────────┴─────────┘
```

### Example 4: No Custom Configuration

```bash
aam config list
```

If `~/.aam/config.yaml` doesn't exist or is empty, only defaults are shown:

**Output:**
```
AAM Configuration:

┌──────────────────────────────┬─────────┬─────────┐
│ Key                          │ Value   │ Source  │
├──────────────────────────────┼─────────┼─────────┤
│ default_platform             │ cursor  │ default │
│ active_platforms             │ cursor  │ default │
│ security.require_checksum    │ False   │ default │
│ security.require_signature   │ False   │ default │
└──────────────────────────────┴─────────┴─────────┘
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |

## Output Details

### Columns

- **Key** - Configuration key in dot notation
- **Value** - Current value
- **Source** - Where the value comes from:
  - `config` - Set in `~/.aam/config.yaml`
  - `default` - Built-in default value

### Registry Entries

Registries are shown as indexed entries:

```
registries.0.name    → First registry name
registries.0.url     → First registry URL
registries.1.name    → Second registry name
registries.1.url     → Second registry URL
```

### List Values

List values (like `active_platforms`) are displayed comma-separated:

```
active_platforms     cursor, copilot, claude
```

## Related Commands

- [`aam config set`](config-set.md) - Set configuration values
- [`aam config get`](config-get.md) - Get a specific value
- [`aam registry list`](registry-list.md) - List registries (more detail)

## Notes

### Configuration File Location

Global configuration: `~/.aam/config.yaml`

Example file:

```yaml
default_platform: cursor
active_platforms:
  - cursor
  - copilot

registries:
  - name: local
    url: file:///home/user/packages
    type: local
    default: true

security:
  require_checksum: true
  require_signature: false

author:
  name: John Doe
  email: john@example.com
```

### Source Column

The source column helps identify:

- **config** - You've explicitly set this value
- **default** - Using AAM's built-in default

This helps identify which values you can change vs. which are defaults.

### Modifying Values

To change values shown with `source: config`:

```bash
aam config set key value
```

To change values shown with `source: default`, set them:

```bash
aam config set security.require_checksum true
# Source changes from 'default' to 'config'
```

### Registry Management

For more detailed registry information, use:

```bash
aam registry list
```

This shows registries in a more readable format.

### Environment Variable Override

This command shows configuration from the file, not runtime values with environment variable overrides.

For effective runtime values:

```bash
export AAM_DEFAULT_PLATFORM=copilot
aam config list
# Still shows 'cursor' from config

# But commands use 'copilot' from environment
```

### Filtering Output

To filter configuration:

```bash
# Show only author config
aam config list | grep author

# Show only security config
aam config list | grep security
```

### Exporting Configuration

Save configuration for backup or sharing:

```bash
aam config list > my-aam-config.txt
```

Or directly copy the config file:

```bash
cp ~/.aam/config.yaml ~/aam-config-backup.yaml
```

### Comparing Configurations

Compare configurations across systems:

```bash
# On system 1
aam config list > system1-config.txt

# On system 2
aam config list > system2-config.txt

# Compare
diff system1-config.txt system2-config.txt
```

### Team Configuration Template

Generate a template for team members:

```bash
aam config list
# Share this output as a reference
# Team members can use 'aam config set' to match
```

### Verbose Mode

For additional context:

```bash
aam config list --verbose  # Planned feature
```

Would show:

- Configuration file path
- Last modified time
- Validation status
- Environment variable overrides

### Resetting Configuration

To reset to defaults, remove custom config:

```bash
rm ~/.aam/config.yaml
aam config list
# Shows all defaults
```

Or selectively reset keys by editing `~/.aam/config.yaml`.

### Programmatic Access

For scripts, use `aam config get` for specific values:

```bash
PLATFORM=$(aam config get default_platform | cut -d= -f2 | xargs)
```

Or parse the YAML file directly:

```bash
python -c "import yaml; print(yaml.safe_load(open('~/.aam/config.yaml'))['default_platform'])"
```
