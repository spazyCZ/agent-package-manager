# CLI Reference

Complete command reference for the AAM (Agent Artifact Manager) command-line interface.

## Quick Reference

### Package Management

| Command | Description |
|---------|-------------|
| [`aam install`](install.md) | Install a package and its dependencies |
| [`aam uninstall`](uninstall.md) | Remove an installed package |
| [`aam list`](list.md) | List installed packages |
| [`aam info`](info.md) | Show detailed package information |
| [`aam search`](search.md) | Search registries for packages |

### Package Authoring

| Command | Description |
|---------|-------------|
| [`aam init`](init.md) | Initialize a new package interactively |
| [`aam create-package`](create-package.md) | Create package from existing project |
| [`aam validate`](validate.md) | Validate package manifest and artifacts |
| [`aam pack`](pack.md) | Build distributable .aam archive |
| [`aam publish`](publish.md) | Publish package to registry |
| [`aam build`](build.md) | Build portable platform-specific bundle |

### Registry Management

| Command | Description |
|---------|-------------|
| [`aam registry init`](registry-init.md) | Create a new local registry |
| [`aam registry add`](registry-add.md) | Add a registry source |
| [`aam registry list`](registry-list.md) | List configured registries |
| [`aam registry remove`](registry-remove.md) | Remove a registry source |

### Configuration

| Command | Description |
|---------|-------------|
| [`aam config set`](config-set.md) | Set a configuration value |
| [`aam config get`](config-get.md) | Get a configuration value |
| [`aam config list`](config-list.md) | List all configuration values |

## Global Options

All commands support these global options:

| Option | Short | Description |
|--------|-------|-------------|
| `--verbose` | `-v` | Enable verbose output with debug logging |
| `--version` | | Show AAM version and exit |
| `--help` | `-h` | Show command help and exit |

See [Global Options](global-options.md) for detailed information about global flags and environment variables.

## Command Conventions

### Package Specifiers

AAM supports multiple package specifier formats:

- `name` - Install latest version from registry
- `name@version` - Install specific version
- `@scope/name` - Scoped package from registry
- `@scope/name@version` - Scoped package with version
- `./path/` - Install from local directory
- `file.aam` - Install from archive file

### Version Constraints

When specifying version constraints in dependencies:

- `1.0.0` - Exact version
- `>=1.0.0` - Minimum version
- `^1.0.0` - Compatible (>=1.0.0 <2.0.0)
- `~1.0.0` - Approximate (>=1.0.0 <1.1.0)
- `*` - Any version

### Exit Codes

All AAM commands follow standard exit code conventions:

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error (validation, network, permissions) |
| 2 | Command usage error (invalid arguments) |

## Getting Help

For any command, use `--help` to see detailed usage:

```bash
aam --help              # Show all commands
aam install --help      # Show install command options
aam registry --help     # Show registry subcommands
```

## Related Documentation

- [Getting Started](../getting-started/installation.md) - Install and configure AAM
- [Concepts](../concepts/packages.md) - Learn about AAM concepts
- [Configuration](../configuration/config-file.md) - Configure AAM behavior
