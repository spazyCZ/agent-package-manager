# aam test

**Quality & Testing**

## Synopsis

```bash
aam test [SKILL_NAME] [OPTIONS]
```

## Description

Run deterministic assert-based tests for skills or hooks in the current
AAM package. Tests live under a skill's `tests/` directory (or
`hooks/tests/` for hook tests) and are discovered automatically.

Use this command to verify skills and hooks behave as expected before
packing or publishing.

## Arguments

| Argument | Description |
|----------|-------------|
| `SKILL_NAME` | Optional — run tests for a specific skill only. |

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--hooks` | off | Run hook tests instead of skill tests |
| `--event` | none | Filter hook tests by event name |
| `--case` | none | Run a specific test case by name |
| `--json` | off | Output results as JSON |

## Examples

### Example 1: Test all skills

```bash
aam test
```

### Example 2: Test a specific skill

```bash
aam test my-skill
```

### Example 3: Test hooks for a specific event

```bash
aam test --hooks --event pre_tool_use
```

### Example 4: Run a single test case

```bash
aam test my-skill --case handles-empty-input
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | All test cases passed (or no test suites were found) |
| 1 | One or more test cases failed |

## Related commands

- [`aam eval`](eval.md) — Run LLM-judged evaluations
- [`aam validate`](validate.md) — Validate package structure
