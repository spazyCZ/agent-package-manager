# Scoped Packages

## Overview

Scoped packages use namespaces to organize packages and clarify ownership. A scoped package name looks like `@scope/package-name`, where the scope is typically an organization, team, or author name.

**Examples:**

- `@author/asvc-auditor` - Author's personal scope
- `@mycompany/code-reviewer` - Company scope
- `@ai-toolkit/prompt-library` - Organization scope

## Why Use Scoped Packages?

### Clear Ownership

```bash
# Unscoped (ambiguous)
code-reviewer  # Who created this?

# Scoped (clear)
@alice/code-reviewer    # Alice's package
@acme-corp/code-reviewer  # Acme Corp's package
```

### Prevent Naming Conflicts

```bash
# Multiple teams can have same names
@team-a/agent
@team-b/agent
@team-c/agent
```

### Organization and discovery

```bash
# Search by scope
aam search "@mycompany/*"
```

### Access Control (HTTP Registry)

```bash
# Control who can publish to your scope
# Only @mycompany members can publish @mycompany/* packages
```

## Scoped vs Unscoped Packages

| Feature | Unscoped | Scoped |
|---------|----------|--------|
| **Name format** | `package-name` | `@scope/package-name` |
| **Ownership** | Ambiguous | Clear (`@scope` owner) |
| **Naming conflicts** | Possible | Rare (scope isolates) |
| **Visibility** | Public | Public or private (HTTP) |
| **Access control** | N/A | Scope-based (HTTP) |

## Creating Scoped Packages

### Initialize with Scope

```bash
# Create scoped package
aam pkg init @alice/my-agent

# Interactive prompts
Package name: @alice/my-agent
Version (1.0.0):
Description: My custom agent
Author: alice
License (MIT):
```

### Convert Existing Package

```yaml
# aam.yaml
name: my-agent  # Unscoped

# Change to:
name: "@alice/my-agent"  # Scoped
```

### Scope Naming Rules

**Valid scopes:**

- Lowercase alphanumeric characters
- Hyphens allowed
- Maximum 63 characters
- Must start with alphanumeric

**Valid:**

```
@alice
@my-company
@ai-toolkit
@org123
```

**Invalid:**

```
@Alice           # Uppercase
@my_company      # Underscore
@-company        # Starts with hyphen
@verylongscopename...  # Too long (>63 chars)
```

**Package name rules** (same as unscoped):

- Lowercase alphanumeric + hyphens
- Maximum 63 characters
- Must start with alphanumeric

## Publishing Scoped Packages

```bash
# Publish scoped package
aam pkg publish

# Package name from aam.yaml: @alice/my-agent
# Published as: @alice/my-agent@1.0.0
```

## Installing Scoped Packages

```bash
# Install scoped package
aam install @alice/my-agent

# Install specific version
aam install @alice/my-agent@1.2.0

# Install with tag
aam install @alice/my-agent@stable
```

## Filesystem Representation

Scoped packages use the **double-hyphen convention** in filesystems:

```
@alice/my-agent  →  alice--my-agent
```

### Local Storage

```
.aam/packages/
└── alice--my-agent/
    └── 1.0.0/
        ├── aam.yaml
        ├── agents/
        └── skills/
```

### Platform Deployment

```
# Cursor
.cursor/skills/alice--my-agent/

# Claude
.claude/skills/alice--my-agent/

# Copilot
.github/skills/alice--my-agent/

# Codex
.codex/skills/alice--my-agent/
```

### Registry Storage

```
registry/packages/
└── alice--my-agent/
    ├── metadata.yaml
    └── versions/
        ├── 1.0.0.aam
        └── 1.1.0.aam
```

## Scope Ownership (HTTP Registry)

### Claiming a Scope

```bash
# Register account
aam register
# Username: alice

# Scope @alice is automatically yours

# Publish to your scope
aam pkg publish
# Package: @alice/my-agent
# ✓ Published (you own @alice scope)
```

### Organization Scopes

```bash
# Create organization (admin panel or API)
# Organization: mycompany

# Add members
# Members can publish to @mycompany/*

# Member publishes
aam pkg publish
# Package: @mycompany/internal-tool
# ✓ Published (member of @mycompany)
```

### Scope Permissions

| Role | Can Publish | Can Manage Tags | Can Add Members |
|------|-------------|----------------|-----------------|
| Owner | Yes | Yes | Yes |
| Member | Yes | Yes | No |
| Contributor | Yes | No | No |

## Searching scoped packages

```bash
# Search all scopes
aam search "agent"

# Search specific scope
aam search "@alice/*"
aam search "@mycompany/*"
```

## Private Scoped Packages (HTTP Registry)

Make packages in your scope private:

```yaml
# aam.yaml
name: "@mycompany/secret-agent"
private: true  # Only accessible to scope members
```

```bash
# Publish private package
aam pkg publish
# ✓ Published @mycompany/secret-agent@1.0.0 (private)

# Install requires authentication
aam login
aam install @mycompany/secret-agent
```

## Migrating to Scoped Packages

### Step 1: Update Manifest

```yaml
# Old (unscoped)
name: my-agent

# New (scoped)
name: "@alice/my-agent"
```

### Step 2: Increment Version

```yaml
# Signal the migration with a new major version
version: 2.0.0
```

### Step 3: Publish

```bash
aam pkg pack
aam pkg publish

# Now available as @alice/my-agent@2.0.0
```

### Step 4: Deprecate Old Package

```bash
# Yank old unscoped versions
aam yank my-agent@1.0.0
aam yank my-agent@1.1.0

# Or add deprecation notice
# Update registry metadata to redirect users
```

### Step 5: Communicate Migration

Add migration notice to README:

```markdown
# Migration Notice

This package has moved to `@alice/my-agent`.

Please update your installs:

\`\`\`bash
# Old
aam install my-agent

# New
aam install @alice/my-agent
\`\`\`
```

## Best Practices

### Scope Naming

**Personal packages:**

```
@alice/my-agent
@bob/code-reviewer
```

Use your username or name.

**Organization packages:**

```
@acme-corp/internal-tool
@ai-toolkit/prompt-library
```

Use organization or project name.

### Package Naming

Keep package names short and descriptive:

```
# Good
@alice/agent
@alice/code-reviewer
@alice/sql-helper

# Verbose
@alice/alices-custom-agent-for-code-review
```

### Scope Consistency

Use the same scope for related packages:

```
@alice/agent-core
@alice/agent-tools
@alice/agent-skills
```

### Private vs Public

**Public:** Default for open-source packages

```yaml
name: "@alice/my-agent"
# Implicitly public
```

**Private:** For sensitive or internal packages

```yaml
name: "@mycompany/internal-tool"
private: true
```

## Troubleshooting

### Scope Already Taken

**Symptom:** `Error: Scope @mycompany already exists`

**Cause:** Someone else owns that scope (HTTP registry).

**Solution:**

Choose a different scope:

```
@mycompany-inc
@mycompany-org
@mycompanyai
```

### Permission Denied

**Symptom:** `Error: Permission denied for scope @mycompany`

**Cause:** You're not a member of that scope.

**Solution:**

- Ask the scope owner to add you as a member
- Use your own scope: `@alice/my-agent`

### Filesystem Name Collision

**Symptom:** `@alice/my-agent` and unscoped `alice-my-agent` conflict.

**Cause:** Both resolve to similar filesystem names.

**Solution:**

This is not a real issue - AAM uses double-hyphen (`alice--my-agent`) to prevent collisions.

### Invalid Scope Name

**Symptom:** `Error: Invalid scope name`

**Cause:** Scope contains invalid characters.

**Solution:**

Fix scope name:

```bash
# Invalid
@Alice/my-agent        # Uppercase
@my_company/agent      # Underscore

# Valid
@alice/my-agent
@my-company/agent
```

## Advanced: Scope Aliasing

Create short aliases for long scopes:

```yaml
# ~/.aam/config.yaml
scope_aliases:
  ac: acme-corp
  ait: ai-toolkit
```

```bash
# Use alias
aam install @ac/my-agent
# Resolves to @acme-corp/my-agent
```

## Next Steps

- [HTTP Registry](http-registry.md) - Scope management and access control
- [Dist-Tags](dist-tags.md) - Version aliasing for scoped packages
- [Package Signing](signing.md) - Sign scoped packages
- [Configuration Reference](../configuration/manifest.md) - Manifest details
