# Lock Files Reference (aam-lock.yaml)

The lock file (`.aam/aam-lock.yaml`) records the exact versions of all installed packages and their dependencies, ensuring reproducible installations across different environments.

## Purpose

Lock files solve the "works on my machine" problem by:

- **Freezing exact versions** - Every package version is recorded
- **Recording checksums** - Verify package integrity on every install
- **Capturing dependency tree** - Full resolution graph is preserved
- **Ensuring reproducibility** - Same lock file = identical installation

## File Location

```
my-project/
└── .aam/
    └── aam-lock.yaml  ← Lock file (committed to git)
```

## Version Control

**Always commit lock files to Git.**

```bash
git add .aam/aam-lock.yaml
git commit -m "Update dependencies"
```

This ensures all team members and CI/CD systems use identical package versions.

## When Lock Files Are Generated

Lock files are automatically created or updated by:

| Command | Behavior |
|---------|----------|
| `aam install` | Creates/updates lock file with resolved versions |
| `aam add <package>` | Adds package and updates lock file |
| `aam update` | Resolves latest versions and updates lock file |
| `aam remove <package>` | Removes package and updates lock file |

## Lock File Schema

### Top-Level Fields

| Field | Type | Description |
|-------|------|-------------|
| `lockfile_version` | integer | Lock file format version (currently 1) |
| `resolved_at` | string | ISO 8601 timestamp of last resolution |
| `packages` | dict[string, LockedPackage] | Resolved package versions |

### LockedPackage Schema

| Field | Type | Description |
|-------|------|-------------|
| `version` | string | Exact resolved version |
| `source` | string | Registry name or "local" |
| `checksum` | string | SHA-256 checksum (format: `sha256:<hex>`) |
| `dependencies` | dict[string, string] | Resolved dependency versions |

## Complete Example

```yaml
# .aam/aam-lock.yaml — Lock file (commit to git)

lockfile_version: 1
resolved_at: "2026-02-09T14:32:15.123456Z"

packages:
  "@myorg/asvc-auditor":
    version: "2.1.0"
    source: "aam-central"
    checksum: "sha256:a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456"
    dependencies:
      "@myorg/base-auditor": "3.0.2"
      "@tools/report-generator": "2.1.5"
      "common-prompts": "1.5.3"

  "@myorg/base-auditor":
    version: "3.0.2"
    source: "aam-central"
    checksum: "sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    dependencies:
      "common-prompts": "1.5.3"

  "@tools/report-generator":
    version: "2.1.5"
    source: "company-registry"
    checksum: "sha256:fedcba0987654321fedcba0987654321fedcba0987654321fedcba0987654321"
    dependencies: {}

  "common-prompts":
    version: "1.5.3"
    source: "aam-central"
    checksum: "sha256:567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234"
    dependencies: {}
```

## Field Reference

### Field: `lockfile_version`

**Type:** `integer`
**Current value:** `1`

Lock file format version. Used for backwards compatibility if the format changes in future AAM versions.

```yaml
lockfile_version: 1
```

### Field: `resolved_at`

**Type:** `string` (ISO 8601 timestamp)

When the dependency resolution was last performed.

```yaml
resolved_at: "2026-02-09T14:32:15.123456Z"
```

**Format:** ISO 8601 with timezone (UTC)

**Updated by:**
- `aam install`
- `aam add`
- `aam update`
- `aam remove`

### Field: `packages`

**Type:** `dict[string, LockedPackage]`

Map of package names to their locked versions and metadata.

**Keys:** Full package names (scoped or unscoped)
**Values:** LockedPackage objects

### Field: `packages.<name>.version`

**Type:** `string`

Exact resolved version (always specific, never a constraint).

```yaml
packages:
  my-package:
    version: "2.1.0"  # Exact version, not "^2.0.0"
```

### Field: `packages.<name>.source`

**Type:** `string`

Registry name where the package was downloaded from.

```yaml
packages:
  my-package:
    source: "aam-central"  # Registry name from config
```

**Special values:**
- `"local"` - Package installed from local path
- `"<registry-name>"` - Registry name from `~/.aam/config.yaml`

### Field: `packages.<name>.checksum`

**Type:** `string`

SHA-256 checksum of the package archive.

```yaml
packages:
  my-package:
    checksum: "sha256:a1b2c3d4e5f6..."  # 64 hex characters
```

**Format:** `sha256:<64-character-hex>`

**Verification:** AAM verifies checksums on every `aam install` to detect tampering.

### Field: `packages.<name>.dependencies`

**Type:** `dict[string, string]`

Resolved versions of this package's dependencies.

```yaml
packages:
  parent-package:
    version: "1.0.0"
    dependencies:
      child-package: "2.3.1"  # Exact resolved version
      another-dep: "1.5.0"
```

**Empty if no dependencies:**
```yaml
packages:
  standalone-package:
    version: "1.0.0"
    dependencies: {}
```

## Understanding Resolution

### Example: Constraint Resolution

Given `aam.yaml`:
```yaml
dependencies:
  "@myorg/base-auditor": "^3.0.0"
  "common-prompts": ">=1.0.0"
```

AAM resolves to specific versions and records in lock file:
```yaml
packages:
  "@myorg/base-auditor":
    version: "3.0.2"  # Latest 3.x version
    source: "aam-central"
    checksum: "sha256:..."
    dependencies:
      "common-prompts": "1.5.3"

  "common-prompts":
    version: "1.5.3"  # Latest version satisfying >=1.0.0
    source: "aam-central"
    checksum: "sha256:..."
    dependencies: {}
```

### Example: Transitive Dependencies

Package A depends on B, B depends on C:

```yaml
packages:
  package-a:
    version: "1.0.0"
    dependencies:
      package-b: "2.0.0"

  package-b:
    version: "2.0.0"
    dependencies:
      package-c: "3.0.0"

  package-c:
    version: "3.0.0"
    dependencies: {}
```

All three packages are locked, ensuring the entire dependency tree is reproducible.

## Reproducible Installs

### Install from Lock File

When a lock file exists, `aam install` uses locked versions:

```bash
# Team member clones repo
git clone https://github.com/myteam/project
cd project

# Install uses .aam/aam-lock.yaml
aam install
# Installs exact versions from lock file
```

**Result:** Identical package versions across all team members.

### Install Without Lock File

If no lock file exists, AAM resolves dependencies fresh:

```bash
aam install
# 1. Reads aam.yaml dependencies
# 2. Resolves version constraints
# 3. Downloads packages
# 4. Creates .aam/aam-lock.yaml
```

**Commit the generated lock file:**
```bash
git add .aam/aam-lock.yaml
git commit -m "Add lock file for reproducible installs"
```

## Updating Dependencies

### Update All Packages

```bash
aam update
# Resolves latest versions matching constraints
# Updates lock file
```

**Before:**
```yaml
packages:
  my-package:
    version: "1.0.0"  # Old version
```

**After:**
```yaml
packages:
  my-package:
    version: "1.5.0"  # Updated to latest 1.x
```

### Update Specific Package

```bash
aam update my-package
# Updates only my-package (and its dependencies if needed)
```

### Update to Latest Major Version

Edit `aam.yaml` to change constraint:

```yaml
dependencies:
  my-package: "^2.0.0"  # Changed from ^1.0.0
```

Then update:
```bash
aam install
# Resolves to latest 2.x version
# Updates lock file
```

## Lock File Workflow

### For Individual Developers

1. **Initial setup:**
   ```bash
   cd my-project
   aam init
   aam add @myorg/my-package
   # Creates .aam/aam-lock.yaml
   ```

2. **Commit lock file:**
   ```bash
   git add .aam/aam-lock.yaml
   git commit -m "Add dependencies"
   ```

3. **Install on another machine:**
   ```bash
   git clone ...
   cd my-project
   aam install
   # Uses locked versions
   ```

### For Teams

1. **Project maintainer adds dependency:**
   ```bash
   aam add @myorg/new-package
   git add .aam/aam-lock.yaml
   git commit -m "Add new-package dependency"
   git push
   ```

2. **Team member pulls changes:**
   ```bash
   git pull
   aam install
   # Installs new-package at locked version
   ```

3. **Team member updates dependencies:**
   ```bash
   aam update
   git add .aam/aam-lock.yaml
   git commit -m "Update dependencies"
   git push
   ```

### For CI/CD

```yaml
# .github/workflows/test.yml
steps:
  - uses: actions/checkout@v3

  - name: Install AAM
    run: pip install aam-cli

  - name: Install packages
    run: aam install
    # Uses .aam/aam-lock.yaml for reproducible builds

  - name: Run tests
    run: aam test
```

## Manual Editing

**Do not manually edit lock files.**

The lock file is generated by AAM's dependency resolver. Manual edits can:
- Break dependency resolution
- Introduce invalid checksums
- Cause install failures

### Regenerating Lock File

If the lock file is corrupted or you need to regenerate it:

```bash
# Delete existing lock file
rm .aam/aam-lock.yaml

# Regenerate from aam.yaml
aam install
```

## Troubleshooting

### Lock File Missing After Clone

**Problem:** Cloned repo but no `.aam/aam-lock.yaml`

**Solution:**
```bash
aam install
# Generates new lock file
git add .aam/aam-lock.yaml
git commit -m "Add lock file"
```

### Checksum Mismatch

**Problem:**
```
Error: Checksum mismatch for package my-package@1.0.0
Expected: sha256:abc123...
Got:      sha256:def456...
```

**Cause:** Package was modified or corrupted

**Solution:**
```bash
# Force re-download
aam install --force

# Or regenerate lock file
rm .aam/aam-lock.yaml
aam install
```

### Version Conflict

**Problem:**
```
Error: Cannot resolve dependencies
Package A requires package C ^1.0.0
Package B requires package C ^2.0.0
```

**Solution:** Update one of the conflicting packages or use compatible versions

```bash
# Update packages to find compatible versions
aam update

# Or manually adjust constraints in aam.yaml
```

### Outdated Lock File

**Problem:** Lock file has old versions

**Solution:**
```bash
aam update
# Resolves latest versions
# Updates lock file
```

## Comparison with Other Package Managers

| Feature | AAM | npm | pip |
|---------|-----|-----|-----|
| Lock file | `aam-lock.yaml` | `package-lock.json` | `requirements.txt` + hash |
| Format | YAML | JSON | Text |
| Checksums | Always | Yes | Optional |
| Auto-generated | Yes | Yes | No (manual) |
| Commit to git | Yes | Yes | Yes |

## Best Practices

### Always Commit Lock Files

```bash
# .gitignore should NOT include:
# .aam/aam-lock.yaml  ← DO NOT IGNORE

# Commit lock file
git add .aam/aam-lock.yaml
git commit -m "Update dependencies"
```

### Update Regularly

```bash
# Weekly or monthly
aam update
git add .aam/aam-lock.yaml
git commit -m "Update dependencies to latest versions"
```

### Verify After Clone

```bash
git clone ...
cd project
aam install
aam test  # Verify everything works
```

### Use in CI/CD

Lock files ensure CI builds are reproducible:

```bash
# CI script
aam install  # Uses locked versions
aam test     # Tests against exact versions
```

### Don't Ignore Lock Files

**Bad:**
```gitignore
# .gitignore
.aam/aam-lock.yaml  # ← DON'T DO THIS
```

**Good:**
```gitignore
# .gitignore
.aam/packages/  # Ignore installed packages, but NOT lock file
```

## Advanced Topics

### Multiple Lock Files

AAM supports only one lock file per project (`.aam/aam-lock.yaml`).

For multi-environment setups, use:
- Different branches (e.g., `dev`, `staging`, `prod`)
- Or different projects with their own lock files

### Lock File Diff

Review lock file changes before committing:

```bash
git diff .aam/aam-lock.yaml
```

**Example diff:**
```diff
packages:
  my-package:
-   version: "1.0.0"
+   version: "1.5.0"
-   checksum: "sha256:abc123..."
+   checksum: "sha256:def456..."
```

### Auditing Lock File

Check what's locked:

```bash
aam list
# Shows all locked packages with versions
```

**Example output:**
```
@myorg/asvc-auditor@2.1.0
├── @myorg/base-auditor@3.0.2
│   └── common-prompts@1.5.3
├── @tools/report-generator@2.1.5
└── common-prompts@1.5.3
```

## Migration

### From v0.x Lock Files

AAM v1 lock files are compatible with v0.x (same format).

No migration needed.

### From Other Package Managers

Converting from `package.json`, `requirements.txt`, etc.:

1. Create `aam.yaml` with dependencies
2. Run `aam install`
3. Lock file is generated automatically

## Next Steps

- [Manifest Reference](manifest.md) - Define dependencies in `aam.yaml`
- [CLI Reference: install](../cli/install.md) - Installing packages
- [CLI Reference: update](../cli/update.md) - Updating dependencies
- [Concepts: Dependency Resolution](../concepts/dependencies.md) - How resolution works
