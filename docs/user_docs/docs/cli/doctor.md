# aam doctor

**Utilities**

## Synopsis

```bash
aam doctor
```

## Description

Run comprehensive environment diagnostics to identify configuration,
registry, and package integrity issues. Use this command to verify that
your AAM installation is healthy and to troubleshoot common problems.

The doctor command performs the following checks:

1. **Python version** -- verifies Python 3.11 or later is installed.
2. **Config file paths** -- reports the absolute path of each config
   file (global and project), whether it exists, and whether its YAML
   syntax and schema are valid.
3. **Configuration validity** -- loads the merged configuration
   (global + project + defaults) and verifies it parses successfully.
4. **Registry accessibility** -- checks that each configured registry
   path exists (local registries) or is reachable (HTTP registries).
5. **Package integrity** -- verifies that every locked package has a
   valid directory and a parseable manifest.
6. **Incomplete installations** -- detects leftover staging directories
   from interrupted installs.

## Options

This command has no options.

## Examples

### Example 1: Healthy environment

```bash
aam doctor
```

**Output:**
```
AAM Environment Diagnostics

  ✓ Python 3.12.3
  ✓ Global config: /home/user/.aam/config.yaml (valid)
  ✓ Project config: /home/user/my-project/.aam/config.yaml (not found, using defaults)
  ✓ Configuration loaded (1 registry configured)
  ✓ Registry 'local' accessible at /home/user/.aam/registry
  ✓ Package 'code-review@1.0.0' — manifest valid, 3 artifacts
  ✓ No incomplete installations detected

✓ 7/7 checks passed
```

### Example 2: Config file with errors

If a config file contains invalid YAML or unknown fields, `aam doctor`
reports the problem and suggests how to fix it:

```bash
aam doctor
```

**Output:**
```
AAM Environment Diagnostics

  ✓ Python 3.12.3
  ✗ Global config: /home/user/.aam/config.yaml (invalid YAML: ...)
  ✓ Project config: /home/user/my-project/.aam/config.yaml (valid)
  ✗ Failed to load configuration: ...
  ✓ No incomplete installations detected

✗ 3/5 checks passed, 2 failures
```

### Example 3: Missing package directory

```bash
aam doctor
```

**Output:**
```
AAM Environment Diagnostics

  ✓ Python 3.12.3
  ✓ Global config: /home/user/.aam/config.yaml (valid)
  ✓ Project config: /home/user/my-project/.aam/config.yaml (not found, using defaults)
  ✓ Configuration loaded (0 registries configured)
  ⚠ Package 'my-agent' directory not found: ...
  ✓ No incomplete installations detected

✓ 5/6 checks passed, 1 warnings
```

## Checks reference

| Check | Status | Meaning |
|-------|--------|---------|
| Python version | pass | Python 3.11+ installed |
| Python version | fail | Upgrade to Python 3.11 or later |
| Global config | pass | File exists with valid YAML and schema, or file not found (defaults used) |
| Global config | fail | File exists but has invalid YAML or schema errors |
| Project config | pass | File exists with valid YAML and schema, or file not found (defaults used) |
| Project config | fail | File exists but has invalid YAML or schema errors |
| Configuration | pass | Merged configuration loaded successfully |
| Configuration | fail | Merged configuration could not be parsed |
| Registry | pass | Registry path exists or HTTP URL configured |
| Registry | warn | Registry path not found on disk |
| Package | pass | Package directory and manifest are valid |
| Package | warn | Package directory missing or manifest unreadable |
| Incomplete install | pass | No leftover staging directories |
| Incomplete install | warn | Staging directories found from interrupted install |

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | All checks passed (warnings are allowed) |
| 1 | One or more checks failed |

## Config file resolution

AAM uses a 4-level configuration precedence (highest to lowest):

1. CLI flags
2. Project config (`<project>/.aam/config.yaml`)
3. Global config (`~/.aam/config.yaml`)
4. Built-in defaults

The doctor command reports the absolute path and status of both the
global and project config files so you can quickly identify which files
are active.

## See also

- [aam config list](config-list.md) -- List all configuration values
- [aam config set](config-set.md) -- Change a configuration value
- [aam verify](verify.md) -- Verify package file integrity
