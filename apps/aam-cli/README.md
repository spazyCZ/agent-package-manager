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
# 1. Initialize AAM for this machine/project
aam init --yes

# 2. Create a local registry
aam registry init ~/aam-registry --default

# 3. Package your project's artifacts
cd /path/to/your/project
aam pkg create --all --name my-skills --yes

# 4. Validate, pack, and publish
aam pkg validate
aam pkg pack
aam pkg publish

# 5. Install in another project
cd /path/to/other/project
aam install my-skills
```

---

## Step-by-Step Guide

### 1. Initialize AAM client (recommended)

Run this once to configure your default platform and sources:

```bash
aam init
```

Use `aam init --project` to create a project-local `.aam/config.yaml`.

### 2. Set Up a Local Registry

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

### 3. Create a Package

There are two ways to create a package.

#### Option A — From an existing project (recommended)

If your project already contains skills, agents, prompts, or instruction files, let `aam` auto-detect them:

```bash
cd /path/to/your/project
aam pkg create
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
aam pkg create --all --name my-skills --version 1.0.0 --description "My AI skills" --yes
```

#### Option B — From scratch

Scaffold a brand-new, empty package interactively:

```bash
aam pkg init
```

You will be prompted for name, version, description, author, license, artifact types, and target platforms. The command creates the directory structure and `aam.yaml` manifest.

```bash
# Or pass a name directly
aam pkg init my-new-package
aam pkg init @myteam/my-new-package
```

Result:

```
my-new-package/
├── package.agent.json
├── skills/
├── agents/
├── instructions/
├── commands/
└── rules/
```

### 4. Validate the Package

Before packing, verify the manifest is correct and all artifact files exist.
AAM validates either `package.agent.json` or `aam.yaml`:

```bash
aam pkg validate
```

The command checks:
- The manifest parses against the Pydantic schema
- All required fields (name, version) are present
- All artifact paths referenced in the manifest exist on disk
- Version is valid semver
- Dependency constraints are well-formed

### 5. Pack into an Archive

Build a distributable `.aam` file (gzipped tar):

```bash
aam pkg pack
```

Output: `my-skills-1.0.0.aam` (or `@myteam-my-skills-1.0.0.aam` for scoped packages) in the package directory, along with a SHA256 checksum.

### 6. Publish to the Registry

Push the archive to your default local registry:

```bash
aam pkg publish
```

**Flags:**

| Flag | Purpose |
|------|---------|
| `--registry <name>` | Publish to a specific registry instead of the default |
| `--tag beta` | Tag this release (default: `latest`) |
| `--dry-run` | Preview without actually publishing |

The publish command copies the `.aam` archive into the registry, creates/updates `metadata.yaml` for the package, and rebuilds the search index.

### 7. Search for Packages

Query the registry for published packages:

```bash
aam search chatbot
aam search "code review" --type skill
aam search audit --limit 5
aam search audit --json
```

### 8. Install a Package

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

Installed packages go to `.agent-packages/<name>/` and are recorded in
`package.agent.lock`.

### 9. List Installed Packages

```bash
aam list           # flat table with version and artifact counts
aam list --tree    # dependency tree view
```

### 10. Show package details

```bash
aam info my-skills
aam info @myteam/my-skills
```

Displays name, version, description, author, license, artifacts, dependencies, and source.

### 11. Uninstall a Package

```bash
aam uninstall my-skills
```

This removes the package from `.agent-packages/`, undeploys artifacts from the
platform, and updates the lock file. If other packages depend on it, you are
warned before removal.

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
aam config list         # Show all configuration
aam config get <key>    # Get one value
aam config set <k> <v>  # Set a configuration value
```

For list-type keys such as `active_platforms`, a single value is saved as a
one-item YAML list:

```bash
aam config set active_platforms claude
```

---

## Project Structure After Installing Packages

```
your-project/
├── .agent-packages/
│   └── my-skills/
│       ├── aam.yaml
│       ├── skills/
│       └── ...
├── package.agent.lock
├── .aam/
│   └── config.yaml
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
| `aam init` | Initialize client configuration and sources |
| `aam install <package>` | Install a package |
| `aam uninstall <package>` | Remove a package |
| `aam upgrade [package]` | Upgrade outdated packages |
| `aam outdated` | Check for available upgrades |
| `aam search <query>` | Search registries and sources |
| `aam list` | List installed packages |
| `aam info <package>` | Show package details |
| `aam tree` | Show resolved dependency tree |
| `aam why <package>` | Explain why a package is installed |
| `aam check` | Verify lock/install consistency |
| `aam audit` | Audit installed package integrity |
| `aam dedupe` | Detect or clean duplicate installs |
| `aam prune` | Remove untracked package directories |
| `aam pkg init` | Scaffold a new package |
| `aam pkg create` | Create a package from existing artifacts |
| `aam pkg validate` | Validate package manifest and artifacts |
| `aam pkg pack` | Build a `.aam` archive |
| `aam pkg publish` | Publish archive to a registry |
| `aam source add/list/scan/update/remove` | Manage git artifact sources |
| `aam source candidates` | Show unpackaged source artifacts |
| `aam source enable-defaults` | Re-enable default community sources |
| `aam registry init/add/list/remove` | Manage registries |
| `aam config list/get/set` | Manage configuration |
| `aam cache ls/clean` | Manage package download cache |
| `aam mcp serve` | Run the MCP server |

Legacy aliases such as `aam create-package`, `aam validate`, `aam pack`, and
`aam publish` still work with deprecation warnings, but `aam pkg ...` is the
supported path.

---

## MCP Server

AAM includes a built-in [Model Context Protocol](https://modelcontextprotocol.io) server that exposes AAM capabilities as tools for IDE agents. This lets AI assistants in Cursor, Claude Desktop, Windsurf, and VS Code search for packages, manage sources, install skills, and get recommendations directly.

### Starting the Server

```bash
# Read-only mode (default — safe for any IDE)
aam mcp serve

# Enable write operations (install, publish, source add/remove, etc.)
aam mcp serve --allow-write

# HTTP/SSE transport instead of stdio
aam mcp serve --transport http --port 8000

# With logging
aam mcp serve --log-file /tmp/aam-mcp.log --log-level DEBUG
```

### Options

| Flag | Description |
|------|-------------|
| `--transport` | `stdio` (default) or `http` |
| `--port PORT` | HTTP port (default: `8000`, only for `--transport http`) |
| `--allow-write` | Enable write tools — install, uninstall, publish, source management, config changes. **Without this flag, only read-only tools are available.** |
| `--log-file PATH` | Log to file instead of stderr |
| `--log-level` | `DEBUG`, `INFO` (default), `WARNING`, `ERROR` |

### Safety Model

By default the server starts in **read-only mode** with only safe,
non-destructive tools. When `--allow-write` is passed, additional mutating
tools are enabled, including install/uninstall, source management, config
changes, and publish operations.

### Available Tools

**Read-only tools (always available) include:**

| Tool | Description |
|------|-------------|
| `aam_search` | Search registries and sources for packages |
| `aam_list` | List installed packages |
| `aam_info` | Get detailed package metadata |
| `aam_validate` | Validate package manifest and artifacts |
| `aam_config_get` | Get configuration values |
| `aam_registry_list` | List configured registries |
| `aam_doctor` | Run environment diagnostics |
| `aam_source_list` | List configured git sources |
| `aam_source_scan` | Scan a source for artifacts |
| `aam_source_candidates` | List unpackaged artifact candidates |
| `aam_source_diff` | Preview upstream changes |
| `aam_verify` | Verify package file integrity |
| `aam_diff` | Show file differences in packages |
| `aam_outdated` | Check for outdated source-installed packages |
| `aam_available` | List all available artifacts from sources |
| `aam_init_info` | Get client initialization information |
| `aam_tree` | Show resolved dependency tree |
| `aam_why` | Explain why a package is installed |
| `aam_check` | Check dependency and install consistency |
| `aam_audit` | Audit package integrity findings |
| `aam_dedupe` | Detect duplicate installations |
| `aam_prune` | Report or remove untracked package directories |
| `aam_cache_ls` | List cached package archives |
| `aam_recommend_skills` | Recommend skills based on repo analysis |

**Write tools (requires `--allow-write`) include:**

| Tool | Description |
|------|-------------|
| `aam_install` | Install packages from registries or sources |
| `aam_uninstall` | Uninstall packages |
| `aam_publish` | Publish packages to registry |
| `aam_create_package` | Create a package manifest |
| `aam_config_set` | Set configuration values |
| `aam_registry_add` | Add a new registry |
| `aam_source_add` | Add a git source |
| `aam_source_remove` | Remove a git source |
| `aam_source_update` | Update git sources |
| `aam_upgrade` | Upgrade outdated packages |
| `aam_init` | Initialize client for a platform |
| `aam_init_package` | Scaffold a new package |
| `aam_test` | Run deterministic package tests |
| `aam_eval` | Run evaluation suites |
| `aam_cache_clean` | Clean cached package archives |
| `aam_convert` | Convert artifacts between platforms |

### MCP Resources

The server also exposes 9 read-only resources for passive data access:

| URI | Description |
|-----|-------------|
| `aam://config` | Current merged configuration |
| `aam://packages/installed` | List of installed packages |
| `aam://packages/{name}` | Details for a specific package |
| `aam://registries` | Configured registries |
| `aam://manifest` | Read `aam.yaml` from current directory |
| `aam://sources` | List of git sources |
| `aam://sources/{source_id}` | Source details with artifacts |
| `aam://sources/{source_id}/candidates` | Candidate artifacts from a source |
| `aam://init_status` | Client initialization status |

### IDE Configuration

**Cursor / Claude Desktop / Windsurf** (stdio):

```json
{
  "mcpServers": {
    "aam": {
      "command": "aam",
      "args": ["mcp", "serve"]
    }
  }
}
```

**With write access enabled:**

```json
{
  "mcpServers": {
    "aam": {
      "command": "aam",
      "args": ["mcp", "serve", "--allow-write"]
    }
  }
}
```

**HTTP transport:**

```json
{
  "mcpServers": {
    "aam": {
      "url": "http://localhost:8000"
    }
  }
}
```

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
