# aam install

**Package Management**

## Synopsis

```bash
aam install PACKAGE [OPTIONS]
```

## Description

Install a package and its dependencies from a registry, local directory, or archive file. Resolves all dependencies recursively, downloads missing packages, extracts them to `.aam/packages/`, and deploys artifacts to the target platform.

Use this command to add new packages to your project or reinstall existing packages.

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| PACKAGE | Yes | Package specifier (see formats below) |

### Package Specifier Formats

- `name` - Install latest version from registry (e.g., `my-agent`)
- `name@version` - Install specific version (e.g., `my-agent@1.0.0`)
- `@scope/name` - Scoped package from registry (e.g., `@author/my-agent`)
- `@scope/name@version` - Scoped package with version (e.g., `@author/my-agent@1.2.0`)
- `./path/` - Install from local directory
- `file.aam` - Install from archive file

## Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--platform` | | config | Deploy to specific platform only |
| `--no-deploy` | | false | Download only, skip deployment |
| `--force` | `-f` | false | Reinstall even if already present |
| `--dry-run` | | false | Preview installation without changes |

## Examples

### Example 1: Install Latest Version

```bash
aam install my-agent
```

**Output:**
```
Resolving my-agent@*...
  + my-agent@1.2.0
  + dependency-package@2.0.1

Installed 2 packages
```

### Example 2: Install Specific Version

```bash
aam install @author/my-agent@1.0.0
```

**Output:**
```
Resolving @author/my-agent@1.0.0...
  + @author/my-agent@1.0.0

Installed 1 package
```

### Example 3: Install from Local Directory

```bash
aam install ./my-package/
```

**Output:**
```
Installing my-package@1.0.0 from /path/to/my-package...

✓ Installed my-package@1.0.0
```

### Example 4: Install from Archive

```bash
aam install my-package-1.0.0.aam
```

**Output:**
```
Installing from archive: my-package-1.0.0.aam...

✓ Installed my-package@1.0.0
```

### Example 5: Install Without Deployment

```bash
aam install my-agent --no-deploy
```

Downloads and extracts the package but does not deploy artifacts to any platform. Useful for pre-downloading packages or inspecting contents.

### Example 6: Force Reinstall

```bash
aam install my-agent --force
```

Reinstalls the package even if it's already installed. Useful for:

- Recovering from corrupted installations
- Updating deployment after manual changes
- Testing installation process

### Example 7: Preview Installation

```bash
aam install my-agent --dry-run
```

**Output:**
```
Dry run mode — no changes will be made

Resolving my-agent@*...
  + my-agent@1.2.0
  + dependency-package@2.0.1

[Dry run — no packages installed]
```

### Example 8: Install to Specific Platform

```bash
aam install my-agent --platform cursor
```

Deploys artifacts only to Cursor, ignoring other configured platforms.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - package installed |
| 1 | Error - package not found, validation failed, or network error |

## Installation Flow

When you run `aam install`:

1. Parse the package specifier
2. Check if package is already installed (unless `--force`)
3. Resolve package version from registry or local source
4. Recursively resolve all dependencies
5. Download missing packages
6. Extract packages to `.aam/packages/`
7. Deploy artifacts to platform (unless `--no-deploy`)
8. Update lock file (`.aam/aam-lock.yaml`)

## Related Commands

- [`aam uninstall`](uninstall.md) - Remove an installed package
- [`aam list`](list.md) - List installed packages
- [`aam info`](info.md) - Show package details
- [`aam search`](search.md) - Find packages in registries

## Notes

### Dependency Resolution

AAM uses semantic versioning for dependency resolution:

- `^1.0.0` means `>=1.0.0 <2.0.0` (compatible versions)
- `~1.0.0` means `>=1.0.0 <1.1.0` (approximate versions)
- `>=1.0.0` means any version equal to or greater than 1.0.0

### Lock File

The lock file (`.aam/aam-lock.yaml`) records exact versions installed. This ensures reproducible installations across different environments.

### Registry Configuration

If no registries are configured, you'll see:

```
Error: No registries configured. Run 'aam registry init' to create one, then 'aam registry add' to register it.
```

### Already Installed

If the package is already installed:

```
my-package@1.0.0 is already installed. Use --force to reinstall.
```
