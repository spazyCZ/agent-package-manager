# aam pack

**Package Authoring**

## Synopsis

```bash
aam pack [PATH]
```

## Description

Build a distributable `.aam` archive from a validated package. Creates a gzipped tar archive containing the package manifest, all artifacts, and supporting files. The archive can be published to a registry or shared manually.

Runs validation automatically before packing. Maximum archive size is 50 MB.

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| PATH | No | Path to package directory (default: current directory) |

## Options

This command has no command-specific options.

## Examples

### Example 1: Pack Current Directory

```bash
aam pack
```

**Output:**
```
Building my-package@1.0.0...
  Adding aam.yaml
  Adding skills/my-skill/
  Adding agents/my-agent/
  Adding prompts/welcome.md

✓ Built my-package-1.0.0.aam (127.3 KB)
  Checksum: sha256:a1b2c3d4e5f6789...
```

### Example 2: Pack Specific Directory

```bash
aam pack ./my-package/
```

Creates archive in the package directory.

### Example 3: Scoped Package

```bash
cd my-scoped-package
aam pack
```

**Output:**
```
Building @author/my-package@2.0.0...
  Adding aam.yaml
  Adding skills/advanced-skill/

✓ Built author-my-package-2.0.0.aam (45.2 KB)
  Checksum: sha256:9f8e7d6c5b4a321...
```

### Example 4: Validation Failure

```bash
aam pack
```

**Output:**
```
Error: Package validation failed. Run 'aam validate' for details.
  ✗ Missing: agents/broken-agent/
```

### Example 5: Large Package

```bash
aam pack
```

**Output:**
```
Building large-package@1.0.0...
  Adding aam.yaml
  Adding skills/skill-1/
  Adding skills/skill-2/
  Adding skills/skill-3/
  Adding assets/large-file.pdf
  Adding assets/documentation/

✓ Built large-package-1.0.0.aam (15.8 MB)
  Checksum: sha256:1a2b3c4d5e6f7g8...
```

### Example 6: Minimal Package

```bash
aam pack
```

**Output:**
```
Building minimal-skill@0.1.0...
  Adding aam.yaml
  Adding skills/simple-skill/

✓ Built minimal-skill-0.1.0.aam (8.5 KB)
  Checksum: sha256:7h8i9j0k1l2m3n4...
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - archive created |
| 1 | Error - validation failed or archive too large |

## Archive Details

### Archive Name Format

**Unscoped packages:**
```
package-name-1.0.0.aam
```

**Scoped packages:**
```
scope-package-name-1.0.0.aam
```

Note: The `@` symbol is removed from scoped package archives.

### Archive Contents

The `.aam` archive contains:

- `aam.yaml` - Package manifest
- All artifact directories and files
- Supporting files referenced by artifacts
- README.md (if present)
- LICENSE (if present)

### Excluded Files

The following are automatically excluded:

- `.git/` directory
- `.aam/` directory (workspace files)
- `node_modules/`
- `__pycache__/`
- `.DS_Store`
- Temporary files (`.tmp`, `.temp`)
- Archive files (`*.aam`)

### Maximum Size

Archives are limited to 50 MB. If your package exceeds this:

```
Error: Archive size exceeds 50 MB limit (actual: 65.3 MB)
```

**Solutions:**

- Remove large binary files
- Move documentation to repository
- Split into multiple packages
- Use external asset hosting

## Related Commands

- [`aam validate`](validate.md) - Validate before packing
- [`aam publish`](publish.md) - Publish the archive to a registry
- [`aam install`](install.md) - Install from an archive file

## Notes

### Automatic Validation

The pack command runs validation automatically. If validation fails, packing is aborted. You can pre-validate with:

```bash
aam validate && aam pack
```

### Checksum

The SHA-256 checksum is calculated for integrity verification. Registries use this to verify uploads, and `aam install` uses it to verify downloads.

### Archive Format

Archives use the `.aam` extension but are standard gzipped tar files (tar.gz). You can inspect them with:

```bash
tar -tzf my-package-1.0.0.aam
```

Extract manually:

```bash
tar -xzf my-package-1.0.0.aam -C ./extracted/
```

### Version in Filename

The archive filename includes the version from `aam.yaml`. Ensure the version is correct before packing:

```yaml
version: 1.0.0
```

### Reproducible Builds

Archives are deterministic - packing the same package multiple times produces identical checksums (excluding timestamps).

### Publishing Workflow

Typical workflow:

```bash
# 1. Validate package
aam validate

# 2. Pack archive
aam pack

# 3. Publish to registry
aam publish

# Or combine:
aam validate && aam pack && aam publish
```

### Local Installation

You can install directly from the packed archive without publishing:

```bash
aam pack
aam install ./my-package-1.0.0.aam
```

Useful for testing before publishing.

### CI/CD Integration

Example GitHub Actions workflow:

```yaml
- name: Pack package
  run: aam pack

- name: Upload artifact
  uses: actions/upload-artifact@v3
  with:
    name: package-archive
    path: '*.aam'
```
