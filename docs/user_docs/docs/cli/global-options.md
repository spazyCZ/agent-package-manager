# Global Options

Global options and environment variables that apply to all AAM commands.

## Global Flags

### --verbose / -v

Enable verbose output with debug-level logging.

```bash
aam install my-package --verbose
aam validate -v
```

When enabled:

- Shows DEBUG-level log messages
- Displays detailed operation steps
- Includes timestamps and module names in logs
- Useful for troubleshooting and understanding command behavior

**Default:** Disabled (WARNING-level logging)

### --version

Display the AAM version and exit.

```bash
aam --version
```

**Output:**
```
aam version 0.1.0
```

### --help / -h

Show command help and exit. Can be used with any command or subcommand.

```bash
aam --help                # Show all commands
aam install --help        # Show install options
aam registry --help       # Show registry subcommands
aam registry add --help   # Show registry add options
```

## Environment Variables

AAM respects the following environment variables:

### AAM_HOME

Override the default AAM home directory.

**Default:** `~/.aam` (Linux/macOS) or `%USERPROFILE%\.aam` (Windows)

**Usage:**
```bash
export AAM_HOME=/custom/path/to/aam
aam install my-package
```

This directory contains:

- `config.yaml` - Global configuration file
- `cache/` - Downloaded package cache
- `logs/` - Command logs (if enabled)

### AAM_CONFIG_PATH

Override the global configuration file path.

**Default:** `$AAM_HOME/config.yaml`

**Usage:**
```bash
export AAM_CONFIG_PATH=/path/to/custom-config.yaml
aam config list
```

Useful for:

- Using different configuration profiles
- Testing configuration changes
- CI/CD environments with custom config

### AAM_REGISTRY_URL

Set a default registry URL without modifying config.

**Usage:**
```bash
export AAM_REGISTRY_URL=https://registry.example.com
aam search chatbot
```

This takes precedence over registries in `config.yaml`.

### AAM_NO_COLOR

Disable colored output (for CI/CD or log files).

**Usage:**
```bash
export AAM_NO_COLOR=1
aam install my-package
```

### AAM_LOG_LEVEL

Set the logging level without using `--verbose`.

**Valid values:** `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

**Usage:**
```bash
export AAM_LOG_LEVEL=DEBUG
aam validate
```

### AAM_CACHE_DIR

Override the package cache directory.

**Default:** `$AAM_HOME/cache`

**Usage:**
```bash
export AAM_CACHE_DIR=/tmp/aam-cache
aam install my-package
```

## Configuration Precedence

AAM loads configuration in the following order (later sources override earlier):

1. Built-in defaults
2. Global config file (`$AAM_HOME/config.yaml`)
3. Project config file (`./.aam/config.yaml`)
4. Environment variables
5. Command-line flags

## Examples

### Verbose Installation with Custom Cache

```bash
export AAM_CACHE_DIR=/mnt/fast-ssd/aam-cache
aam install my-package --verbose
```

### CI/CD Configuration

```bash
export AAM_NO_COLOR=1
export AAM_HOME=/tmp/aam
export AAM_REGISTRY_URL=https://internal-registry.company.com
aam install required-packages
```

### Debugging Registry Issues

```bash
export AAM_LOG_LEVEL=DEBUG
aam search my-query --verbose
```

## Related Commands

- [`aam config set`](config-set.md) - Set configuration values
- [`aam config get`](config-get.md) - Get configuration values
- [`aam config list`](config-list.md) - List all configuration

## Related Documentation

- [Configuration File](../configuration/config-file.md) - Configuration file format
- [Environment Setup](../getting-started/installation.md) - Initial setup
