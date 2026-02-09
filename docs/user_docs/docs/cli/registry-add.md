# aam registry add

**Registry Management**

## Synopsis

```bash
aam registry add NAME URL [OPTIONS]
```

## Description

Register a new registry source for package installation and searching. Supports both local file-based registries and HTTP registries. Multiple registries can be configured, with one marked as default for publishing.

Registered registries are stored in the global configuration file.

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| NAME | Yes | Registry identifier (used in commands) |
| URL | Yes | Registry URL (file:// or https://) |

## Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--default` | | false | Set this registry as the default |

## Examples

### Example 1: Add Local Registry

```bash
aam registry add local file:///home/user/my-packages
```

**Output:**
```
✓ Added registry 'local' (file:///home/user/my-packages)
```

### Example 2: Add and Set as Default

```bash
aam registry add local file:///home/user/packages --default
```

**Output:**
```
✓ Added registry 'local' (file:///home/user/packages)
  Set as default: yes
```

### Example 3: Add HTTP Registry

```bash
aam registry add aam-central https://registry.aam.dev
```

**Output:**
```
✓ Added registry 'aam-central' (https://registry.aam.dev)
```

### Example 4: Add Company Internal Registry

```bash
aam registry add company https://packages.company.internal
```

**Output:**
```
✓ Added registry 'company' (https://packages.company.internal)
```

### Example 5: Registry Already Exists

```bash
aam registry add local file:///home/user/packages
```

**Output:**
```
Error: Registry 'local' already configured. Use 'aam registry remove local' first.
```

Solution: Remove the existing entry first or use a different name:

```bash
aam registry remove local
aam registry add local file:///home/user/packages
```

### Example 6: Path Does Not Exist

```bash
aam registry add local file:///nonexistent/path
```

**Output:**
```
Error: Registry path does not exist: /nonexistent/path
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - registry added |
| 1 | Error - duplicate name or invalid path |

## URL Formats

### Local Registry

Use `file://` URLs for local directories:

```bash
# Absolute path
aam registry add local file:///home/user/packages

# Relative paths are converted to absolute
aam registry add local file://./my-registry
```

### HTTP Registry

Use `https://` URLs for remote registries:

```bash
aam registry add central https://registry.aam.dev
aam registry add company https://packages.company.com
```

HTTP registries may require authentication (configured separately).

## Related Commands

- [`aam registry init`](registry-init.md) - Create a new local registry
- [`aam registry list`](registry-list.md) - List all registered registries
- [`aam registry remove`](registry-remove.md) - Remove a registry

## Notes

### Registry Names

Choose meaningful names:

- `local` - Local development registry
- `team` - Team shared registry
- `company` - Company internal registry
- `aam-central` - Public central registry
- `production` - Production packages

Names must be unique.

### Default Registry

The default registry is used for:

- `aam publish` (without `--registry` flag)
- First source for `aam search` and `aam install`

Set a default when adding:

```bash
aam registry add local file:///home/user/packages --default
```

Or change default later (planned feature):

```bash
aam registry set-default local
```

### Multiple Registries

You can configure multiple registries:

```bash
# Local development
aam registry add local file:///home/user/dev-packages

# Team shared
aam registry add team file:///mnt/shared/packages

# Company internal
aam registry add company https://packages.company.com --default
```

`aam search` and `aam install` will query all registries.

### File URL Paths

File URLs must be absolute:

```bash
# Correct
aam registry add local file:///home/user/packages
aam registry add local file:///Users/john/packages

# Incorrect (relative paths are converted to absolute)
aam registry add local file://./packages
# Becomes: file:///current/working/dir/packages
```

### Registry Type Detection

AAM detects the registry type from the URL:

- `file://` → Local registry
- `https://` → HTTP registry
- `http://` → HTTP registry (insecure, not recommended)

### Verification

After adding, verify registration:

```bash
aam registry list
```

**Output:**
```
Configured registries:

┌──────────┬────────────────────────────────┬───────┬─────────┐
│ Name     │ URL                            │ Type  │ Default │
├──────────┼────────────────────────────────┼───────┼─────────┤
│ local    │ file:///home/user/packages     │ local │ ✓       │
│ aam-cent │ https://registry.aam.dev       │ http  │         │
└──────────┴────────────────────────────────┴───────┴─────────┘
```

### Authentication for HTTP Registries

HTTP registries may require authentication:

```bash
# Add registry
aam registry add company https://packages.company.com

# Login (saves token)
aam login company
```

Authentication details are stored separately from registry configuration.

### Shared Team Setup

For a team using a shared network registry:

```bash
# On shared NFS mount
aam registry init /mnt/nfs/team-packages

# Each team member:
aam registry add team file:///mnt/nfs/team-packages --default
```

### Git-Based Registry

For git-based registries:

```bash
# Clone registry repo
git clone git@github.com:team/registry.git ~/team-registry

# Add to AAM
aam registry add team file:///home/user/team-registry

# Pull updates
cd ~/team-registry && git pull
```

### Priority Order

When multiple registries are configured, AAM searches in config file order. The first match is used for installation.

To change priority, edit `~/.aam/config.yaml` and reorder the `registries` list.
