# aam registry list

**Registry Management**

## Synopsis

```bash
aam registry list
```

## Description

Display all configured registries. Shows registry names, URLs, types (local or HTTP), and which registry is set as default.

This command reads from the global configuration file.

## Arguments

This command takes no arguments.

## Options

This command has no command-specific options.

## Examples

### Example 1: List Registries

```bash
aam registry list
```

**Output:**
```
Configured registries:

┌──────────────┬─────────────────────────────────────┬───────┬─────────┐
│ Name         │ URL                                 │ Type  │ Default │
├──────────────┼─────────────────────────────────────┼───────┼─────────┤
│ local        │ file:///home/user/my-packages       │ local │ ✓       │
│ team         │ file:///mnt/shared/team-packages    │ local │         │
│ aam-central  │ https://registry.aam.dev            │ http  │         │
└──────────────┴─────────────────────────────────────┴───────┴─────────┘
```

### Example 2: Single Registry

```bash
aam registry list
```

**Output:**
```
Configured registries:

┌──────┬────────────────────────────────┬───────┬─────────┐
│ Name │ URL                            │ Type  │ Default │
├──────┼────────────────────────────────┼───────┼─────────┤
│ local│ file:///home/user/packages     │ local │ ✓       │
└──────┴────────────────────────────────┴───────┴─────────┘
```

### Example 3: No Registries Configured

```bash
aam registry list
```

**Output:**
```
No registries configured. Run 'aam registry init' to create one.
```

### Example 4: Multiple Registries

```bash
aam registry list
```

**Output:**
```
Configured registries:

┌──────────────┬─────────────────────────────────────┬───────┬─────────┐
│ Name         │ URL                                 │ Type  │ Default │
├──────────────┼─────────────────────────────────────┼───────┼─────────┤
│ dev          │ file:///home/user/dev-packages      │ local │         │
│ staging      │ file:///home/user/staging-packages  │ local │         │
│ production   │ https://packages.company.com        │ http  │ ✓       │
│ experimental │ file:///home/user/experiments       │ local │         │
└──────────────┴─────────────────────────────────────┴───────┴─────────┘
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |

## Output Details

### Columns

- **Name** - Registry identifier used in commands
- **URL** - Registry location (file:// or https://)
- **Type** - Registry type:
  - `local` - File-based registry
  - `http` - HTTP API-based registry
- **Default** - Checkmark (✓) indicates the default registry

### Default Registry

The default registry is used when:

- Publishing without `--registry` flag
- Commands don't specify a registry explicitly

Only one registry can be default.

## Related Commands

- [`aam registry add`](registry-add.md) - Add a new registry
- [`aam registry remove`](registry-remove.md) - Remove a registry
- [`aam registry init`](registry-init.md) - Create a local registry

## Notes

### Configuration Location

Registries are stored in `~/.aam/config.yaml`:

```yaml
registries:
  - name: local
    url: file:///home/user/packages
    type: local
    default: true
  - name: aam-central
    url: https://registry.aam.dev
    type: http
    default: false
```

### Registry Order

Registries are listed in configuration file order. This affects:

- Search result ordering
- Package resolution priority

To reorder, edit `config.yaml` manually.

### Testing Registry Access

After listing registries, test access with:

```bash
# Search to verify connectivity
aam search test

# Or install a package
aam install known-package
```

### Identifying Issues

Common issues visible in the list:

**Wrong URL:**
```
file:///wrong/path  → Registry not accessible
```

**No Default:**
```
All registries missing ✓ → Set one as default
```

**Too Many Registries:**
```
10+ registries → Consider removing unused ones
```

### Registry Types

**Local registries:**

- Pros: Simple, offline, no auth needed
- Cons: Not remotely accessible, manual sync needed
- Use for: Development, file-sharing, offline work

**HTTP registries:**

- Pros: Centralized, auth, analytics, web UI
- Cons: Requires server, internet access
- Use for: Teams, production, public packages

### Adding First Registry

If you see "No registries configured":

```bash
# Create and add local registry
aam registry init ~/my-packages --default

# Or add existing HTTP registry
aam registry add aam-central https://registry.aam.dev --default
```

### Checking Default

To identify the default registry:

```bash
aam registry list | grep "✓"
```

Or programmatically:

```bash
aam config get default_registry  # Planned feature
```

### Removing Unused Registries

Clean up unused registries:

```bash
aam registry list
# Identify unused registries

aam registry remove old-registry
aam registry remove unused-registry
```

### Verifying Configuration

Check that the configuration is valid:

```bash
aam doctor
```

This runs diagnostics including registry accessibility checks.

### Verbose Output

For detailed registry information:

```bash
aam registry list --verbose  # Planned feature
```

Would show:

- Last access time
- Package count
- Authentication status
- Health check status

### Environment Override

Registry configuration can be overridden temporarily:

```bash
export AAM_REGISTRY_URL=https://different-registry.com
aam search package  # Uses override URL
```
