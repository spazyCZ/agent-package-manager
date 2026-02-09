# Tutorial: Packaging Existing Skills

**Difficulty:** Beginner
**Time:** 10 minutes

## What You'll Learn

In this tutorial, you'll learn how to use `aam create-package` to transform an existing project with scattered skills, agents, and instructions into a proper AAM package ready for sharing and installation.

## Prerequisites

- AAM installed (`aam --version` works)
- A project directory with at least one skill, agent, or instruction file
- Basic familiarity with the command line

!!! tip "Don't have an existing project?"
    No problem! We'll create a sample project structure you can use to follow along.

---

## The Scenario

You've been working on a Python project and have organically created several useful artifacts:

- Skills in `.cursor/skills/` for code review and deployment
- Agent configurations in `.cursor/rules/`
- Python coding standards as Cursor rules
- Reusable prompt templates

These artifacts work great in your project, but they're trapped in platform-specific locations. You want to:

1. Package them as a distributable AAM package
2. Share them with your team
3. Reuse them in other projects
4. Version them properly

Let's see how `aam create-package` makes this easy.

---

## Step 1: Set Up the Example Project

First, let's create a sample project structure that mirrors what you might have in a real project:

```bash
# Create project directory
mkdir my-python-toolkit
cd my-python-toolkit

# Create Cursor-style skills
mkdir -p .cursor/skills/code-reviewer
cat > .cursor/skills/code-reviewer/SKILL.md << 'EOF'
---
name: code-reviewer
description: Review Python code for common issues and best practices
---

# Code Reviewer

Review Python code for:

- PEP 8 compliance
- Common anti-patterns
- Type hints
- Documentation quality

## Usage

Ask me to review any Python file or module and I'll provide feedback.
EOF

mkdir -p .cursor/skills/deploy-helper
cat > .cursor/skills/deploy-helper/SKILL.md << 'EOF'
---
name: deploy-helper
description: Assist with deployment tasks and DevOps workflows
---

# Deploy Helper

Help with:

- Docker configuration
- CI/CD pipeline setup
- Environment configuration
- Deployment checklists
EOF

# Create Cursor rules (agent + instruction)
mkdir -p .cursor/rules
cat > .cursor/rules/agent-python-mentor.mdc << 'EOF'
---
description: "Python mentor agent for code reviews"
alwaysApply: true
---

You are a Python expert focused on teaching best practices.
Provide constructive, educational feedback on code.
EOF

cat > .cursor/rules/python-standards.mdc << 'EOF'
---
description: "Python coding standards"
globs: "**/*.py"
alwaysApply: false
---

# Python Standards

- Use type hints for all functions
- Follow PEP 8
- Maximum line length: 100 characters
- Use docstrings for all public functions
EOF

# Create prompts
mkdir -p .cursor/prompts
cat > .cursor/prompts/refactor-template.md << 'EOF'
# Refactoring Request

**File:** {file}
**Function:** {function}

## Current Issues

{issues}

## Desired Outcome

{outcome}

## Constraints

- Maintain backward compatibility
- Add type hints
- Improve readability
EOF

# Create some fake application code
mkdir -p src
cat > src/app.py << 'EOF'
# Your application code here
def main():
    print("Hello, world!")
EOF

echo "✓ Sample project structure created!"
tree -a -I 'src' .
```

You should see output like:

```
.
├── .cursor
│   ├── prompts
│   │   └── refactor-template.md
│   ├── rules
│   │   ├── agent-python-mentor.mdc
│   │   └── python-standards.mdc
│   └── skills
│       ├── code-reviewer
│       │   └── SKILL.md
│       └── deploy-helper
│           └── SKILL.md
└── src
    └── app.py
```

---

## Step 2: Run Auto-Detection

Now let's see what AAM can detect:

```bash
aam create-package
```

You'll see AAM scan your project and find all the artifacts:

```
Scanning for artifacts not managed by AAM...

Found 5 artifacts:

  Skills (2):
    [x] 1. code-reviewer       .cursor/skills/code-reviewer/SKILL.md
    [x] 2. deploy-helper       .cursor/skills/deploy-helper/SKILL.md

  Agents (1):
    [x] 3. python-mentor       .cursor/rules/agent-python-mentor.mdc

  Instructions (1):
    [x] 4. python-standards    .cursor/rules/python-standards.mdc

  Prompts (1):
    [x] 5. refactor-template   .cursor/prompts/refactor-template.md

Toggle selection with [space], confirm with [enter].
Select/deselect all: [a]  |  Invert selection: [i]
```

!!! info "What Gets Detected?"
    AAM automatically detects:

    - **Skills** - Any directory with a `SKILL.md` file
    - **Agents** - Files matching `**/agent.yaml` or `.cursor/rules/agent-*.mdc`
    - **Instructions** - Files in `instructions/`, `.cursor/rules/*.mdc` (non-agent), `CLAUDE.md`, etc.
    - **Prompts** - Markdown files in `prompts/`, `.cursor/prompts/`, `.github/prompts/`

    It excludes `.aam/packages/`, `node_modules/`, `.venv/`, and other common directories.

---

## Step 3: Select Artifacts Interactively

The interactive selector lets you choose which artifacts to include:

- Press **Space** to toggle individual items
- Press **a** to select/deselect all
- Press **i** to invert selection
- Press **Enter** to confirm

For this tutorial, keep all 5 artifacts selected and press **Enter**.

```
Selected 5 artifacts. Continue? [Y/n] y
```

Press **y** or just **Enter** to continue.

---

## Step 4: Fill in Package Metadata

Now AAM will prompt you for package information:

```
Package name [my-python-toolkit]:
```

Press **Enter** to accept the default, or type a custom name like `@myorg/python-toolkit` for a scoped package.

```
Version [1.0.0]:
```

Press **Enter** to accept `1.0.0`.

```
Description:
```

Type a description:

```
Python development toolkit with code review and deployment helpers
```

```
Author [your-username]:
```

Enter your name or username.

```
License [MIT]:
```

Press **Enter** to accept MIT license.

---

## Step 5: Choose Organization Mode

AAM will ask how to organize the files:

```
How should files be organized?
  (c) Copy into AAM package structure [recommended]
  (r) Reference in-place (keep files where they are)
  (m) Move into AAM package structure (destructive)

Your choice [c]:
```

Let's understand each mode:

### Copy Mode (Recommended)

```
Your choice [c]: c
```

This **copies** detected artifacts into the standard AAM structure. Your original files remain untouched, so you can keep using them in their current locations.

**When to use:** Almost always. Safe, non-destructive, and creates a clean package structure.

**Result:**
```
my-python-toolkit/
├── aam.yaml                    # NEW
├── skills/                     # NEW (copied from .cursor/skills/)
│   ├── code-reviewer/
│   └── deploy-helper/
├── agents/                     # NEW (converted from .cursor/rules/)
│   └── python-mentor/
├── instructions/               # NEW (converted from .cursor/rules/)
│   └── python-standards.md
├── prompts/                    # NEW (copied from .cursor/prompts/)
│   └── refactor-template.md
└── .cursor/                    # UNCHANGED
    └── ...
```

### Reference Mode

```
Your choice [c]: r
```

This creates only `aam.yaml` with **path references** to artifacts at their current locations. No files are copied or moved.

**When to use:** When you want to keep using platform-specific paths and don't plan to distribute the package widely.

**Result:**
```yaml
# aam.yaml (reference mode)
artifacts:
  skills:
    - name: code-reviewer
      path: .cursor/skills/code-reviewer/
      description: "..."
  # ... other artifacts reference .cursor/ paths
```

### Move Mode (Destructive)

```
Your choice [c]: m
```

This **moves** files into AAM structure and **deletes** the originals. **Use with caution.**

**When to use:** Only when you're fully committing to AAM and want to clean up legacy platform-specific directories.

For this tutorial, choose **Copy mode** (press `c` or just **Enter**).

---

## Step 6: Review the Created Package

AAM will now create the package:

```
Creating package...
  ✓ Created aam.yaml
  ✓ Copied .cursor/skills/code-reviewer/ → skills/code-reviewer/
  ✓ Copied .cursor/skills/deploy-helper/ → skills/deploy-helper/
  ✓ Converted .cursor/rules/agent-python-mentor.mdc → agents/python-mentor/
  ✓ Converted .cursor/rules/python-standards.mdc → instructions/python-standards.md
  ✓ Copied .cursor/prompts/refactor-template.md → prompts/refactor-template.md

✓ Package created: my-python-toolkit@1.0.0
  5 artifacts (2 skills, 1 agent, 1 instruction, 1 prompt)

Next steps:
  aam validate    — verify the package is well-formed
  aam pack        — build distributable .aam archive
  aam publish     — publish to registry
```

Let's examine what was created:

```bash
# View the package structure
tree -L 2 -I '.cursor|src'

# Output:
# .
# ├── aam.yaml
# ├── agents
# │   └── python-mentor
# ├── instructions
# │   └── python-standards.md
# ├── prompts
# │   └── refactor-template.md
# └── skills
#     ├── code-reviewer
#     └── deploy-helper
```

---

## Step 7: Understand Platform Conversions

Notice that some artifacts were **converted** rather than just copied. Let's look at the conversions:

### Cursor Agent Rule → AAM Agent

The `.mdc` agent rule was converted to an AAM agent structure:

```bash
cat agents/python-mentor/agent.yaml
```

```yaml
name: python-mentor
description: "Python mentor agent for code reviews"
version: 1.0.0
system_prompt: system-prompt.md
```

```bash
cat agents/python-mentor/system-prompt.md
```

```markdown
You are a Python expert focused on teaching best practices.
Provide constructive, educational feedback on code.
```

### Cursor Instruction Rule → AAM Instruction

The `.mdc` instruction was converted to standard markdown with frontmatter:

```bash
cat instructions/python-standards.md
```

```yaml
---
name: python-standards
description: "Python coding standards"
scope: project
globs: "**/*.py"
---

# Python Standards

- Use type hints for all functions
- Follow PEP 8
- Maximum line length: 100 characters
- Use docstrings for all public functions
```

!!! success "Why Convert?"
    AAM uses platform-neutral formats so your package can deploy to **any** platform (Cursor, Claude, Copilot, Codex). The adapters will convert back to platform-specific formats during deployment.

---

## Step 8: Inspect the Manifest

The `aam.yaml` file is the heart of your package:

```bash
cat aam.yaml
```

```yaml
name: my-python-toolkit
version: 1.0.0
description: Python development toolkit with code review and deployment helpers
author: your-username
license: MIT

artifacts:
  skills:
    - name: code-reviewer
      path: skills/code-reviewer/
      description: Review Python code for common issues and best practices
    - name: deploy-helper
      path: skills/deploy-helper/
      description: Assist with deployment tasks and DevOps workflows

  agents:
    - name: python-mentor
      path: agents/python-mentor/
      description: Python mentor agent for code reviews

  prompts:
    - name: refactor-template
      path: prompts/refactor-template.md
      description: Template for refactoring requests

  instructions:
    - name: python-standards
      path: instructions/python-standards.md
      description: Python coding standards

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

## Step 9: Validate the Package

Before publishing, always validate:

```bash
aam validate
```

Expected output:

```
Validating package: my-python-toolkit@1.0.0

✓ Manifest is valid
✓ All artifact paths exist
✓ Skills are well-formed (2/2)
✓ Agents are well-formed (1/1)
✓ Prompts are well-formed (1/1)
✓ Instructions are well-formed (1/1)
✓ No dependency conflicts

Package is ready for publishing!
```

If there are any issues, AAM will tell you exactly what needs fixing.

---

## Step 10: Build the Package

Create a distributable archive:

```bash
aam pack
```

```
Building package: my-python-toolkit@1.0.0

✓ Validated manifest
✓ Copied artifacts
✓ Generated checksums
✓ Created archive: dist/my-python-toolkit-1.0.0.aam (12.3 KB)

Archive contents:
  - aam.yaml
  - 2 skills
  - 1 agent
  - 1 prompt
  - 1 instruction
```

The `.aam` file is a gzipped tarball that can be:

- Published to a registry
- Shared directly with teammates (via Slack, email, etc.)
- Installed with `aam install ./dist/my-python-toolkit-1.0.0.aam`

---

## Step 11: Test Installation (Optional)

Let's test installing the package in another directory:

```bash
# Create a test project
cd ..
mkdir test-install
cd test-install

# Install the package
aam install ../my-python-toolkit/dist/my-python-toolkit-1.0.0.aam

# Verify installation
aam list
```

Expected output:

```
Installed packages:
  my-python-toolkit  1.0.0  5 artifacts (2 skills, 1 agent, 1 prompt, 1 instruction)
```

Check that artifacts were deployed:

```bash
# Skills deployed to .cursor/skills/
ls -la .aam/packages/my-python-toolkit/skills/

# Agent deployed to .cursor/rules/
ls -la .cursor/rules/

# You should see: agent-python-mentor.mdc
```

---

## Alternative: Non-Interactive Mode

For scripting or CI/CD, skip the interactive prompts:

```bash
cd my-python-toolkit

aam create-package \
  --all \
  --name my-python-toolkit \
  --version 1.0.0 \
  --description "Python toolkit" \
  --author "your-username" \
  --organize copy \
  --yes
```

This selects all detected artifacts and uses the provided metadata without prompting.

---

## Alternative: Dry Run Preview

Want to see what would happen without creating any files?

```bash
aam create-package --dry-run
```

```
Scanning for artifacts not managed by AAM...

Found 5 artifacts:
  skill:       code-reviewer       .cursor/skills/code-reviewer/SKILL.md
  skill:       deploy-helper       .cursor/skills/deploy-helper/SKILL.md
  agent:       python-mentor       .cursor/rules/agent-python-mentor.mdc
  instruction: python-standards    .cursor/rules/python-standards.mdc
  prompt:      refactor-template   .cursor/prompts/refactor-template.md

Would create:
  aam.yaml
  skills/code-reviewer/  (copy from .cursor/skills/code-reviewer/)
  skills/deploy-helper/  (copy from .cursor/skills/deploy-helper/)
  agents/python-mentor/  (convert from .cursor/rules/agent-python-mentor.mdc)
  instructions/python-standards.md  (convert from .cursor/rules/python-standards.mdc)
  prompts/refactor-template.md  (copy from .cursor/prompts/refactor-template.md)

[Dry run — no files written]
```

---

## Next Steps

Congratulations! You've learned how to package existing project artifacts with AAM.

Now you can:

- **Share with your team** - Follow the [Sharing with Your Team](share-with-team.md) tutorial
- **Add dependencies** - Learn about dependencies in [Working with Dependencies](working-with-dependencies.md)
- **Build from scratch** - Create a complete package in [Building a Code Review Package](build-code-review-package.md)
- **Deploy multi-platform** - Configure deployment in [Multi-Platform Deployment](multi-platform-deployment.md)

---

## Troubleshooting

### No artifacts detected

**Problem:** AAM says "Found 0 artifacts"

**Solutions:**

- Check that files match expected patterns (e.g., `SKILL.md` for skills)
- Ensure you're in the project root directory
- Use `--include` to manually add files:
  ```bash
  aam create-package --include ./my-skill/ --include-as skill
  ```

### Files in wrong locations after copy

**Problem:** Artifacts weren't organized as expected

**Solution:**

- Delete the created files and re-run with different organization mode
- Manually edit `aam.yaml` to adjust paths if needed

### Package validation fails

**Problem:** `aam validate` shows errors

**Solution:**

- Read the error messages - they tell you exactly what's wrong
- Common issues:
    - Missing required frontmatter fields in SKILL.md
    - Invalid YAML syntax in agent.yaml
    - Path references to non-existent files

---

## Summary

In this tutorial, you learned:

- How to use `aam create-package` to detect existing artifacts
- The difference between Copy, Reference, and Move organization modes
- How AAM converts platform-specific formats to neutral formats
- How to validate and package artifacts for distribution

**Key Commands:**

```bash
aam create-package              # Interactive package creation
aam create-package --dry-run    # Preview without creating files
aam validate                    # Verify package structure
aam pack                        # Build distributable archive
```

Ready for more? Try the [Building a Code Review Package](build-code-review-package.md) tutorial to build a complete package from scratch!
