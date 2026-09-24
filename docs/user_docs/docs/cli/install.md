# aam install

**Package Management**

## Synopsis

```bash
aam install PACKAGE [OPTIONS]
```

## Description

Install a package and its dependencies from a registry, local directory, or archive file. Resolves all dependencies recursively, downloads missing packages, extracts them to `.agent-packages/`, and deploys artifacts to the target platform.

Use this command to add new packages to your project or reinstall existing packages.

## Arguments


| Argument | Required | Description                           |
| -------- | -------- | ------------------------------------- |
| PACKAGE  | Yes      | Package specifier (see formats below) |


### Package Specifier Formats

- `name` - Install latest version from registry (e.g., `my-agent`)
- `name@version` - Install specific version (e.g., `my-agent@1.0.0`)
- `@scope/name` - Scoped package from registry (e.g., `@author/my-agent`)
- `@scope/name@version` - Scoped package with version (e.g., `@author/my-agent@1.2.0`)
- `source-name/artifact` - Install from a specific git source (e.g., `anthropics/skills/skill-creator`)
- `./path/` - Install from local directory
- `file.aam` - Install from archive file

**Installing from a specific source:** Use the qualified name `source-name/artifact` as a single argument. The source name appears in `aam search` (Source column) and `aam list --available` (group header). For sources with a scan path, the format is `owner/repo:path/artifact` (e.g., `openai/skills:.curated/code-review`). There is no `-s` or `--source` option for `aam install` — the source is specified in the package argument.

## Options


| Option                  | Short | Default | Description                                                              |
| ----------------------- | ----- | ------- | ------------------------------------------------------------------------ |
| `--platform`            |       | config  | Deploy to specific platform only                                         |
| `--no-deploy`           |       | false   | Download only, skip deployment                                           |
| `--force`               | `-f`  | false   | Reinstall even if already present                                        |
| `--dry-run`             |       | false   | Preview installation without changes                                     |
| `--global`              | `-g`  | false   | Install to global `~/.aam/` directory                                    |
| `--frozen`              |       | false   | Use exact versions from lock file; fail if lock file is missing or stale |
| `--minimal`             |       | false   | Select lowest satisfying version for stable reproducible builds          |
| `--latest`              |       | false   | Select highest available version for each package                        |
| `--install-system-deps` |       | false   | Auto-install missing pip/npm system dependencies                         |
| `--allow-sudo`          |       | false   | Allow brew/apt installs requiring elevated privileges                    |
| `--skip-checks`         |       | false   | Skip system dependency pre-flight checks (useful in CI)                  |
| `--install-mode`        |       | `copy`  | Installation mode: `copy` (default) or `link` — `link` creates symlinks instead of copying files |
| `--no-cache`            |       | false   | Bypass the local package cache and always download fresh                  |


!!! note "Resolution strategies"
    `--frozen`, `--minimal`, and `--latest` are mutually exclusive. You
    can only use one at a time. Without any strategy flag, the default
    resolver selects the highest compatible version.

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

### Example 5: Install from a Specific Git Source

When multiple sources provide an artifact with the same name, use the qualified name to pick a specific source. The format is `source-name/artifact` (one argument).

```bash
# Install skill-creator from the anthropics/skills source
aam install anthropics/skills/skill-creator

# For sources with a scan path (e.g., openai/skills:.curated)
aam install openai/skills:.curated/code-review
```

**Output:**

```
Searching sources for 'anthropics/skills/skill-creator'...
  Found skill-creator (skill) in source anthropics/skills

✓ Installed skill-creator from source anthropics/skills @ abc1234
```

To discover qualified names: run `aam search <query>` and note the Source column, or `aam list --available` and combine the source name (group header) with the artifact name. Use `aam info source/artifact` to see the exact install command.

### Example 6: Install Without Deployment

```bash
aam install my-agent --no-deploy
```

Downloads and extracts the package but does not deploy artifacts to any platform. Useful for pre-downloading packages or inspecting contents.

### Example 7: Force Reinstall

```bash
aam install my-agent --force
```

Reinstalls the package even if it's already installed. Useful for:

- Recovering from corrupted installations
- Updating deployment after manual changes
- Testing installation process

### Example 8: Preview Installation

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

### Example 9: Install to Specific Platform

```bash
aam install my-agent --platform cursor
```

Deploys artifacts only to Cursor, ignoring other configured platforms.

### Example 10: Global Install

```bash
aam install my-agent -g
```

**Output:**

```
Operating in global mode (~/.aam/)

Resolving my-agent@*...
  + my-agent@1.2.0

✓ Installed 1 packages
```

Installs the package to the global `~/.aam/` directory so it is available user-wide, similar to `npm install -g`. The global lock file is updated instead of the project-local one.

### Example 11: Frozen install (CI reproducibility)

```bash
aam install my-agent --frozen
```

Uses exact versions from `package.agent.lock`. Fails immediately if
the lock file is missing or stale relative to the manifest. Ideal for
CI/CD pipelines.

### Example 12: Minimal version resolution

```bash
aam install my-agent --minimal
```

Selects the lowest version satisfying each constraint, producing
maximally stable and predictable builds.

### Example 13: Auto-install system dependencies

```bash
aam install my-agent --install-system-deps
```

Automatically installs missing pip and npm packages declared in
`systemDependencies`. For brew or apt packages, you must also pass
`--allow-sudo`:

```bash
aam install my-agent --install-system-deps --allow-sudo
```

### Example 14: Skip system checks in CI

```bash
aam install my-agent --skip-checks
```

Skips system dependency pre-flight checks entirely. Useful when
dependencies are pre-provisioned in the CI environment.

### Example 15: Link-mode install (development)

```bash
aam install my-agent --install-mode link
```

Creates symlinks to the source package instead of copying files.
Useful during package development so edits to the source are
reflected immediately without reinstalling.

### Example 16: Force fresh download (bypass cache)

```bash
aam install my-agent --no-cache
```

Ignores any locally cached archives and downloads the package
fresh from the registry. Useful when you suspect cache corruption
or want to verify the latest published content.

## Exit Codes


| Code | Meaning                                                        |
| ---- | -------------------------------------------------------------- |
| 0    | Success - package installed                                    |
| 1    | Error - package not found, validation failed, or network error |


## Installation Flow

When you run `aam install`:

1. Parse the package specifier
2. Check if package is already installed (unless `--force`)
3. Resolve package version from registry or local source
4. Recursively resolve all dependencies (with hoisting)
5. Run system dependency pre-flight checks (unless `--skip-checks`)
6. Prompt for missing environment variables and permissions
7. Download missing packages
8. Extract packages to `.agent-packages/`
9. Deploy artifacts to platform (unless `--no-deploy`)
10. Update lock file (`package.agent.lock`)

## Related Commands

- `[aam uninstall](uninstall.md)` - Remove an installed package
- `[aam list](list.md)` - List installed packages
- `[aam info](info.md)` - Show package details
- `[aam search](search.md)` - Find packages in registries
- `[aam tree](tree.md)` - Display the dependency tree
- `[aam check](check.md)` - Verify dependencies are present
- `[aam why](why.md)` - Explain why a package is installed

## Notes

### Dependency Resolution

AAM uses semantic versioning for dependency resolution:

- `^1.0.0` means `>=1.0.0 <2.0.0` (compatible versions)
- `~1.0.0` means `>=1.0.0 <1.1.0` (approximate versions)
- `>=1.0.0` means any version equal to or greater than 1.0.0

### Lock File

The lock file (`package.agent.lock`) records exact versions installed. This ensures reproducible installations across different environments. Use `--frozen` in CI to enforce exact lock file versions.

### System dependency pre-flight checks

When a package declares `systemDependencies`, AAM verifies all
requirements before installing any files. Missing items are reported
with install instructions. Use `--install-system-deps` to auto-install
pip/npm packages, and add `--allow-sudo` for brew/apt packages. Use
`--skip-checks` to bypass checks entirely in pre-provisioned environments.

### Global Installs

When using `-g` / `--global`, packages are installed to `~/.aam/packages/` instead of the project-local `.agent-packages/`. The global lock file `~/.aam/global.lock` tracks globally installed packages. This is useful for packages you want available across all projects without adding them to each project individually.

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

