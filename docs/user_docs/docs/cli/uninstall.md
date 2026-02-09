# aam uninstall

**Package Management**

## Synopsis

```bash
aam uninstall PACKAGE
```

## Description

Remove an installed package from the project. Undeploys artifacts from the target platform, removes the package directory from `.aam/packages/`, and updates the lock file.

If other installed packages depend on this package, AAM will warn you and ask for confirmation before proceeding.

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| PACKAGE | Yes | Name of the package to uninstall |

## Options

This command has no command-specific options.

## Examples

### Example 1: Uninstall a Package

```bash
aam uninstall my-package
```

**Output:**
```
Uninstalling my-package@1.0.0...

Removing deployed artifacts from cursor...
  ✓ Removed skill: my-skill
  ✓ Removed agent: my-agent

✓ Uninstalled my-package
```

### Example 2: Uninstall Scoped Package

```bash
aam uninstall @author/my-package
```

**Output:**
```
Uninstalling @author/my-package@2.1.0...

Removing deployed artifacts from cursor...
  ✓ Removed skill: example-skill

✓ Uninstalled @author/my-package
```

### Example 3: Package with Dependents (Warning)

```bash
aam uninstall dependency-package
```

**Output:**
```
Warning: 'dependency-package' is required by: my-agent, another-package.
Uninstall anyway? [y/N]: n
Aborted.
```

If you confirm:

```
Warning: 'dependency-package' is required by: my-agent, another-package.
Uninstall anyway? [y/N]: y

Uninstalling dependency-package@1.5.0...

Removing deployed artifacts from cursor...
  ✓ Removed skill: dep-skill

✓ Uninstalled dependency-package
```

### Example 4: Package Not Installed

```bash
aam uninstall non-existent-package
```

**Output:**
```
Error: 'non-existent-package' is not installed.
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - package uninstalled |
| 1 | Error - package not found or uninstall failed |

## Uninstall Flow

When you run `aam uninstall`:

1. Check if the package is installed
2. Check for dependent packages
3. Warn and prompt if dependents exist
4. Load package manifest
5. Undeploy artifacts from platform
6. Remove package directory from `.aam/packages/`
7. Update lock file

## Related Commands

- [`aam install`](install.md) - Install a package
- [`aam list`](list.md) - List installed packages
- [`aam info`](info.md) - Show package details

## Notes

### Dependent Packages

AAM checks the lock file for packages that depend on the package you're uninstalling. If found, it will:

1. Display the dependent package names
2. Prompt for confirmation
3. Proceed only if you confirm

This prevents breaking your environment by removing required dependencies.

### Artifact Cleanup

Uninstall removes deployed artifacts from:

- `.cursor/skills/` - Skills
- `.cursor/rules/` - Agents and instructions
- `.cursor/prompts/` - Prompts
- Other platform-specific directories

### Lock File Update

The lock file is automatically updated to remove the uninstalled package entry.

### Orphaned Dependencies

Uninstalling a package does not automatically remove its dependencies. To remove unused dependencies, you would need to manually uninstall them:

```bash
aam uninstall dependency-name
```

Future versions may include an `aam prune` command to automatically remove orphaned dependencies.
