# aam registry remove

**Registry Management**

## Synopsis

```bash
aam registry remove NAME
```

## Description

Remove a configured registry from the global configuration. The registry directory itself is not deleted, only the AAM configuration entry.

After removal, packages from this registry will no longer be available for installation or search.

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| NAME | Yes | Registry name to remove |

## Options

This command has no command-specific options.

## Examples

### Example 1: Remove Registry

```bash
aam registry remove local
```

**Output:**
```
✓ Removed registry 'local'
```

### Example 2: Registry Not Found

```bash
aam registry remove nonexistent
```

**Output:**
```
Error: Registry 'nonexistent' not found. Run 'aam registry list' to see configured registries.
```

### Example 3: Remove and Re-add

```bash
# Remove old configuration
aam registry remove team

# Add with updated URL
aam registry add team file:///mnt/new-location --default
```

### Example 4: Clean Up Multiple Registries

```bash
aam registry remove old-registry
aam registry remove experimental
aam registry remove unused-dev
```

**Output:**
```
✓ Removed registry 'old-registry'
✓ Removed registry 'experimental'
✓ Removed registry 'unused-dev'
```

### Example 5: Remove Default Registry

```bash
aam registry remove local
```

**Output:**
```
✓ Removed registry 'local'
```

If this was the default registry, you'll need to set a new default:

```bash
aam registry add new-default file:///path --default
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - registry removed |
| 1 | Error - registry not found |

## Related Commands

- [`aam registry list`](registry-list.md) - List configured registries
- [`aam registry add`](registry-add.md) - Add a registry
- [`aam registry init`](registry-init.md) - Create a local registry

## Notes

### Registry Data Preserved

Removing a registry from AAM configuration does not delete the registry directory or packages:

```bash
# Remove from config
aam registry remove local

# Registry files still exist
ls ~/my-packages/
# registry.yaml, index.yaml, packages/
```

To re-add:

```bash
aam registry add local file:///home/user/my-packages
```

### Impact on Installed Packages

Removing a registry does not affect already-installed packages:

```bash
# Install package
aam install my-package

# Remove registry
aam registry remove local

# Package still installed and functional
aam list
# my-package@1.0.0 still listed
```

However, you cannot reinstall or update packages from the removed registry.

### Removing Default Registry

If you remove the default registry, AAM will not have a default:

```bash
aam registry remove local  # Was default

aam pkg publish  # Error: no default registry
```

Solution: Set a new default:

```bash
aam registry add new-default file:///path --default
```

### Verification

After removal, verify:

```bash
aam registry list
```

The removed registry should not appear in the list.

### Cannot Undo

There is no built-in undo. To restore a removed registry, re-add it:

```bash
# Removed by mistake
aam registry remove important

# Restore
aam registry add important file:///path/to/registry
```

### Cleaning Up

Remove registries you no longer use:

```bash
# List all registries
aam registry list

# Remove unused ones
aam registry remove old-dev
aam registry remove temporary-test
aam registry remove archived-2023
```

This keeps configuration clean and improves performance for search and install operations.

### Registry Name Case

Registry names are case-sensitive:

```bash
aam registry remove Local   # Error if name is 'local'
aam registry remove local    # Correct
```

### Alternative: Manual Editing

You can also edit `~/.aam/config.yaml` directly:

```yaml
registries:
  - name: local
    url: file:///home/user/packages
    type: local
    default: true
  - name: remove-this  # Delete this entry
    url: file:///tmp/old
    type: local
    default: false
```

After editing, verify:

```bash
aam registry list
```

### Migration Scenario

When migrating registries:

```bash
# Old setup
aam registry list
# old-location (local)

# Create new registry
aam registry init /new/location

# Copy packages
cp -r /old/location/packages/* /new/location/packages/

# Update AAM config
aam registry remove old-location
aam registry add new-location file:///new/location --default
```

### Team Coordination

When removing shared registries, coordinate with team:

1. Announce registry removal
2. Ensure team has alternatives
3. Remove from team documentation
4. Update team configs

### Safety Check

Before removing important registries, check what's installed from them:

```bash
# Check installed packages
aam list

# Check registry contents
ls /path/to/registry/packages/
```
