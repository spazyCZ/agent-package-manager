# aam init

**Getting Started**

## Synopsis

```bash
aam init [OPTIONS]
```

## Description

Set up AAM for your project. Guides you through selecting your AI platform and registering community artifact sources. Run this once when you first start using AAM.

If called with a NAME argument (e.g., `aam init my-package`), AAM assumes you mean the old package scaffolding command and delegates to [`aam pkg init`](pkg-init.md) with a deprecation warning.

## Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--yes` | `-y` | false | Non-interactive: use detected defaults |

## Examples

### Example 1: Interactive Setup

```bash
aam init
```

**Output:**
```
  Detected platform: cursor
Choose platform [cursor]:
Register community artifact sources? [Y/n] y

✓ AAM initialized successfully.
  Platform:  cursor
  Config:    ~/.aam/config.yaml
  Sources:   2 community source(s) added

Next steps:
  aam search <query>   — Find packages to install
  aam install <pkg>     — Install a package
  aam list --available  — Browse source artifacts
  aam pkg init          — Create a new package
```

### Example 2: Non-Interactive with Defaults

```bash
aam init --yes
```

Uses the auto-detected platform (or `cursor` if none detected) and registers default sources without prompting.

### Example 3: Reconfigure

```bash
aam init
```

If AAM is already configured, you'll be asked to confirm reconfiguration:

```
AAM is already configured. Config: ~/.aam/config.yaml
Reconfigure? [y/N]: y
Choose platform [cursor]: copilot

✓ AAM reconfigured successfully.
  Platform:  copilot
  Config:    ~/.aam/config.yaml
```

## Platform Detection

AAM auto-detects your AI platform from project directory indicators:

| Indicator | Detected Platform |
|-----------|-------------------|
| `.cursor/` directory | cursor |
| `.github/copilot/` directory | copilot |
| `CLAUDE.md` file | claude |
| `.codex/` directory | codex |

If no platform is detected, `cursor` is used as the default.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - AAM configured |
| 1 | Error - configuration failed |

## Backward Compatibility

!!! warning "Deprecation Notice"
    Running `aam init <name>` (with a NAME argument) is deprecated. This usage delegates to [`aam pkg init <name>`](pkg-init.md) and will be removed in v0.3.0. Use `aam pkg init` for package scaffolding.

## Related Commands

- [`aam pkg init`](pkg-init.md) - Scaffold a new package from scratch
- [`aam pkg create`](create-package.md) - Create package from existing artifacts
- [`aam install`](install.md) - Install a package
- [`aam search`](search.md) - Search for packages
- [`aam source enable-defaults`](source-enable-defaults.md) - Re-enable default sources

## Notes

### Configuration File

`aam init` writes to `~/.aam/config.yaml` (global configuration). This sets:

- `default_platform`: Your selected AI platform
- `sources`: Registered community artifact sources

### Community Sources

When you accept default sources, AAM registers 4 curated community repositories that contain shared skills, agents, and prompts. You can manage sources later with `aam source add` and `aam source remove`. If you skipped default sources during init or removed them later, run `aam source enable-defaults` to restore them.
