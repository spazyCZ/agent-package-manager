# Tasks: Improve Search Command UX

**Input**: Design documents from `/specs/005-improve-search-ux/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/search-service.md, quickstart.md

**Tests**: Included — the spec requires test-driven quality (constitution principle IV), and the plan explicitly lists test cases.

**Organization**: Tasks are grouped by implementation phase. Because multiple P1 user stories (US1, US2, US3, US7) share the same files (`search_service.py`, `search.py`), they are implemented together in the service and command rewrite phases. P2 stories (US4, US5, US6) are integrated during those same rewrites but have dedicated verification tasks.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

All paths are relative to `apps/aam-cli/`:
- **Source**: `src/aam_cli/`
- **Tests**: `tests/unit/`
- **Docs**: `docs/user_docs/docs/cli/`

---

## Phase 1: Setup

**Purpose**: No project initialization needed — this is an enhancement to an existing app. Verify branch is clean and tests pass.

- [X] T001 Verify existing tests pass by running `npx nx test aam-cli` on branch `005-improve-search-ux`

---

## Phase 2: Foundational (Shared Utilities & Models)

**Purpose**: Create the utility module and Pydantic models that ALL user stories depend on. Must complete before any story implementation.

**CRITICAL**: No user story work can begin until this phase is complete.

### Tests for Foundational

- [X] T002 [P] Create unit tests for `find_similar_names()` in `apps/aam-cli/tests/unit/test_unit_text_match.py` — test cases: exact typo match ("chatbt" → "chatbot-agent"), no match ("xyz" → empty), multiple suggestions sorted by similarity, threshold filtering, max_suggestions limit, case-insensitive matching, empty names list, empty query

### Implementation for Foundational

- [X] T003 [P] Create `apps/aam-cli/src/aam_cli/utils/text_match.py` — implement `find_similar_names()` using `difflib.SequenceMatcher.ratio()` with constants `SUGGESTION_THRESHOLD = 0.6` and `MAX_SUGGESTIONS = 3`. Include module-level logger, type hints, Google-style docstring, 80-char section headers per constitution. See contracts/search-service.md for full signature.

- [X] T004 Add Pydantic models `SearchResult` and `SearchResponse` plus scoring constants (`SCORE_EXACT_NAME = 100`, `SCORE_NAME_PREFIX = 80`, `SCORE_NAME_CONTAINS = 60`, `SCORE_KEYWORD_MATCH = 50`, `SCORE_DESCRIPTION_CONTAINS = 30`) and validation constants (`VALID_ARTIFACT_TYPES`, `VALID_SORT_OPTIONS`) to `apps/aam-cli/src/aam_cli/services/search_service.py`. Preserve existing `MIN_SEARCH_LIMIT`, `MAX_SEARCH_LIMIT`, `DEFAULT_SEARCH_LIMIT`. See data-model.md for all field definitions and validation rules.

- [X] T005 Implement `compute_relevance_score()` function in `apps/aam-cli/src/aam_cli/services/search_service.py` — tiered scoring: exact name (100) → prefix (80) → substring (60) → keyword (50) → description (30) → no match (0). Empty query returns 100 (browse mode). See contracts/search-service.md for exact signature and behavior.

- [X] T006 [P] Write unit tests for `compute_relevance_score()` in `apps/aam-cli/tests/unit/test_services_search.py` — test cases: exact name match, prefix match, substring match, keyword match, description-only match, no match returns 0, empty query returns max score, case-insensitive behavior, highest-tier-wins (name+description returns name score only)

**Checkpoint**: Utilities and models ready. `find_similar_names()` and `compute_relevance_score()` both tested independently. Service rewrite can now begin.

---

## Phase 3: US3 — Unified Service Layer (Priority: P1) — MVP

**Goal**: Rewrite `search_packages()` to search both registries AND sources in a single operation, returning `SearchResponse` with scored results, warnings, and total count. This is the foundational change that enables US1 (ranking), US2 (source-only search), US7 (visible warnings), US4 (filtering), and US6 (sorting).

**Independent Test**: Call `search_packages()` from the service layer with a config containing both registries and sources. Verify it returns `SearchResponse` with results from both, scored by relevance, with `total_count` and empty `warnings`.

### Tests for US3

- [X] T007 Write unit tests for the rewritten `search_packages()` in `apps/aam-cli/tests/unit/test_services_search.py`. Update existing 5 tests to match `SearchResponse` return type. Add new tests: `test_unit_search_sources_included` (results include source artifacts), `test_unit_search_sources_only_no_registry` (works with zero registries if sources exist — US2), `test_unit_search_no_sources_no_registries_error` (raises ValueError when both empty — US2), `test_unit_search_source_failure_warning` (warning string in response.warnings on source failure — US7), `test_unit_search_registry_failure_warning` (warning on registry failure — US7), `test_unit_search_total_count_with_limit` (total_count > len(results) when truncated), `test_unit_search_all_names_on_empty_results` (all_names populated when 0 results), `test_unit_search_empty_query_browse` (empty query returns all packages scored equally), `test_unit_search_relevance_exact_name_first` (exact name scores 100 — US1), `test_unit_search_relevance_prefix_before_substring` (prefix 80 > substring 60 — US1), `test_unit_search_relevance_name_before_description` (name 60 > description 30 — US1), `test_unit_search_type_filter_multiple` (multi-type OR filtering — US4), `test_unit_search_source_filter` (source_filter limits to one source — US4), `test_unit_search_registry_filter` (registry_filter limits to one registry — US4), `test_unit_search_unknown_type_warning` (warning for invalid type — US4), `test_unit_search_unknown_source_warning` (warning for non-existent source — US4), `test_unit_search_sort_name` (alphabetical — US6), `test_unit_search_sort_recent` (most recent first — US6), `test_unit_search_sort_relevance_default` (relevance by default — US6), `test_unit_search_invalid_sort_raises` (ValueError for bad sort), `test_unit_search_response_model_validation` (Pydantic model validates correctly), `test_unit_search_special_characters_in_query` (query with special chars `@`, `#`, `[`, etc. does not crash — EC-005), `test_unit_search_duplicate_names_across_origins` (same package name from registry and source both appear with distinct `origin`/`origin_type` fields), `test_unit_search_limit_exceeds_total` (limit=100 with only 5 results returns all 5, total_count=5, no error)

### Implementation for US3

- [X] T008 [US3] Rewrite `search_packages()` in `apps/aam-cli/src/aam_cli/services/search_service.py` — replace the existing function body with the full unified implementation per contracts/search-service.md: (1) validate limit/sort_by, (2) validate package_types with warnings, (3) validate source_filter/registry_filter with warnings, (4) error when no registries AND no sources (US2), (5) search registries converting PackageIndexEntry → SearchResult with score, catching (ValueError, OSError, KeyError) per source and adding warnings (US7), (6) search sources via build_source_index() converting VirtualPackage → SearchResult with score, catching (ValueError, OSError) and adding warnings (US7), (7) apply package_types filter (OR logic — US4), (8) sort by sort_by: relevance (score desc, name asc), name (asc), recent (updated_at desc) (US6), (9) compute total_count before limit, (10) apply limit, (11) populate all_names when results empty (US5), (12) return SearchResponse. Import `build_source_index` from `source_service`. Remove old function body entirely.

- [X] T009 [US3] Run `npx nx test aam-cli` and verify all new and updated tests pass for the service layer

**Checkpoint**: Service layer complete. `search_packages()` returns `SearchResponse` with unified results from registries + sources. All P1 stories (US1 ranking, US2 source-only, US3 unified, US7 warnings) are functional at the service level. P2 stories (US4 filtering, US5 suggestions data, US6 sorting) are also functional at the service level.

---

## Phase 4: US1 — Relevance Ranking + Tabular Display (Priority: P1)

**Goal**: Rewrite the CLI command to be a thin presentation layer — Rich Table display with relevance-ranked results, new Click options, warning display, "Showing X of Y", and JSON envelope output.

**Independent Test**: Run `aam search chatbot` against a registry with multiple packages. Verify results appear in a Rich Table sorted by relevance score (exact > prefix > substring > description), with aligned columns for Name, Version, Type, Source, Description.

### Implementation for US1

- [X] T010 [US1] Rewrite `apps/aam-cli/src/aam_cli/commands/search.py` — remove ALL inline search logic (registry loop, source search, type filtering, result combining). Replace with: (1) Click options: change `--type` to `multiple=True` (tuple), add `--source`/`-s` (string), `--registry`/`-r` (string), `--sort` (`click.Choice(["relevance", "name", "recent"])`, default "relevance"), (2) call `search_packages()` from service with all params, (3) handle ValueError from service (no sources configured — US2) as error message, (4) display `response.warnings` as `[yellow]Warning:[/yellow]` lines, (5) JSON output path: serialize SearchResponse as `{"results": [...], "total_count": N, "warnings": [...]}` envelope (US7/R-007), (6) empty results path: call `find_similar_names(query, response.all_names)` and display suggestions (US5), (7) Rich Table with columns: Name (cyan, bold, no_wrap), Version (dim, 12 max, no_wrap), Type (16 max), Source (magenta, 20 max), Description (dim, flexible) per research.md R-003, (8) table title: `Search results for "query" (showing X of Y)` when total_count > len(results), otherwise `Search results for "query" (Y matches)` (FR-015).

- [X] T011 [US1] Run `npx nx test aam-cli` and verify all existing CLI-related tests still pass (no regressions from command rewrite)

**Checkpoint**: CLI displays relevance-ranked results in a scannable Rich Table. US1 acceptance scenarios verifiable. US2 (source-only) works end-to-end. US7 (warnings) visible in output. US4 (filtering), US5 (suggestions), US6 (sorting) all work through new CLI options.

---

## Phase 5: US3 (continued) — MCP Tool Update (Priority: P1)

**Goal**: Update the MCP tool to use the new `search_packages()` signature and return structured `SearchResponse`, ensuring CLI and MCP return identical results.

**Independent Test**: Call `aam_search()` MCP tool with a query and verify it returns `{"results": [...], "total_count": N, "warnings": [...]}` with the same result set as the CLI for the same query.

### Tests for US3 MCP

- [X] T012 [P] [US3] Update MCP search tests in `apps/aam-cli/tests/unit/test_mcp_tools_read.py` — update `aam_search` test to expect `dict` return (not `list`), add test for new parameters (`package_types`, `source_filter`, `registry_filter`, `sort_by`), verify response structure has `results`, `total_count`, `warnings` keys

### Implementation for US3 MCP

- [X] T013 [US3] Update `aam_search()` in `apps/aam-cli/src/aam_cli/mcp/tools_read.py` — change signature to accept `package_types: list[str] | None = None`, `source_filter: str | None = None`, `registry_filter: str | None = None`, `sort_by: str = "relevance"`. Remove old `package_type: str | None` param. Call `search_packages()` with new params. Serialize `SearchResponse` to dict via `.model_dump()` and return. Update return type annotation to `dict[str, Any]`.

- [X] T014 [US3] Run `npx nx test aam-cli` and verify MCP tests pass

**Checkpoint**: MCP and CLI return identical results. US3 fully complete — both consumers share the unified service layer.

---

## Phase 6: US5 — "Did You Mean?" Suggestions (Priority: P2)

**Goal**: Verify that misspelled queries surface helpful suggestions using the `find_similar_names()` utility integrated in Phase 4.

**Independent Test**: Run `aam search chatbt` against a source containing "chatbot-agent" and verify output shows `Did you mean: chatbot-agent?`

- [X] T015 [US5] Verify "Did you mean?" behavior end-to-end: confirm that the command from T010 correctly calls `find_similar_names()` when `response.results` is empty and `response.all_names` is populated, and displays up to 3 suggestions. If the integration is incomplete, add/fix the suggestion display logic in `apps/aam-cli/src/aam_cli/commands/search.py`.

**Checkpoint**: US5 acceptance scenarios verifiable — misspelled queries show suggestions, no-match queries without similar names show plain message.

---

## Phase 7: US4 — Filtering Verification (Priority: P2)

**Goal**: Verify that multi-type filtering, source filtering, and registry filtering work end-to-end through the CLI.

**Independent Test**: Run `aam search data --type skill --type agent` and verify only matching types appear. Run `aam search doc --source google-gemini` and verify only that source's results appear.

- [X] T016 [US4] Verify filtering behavior end-to-end: confirm `--type` multiple values, `--source` filter, `--registry` filter, and invalid filter warnings all work correctly through the CLI command. If any filtering path is incomplete, fix in `apps/aam-cli/src/aam_cli/commands/search.py`.

**Checkpoint**: US4 acceptance scenarios verifiable — multi-type, source, and registry filtering all work.

---

## Phase 8: US6 — Sorting Verification (Priority: P2)

**Goal**: Verify that `--sort name`, `--sort recent`, and default `--sort relevance` all produce correctly ordered results.

**Independent Test**: Run `aam search agent --sort name` and verify alphabetical order. Run with `--sort recent` and verify most-recent-first.

- [X] T017 [US6] Verify sorting behavior end-to-end: confirm `--sort name` (alphabetical), `--sort recent` (newest first), and default `--sort relevance` (score descending, name ascending tiebreak) all work correctly through the CLI. If any sort path is incomplete, fix in `apps/aam-cli/src/aam_cli/commands/search.py`.

**Checkpoint**: US6 acceptance scenarios verifiable — all three sort modes work correctly.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Documentation updates (constitution principle VIII) and final cleanup.

- [X] T018 [P] Update user documentation in `docs/user_docs/docs/cli/search.md` — (1) add `--source`, `--registry`, `--sort` to Options table, (2) update `--type` to mention `multiple=True` repeatable usage, (3) add Example for multi-type filter (`aam search data --type skill --type agent`), (4) add Example for source filter (`aam search doc --source google-gemini`), (5) add Example for sorting (`aam search agent --sort name`), (6) update JSON output example with envelope structure (`{"results": [...], "total_count": N, "warnings": []}`), (7) add "Relevance scoring" section explaining tiered scoring, (8) add "Did you mean?" section, (9) update "Result ordering" section, (10) document JSON breaking change (flat array → envelope), (11) update "Future Enhancements" to remove now-implemented items

- [X] T019 [P] Run full test suite `npx nx test aam-cli` and verify all tests pass with no regressions

- [X] T020 Run linter `npx nx lint aam-cli` and fix any style issues in modified files

- [X] T021 Review all modified files for constitution compliance: module-level loggers, type hints on all signatures, Google-style docstrings, 80-char section headers, no print(), no bare except, specific exception handling, structured logging at entry/exit/error

---

## Phase 10: Evaluation & Acceptance Criteria Validation

**Purpose**: Validate success criteria SC-001, SC-005, and SC-007 that require measurement beyond unit tests.

- [X] T022 [SC-001] Create a ranking accuracy evaluation dataset in `apps/aam-cli/tests/evals/datasets/search_ranking_dataset.py` — at least 10 query-expected-top-3 pairs covering exact name, prefix, substring, keyword, and description matches. Manually verify that `compute_relevance_score()` places the expected package in the top 3 for ≥90% of cases (SC-001: 90% top-3 accuracy).

- [X] T023 [SC-005] Create a suggestion hit-rate evaluation dataset in `apps/aam-cli/tests/evals/datasets/search_suggestion_dataset.py` — at least 10 misspelled-query-expected-suggestion pairs. Manually verify that `find_similar_names()` returns the intended package for ≥80% of cases (SC-005: 80% suggestion hit rate).

- [X] T024 [SC-007] Add a performance benchmark test in `apps/aam-cli/tests/unit/test_services_search.py` — `test_unit_search_performance_under_2s`: create a mock config with 500 packages across 3 registries and 2 sources, time a `search_packages()` call, assert completion in <2 seconds (SC-007: <2s response time for 500 packages).

**Checkpoint**: All measurable success criteria (SC-001, SC-005, SC-007) have been validated with concrete evidence.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — verify baseline
- **Foundational (Phase 2)**: Depends on Phase 1 — creates shared utilities and models
- **US3 Service (Phase 3)**: Depends on Phase 2 — rewrites service using new models and scoring
- **US1 CLI (Phase 4)**: Depends on Phase 3 — rewrites command using new service
- **US3 MCP (Phase 5)**: Depends on Phase 3 — can run in parallel with Phase 4
- **US5 Verify (Phase 6)**: Depends on Phase 4 — verifies suggestion display
- **US4 Verify (Phase 7)**: Depends on Phase 4 — verifies filtering display
- **US6 Verify (Phase 8)**: Depends on Phase 4 — verifies sorting display
- **Polish (Phase 9)**: Depends on all previous phases (1-8)
- **Evaluation (Phase 10)**: Depends on Phase 2 (scoring + suggestions implemented) and Phase 3 (service layer). Can run in parallel with Phases 6-9

### User Story Delivery Map

| Story | Service (Phase 3) | CLI (Phase 4) | MCP (Phase 5) | Verify | Docs (Phase 9) |
|-------|-------------------|---------------|----------------|--------|-----------------|
| US1 (P1) Ranking | T008 | T010 | — | — | T018 |
| US2 (P1) Source-only | T008 | T010 | T013 | — | T018 |
| US3 (P1) Unified | T008 | T010 | T013 | — | T018 |
| US4 (P2) Filtering | T008 | T010 | T013 | T016 | T018 |
| US5 (P2) Suggestions | T008 | T010 | — | T015 | T018 |
| US6 (P2) Sorting | T008 | T010 | T013 | T017 | T018 |
| US7 (P1) Warnings | T008 | T010 | T013 | — | T018 |

### Within Each Phase

- Tests written FIRST, verified to fail before implementation
- Models/utilities before service logic
- Service before consumers (CLI, MCP)
- Core implementation before integration verification

### Parallel Opportunities

- **Phase 2**: T002 (text_match tests) and T003 (text_match impl) can run in parallel with T004+T005+T006 (scoring)
- **Phase 4 + Phase 5**: CLI rewrite (T010) and MCP update (T012+T013) can run in parallel (different files, both depend only on Phase 3)
- **Phase 6 + Phase 7 + Phase 8**: Verification tasks T015, T016, T017 can run in parallel (read-only verification)
- **Phase 9**: T018 (docs) and T019 (test suite) can run in parallel
- **Phase 10**: T022, T023, T024 can all run in parallel with each other and with Phases 6-9

---

## Parallel Example: Phase 2 (Foundational)

```text
# Parallel batch 1 — different files:
Task T002: "Unit tests for find_similar_names() in tests/unit/test_unit_text_match.py"
Task T003: "Create text_match.py in src/aam_cli/utils/text_match.py"
Task T006: "Unit tests for compute_relevance_score() in tests/unit/test_services_search.py"

# Sequential (depends on above):
Task T004: "Add Pydantic models + constants to search_service.py"
Task T005: "Implement compute_relevance_score() in search_service.py"
```

## Parallel Example: Phase 4 + Phase 5

```text
# These phases can overlap (different files):
Task T010: "Rewrite commands/search.py" (CLI)
Task T012+T013: "Update mcp/tools_read.py" (MCP)
```

---

## Implementation Strategy

### MVP First (Phases 1-4: US1+US2+US3+US7)

1. Complete Phase 1: Verify baseline
2. Complete Phase 2: Utilities and models
3. Complete Phase 3: Service layer rewrite (ALL P1 stories functional at service level)
4. Complete Phase 4: CLI rewrite (ALL P1 stories functional end-to-end)
5. **STOP and VALIDATE**: All P1 stories independently testable
   - `aam search chatbot` → ranked results in table (US1)
   - `aam search doc` with sources only → results appear (US2)
   - Service layer called by both CLI and MCP (US3)
   - Corrupted source → visible warning (US7)

### Incremental Delivery

1. Phases 1-4 → P1 stories complete → MVP deployable
2. Phase 5 → MCP parity → US3 fully complete
3. Phases 6-8 → P2 verification → US4/US5/US6 confirmed
4. Phase 9 → Docs + polish → Feature complete
5. Phase 10 → Eval datasets + performance benchmark → Success criteria validated (SC-001, SC-005, SC-007)

### Suggested MVP Scope

**Phases 1-4** (tasks T001-T011) deliver all four P1 stories as a cohesive unit. This is the minimum viable increment that transforms the search experience.

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks in the same phase
- [US?] label maps task to the primary user story it serves
- [SC-???] label maps task to the success criterion it validates
- T008 (service rewrite) is the highest-risk, highest-value task — it implements the core logic for 6 of 7 user stories
- T010 (command rewrite) is the second-highest-risk task — it replaces all display logic
- Phases 6-8 are verification-only — the actual implementation happens in Phases 3-4
- Phase 10 validates measurable success criteria (SC-001, SC-005, SC-007) with concrete datasets and benchmarks
- The JSON output format is a breaking change (flat array → envelope) — documented in T018
- No new PyPI dependencies — uses stdlib `difflib` + existing `rich`
- Total tasks: 24 (T001-T024)
