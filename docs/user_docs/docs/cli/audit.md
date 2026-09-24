# aam audit

**Dependency Management**

## Synopsis

```bash
aam audit [OPTIONS]
```

## Description

Audit installed packages for integrity issues. Computes directory
hashes for all installed packages and compares them against stored
checksums in `package.agent.lock`. Reports any mismatches as findings
with severity levels.

Use this command to detect tampering, corruption, or unexpected
modifications to installed packages.

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--severity` | `all` | Minimum severity level to report: `critical`, `high`, `medium`, `low`, `info`, `all` |
| `--project` | current directory | Project directory path |

## Examples

### Example 1: Audit all packages

```bash
aam audit
```

**Output (no findings):**
```
✓ All 5 packages passed integrity audit
```

**Output (with findings):**
```
             Audit Findings (all)
┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Package            ┃ Version ┃ Severity  ┃ Title                    ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ report-templates   │ 2.1.0   │ CRITICAL  │ Checksum mismatch        │
│ shared-prompts     │ 1.0.0   │ MEDIUM    │ Extra files detected     │
└────────────────────┴─────────┴───────────┴──────────────────────────┘

✗ 2 finding(s) across 5 packages audited
```

### Example 2: Filter by severity

```bash
aam audit --severity critical
```

Shows only critical findings. Useful in CI pipelines where you want
to fail only on serious integrity issues.

### Example 3: Audit a specific project

```bash
aam audit --severity high --project ./my-project
```

### Example 4: No packages installed

```bash
aam audit
```

**Output:**
```
No packages installed to audit.
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | No findings at or above the specified severity |
| 1 | One or more findings detected |

## Related commands

- [`aam verify`](verify.md) — Verify individual file checksums
- [`aam check`](check.md) — Verify packages are installed
- [`aam diff`](diff.md) — Show diffs for modified files

## Notes

### Severity levels

Findings are classified by severity:

| Level | Meaning |
|-------|---------|
| `critical` | Checksum mismatch — package contents differ from lock file |
| `high` | Missing package directory |
| `medium` | Extra or unexpected files detected |
| `low` | Minor discrepancies |
| `info` | Informational notices |

### CI/CD usage

Use `aam audit` in your CI pipeline to catch integrity issues:

```bash
aam audit --severity high
```

The command exits with code 1 if findings exist, making it suitable
as a pipeline gate.
