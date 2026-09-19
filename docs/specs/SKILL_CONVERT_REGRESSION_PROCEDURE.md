# Skill convert regression procedure

This procedure measures regressions in cross-platform skill conversion for
supported coding agents (Cursor, Copilot, Claude Code, Codex). Use it before
each release, and whenever convert, adapters, scanner, or skill path mappings
change.

## Purpose

You verify that `aam convert` still follows the skill conventions in
[BIDIRECTIONAL_CONVERSION_CONVENTIONS.md](BIDIRECTIONAL_CONVERSION_CONVENTIONS.md):

- Skills are copied as-is (frontmatter is not rewritten).
- Cursor and Codex targets preserve nesting under the skills root.
- Copilot and Claude Code targets flatten to the `SKILL.md` parent folder name.
- Discovery covers platform roots plus shared `.agents/skills/` and legacy
  `.codex/skills/` (Codex).
- Re-running convert without `--force` skips existing targets.

## References

| Document | Role |
|----------|------|
| [BIDIRECTIONAL_CONVERSION_CONVENTIONS.md](BIDIRECTIONAL_CONVERSION_CONVENTIONS.md) | Source of truth for path and nesting rules |
| [SPEC-convert-command.md](SPEC-convert-command.md) | Convert command contract |
| [docs/user_docs/docs/cli/convert.md](../user_docs/docs/cli/convert.md) | User-facing convert docs |
| `apps/aam-cli/tests/integration/test_integration_skill_convert_conventions.py` | Automated E2E suite |

## Prerequisites

1. Use Python 3.11+ and the repo virtualenv.
2. Install the CLI in editable mode from `apps/aam-cli` if needed:
   `pip install -e ".[dev]"`.
3. Confirm `aam --help` lists the `convert` command.

```bash
cd /data/projects/code_workspace/agent-package-manager
source .venv/bin/activate
aam --version
```

## Automated regression gate (required for release)

Run these commands from the monorepo root (or from `apps/aam-cli` for pytest
paths below).

### 1. Skill convert E2E integration suite

```bash
cd apps/aam-cli
source ../../.venv/bin/activate
pytest tests/integration/test_integration_skill_convert_conventions.py -v --tb=short
```

**Pass criteria:**

- [ ] All tests in the file pass (8 cases as of 2026-09-19).
- [ ] Exit code is `0`.

**What the suite covers:**

| Test class / case | Convention checked |
|-------------------|--------------------|
| Cursor → Codex nested skill | Nesting preserved under `.agents/skills/shipping/land-it/` |
| Cursor → Copilot nested skill | Flattened to `.github/skills/land-it/` |
| Cursor → Claude nested skill | Flattened to `.claude/skills/land-it/` |
| Codex legacy + shared roots | `.codex/skills/` and `.agents/skills/` convert to Cursor |
| Claude → Cursor as-is | Claude-only frontmatter (`when_to_use`, `allowed-tools`) unchanged |
| CLI Cursor → Codex | `aam convert -s cursor -t codex --type skill --force` |
| CLI idempotent skip | Second run without `--force` skips existing targets |
| Round-trip Cursor → Codex → Cursor | Nested path and `SKILL.md` body unchanged |

### 2. Broader convert and adapter unit coverage

```bash
pytest tests/unit/test_convert.py \
  tests/unit/test_unit_skill_scope_deploy.py \
  tests/unit/test_adapters_factory.py \
  tests/unit/test_unit_adapter_lifecycle.py \
  tests/unit/test_unit_adapter_commands.py \
  -v --tb=short
```

**Pass criteria:**

- [ ] All listed unit tests pass.

### 3. Full CLI suite (release gate)

```bash
cd ../..   # monorepo root
npx nx test aam-cli
```

**Pass criteria:**

- [ ] `npx nx test aam-cli` exits `0`.
- [ ] Record pass/skip counts in the release notes checklist (example baseline:
  803 passed, 3 skipped on 2026-09-19).

## Manual smoke (recommended for release)

Use a disposable project. Do not run this in a real developer workspace.

### Setup fixture project

```bash
WORKDIR=/tmp/aam-skill-convert-regression-$(date +%Y%m%d)
mkdir -p "$WORKDIR" && cd "$WORKDIR"

# Nested Cursor skill with support files
mkdir -p .cursor/skills/shipping/land-it/{scripts,references}
cat > .cursor/skills/shipping/land-it/SKILL.md <<'EOF'
---
name: land-it
description: Land a change safely. Use when merging PRs or finishing a ship.
paths:
  - "**/*.ts"
disable-model-invocation: false
metadata:
  author: aam-regression
  version: "1.0"
---

# Land It

Ship carefully. Run tests before merge.
EOF
echo '#!/usr/bin/env bash
echo ok' > .cursor/skills/shipping/land-it/scripts/validate.sh
echo '# Checklist
- tests' > .cursor/skills/shipping/land-it/references/CHECKLIST.md

# Flat Cursor skill
mkdir -p .cursor/skills/code-review
cat > .cursor/skills/code-review/SKILL.md <<'EOF'
---
name: code-review
description: Review code for defects.
---

# Code Review
EOF

# Shared root skill (Cursor / Copilot / Codex discover this)
mkdir -p .agents/skills/shared-ops
cat > .agents/skills/shared-ops/SKILL.md <<'EOF'
---
name: shared-ops
description: Shared ops skill.
---

# Shared Ops
EOF

# Legacy Codex skill
mkdir -p .codex/skills/legacy-ops
cat > .codex/skills/legacy-ops/SKILL.md <<'EOF'
---
name: legacy-ops
description: Legacy Codex skill path.
---

# Legacy Ops
EOF

# Claude-only skill with Claude extras
mkdir -p .claude/skills/security-audit
cat > .claude/skills/security-audit/SKILL.md <<'EOF'
---
name: security-audit
description: Security-focused audit skill for Claude Code.
when_to_use: When reviewing auth, secrets, or injection risks.
allowed-tools: Read Grep Bash(git:*)
---

# Security Audit
EOF
```

### TC-S01: Cursor → Codex preserves nesting

```bash
cd "$WORKDIR"
aam convert -s cursor -t codex --type skill --force
```

**Verify:**

- [ ] `.agents/skills/shipping/land-it/SKILL.md` exists.
- [ ] `.agents/skills/shipping/land-it/scripts/validate.sh` exists.
- [ ] `.agents/skills/code-review/SKILL.md` exists.
- [ ] `paths` and `metadata` remain in the converted `land-it` frontmatter.
- [ ] Shared skill at `.agents/skills/shared-ops` is skipped as same-path
  (or reported as skipped), not corrupted.

### TC-S02: Cursor → Copilot flattens nesting

```bash
cd "$WORKDIR"
# Start from a fresh copy of the fixture if TC-S01 already mutated trees
aam convert -s cursor -t copilot --type skill --force
```

**Verify:**

- [ ] `.github/skills/land-it/SKILL.md` exists.
- [ ] `.github/skills/shipping/land-it/` does **not** exist.
- [ ] Frontmatter fields from Cursor (for example `paths`) are still present
  (as-is copy).

### TC-S03: Cursor → Claude Code flattens nesting

```bash
aam convert -s cursor -t claude-code --type skill --force
```

**Verify:**

- [ ] `.claude/skills/land-it/SKILL.md` exists (flattened).
- [ ] Original `.claude/skills/security-audit/SKILL.md` still exists.

### TC-S04: Codex legacy root → Cursor

```bash
aam convert -s codex -t cursor --type skill --force
```

**Verify:**

- [ ] `.cursor/skills/legacy-ops/SKILL.md` exists.
- [ ] `.cursor/skills/shared-ops/SKILL.md` exists (from `.agents/skills`).

### TC-S05: Claude → Cursor keeps Claude extras as-is

```bash
aam convert -s claude-code -t cursor --type skill --force
```

**Verify:**

- [ ] `.cursor/skills/security-audit/SKILL.md` contains `when_to_use`.
- [ ] `.cursor/skills/security-audit/SKILL.md` contains `allowed-tools`.

### TC-S06: Idempotent skip without `--force`

```bash
aam convert -s cursor -t copilot --type skill --force
aam convert -s cursor -t copilot --type skill
```

**Verify:**

- [ ] Second run exit code is `0`.
- [ ] Output indicates skip / use `--force` for existing targets.
- [ ] Existing `.github/skills/land-it/SKILL.md` content is unchanged.

### TC-S07: Round-trip Cursor → Codex → Cursor

```bash
# Ensure nested Cursor source exists, then:
aam convert -s cursor -t codex --type skill --force
rm -rf .cursor/skills/shipping
aam convert -s codex -t cursor --type skill --force
```

**Verify:**

- [ ] `.cursor/skills/shipping/land-it/SKILL.md` is restored.
- [ ] Body text matches the original ("Ship carefully").
- [ ] `scripts/validate.sh` is restored.

## Install path regression (related, not convert)

Skill install paths must stay aligned with convert targets.

| Platform | `skill_scope: project` | `skill_scope: user` |
|----------|------------------------|---------------------|
| Cursor | `.cursor/skills/` | `~/.cursor/skills/` |
| Codex | `.agents/skills/` | `~/.agents/skills/` |

```bash
cd apps/aam-cli
pytest tests/unit/test_unit_skill_scope_deploy.py -v --tb=short
```

**Pass criteria:**

- [ ] All skill_scope deploy tests pass.
- [ ] Codex undeploy/list still finds legacy `~/.codex/skills/` for cleanup.

## Recording results for a release

Copy this block into the release checklist or PR description:

```text
Skill convert regression — release: <version or date>
Date:
Tester / CI job:

Automated:
- [ ] test_integration_skill_convert_conventions.py  ( / 8 passed)
- [ ] convert + adapter unit subset
- [ ] npx nx test aam-cli  (passed / skipped / failed)

Manual smoke:
- [ ] TC-S01 Cursor → Codex preserve nesting
- [ ] TC-S02 Cursor → Copilot flatten
- [ ] TC-S03 Cursor → Claude flatten
- [ ] TC-S04 Codex legacy + shared roots
- [ ] TC-S05 Claude extras as-is
- [ ] TC-S06 Idempotent skip
- [ ] TC-S07 Round-trip

Notes / failures:
```

## When to re-run

Re-run this procedure when any of the following change:

- `apps/aam-cli/src/aam_cli/services/convert_service.py`
- `apps/aam-cli/src/aam_cli/converters/mappings.py`
- `apps/aam-cli/src/aam_cli/adapters/cursor.py` or `codex.py`
- `apps/aam-cli/src/aam_cli/detection/scanner.py`
- `apps/aam-cli/src/aam_cli/core/installer.py` skill_scope wiring
- Skill path sections in BIDIRECTIONAL_CONVERSION_CONVENTIONS or convert docs

## Baseline

| Date | Gate | Result |
|------|------|--------|
| 2026-09-19 | `test_integration_skill_convert_conventions.py` | 8 passed |
| 2026-09-19 | `npx nx test aam-cli` | 803 passed, 3 skipped |

Update this table after each release run.
