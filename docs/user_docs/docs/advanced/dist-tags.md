# Dist-Tags

## Overview

Distribution tags (dist-tags) are **named aliases for package versions**. They allow you to reference versions by name instead of number, enabling flexible deployment strategies and organizational gates.

**Common use cases:**

- `latest` - Always points to newest version
- `stable` - Points to production-ready version
- `beta` - Points to beta release
- `bank-approved` - Custom gate for enterprise approval
- `staging` - Version deployed to staging environment

## Why Use Dist-Tags?

### Controlled Deployments

```bash
# Users install from "stable" tag, not "latest"
aam install @author/my-agent@stable

# Authors can test new versions before promoting to stable
aam publish  # Creates 2.0.0 tagged as "latest"
# Test 2.0.0 in production
aam dist-tag add @author/my-agent@2.0.0 stable  # Promote when ready
```

### Release Channels

```bash
# Maintain multiple release channels
aam dist-tag add @author/my-agent@1.5.0 stable
aam dist-tag add @author/my-agent@2.0.0-beta.1 beta
aam dist-tag add @author/my-agent@3.0.0-alpha.1 next

# Users choose their channel
aam install @author/my-agent@stable  # Gets 1.5.0
aam install @author/my-agent@beta    # Gets 2.0.0-beta.1
aam install @author/my-agent@next    # Gets 3.0.0-alpha.1
```

### Organizational Gates

```bash
# Require approval before tagging
aam dist-tag add @author/my-agent@1.2.0 bank-approved

# CI/CD only installs approved versions
aam install @author/my-agent@bank-approved
```

## Default Tags

### `latest`

- Automatically set to the newest published version
- Updated on every `aam publish`
- Default tag when no version specified

```bash
aam publish  # Publishes 1.0.0, sets "latest" to 1.0.0
aam publish  # Publishes 1.1.0, updates "latest" to 1.1.0
```

### `stable`

- Opt-in tag for production-ready versions
- Must be set manually
- Not automatically updated

```bash
# Promote to stable after testing
aam dist-tag add @author/my-agent@1.1.0 stable
```

## Managing Dist-Tags

### Add Tag

```bash
# Tag a version
aam dist-tag add @author/my-agent@1.2.0 stable

# Tag with custom name
aam dist-tag add @author/my-agent@1.2.0 bank-approved
```

**Output:**

```
✓ Tagged @author/my-agent@1.2.0 as "stable"
```

### Remove Tag

```bash
# Remove a tag
aam dist-tag rm @author/my-agent stable
```

**Output:**

```
✓ Removed tag "stable" from @author/my-agent
```

### List Tags

```bash
# List all tags for a package
aam dist-tag ls @author/my-agent
```

**Output:**

```
Tags for @author/my-agent:
  latest: 1.3.0
  stable: 1.2.0
  beta: 1.3.0-beta.1
  bank-approved: 1.1.0
```

### Publish with Tag

```bash
# Publish and tag in one step
aam publish --tag beta

# Publishes new version and tags it as "beta"
# Also updates "latest" (automatic)
```

## Installing with Tags

```bash
# Install latest (default)
aam install @author/my-agent
# Equivalent to: aam install @author/my-agent@latest

# Install stable
aam install @author/my-agent@stable

# Install from specific tag
aam install @author/my-agent@beta
aam install @author/my-agent@bank-approved
```

## Tag Rules

### Naming

- Lowercase alphanumeric + hyphens only
- Maximum 32 characters
- Cannot be a valid semver string
- Cannot be reserved words: `all`, `true`, `false`

**Valid:**

```
stable
beta
next
qa-approved
bank-approved
prod-2026-q1
```

**Invalid:**

```
Stable           # Uppercase
beta_1           # Underscore
1.2.0            # Semver (reserved for versions)
latest version   # Spaces
qa approved      # Spaces
```

### Tag Resolution

When you install with a tag:

1. Registry looks up tag in package metadata
2. Tag resolves to a concrete version (e.g., `stable` → `1.2.0`)
3. AAM proceeds with normal version resolution
4. Package is installed

```bash
aam install @author/my-agent@stable

# Behind the scenes:
# 1. Query: What version is tagged "stable"?
# 2. Response: 1.2.0
# 3. Install @author/my-agent@1.2.0
```

## Common Workflows

### Stable Release Workflow

```bash
# 1. Publish new version
aam publish
# Created @author/my-agent@1.2.0 (tagged as "latest")

# 2. Test in staging
aam install @author/my-agent@latest

# 3. Promote to stable after testing
aam dist-tag add @author/my-agent@1.2.0 stable

# 4. Production uses stable tag
aam install @author/my-agent@stable
```

### Beta Testing Workflow

```bash
# 1. Publish beta version
aam publish --tag beta
# Created @author/my-agent@2.0.0-beta.1 (tagged as "latest" and "beta")

# 2. Beta testers use beta tag
aam install @author/my-agent@beta

# 3. Regular users stay on stable
aam install @author/my-agent@stable  # Still 1.5.0

# 4. Promote beta to stable when ready
aam dist-tag add @author/my-agent@2.0.0 stable
```

### Enterprise Approval Workflow

```bash
# 1. Author publishes
aam publish
# Created @author/my-agent@1.3.0

# 2. Compliance team reviews and approves
aam approve @author/my-agent@1.3.0
aam dist-tag add @author/my-agent@1.3.0 bank-approved

# 3. CI/CD only installs approved versions
# In .aam/config.yaml:
# install_policy:
#   tag: bank-approved

aam install @author/my-agent  # Uses bank-approved tag
```

## Registry Support

### Local Registry

Dist-tags stored in `metadata.yaml`:

```yaml
# registry/packages/@author/my-agent/metadata.yaml
name: "@author/my-agent"
tags:
  latest: "1.3.0"
  stable: "1.2.0"
  beta: "1.3.0-beta.1"
  bank-approved: "1.1.0"
```

Update tags with:

```bash
aam dist-tag add @author/my-agent@1.2.0 stable
# Updates metadata.yaml
```

### HTTP Registry

Dist-tags stored in database and managed via API:

```bash
# List tags via API
GET /api/v1/packages/@author/my-agent/tags

# Set tag via API (requires auth)
PUT /api/v1/packages/@author/my-agent/tags/stable
{"version": "1.2.0"}

# Remove tag via API (requires auth)
DELETE /api/v1/packages/@author/my-agent/tags/stable
```

## Configuration

### Default Tag

Change the default tag for installs:

```yaml
# ~/.aam/config.yaml
default_tag: stable  # Use "stable" instead of "latest"
```

Now `aam install @author/my-agent` uses `stable` by default.

### Tag Restrictions

Restrict which tags can be used:

```yaml
# Registry .env
ALLOWED_TAGS=latest,stable,beta,bank-approved
REQUIRE_APPROVAL_FOR_TAGS=bank-approved
```

### Install Policy

Enforce tag-based installs:

```yaml
# ~/.aam/config.yaml or .aam/config.yaml
install_policy:
  require_tag: true           # Must specify a tag
  allowed_tags:               # Only allow these tags
    - stable
    - bank-approved
```

```bash
# This will fail
aam install @author/my-agent@1.2.0
# Error: Direct version install not allowed. Use a tag.

# This succeeds
aam install @author/my-agent@stable
```

## Advanced Use Cases

### Environment-Specific Tags

```bash
# Tag versions for each environment
aam dist-tag add @author/my-agent@1.1.0 prod
aam dist-tag add @author/my-agent@1.2.0 staging
aam dist-tag add @author/my-agent@1.3.0-dev dev

# Each environment installs from its tag
# Production:
aam install @author/my-agent@prod

# Staging:
aam install @author/my-agent@staging

# Development:
aam install @author/my-agent@dev
```

### Rollback with Tags

```bash
# Current stable: 1.3.0
aam install @author/my-agent@stable  # Installs 1.3.0

# Issue found in 1.3.0, rollback
aam dist-tag add @author/my-agent@1.2.0 stable

# Users reinstall and get 1.2.0
aam install @author/my-agent@stable --force
```

### Multi-Track Releases

```bash
# Maintain LTS and current tracks
aam dist-tag add @author/my-agent@1.4.5 lts-v1
aam dist-tag add @author/my-agent@2.3.1 lts-v2
aam dist-tag add @author/my-agent@3.0.2 current

# Users choose their track
aam install @author/my-agent@lts-v1   # Conservative
aam install @author/my-agent@current  # Cutting edge
```

### Quality Gates

```bash
# Automated tests pass → tag as "qa-passed"
# Manual review → tag as "reviewed"
# Security scan → tag as "security-approved"
# All three → tag as "production-ready"

# CI/CD workflow:
aam publish                                          # Publishes 1.5.0
./run-tests.sh && aam dist-tag add ... qa-passed
./manual-review.sh && aam dist-tag add ... reviewed
./security-scan.sh && aam dist-tag add ... security-approved

# If all pass:
aam dist-tag add @author/my-agent@1.5.0 production-ready
```

## Troubleshooting

### Tag Not Found

**Symptom:** `Error: Tag 'stable' not found for @author/my-agent`

**Cause:** Tag doesn't exist or misspelled.

**Solution:**

```bash
# List available tags
aam dist-tag ls @author/my-agent

# Add tag if missing
aam dist-tag add @author/my-agent@1.2.0 stable
```

### Tag Already Exists

**Symptom:** `Error: Tag 'stable' already exists`

**Cause:** Tag already points to a version.

**Solution:**

```bash
# Remove old tag first
aam dist-tag rm @author/my-agent stable

# Add new tag
aam dist-tag add @author/my-agent@1.3.0 stable

# Or use --force to replace
aam dist-tag add @author/my-agent@1.3.0 stable --force
```

### Permission Denied

**Symptom:** `Error: Permission denied` when managing tags.

**Cause:** Only package owners can manage tags (HTTP registry).

**Solution:**

- Ensure you're logged in: `aam login`
- Verify you're a package owner: `aam info @author/my-agent`

### Invalid Tag Name

**Symptom:** `Error: Invalid tag name 'my_tag'`

**Cause:** Tag contains invalid characters.

**Solution:**

Use valid characters (lowercase alphanumeric + hyphens):

```bash
# Invalid
aam dist-tag add @author/my-agent@1.0.0 my_tag

# Valid
aam dist-tag add @author/my-agent@1.0.0 my-tag
```

## Next Steps

- [HTTP Registry](http-registry.md) - Registry with tag management
- [Scoped Packages](scoped-packages.md) - Package namespaces
- [Quality & Evals](quality-evals.md) - Quality gates
- [Configuration Reference](../configuration/index.md) - Tag configuration
