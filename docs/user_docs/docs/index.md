---
hide:
  - navigation
  - toc
---

<div class="hero" markdown>

# AAM — Agent Artifact Manager

<p class="hero-subtitle">
The package manager for AI agent artifacts. Install, share, and deploy skills, agents, prompts, and instructions across every AI platform.
</p>

<div class="hero-actions" markdown>

[Get Started](getting-started/index.md){ .md-button .md-button--primary }
[CLI Reference](cli/index.md){ .md-button }
[MCP Interface](mcp/index.md){ .md-button }

</div>

</div>

<div class="install-block">
pip install aam
</div>

---

## Why AAM?

<div class="grid" markdown>

<div class="card" markdown>

### Multi-Platform Deploy

Deploy once to **Cursor**, **Claude**, **GitHub Copilot**, and **Codex**. AAM translates your artifacts into each platform's native format automatically.

</div>

<div class="card" markdown>

### Dependency Resolution

Automatic dependency management with **semver constraints** and **lock files**. If your agent needs a skill, AAM resolves and installs the entire tree.

</div>

<div class="card" markdown>

### Local-First

Works fully **offline** with local registries. No server required. Git directories, bare repos, or plain folders all work as registries out of the box.

</div>

<div class="card" markdown>

### Package and Share

**Create**, **validate**, **sign**, and **publish** packages to any registry. Share with your team via a private registry or with the world via a public one.

</div>

</div>

---

## Quick Example

A typical workflow from zero to a published and installed package:

```bash title="Terminal"
# 1. Set up AAM client (config, sources)
aam init

# 2. Create a new package interactively
aam pkg create my-code-review-skill

# 3. Publish to your registry
aam pkg publish --registry file:///home/user/my-registry

# 4. Install a package in any project
aam install @yourname/my-code-review-skill
```

That is it. The skill is now deployed to your configured platform (Cursor, Claude, Copilot, or Codex) and ready to use.

---

## What Can You Package?

AAM manages four types of AI agent artifacts:

| Artifact Type | What It Is | Example |
|---|---|---|
| **Skills** | Workflow and capability packages containing a SKILL.md with optional scripts, references, and assets. | A code-review skill that walks an agent through a structured review process. |
| **Agents** | Full agent definitions including system prompts, personality configuration, tool settings, and skill references. | A security-audit agent pre-configured with analysis skills and reporting templates. |
| **Prompts** | Reusable prompt templates with optional variable placeholders for dynamic content. | A structured bug-report prompt that ensures consistent issue descriptions. |
| **Instructions** | Platform-specific rules, conventions, and guidelines that shape agent behavior. | Python coding standards that enforce style and architecture decisions. |

---

## Tools & Prerequisites

AAM is designed to be lightweight. Install only what you need based on your planned tasks:

<div class="grid" markdown>

<div class="card" markdown>

### Always Required

| Tool | Version | Purpose |
|------|---------|---------|
| **Python** | 3.11+ | Runtime for AAM |
| **pip** | 22.0+ | Install the `aam` package |

```bash
pip install aam
```

</div>

<div class="card" markdown>

### For Git Source Workflows

| Tool | Version | Purpose |
|------|---------|---------|
| **Git** | 2.25+ | Clone and fetch community skill sources |

Required when using `aam source add`, `aam source update`, or `aam source enable-defaults` to manage git-based package sources.

</div>

<div class="card" markdown>

### For MCP / IDE Integration

| Tool | Version | Purpose |
|------|---------|---------|
| **Cursor**, **Claude Desktop**, **VS Code**, or any MCP client | Latest | Connect to AAM's MCP server |

AAM ships with a built-in MCP server. No extra install needed --- just configure your IDE to spawn `aam mcp serve`.

</div>

<div class="card" markdown>

### For Package Authoring & Publishing

| Tool | Version | Purpose |
|------|---------|---------|
| **Text editor** | Any | Edit `aam.yaml` manifests and artifact files |
| **Git** | 2.25+ | Version control your packages |

Use `aam pkg create` or `aam pkg init` to scaffold packages, then `aam pkg publish` to share them.

</div>

</div>

!!! tip "Check your environment"
    Run `aam doctor` at any time to verify your setup. It checks Python version, configuration files, registry accessibility, and package integrity.

---

## Get Started

<div class="grid" markdown>

<div class="card" markdown>

### :material-download: Install AAM

Install with pip, set your default AI platform, and configure a local registry. Everything you need in five minutes.

[Installation guide](getting-started/installation.md){ .md-button .md-button--primary }

</div>

<div class="card" markdown>

### :material-rocket-launch: Quick Start

Create a registry, build a package, publish it, and install it --- all in a single walkthrough.

[Quick start](getting-started/quickstart.md){ .md-button .md-button--primary }

</div>

<div class="card" markdown>

### :material-package-variant: Your First Package

Build a complete package with skills, agents, prompts, and instructions from scratch.

[First package](getting-started/first-package.md){ .md-button .md-button--primary }

</div>

</div>

---

## CLI Reference

AAM provides a comprehensive CLI organized into command groups. Every command is also available as an MCP tool for IDE agents.

| Command Group | Key Commands | What It Does |
|---------------|-------------|--------------|
| **Getting Started** | [`aam init`](cli/init.md) | Set up AAM (platform, default sources) |
| **Package Management** | [`aam install`](cli/install.md), [`aam search`](cli/search.md), [`aam list`](cli/list.md) | Install, search, list, upgrade, and remove packages |
| **Package Integrity** | [`aam verify`](cli/verify.md), [`aam diff`](cli/diff.md) | Verify checksums and show diffs for modified files |
| **Package Authoring** | [`aam pkg create`](cli/create-package.md), [`aam pkg publish`](cli/publish.md) | Create, validate, pack, and publish packages |
| **Source Management** | [`aam source add`](cli/source-add.md), [`aam source scan`](cli/source-scan.md) | Manage git-based package sources |
| **Registry Management** | [`aam registry init`](cli/registry-init.md), [`aam registry add`](cli/registry-add.md) | Create and configure local or remote registries |
| **Configuration** | [`aam config set`](cli/config-set.md), [`aam config list`](cli/config-list.md) | Get and set configuration values |
| **Diagnostics** | [`aam doctor`](cli/doctor.md) | Run health checks on your AAM setup |

[Full CLI reference](cli/index.md){ .md-button }

---

## MCP Interface

AAM ships with a built-in **MCP (Model Context Protocol) server** that lets AI agents in your IDE manage packages directly --- no terminal required.

<div class="grid" markdown>

<div class="card" markdown>

### Read-Only Tools (17)

Search packages, list sources, check configuration, verify integrity, and run diagnostics. Always safe, always available.

</div>

<div class="card" markdown>

### Write Tools (12)

Install, uninstall, upgrade, and publish packages. Create packages and manage sources. Requires explicit `--allow-write` opt-in.

</div>

<div class="card" markdown>

### Resources (9)

Passive data endpoints: installed packages, configuration, registries, source lists, and manifest data. Available to any connected agent.

</div>

<div class="card" markdown>

### IDE Integration

Works with **Cursor**, **Claude Desktop**, **VS Code**, **Windsurf**, and any MCP-compatible client. One line of config to connect.

</div>

</div>

```bash
# Start MCP server (read-only, safe for exploration)
aam mcp serve

# Start with full read/write access
aam mcp serve --allow-write
```

[MCP Interface documentation](mcp/index.md){ .md-button }

---

## Where to Go Next

<div class="grid" markdown>

<div class="card" markdown>

### Tutorials

Step-by-step guides for common tasks: packaging existing skills, building packages, and deploying to multiple platforms.

[Browse tutorials](tutorials/index.md){ .md-button }

</div>

<div class="card" markdown>

### Platform Guides

Deploy artifacts to Cursor, Claude Desktop, GitHub Copilot, and OpenAI Codex with platform-specific configuration.

[Platform guides](platforms/index.md){ .md-button }

</div>

<div class="card" markdown>

### Concepts

Understand packages, artifacts, git sources, registries, dependency resolution, and platform adapters.

[Learn concepts](concepts/index.md){ .md-button }

</div>

</div>
