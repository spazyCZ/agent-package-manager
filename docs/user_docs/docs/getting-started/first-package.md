# Your First Package

This tutorial walks you through creating a complete AAM package from scratch. You'll build a real-world package containing all four artifact types: skills, agents, prompts, and instructions.

By the end, you'll have a production-ready package that demonstrates AAM's full capabilities.

---

## What You'll Build

**Package:** `@yourname/python-best-practices`

**Contents:**

- 1 **Skill** — `python-reviewer` with scripts and references
- 1 **Agent** — `python-mentor` that uses the skill
- 1 **Prompt** — `refactor-function` template
- 1 **Instruction** — `python-standards` coding guidelines

**Time:** 15-20 minutes

---

## Prerequisites

Before starting, ensure you have:

- AAM installed (`aam --version` works)
- A local registry configured (from [Quick Start](quickstart.md))
- Your default platform set (`aam config set default_platform cursor`)

---

## Step 1: Initialize the Package

Create a new directory and initialize the package:

```bash
mkdir -p ~/python-best-practices && cd ~/python-best-practices
aam pkg init
```

**Interactive prompts:**

```
Package name [python-best-practices]: @yourname/python-best-practices
Version [1.0.0]:
Description: Python coding standards and best practices for AI agents
Author: Your Name
License [MIT]:

What artifacts will this package contain?
  [x] Skills
  [x] Agents
  [x] Prompts
  [x] Instructions

Which platforms should this package support?
  [x] Cursor
  [x] Claude
  [ ] GitHub Copilot
  [ ] Codex
```

**Expected output:**

```
✓ Created @yourname/python-best-practices/
  ├── aam.yaml
  ├── skills/
  ├── agents/
  ├── prompts/
  ├── instructions/
  └── README.md
```

!!! tip "Scoped packages"
    Using `@yourname/` as a scope helps organize packages and prevents naming conflicts. It's like npm's scoped packages or GitHub's username/repo format. To scaffold a package from a template without the interactive wizard, use `aam pkg create` instead of `aam pkg init`.

---

## Step 2: Create the Skill

A skill is the core workflow — it includes instructions, scripts, templates, and references.

### Create Skill Directory Structure

```bash
mkdir -p skills/python-reviewer/{scripts,templates,references}
```

### Create SKILL.md

Create `skills/python-reviewer/SKILL.md`:

```markdown title="skills/python-reviewer/SKILL.md"
---
name: python-reviewer
description: Review Python code for best practices, PEP 8 compliance, and common issues. Use when asked to review Python files or suggest improvements.
---

# Python Code Reviewer

## When to Use

- User asks to review Python code
- User asks about Python best practices
- User wants to improve code quality

## Available Scripts

This skill includes executable scripts:

- `scripts/analyze.py` — Static analysis script that checks for common issues
- `scripts/complexity.py` — Calculate cyclomatic complexity metrics

Run scripts when deeper analysis is needed:

```bash
python skills/python-reviewer/scripts/analyze.py <file.py>
```

## Templates

Use these templates for consistent output:

- `templates/review-report.md` — Full review report format
- `templates/quick-summary.md` — Brief summary format

## References

Load these for detailed guidance:

- [PEP 8 Summary](references/pep8-summary.md) — PEP 8 quick reference
- [Best Practices](references/best-practices.md) — Python idioms and patterns

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

Structure feedback as:

```markdown
## Code Review: [filename]

### Summary
[1-2 sentence overview]

### Issues Found

#### Critical
- **Line X**: [issue with line reference]

#### Suggestions
- **Line Y**: [improvement with example]

### Positive Aspects
- [what's done well]
```
```

### Create Analysis Script

Create `skills/python-reviewer/scripts/analyze.py`:

```python title="skills/python-reviewer/scripts/analyze.py"
#!/usr/bin/env python3
"""
Static analysis script for Python code review.
Usage: python analyze.py <file.py> [--format json|text]
"""
import ast
import sys
import json
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class Issue:
    line: int
    column: int
    severity: str  # critical, high, medium, low
    category: str
    message: str
    suggestion: str | None = None


def analyze_file(filepath: Path) -> list[Issue]:
    """Analyze a Python file for common issues."""
    issues = []
    content = filepath.read_text()

    # Check line lengths
    for i, line in enumerate(content.splitlines(), 1):
        if len(line) > 88:
            issues.append(Issue(
                line=i,
                column=89,
                severity="low",
                category="formatting",
                message=f"Line exceeds 88 characters ({len(line)} chars)",
                suggestion="Break line or use Black formatter"
            ))

    # Parse AST for deeper analysis
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        issues.append(Issue(
            line=e.lineno or 0,
            column=e.offset or 0,
            severity="critical",
            category="syntax",
            message=f"Syntax error: {e.msg}",
            suggestion="Fix syntax error"
        ))
        return issues

    for node in ast.walk(tree):
        # Check for bare except
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            issues.append(Issue(
                line=node.lineno,
                column=node.col_offset,
                severity="high",
                category="error-handling",
                message="Bare 'except:' clause catches all exceptions",
                suggestion="Specify exception type: except Exception:"
            ))

        # Check for missing docstrings
        if isinstance(node, ast.FunctionDef):
            if not ast.get_docstring(node):
                issues.append(Issue(
                    line=node.lineno,
                    column=node.col_offset,
                    severity="medium",
                    category="documentation",
                    message=f"Function '{node.name}' missing docstring",
                    suggestion="Add docstring describing purpose and parameters"
                ))

    return issues


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze.py <file.py> [--format json|text]")
        sys.exit(1)

    filepath = Path(sys.argv[1])
    output_format = "text"
    if "--format" in sys.argv:
        idx = sys.argv.index("--format")
        output_format = sys.argv[idx + 1]

    if not filepath.exists():
        print(f"Error: File '{filepath}' not found")
        sys.exit(1)

    issues = analyze_file(filepath)

    if output_format == "json":
        print(json.dumps([asdict(i) for i in issues], indent=2))
    else:
        if not issues:
            print(f"✓ No issues found in {filepath}")
        else:
            for issue in issues:
                print(f"{filepath}:{issue.line}:{issue.column} [{issue.severity}] {issue.message}")
                if issue.suggestion:
                    print(f"  → {issue.suggestion}")


if __name__ == "__main__":
    main()
```

### Create Complexity Script

Create `skills/python-reviewer/scripts/complexity.py`:

```python title="skills/python-reviewer/scripts/complexity.py"
#!/usr/bin/env python3
"""
Calculate cyclomatic complexity for Python functions.
Usage: python complexity.py <file.py>
"""
import ast
import sys
from pathlib import Path


class ComplexityVisitor(ast.NodeVisitor):
    """Calculate cyclomatic complexity of functions."""

    def __init__(self):
        self.results = []

    def visit_FunctionDef(self, node):
        complexity = self._calculate_complexity(node)
        self.results.append({
            "name": node.name,
            "line": node.lineno,
            "complexity": complexity,
            "rating": self._rate_complexity(complexity)
        })
        self.generic_visit(node)

    def _calculate_complexity(self, node) -> int:
        """Count decision points."""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.comprehension):
                complexity += 1

        return complexity

    def _rate_complexity(self, complexity: int) -> str:
        if complexity <= 5:
            return "low (good)"
        elif complexity <= 10:
            return "moderate"
        elif complexity <= 20:
            return "high (consider refactoring)"
        else:
            return "very high (refactor recommended)"


def main():
    if len(sys.argv) < 2:
        print("Usage: python complexity.py <file.py>")
        sys.exit(1)

    filepath = Path(sys.argv[1])
    if not filepath.exists():
        print(f"Error: File '{filepath}' not found")
        sys.exit(1)

    tree = ast.parse(filepath.read_text())

    visitor = ComplexityVisitor()
    visitor.visit(tree)

    print(f"Complexity Analysis: {filepath}\n")
    print(f"{'Function':<30} {'Line':<6} {'Complexity':<12} {'Rating'}")
    print("-" * 75)

    for result in visitor.results:
        print(f"{result['name']:<30} {result['line']:<6} {result['complexity']:<12} {result['rating']}")


if __name__ == "__main__":
    main()
```

### Create Reference Documents

Create `skills/python-reviewer/references/pep8-summary.md`:

```markdown title="skills/python-reviewer/references/pep8-summary.md"
# PEP 8 Quick Reference

## Naming Conventions

| Type | Convention | Example |
|------|-----------|---------|
| Module | lowercase_with_underscores | `my_module.py` |
| Class | CapitalizedWords | `MyClass` |
| Function | lowercase_with_underscores | `my_function()` |
| Variable | lowercase_with_underscores | `my_variable` |
| Constant | UPPERCASE_WITH_UNDERSCORES | `MAX_VALUE` |
| Private | _single_leading_underscore | `_internal` |

## Indentation

- Use 4 spaces per indentation level
- Never mix tabs and spaces
- Continuation lines: align with opening delimiter or use hanging indent

## Line Length

- Maximum 79 characters (72 for docstrings)
- Maximum 88 characters (Black formatter default)

## Imports

Order:
1. Standard library imports
2. Related third-party imports
3. Local application imports

Each group separated by a blank line.

## Whitespace

- No whitespace inside parentheses: `spam(ham[1], {eggs: 2})`
- No whitespace before comma: `if x == 4: print(x, y)`
- Surround operators with single space: `x = 1`
```

Create `skills/python-reviewer/references/best-practices.md`:

```markdown title="skills/python-reviewer/references/best-practices.md"
# Python Best Practices

## Use Context Managers

```python
# Bad
f = open('file.txt')
content = f.read()
f.close()

# Good
with open('file.txt') as f:
    content = f.read()
```

## Use List Comprehensions

```python
# Bad
squares = []
for x in range(10):
    squares.append(x ** 2)

# Good
squares = [x ** 2 for x in range(10)]
```

## Use f-strings

```python
# Bad
message = "Hello, " + name + "!"
message = "Hello, {}!".format(name)

# Good
message = f"Hello, {name}!"
```

## Use Type Hints

```python
def greet(name: str, times: int = 1) -> str:
    return f"Hello, {name}! " * times
```

## Use dataclasses

```python
from dataclasses import dataclass

@dataclass
class User:
    name: str
    email: str
    age: int = 0
```
```

### Create Templates

Create `skills/python-reviewer/templates/review-report.md`:

````markdown title="skills/python-reviewer/templates/review-report.md"
# Code Review Report

**File:** {{ filename }}
**Reviewed:** {{ timestamp }}
**Reviewer:** AI Code Reviewer

---

## Summary

{{ summary }}

**Overall Score:** {{ score }}/10

---

## Issues Found

{% if critical_issues %}
### Critical ({{ critical_issues | length }})

{% for issue in critical_issues %}
- **Line {{ issue.line }}**: {{ issue.message }}
  - Suggestion: {{ issue.suggestion }}
{% endfor %}
{% endif %}

{% if high_issues %}
### High Priority ({{ high_issues | length }})

{% for issue in high_issues %}
- **Line {{ issue.line }}**: {{ issue.message }}
  - Suggestion: {{ issue.suggestion }}
{% endfor %}
{% endif %}

---

## Recommendations

{% for rec in recommendations %}
{{ loop.index }}. {{ rec }}
{% endfor %}

---

*Generated by python-reviewer skill*
````

---

## Step 3: Create the Agent

An agent ties together skills, prompts, and behavioral instructions.

### Create Agent Directory

```bash
mkdir -p agents/python-mentor
```

### Create Agent Definition

Create `agents/python-mentor/agent.yaml`:

```yaml title="agents/python-mentor/agent.yaml"
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

### Create System Prompt

Create `agents/python-mentor/system-prompt.md`:

```markdown title="agents/python-mentor/system-prompt.md"
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

Run the analysis scripts when deeper insight is needed:

```bash
python skills/python-reviewer/scripts/analyze.py <file.py>
python skills/python-reviewer/scripts/complexity.py <file.py>
```

## When Refactoring

Use the refactor-function prompt template to ensure consistent, thorough refactoring.

## Communication Style

- Use clear, jargon-free explanations
- Provide code examples for every suggestion
- Reference official Python documentation when relevant
- Offer multiple solutions when trade-offs exist
```

---

## Step 4: Create the Prompt

Create `prompts/refactor-function.md`:

```markdown title="prompts/refactor-function.md"
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

---

## Step 5: Create the Instruction

Create `instructions/python-standards.md`:

```markdown title="instructions/python-standards.md"
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

---

## Step 6: Update the Manifest

Edit `aam.yaml` to include all artifacts:

```yaml title="aam.yaml"
name: "@yourname/python-best-practices"
version: 1.0.0
description: "Python coding standards and best practices for AI agents"
author: Your Name
license: Apache-2.0
repository: https://github.com/yourname/python-best-practices

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

keywords:
  - python
  - code-review
  - best-practices
  - pep8
  - mentor
```

---

## Step 7: Validate the Package

Validate your complete package:

```bash
aam pkg validate
```

**Expected output:**

```
Validating @yourname/python-best-practices@1.0.0...

Manifest:
  ✓ name: valid scoped format (@yourname/python-best-practices)
  ✓ version: valid semver (1.0.0)
  ✓ description: present
  ✓ author: present

Artifacts:
  ✓ agent: python-mentor
    ✓ agent.yaml exists and valid
    ✓ system-prompt.md exists
    ✓ References skill: python-reviewer (found)
    ✓ References prompt: refactor-function (found)
  ✓ skill: python-reviewer
    ✓ SKILL.md exists and valid
    ✓ scripts/analyze.py exists
    ✓ scripts/complexity.py exists
    ✓ references/ directory exists
    ✓ templates/ directory exists
  ✓ prompt: refactor-function
    ✓ prompts/refactor-function.md exists and valid
    ✓ frontmatter valid
    ✓ variables declared correctly
  ✓ instruction: python-standards
    ✓ instructions/python-standards.md exists and valid
    ✓ frontmatter valid

Dependencies:
  ✓ No dependencies declared

✓ Package is valid and ready to publish
```

!!! success "Validation passed!"
    Your package is well-formed and all internal references (agent → skill, agent → prompt) are resolved correctly.

---

## Step 8: Pack the Package

Build the distributable archive:

```bash
aam pkg pack
```

**Expected output:**

```
Building @yourname/python-best-practices@1.0.0...
  Adding aam.yaml
  Adding agents/python-mentor/agent.yaml
  Adding agents/python-mentor/system-prompt.md
  Adding skills/python-reviewer/SKILL.md
  Adding skills/python-reviewer/scripts/analyze.py
  Adding skills/python-reviewer/scripts/complexity.py
  Adding skills/python-reviewer/references/pep8-summary.md
  Adding skills/python-reviewer/references/best-practices.md
  Adding skills/python-reviewer/templates/review-report.md
  Adding prompts/refactor-function.md
  Adding instructions/python-standards.md

✓ Built python-best-practices-1.0.0.aam (8.4 KB)
  Checksum: sha256:a1b2c3d4e5f6...
```

Inspect the archive (optional):

```bash
tar -tzf python-best-practices-1.0.0.aam | head -n 15
```

---

## Step 9: Publish to Registry

Publish to your local registry:

```bash
aam pkg publish --registry local
```

**Expected output:**

```
Publishing @yourname/python-best-practices@1.0.0 to registry 'local'...

Uploading python-best-practices-1.0.0.aam...
  ████████████████████████████████ 100%

✓ Published @yourname/python-best-practices@1.0.0
  Registry: local (file:///home/user/my-packages)
  URL: file:///home/user/my-packages/@yourname/python-best-practices/1.0.0/

⚠ Package is unsigned. Consider signing with --sign for better security.
```

Verify it's in the registry:

```bash
aam search python
```

**Expected output:**

```
    Search results for "python" (1 match)
 Name                             Version  Type   Source  Description
 @yourname/python-best-practices  1.0.0    skill  local   Python coding standards and best practices
```

---

## Step 10: Install and Test

Navigate to a test directory:

```bash
cd ~/test-project
```

Install your package:

```bash
aam install @yourname/python-best-practices
```

**Expected output:**

```
Resolving @yourname/python-best-practices@1.0.0...
  + @yourname/python-best-practices@1.0.0

Downloading 1 package...
  ✓ @yourname/python-best-practices@1.0.0 (8.4 KB)

Verification:
  ✓ Checksum: sha256:a1b2c3d4... matches

Deploying to cursor...
  → agent: python-mentor         → .cursor/rules/agent-yourname--python-mentor.mdc
  → skill: python-reviewer       → .cursor/skills/yourname--python-reviewer/
  → prompt: refactor-function    → .cursor/prompts/refactor-function.md
  → instruction: python-standards → .cursor/rules/python-standards.mdc

✓ Installed 1 package (1 agent, 1 skill, 1 prompt, 1 instruction)
```

Verify deployment:

```bash
# Check skill deployed
ls .cursor/skills/yourname--python-reviewer/

# Check agent deployed
ls .cursor/rules/

# Check instruction deployed
cat .cursor/rules/python-standards.mdc
```

Test the scripts:

```bash
# Create a sample Python file to test
cat > test.py << 'EOF'
def calculate(x,y):
    result=x+y
    return result
EOF

# Run the analysis script
python .cursor/skills/yourname--python-reviewer/scripts/analyze.py test.py
```

**Expected output:**

```
test.py:1:0 [medium] Function 'calculate' missing docstring
  → Add docstring describing purpose and parameters
```

Get package info:

```bash
aam info @yourname/python-best-practices
```

**Expected output:**

```
@yourname/python-best-practices@1.0.0
  Description: Python coding standards and best practices for AI agents
  Author:      Your Name
  License:     MIT
  Repository:  https://github.com/yourname/python-best-practices

  Artifacts:
    agent: python-mentor           — Python mentor agent for code review
    skill: python-reviewer         — Review Python code for best practices
    prompt: refactor-function      — Template for refactoring functions
    instruction: python-standards  — Python coding standards

  Dependencies: none

  Deployed to:
    cursor: .cursor/skills/yourname--python-reviewer/
            .cursor/rules/agent-yourname--python-mentor.mdc
            .cursor/prompts/refactor-function.md
            .cursor/rules/python-standards.mdc
```

---

## What You Built

Congratulations! You created a complete, production-ready AAM package with:

### 1 Skill (python-reviewer)

- ✅ Main instructions (`SKILL.md`)
- ✅ Executable scripts (`analyze.py`, `complexity.py`)
- ✅ Reference documentation (PEP 8, best practices)
- ✅ Output templates (review report)

### 1 Agent (python-mentor)

- ✅ Agent definition (`agent.yaml`)
- ✅ System prompt with personality and instructions
- ✅ References to skill and prompt
- ✅ Tool access configuration

### 1 Prompt (refactor-function)

- ✅ Markdown template with frontmatter
- ✅ Variable declarations
- ✅ Clear instructions for the AI

### 1 Instruction (python-standards)

- ✅ Project-level coding standards
- ✅ Frontmatter with scope and globs
- ✅ Platform-specific deployment rules

---

## Complete Package Structure

Your final package structure:

```
python-best-practices/
├── aam.yaml
├── agents/
│   └── python-mentor/
│       ├── agent.yaml
│       └── system-prompt.md
├── skills/
│   └── python-reviewer/
│       ├── SKILL.md
│       ├── scripts/
│       │   ├── analyze.py
│       │   └── complexity.py
│       ├── templates/
│       │   └── review-report.md
│       └── references/
│           ├── pep8-summary.md
│           └── best-practices.md
├── prompts/
│   └── refactor-function.md
├── instructions/
│   └── python-standards.md
└── python-best-practices-1.0.0.aam  (built archive)
```

---

## Next Steps

Now that you've created a complete package, you can:

### Enhance Your Package

- **Add dependencies** — Reference other packages for shared skills
- **Add tests** — Create a `tests/` directory with pytest tests
- **Add evaluations** — Define metrics to measure package quality
- **Sign your package** — Use Sigstore or GPG for authenticity

### Share Your Package

- **Publish to a shared registry** — Set up an HTTP registry for your team
- **Create portable bundles** — Build platform-specific bundles for sharing via Slack
- **Version and tag** — Use dist-tags like `stable` or `beta`

### Learn More

- **[Dependencies](../concepts/dependencies.md)** — Declare and resolve package dependencies
- **[Platform Adapters](../concepts/platform-adapters.md)** — Understand how AAM deploys to different platforms
- **[Package Existing Artifacts](../tutorials/package-existing-artifacts.md)** — Wrap existing skills into packages
- **[Signing Packages](../tutorials/signing-packages.md)** — Add cryptographic signatures
- **[Testing and Evals](../tutorials/testing-and-evals.md)** — Add quality gates to your packages

---

## Troubleshooting

### Validation Errors

If `aam pkg validate` fails:

1. **Check the error message** — It will tell you exactly what's wrong
2. **Verify file paths** — Ensure paths in `aam.yaml` match actual files
3. **Check frontmatter** — YAML frontmatter must be valid
4. **Test scripts** — Ensure Python scripts are executable and syntax-valid

### Deployment Issues

If artifacts don't appear after install:

```bash
# Check platform configuration
aam config list

# Verify deployment locations
ls -la .cursor/skills/
ls -la .cursor/rules/

# Try reinstalling
aam uninstall @yourname/python-best-practices
aam install @yourname/python-best-practices
```

### Script Execution Issues

If scripts don't run:

```bash
# Make scripts executable
chmod +x .cursor/skills/yourname--python-reviewer/scripts/*.py

# Run with explicit Python
python3 .cursor/skills/yourname--python-reviewer/scripts/analyze.py test.py
```

---

## Summary

In this tutorial, you:

1. ✅ Initialized a scoped package with `aam pkg init` (`@yourname/python-best-practices`)
2. ✅ Created a complete skill with scripts, templates, and references
3. ✅ Created an agent that uses the skill and prompts
4. ✅ Created a prompt template with variables
5. ✅ Created project-level instructions
6. ✅ Validated the package structure (`aam pkg validate`)
7. ✅ Built a distributable `.aam` archive (`aam pkg pack`)
8. ✅ Published to a local registry (`aam pkg publish`)
9. ✅ Installed and verified deployment

You now have hands-on experience with the full AAM workflow and understand how to create production-ready packages.

**Ready to build more?** Check out the [Tutorials](../tutorials/index.md) section for advanced topics and real-world examples.
