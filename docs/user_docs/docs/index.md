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

## Where to Go Next

<div class="grid" markdown>

<div class="card" markdown>

### Getting Started

Install AAM, configure your platform, and install your first package in under five minutes.

[Start here](getting-started/index.md){ .md-button }

</div>

<div class="card" markdown>

### Tutorials

Step-by-step guides for common tasks: packaging existing skills, building packages, and deploying to multiple platforms.

[Browse tutorials](tutorials/index.md){ .md-button }

</div>

<div class="card" markdown>

### CLI Reference

Complete reference for every AAM command, flag, and option.

[View commands](cli/index.md){ .md-button }

</div>

</div>
