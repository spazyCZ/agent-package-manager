# aam publish (deprecated)

**Package Authoring**

!!! warning "Deprecated"
    `aam publish` is deprecated and will be removed in v0.3.0.
    Use [`aam pkg publish`](publish.md) instead. The command still works but prints a deprecation warning.

## Synopsis

```bash
aam pkg publish [OPTIONS]
```

## Description

Publish a packed `.aam` archive to a configured registry. Must be run from the package directory containing `aam.yaml`. The archive must exist (run `aam pkg pack` first).

For local registries, copies the archive and updates metadata. For HTTP registries, uploads the archive and updates the package index.

## Arguments

This command takes no arguments.

## Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--registry` | | default | Target registry name |
| `--tag` | | latest | Distribution tag for this version |
| `--dry-run` | | false | Preview without publishing |

## Examples

### Example 1: Publish to Default Registry

```bash
aam pkg publish
```

**Output:**
```
Publishing my-package@1.0.0 to local...

  ✓ Archive verified: sha256:a1b2c3d4e5f6...
  ✓ Copied to registry
  ✓ Updated metadata.yaml
  ✓ Rebuilt index.yaml
  ✓ Tagged as 'latest'

✓ Published my-package@1.0.0
```

### Example 2: Publish to Specific Registry

```bash
aam pkg publish --registry company-registry
```

**Output:**
```
Publishing my-package@1.0.0 to company-registry...

  ✓ Archive verified: sha256:a1b2c3d4e5f6...
  ✓ Copied to registry
  ✓ Updated metadata.yaml
  ✓ Rebuilt index.yaml
  ✓ Tagged as 'latest'

✓ Published my-package@1.0.0
```

### Example 3: Publish with Custom Tag

```bash
aam pkg publish --tag beta
```

Publishes and tags the version as `beta`. Users can install with:

```bash
aam install my-package@beta
```

### Example 4: Dry Run

```bash
aam pkg publish --dry-run
```

**Output:**
```
Publishing my-package@1.0.0 to local...

  ✓ Archive verified: sha256:a1b2c3d4e5f6...

[Dry run — package not published]
```

### Example 5: Missing Archive

```bash
aam pkg publish
```

**Output:**
```
Error: No archive found. Run 'aam pkg pack' first.
```

Solution:

```bash
aam pkg pack && aam pkg publish
```

### Example 6: No Registries Configured

```bash
aam pkg publish
```

**Output:**
```
Error: No registries configured. Run 'aam registry init' to create one.
```

### Example 7: Registry Not Found

```bash
aam pkg publish --registry nonexistent
```

**Output:**
```
Error: Registry 'nonexistent' not found. Run 'aam registry list'.
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - package published |
| 1 | Error - archive not found, registry error, or validation failed |

## Publishing Flow

When you run `aam pkg publish`:

1. Load manifest to get package name and version
2. Find `.aam` archive in directory
3. Get target registry from config
4. Verify archive checksum
5. Copy/upload archive to registry
6. Update registry metadata
7. Rebuild registry index
8. Apply distribution tag

## Distribution Tags

Tags are named aliases for versions:

- `latest` - Automatically set to newest version (default)
- `beta` - Pre-release version
- `stable` - Production-ready version
- Custom tags for organizational workflows

Install using tags:

```bash
aam install my-package@latest
aam install my-package@beta
aam install my-package@stable
```

## Related Commands

- [`aam pkg pack`](pack.md) - Create distributable archive
- [`aam pkg validate`](validate.md) - Validate before publishing
- [`aam registry list`](registry-list.md) - List configured registries

## Notes

### Registry Types

**Local registries:**

- Packages are copied to the registry directory
- Metadata updated immediately
- No network required
- Suitable for offline use or file-sharing

**HTTP registries:**

- Packages are uploaded via API
- May require authentication
- Support additional features (analytics, signing)
- Central discovery for teams

### Workflow

Typical publishing workflow:

```bash
# 1. Create or update package
aam pkg validate

# 2. Pack archive
aam pkg pack

# 3. Publish to registry
aam pkg publish

# Or chain commands:
aam pkg validate && aam pkg pack && aam pkg publish
```

### Version Conflicts

If the version already exists in the registry:

**Local registry:**
```
Error: Version 1.0.0 already exists. Increment version or use 'aam yank' first.
```

**HTTP registry:**
```
Error: Version 1.0.0 already published (422 Unprocessable Entity)
```

**Solution:** Increment the version in `aam.yaml`:

```yaml
version: 1.0.1
```

Then re-pack and publish.

### Checksum Verification

The archive checksum is verified before publishing to ensure the file is not corrupted.

### Multiple Registries

If you have multiple registries:

```bash
# Publish to default
aam pkg publish

# Publish to company internal registry
aam pkg publish --registry company-internal

# Publish to public registry
aam pkg publish --registry aam-central
```

### Archive Naming

The command looks for archives matching this pattern:

```
<package-name>-<version>.aam
```

For scoped packages:

```
<scope>-<package-name>-<version>.aam
```

If multiple archives exist, the first match is used.

### Tagging Workflow

Advanced tagging workflow:

```bash
# Publish as beta first
aam pkg publish --tag beta

# After testing, promote to latest
aam dist-tag add my-package@1.0.0 latest

# Mark as stable
aam dist-tag add my-package@1.0.0 stable
```

### CI/CD Publishing

Example for automated publishing:

```yaml
# .github/workflows/publish.yml
- name: Pack and publish
  run: |
    aam pkg pack
    aam pkg publish --registry internal
  env:
    AAM_REGISTRY_URL: ${{ secrets.REGISTRY_URL }}
```
