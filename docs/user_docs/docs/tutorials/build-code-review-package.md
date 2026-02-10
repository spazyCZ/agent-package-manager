# Tutorial: Building a Code Review Package

**Difficulty:** Intermediate
**Time:** 25 minutes

## What You'll Learn

In this comprehensive tutorial, you'll build a complete AAM package from scratch: a security review toolkit with skills, scripts, templates, agents, prompts, instructions, and quality tests.

This tutorial demonstrates:

- Creating all artifact types (skills, agents, prompts, instructions)
- Organizing complex skills with scripts, templates, and references
- Wiring up dependencies between artifacts
- Adding quality tests and validations
- The complete workflow from `aam pkg init` through `aam pkg publish`

## Prerequisites

- AAM installed (`aam --version` works)
- Python 3.8+ (for the example scripts)
- Basic understanding of YAML and Markdown
- Familiarity with command line operations

## The Scenario

You're building a **security review toolkit** for your team. It needs:

1. **security-scan skill** - Automated scanning with scripts and templates
2. **performance-check skill** - Performance analysis tools
3. **security-reviewer agent** - An AI agent that uses the security-scan skill
4. **security-report prompt** - Structured prompt for generating reports
5. **secure-coding instruction** - Security guidelines applied to all code

Let's build it step by step.

---

## Step 1: Initialize the Package

Create a new directory and initialize the AAM package:

```bash
mkdir code-review-toolkit
cd code-review-toolkit

aam pkg init
```

Fill in the prompts:

```
Package name [code-review-toolkit]: @author/code-review-toolkit
Version [1.0.0]: <press Enter>
Description: Comprehensive security and performance code review toolkit
Author: <your-username>
License [MIT]: <press Enter>

What artifacts will this package contain?
  [x] Skills
  [x] Agents
  [x] Prompts
  [x] Instructions
```

This creates:

```
code-review-toolkit/
├── aam.yaml
├── skills/
├── agents/
├── prompts/
└── instructions/
```

---

## Step 2: Create the Security Scan Skill

This skill demonstrates a **complete skill structure** with all components.

### 2.1 Create Directory Structure

```bash
mkdir -p skills/security-scan/{scripts,templates,references}
```

### 2.2 Create SKILL.md

Create `skills/security-scan/SKILL.md`:

```markdown
---
name: security-scan
description: Scan code for common security vulnerabilities. Use when reviewing code for security issues or when asked about secure coding practices.
---

# Security Scanner

## Available Scripts

Run these scripts for automated analysis:

- `scripts/scan.py <file>` — Static security analysis
- `scripts/check_secrets.sh <dir>` — Detect hardcoded secrets

Example:
\```bash
python skills/security-scan/scripts/scan.py src/auth.py --format json
\```

## Templates

Use for consistent output:

- `templates/security-report.md.j2` — Full security assessment
- `templates/finding.md.j2` — Individual finding format

## References

Load for detailed guidance:

- [OWASP Top 10](references/owasp-top10.md) — Common web vulnerabilities
- [CWE Patterns](references/cwe-patterns.md) — Weakness enumeration

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
1. Run `scripts/scan.py` for automated detection
2. Manually review for logic flaws
3. Rate severity: Critical / High / Medium / Low
4. Generate report using template
5. Provide remediation guidance with CWE references
```

### 2.3 Create scan.py Script

Create `skills/security-scan/scripts/scan.py`:

```python
#!/usr/bin/env python3
"""
Security scanner for common vulnerabilities.
Usage: python scan.py <file> [--format text|json]
"""
import re
import sys
import json
from pathlib import Path
from dataclasses import dataclass, asdict

@dataclass
class Finding:
    id: str
    severity: str
    category: str
    title: str
    file: str
    line: int
    code: str
    description: str
    cwe: str
    remediation: str

# Security patterns to detect
PATTERNS = {
    "sql_injection": {
        "pattern": r'execute\s*\(\s*["\'].*%s.*["\']\s*%',
        "severity": "critical",
        "cwe": "CWE-89",
        "title": "SQL Injection",
        "description": "User input directly concatenated into SQL query",
        "remediation": "Use parameterized queries or prepared statements"
    },
    "hardcoded_password": {
        "pattern": r'(?i)(password|passwd|pwd)\s*=\s*["\'][^"\']+["\']',
        "severity": "high",
        "cwe": "CWE-798",
        "title": "Hardcoded Credentials",
        "description": "Password appears to be hardcoded in source",
        "remediation": "Use environment variables or secure vault"
    },
    "eval_usage": {
        "pattern": r'\beval\s*\(',
        "severity": "high",
        "cwe": "CWE-95",
        "title": "Code Injection via eval()",
        "description": "eval() can execute arbitrary code",
        "remediation": "Use ast.literal_eval() or avoid dynamic evaluation"
    },
    "shell_injection": {
        "pattern": r'os\.system\s*\(|subprocess\.call\s*\([^,]+shell\s*=\s*True',
        "severity": "critical",
        "cwe": "CWE-78",
        "title": "Shell Injection",
        "description": "Command executed with shell=True or os.system",
        "remediation": "Use subprocess with shell=False and argument list"
    }
}

def scan_file(filepath: Path) -> list[Finding]:
    findings = []
    content = filepath.read_text()
    lines = content.splitlines()

    for vuln_id, config in PATTERNS.items():
        for i, line in enumerate(lines, 1):
            if re.search(config["pattern"], line):
                findings.append(Finding(
                    id=f"SEC-{len(findings)+1:03d}",
                    severity=config["severity"],
                    category="security",
                    title=config["title"],
                    file=str(filepath),
                    line=i,
                    code=line.strip(),
                    description=config["description"],
                    cwe=config["cwe"],
                    remediation=config["remediation"]
                ))

    return findings

def main():
    if len(sys.argv) < 2:
        print("Usage: python scan.py <file> [--format text|json]")
        sys.exit(1)

    filepath = Path(sys.argv[1])
    output_format = "text"
    if "--format" in sys.argv:
        output_format = sys.argv[sys.argv.index("--format") + 1]

    findings = scan_file(filepath)

    if output_format == "json":
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        for f in findings:
            print(f"[{f.severity.upper()}] {f.id}: {f.title}")
            print(f"  File: {f.file}:{f.line}")
            print(f"  Code: {f.code}")
            print(f"  CWE: {f.cwe}")
            print(f"  Fix: {f.remediation}")
            print()

if __name__ == "__main__":
    main()
```

Make it executable:

```bash
chmod +x skills/security-scan/scripts/scan.py
```

### 2.4 Create check_secrets.sh Script

Create `skills/security-scan/scripts/check_secrets.sh`:

```bash
#!/bin/bash
# Detect hardcoded secrets in source files
# Usage: ./check_secrets.sh <directory>

DIR="${1:-.}"

echo "Scanning for secrets in: $DIR"
echo "================================"

# Patterns to detect
patterns=(
    "api[_-]?key\s*[:=]"
    "secret[_-]?key\s*[:=]"
    "password\s*[:=]"
    "private[_-]?key"
    "AWS_SECRET"
    "BEGIN RSA PRIVATE KEY"
)

found=0

for pattern in "${patterns[@]}"; do
    results=$(grep -rn -E "$pattern" "$DIR" \
        --include="*.py" --include="*.js" \
        --include="*.yaml" --include="*.json" 2>/dev/null)
    if [ -n "$results" ]; then
        echo "Pattern: $pattern"
        echo "$results"
        echo ""
        ((found++))
    fi
done

if [ $found -eq 0 ]; then
    echo "No secrets detected."
else
    echo "================================"
    echo "Found $found potential secret patterns!"
fi
```

Make it executable:

```bash
chmod +x skills/security-scan/scripts/check_secrets.sh
```

### 2.5 Create Report Template

Create `skills/security-scan/templates/security-report.md.j2`:

```jinja2
# Security Assessment Report

**Target:** {{ target }}
**Date:** {{ date }}
**Scanner:** security-scan skill v1.0

---

## Executive Summary

| Severity | Count |
|----------|-------|
| Critical | {{ findings | selectattr('severity', 'eq', 'critical') | list | length }} |
| High     | {{ findings | selectattr('severity', 'eq', 'high') | list | length }} |
| Medium   | {{ findings | selectattr('severity', 'eq', 'medium') | list | length }} |
| Low      | {{ findings | selectattr('severity', 'eq', 'low') | list | length }} |

**Risk Level:** {{ risk_level }}

---

## Findings

{% for finding in findings %}
### {{ finding.id }}: {{ finding.title }}

| Field | Value |
|-------|-------|
| Severity | **{{ finding.severity | upper }}** |
| Location | `{{ finding.file }}:{{ finding.line }}` |
| CWE | [{{ finding.cwe }}](https://cwe.mitre.org/data/definitions/{{ finding.cwe | replace('CWE-', '') }}.html) |

**Description:** {{ finding.description }}

**Vulnerable Code:**
```
{{ finding.code }}
```

**Remediation:** {{ finding.remediation }}

---

{% endfor %}

## Recommendations

1. Address all Critical findings immediately
2. Schedule High findings for next sprint
3. Track Medium/Low in backlog
4. Implement security linting in CI/CD

---

*Generated by security-scan skill*
```

### 2.6 Create Reference Documents

Create `skills/security-scan/references/owasp-top10.md`:

```markdown
# OWASP Top 10 (2021)

## A01: Broken Access Control

Access control enforces policy such that users cannot act outside their intended permissions.

**What to look for:**
- Missing authorization checks
- IDOR (Insecure Direct Object References)
- CORS misconfiguration
- Path traversal

## A02: Cryptographic Failures

Failures related to cryptography which often lead to sensitive data exposure.

**What to look for:**
- Weak algorithms (MD5, SHA1 for passwords)
- Hardcoded keys
- Missing encryption for sensitive data
- Improper certificate validation

## A03: Injection

User-supplied data is not validated, filtered, or sanitized.

**What to look for:**
- SQL injection
- Command injection
- LDAP injection
- XSS (Cross-site scripting)

## A04: Insecure Design

Missing or ineffective security controls.

**What to look for:**
- Missing rate limiting
- No defense in depth
- Missing input validation at trust boundaries

## A05-A10: Additional Vulnerabilities

See the full OWASP Top 10 for complete coverage of:
- Security Misconfiguration
- Vulnerable Components
- Authentication Failures
- Software and Data Integrity Failures
- Security Logging Failures
- Server-Side Request Forgery
```

Create `skills/security-scan/references/cwe-patterns.md`:

```markdown
# Common CWE Patterns

## CWE-89: SQL Injection

**Pattern:**
\```python
# Vulnerable
query = "SELECT * FROM users WHERE id = " + user_id
cursor.execute(query)

# Safe
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
\```

## CWE-78: OS Command Injection

**Pattern:**
\```python
# Vulnerable
os.system(f"ping {host}")

# Safe
subprocess.run(["ping", host], shell=False)
\```

## CWE-798: Hardcoded Credentials

**Pattern:**
\```python
# Vulnerable
password = "secret123"

# Safe
password = os.environ.get("DB_PASSWORD")
\```
```

---

## Step 3: Create the Performance Check Skill

Create the second skill with a simpler structure:

```bash
mkdir -p skills/performance-check/{scripts,references}
```

Create `skills/performance-check/SKILL.md`:

```markdown
---
name: performance-check
description: Analyze code for performance issues and optimization opportunities. Use when asked about performance, optimization, or efficiency.
---

# Performance Analyzer

## Available Scripts

- `scripts/complexity.py <file>` — Calculate cyclomatic and cognitive complexity

Example:
\```bash
python skills/performance-check/scripts/complexity.py src/main.py
\```

## References

- [Big-O Cheatsheet](references/big-o-cheatsheet.md) — Complexity reference

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

## Workflow

1. Run `scripts/complexity.py` for static analysis
2. Review findings against Big-O cheatsheet
3. Provide optimization recommendations
```

Create a simplified `skills/performance-check/scripts/complexity.py`:

```python
#!/usr/bin/env python3
"""
Simple complexity analyzer.
Usage: python complexity.py <file.py>
"""
import ast
import sys
from pathlib import Path

def count_complexity(node):
    """Simple cyclomatic complexity counter."""
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
            complexity += 1
    return complexity

def analyze(filepath: Path):
    tree = ast.parse(filepath.read_text())

    print(f"Complexity Analysis: {filepath}\n")
    print(f"{'Function':<25} {'Complexity':<12} {'Rating'}")
    print("-" * 50)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            cc = count_complexity(node)
            rating = "Good" if cc <= 10 else "Refactor recommended"
            print(f"{node.name:<25} {cc:<12} {rating}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python complexity.py <file.py>")
        sys.exit(1)
    analyze(Path(sys.argv[1]))
```

```bash
chmod +x skills/performance-check/scripts/complexity.py
```

Create `skills/performance-check/references/big-o-cheatsheet.md`:

```markdown
# Big-O Complexity Cheatsheet

## Common Time Complexities

| Notation | Name | Example |
|----------|------|---------|
| O(1) | Constant | Hash table lookup |
| O(log n) | Logarithmic | Binary search |
| O(n) | Linear | Single loop |
| O(n log n) | Linearithmic | Merge sort |
| O(n²) | Quadratic | Nested loops |
| O(2ⁿ) | Exponential | Recursive fibonacci |

## Python-Specific

| Operation | Time |
|-----------|------|
| `list.append()` | O(1) |
| `x in list` | O(n) |
| `x in set` | O(1) |
| `list.sort()` | O(n log n) |
```

---

## Step 4: Create the Security Reviewer Agent

Create the agent that uses the security-scan skill:

```bash
mkdir -p agents/security-reviewer
```

Create `agents/security-reviewer/agent.yaml`:

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

Create `agents/security-reviewer/system-prompt.md`:

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

---

## Step 5: Create the Security Report Prompt

Create `prompts/security-report.md`:

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

---

## Step 6: Create the Secure Coding Instruction

Create `instructions/secure-coding.md`:

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

---

## Step 7: Update the Manifest

Your `aam.yaml` should already have been created. Update it to declare all artifacts:

```yaml
name: "@author/code-review-toolkit"
version: 1.0.0
description: "Comprehensive security and performance code review toolkit"
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

---

## Step 8: Add Quality Tests (Optional)

Add test declarations to `aam.yaml`:

```yaml
# Add this section to aam.yaml
quality:
  tests:
    - name: "validate-scripts"
      command: "python -m py_compile skills/*/scripts/*.py"
      description: "Validate Python scripts syntax"
    - name: "check-markdown"
      command: "markdownlint skills/ agents/ instructions/ prompts/ || true"
      description: "Check markdown formatting"
```

---

## Step 9: Validate the Package

Check that everything is properly configured:

```bash
aam pkg validate
```

Expected output:

```
Validating package: @author/code-review-toolkit@1.0.0

✓ Manifest is valid
✓ All artifact paths exist
✓ Skills are well-formed (2/2)
  - security-scan: ✓ SKILL.md valid, 2 scripts, 1 template, 2 references
  - performance-check: ✓ SKILL.md valid, 1 script, 1 reference
✓ Agents are well-formed (1/1)
  - security-reviewer: ✓ agent.yaml valid, system-prompt.md exists
✓ Prompts are well-formed (1/1)
  - security-report: ✓ Frontmatter valid, 2 variables declared
✓ Instructions are well-formed (1/1)
  - secure-coding: ✓ Frontmatter valid
✓ No dependency conflicts
✓ Quality tests declared (2)

Package is ready for publishing!
```

If you see errors, fix them before proceeding.

---

## Step 10: Test the Scripts Locally

Before packaging, test that the scripts work:

```bash
# Create a test file with vulnerabilities
cat > test_vulnerable.py << 'EOF'
# Test file with security issues
password = "hardcoded_secret123"
query = "SELECT * FROM users WHERE id = " + user_id
os.system("rm " + filename)
EOF

# Run the security scanner
python skills/security-scan/scripts/scan.py test_vulnerable.py
```

Expected output:

```
[HIGH] SEC-001: Hardcoded Credentials
  File: test_vulnerable.py:2
  Code: password = "hardcoded_secret123"
  CWE: CWE-798
  Fix: Use environment variables or secure vault

[CRITICAL] SEC-002: SQL Injection
  File: test_vulnerable.py:3
  Code: query = "SELECT * FROM users WHERE id = " + user_id
  CWE: CWE-89
  Fix: Use parameterized queries or prepared statements

[CRITICAL] SEC-003: Shell Injection
  File: test_vulnerable.py:4
  Code: os.system("rm " + filename)
  CWE: CWE-78
  Fix: Use subprocess with shell=False and argument list
```

Great! The scanner works. Clean up:

```bash
rm test_vulnerable.py
```

---

## Step 11: Pack the Package

Build the distributable archive:

```bash
aam pkg pack
```

Expected output:

```
Building package: @author/code-review-toolkit@1.0.0

✓ Validated manifest
✓ Copied artifacts
✓ Generated checksums
✓ Created archive: dist/code-review-toolkit-1.0.0.aam (15.2 KB)

Archive contents:
  - aam.yaml
  - 2 skills (with 3 scripts, 1 template, 3 references)
  - 1 agent
  - 1 prompt
  - 1 instruction
  - 2 quality tests
```

---

## Step 12: Test Installation

Install the package in a test directory:

```bash
# Go to a test location
cd /tmp
mkdir test-install
cd test-install

# Install the package
aam install ~/code-review-toolkit/dist/code-review-toolkit-1.0.0.aam

# Verify installation
aam list
```

Expected output:

```
Installed packages:
  @author/code-review-toolkit  1.0.0  5 artifacts (2 skills, 1 agent, 1 prompt, 1 instruction)
```

Check deployed files:

```bash
# Skills deployed
ls .aam/packages/author--code-review-toolkit/skills/
# security-scan  performance-check

# Agent deployed to Cursor (if cursor is your default platform)
ls .cursor/rules/
# agent-author--security-reviewer.mdc

# Scripts are available
ls .aam/packages/author--code-review-toolkit/skills/security-scan/scripts/
# scan.py  check_secrets.sh
```

---

## Step 13: Publish to Registry (Optional)

If you have a registry configured:

```bash
cd ~/code-review-toolkit

# Publish to local registry
aam pkg publish --registry local

# Or publish with signature (requires signing setup)
aam pkg publish --sign
```

---

## Next Steps

Congratulations! You've built a complete AAM package with:

- 2 skills with executable scripts and reference materials
- 1 agent that uses those skills
- 1 structured prompt template
- 1 instruction for coding standards
- Quality tests for validation

Now you can:

- **Share with your team** - Follow [Sharing with Your Team](share-with-team.md)
- **Add dependencies** - Enhance it with external packages in [Working with Dependencies](working-with-dependencies.md)
- **Deploy multi-platform** - Configure deployment in [Multi-Platform Deployment](multi-platform-deployment.md)

---

## Summary

**Key Concepts Covered:**

- **Complete skill structure** - Scripts, templates, references
- **Agent-skill wiring** - Agents reference skills in their configuration
- **Prompt variables** - Structured prompts with variable interpolation
- **Global instructions** - Apply security standards across all code
- **Quality gates** - Validate scripts before publishing

**Complete Package Structure:**

```
code-review-toolkit/
├── aam.yaml
├── skills/
│   ├── security-scan/
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   │   ├── scan.py
│   │   │   └── check_secrets.sh
│   │   ├── templates/
│   │   │   └── security-report.md.j2
│   │   └── references/
│   │       ├── owasp-top10.md
│   │       └── cwe-patterns.md
│   └── performance-check/
│       ├── SKILL.md
│       ├── scripts/
│       │   └── complexity.py
│       └── references/
│           └── big-o-cheatsheet.md
├── agents/
│   └── security-reviewer/
│       ├── agent.yaml
│       └── system-prompt.md
├── prompts/
│   └── security-report.md
└── instructions/
    └── secure-coding.md
```

You've mastered the complete AAM package creation workflow!
