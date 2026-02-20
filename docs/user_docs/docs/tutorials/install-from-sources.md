# Tutorial: Installing Skills from Sources

**Difficulty:** Beginner
**Time:** 10 minutes

## What You'll Learn

In this tutorial, you'll walk through the complete workflow of setting up AAM, connecting to community skill sources, discovering artifacts, and installing them into your project. By the end, you'll have community skills deployed and working in your IDE.

## Prerequisites

- AAM installed (`aam --version` works)
- A project directory where you want to use skills
- Git installed (for source cloning)

---

## The Scenario

You've just started a new project and want to supercharge your AI coding assistant with community skills. Rather than writing everything from scratch, you'll:

1. Initialize AAM and connect to community skill repositories
2. Browse and search for useful skills
3. Install skills directly into your project
4. Verify the installation and manage updates

---

## Step 1: Initialize AAM

Navigate to your project directory and run the setup:

```bash
cd ~/my-project
aam init
```

AAM detects your IDE platform and walks you through setup:

```
  Detected platform: cursor
Choose platform [cursor]:
Register community artifact sources? [Y/n] y

✓ AAM initialized successfully.
  Platform:  cursor
  Config:    ~/.aam/config.yaml
  Sources:   4 community source(s) added

Next steps:
  aam search <query>   — Find packages to install
  aam install <pkg>    — Install a package
  aam list --available — Browse source artifacts
  aam pkg init         — Create a new package
```

!!! info "What just happened?"
    `aam init` did two things:

    1. **Set your platform** — AAM knows to deploy skills to `.cursor/skills/`, agents to `.cursor/rules/`, etc.
    2. **Registered default sources** — Added 4 curated community repositories as git sources:
        - `github/awesome-copilot`
        - `openai/skills:.curated`
        - `anthropics/skills`
        - `microsoft/skills`

    If you missed adding default sources during init, run `aam source enable-defaults` at any time.

For non-interactive setup (e.g., in CI or scripts):

```bash
aam init --yes
```

This auto-detects the platform and registers default sources without prompting.

---

## Step 2: Update Source Caches

The sources are registered but not yet cloned. Fetch them:

```bash
aam source update --all
```

```
Updating all sources...

  github/awesome-copilot
    ✓ Cloned https://github.com/github/awesome-copilot (main)
    Found 12 artifacts (8 skills, 2 agents, 2 prompts)

  openai/skills:.curated
    ✓ Cloned https://github.com/openai/skills (main) → skills/.curated
    Found 6 artifacts (6 skills)

  anthropics/skills
    ✓ Cloned https://github.com/anthropics/skills (main)
    Found 4 artifacts (3 skills, 1 agent)

  microsoft/skills
    ✓ Cloned https://github.com/microsoft/skills (main) → .github/skills
    Found 5 artifacts (5 skills)

✓ Updated 4 sources (27 artifacts total)
```

!!! tip "Where are the clones?"
    Source repositories are cached at `~/.aam/cache/git/{host}/{owner}/{repo}/`. This cache is shared across all your projects — you only clone once.

---

## Step 3: Browse Available Skills

See everything available across all sources:

```bash
aam list --available
```

```
Source: github/awesome-copilot
  Type     Name                     Description
  skill    commit-message-writer    Write conventional commit messages
  skill    code-reviewer            Review code for best practices
  skill    test-generator           Generate unit tests
  skill    documentation-writer     Write project documentation
  ...

Source: openai/skills:.curated
  Type     Name                     Description
  skill    code-review              Comprehensive code review
  skill    refactoring              Suggest refactoring improvements
  ...

Source: anthropics/skills
  Type     Name                     Description
  skill    skill-creator            Create new skills from descriptions
  skill    debugging-assistant      Systematic debugging helper
  ...
```

### Search for Specific Skills

Use `aam search` to find skills by keyword:

```bash
aam search review
```

```
Search results for "review" (3 matches)

Name                Version  Type   Source                    Description
code-reviewer       —        skill  github/awesome-copilot    Review code for best practices
code-review         —        skill  openai/skills:.curated    Comprehensive code review
```

Filter by artifact type:

```bash
aam search deploy --type skill
```

---

## Step 4: Install a Skill

Install a skill by name:

```bash
aam install code-reviewer
```

```
Searching sources for 'code-reviewer'...
  Found code-reviewer (skill) in source github/awesome-copilot

Installing code-reviewer from source github/awesome-copilot...
  ✓ Copied skill files
  ✓ Generated manifest
  ✓ Computed checksums
  ✓ Deployed to .cursor/skills/code-reviewer/

✓ Installed code-reviewer from source github/awesome-copilot @ a1b2c3d
```

That's it — the skill is now installed and deployed to your IDE.

### What Happened Under the Hood

1. **Resolved** — AAM searched all configured sources and found `code-reviewer` in `github/awesome-copilot`
2. **Copied** — Skill files were copied from the source cache to `.aam/packages/code-reviewer/`
3. **Manifest** — An `aam.yaml` was generated with provenance metadata (source URL, commit SHA)
4. **Checksums** — Per-file SHA-256 checksums were computed for integrity verification
5. **Deployed** — The skill was deployed to `.cursor/skills/code-reviewer/` (based on your configured platform)
6. **Locked** — The lock file (`.aam/aam-lock.yaml`) was updated with the exact version and commit

---

## Step 5: Install from a Specific Source

When multiple sources have skills with similar names, use the **qualified name** to be explicit:

```bash
# Install from a specific source using: source-name/artifact-name
aam install openai/skills:.curated/code-review
```

```
Searching sources for 'openai/skills:.curated/code-review'...
  Found code-review (skill) in source openai/skills:.curated

✓ Installed code-review from source openai/skills:.curated @ d4e5f6a
```

!!! tip "Finding qualified names"
    The qualified name format is `source-name/artifact-name`. You can discover these from:

    - `aam search <query>` — the **Source** column shows the source name
    - `aam list --available` — the group header is the source name
    - `aam info source-name/artifact-name` — shows details and the install command

---

## Step 6: Verify the Installation

Check what's installed:

```bash
aam list
```

```
Installed packages:
  code-reviewer   —  1 artifact (1 skill)   source: github/awesome-copilot
  code-review     —  1 artifact (1 skill)   source: openai/skills:.curated
```

Verify file integrity:

```bash
aam verify
```

```
Verifying installed packages...

  code-reviewer
    ✓ All files match checksums (2 files)

  code-review
    ✓ All files match checksums (3 files)

✓ All packages verified
```

Check what was deployed to your IDE:

```bash
ls .cursor/skills/
```

```
code-review/
code-reviewer/
```

---

## Step 7: Get Package Details

View detailed information about an installed package:

```bash
aam info code-reviewer
```

```
code-reviewer
  Type:        skill
  Source:      github/awesome-copilot
  Commit:      a1b2c3d
  Installed:   .aam/packages/code-reviewer/
  Deployed:    .cursor/skills/code-reviewer/

  Provenance:
    source_url:    https://github.com/github/awesome-copilot
    source_ref:    main
    source_commit: a1b2c3d4e5f6
    fetched_at:    2026-02-13T10:30:00Z
```

---

## Step 8: Check for Updates

After some time, check if upstream sources have new content:

```bash
# Fetch latest from all sources
aam source update --all
```

```
Updating all sources...

  github/awesome-copilot
    ✓ Updated (a1b2c3d → f7g8h9i)
    2 new artifacts, 1 modified

  openai/skills:.curated
    ✓ Already up to date

  anthropics/skills
    ✓ Updated (j1k2l3m → n4o5p6q)
    1 new artifact
```

Check which installed packages have upstream changes:

```bash
aam outdated
```

```
Outdated packages:

  Package          Current Commit  Latest Commit   Source
  code-reviewer    a1b2c3d         f7g8h9i         github/awesome-copilot
```

Upgrade outdated packages:

```bash
aam upgrade code-reviewer
```

```
Upgrading code-reviewer...
  Source: github/awesome-copilot
  a1b2c3d → f7g8h9i

  ✓ Updated skill files
  ✓ Recomputed checksums
  ✓ Redeployed to .cursor/skills/code-reviewer/

✓ Upgraded code-reviewer
```

Or upgrade everything at once:

```bash
aam upgrade
```

---

## Step 9: Add Your Own Sources

Beyond the defaults, add any Git repository as a source:

```bash
# GitHub shorthand
aam source add myorg/ai-skills

# Full HTTPS URL
aam source add https://github.com/myorg/ai-skills

# With a branch and subdirectory
aam source add myorg/monorepo@develop:skills/curated

# SSH URL
aam source add git@github.com:myorg/private-skills.git
```

After adding, update and browse:

```bash
aam source update myorg/ai-skills
aam list --available
```

### Manage Sources

```bash
# List all configured sources
aam source list

# Scan a specific source for artifacts
aam source scan anthropics/skills

# Remove a source (optionally delete cached clone)
aam source remove myorg/old-skills --purge-cache
```

---

## Step 10: Uninstall a Package

If you no longer need a skill:

```bash
aam uninstall code-review
```

```
Uninstalling code-review...
  ✓ Removed from .aam/packages/code-review/
  ✓ Undeployed from .cursor/skills/code-review/
  ✓ Updated lock file

✓ Uninstalled code-review
```

---

## Install Options Reference

Here's a quick reference for `aam install` options:

```bash
# Install latest from any source
aam install <skill-name>

# Install from a specific source (qualified name)
aam install <source-name>/<artifact-name>

# Install from a local directory
aam install ./path/to/package/

# Install from an .aam archive
aam install my-package-1.0.0.aam

# Install without deploying to IDE
aam install <skill-name> --no-deploy

# Force reinstall
aam install <skill-name> --force

# Preview what would happen
aam install <skill-name> --dry-run

# Install to a specific platform
aam install <skill-name> --platform claude

# Install globally (available across all projects)
aam install <skill-name> -g
```

---

## Next Steps

Now that you know how to discover and install skills, you can:

- **Consolidate skills** — Bundle favorites into a team package with [Skill Consolidation](skill-consolidation.md)
- **Create your own** — Build a package from scratch in [Building a Code Review Package](build-code-review-package.md)
- **Package existing skills** — Wrap what you already have in [Packaging Existing Skills](package-existing-skills.md)
- **Deploy to multiple platforms** — Configure multi-platform deployment in [Multi-Platform Deployment](multi-platform-deployment.md)
- **Manage dependencies** — Learn about dependency resolution in [Working with Dependencies](working-with-dependencies.md)

---

## Troubleshooting

### Source clone fails

**Problem:** `aam source update` fails with a git error

**Solutions:**

- Check your internet connection
- Verify the repository URL is correct: `aam source list`
- For private repos, ensure SSH keys or credentials are configured
- Try removing and re-adding: `aam source remove <name> --purge-cache` then `aam source add <url>`

### Artifact not found

**Problem:** `aam install my-skill` says "not found"

**Solutions:**

- Run `aam source update --all` to refresh caches
- Search to verify the name: `aam search my-skill`
- Use `aam list --available` to see all available artifacts
- Check if the skill requires a qualified name: `aam search my-skill` and note the Source column

### Deployment fails

**Problem:** Skill is installed but not deployed to the IDE

**Solutions:**

- Check your platform: `aam config get default_platform`
- Try redeploying: `aam install <skill-name> --force`
- Verify the deploy path exists: `ls .cursor/skills/` (for Cursor)
- Restart your IDE to pick up new skills

### Lock file conflicts

**Problem:** Multiple team members get different versions

**Solution:** Commit `.aam/aam-lock.yaml` to version control. The lock file records exact source commits, so everyone gets the same versions:

```bash
git add .aam/aam-lock.yaml
git commit -m "Lock AAM package versions"
```

---

## Summary

In this tutorial, you learned how to:

- Initialize AAM and configure your platform with `aam init`
- Update source caches with `aam source update --all`
- Browse available artifacts with `aam list --available` and `aam search`
- Install skills from sources with `aam install`
- Use qualified names to install from a specific source
- Verify installations with `aam verify`
- Check for and apply updates with `aam outdated` and `aam upgrade`
- Add custom git sources with `aam source add`
- Uninstall packages with `aam uninstall`

**Key Commands:**

```bash
aam init                          # Set up AAM (platform + sources)
aam source update --all           # Clone/refresh source caches
aam list --available              # Browse all available artifacts
aam search <query>                # Search for skills
aam install <name>                # Install a skill
aam install <source>/<artifact>   # Install from specific source
aam verify                        # Check file integrity
aam outdated                      # List outdated packages
aam upgrade                       # Upgrade to latest versions
```

Ready to consolidate your favorite skills into a team package? Continue to [Skill Consolidation](skill-consolidation.md)!
