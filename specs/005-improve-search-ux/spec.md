# Feature Specification: Improve Search Command UX

**Feature Branch**: `005-improve-search-ux`  
**Created**: 2026-02-10  
**Status**: Draft  
**Input**: User description: "Improve search command UX based on analysis of current implementation — relevance ranking, unified service layer, better display, enhanced filtering, and graceful error handling"

## Background & Analysis

The `aam search` command is the primary discovery mechanism for users finding packages and artifacts. An analysis of the current implementation (branch `004-npm-style-source-workflow`) revealed twelve areas for improvement spanning architecture, search quality, result presentation, and error handling.

### Current State Summary

- Search performs case-insensitive substring matching on package name, description, and keywords
- Results come from two sources: configured registries and git source artifacts
- Output is plain Rich-formatted text (no tables, no alignment)
- The command file contains inline business logic that duplicates and diverges from the existing search service
- Results are unranked — registry results always appear before source results regardless of relevance
- Search fails entirely when no registries are configured, even if git sources exist
- Source search errors are silently swallowed
- No pagination, no sorting, no multi-type filtering, no fuzzy matching

### Key Problems (Ranked by User Impact)

1. **Results are unranked** — an exact name match can appear below a weak description match
2. **Search blocks entirely** when no registries configured, even with sources available
3. **Service layer is bypassed** — command duplicates logic, making the MCP server unable to search sources
4. **Display is hard to scan** — no table layout, no alignment, no total-vs-shown count
5. **Errors vanish silently** — source search failures logged at DEBUG only
6. **Limited filtering** — single type only, no source/registry scoping
7. **No guidance on empty results** — no suggestions, no fuzzy matching

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Finding the Best Match Quickly (Priority: P1)

A developer searches for "chatbot" and expects the most relevant results to appear at the top — exact name matches first, then partial name matches, then description-only matches. They want to scan a clean, aligned table and immediately identify which package to install.

**Why this priority**: Relevance ranking is the single highest-impact improvement. Without it, users must mentally re-sort every result set. Combined with better display, this transforms the core search experience.

**Independent Test**: Can be fully tested by running `aam search chatbot` against a registry with 10+ packages and verifying that exact name matches rank above partial matches, and partial name matches rank above description-only matches. Delivers immediate value by surfacing the right package first.

**Acceptance Scenarios**:

1. **Given** a registry containing packages named "chatbot-agent", "advanced-chatbot", and a package with "chatbot" only in its description, **When** the user runs `aam search chatbot`, **Then** "chatbot-agent" appears before "advanced-chatbot" (prefix match beats substring), and both appear before the description-only match.
2. **Given** a registry containing a package named exactly "audit", **When** the user runs `aam search audit`, **Then** the exact name match appears as the first result.
3. **Given** search results exist, **When** results are displayed, **Then** they appear in a tabular format with aligned columns for Name, Version, Type, Source, and Description.
4. **Given** 25 total matches and the default limit of 10, **When** the user runs `aam search agent`, **Then** the output header shows "Showing 10 of 25 results" and suggests using `--limit` to see more.

---

### User Story 2 — Searching Sources Without Registries (Priority: P1)

A new user has configured git sources (e.g., `openai/skills`, `google-gemini/gemini-cli`) but has not yet set up any registry. They run `aam search doc` and expect to find source artifacts instead of seeing a blocking error.

**Why this priority**: This is a functional bug — search should work with any configured package source, not just registries. New users following the quick-start guide hit this immediately.

**Independent Test**: Can be fully tested by configuring only git sources (no registries), running `aam search <query>`, and verifying results from sources are returned. Delivers value by unblocking the primary discovery flow for source-only setups.

**Acceptance Scenarios**:

1. **Given** no registries are configured but two git sources are configured, **When** the user runs `aam search doc`, **Then** results from git sources are displayed (not an error message).
2. **Given** no registries AND no sources are configured, **When** the user runs `aam search anything`, **Then** a helpful error message explains that no package sources are configured and suggests running both `aam source enable-defaults` and `aam registry init`.
3. **Given** both registries and sources are configured, **When** the user runs `aam search doc`, **Then** results from both registries and sources are combined and ranked by relevance.

---

### User Story 3 — Unified Search for CLI and MCP (Priority: P1)

A developer uses the AAM MCP server from their AI coding assistant and expects the same search results as the CLI. Currently the MCP server calls the search service, which only searches registries — it misses all source artifacts.

**Why this priority**: Two different consumers (CLI and MCP) return different results for the same query, which is confusing and breaks trust. Unifying the logic in the service layer fixes this and reduces maintenance burden.

**Independent Test**: Can be fully tested by calling `search_packages()` from the service layer and verifying it returns results from both registries and sources. Delivers value by ensuring all consumers get consistent, complete results.

**Acceptance Scenarios**:

1. **Given** registries and sources are both configured, **When** the search service function is called with a query, **Then** results include both registry packages and source artifacts.
2. **Given** the CLI command runs a search, **When** examining the code path, **Then** the command delegates all search logic to the service layer and only handles display formatting.
3. **Given** the search service receives a limit of 0 or 51, **When** the service validates the input, **Then** it raises a clear validation error.

---

### User Story 4 — Filtering by Type and Source (Priority: P2)

A user wants to find only "skill" artifacts from a specific source. They use `--type skill --type prompt` to find artifacts matching multiple types, and `--source openai` to scope their search to a specific provider.

**Why this priority**: Filtering is important for power users managing many sources, but basic search works without it. This builds on the unified service layer from Story 3.

**Independent Test**: Can be fully tested by running `aam search data --type skill --type agent` and `aam search doc --source google-gemini` and verifying correct filtering. Delivers value by reducing noise in large result sets.

**Acceptance Scenarios**:

1. **Given** packages with types "skill", "agent", and "prompt" exist, **When** the user runs `aam search data --type skill --type agent`, **Then** only packages containing "skill" or "agent" types are shown (not "prompt"-only packages).
2. **Given** multiple sources are configured, **When** the user runs `aam search doc --source google-gemini`, **Then** only results from the "google-gemini" source are shown.
3. **Given** multiple registries are configured, **When** the user runs `aam search audit --registry local`, **Then** only results from the "local" registry are shown.
4. **Given** the user provides a `--source` name that doesn't match any configured source, **When** the search runs, **Then** a warning is displayed: "Source 'xyz' not found. Available sources: ..."

---

### User Story 5 — Understanding Empty Results (Priority: P2)

A user misspells a query (e.g., `aam search chatbt`) and gets zero results. Instead of a bare "No packages found" message, they see a helpful suggestion: "Did you mean: chatbot?"

**Why this priority**: Empty-result guidance significantly reduces user frustration and helps users self-correct. This is medium effort (requires building a name index for similarity comparison) but high perceived quality.

**Independent Test**: Can be fully tested by running a misspelled query and verifying that suggestions appear based on the available package index. Delivers value by turning dead-end searches into successful discoveries.

**Acceptance Scenarios**:

1. **Given** a package "chatbot-agent" exists, **When** the user runs `aam search chatbt`, **Then** the output shows "No packages found matching 'chatbt'. Did you mean: chatbot-agent?"
2. **Given** no similar packages exist for a query, **When** the user runs `aam search xyznonexistent`, **Then** the output shows "No packages found matching 'xyznonexistent'." without a "Did you mean?" suggestion.
3. **Given** multiple similar names exist, **When** the user runs a misspelled query, **Then** up to 3 suggestions are shown, ordered by similarity.

---

### User Story 6 — Sorting Results (Priority: P2)

A user wants to see the most recently updated packages first, or sort alphabetically for easier scanning. They use `--sort recent` or `--sort name` to control the result order.

**Why this priority**: Sorting is useful for power users and becomes increasingly important as the package ecosystem grows. It builds naturally on the relevance scoring from Story 1.

**Independent Test**: Can be fully tested by running `aam search agent --sort name` and verifying alphabetical order, or `--sort recent` and verifying date order. Delivers value by giving users control over how they browse results.

**Acceptance Scenarios**:

1. **Given** multiple matching packages, **When** the user runs `aam search agent --sort name`, **Then** results appear in alphabetical order by package name.
2. **Given** multiple matching packages with different update dates, **When** the user runs `aam search agent --sort recent`, **Then** results appear with most recently updated first.
3. **Given** no `--sort` option is specified, **When** the user runs `aam search agent`, **Then** results are sorted by relevance score (default behavior from Story 1).

---

### User Story 7 — Visible Source Search Failures (Priority: P1)

A user has configured sources but one has a corrupted cache or network issue. When they search, they expect to be warned that some sources could not be searched, rather than silently receiving incomplete results.

**Why this priority**: Silent failures erode trust. Users make decisions based on search results — if results are incomplete and the user doesn't know, they may miss the package they need. This is low effort with high debuggability impact.

**Independent Test**: Can be fully tested by simulating a source search failure (corrupted cache) and verifying a visible warning appears alongside partial results. Delivers value by keeping users informed.

**Acceptance Scenarios**:

1. **Given** two sources are configured and one has a corrupted cache, **When** the user runs `aam search doc`, **Then** results from the healthy source are shown AND a warning displays: "Warning: Could not search source 'xyz': [reason]".
2. **Given** a source search fails, **When** results are displayed, **Then** registry results are still shown (graceful degradation).
3. **Given** the `--json` output flag is used and a source fails, **When** results are returned, **Then** the JSON includes a "warnings" array with the failure details.

---

### Edge Cases

- What happens when the query is an empty string? The system should return all packages up to the limit (browse mode).
- What happens when `--type` value doesn't match any known artifact type (e.g., `--type foo`)? The system should show a warning listing valid types.
- What happens when `--limit` exceeds the total number of results? The system should show all results without error.
- What happens when the same package exists in both a registry and a source? Both results should appear, clearly labeled with their origin.
- What happens when the query contains special characters (quotes, brackets, regex chars)? The system should treat them as literal characters, not patterns.
- What happens when a source has thousands of artifacts? The system should search efficiently and respect the limit without loading all artifacts into memory upfront.

## Requirements *(mandatory)*

### Functional Requirements

**Search Logic (Unified Service Layer)**

- **FR-001**: The search service MUST search both configured registries and git source artifacts in a single operation.
- **FR-002**: The search service MUST assign a relevance score to each result based on match type: exact name match (highest), name-prefix match, name-substring match, keyword match, and description-substring match (lowest).
- **FR-003**: The search service MUST sort results by relevance score in descending order by default.
- **FR-004**: The search service MUST validate the limit parameter is between 1 and 50 and raise a clear error for invalid values.
- **FR-005**: The search service MUST return a total count of all matches alongside the limited result set.
- **FR-006**: The search service MUST support searching with an empty query string, returning all packages up to the limit (browse mode).

**Filtering**

- **FR-007**: The CLI MUST accept multiple `--type` values in a single command (e.g., `--type skill --type agent`).
- **FR-008**: The CLI MUST accept a `--source` option to limit search to a specific git source by name.
- **FR-009**: The CLI MUST accept a `--registry` option to limit search to a specific registry by name.
- **FR-010**: The CLI MUST display a warning when a `--source` or `--registry` filter name does not match any configured source or registry.

**Sorting**

- **FR-011**: The CLI MUST accept a `--sort` option with values: `relevance` (default), `name`, and `recent`.
- **FR-012**: When `--sort name` is used, results MUST be sorted alphabetically by package name.
- **FR-013**: When `--sort recent` is used, results MUST be sorted by last-updated date, most recent first.

**Display**

- **FR-014**: The CLI MUST display results in a tabular format with aligned columns for Name, Version, Type, Source/Registry, and Description.
- **FR-015**: The CLI MUST show "Showing X of Y results" when the total exceeds the limit, and suggest `--limit` to see more.
- **FR-016**: The CLI MUST support `--json` output with the same data fields plus a `warnings` array for any search failures.

**Empty Results & Suggestions**

- **FR-017**: When zero results are found, the CLI MUST search the full package name index for similar names (approximate string matching) and suggest up to 3 alternatives.
- **FR-018**: Suggestions MUST only appear when at least one name has a similarity score above a threshold of 0.6 (see research.md R-002).

**Error Handling**

- **FR-019**: The CLI MUST NOT require registries to be configured when git sources are available — search MUST proceed with whatever sources are configured.
- **FR-020**: The CLI MUST display a visible warning (not just a debug log) when a specific source or registry fails during search, while still returning results from successful sources.
- **FR-021**: The CLI MUST display a clear error only when no registries AND no sources are configured.
- **FR-022**: The CLI MUST display a warning when an unknown `--type` value is provided, listing the valid artifact types.

**Architecture**

- **FR-023**: The search command MUST delegate all search logic (registry search, source search, scoring, filtering, sorting) to the search service layer — the command file MUST only handle CLI argument parsing and result presentation.
- **FR-024**: The search service MUST be usable by both the CLI command and the MCP server, returning identical results for the same query and parameters.

### Key Entities

- **SearchResult**: A unified result object containing: name, version, description, keywords, artifact types, source/registry origin, relevance score, and last-updated date.
- **SearchQuery**: The user's search parameters: query string, limit, type filters, source/registry filters, and sort preference.
- **SearchResponse**: A response envelope containing: the list of search results (limited), the total match count, and any warnings from failed sources.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The most relevant result (exact or prefix name match) appears in the top 3 results for 90% of single-word queries against a test dataset of 50+ packages.
- **SC-002**: Users can discover packages from git sources without configuring any registry — search works with sources alone.
- **SC-003**: The CLI and MCP server return identical result sets (same names, same order) for the same query and parameters.
- **SC-004**: When a source search fails, a visible warning appears in the output — no silent failures.
- **SC-005**: Misspelled queries against a 50+ package index surface at least one correct suggestion 80% of the time when the intended package exists.
- **SC-006**: Search results are displayed in a scannable tabular layout that allows users to identify package name, type, and origin without reading descriptions.
- **SC-007**: The search command completes within 2 seconds for local registries and cached sources with up to 500 indexed packages.
