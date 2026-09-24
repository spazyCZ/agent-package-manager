# aam init

**Getting Started**

## Synopsis

```bash
aam init [NAME] [OPTIONS]
```

## Description

Set up AAM client configuration.

- `aam init` initializes **global** config (`~/.aam/config.yaml`) and can register community sources.
- `aam init --project` initializes **project** config (`.aam/config.yaml`) in the current directory.

If called with a NAME argument (e.g., `aam init my-package`), AAM assumes you mean the old package scaffolding command and delegates to [`aam pkg init`](pkg-init.md) with a deprecation warning.

## Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--yes` | `-y` | false | Non-interactive: use detected defaults |
| `--project` | - | false | Create project-level `.aam/config.yaml` (overrides only) |

## Examples

### Example 1: Interactive Global Setup

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
  Sources:   4 community source(s) added

Next steps:
  aam search <query>   — Find packages to install
  aam install <pkg>     — Install a package
  aam list --available  — Browse source artifacts
  aam pkg init          — Create a new package
```

### Example 2: Interactive Project Setup

```bash
aam init --project
```

**Output:**
```
  Detected platform: cursor
Choose default platform [cursor]:

  Active platforms (comma-separated, default: cursor):
Active platforms [cursor]: cursor, claude-code

  Platform:         cursor
  Active platforms: cursor, claude-code

✓ Project config created.
  Config: /path/to/project/.aam/config.yaml
```

This writes a sparse project override file with:

- `default_platform`
- `active_platforms`

### Example 3: Non-Interactive Project Setup

```bash
aam init --project --yes
```

Uses the auto-detected platform (or `cursor` if none detected), sets `active_platforms` to that same platform, and skips all prompts.

### Example 4: Existing Project Config (Overwrite Prompt)

```bash
aam init --project
```

If `.aam/config.yaml` already exists, you'll be asked to confirm overwrite:

```
Project config already exists. Config: /path/to/project/.aam/config.yaml
Overwrite? [y/N]: y
...
✓ Project config updated.
  Config: /path/to/project/.aam/config.yaml
```

Use `-y` / `--yes` to skip this confirmation.

## Platform Detection

AAM auto-detects your AI platform from project directory indicators:

| Indicator | Detected Platform |
|-----------|-------------------|
| `.cursor/` directory | cursor |
| `.github/copilot/` directory | copilot |
| `CLAUDE.md` file | claude-code |
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

`aam init` (without `--project`) writes to `~/.aam/config.yaml` (global configuration). This sets:

- `default_platform`: Your selected AI platform
- `sources`: Registered community artifact sources

`aam init --project` writes to `.aam/config.yaml` in the current directory and stores only project overrides:

- `default_platform`
- `active_platforms`

All other settings continue to inherit from global config.

### Community Sources

When you accept default sources in global init mode, AAM registers 4 curated community repositories that contain shared skills, agents, and prompts. You can manage sources later with `aam source add` and `aam source remove`. If you skipped default sources during init or removed them later, run `aam source enable-defaults` to restore them.
