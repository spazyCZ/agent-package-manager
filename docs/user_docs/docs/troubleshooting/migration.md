# Migration Guide

This guide covers migrating between AAM versions, platforms, and from manual artifact management to AAM.

## CLI command changes (pkg subcommand)

If you used older AAM commands, note these changes:

| Old command | New command | Notes |
|-------------|-------------|--------|
| `aam init <name>` (package scaffolding) | `aam pkg init <name>` | Package scaffolding only. |
| `aam init` (no args) | `aam init` | **Unchanged** — client setup (config, sources). |
| `aam create-package` | `aam pkg create` | Create package from existing artifacts. |
| `aam validate` | `aam pkg validate` | Validate package manifest and contents. |
| `aam pack` | `aam pkg pack` | Build package archive. |
| `aam publish` | `aam pkg publish` | Publish to registry. |
| `aam build` | `aam pkg build` | Build package (e.g. platform-specific). |

**Summary:** `aam init` with no arguments is for **client setup** (creating `~/.aam/`, config, sources). Use `aam pkg init <name>` to **scaffold a new package** in the current directory.

## Migrating from Manual Skills to AAM

### Step 1: Detect Existing Artifacts

```bash
cd your-project/
aam pkg create --dry-run
```

This scans for skills, agents, prompts, and instructions not yet managed by AAM.

### Step 2: Create Package

```bash
aam pkg create
```

Interactive selection of artifacts and package metadata.

### Step 3: Validate

```bash
aam pkg validate
```

Ensures the package is well-formed.

### Step 4: Publish

```bash
aam pkg pack
aam pkg publish
```

### Step 5: Update Workflow

Replace manual file copying with:

```bash
aam install @author/my-package
```

See [Package Existing Skills Tutorial](../tutorials/package-existing-skills.md) for details.

## Migrating from Unscoped to Scoped Packages

### Why Migrate?

Scoped packages (`@author/name`) provide:

- Clear ownership
- Namespace isolation
- Better organization

### Migration Steps

#### 1. Update Manifest

```yaml
# Old
name: my-package
version: 1.5.0

# New
name: "@author/my-package"
version: 2.0.0  # Bump major version
```

#### 2. Publish New Version

```bash
aam pkg validate
aam pkg pack
aam pkg publish
```

#### 3. Deprecate Old Package

Add notice to old package README:

```markdown
# Deprecated

This package has moved to `@author/my-package`.

Please update:
\`\`\`bash
aam install @author/my-package
\`\`\`
```

Optionally yank old versions:

```bash
aam yank my-package@1.5.0
```

#### 4. Update Dependents

If other packages depend on the old name, update their `aam.yaml`:

```yaml
dependencies:
  my-package: "^1.0.0"  # Old

  # Change to:
  "@author/my-package": "^2.0.0"  # New
```

## Migrating Between AAM Versions

### 0.x to 1.x (Breaking Changes)

**Changes:**

- Manifest format updated
- New CLI commands
- Platform adapter refactor

**Migration:**

1. **Backup:**
   ```bash
   cp -r .aam .aam.backup
   ```

2. **Upgrade:**
   ```bash
   pip install --upgrade aam
   ```

3. **Update manifests:**
   ```bash
   aam migrate-manifest
   ```

4. **Rebuild packages:**
   ```bash
   aam pkg validate
   aam pkg pack
   ```

5. **Test:**
   ```bash
   aam list
   aam deploy
   ```

### Patch Updates (0.1.x to 0.1.y)

No breaking changes. Just upgrade:

```bash
pip install --upgrade aam
```

## Migrating Between Registries

### Local to HTTP Registry

#### 1. Set Up HTTP Registry

```bash
aam registry add https://registry.yourcompany.com --name company
```

#### 2. Register and Login

```bash
aam register
aam login
```

#### 3. Republish Packages

```bash
# For each package
cd package-directory/
aam pkg publish --registry company
```

#### 4. Update Consumers

```bash
# On consumer machines
aam registry add https://registry.yourcompany.com --name company --default
aam install @author/my-package
```

### Git to HTTP Registry

Same as Local to HTTP above.

### HTTP to Local (Offline Setup)

#### 1. Create Local Registry

```bash
aam registry init ~/local-registry
```

#### 2. Download Packages

```bash
# Download from HTTP registry
aam install @author/package1 --no-deploy
aam install @author/package2 --no-deploy
```

#### 3. Copy to Local Registry

```bash
cp .aam/cache/*.aam ~/local-registry/packages/
```

#### 4. Configure Local Registry

```bash
aam registry add file:///home/user/local-registry --name local --default
```

## Migrating Between Platforms

### Cursor to Claude

#### 1. Install Package

```bash
aam config set active_platforms claude
aam install @author/my-package
```

AAM automatically converts:
- `.cursor/skills/` → `.claude/skills/`
- `.cursor/rules/` → `CLAUDE.md`

#### 2. Verify Deployment

```bash
ls .claude/skills/
cat CLAUDE.md
```

### Any Platform to Multi-Platform

```bash
# Enable all platforms
aam config set active_platforms cursor,claude,copilot,codex

# Redeploy
aam deploy
```

## Migrating Lock Files

### Regenerate Lock File

If `aam-lock.yaml` is out of sync:

```bash
rm .aam/aam-lock.yaml
aam install
```

This regenerates the lock file based on current installations.

### Update Dependencies

```bash
aam update
```

Updates all packages to latest compatible versions and updates lock file.

## Migrating Custom Configurations

### Export Configuration

```bash
# On old machine
aam config list > config-backup.txt
```

### Import Configuration

```bash
# On new machine
# Manually set each value
aam config set <key> <value>
```

Or copy config file:

```bash
cp ~/.aam/config.yaml new-machine:~/.aam/config.yaml
```

## Common Migration Issues

### Manifest Format Changed

**Error:** `Invalid manifest format`

**Solution:**

```bash
aam migrate-manifest
```

Or manually update based on new schema.

### Dependency Conflicts After Migration

**Error:** `Could not resolve dependencies`

**Solution:**

```bash
# Clear lock file
rm .aam/aam-lock.yaml

# Reinstall
aam install
```

### Platform Mismatch

**Error:** Artifacts deployed to wrong location

**Solution:**

```bash
# Check platform configuration
aam config list

# Set correct platform
aam config set default_platform <platform>

# Redeploy
aam deploy --platform <platform>
```

### Lost Packages After Migration

**Solution:**

Check `.aam.backup/` for backup:

```bash
ls .aam.backup/packages/

# Restore if needed
cp -r .aam.backup/packages/* .aam/packages/
```

## Migration Checklist

Before major migrations:

- [ ] Backup `.aam/` directory
- [ ] Backup custom configuration (`~/.aam/config.yaml`)
- [ ] Note current AAM version (`aam --version`)
- [ ] List installed packages (`aam list > packages.txt`)
- [ ] Export configuration (`aam config list > config.txt`)

After migration:

- [ ] Verify AAM version (`aam --version`)
- [ ] Check configuration (`aam config list`)
- [ ] Test package installation (`aam install test-package`)
- [ ] Verify deployment (`aam list`)
- [ ] Test platform functionality (reload IDE, check artifacts)
- [ ] Run diagnostics (`aam doctor`)

## Rollback

If migration fails:

```bash
# Uninstall new version
pip uninstall aam

# Reinstall old version
pip install aam==<old-version>

# Restore backup
rm -rf .aam
mv .aam.backup .aam

# Verify
aam --version
aam list
```

## Getting Help

If migration issues persist:

1. Check [Common Issues](common-issues.md)
2. Run `aam doctor`
3. File an issue on GitHub with:
   - Old AAM version
   - New AAM version
   - Migration steps taken
   - Error messages

## Next Steps

- [Troubleshooting Index](index.md) - More help
- [Common Issues](common-issues.md) - Specific problems
- [FAQ](faq.md) - Frequently asked questions
