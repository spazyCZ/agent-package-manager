# Tutorial: Sharing with Your Team

**Difficulty:** Beginner
**Time:** 15 minutes

## What You'll Learn

In this tutorial, you'll learn different ways to share AAM packages with your team without needing a centralized server. We'll cover:

- Setting up a local file-based registry
- Sharing via shared network drives (NFS, SMB)
- Git-based registries for version control
- Registry resolution order and priority

## Prerequisites

- AAM installed on all team members' machines
- At least one packaged `.aam` file to share
- (Optional) Access to a shared filesystem or Git repository

## The Scenario

You've created a useful package (`@myteam/python-toolkit`) and want to share it with your team. You want teammates to be able to run:

```bash
aam install @myteam/python-toolkit
```

and have it "just work" without manually passing around `.aam` files.

Let's explore three approaches.

---

## Approach 1: Shared Filesystem Registry

**Best for:** Teams with a shared network drive, NFS mount, or cloud-synced folder (Dropbox, Google Drive, OneDrive)

**Advantages:**
- No server setup required
- Works offline (if locally mounted)
- Simple permissions model (filesystem ACLs)
- Instant publishing (just copy files)

### Step 1: Initialize the Registry

One team member creates the shared registry:

```bash
# Create registry on shared drive
aam registry init /mnt/shared/aam-registry

# Or on cloud-synced folder
aam registry init ~/Dropbox/team-aam-registry
```

This creates:

```
/mnt/shared/aam-registry/
├── registry.yaml          # Registry metadata
├── index.yaml             # Search index (empty initially)
└── packages/              # Package storage
```

### Step 2: Configure Team Members

Each team member adds the shared registry:

```bash
# Add the shared registry (adjust path as needed)
aam registry add team file:///mnt/shared/aam-registry

# Make it the default registry
aam registry add team file:///mnt/shared/aam-registry --default

# Verify it's configured
aam registry list
```

Expected output:

```
Configured registries:
  team (file:///mnt/shared/aam-registry) [default]
  aam-central (https://github.com/aam-packages/registry)
```

!!! info "Registry Resolution Order"
    AAM searches registries in the order listed. With `team` set as default, it will be searched first.

### Step 3: Publish to the Shared Registry

The package author publishes:

```bash
cd my-package/

# Build the package
aam pkg pack

# Publish to the shared registry
aam pkg publish --registry team
```

Expected output:

```
Publishing @myteam/python-toolkit@1.0.0 to team...

✓ Validated package
✓ Copied to /mnt/shared/aam-registry/packages/@myteam/python-toolkit/versions/1.0.0.aam
✓ Updated metadata
✓ Rebuilt search index

Published @myteam/python-toolkit@1.0.0
```

### Step 4: Teammates Install

Any team member can now install:

```bash
aam install @myteam/python-toolkit
```

AAM will:

1. Search the `team` registry first (since it's default)
2. Find `@myteam/python-toolkit@1.0.0`
3. Install from `/mnt/shared/aam-registry/packages/...`

### Step 5: Publishing Updates

When you publish a new version:

```bash
# Bump version in aam.yaml
# version: 1.1.0

aam pkg pack
aam pkg publish --registry team
```

The registry structure becomes:

```
/mnt/shared/aam-registry/
└── packages/
    └── @myteam/
        └── python-toolkit/
            ├── metadata.yaml       # Lists all versions
            └── versions/
                ├── 1.0.0.aam
                └── 1.1.0.aam       # New version
```

Teammates can update:

```bash
aam update @myteam/python-toolkit
```

### Permissions Best Practices

For shared filesystem registries:

**Option A: Everyone can publish (small teams)**

```bash
# Make packages/ writable by everyone
chmod -R 775 /mnt/shared/aam-registry/packages/
```

**Option B: Dedicated publishers (larger teams)**

```bash
# Only the 'publishers' group can write
chgrp -R publishers /mnt/shared/aam-registry/packages/
chmod -R 775 /mnt/shared/aam-registry/packages/
```

Non-publishers can still read and install.

---

## Approach 2: Git-Based Registry

**Best for:** Teams already using Git, want version control of packages, distributed teams

**Advantages:**
- Full version history of packages
- Works with existing Git workflows (PRs, code review)
- Can be public or private
- No special infrastructure needed

### Step 1: Create Git Registry Repository

One team member creates a Git repository:

```bash
# Create registry directory
mkdir aam-registry
cd aam-registry

# Initialize as AAM registry
aam registry init .

# Initialize git
git init
git add .
git commit -m "Initialize AAM registry"

# Push to remote (GitHub, GitLab, etc.)
git remote add origin git@github.com:myteam/aam-registry.git
git push -u origin main
```

### Step 2: Team Members Clone and Configure

Each team member:

```bash
# Clone the registry
git clone git@github.com:myteam/aam-registry.git ~/aam-registry

# Add as AAM registry
aam registry add team file:///$HOME/aam-registry --default

# Or use the Git URL directly (AAM will clone it)
aam registry add team git@github.com:myteam/aam-registry.git --default
```

### Step 3: Publish to Git Registry

The package author:

```bash
cd my-package/

# Pack the package
aam pkg pack

# Publish to the git registry
aam pkg publish --registry team

# The registry is now updated locally
cd ~/aam-registry

# Commit and push
git add .
git commit -m "Publish @myteam/python-toolkit@1.0.0"
git push origin main
```

### Step 4: Teammates Pull Updates

When a new package is published, teammates sync:

```bash
cd ~/aam-registry
git pull

# Or let AAM handle it automatically
aam registry update team
```

Then install:

```bash
aam install @myteam/python-toolkit
```

### Workflow with Pull Requests

For more controlled publishing:

**Author workflow:**

```bash
# Publish to a branch
git checkout -b publish/python-toolkit-1.0.0
aam pkg publish --registry team
git add .
git commit -m "Publish @myteam/python-toolkit@1.0.0"
git push origin publish/python-toolkit-1.0.0

# Open PR on GitHub/GitLab
```

**Reviewer workflow:**

- Review the package contents in the PR
- Approve and merge to main

**Team workflow:**

```bash
# Update local registry
aam registry update team

# Install the approved package
aam install @myteam/python-toolkit
```

---

## Approach 3: Multiple Registries with Priority

**Best for:** Using both internal and external packages

You can configure multiple registries with different priorities:

```bash
# Add internal team registry (highest priority)
aam registry add team file:///mnt/shared/aam-registry --priority 1

# Add public registry (lower priority)
aam registry add public https://registry.aam.dev --priority 2

# Add experimental registry (lowest priority)
aam registry add experimental file:///$HOME/experiments --priority 3
```

View configuration:

```bash
aam registry list
```

```
Configured registries:
  team (file:///mnt/shared/aam-registry) [priority: 1]
  public (https://registry.aam.dev) [priority: 2]
  experimental (file:///home/user/experiments) [priority: 3]
```

### Resolution Behavior

When you run `aam install @author/some-package`:

1. AAM checks `team` registry first (priority 1)
2. If not found, checks `public` registry (priority 2)
3. If still not found, checks `experimental` (priority 3)
4. If not found anywhere, reports an error

This allows:

- **Overriding external packages** - If you have `@author/tool` in both `team` and `public`, the `team` version wins
- **Internal-only packages** - Scoped packages like `@myteam/*` only exist in `team`
- **Fallback to public** - External dependencies resolve from public registries

### Pinning Packages to Specific Registries

Force a package to install from a specific registry:

```bash
# Install from team registry only
aam install @myteam/tool --registry team

# Install from public registry only
aam install @external/lib --registry public
```

---

## Approach 4: Cloud Storage (Dropbox, Google Drive, OneDrive)

**Best for:** Small teams, simple setup, no Git knowledge required

### Setup with Dropbox

```bash
# One team member creates the registry
aam registry init ~/Dropbox/aam-registry

# Share the Dropbox folder with teammates

# Teammates add the registry (paths vary by OS)
# macOS/Linux:
aam registry add team file://$HOME/Dropbox/aam-registry --default

# Windows:
aam registry add team file:///C:/Users/yourname/Dropbox/aam-registry --default
```

### Publishing

```bash
aam pkg pack
aam pkg publish --registry team

# Dropbox automatically syncs to teammates
```

!!! warning "Sync Conflicts"
    Multiple people publishing simultaneously can cause sync conflicts. Use a coordination channel (Slack, email) to avoid conflicts, or use Git-based approach instead.

---

## Approach 5: Direct File Sharing (No Registry)

**Best for:** One-off sharing, testing, no registry setup

You can skip the registry entirely and share `.aam` files directly:

### Share via Slack/Email

```bash
# Pack the package
aam pkg pack

# Share dist/my-package-1.0.0.aam via Slack, email, etc.
```

### Install from File

Recipient:

```bash
# Download the .aam file
# Install directly
aam install ./my-package-1.0.0.aam
```

### Share via USB Drive

```bash
# Copy to USB
cp dist/my-package-1.0.0.aam /media/usb/

# On another machine
aam install /media/usb/my-package-1.0.0.aam
```

!!! note "Trade-offs"
    Direct file sharing works but loses benefits of registries:

    - No automatic updates (`aam update` won't work)
    - No dependency resolution from registry
    - Manual version tracking

---

## Registry Configuration Reference

### View Current Configuration

```bash
# List all registries
aam registry list

# Show details for a specific registry
aam registry info team
```

### Modify Registries

```bash
# Remove a registry
aam registry remove experimental

# Set a different default
aam registry set-default public

# Update registry metadata (pull latest)
aam registry update team
```

### Configuration File

Registries are stored in `~/.aam/config.yaml`:

```yaml
registries:
  - name: team
    url: file:///mnt/shared/aam-registry
    type: local
    priority: 1
  - name: public
    url: https://registry.aam.dev
    type: http
    priority: 2
```

You can edit this file directly if needed.

---

## Troubleshooting

### "Registry not found" error

**Problem:**

```
ERROR: Registry 'team' not found
```

**Solution:**

```bash
# Verify registry exists
ls /mnt/shared/aam-registry

# Re-add the registry
aam registry add team file:///mnt/shared/aam-registry
```

### "Permission denied" when publishing

**Problem:**

```
ERROR: Permission denied: /mnt/shared/aam-registry/packages/...
```

**Solution:**

```bash
# Check permissions
ls -la /mnt/shared/aam-registry/packages/

# Fix permissions (if you have access)
chmod 775 /mnt/shared/aam-registry/packages/

# Or contact the registry administrator
```

### Package not found after publishing

**Problem:**

```
ERROR: Package '@myteam/tool' not found
```

**Solution:**

```bash
# Verify it's in the registry
ls /mnt/shared/aam-registry/packages/@myteam/tool/

# Rebuild search index
cd /mnt/shared/aam-registry
aam registry reindex

# Check if registry is configured
aam registry list
```

### Git registry out of sync

**Problem:** Teammates can't see newly published packages

**Solution:**

```bash
# Pull latest changes
cd ~/aam-registry
git pull

# Or use AAM command
aam registry update team
```

---

## Best Practices

### 1. Use Scoped Packages for Internal Tools

```yaml
# aam.yaml
name: "@myteam/internal-tool"  # Scope makes it clear it's internal
```

### 2. Document Registry Setup for New Team Members

Create a `REGISTRY.md` in your team wiki:

```markdown
# AAM Registry Setup

## Step 1: Add the registry

\```bash
aam registry add team file:///mnt/shared/aam-registry --default
\```

## Step 2: Verify

\```bash
aam search "@myteam/*"
\```

You should see our internal packages.
```

### 3. Automate Registry Updates (Git-Based)

Add to your shell profile (`.bashrc`, `.zshrc`):

```bash
# Update AAM registry daily
if [ -d ~/aam-registry ]; then
    cd ~/aam-registry && git pull --quiet && cd - > /dev/null
fi
```

### 4. Use dist-tags for Stability

```bash
# Mark stable releases
aam dist-tag add @myteam/tool@1.2.0 stable

# Teammates install stable versions
aam install @myteam/tool@stable
```

---

## Comparison Table

| Feature | Shared Filesystem | Git-Based | Cloud Sync | Direct Files |
|---------|------------------|-----------|------------|--------------|
| **Setup Complexity** | Low | Medium | Low | None |
| **Version Control** | No | Yes | No | No |
| **Code Review** | No | Yes (PRs) | No | No |
| **Offline Access** | Yes | Yes | Yes | Yes |
| **Auto Updates** | Yes | Yes (with pull) | Yes | No |
| **Scale** | Small teams | Any size | Small teams | 1-on-1 |
| **Permissions** | Filesystem ACLs | Git access control | Share settings | N/A |

---

## Next Steps

Now that your team can share packages, explore:

- **[Working with Dependencies](working-with-dependencies.md)** - Manage package dependencies and version constraints
- **[Multi-Platform Deployment](multi-platform-deployment.md)** - Deploy to multiple AI platforms simultaneously
- **[Configuration Guide](../configuration/index.md)** - Advanced registry and deployment configuration

---

## Summary

You've learned how to share AAM packages with your team using:

- **Shared filesystem registries** - Simple, immediate, no server needed
- **Git-based registries** - Version controlled, PR workflow, distributed
- **Cloud storage** - Easy sync via Dropbox/Drive/OneDrive
- **Direct file sharing** - Quick one-off distribution
- **Multiple registries** - Combine internal and external sources

**Key Commands:**

```bash
aam registry init <path>                   # Create new registry
aam registry add <name> <url> [--default]  # Add registry
aam registry list                          # View configured registries
aam pkg publish --registry <name>              # Publish to specific registry
aam registry update <name>                 # Sync registry (git-based)
```

Choose the approach that fits your team's workflow and infrastructure!
