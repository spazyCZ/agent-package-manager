# Bidirectional conversion conventions (Claude, Cursor, and UAAPS)

This document defines one canonical mapping for converting artifacts between
Claude Code plugin-style files, Cursor project files, and a UAAPS
intermediate representation (IR). Use these conventions as the source of truth
for converter behavior, warning messages, and expected output paths.

## Scope

This mapping covers only these artifact families:

- instructions
- agents
- prompts
- skills
- plugin metadata and hooks (where representable)

## Required conversion flow

Use UAAPS IR as the mandatory normalization step for all cross-platform
conversions:

1. Parse source platform files (Claude or Cursor).
2. Normalize into UAAPS IR (`package.agent.json` + standard artifact layout).
3. Generate target platform files from UAAPS IR.

This design keeps conversion deterministic and makes repeated conversions
idempotent.

## UAAPS intermediate representation

For conversion, normalize into this minimal UAAPS structure:

```text
<workspace>/
├── package.agent.json
├── agents/
│   └── <name>/
│       ├── agent.yaml
│       └── system-prompt.md
├── prompts/
│   └── <name>.md
├── skills/
│   └── <name>/SKILL.md
└── rules/
    └── <name>/RULE.md
```

The converter must treat this layout as the canonical in-memory model even when
it does not write IR files to disk.

## Platform to UAAPS mapping

The converter must first map source files into UAAPS IR using these rules.

### Claude to UAAPS

| Artifact | Claude source | UAAPS IR target | Conversion type |
|---|---|---|---|
| instruction | `CLAUDE.md` | `rules/claude-global/RULE.md` | lossy |
| instruction | marker section in `CLAUDE.md` | `rules/<marker-id>/RULE.md` | near-lossless |
| agent | `.claude/agents/<name>.md` | `agents/<name>/system-prompt.md` + generated `agent.yaml` | near-lossless |
| prompt | `.claude/prompts/<name>.md` | `prompts/<name>.md` | near-lossless |
| skill | `.claude/skills/<name>/SKILL.md` (+ files) | `skills/<name>/SKILL.md` (+ files) | lossless |

### Cursor to UAAPS

| Artifact | Cursor source | UAAPS IR target | Conversion type |
|---|---|---|---|
| instruction | `.cursor/rules/<name>.mdc` | `rules/<name>/RULE.md` | near-lossless |
| agent | `.cursor/agents/<name>.md` | `agents/<name>/system-prompt.md` + generated `agent.yaml` | near-lossless |
| agent (legacy pattern) | `.cursor/rules/agent-<name>.mdc` | `agents/<name>/system-prompt.md` + generated `agent.yaml` | lossy-context |
| prompt | `.cursor/prompts/<name>.md` | `prompts/<name>.md` | near-lossless |
| command | `.cursor/commands/<name>.md` | `commands/<name>.md` | near-lossless |
| skill | `.cursor/skills/<name>/SKILL.md` (+ files) | `skills/<name>/SKILL.md` (+ files) | lossless |
| skill | `.cursor/skills/<category>/<name>/SKILL.md` | `skills/<category>/<name>/SKILL.md` | lossless (nested) |
| skill | `.agents/skills/<name>/SKILL.md` (+ files) | `skills/<name>/SKILL.md` (+ files) | lossless (shared root) |

### Skill discovery and nesting (convert)

Source roots scanned recursively for `SKILL.md`:

| Platform | Roots (prefer first on duplicate relative paths) |
|---|---|
| Cursor | `.cursor/skills/`, `.agents/skills/` |
| Copilot | `.github/skills/`, `.agents/skills/` |
| Claude | `.claude/skills/` |
| Codex | `.agents/skills/`, legacy `.codex/skills/` |

When writing skills:

| Target | Layout rule |
|---|---|
| Cursor, Codex | Preserve path relative to the source skills root |
| Copilot, Claude | Flatten to the parent folder of `SKILL.md` |

Do not rewrite skill frontmatter. Platform-specific fields pass through as-is.

## UAAPS to Cursor (new agent) mapping

For "new agent in Cursor" output, generate from UAAPS IR as follows:

| UAAPS IR | Cursor target | Rule |
|---|---|---|
| `agents/<name>/system-prompt.md` + `agent.yaml` | `.cursor/agents/<name>.md` | write prompt body as target content; map compatible frontmatter |
| `rules/<name>/RULE.md` | `.cursor/rules/<name>.mdc` | keep frontmatter fields (`description`, `globs`, `alwaysApply`) |
| `prompts/<name>.md` | `.cursor/prompts/<name>.md` | copy as-is |
| `commands/<name>.md` | `.cursor/commands/<name>.md` | copy as-is |
| `skills/<name>/` | `.cursor/skills/<name>/` | copy directory as-is |

When both a UAAPS agent and a same-name UAAPS rule exist, keep both outputs
and do not merge them automatically.

## Canonical path mapping

The converter must use the following path-level mapping.

| Artifact | Claude source | Cursor target | Conversion type |
|---|---|---|---|
| instruction | `CLAUDE.md` | `.cursor/rules/claude-global.mdc` | lossy |
| instruction | `CLAUDE.md` section blocks | `.cursor/rules/<name>.mdc` | lossy |
| instruction | `.claude/CLAUDE.md` | `.cursor/rules/claude-global.mdc` | lossy |
| agent | `.claude/agents/<name>.md` | `.cursor/agents/<name>.md` | near-lossless |
| prompt | `.claude/prompts/<name>.md` | `.cursor/prompts/<name>.md` | near-lossless |
| skill | `.claude/skills/<name>/SKILL.md` (+ files) | `.cursor/skills/<name>/SKILL.md` (+ files) | lossless |
| instruction | `.cursor/rules/<name>.mdc` | `CLAUDE.md` section | lossy |
| agent | `.cursor/agents/<name>.md` | `.claude/agents/<name>.md` | near-lossless |
| prompt | `.cursor/prompts/<name>.md` | `.claude/prompts/<name>.md` | near-lossless |
| prompt | `.cursor/commands/<name>.md` | `.claude/prompts/<name>.md` | lossy-context |
| skill | `.cursor/skills/<name>/SKILL.md` (+ files) | `.claude/skills/<name>/SKILL.md` (+ files) | lossless |

## Frontmatter and metadata mapping

Apply these field mappings when both source and target support frontmatter.

| Source field | Target field | Rule |
|---|---|---|
| `name` | `name` | copy if present |
| `description` | `description` | copy if present |
| `model` | `model` | copy only when target supports same value |
| `readonly` | `readonly` | copy only for agent file targets that support it |
| `is_background` | `is_background` | copy only for agent file targets that support it |
| `tools` | N/A | drop and warn |
| `handoffs` | N/A | drop and warn |
| `user-invokable` | N/A | drop and warn |
| `target` | N/A | drop and warn |

### Instruction-specific metadata

| Cursor field | Claude equivalent | Rule |
|---|---|---|
| `globs` | none | drop; prepend note in converted section |
| `alwaysApply` | implicit always-on | drop; no functional replacement |
| `description` | section heading text | preserve as section title if useful |

## Content wrapping conventions

When writing instruction content into `CLAUDE.md`, always wrap converted blocks
with stable markers:

```markdown
<!-- BEGIN AAM CONVERTED: <id> -->
## <title>
<converted content>
<!-- END AAM CONVERTED: <id> -->
```

When generating `.mdc` from `CLAUDE.md`, use this minimal frontmatter:

```markdown
---
description: "Converted from CLAUDE.md"
alwaysApply: true
---
```

If source content clearly targets a file type, set `alwaysApply: false` and
populate `globs` using best-effort inference. If inference is uncertain, keep
`alwaysApply: true`.

## Bidirectional lossy rules

The converter must emit deterministic warnings for each lossy transform.

| Direction | Loss | Required warning text pattern |
|---|---|---|
| Claude -> Cursor | no native scoped instruction metadata | `Converted global instruction; no source scoping metadata found.` |
| Cursor -> Claude | `globs` dropped | `Glob-scoped rule converted to always-on CLAUDE.md section. Original globs: <value>.` |
| Cursor -> Claude | `alwaysApply` dropped | `alwaysApply metadata is not supported in CLAUDE.md and was removed.` |
| Claude -> Cursor | marker-free mixed manual content split into one rule | `CLAUDE.md mixed content converted as a single global rule.` |
| Cursor commands -> Claude prompts | command invocation semantics lost | `Cursor command converted to Claude prompt text without slash-command binding.` |
| Claude/Cursor -> UAAPS | source lacks explicit structured agent metadata | `Generated agent.yaml from source prompt content; review tools, skills, and parameters.` |
| UAAPS -> Cursor | UAAPS agent tools/parameters not supported in Cursor agent frontmatter | `UAAPS agent fields not supported by Cursor were removed: <field-list>.` |
| Any -> Any | unsupported plugin runtime fields | `Platform-specific runtime metadata removed: <field-list>.` |

## File naming conventions

Use deterministic names so repeated conversions are idempotent.

| Case | Convention |
|---|---|
| unnamed CLAUDE block -> Cursor rule | `claude-global.mdc` |
| marker id exists | `<marker-id>.mdc` |
| scoped package name | keep `author--name` filesystem form |
| agent names | preserve stem exactly, lowercase only if source is mixed-case and target rejects it |

## Conflict and merge conventions

Use these write rules for existing target files:

1. If target does not exist, create it.
2. If target exists and `--force` is false, skip and warn.
3. If target exists and `--force` is true, overwrite.
4. For `CLAUDE.md`, upsert by marker block instead of full overwrite.
5. Never edit content outside converter markers in `CLAUDE.md`.

## Unsupported components

Claude plugin hooks and event automation do not have a first-class Cursor
plugin equivalent. The converter must not fabricate behavior.

- map hook files to a warning-only report entry
- suggest migration to `.cursor/rules` narrative constraints or external scripts
- do not generate fake executable hook stubs unless explicitly requested

## Minimal validation checklist

A converted output is valid when all checks pass:

1. Required target paths are created.
2. Markdown files parse without malformed frontmatter delimiters.
3. Marker pairs in `CLAUDE.md` are balanced.
4. Lossy transforms include warning entries.
5. Re-running conversion without source changes produces no diff.
6. UAAPS IR contains valid `package.agent.json` and expected artifact paths.

For release and regression measurement of skill conversion across Cursor,
Copilot, Claude Code, and Codex, follow
[SKILL_CONVERT_REGRESSION_PROCEDURE.md](SKILL_CONVERT_REGRESSION_PROCEDURE.md).

## End-to-end example (Claude to UAAPS to Cursor)

This example demonstrates the exact conversion flow for creating a new Cursor
agent from a Claude source file.

### Step 1: Source (Claude)

Source file:

`/.claude/agents/security-reviewer.md`

Example content:

```markdown
---
name: security-reviewer
description: Security-focused code reviewer
model: sonnet
tools:
  - filesystem
  - bash
---
You are a security-focused reviewer.
Check for injection risks, secret leaks, and auth flaws.
```

### Step 2: Normalize to UAAPS IR

Generated UAAPS files:

- `package.agent.json` (minimal generated package metadata)
- `agents/security-reviewer/agent.yaml`
- `agents/security-reviewer/system-prompt.md`

Generated `agents/security-reviewer/agent.yaml`:

```yaml
name: security-reviewer
description: Security-focused code reviewer
version: 1.0.0
system_prompt: system-prompt.md
tools:
  - filesystem
  - bash
skills: []
prompts: []
parameters: {}
```

Generated `agents/security-reviewer/system-prompt.md`:

```markdown
You are a security-focused reviewer.
Check for injection risks, secret leaks, and auth flaws.
```

If structured agent fields cannot be inferred from source content, the
converter must create safe defaults and emit this warning:

`Generated agent.yaml from source prompt content; review tools, skills, and parameters.`

### Step 3: Generate target (new Cursor agent)

Output file:

`/.cursor/agents/security-reviewer.md`

Generated content:

```markdown
---
name: security-reviewer
description: Security-focused code reviewer
---
You are a security-focused reviewer.
Check for injection risks, secret leaks, and auth flaws.
```

If UAAPS fields are not supported by Cursor agent frontmatter, drop them and
emit this warning:

`UAAPS agent fields not supported by Cursor were removed: <field-list>.`
