# Feature Specification: Skill Path Convert Remediation

**Feature Branch**: `009-skill-path-convert`  
**Created**: 2026-09-19  
**Status**: Implemented  
**Input**: Align AAM skill discovery, convert, and install paths with current
Agent Skills conventions for Cursor, Copilot, Claude Code, and Codex. Keep
`SKILL.md` copy-as-is; fix path/discovery only.

## Summary of changes

This feature is **not** part of `008-commands-layout` (CLI command directory
restructure). It remediates skill filesystem paths and convert behavior after
platform skill specs converged on agentskills.io.

### What changed

| Area | Change |
|------|--------|
| Convert discovery | Recursive `SKILL.md` search under multi-root tables per platform |
| Nesting layout | Cursor/Codex **preserve** nesting; Copilot/Claude **flatten** to parent folder name |
| Shared / legacy roots | Cursor/Copilot also scan `.agents/skills/`; Codex scans `.agents/skills/` + legacy `.codex/skills/` |
| Install (Codex) | Skills/commands deploy to `.agents/skills/` (project) or `~/.agents/skills/` (user) via `skill_scope` |
| Install (Cursor) | Honor `platforms.cursor.skill_scope` (`.cursor/skills/` vs `~/.cursor/skills/`) |
| Installer | Pass `skill_scope` from package `platforms.<adapter>` into adapter deploy config |
| Scanner | Tag `.github/skills`, `.claude/skills`, `.agents/skills`, legacy `.codex/skills` |
| Docs / regression | Conventions, convert docs, platform pages, release regression procedure |

### What did **not** change

- Skill frontmatter is not rewritten (as-is copy).
- No mapping of platform-specific fields (`paths`, `when_to_use`, `agents/openai.yaml`).
- Codex prompts remain under `~/.codex/prompts/`.
- CLI command layout / `pkg create` / `config set` work stays under **008**.

## User scenarios

### US1 — Convert nested Cursor skills correctly (P1)

**Given** `.cursor/skills/shipping/land-it/SKILL.md`,  
**When** `aam convert -s cursor -t codex --type skill`,  
**Then** output is `.agents/skills/shipping/land-it/` (nesting preserved).  
**When** target is Copilot or Claude Code,  
**Then** output is `.github/skills/land-it/` or `.claude/skills/land-it/` (flattened).

### US2 — Discover shared and legacy Codex roots (P1)

**Given** skills under `.agents/skills/` and legacy `.codex/skills/`,  
**When** converting from Cursor or Codex,  
**Then** both roots are found; duplicates prefer the platform-specific root.

### US3 — Install honors skill_scope (P1)

**Given** package manifest `platforms.codex.skill_scope: project`,  
**When** installing for Codex,  
**Then** skills land in `<project>/.agents/skills/`.  
**Given** `skill_scope: user`,  
**Then** skills land in `~/.agents/skills/`. Legacy `~/.codex/skills/` remains
listable/undeployable for cleanup only.

### US4 — Regression gate for releases (P2)

**Given** the release checklist,  
**When** CI or a developer runs the skill convert regression procedure,  
**Then** automated E2E and unit gates pass, and optional manual TC-S01–TC-S07
can be recorded.

## Implementation map

### Code

- `apps/aam-cli/src/aam_cli/converters/mappings.py` — `SKILL_SOURCE_ROOTS`, `SKILL_PRESERVE_NESTING`
- `apps/aam-cli/src/aam_cli/services/convert_service.py` — discovery, flatten/preserve, collisions
- `apps/aam-cli/src/aam_cli/core/installer.py` — pass `skill_scope`
- `apps/aam-cli/src/aam_cli/adapters/codex.py` — `.agents/skills` deploy + legacy cleanup
- `apps/aam-cli/src/aam_cli/adapters/cursor.py` — honor `skill_scope`
- `apps/aam-cli/src/aam_cli/detection/scanner.py` — platform tagging for skill roots

### Tests

- `apps/aam-cli/tests/unit/test_convert.py` — nested / flatten / roots
- `apps/aam-cli/tests/unit/test_unit_skill_scope_deploy.py` — scope + installer wiring
- `apps/aam-cli/tests/unit/test_adapters_factory.py` — Codex/Cursor destinations
- `apps/aam-cli/tests/unit/test_unit_adapter_lifecycle.py` — undeploy/list new + legacy
- `apps/aam-cli/tests/unit/test_unit_adapter_commands.py` — Codex command skill path
- `apps/aam-cli/tests/integration/test_integration_skill_convert_conventions.py` — E2E conventions

### Specs and docs

- `docs/specs/BIDIRECTIONAL_CONVERSION_CONVENTIONS.md`
- `docs/specs/SKILL_CONVERT_REGRESSION_PROCEDURE.md`
- `docs/specs/SPEC-convert-command.md`
- `docs/user_docs/docs/cli/convert.md`
- `docs/user_docs/docs/cli/create-package.md` (skill detection roots)
- `docs/user_docs/docs/platforms/codex.md`, `copilot.md`
- `docs/user_docs/docs/concepts/platform-adapters.md`
- `CHANGELOG.md`

## Explicitly out of this commit (008 / other)

Keep these on `008-commands-layout` (or a separate commit):

- `apps/aam-cli/README.md` — `pkg create` / command rename docs
- `apps/aam-cli/src/aam_cli/commands/pkg/create.py`
- `apps/aam-cli/src/aam_cli/commands/config/set.py` — `active_platforms` list coerce
- `apps/aam-cli/tests/test_main.py` — config set list coerce test
- `apps/aam-cli/tests/unit/test_unit_pkg_create_uaaps_alignment.py`
- `docs/user_docs/docs/cli/config-set.md`
- `docs/user_docs/docs/platforms/claude.md` — config set serializer note

## Verification

```bash
# Skill convert E2E
cd apps/aam-cli && pytest tests/integration/test_integration_skill_convert_conventions.py -v

# Unit subset
pytest tests/unit/test_convert.py tests/unit/test_unit_skill_scope_deploy.py \
  tests/unit/test_adapters_factory.py tests/unit/test_unit_adapter_lifecycle.py \
  tests/unit/test_unit_adapter_commands.py -v

# Full release gate
cd ../.. && npx nx test aam-cli
```

Baseline (2026-09-19): E2E 8 passed; full suite 803 passed, 3 skipped.

Full release/manual procedure:
[docs/specs/SKILL_CONVERT_REGRESSION_PROCEDURE.md](../../docs/specs/SKILL_CONVERT_REGRESSION_PROCEDURE.md)

## Success criteria

1. Nested Cursor skills preserve path on Codex; flatten on Copilot/Claude.
2. Frontmatter round-trips as-is.
3. Codex install uses `.agents/skills/` (not `~/.codex/skills/`) for new deploys.
4. Cursor `skill_scope` works for project vs user.
5. Regression procedure exists and automated E2E is green.
