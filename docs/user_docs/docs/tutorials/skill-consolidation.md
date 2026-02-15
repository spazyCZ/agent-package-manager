# Tutorial: Skill Consolidation

**Difficulty:** Intermediate
**Time:** 20 minutes

## What You'll Learn

In this tutorial, you'll learn how to consolidate skills from multiple upstream sources and your own project into a single, curated AAM package. This is the "playlist" approach — pick the best skills from the community, add your own, and distribute a single package that gives your team everything they need.

## Prerequisites

- AAM installed (`aam --version` works)
- `aam init` completed (platform configured, default sources registered)
- Basic familiarity with `aam source` and `aam install` commands

!!! tip "New to sources?"
    If you haven't set up sources yet, run `aam init` first, then `aam source update --all` to clone the default community repositories. See [Git Sources](../concepts/git-sources.md) for background.

---

## The Scenario

Your team uses skills from several places:

- **Community sources** — Useful skills from `openai/skills`, `anthropics/skills`, and `github/awesome-copilot`
- **Internal skills** — Custom skills you've written for your specific stack (e.g., internal API conventions, deployment workflows)
- **Modified community skills** — Community skills you've tweaked to fit your team's coding standards

You want to:

1. Cherry-pick the best community skills
2. Combine them with your internal skills
3. Bundle everything into a single team package
4. Version and distribute it so everyone stays in sync

---

## Step 1: Review Available Skills

First, let's see what's available across all configured sources:

```bash
aam list --available
```

**Expected output:**

```
Source: github/awesome-copilot
  skill    commit-message-writer    Write conventional commit messages
  skill    code-reviewer            Review code for best practices
  skill    test-generator           Generate unit tests

Source: openai/skills:.curated
  skill    code-review              Comprehensive code review
  skill    refactoring              Suggest refactoring improvements
  skill    documentation-writer     Generate documentation

Source: anthropics/skills
  skill    skill-creator            Create new skills from descriptions
  skill    debugging-assistant      Systematic debugging helper

Source: microsoft/skills
  skill    csharp-analyzer          C# code analysis
  skill    azure-deployer           Azure deployment helper
```

You can also search for specific skills:

```bash
aam search review --type skill
```

```
Search results for "review" (3 matches)

Name                    Version  Type   Source                    Description
code-reviewer           —        skill  github/awesome-copilot    Review code for best practices
code-review             —        skill  openai/skills:.curated    Comprehensive code review
```

---

## Step 2: Create the Consolidation Package

Create a directory for your consolidated package:

```bash
mkdir team-skills && cd team-skills
```

Now use `aam pkg create --from-source` to pull skills from remote sources. Start with the first source:

```bash
aam pkg create --from-source anthropics/skills \
  --type skill \
  --name @myteam/consolidated-skills \
  --version 1.0.0 \
  --description "Curated team skill set" \
  --author "My Team" \
  --output-dir . \
  --yes
```

**Expected output:**

```
Scanning source 'anthropics/skills' for skill artifacts...

Found 2 artifacts:
  [x] 1. skill-creator         skills/skill-creator/SKILL.md
  [x] 2. debugging-assistant   skills/debugging-assistant/SKILL.md

Creating package...
  ✓ Created aam.yaml
  ✓ Copied skill-creator → skills/skill-creator/
  ✓ Copied debugging-assistant → skills/debugging-assistant/
  ✓ Added provenance metadata
  ✓ Computed file checksums

✓ Package created: @myteam/consolidated-skills@1.0.0
  2 artifacts (2 skills)
```

!!! info "What's `--from-source`?"
    The `--from-source` flag tells `aam pkg create` to pull artifacts from a registered git source instead of scanning the local project directory. AAM copies the files from the source cache and records provenance (source URL, commit SHA, fetch timestamp) in the manifest.

---

## Step 3: Add Skills from Other Sources

Now add skills from additional sources. Use `aam pkg create --from-source` with `--artifacts` to cherry-pick specific skills:

```bash
# Add just the code-review skill from openai/skills:.curated
aam pkg create --from-source openai/skills:.curated \
  --artifacts code-review \
  --output-dir . \
  --yes
```

```
Found 1 matching artifact:
  [x] 1. code-review   skills/.curated/code-review/SKILL.md

  ✓ Copied code-review → skills/code-review/
  ✓ Updated aam.yaml (3 skills total)
```

```bash
# Add the commit-message-writer from github/awesome-copilot
aam pkg create --from-source github/awesome-copilot \
  --artifacts commit-message-writer \
  --output-dir . \
  --yes
```

```
  ✓ Copied commit-message-writer → skills/commit-message-writer/
  ✓ Updated aam.yaml (4 skills total)
```

!!! tip "Cherry-picking with `--artifacts`"
    Use `--artifacts` to select specific artifacts by name. You can specify multiple names separated by commas: `--artifacts code-review,refactoring`. Without `--artifacts`, all discovered artifacts from the source are included.

---

## Step 4: Add Your Own Internal Skills

Now add your team's custom skills. Create them directly in the package:

```bash
# Create a custom skill for your internal API conventions
mkdir -p skills/internal-api-conventions
cat > skills/internal-api-conventions/SKILL.md << 'EOF'
---
name: internal-api-conventions
description: Enforce team API design conventions and patterns
---

# Internal API Conventions

## When to Use

Use this skill when designing or reviewing REST API endpoints.

## Conventions

### Naming
- Use kebab-case for URL paths: `/user-profiles/`, not `/userProfiles/`
- Use plural nouns for collections: `/users/`, not `/user/`
- Use `snake_case` for JSON field names

### Versioning
- Always version APIs: `/api/v1/...`
- Never break backward compatibility in the same major version

### Error Responses
- Always return structured errors:
  ```json
  {"error": {"code": "NOT_FOUND", "message": "User not found", "details": {}}}
  ```
- Use standard HTTP status codes

### Pagination
- Use cursor-based pagination for lists
- Always include `next_cursor` and `has_more` fields

## Review Checklist

When reviewing API changes:

1. ✅ Endpoints follow naming conventions
2. ✅ Error responses use the standard format
3. ✅ New fields don't break existing clients
4. ✅ Pagination is implemented for list endpoints
5. ✅ Input validation returns 422 with field-level errors
EOF
```

```bash
# Create a deployment workflow skill
mkdir -p skills/deploy-workflow
cat > skills/deploy-workflow/SKILL.md << 'EOF'
---
name: deploy-workflow
description: Guide through the team deployment process
---

# Deployment Workflow

## When to Use

Use this skill when preparing or executing a deployment.

## Pre-Deployment Checklist

1. **Tests pass** — All CI checks are green
2. **Changelog updated** — Version bump and changelog entry added
3. **Database migrations** — Any pending migrations are reviewed
4. **Feature flags** — New features are behind flags if needed
5. **Rollback plan** — Know how to revert if something goes wrong

## Deployment Steps

### Staging
```bash
git tag -a v{version}-rc.1 -m "Release candidate"
git push origin v{version}-rc.1
# Wait for staging deploy to complete
# Run smoke tests against staging
```

### Production
```bash
git tag -a v{version} -m "Release v{version}"
git push origin v{version}
# Monitor error rates for 30 minutes
# Verify key user flows
```

## Rollback

If issues are detected:
```bash
# Revert to previous version
git revert HEAD
git push origin main
# Or: redeploy the previous tag
```
EOF
```

Now update the manifest to include your custom skills:

```bash
cat >> aam.yaml << 'EOF'

# Added manually — custom skills below are appended to the artifacts list
EOF
```

Or better yet, just edit `aam.yaml` to add them to the existing artifacts list:

```yaml title="aam.yaml (updated)"
name: "@myteam/consolidated-skills"
version: 1.0.0
description: Curated team skill set
author: My Team
license: Apache-2.0

artifacts:
  skills:
    # From anthropics/skills
    - name: skill-creator
      path: skills/skill-creator/
      description: Create new skills from descriptions
    - name: debugging-assistant
      path: skills/debugging-assistant/
      description: Systematic debugging helper

    # From openai/skills:.curated
    - name: code-review
      path: skills/code-review/
      description: Comprehensive code review

    # From github/awesome-copilot
    - name: commit-message-writer
      path: skills/commit-message-writer/
      description: Write conventional commit messages

    # Internal team skills
    - name: internal-api-conventions
      path: skills/internal-api-conventions/
      description: Enforce team API design conventions and patterns
    - name: deploy-workflow
      path: skills/deploy-workflow/
      description: Guide through the team deployment process

dependencies: {}

platforms:
  cursor:
    skill_scope: project
  claude:
    merge_instructions: true
  copilot:
    merge_instructions: true
```

---

## Step 5: Review the Package Structure

Your consolidated package should now look like this:

```bash
tree -L 2
```

```
.
├── aam.yaml
└── skills/
    ├── code-review/
    ├── commit-message-writer/
    ├── debugging-assistant/
    ├── deploy-workflow/
    ├── internal-api-conventions/
    └── skill-creator/
```

Six skills from three different sources plus your own — all in one package.

---

## Step 6: Validate and Pack

Validate the consolidated package:

```bash
aam pkg validate
```

```
Validating @myteam/consolidated-skills@1.0.0...

Manifest:
  ✓ name: valid scoped format
  ✓ version: valid semver (1.0.0)
  ✓ description: present
  ✓ author: present

Artifacts:
  ✓ skill: skill-creator
  ✓ skill: debugging-assistant
  ✓ skill: code-review
  ✓ skill: commit-message-writer
  ✓ skill: internal-api-conventions
  ✓ skill: deploy-workflow

✓ Package is valid and ready to publish
```

Build the archive:

```bash
aam pkg pack
```

```
Building @myteam/consolidated-skills@1.0.0...

✓ Built myteam-consolidated-skills-1.0.0.aam (18.5 KB)
  6 skills, checksums computed
```

---

## Step 7: Distribute to Your Team

### Option A: Publish to a Registry

```bash
# Publish to your team's registry
aam pkg publish --registry team-registry
```

Your teammates can then install with a single command:

```bash
aam install @myteam/consolidated-skills
```

### Option B: Share the Archive Directly

Share the `.aam` file via Slack, email, or a shared drive:

```bash
# Teammate installs from the archive
aam install ./myteam-consolidated-skills-1.0.0.aam
```

### Option C: Use a Git Repository as a Source

Commit the package to a Git repository and add it as a source:

```bash
# In the package directory
git init && git add . && git commit -m "Initial consolidated skills"
git remote add origin git@github.com:myteam/team-skills.git
git push -u origin main

# Teammates add it as a source
aam source add myteam/team-skills
aam install consolidated-skills
```

---

## Step 8: Keep It Updated

When upstream sources release new skills or updates, you can refresh your package:

```bash
# Update all sources to fetch latest changes
aam source update --all

# Check what changed
aam outdated

# Re-create from source to pick up changes
aam pkg create --from-source anthropics/skills \
  --artifacts skill-creator,debugging-assistant \
  --output-dir . \
  --yes
```

Bump the version in `aam.yaml`, then validate, pack, and publish the update:

```bash
# Edit aam.yaml: version: 1.0.0 → 1.1.0
aam pkg validate
aam pkg pack
aam pkg publish --registry team-registry
```

Your teammates upgrade with:

```bash
aam upgrade @myteam/consolidated-skills
```

---

## Consolidation Patterns

Here are common patterns for skill consolidation:

### Pattern 1: Role-Based Packages

Create separate packages for different roles:

```
@myteam/frontend-skills    → React, CSS, accessibility skills
@myteam/backend-skills     → API, database, security skills
@myteam/devops-skills      → CI/CD, Docker, monitoring skills
```

### Pattern 2: Project-Specific Packages

Bundle skills relevant to a specific project:

```
@myteam/project-alpha      → API conventions + deploy workflow + code review
@myteam/project-beta       → ML pipeline + data validation + notebook helpers
```

### Pattern 3: Onboarding Package

A single package for new team members:

```
@myteam/onboarding         → Coding standards + git workflow + deploy process + code review
```

### Pattern 4: Layered Packages with Dependencies

Use dependencies to create a layered structure:

```yaml
# @myteam/base-skills/aam.yaml
name: "@myteam/base-skills"
artifacts:
  skills:
    - name: code-review
    - name: commit-message-writer
```

```yaml
# @myteam/frontend-skills/aam.yaml
name: "@myteam/frontend-skills"
dependencies:
  "@myteam/base-skills": "^1.0.0"
artifacts:
  skills:
    - name: react-patterns
    - name: css-conventions
```

---

## Next Steps

Now that you've consolidated skills, you can:

- **Install across platforms** — Follow the [Multi-Platform Deployment](multi-platform-deployment.md) tutorial
- **Add dependencies** — Learn about dependencies in [Working with Dependencies](working-with-dependencies.md)
- **Share with your team** — Follow the [Sharing with Your Team](share-with-team.md) tutorial
- **Keep skills updated** — Use `aam outdated` and `aam upgrade` to stay current

---

## Troubleshooting

### Source not found

**Problem:** `aam pkg create --from-source myrepo` fails with "source not found"

**Solution:** Make sure the source is registered:

```bash
aam source list                    # Check registered sources
aam source add github.com/org/repo # Add missing source
aam source update org/repo         # Ensure cache is fresh
```

### Artifact name conflicts

**Problem:** Two sources have skills with the same name

**Solution:** Use qualified names when installing or rename one skill in your package:

```bash
# Install with qualified name
aam install openai/skills:.curated/code-review

# Or rename in your package by editing the name in aam.yaml
# and renaming the directory
```

### Stale source cache

**Problem:** Source shows old artifacts that have been removed upstream

**Solution:** Update the source cache:

```bash
aam source update --all
```

---

## Summary

In this tutorial, you learned how to:

- Browse available skills across multiple sources with `aam list --available` and `aam search`
- Pull skills from remote sources with `aam pkg create --from-source`
- Cherry-pick specific artifacts with `--artifacts`
- Add your own custom skills alongside community ones
- Validate, pack, and distribute a consolidated package
- Keep the package updated as upstream sources change

**Key Commands:**

```bash
aam list --available                              # Browse all source artifacts
aam search <query> --type skill                   # Search for specific skills
aam pkg create --from-source <source> --artifacts <names>  # Pull from source
aam pkg validate                                  # Verify package
aam pkg pack                                      # Build archive
aam source update --all                           # Refresh source caches
```

Ready to share your consolidated package? Continue to [Sharing with Your Team](share-with-team.md)!
