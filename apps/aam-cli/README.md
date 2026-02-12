# AAM CLI

Command-line interface for the Agent Artifact Manager — package, share, and install AI agent artifacts (skills, agents, prompts, instructions) across platforms like Cursor, Claude, Copilot, and Codex.

---

## Installation

```bash
cd apps/aam-cli
pip install -e '.[dev]'
```

Verify the install:

```bash
aam --version
aam --help
```

---

## Quick Start — Local Workflow

This is the fastest way to go from an existing project to a published, installable package using only your local filesystem.

```bash
# 1. Create a local registry
aam registry init ~/aam-registry --default

# 2. Package your project's artifacts
cd /path/to/your/project
aam create-package --all --name my-skills --yes

# 3. Validate, pack, and publish
aam validate
aam pack
aam publish

# 4. Install in another project
cd /path/to/other/project
aam install my-skills
```

---

## Step-by-Step Guide

### 1. Set Up a Local Registry

A local registry is a directory on your filesystem where packed `.aam` archives are stored and indexed. You must create one before you can publish or install by name.

```bash
aam registry init ~/aam-registry --default
```

This creates:

```
~/aam-registry/
├── registry.yaml    # registry metadata
├── index.yaml       # searchable package index
└── packages/        # stored .aam archives
```

| Flag | Purpose |
|------|---------|
| `--default` | Register this path and set it as the active default registry |
| `--force` | Reinitialize if the directory already contains a registry |

To see your configured registries at any time:

```bash
aam registry list
```

### 2. Create a Package

There are two ways to create a package.

#### Option A — From an existing project (recommended)

If your project already contains skills, agents, prompts, or instruction files, let `aam` auto-detect them:

```bash
cd /path/to/your/project
aam create-package
```

This scans the project, shows what it found, and lets you interactively select which artifacts to include. It then generates an `aam.yaml` manifest and copies files into the standard AAM layout.

**Common flags:**

| Flag | Purpose |
|------|---------|
| `--all` | Include every detected artifact (skip selection) |
| `--name my-pkg` | Set the package name |
| `--scope myteam` | Add a scope prefix (`@myteam/my-pkg`) |
| `--version 1.0.0` | Set the version |
| `--type skill` | Only detect artifacts of a specific type |
| `--include path/to/file` | Manually add a file not auto-detected |
| `--organize copy` | `copy` (default), `reference`, or `move` files |
| `--dry-run` | Preview what would be created without writing |
| `-y` / `--yes` | Skip confirmation prompts |

**Non-interactive one-liner:**

```bash
aam create-package --all --name my-skills --version 1.0.0 --description "My AI skills" --yes
```

#### Option B — From scratch

Scaffold a brand-new, empty package interactively:

```bash
aam init
```

You will be prompted for name, version, description, author, license, artifact types, and target platforms. The command creates the directory structure and `aam.yaml` manifest.

```bash
# Or pass a name directly
aam init my-new-package
aam init @myteam/my-new-package
```

Result:

```
my-new-package/
├── aam.yaml
├── skills/
├── agents/
├── prompts/
└── instructions/
```

### 3. Validate the Package

Before packing, verify the manifest is correct and all artifact files exist:

```bash
aam validate
```

The command checks:
- `aam.yaml` parses against the Pydantic schema
- All required fields (name, version) are present
- All artifact paths referenced in the manifest exist on disk
- Version is valid semver
- Dependency constraints are well-formed

### 4. Pack into an Archive

Build a distributable `.aam` file (gzipped tar):

```bash
aam pack
```

Output: `my-skills-1.0.0.aam` (or `@myteam-my-skills-1.0.0.aam` for scoped packages) in the package directory, along with a SHA256 checksum.

### 5. Publish to the Registry

Push the archive to your default local registry:

```bash
aam publish
```

**Flags:**

| Flag | Purpose |
|------|---------|
| `--registry <name>` | Publish to a specific registry instead of the default |
| `--tag beta` | Tag this release (default: `latest`) |
| `--dry-run` | Preview without actually publishing |

The publish command copies the `.aam` archive into the registry, creates/updates `metadata.yaml` for the package, and rebuilds the search index.

### 6. Search for Packages

Query the registry for published packages:

```bash
aam search chatbot
aam search "code review" --type skill
aam search audit --limit 5
aam search audit --json
```

### 7. Install a Package

Install into any project from the registry, a local directory, or an archive file:

```bash
# From registry (by name)
aam install my-skills
aam install my-skills@1.0.0
aam install @myteam/my-skills

# From a local directory
aam install ./path/to/package/

# From a .aam archive file
aam install my-skills-1.0.0.aam
```

**Flags:**

| Flag | Purpose |
|------|---------|
| `--platform cursor` | Deploy to a specific platform |
| `--no-deploy` | Download only — skip deploying artifacts |
| `--force` / `-f` | Reinstall even if the package is already present |
| `--dry-run` | Preview resolution and changes without installing |

Installed packages go to `.aam/packages/<name>/` and are recorded in `aam-lock.yaml`.

### 8. List Installed Packages

```bash
aam list           # flat table with version and artifact counts
aam list --tree    # dependency tree view
```

### 9. Show Package Details

```bash
aam info my-skills
aam info @myteam/my-skills
```

Displays name, version, description, author, license, artifacts, dependencies, and source.

### 10. Uninstall a Package

```bash
aam uninstall my-skills
```

This removes the package from `.aam/packages/`, undeploys artifacts from the platform, and updates the lock file. If other packages depend on it, you will be warned before removal.

---

## Managing Multiple Registries

```bash
# Add a second registry
aam registry add team-registry file:///shared/team-packages --default

# List all registries
aam registry list

# Remove a registry
aam registry remove team-registry
```

When you `install` or `search`, all configured registries are queried. Use `--default` on `add` or `init` to control which registry `publish` targets.

---

## Configuration

```bash
aam config get          # Show all configuration
aam config set <k> <v>  # Set a configuration value
```

---

## Project Structure After Installing Packages

```
your-project/
├── .aam/
│   ├── packages/
│   │   └── my-skills/
│   │       ├── aam.yaml
│   │       ├── skills/
│   │       └── ...
│   └── aam-lock.yaml
├── .cursor/
│   ├── rules/          # deployed instruction rules
│   └── skills/         # deployed skills
└── ...
```

---

## Verbose Output

Add `-v` to any command for debug-level logging:

```bash
aam -v install my-skills
aam -v publish --dry-run
```

---

## Command Reference

| Command | Description |
|---------|-------------|
| `aam init [name]` | Scaffold a new package interactively |
| `aam create-package [path]` | Create a package from an existing project |
| `aam validate [path]` | Validate manifest and artifact paths |
| `aam pack [path]` | Build a `.aam` archive |
| `aam publish` | Publish archive to a registry |
| `aam search <query>` | Search registries for packages |
| `aam install <package>` | Install a package |
| `aam list` | List installed packages |
| `aam info <package>` | Show package details |
| `aam uninstall <package>` | Remove a package |
| `aam registry init <path>` | Create a local file-based registry |
| `aam registry add <name> <url>` | Register a registry source |
| `aam registry list` | Show configured registries |
| `aam registry remove <name>` | Remove a registry |
| `aam config get` | Show configuration |
| `aam config set <key> <value>` | Set a configuration value |

---

## Development

```bash
# Install development dependencies
pip install -e '.[dev]'

# Run tests
pytest

# Linting
ruff check src/ tests/
mypy src/

# Format
ruff format src/ tests/
```
