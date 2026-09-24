# aam eval

**Quality & Testing**

## Synopsis

```bash
aam eval [OPTIONS]
```

## Description

Run LLM-judged evaluations for skills in the current AAM package. Eval
cases are declared in a skill's `evals/` directory and are scored by
running the configured engine against each case.

Use `--dry-run` to parse and list discovered eval cases without
executing them (useful for quickly checking coverage without incurring
LLM cost).

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--target` | none | Evaluate a specific skill only |
| `--engine` | `claude-code` | Eval engine to use (`claude-code`) |
| `--dry-run` | off | Parse cases without executing them |
| `--json` | off | Output results as JSON |

## Examples

### Example 1: Preview eval cases

```bash
aam eval --dry-run
```

### Example 2: Run all evals

```bash
aam eval
```

### Example 3: Evaluate a specific skill

```bash
aam eval --target my-skill
```

### Example 4: Output as JSON

```bash
aam eval --engine claude-code --json
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | All eval cases passed (or this was a dry run) |
| 1 | One or more eval cases failed |

## Related commands

- [`aam test`](test.md) — Run deterministic assert-based tests
- [`aam validate`](validate.md) — Validate package structure
