# CLI Reference

Complete command reference for the AAM (Agent Artifact Manager) command-line interface.

## Quick Reference

### Getting Started

| Command | Description |
|---------|-------------|
| [`aam init`](init.md) | Set up AAM (platform, default sources) |

### Package Management

| Command | Description |
|---------|-------------|
| [`aam install`](install.md) | Install a package and its dependencies |
| [`aam uninstall`](uninstall.md) | Remove an installed package |
| [`aam upgrade`](upgrade.md) | Upgrade outdated source-installed packages |
| [`aam outdated`](outdated.md) | Check for outdated packages |
| [`aam search`](search.md) | Search registries and sources (relevance-ranked) |
| [`aam list`](list.md) | List installed packages (`--available` for sources) |
| [`aam info`](info.md) | Show detailed package information |

### Dependency Management

| Command | Description |
|---------|-------------|
| [`aam tree`](tree.md) | Display the resolved dependency tree |
| [`aam why`](why.md) | Show why a package is installed |
| [`aam check`](check.md) | Verify all dependencies are installed and compatible |
| [`aam audit`](audit.md) | Audit installed packages for integrity issues |
| [`aam dedupe`](dedupe.md) | Flatten duplicate package installations |
| [`aam prune`](prune.md) | Remove unlisted package directories |

### Package Integrity

| Command | Description |
|---------|-------------|
| [`aam verify`](verify.md) | Verify installed file checksums |
| [`aam diff`](diff.md) | Show unified diffs for modified files |

### Package Authoring (`aam pkg`)

| Command | Description |
|---------|-------------|
| [`aam pkg init`](pkg-init.md) | Scaffold a new package from scratch |
| [`aam pkg create`](create-package.md) | Create package from existing project |
| [`aam pkg validate`](validate.md) | Validate package manifest and artifacts |
| [`aam pkg pack`](pack.md) | Build distributable .aam archive |
| [`aam pkg publish`](publish.md) | Publish package to registry |
| [`aam pkg build`](build.md) | Build portable platform-specific bundle |

### Source Management

| Command | Description |
|---------|-------------|
| [`aam source add`](source-add.md) | Add a remote git repository as source |
| [`aam source scan`](source-scan.md) | Scan a source for artifacts |
| [`aam source update`](source-update.md) | Fetch upstream changes |
| [`aam source list`](source-list.md) | List configured sources |
| [`aam source remove`](source-remove.md) | Remove a configured source |
| [`aam source candidates`](source-candidates.md) | List unpackaged artifact candidates |
| [`aam source enable-defaults`](source-enable-defaults.md) | Enable all default community skill sources |

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

### Quality & Testing

| Command | Description |
|---------|-------------|
| [`aam test`](test.md) | Run all package tests declared in `quality.tests` |
| [`aam eval`](eval.md) | Run all package evaluations declared in `quality.evals` |

### Authentication

| Command | Description |
|---------|-------------|
| `aam login` | Authenticate with an HTTP registry |
| `aam logout` | Remove stored credentials for a registry |
| `aam whoami` | Show the currently authenticated user |

### Cache Management

| Command | Description |
|---------|-------------|
| `aam cache clean` | Remove all cached package archives |
| `aam cache ls` | List cached package archives |

### Utilities

| Command | Description |
|---------|-------------|
| [`aam doctor`](doctor.md) | Run environment diagnostics |
| [`aam convert`](convert.md) | Convert configs between platforms (Cursor, Copilot, Claude, Codex) |

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

- `name` - Install latest version from registry or source
- `name@version` - Install specific version
- `@scope/name` - Scoped package from registry
- `source/artifact` - Qualified name from a specific source
- `./path/` - Install from local directory
- `file.aam` - Install from archive file

### Exit Codes

All AAM commands follow standard exit code conventions:

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error (validation, network, permissions) |
| 2 | Command usage error (invalid arguments) |

## Getting Help

```bash
aam --help              # Show all commands
aam install --help      # Show install command options
aam pkg --help          # Show package authoring commands
aam source --help       # Show source management commands
```

## Related Documentation

- [Getting Started](../getting-started/installation.md) - Install and configure AAM
- [Concepts](../concepts/packages.md) - Learn about AAM concepts
- [Configuration](../configuration/global.md) - Configure AAM behavior
