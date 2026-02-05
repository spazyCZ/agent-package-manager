# AAM User Guide

**Version:** 0.1.0  
**Date:** 2026-02-05

This guide walks you through creating, publishing, and installing AAM packages with practical examples.

---

## Table of Contents

1. [Quick Start](#1-quick-start)
2. [Creating a Package](#2-creating-a-package)
3. [Publishing a Package](#3-publishing-a-package)
4. [Installing a Package](#4-installing-a-package)
5. [Adding Dependencies](#5-adding-dependencies)
6. [Complete Example: Building a Code Review Package](#6-complete-example-building-a-code-review-package)

---

## 1. Quick Start

### Prerequisites

```bash
# Install AAM
pip install aam

# Verify installation
aam --version
# aam 0.1.0

# Configure default platform
aam config set default_platform cursor
```

### TL;DR Commands

```bash
# Create a new package
aam init my-package

# Validate before publishing
aam validate

# Build and publish
aam pack
aam publish

# Install a package
aam install my-package
```

---

## 2. Creating a Package

### 2.1 Initialize a New Package

Use `aam init` to create a new package interactively:

```bash
$ mkdir python-best-practices && cd python-best-practices
$ aam init

Package name [python-best-practices]: 
Version [1.0.0]: 
Description: Python coding standards and best practices for AI agents
Author: your-username
License [MIT]: 

What artifacts will this package contain?
  [x] Skills
  [x] Agents
  [x] Prompts
  [x] Instructions

Which platforms should this package support?
  [x] Cursor
  [x] Claude
  [x] GitHub Copilot
  [ ] Codex

Created python-best-practices/
  ├── aam.yaml
  ├── agents/
  ├── skills/
  ├── prompts/
  └── instructions/
```

### 2.2 Package Structure

After initialization, your package looks like this:

```
python-best-practices/
├── aam.yaml                    # Package manifest (required)
├── agents/                     # Agent definitions
├── skills/                     # Skill definitions
├── prompts/                    # Prompt templates
└── instructions/               # Platform instructions/rules
```

### 2.3 The Manifest: `aam.yaml`

The generated `aam.yaml` is the heart of your package:

```yaml
# aam.yaml
name: python-best-practices
version: 1.0.0
description: "Python coding standards and best practices for AI agents"
author: your-username
license: MIT
repository: https://github.com/your-username/python-best-practices

# Declare what this package provides
artifacts:
  skills: []
  agents: []
  prompts: []
  instructions: []

# Dependencies on other AAM packages
dependencies: {}

# Platform-specific configuration
platforms:
  cursor:
    skill_scope: project
  claude:
    merge_instructions: true
  copilot:
    merge_instructions: true
```

### 2.4 Adding Artifacts

#### Add a Skill

Create `skills/python-reviewer/SKILL.md`:

```bash
mkdir -p skills/python-reviewer
```

```markdown
---
name: python-reviewer
description: Review Python code for best practices, PEP 8 compliance, and common issues. Use when asked to review Python files or suggest improvements.
---

# Python Code Reviewer

## When to Use
- User asks to review Python code
- User asks about Python best practices
- User wants to improve code quality

## Review Checklist

1. **PEP 8 Compliance**
   - Line length (max 88 for Black, 79 for strict PEP 8)
   - Naming conventions (snake_case for functions/variables, PascalCase for classes)
   - Import ordering (standard library, third-party, local)

2. **Type Hints**
   - Function parameters and return types
   - Variable annotations where helpful
   - Use `typing` module for complex types

3. **Documentation**
   - Module docstrings
   - Function/method docstrings (Google or NumPy style)
   - Inline comments for complex logic

4. **Error Handling**
   - Specific exception types (not bare `except:`)
   - Context managers for resources
   - Proper error messages

5. **Performance**
   - List comprehensions over loops where appropriate
   - Generator expressions for large datasets
   - Avoid premature optimization

## Output Format

When reviewing code, structure feedback as:

```markdown
## Code Review: [filename]

### Summary
[1-2 sentence overview]

### Issues Found

#### Critical
- [issue with line reference]

#### Suggestions
- [improvement with example]

### Positive Aspects
- [what's done well]
```
```

Update `aam.yaml` to include the skill:

```yaml
artifacts:
  skills:
    - name: python-reviewer
      path: skills/python-reviewer/
      description: "Review Python code for best practices and PEP 8 compliance"
```

#### Add a Prompt

Create `prompts/refactor-function.md`:

```markdown
---
name: refactor-function
description: "Prompt template for refactoring a Python function"
variables:
  - name: function_code
    description: "The function code to refactor"
    required: true
  - name: focus_area
    description: "Specific area to focus on"
    required: false
    enum: [readability, performance, testability, all]
    default: all
---

# Refactor Python Function

Refactor the following Python function with focus on: **{{focus_area}}**

```python
{{function_code}}
```

## Requirements

1. Maintain the same functionality and API
2. Add or improve type hints
3. Add docstring if missing
4. Apply PEP 8 conventions
5. Suggest unit tests if applicable

## Output

Provide:
1. The refactored code
2. Explanation of changes made
3. Any trade-offs or considerations
```

Update `aam.yaml`:

```yaml
artifacts:
  skills:
    - name: python-reviewer
      path: skills/python-reviewer/
      description: "Review Python code for best practices and PEP 8 compliance"
  
  prompts:
    - name: refactor-function
      path: prompts/refactor-function.md
      description: "Template for refactoring Python functions"
```

#### Add an Instruction

Create `instructions/python-standards.md`:

```markdown
---
name: python-standards
description: "Python coding standards for this project"
scope: project
globs: "**/*.py"
---

# Python Coding Standards

When working with Python files in this project, follow these standards:

## Style
- Use Black formatter with default settings (line length 88)
- Sort imports with isort (Black-compatible profile)
- Use double quotes for strings

## Type Hints
- All public functions must have type hints
- Use `from __future__ import annotations` for forward references
- Prefer `list[str]` over `List[str]` (Python 3.9+)

## Testing
- Use pytest for all tests
- Minimum 80% code coverage for new code
- Name test files `test_*.py`
- Name test functions `test_*`

## Documentation
- Use Google-style docstrings
- All public modules, classes, and functions need docstrings

## Error Handling
- Never use bare `except:`
- Create custom exceptions in `exceptions.py`
- Log errors before re-raising
```

Update `aam.yaml`:

```yaml
artifacts:
  skills:
    - name: python-reviewer
      path: skills/python-reviewer/
      description: "Review Python code for best practices and PEP 8 compliance"
  
  prompts:
    - name: refactor-function
      path: prompts/refactor-function.md
      description: "Template for refactoring Python functions"
  
  instructions:
    - name: python-standards
      path: instructions/python-standards.md
      description: "Python coding standards for projects"
```

#### Add an Agent

Create agent directory and files:

```bash
mkdir -p agents/python-mentor
```

Create `agents/python-mentor/agent.yaml`:

```yaml
name: python-mentor
description: "A Python mentor agent that helps write better Python code"
version: 1.0.0

system_prompt: system-prompt.md

# Skills this agent uses
skills:
  - python-reviewer

# Prompts this agent uses  
prompts:
  - refactor-function

# Tools the agent can access
tools:
  - file_read
  - file_write
  - shell

# Behavioral parameters
parameters:
  temperature: 0.3
  style: educational
  verbosity: detailed
```

Create `agents/python-mentor/system-prompt.md`:

```markdown
You are a Python Mentor — an expert Python developer focused on teaching and improving code quality.

## Your Role

- Help users write better Python code
- Explain concepts clearly with examples
- Review code constructively, highlighting both issues and strengths
- Suggest improvements with explanations of why they're better

## Your Approach

1. **Be Educational**: Don't just fix code, explain why changes improve it
2. **Be Encouraging**: Acknowledge what's done well before suggesting improvements
3. **Be Practical**: Focus on changes that provide real value
4. **Be Current**: Use modern Python (3.10+) features and idioms

## When Reviewing Code

Use the python-reviewer skill to systematically check:
- PEP 8 compliance
- Type hints
- Documentation
- Error handling
- Performance

## When Refactoring

Use the refactor-function prompt template to ensure consistent, thorough refactoring.

## Communication Style

- Use clear, jargon-free explanations
- Provide code examples for every suggestion
- Reference official Python documentation when relevant
- Offer multiple solutions when trade-offs exist
```

Update final `aam.yaml`:

```yaml
# aam.yaml - Complete package manifest
name: python-best-practices
version: 1.0.0
description: "Python coding standards and best practices for AI agents"
author: your-username
license: MIT
repository: https://github.com/your-username/python-best-practices

artifacts:
  agents:
    - name: python-mentor
      path: agents/python-mentor/
      description: "Python mentor agent for code review and improvement"

  skills:
    - name: python-reviewer
      path: skills/python-reviewer/
      description: "Review Python code for best practices and PEP 8 compliance"

  prompts:
    - name: refactor-function
      path: prompts/refactor-function.md
      description: "Template for refactoring Python functions"

  instructions:
    - name: python-standards
      path: instructions/python-standards.md
      description: "Python coding standards for projects"

dependencies: {}

platforms:
  cursor:
    skill_scope: project
    deploy_instructions_as: rules
  claude:
    merge_instructions: true
  copilot:
    merge_instructions: true

keywords:
  - python
  - code-review
  - best-practices
  - pep8
  - mentor
```

### 2.5 Validate Your Package

Before publishing, validate your package:

```bash
$ aam validate

Validating python-best-practices@1.0.0...

Manifest:
  ✓ name: valid format
  ✓ version: valid semver
  ✓ description: present
  ✓ author: present

Artifacts:
  ✓ agent: python-mentor
    ✓ agent.yaml exists and valid
    ✓ system-prompt.md exists
  ✓ skill: python-reviewer
    ✓ SKILL.md exists and valid
  ✓ prompt: refactor-function
    ✓ prompts/refactor-function.md exists and valid
  ✓ instruction: python-standards
    ✓ instructions/python-standards.md exists and valid

Dependencies:
  ✓ No dependencies declared

✓ Package is valid and ready to publish
```

---

## 3. Publishing a Package

### 3.1 Create a Registry Account

First, register on the AAM registry:

```bash
$ aam register

Username: your-username
Email: you@example.com
Password: ********
Confirm password: ********

✓ Account created successfully
✓ Verification email sent to you@example.com

Please verify your email, then run `aam login` to authenticate.
```

### 3.2 Login and Get API Token

```bash
$ aam login

Email or username: your-username
Password: ********

✓ Logged in as your-username
✓ API token saved to ~/.aam/credentials.yaml

Token scopes: publish, yank
Token expires: never (revoke with `aam logout`)
```

### 3.3 Build the Package Archive

```bash
$ aam pack

Building python-best-practices@1.0.0...
  Adding aam.yaml
  Adding agents/python-mentor/agent.yaml
  Adding agents/python-mentor/system-prompt.md
  Adding skills/python-reviewer/SKILL.md
  Adding prompts/refactor-function.md
  Adding instructions/python-standards.md

✓ Built python-best-practices-1.0.0.aam (4.2 KB)
  Checksum: sha256:a1b2c3d4e5f6...
```

### 3.4 Publish to Registry

#### Basic Publish (No Signature)

```bash
$ aam publish

Publishing python-best-practices@1.0.0...

Uploading python-best-practices-1.0.0.aam...
  ████████████████████████████████ 100%

✓ Published python-best-practices@1.0.0
  URL: https://registry.aam.dev/packages/python-best-practices
  
⚠ Package is unsigned. Consider signing with --sign for better security.
```

#### Publish with Sigstore Signature (Recommended)

```bash
$ aam publish --sign

Publishing python-best-practices@1.0.0...

Signing package with Sigstore...
  🔐 Opening browser for authentication...
  ✓ Authenticated as your-username@github
  ✓ Package signed
  ✓ Recorded in Rekor transparency log

Uploading python-best-practices-1.0.0.aam...
  ████████████████████████████████ 100%

✓ Published python-best-practices@1.0.0
  URL: https://registry.aam.dev/packages/python-best-practices
  Signed by: your-username@github
  Transparency log: https://rekor.sigstore.dev/api/v1/log/entries/...
```

#### Publish with GPG Signature

```bash
$ aam publish --sign --sign-type gpg --key-id ABC123DEF456

Publishing python-best-practices@1.0.0...

Signing package with GPG key ABC123DEF456...
  ✓ Package signed

Uploading python-best-practices-1.0.0.aam...
  ████████████████████████████████ 100%

✓ Published python-best-practices@1.0.0
  URL: https://registry.aam.dev/packages/python-best-practices
  Signed by: ABC123DEF456
```

### 3.5 Publish a New Version

Update `version` in `aam.yaml`:

```yaml
version: 1.1.0
```

Then publish:

```bash
$ aam validate && aam pack && aam publish --sign

✓ Package is valid
✓ Built python-best-practices-1.1.0.aam (4.5 KB)
✓ Published python-best-practices@1.1.0
```

### 3.6 Yank a Bad Version

If you publish a version with issues, yank it (marks as "do not install" but doesn't delete):

```bash
$ aam yank python-best-practices@1.0.0 --reason "Security issue in prompt template"

⚠ This will mark python-best-practices@1.0.0 as yanked.
  Existing installations will continue to work.
  New installations will skip this version.

Proceed? [y/N] y

✓ Yanked python-best-practices@1.0.0
```

---

## 4. Installing a Package

### 4.1 Basic Installation

```bash
$ cd my-project/
$ aam install python-best-practices

Resolving python-best-practices@1.1.0...
  + python-best-practices@1.1.0

Downloading 1 package...
  ✓ python-best-practices@1.1.0 (4.5 KB)

Verification:
  ✓ Checksum: sha256:a1b2c3d4... matches
  ✓ Signature: Sigstore (your-username@github)

Deploying to cursor...
  → agent: python-mentor       → .cursor/rules/agent-python-mentor.mdc
  → skill: python-reviewer     → .cursor/skills/python-reviewer/
  → prompt: refactor-function  → .cursor/prompts/refactor-function.md
  → instruction: python-standards → .cursor/rules/python-standards.mdc

✓ Installed 1 package (1 agent, 1 skill, 1 prompt, 1 instruction)
```

### 4.2 Install Specific Version

```bash
$ aam install python-best-practices@1.0.0

Resolving python-best-practices@1.0.0...
  + python-best-practices@1.0.0

...
```

### 4.3 Install to Specific Platform

```bash
# Install only to Claude
$ aam install python-best-practices --platform claude

Deploying to claude...
  → skill: python-reviewer     → .claude/skills/python-reviewer/
  → instruction: python-standards → CLAUDE.md (section added)

✓ Installed 1 package
```

### 4.4 Install from Different Sources

```bash
# From registry (default)
aam install python-best-practices

# From git repository
aam install git+https://github.com/user/python-best-practices.git

# From local directory
aam install ./my-local-package/

# From .aam archive file
aam install python-best-practices-1.0.0.aam
```

### 4.5 Install Without Deploying

Download and resolve dependencies without deploying artifacts:

```bash
$ aam install python-best-practices --no-deploy

Resolving python-best-practices@1.1.0...
  + python-best-practices@1.1.0

✓ Downloaded to .aam/packages/python-best-practices/

To deploy later, run: aam deploy
```

### 4.6 View Installed Packages

```bash
$ aam list

Installed packages:
  python-best-practices  1.1.0  4 artifacts (1 agent, 1 skill, 1 prompt, 1 instruction)

$ aam list --tree

python-best-practices@1.1.0
  (no dependencies)

$ aam info python-best-practices

python-best-practices@1.1.0
  Description: Python coding standards and best practices for AI agents
  Author:      your-username
  License:     MIT
  Repository:  https://github.com/your-username/python-best-practices

  Artifacts:
    agent: python-mentor         — Python mentor agent for code review
    skill: python-reviewer       — Review Python code for best practices
    prompt: refactor-function    — Template for refactoring functions
    instruction: python-standards — Python coding standards

  Dependencies: none

  Deployed to:
    cursor: .cursor/skills/, .cursor/rules/, .cursor/prompts/
```

### 4.7 Uninstall a Package

```bash
$ aam uninstall python-best-practices

Uninstalling python-best-practices@1.1.0...

Removing deployed artifacts from cursor...
  ✓ Removed .cursor/rules/agent-python-mentor.mdc
  ✓ Removed .cursor/skills/python-reviewer/
  ✓ Removed .cursor/prompts/refactor-function.md
  ✓ Removed .cursor/rules/python-standards.mdc

✓ Uninstalled python-best-practices
```

---

## 5. Adding Dependencies

### 5.1 Declare Dependencies

Suppose you want your package to depend on a `code-analysis` package. Add it to `aam.yaml`:

```yaml
name: python-best-practices
version: 1.2.0
description: "Python coding standards and best practices for AI agents"
author: your-username
license: MIT

artifacts:
  # ... your artifacts ...

dependencies:
  # Exact version
  code-analysis: "1.0.0"
  
  # Minimum version
  common-prompts: ">=2.0.0"
  
  # Compatible version (>=1.0.0, <2.0.0)
  linting-rules: "^1.0.0"
  
  # Approximate version (>=1.0.0, <1.1.0)
  formatting-utils: "~1.0.0"
  
  # Any version
  utilities: "*"
```

### 5.2 Version Constraint Syntax

| Syntax | Meaning | Example |
|--------|---------|---------|
| `1.0.0` | Exact version | Only 1.0.0 |
| `>=1.0.0` | Minimum version | 1.0.0 or higher |
| `^1.0.0` | Compatible | >=1.0.0, <2.0.0 |
| `~1.0.0` | Approximate | >=1.0.0, <1.1.0 |
| `*` | Any version | Latest available |
| `>=1.0.0,<2.0.0` | Range | Between 1.0.0 and 2.0.0 |

### 5.3 Reference Dependency Artifacts

Your artifacts can reference artifacts from dependencies.

**In an agent (`agents/python-mentor/agent.yaml`):**

```yaml
name: python-mentor
description: "Python mentor with enhanced analysis"
system_prompt: system-prompt.md

skills:
  - python-reviewer           # From this package
  - code-analyzer             # From code-analysis dependency
  - complexity-checker        # From code-analysis dependency

prompts:
  - refactor-function         # From this package
  - explain-code              # From common-prompts dependency
```

**In a skill (`skills/python-reviewer/SKILL.md`):**

```markdown
---
name: python-reviewer
description: Review Python code using analysis tools from dependencies
---

# Python Code Reviewer

## Dependencies

This skill uses:
- `code-analyzer` skill from `code-analysis` package for static analysis
- `complexity-checker` skill from `code-analysis` package for complexity metrics

## Workflow

1. Run code-analyzer to identify issues
2. Run complexity-checker for metrics
3. Compile findings into structured review
```

### 5.4 Install Package with Dependencies

When users install your package, dependencies are resolved automatically:

```bash
$ aam install python-best-practices

Resolving python-best-practices@1.2.0...
  + python-best-practices@1.2.0
  + code-analysis@1.0.0 (dependency)
  + common-prompts@2.1.0 (dependency)
  + linting-rules@1.3.0 (dependency)
  + formatting-utils@1.0.2 (dependency)
  + utilities@3.0.0 (dependency)

Downloading 6 packages...
  ✓ python-best-practices@1.2.0 (4.5 KB)
  ✓ code-analysis@1.0.0 (12.3 KB)
  ✓ common-prompts@2.1.0 (3.1 KB)
  ✓ linting-rules@1.3.0 (2.8 KB)
  ✓ formatting-utils@1.0.2 (1.5 KB)
  ✓ utilities@3.0.0 (2.2 KB)

Deploying to cursor...
  → skill: python-reviewer     → .cursor/skills/python-reviewer/
  → skill: code-analyzer       → .cursor/skills/code-analyzer/
  → skill: complexity-checker  → .cursor/skills/complexity-checker/
  ... (all artifacts deployed)

✓ Installed 6 packages (2 agents, 5 skills, 8 prompts, 3 instructions)
```

### 5.5 View Dependency Tree

```bash
$ aam list --tree

python-best-practices@1.2.0
├── code-analysis@1.0.0
├── common-prompts@2.1.0
├── linting-rules@1.3.0
│   └── utilities@3.0.0
└── formatting-utils@1.0.2
```

### 5.6 Lock File

After installation, AAM creates `.aam/aam-lock.yaml` for reproducible installs:

```yaml
# .aam/aam-lock.yaml — DO NOT EDIT MANUALLY
lockfile_version: 1
resolved_at: "2026-02-05T14:30:00Z"

packages:
  python-best-practices:
    version: 1.2.0
    source: aam-central
    checksum: sha256:a1b2c3d4...
    dependencies:
      code-analysis: 1.0.0
      common-prompts: 2.1.0
      linting-rules: 1.3.0
      formatting-utils: 1.0.2
      utilities: 3.0.0

  code-analysis:
    version: 1.0.0
    source: aam-central
    checksum: sha256:e5f6g7h8...
    dependencies: {}

  common-prompts:
    version: 2.1.0
    source: aam-central
    checksum: sha256:i9j0k1l2...
    dependencies: {}

  linting-rules:
    version: 1.3.0
    source: aam-central
    checksum: sha256:m3n4o5p6...
    dependencies:
      utilities: 3.0.0

  formatting-utils:
    version: 1.0.2
    source: aam-central
    checksum: sha256:q7r8s9t0...
    dependencies: {}

  utilities:
    version: 3.0.0
    source: aam-central
    checksum: sha256:u1v2w3x4...
    dependencies: {}
```

**Commit this file to git** for reproducible installs across your team.

### 5.7 Update Dependencies

```bash
# Update all packages to latest compatible versions
$ aam update

Resolving updates...
  python-best-practices: 1.2.0 (unchanged)
  code-analysis: 1.0.0 → 1.0.1 (patch update)
  common-prompts: 2.1.0 → 2.2.0 (minor update)

Update 2 packages? [Y/n] y

✓ Updated 2 packages

# Update a specific package
$ aam update code-analysis
```

---

## 6. Complete Example: Building a Code Review Package

Let's build a complete package from scratch: a code review toolkit.

### Step 1: Initialize

```bash
mkdir code-review-toolkit && cd code-review-toolkit
aam init
```

Fill in:
- Name: `code-review-toolkit`
- Version: `1.0.0`
- Description: "Comprehensive code review toolkit for multiple languages"
- Author: your-username

### Step 2: Create Directory Structure

```bash
mkdir -p skills/security-scan skills/performance-check
mkdir -p agents/security-reviewer
mkdir -p prompts
mkdir -p instructions
```

### Step 3: Create Skill - Security Scan

`skills/security-scan/SKILL.md`:

```markdown
---
name: security-scan
description: Scan code for common security vulnerabilities. Use when reviewing code for security issues or when asked about secure coding practices.
---

# Security Scanner

## Checks Performed

### Input Validation
- SQL injection patterns
- Command injection patterns
- Path traversal vulnerabilities
- XSS vulnerabilities

### Authentication & Authorization
- Hardcoded credentials
- Weak password patterns
- Missing authentication checks
- Improper session handling

### Data Exposure
- Sensitive data in logs
- Unencrypted sensitive data
- Exposed API keys or secrets

### Dependencies
- Known vulnerable packages
- Outdated dependencies

## Usage

When asked to review security:
1. Identify the language/framework
2. Apply relevant checks from above
3. Rate severity: Critical / High / Medium / Low
4. Provide remediation guidance

## Output Format

```markdown
## Security Review: [file/component]

### Critical Issues
- [issue]: [location] - [remediation]

### High Priority
- [issue]: [location] - [remediation]

### Medium Priority
- [issue]: [location] - [remediation]

### Recommendations
- [general security improvements]
```
```

### Step 4: Create Skill - Performance Check

`skills/performance-check/SKILL.md`:

```markdown
---
name: performance-check
description: Analyze code for performance issues and optimization opportunities. Use when asked about performance, optimization, or efficiency.
---

# Performance Analyzer

## Analysis Areas

### Algorithmic Complexity
- Identify O(n²) or worse operations
- Suggest more efficient algorithms
- Flag unnecessary iterations

### Memory Usage
- Large object allocations
- Memory leaks potential
- Inefficient data structures

### I/O Operations
- Unbatched database queries (N+1)
- Synchronous blocking operations
- Missing caching opportunities

### Language-Specific
- Python: List vs generator, string concatenation
- JavaScript: DOM manipulation, event handlers
- SQL: Missing indexes, inefficient joins

## Output Format

```markdown
## Performance Review: [file/component]

### Issues Found
| Location | Issue | Impact | Suggestion |
|----------|-------|--------|------------|
| line X   | ...   | High   | ...        |

### Optimization Opportunities
- [opportunity with expected improvement]

### Metrics
- Estimated complexity: O(...)
- Potential improvement: X%
```
```

### Step 5: Create Agent - Security Reviewer

`agents/security-reviewer/agent.yaml`:

```yaml
name: security-reviewer
description: "Security-focused code reviewer that identifies vulnerabilities"
version: 1.0.0

system_prompt: system-prompt.md

skills:
  - security-scan

prompts:
  - security-report

tools:
  - file_read
  - grep
  - shell

parameters:
  temperature: 0.2
  style: thorough
  output_format: structured
```

`agents/security-reviewer/system-prompt.md`:

```markdown
You are a Security Code Reviewer — an expert in application security focused on identifying vulnerabilities in code.

## Your Mission

Find security issues before they become incidents. You are thorough, precise, and always explain the "why" behind vulnerabilities.

## Review Process

1. **Understand Context**: What does this code do? What data does it handle?
2. **Threat Model**: Who might attack this? What would they try?
3. **Systematic Scan**: Use security-scan skill for comprehensive checks
4. **Prioritize**: Rate by severity and exploitability
5. **Remediate**: Provide specific, actionable fixes

## Severity Ratings

- **Critical**: Immediate exploitation possible, high impact
- **High**: Exploitation likely, significant impact
- **Medium**: Exploitation requires conditions, moderate impact
- **Low**: Minimal impact or unlikely exploitation

## Communication Style

- Be direct about issues — security requires clarity
- Always explain why something is a vulnerability
- Provide working code fixes, not just descriptions
- Reference OWASP, CWE, or CVE when applicable
```

### Step 6: Create Prompts

`prompts/security-report.md`:

```markdown
---
name: security-report
description: "Generate a structured security assessment report"
variables:
  - name: target
    description: "What is being reviewed (file, component, system)"
    required: true
  - name: scope
    description: "Scope of review"
    required: false
    default: "full"
    enum: [full, critical-only, quick-scan]
---

# Security Assessment: {{target}}

## Scope: {{scope}}

Perform a security review of the specified target and generate a report.

## Required Sections

1. **Executive Summary**
   - Overall risk rating (Critical/High/Medium/Low)
   - Key findings count by severity
   - Immediate actions required

2. **Findings Detail**
   For each finding:
   - ID (SEC-001, SEC-002, etc.)
   - Title
   - Severity
   - Location (file:line)
   - Description
   - Proof of Concept (if safe)
   - Remediation
   - References (CWE, OWASP)

3. **Recommendations**
   - Prioritized action items
   - Security improvements

4. **Appendix**
   - Tools/methods used
   - Scope limitations
```

### Step 7: Create Instruction

`instructions/secure-coding.md`:

```markdown
---
name: secure-coding
description: "Secure coding guidelines for all languages"
scope: global
---

# Secure Coding Guidelines

Apply these security practices when writing or reviewing code:

## Input Validation
- Validate all input at system boundaries
- Use allowlists over denylists
- Sanitize output based on context (HTML, SQL, etc.)

## Authentication
- Never store passwords in plain text
- Use established libraries for auth (don't roll your own)
- Implement proper session management

## Secrets Management
- Never commit secrets to version control
- Use environment variables or secret managers
- Rotate credentials regularly

## Error Handling
- Don't expose stack traces to users
- Log security events with context
- Fail securely (deny by default)

## Dependencies
- Keep dependencies updated
- Review security advisories
- Minimize dependency surface
```

### Step 8: Update Manifest

`aam.yaml`:

```yaml
name: code-review-toolkit
version: 1.0.0
description: "Comprehensive code review toolkit for security and performance"
author: your-username
license: MIT
repository: https://github.com/your-username/code-review-toolkit

artifacts:
  agents:
    - name: security-reviewer
      path: agents/security-reviewer/
      description: "Security-focused code reviewer"

  skills:
    - name: security-scan
      path: skills/security-scan/
      description: "Scan code for security vulnerabilities"
    - name: performance-check
      path: skills/performance-check/
      description: "Analyze code for performance issues"

  prompts:
    - name: security-report
      path: prompts/security-report.md
      description: "Generate security assessment reports"

  instructions:
    - name: secure-coding
      path: instructions/secure-coding.md
      description: "Secure coding guidelines"

dependencies: {}

platforms:
  cursor:
    skill_scope: project
    deploy_instructions_as: rules
  claude:
    merge_instructions: true
  copilot:
    merge_instructions: true

keywords:
  - security
  - code-review
  - performance
  - vulnerabilities
  - best-practices
```

### Step 9: Validate, Pack, Publish

```bash
# Validate
$ aam validate
✓ Package is valid and ready to publish

# Pack
$ aam pack
✓ Built code-review-toolkit-1.0.0.aam (8.7 KB)

# Publish with signature
$ aam publish --sign
✓ Published code-review-toolkit@1.0.0
```

### Step 10: Users Install Your Package

```bash
$ aam install code-review-toolkit

Resolving code-review-toolkit@1.0.0...
  + code-review-toolkit@1.0.0

Deploying to cursor...
  → agent: security-reviewer   → .cursor/rules/agent-security-reviewer.mdc
  → skill: security-scan       → .cursor/skills/security-scan/
  → skill: performance-check   → .cursor/skills/performance-check/
  → prompt: security-report    → .cursor/prompts/security-report.md
  → instruction: secure-coding → .cursor/rules/secure-coding.mdc

✓ Installed 1 package (1 agent, 2 skills, 1 prompt, 1 instruction)
```

---

## Summary

| Task | Command |
|------|---------|
| Create package | `aam init` |
| Validate package | `aam validate` |
| Build archive | `aam pack` |
| Publish to registry | `aam publish [--sign]` |
| Install package | `aam install <name>` |
| Install specific version | `aam install <name>@<version>` |
| List installed | `aam list` |
| Show package info | `aam info <name>` |
| Update packages | `aam update` |
| Uninstall package | `aam uninstall <name>` |
| Search registry | `aam search <query>` |

For more details, see:
- [DESIGN.md](./DESIGN.md) — Architecture and concepts
- [HTTP_REGISTRY_SPEC.md](./HTTP_REGISTRY_SPEC.md) — Registry API specification
