# Research: CLI Interface Scaffolding & npm-Style Source Workflow

**Feature Branch**: `004-npm-style-source-workflow`
**Date**: 2026-02-09
**Status**: Complete — all NEEDS CLARIFICATION resolved

---

## R1: Click Custom Group for Categorized Help Output

**Decision**: Implement a custom `OrderedGroup(click.Group)` subclass that overrides `format_commands()` to render commands in labeled sections.

**Rationale**: Click's default `Group.format_commands()` renders a flat alphabetical list. The custom class iterates over a `SECTIONS` dict mapping section names to command lists, using `formatter.section()` for labeled headers.

**Alternatives Considered**:
- **Typer-style subcommand apps**: Rejected — would require migrating from Click, too invasive
- **Custom `format_help()` override**: Rejected — `format_commands()` is the narrower, more maintainable override point
- **Click's `result_callback`**: Rejected — wrong level of abstraction (post-execution, not help formatting)

**Key Implementation Details**:
- `SECTIONS` dict defines display order: "Getting Started" → "Package Management" → "Package Integrity" → "Package Authoring" → "Source Management" → "Configuration" → "Utilities"
- Hidden commands (`hidden=True`) are automatically excluded since `format_commands()` checks `cmd.hidden`
- Commands not listed in any section are silently omitted from help (good for deprecated aliases)
- Renders correctly in 80-column terminals (Click's `HelpFormatter` handles wrapping)

**Code Pattern**:
```python
class OrderedGroup(click.Group):
    SECTIONS = {
        "Getting Started": ["init"],
        "Package Management": ["install", "uninstall", "upgrade", "outdated", "search", "list", "info"],
        "Package Integrity": ["verify", "diff"],
        "Package Authoring": ["pkg"],
        "Source Management": ["source"],
        "Configuration": ["config", "registry"],
        "Utilities": ["mcp", "doctor"],
    }

    def format_commands(self, ctx, formatter):
        for section_name, cmd_names in self.SECTIONS.items():
            commands = []
            for name in cmd_names:
                cmd = self.commands.get(name)
                if cmd and not cmd.hidden:
                    commands.append((name, cmd))
            if commands:
                with formatter.section(section_name):
                    formatter.write_dl([
                        (name, cmd.get_short_help_str(limit=150))
                        for name, cmd in commands
                    ])
```

---

## R2: Deprecated Command Aliases with Click

**Decision**: Use `hidden=True` on deprecated alias commands, print a styled deprecation warning to stderr via `click.echo(err=True)`, and delegate via `ctx.invoke()` with explicit parameter forwarding.

**Rationale**: Click does NOT have a built-in `deprecated=True` parameter. Manual deprecation warnings with `click.style()` provide colored, informative messages while `hidden=True` removes aliases from `--help`.

**Alternatives Considered**:
- **Dynamic `**kwargs` forwarding**: Rejected — loses type safety, `--help` on alias shows no options
- **Click `result_callback` for auto-delegation**: Rejected — doesn't support parameter forwarding
- **Shared function extraction (no ctx.invoke)**: Rejected — duplicates Click parameter validation logic

**Key Implementation Details**:
- Create `utils/deprecation.py` with `print_deprecation_warning(old_cmd, new_cmd, removal_version)`
- Each deprecated alias replicates all `@click.option` decorators from the target (explicit forwarding)
- Deprecation warnings use `click.style(fg="yellow", bold=True)` and write to stderr
- Removal timeline: v0.3.0 (two minor versions of warnings)
- `aam update` is a **silent** hidden alias for `aam upgrade` (no deprecation warning — permanent npm convention alias)

**Special Case — `aam init`**:
- When called **without** arguments: new client initialization behavior
- When called **with** `[name]` argument: prints deprecation warning, delegates to `aam pkg init [name]`
- Detection: `if name:` branch in the command handler

---

## R3: Virtual Package Resolution — Source Artifact Index

**Decision**: Use a nested dict (`dict[str, list[ArtifactEntry]]`) for unqualified name lookup and a flat dict (`dict[str, ArtifactEntry]`) for qualified name lookup. Build index on-demand during `install`, no persistent cache needed.

**Rationale**: O(1) lookups for both qualified and unqualified names. Building is O(n) where n = total artifacts. For 1000 artifacts: ~50ms build time, ~500KB memory. Persistent cache adds complexity with negligible benefit.

**Resolution Order**:
1. **Qualified name** (`openai/skills/code-review`): Direct source index lookup, bypass registries
2. **Registry lookup** (unqualified): Try all configured registries in config order
3. **Source fallback** (unqualified): Try source index, first match wins + warning if ambiguous

**Alternatives Considered**:
- **Registry-source parity** (equal priority): Rejected — unpredictable, breaking if registry adds same-name package
- **Interactive disambiguation prompt**: Rejected — breaks scripting/automation
- **Persistent index cache**: Deferred — negligible performance gain at v1 scale

**Key Implementation Details**:
- `build_source_index()` added to `services/source_service.py` — reuses existing `scan_source()` logic
- `resolve_artifact()` function handles the 3-level resolution with appropriate error messages
- Each artifact entry carries: `name`, `qualified_name`, `source_name`, `type`, `path`, `commit_sha`, `cache_dir`, `description`
- When multiple sources match unqualified name: use first match (config order), log warning suggesting qualified name
- Error messages include actionable suggestions: `aam source update`, `aam search`, qualified name syntax

**Auto-Generated Manifest**:
- Version format: `0.0.0` (synthetic — source packages don't have semver)
- Provenance: `source_type: git`, `source_url`, `source_ref`, `source_commit`, `fetched_at`
- Single artifact per package (matches source scanner output)
- No dependencies declared (source artifacts don't declare deps)
- Uses existing `Provenance` model from `core/manifest.py`

**Atomic Install from Source**:
- Uses existing staging pattern from `install_service.py` (`.aam/.tmp/`)
- Sequence: stage → copy files → write manifest → compute checksums → move to final → deploy → update lock
- Rollback: backup existing package, restore on failure, clean staging

---

## R4: Interactive Client Initialization (`aam init`)

**Decision**: Use Click's `click.prompt()` + Rich's `Console.print()` for interactive flow. No new dependencies (avoid `questionary`/`InquirerPy`). Multi-select implemented as numbered list with Rich formatting.

**Rationale**: Constitution says minimize dependencies. Click + Rich are already in `pyproject.toml`. The init flow is simple enough that `click.prompt()` with `type=click.Choice()` handles single-select, and a numbered list with `click.prompt("Enter numbers")` handles multi-select.

**Alternatives Considered**:
- **`questionary` library** (checkbox prompts): Rejected — new dependency, constitution discourages unnecessary deps
- **`InquirerPy`**: Rejected — same concern, also has complex terminal requirements
- **Pure Rich `Prompt.ask()`**: Considered — but Click's prompt integrates better with Click context

**Key Implementation Details**:
- Platform selection: `click.prompt("Choose platform", type=click.Choice(["cursor", "copilot", "claude", "codex"]))`
- Registry setup: Numbered options (1: create local, 2: add existing, 3: skip)
- Community sources: Display numbered list, user enters comma-separated numbers to select
- `--yes` flag: Skip all prompts, use defaults (first detected platform, skip registry, add all default sources)
- Existing config detection: Check `~/.aam/config.yaml` exists, offer per-section reconfigure/skip
- Creates config via existing `save_global_config()` from `core/config.py`

**Service Layer**: `services/client_init_service.py` handles business logic:
- `detect_platform()`: Check for `.cursor/`, `.github/copilot/`, `CLAUDE.md`, `.codex/` directories
- `setup_registry()`: Call existing `registry init`/`registry add` logic
- `setup_sources()`: Call existing `source_service.register_default_sources()`
- Returns structured result for CLI to display "Next steps" summary

---

## R5: Outdated Detection and Upgrade Commands

**Decision**: `aam outdated` compares stored `source_commit` in lock file against source cache HEAD SHA, grouped by source for efficiency. `aam upgrade` reuses spec 003's modification check + backup flow. Both use `upgrade_service.py` with the existing workspace lock pattern.

**Rationale**: Commit SHA comparison is fast (no network, no re-scan). Grouping by source means one cache read per source regardless of package count. Reusing spec 003's upgrade warning flow ensures consistency.

**Alternatives Considered**:
- **Full re-scan on outdated check**: Rejected — too slow, unnecessary when commit SHA comparison suffices
- **Network-based freshness check**: Rejected — violates offline-capable constraint (NFR-003)
- **Semver-style version comparison for source packages**: Rejected — misleading since commits don't follow semver

**Key Implementation Details**:

### `aam outdated`
- Data model: `OutdatedPackage` dataclass with `name`, `current_commit`, `latest_commit`, `source_name`, `has_local_modifications`
- Algorithm: Read lock file → group by source → get HEAD SHA per source cache → compare → report
- Stale source warning: If `last_fetched` > 7 days, warn user to run `aam source update`
- JSON output (`--json`): Structured dict with `outdated`, `up_to_date`, `no_source` lists
- Packages without `source_name`/`source_commit` in lock file: reported as "(no source)"

### `aam upgrade`
- Implicit source update: **No** — keep it explicit like apt. User must run `aam source update` first.
- Modification handling: Reuse `checksum_service.check_modifications()` and `create_backup()`
- Interactive prompt for modified packages: backup/skip/diff/force (same as spec 003 install --force)
- `--dry-run`: Read-only analysis, return "would_upgrade" result
- `--force`: Skip modification warnings
- Partial failures: Continue processing remaining packages, report successes/failures/skips at end
- Thread safety: Use `_workspace_lock` pattern from `install_service.py`

### Lock File Extension
```python
class LockedPackage(BaseModel):
    # ... existing fields ...
    source_name: str | None = None       # "openai/skills" — NEW
    source_commit: str | None = None     # Full SHA (40 chars) — NEW
```
- Both fields are `Optional` for backward compatibility
- Populated during `install_from_source()`, `None` for registry installs

---

## R6: MCP Tool Extensions

**Decision**: Add 3 new MCP tools following the existing tool pattern in `mcp/tools_read.py` and `mcp/tools_write.py`.

**Rationale**: Existing MCP infrastructure in `mcp/server.py` uses `register_read_tools()` / `register_write_tools()` with tag-based gating. New tools follow the same pattern.

**Key Implementation Details**:
- `aam_outdated` (read tool): Calls `check_outdated()` from upgrade service, returns structured dict
- `aam_available` (read tool): Calls `build_source_index()` from source service, returns all installable artifacts grouped by source
- `aam_upgrade` (write tool): Calls `upgrade_packages()` from upgrade service, gated by `--allow-write`

---

## Open Questions — Resolved

| # | Question | Resolution | Rationale |
|---|----------|------------|-----------|
| 1 | Auto-deploy on install from source? | **Yes** | Install means "ready to use" — consistent with registry install behavior |
| 2 | Version display for source packages? | **`0.0.0` in manifest, `source@abc123` in display** | Manifest needs valid semver; display shows actual provenance |
| 3 | Should `aam init` detect `aam.yaml`? | **Yes — ask "Did you mean `aam pkg init`?"** | Prevents confusion without silent wrong behavior |
| 4 | Should `aam install` auto-update sources? | **No** | Keep explicit like apt; add `--refresh` flag in future |
| 5 | Deprecation removal timeline? | **v0.3.0** | Two minor versions of deprecation warnings before removal |
| 6 | New dependency for interactive prompts? | **No** | Use Click + Rich (already in pyproject.toml) |
| 7 | Persistent source index cache? | **No (deferred)** | Build on-demand is fast enough (~50ms for 1000 artifacts) |
| 8 | Implicit `source update` in `aam upgrade`? | **No** | Keep explicit, suggest `aam source update` if sources are stale |
