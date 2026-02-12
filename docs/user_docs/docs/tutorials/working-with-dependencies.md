# Tutorial: Working with Dependencies

**Difficulty:** Intermediate
**Time:** 20 minutes

## What You'll Learn

In this tutorial, you'll master AAM's dependency management system. Learn how to:

- Declare dependencies with version constraints
- Understand all constraint syntax (`^`, `~`, `>=`, `*`, exact, ranges)
- Work with transitive dependencies
- Use lock files for reproducible installs
- Visualize dependency trees with `aam list --tree`
- Handle and resolve version conflicts
- Update dependencies safely with `aam update`

## Prerequisites

- AAM installed (`aam --version` works)
- Basic understanding of semantic versioning (MAJOR.MINOR.PATCH)
- At least one AAM package created or available

## The Scenario

You're building a `code-analyzer` package that needs:

1. **linting-rules** - Provides linting configurations (you want compatible versions: `>=1.0.0, <2.0.0`)
2. **security-checker** - Security analysis tool (you want the latest stable: `^2.0.0`)
3. **common-prompts** - Shared prompt templates (you want approximately version 1.5: `~1.5.0`)

Let's learn how to declare these dependencies and manage them effectively.

---

## Understanding Semantic Versioning

AAM uses semantic versioning (semver):

```
MAJOR.MINOR.PATCH
  2  .  1  .  3

MAJOR = Breaking changes (incompatible API changes)
MINOR = New features (backward compatible)
PATCH = Bug fixes (backward compatible)
```

**Examples:**

- `1.0.0` → `1.0.1` = Patch update (safe)
- `1.0.0` → `1.1.0` = Minor update (new features, safe)
- `1.0.0` → `2.0.0` = Major update (breaking changes, review needed)

---

## Step 1: Declare Dependencies

Edit your package's `aam.yaml` to add dependencies:

```yaml
# aam.yaml
name: "@myorg/code-analyzer"
version: 1.0.0
description: "Comprehensive code analysis toolkit"
author: your-username
license: Apache-2.0

artifacts:
  # ... your artifacts ...

dependencies:
  linting-rules: "^1.0.0"              # Compatible version
  "@vendor/security-checker": "^2.0.0" # Scoped dependency
  common-prompts: "~1.5.0"             # Approximate version
```

### Version Constraint Syntax

Let's understand each constraint type:

---

## Version Constraint Reference

### 1. Exact Version

```yaml
dependencies:
  my-package: "1.2.3"
```

**Meaning:** Only version `1.2.3` is acceptable

**Resolves to:** `1.2.3` (exactly)

**Use when:** You need a specific version for compatibility or stability

**Example:**

```yaml
dependencies:
  legacy-tool: "0.9.5"  # Only this old version works with our code
```

---

### 2. Caret (^) - Compatible Version

```yaml
dependencies:
  my-package: "^1.2.3"
```

**Meaning:** Compatible with `1.2.3` (allows MINOR and PATCH updates)

**Resolves to:** `>=1.2.3`, `<2.0.0`

**Use when:** You want bug fixes and new features, but not breaking changes

**Examples:**

| Constraint | Allows | Blocks |
|------------|--------|--------|
| `^1.2.3` | `1.2.3`, `1.2.4`, `1.3.0`, `1.9.9` | `2.0.0`, `0.9.0` |
| `^2.0.0` | `2.0.0`, `2.1.0`, `2.99.0` | `3.0.0`, `1.9.9` |
| `^0.2.3` | `0.2.3`, `0.2.4`, `0.2.99` | `0.3.0`, `1.0.0` |

!!! info "Special Case: 0.x Versions"
    For `0.x.y` versions, the caret is more restrictive:

    - `^0.2.3` → `>=0.2.3`, `<0.3.0` (only patch updates)

    This is because 0.x versions can introduce breaking changes in MINOR updates.

**Most Common Use Case:**

```yaml
dependencies:
  security-tools: "^2.1.0"  # Get updates, avoid breaking changes
```

---

### 3. Tilde (~) - Approximate Version

```yaml
dependencies:
  my-package: "~1.2.3"
```

**Meaning:** Approximately equivalent to `1.2.3` (allows PATCH updates only)

**Resolves to:** `>=1.2.3`, `<1.3.0`

**Use when:** You want bug fixes but no new features

**Examples:**

| Constraint | Allows | Blocks |
|------------|--------|--------|
| `~1.2.3` | `1.2.3`, `1.2.4`, `1.2.99` | `1.3.0`, `1.1.0` |
| `~2.1.0` | `2.1.0`, `2.1.1`, `2.1.9` | `2.2.0`, `3.0.0` |
| `~0.2.3` | `0.2.3`, `0.2.4` | `0.3.0`, `0.2.2` |

**Use Case:**

```yaml
dependencies:
  stable-tool: "~1.5.0"  # Only accept patch updates to 1.5.x
```

---

### 4. Greater Than or Equal (>=)

```yaml
dependencies:
  my-package: ">=1.2.3"
```

**Meaning:** Version `1.2.3` or higher

**Resolves to:** Any version `>=1.2.3` (no upper limit)

**Use when:** You need a minimum version for a feature or fix

**Examples:**

| Constraint | Allows | Blocks |
|------------|--------|--------|
| `>=1.2.3` | `1.2.3`, `1.3.0`, `2.0.0`, `99.0.0` | `1.2.2`, `1.0.0` |
| `>=2.0.0` | `2.0.0`, `2.1.0`, `3.0.0` | `1.9.9` |

**Use Case:**

```yaml
dependencies:
  modern-library: ">=3.0.0"  # Requires features from 3.0+
```

---

### 5. Wildcard (*) - Any Version

```yaml
dependencies:
  my-package: "*"
```

**Meaning:** Any available version is acceptable

**Resolves to:** Latest available version

**Use when:** You don't care about the version (rare, not recommended)

**Example:**

```yaml
dependencies:
  utilities: "*"  # Always get the latest (risky for production)
```

!!! warning "Use Sparingly"
    Wildcard dependencies make your package unpredictable. Prefer explicit constraints.

---

### 6. Range Constraints

```yaml
dependencies:
  my-package: ">=1.2.0,<2.0.0"
```

**Meaning:** Version between `1.2.0` (inclusive) and `2.0.0` (exclusive)

**Use when:** You need fine-grained control over version ranges

**Examples:**

```yaml
dependencies:
  tool: ">=1.5.0,<1.8.0"      # Between 1.5.0 and 1.7.x
  lib: ">=2.0.0,<3.0.0"       # Equivalent to ^2.0.0
  package: ">=1.0.0,<1.0.5"   # Only 1.0.0 through 1.0.4
```

---

## Step 2: Install with Dependencies

When you install a package with dependencies, AAM resolves and installs them automatically:

```bash
aam install @myorg/code-analyzer
```

Expected output:

```
Resolving @myorg/code-analyzer@1.0.0...

Resolving dependencies...
  linting-rules: ^1.0.0 → 1.3.2 (latest compatible)
  @vendor/security-checker: ^2.0.0 → 2.1.5 (latest compatible)
  common-prompts: ~1.5.0 → 1.5.3 (latest patch)

Installing 4 packages:
  + @myorg/code-analyzer@1.0.0
  + linting-rules@1.3.2
  + @vendor/security-checker@2.1.5
  + common-prompts@1.5.3

Deploying to cursor...
  → [artifacts from all 4 packages]

✓ Installed 4 packages (12 artifacts total)
✓ Created lock file: .aam/aam-lock.yaml
```

AAM automatically:

1. Resolved each dependency constraint to a specific version
2. Downloaded and installed all packages
3. Deployed artifacts from all packages
4. Created a lock file for reproducibility

---

## Step 3: Understanding the Lock File

AAM creates `.aam/aam-lock.yaml` after installation:

```yaml
# .aam/aam-lock.yaml — DO NOT EDIT MANUALLY
lockfile_version: 1
resolved_at: "2026-02-09T14:30:00Z"

packages:
  "@myorg/code-analyzer":
    version: 1.0.0
    source: aam-central
    checksum: sha256:abc123...
    dependencies:
      linting-rules: "^1.0.0"
      "@vendor/security-checker": "^2.0.0"
      common-prompts: "~1.5.0"

  linting-rules:
    version: 1.3.2
    source: aam-central
    checksum: sha256:def456...
    dependencies: {}

  "@vendor/security-checker":
    version: 2.1.5
    source: aam-central
    checksum: sha256:789abc...
    dependencies:
      vulnerability-db: "^3.0.0"  # Transitive dependency!

  common-prompts:
    version: 1.5.3
    source: aam-central
    checksum: sha256:321fed...
    dependencies: {}

  vulnerability-db:
    version: 3.2.1
    source: aam-central
    checksum: sha256:654cba...
    dependencies: {}
```

### Why Lock Files Matter

**Without lock file:**

- Developer A installs today: gets `linting-rules@1.3.2`
- Developer B installs next week: gets `linting-rules@1.4.0` (just released)
- Different versions = potential inconsistencies

**With lock file:**

- Both developers get exactly `linting-rules@1.3.2`
- Reproducible builds across teams
- Controlled updates (via `aam update`)

### Lock File Best Practices

1. **Commit lock files to Git**
   ```bash
   git add .aam/aam-lock.yaml
   git commit -m "Lock dependencies"
   ```

2. **Don't edit lock files manually** - Let AAM manage them

3. **Update intentionally** - Use `aam update`, not manual edits

---

## Step 4: Transitive Dependencies

Notice `vulnerability-db@3.2.1` in the lock file? That's a **transitive dependency** - a dependency of your dependency.

**Dependency tree:**

```
@myorg/code-analyzer@1.0.0
├── linting-rules@1.3.2
├── @vendor/security-checker@2.1.5
│   └── vulnerability-db@3.2.1  ← Transitive dependency
└── common-prompts@1.5.3
```

AAM automatically resolves transitive dependencies.

### Visualize Dependency Tree

```bash
aam list --tree
```

```
@myorg/code-analyzer@1.0.0
├── linting-rules@1.3.2
├── @vendor/security-checker@2.1.5
│   └── vulnerability-db@3.2.1
└── common-prompts@1.5.3
```

For multiple installed packages:

```bash
aam list --tree
```

```
my-project (workspace)
├── @myorg/code-analyzer@1.0.0
│   ├── linting-rules@1.3.2
│   ├── @vendor/security-checker@2.1.5
│   │   └── vulnerability-db@3.2.1
│   └── common-prompts@1.5.3
└── @team/deploy-helper@2.0.0
    ├── docker-utils@1.1.0
    └── ci-templates@3.0.5
```

---

## Step 5: Updating Dependencies

### Update All Packages

Check for updates:

```bash
aam update
```

```
Checking for updates...

Available updates:
  linting-rules: 1.3.2 → 1.4.1 (minor update)
    Constraint: ^1.0.0 allows up to 1.99.99

  @vendor/security-checker: 2.1.5 → 2.2.0 (minor update)
    Constraint: ^2.0.0 allows up to 2.99.99

  common-prompts: 1.5.3 → 1.5.4 (patch update)
    Constraint: ~1.5.0 allows up to 1.5.99

  vulnerability-db: 3.2.1 → 3.3.0 (minor update)
    (transitive dependency of @vendor/security-checker)

Update 4 packages? [Y/n]
```

Press `y` to update:

```
Updating packages...
  ✓ Updated linting-rules to 1.4.1
  ✓ Updated @vendor/security-checker to 2.2.0
  ✓ Updated common-prompts to 1.5.4
  ✓ Updated vulnerability-db to 3.3.0

Redeploying updated packages...
  [deployment output]

✓ Updated 4 packages
✓ Updated lock file: .aam/aam-lock.yaml
```

### Update Specific Package

```bash
# Update only linting-rules
aam update linting-rules
```

```
Checking for updates to linting-rules...
  linting-rules: 1.3.2 → 1.4.1

Update? [Y/n] y

✓ Updated linting-rules to 1.4.1
✓ Updated lock file
```

### Update to Specific Version

```bash
# Update to a specific version (must satisfy constraint)
aam update linting-rules@1.4.0
```

---

## Step 6: Handling Version Conflicts

### Scenario: Incompatible Dependencies

Suppose you try to install two packages with conflicting requirements:

```yaml
# Package A
dependencies:
  shared-lib: "^1.0.0"  # Wants 1.x

# Package B
dependencies:
  shared-lib: "^2.0.0"  # Wants 2.x
```

When you install both:

```bash
aam install package-a package-b
```

AAM detects the conflict:

```
ERROR: Dependency conflict detected

  package-a@1.0.0 requires shared-lib ^1.0.0
  package-b@2.0.0 requires shared-lib ^2.0.0

No version of shared-lib satisfies both constraints.

Conflict details:
  ^1.0.0 allows: 1.0.0 - 1.99.99
  ^2.0.0 allows: 2.0.0 - 2.99.99
  Overlap: (none)

Suggestions:
  1. Check if newer versions of package-a or package-b relax constraints
  2. Contact package authors to update dependencies
  3. Install packages in separate projects
  4. Use package aliases (advanced, see docs)
```

### Resolution Strategies

#### Strategy 1: Update Packages

Check if newer versions are compatible:

```bash
# See if package-a has a newer version that supports shared-lib ^2.0.0
aam info package-a

# Try installing the latest
aam install package-a@latest
```

#### Strategy 2: Relax Constraints (Package Author)

If you control one of the packages, update its `aam.yaml`:

```yaml
# package-a/aam.yaml
dependencies:
  shared-lib: ">=1.0.0"  # More permissive - allows 1.x and 2.x
```

#### Strategy 3: Separate Projects

Install conflicting packages in different projects:

```
project-a/
  .aam/
    packages/package-a/
    packages/shared-lib@1.x/

project-b/
  .aam/
    packages/package-b/
    packages/shared-lib@2.x/
```

---

## Step 7: Dependency Constraint Best Practices

### 1. Use Caret (^) for Most Dependencies

```yaml
dependencies:
  common-tool: "^2.0.0"  # Accept minor updates, avoid breaking changes
```

**Why:** Balances stability and getting updates.

### 2. Use Tilde (~) for Critical Stability

```yaml
dependencies:
  production-db: "~3.1.0"  # Only accept patch updates
```

**Why:** Minimize risk in critical dependencies.

### 3. Use >= for Feature Requirements

```yaml
dependencies:
  modern-lib: ">=4.2.0"  # Requires features introduced in 4.2.0
```

**Why:** Clearly documents minimum version requirement.

### 4. Avoid Wildcards in Production

```yaml
# DON'T DO THIS in production packages
dependencies:
  unstable-tool: "*"

# DO THIS instead
dependencies:
  stable-tool: "^1.0.0"
```

**Why:** Wildcard dependencies are unpredictable.

### 5. Pin Exact Versions for Reproducibility (Advanced)

```yaml
dependencies:
  locked-tool: "1.2.3"  # Exact version
```

**Why:** Maximum reproducibility, but you miss bug fixes.

**Better approach:** Use lock files with `^` constraints.

---

## Step 8: Checking Dependency Information

### View Installed Packages

```bash
aam list
```

```
Installed packages:
  @myorg/code-analyzer          1.0.0  4 artifacts
  linting-rules                 1.4.1  2 artifacts
  @vendor/security-checker      2.2.0  3 artifacts
  common-prompts                1.5.4  5 artifacts
  vulnerability-db              3.3.0  1 artifact
```

### View Package Details

```bash
aam info @myorg/code-analyzer
```

```
@myorg/code-analyzer@1.0.0
  Description: Comprehensive code analysis toolkit
  Author:      your-username
  License:     MIT
  Repository:  https://github.com/your-username/code-analyzer

  Artifacts:
    skill: code-linter        — Lint code for style issues
    agent: analyzer           — AI code analysis agent
    prompt: lint-report       — Lint report template
    instruction: coding-rules — Coding standards

  Dependencies:
    linting-rules (^1.0.0)                → 1.4.1 (installed)
    @vendor/security-checker (^2.0.0)     → 2.2.0 (installed)
    common-prompts (~1.5.0)               → 1.5.4 (installed)
```

### Check Dependency Tree

```bash
aam list --tree
```

Shows the full hierarchy.

---

## Real-World Example

Let's create a package with realistic dependencies:

```yaml
# aam.yaml for @myteam/api-toolkit
name: "@myteam/api-toolkit"
version: 2.0.0
description: "REST API development toolkit"
author: myteam
license: Apache-2.0

artifacts:
  # ... artifacts ...

dependencies:
  # Core dependencies - stable versions
  "@industry/rest-standards": "^3.0.0"    # Industry standard patterns
  http-client-skill: "~2.5.0"             # Only patch updates

  # Optional enhancements - flexible versions
  api-docs-generator: ">=1.2.0"           # Minimum version for features
  testing-framework: "^4.0.0"             # Latest major version

  # Exact version for critical tool
  schema-validator: "1.8.3"               # Known stable version
```

Install it:

```bash
aam install @myteam/api-toolkit
```

```
Resolving @myteam/api-toolkit@2.0.0...

Resolving dependencies...
  @industry/rest-standards: ^3.0.0 → 3.2.1
  http-client-skill: ~2.5.0 → 2.5.4
  api-docs-generator: >=1.2.0 → 2.0.3 (latest)
  testing-framework: ^4.0.0 → 4.1.0
  schema-validator: 1.8.3 → 1.8.3 (exact)

Installing 6 packages...
✓ Installed 6 packages
```

View the tree:

```bash
aam list --tree
```

```
@myteam/api-toolkit@2.0.0
├── @industry/rest-standards@3.2.1
│   └── http-specs@5.0.0  (transitive)
├── http-client-skill@2.5.4
├── api-docs-generator@2.0.3
├── testing-framework@4.1.0
│   ├── assertion-library@2.1.0  (transitive)
│   └── mocking-utils@1.3.0  (transitive)
└── schema-validator@1.8.3
```

---

## Summary

You've learned how to:

- **Declare dependencies** with various constraint types
- **Understand version constraints**: `^`, `~`, `>=`, `*`, exact, ranges
- **Work with transitive dependencies** automatically resolved by AAM
- **Use lock files** for reproducible installations
- **Visualize dependency trees** with `aam list --tree`
- **Update dependencies** safely with `aam update`
- **Handle version conflicts** when they arise

**Key Commands:**

```bash
aam install <package>                # Install with dependencies
aam list --tree                      # Visualize dependency tree
aam update                           # Update all dependencies
aam update <package>                 # Update specific package
aam info <package>                   # View dependency information
```

**Version Constraint Quick Reference:**

| Constraint | Meaning | Example | Allows |
|------------|---------|---------|--------|
| `1.2.3` | Exact | `1.2.3` | Only `1.2.3` |
| `^1.2.3` | Compatible | `^1.2.3` | `1.2.3` - `1.99.99` |
| `~1.2.3` | Approximate | `~1.2.3` | `1.2.3` - `1.2.99` |
| `>=1.2.3` | Minimum | `>=1.2.3` | `1.2.3` and above |
| `*` | Any | `*` | Latest available |
| `>=1.0.0,<2.0.0` | Range | `>=1.0.0,<2.0.0` | `1.0.0` - `1.99.99` |

**Best Practices:**

1. Use `^` for most dependencies (balance updates and stability)
2. Use `~` for critical dependencies (patch updates only)
3. Use `>=` when you need specific features
4. Commit lock files to version control
5. Update dependencies intentionally with `aam update`

---

## Next Steps

- **[CLI Reference](../cli-reference/index.md)** - Complete command documentation
- **[Configuration Guide](../configuration/index.md)** - Advanced dependency configuration
- **[Troubleshooting](../troubleshooting/index.md)** - Resolve common dependency issues

You now have complete control over your package dependencies!
