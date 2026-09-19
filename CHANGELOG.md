# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [2026-09-19]

### Added

- Skill convert E2E integration suite:
  `apps/aam-cli/tests/integration/test_integration_skill_convert_conventions.py`.
- Release regression procedure:
  `docs/specs/SKILL_CONVERT_REGRESSION_PROCEDURE.md`.
- Feature spec: `specs/009-skill-path-convert/spec.md`.

## [2026-09-15]

### Changed

- Skill discovery and convert: recursively find `SKILL.md` under each
  platform root; Cursor/Copilot also scan `.agents/skills/`; Codex still
  scans legacy `.codex/skills/`.
- Skill convert layout: Cursor and Codex targets preserve nesting;
  Copilot and Claude targets flatten to the skill folder name.
- Codex install: skills and command-skills deploy to `.agents/skills/`
  (project) or `~/.agents/skills/` (user) via package
  `platforms.codex.skill_scope` (default `project`). Legacy
  `~/.codex/skills/` remains searchable for undeploy/list.
- Cursor install: `platforms.cursor.skill_scope` is honored
  (`.cursor/skills/` vs `~/.cursor/skills/`).
- Installer passes `skill_scope` from the package manifest into adapter
  deploy config.

### Fixed

- Scanner platform tagging for `.github/skills/`, `.claude/skills/`,
  `.agents/skills/`, and legacy `.codex/skills/`.
