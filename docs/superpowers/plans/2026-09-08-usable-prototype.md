# Usable Tampu Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and validate the user-authorized first usable prototype across the prepared 160/320/473-artifact collection stages, preserving an actual consumer's initial and revised findings.

**Architecture:** Capture immutable PDF bytes and provenance-preserving extraction projections in an owner-local store. ArangoDB holds immutable published revision membership and searchable elements. Four MCP tools expose bounded observations and process-local finding state; ingestion and reconciliation are administrative CLI operations.

**Tech Stack:** Python >=3.14, python-arango, MCP Python SDK, pytest, installed Unstructured Docker image and Poppler pdftotext/pdfinfo, existing ArangoDB 3.12.9-4 on localhost:8530.

## Global Constraints

- Binding design: `docs/superpowers/specs/2026-09-07-tampu-prototype-design.md`, its accepted follow-up dispositions, and `docs/experiments/2026-09-08-temporal-growth-scenario.md`.
- The user authorized implementation and signed commits. No new approval is required for ordinary implementation, isolated database provisioning or local experiments. Do not push, merge, download papers, or build optional journey/provider machinery as part of this plan.
- Python `>=3.14`. Keep credentials outside Git; runtime uses a dedicated Tampu database and scoped user, never another project's collections. Administrative credentials must never appear in command output or logs.
- Filesystem capture excludes symlinks and records every observed path's outcome. Capture source bytes before extraction. SHA-256 identifies artifact bytes; work/version assertions need independent provenance.
- Published revisions and projections are immutable. A failed/staged publication is invisible to default reads. The current pointer changes only after indexed visibility and publication records are verified.
- Initial lexical analyzer is `text_en`, with explicit `any_terms`, `all_terms` within one element, and `phrase`. Scores are maximum matching element BM25 per artifact, ties by artifact ID. Metadata and named temporal filters remain separately described lenses.
- Search defaults to 2 hits, permits 0, maximum 20. Default application JSON budget 8192 UTF-8 bytes, hard maximum 32768; scope and omissions take priority. Full candidate cap 10000, database query timeout 10 seconds. Never return partial counts as exact after a cap or timeout.
- Journey expiry 24 hours; aggregate process-local journey budget 256 MiB. Typed capacity errors and `finish(release=true)`; no silent live-state eviction or default durable journey content.
- Extraction per-file timeout 300 seconds, container memory 8 GiB, no implicit network model downloads, no silent extractor fallback. Profile choice follows recorded comparison.
- Four tools only: `describe`, `search`, `inspect`, `finish`. No embeddings, composition, refresh, history shortcut, preservation or historical score re-execution claims.
- Meaningful tests must check observable invariants, including failures. Old pilot tests need their separate disposable server on port 18529; new tests must use dedicated disposable Tampu databases.
- Report development observations as development observations. No held-out, general superiority, completeness-of-literature or statistically established benefit claims.

## Module and interface map

Use ordinary JSON-compatible dictionaries for persisted records and service responses; no generic database abstraction or plugin framework. Private helpers may be added within the following responsibility boundaries.

| Module | Public boundary |
|---|---|
| `capture.py` | `capture_tree(root: Path, store: Path) -> dict` with `sources`, deduplicated `artifacts`, start/end observation times and `enumeration_complete` |
| `extraction.py` | `extract_artifact(artifact: dict, store: Path, *, profile: str, timeout: int = 300, image: str | None = None) -> dict`; immutable projection record plus normalized elements persisted locally |
| `config.py` | `load_config(path: Path | None = None) -> dict`; `TAMPU_CONFIG` or `~/.config/tampu/config.json` |
| `repository.py` | `Repository(config: dict)` owning Arango connection/schema and revision operations; `ingest(collection: str, root: Path, *, profile: str, image: str | None = None) -> dict`; `resolve_revision(collection: str, revision: str | None) -> dict`; `members(revision: str) -> list[dict]`; `search_candidates(revision: str, lens: str, query: str, mode: str, filters: dict) -> dict`; `read_projection(projection_id: str) -> dict`; `describe(collection: str | None = None) -> dict` |
| `service.py` | `Service(repository: Repository, *, trace_path: Path | None = None)` implementing the four tool methods, holding ephemeral journey/result/inspection/finding state and enforcing all response/resource limits |
| `mcp_server.py` | FastMCP wrappers over one Service instance; stdio transport; no admin tools |
| `cli.py` | `main()` for `init`, `ingest`, `describe`, and `serve`; administrative invocation uses the same repository code |
| `errors.py` | `TampuError(code: str, message: str)` where public messages are controlled and contain no raw driver/extractor exception text |

Artifact record keys: `artifact_id` (full digest), `sha256`, `byte_size`, `store_path` (relative to store), `captured_at`. Source observation keys: `relative_path`, `status`, optional `artifact_id`, `mtime_ns`, controlled `error_code`. Projection record keys: `projection_id`, `artifact_id`, `recipe`, `status`, `raw_path`, `elements_path`, `coverage`, `losses`, `elapsed_seconds`; statuses `ready` or `failed`. Normalized element keys: `ordinal`, `original_element_id`, `type`, `text`, `page`, `coordinates`; preserve complete extractor output separately. Projections record actual output digest and exact extractor/profile versions.

Revision records include `revision_id`, `collection`, `parent_revision`, `state`, `observed_start`, `observed_end`, `enumeration_complete`, membership/projection-selection digest, aggregate coverage, counts and changes. Memberships contain aliases, captured source times and attributed metadata assertions. Elements in Arango carry artifact/projection IDs and ordinals; stable evidence addresses contain all three plus character offsets. Each task must document the final dictionary schema it produces for its consumer.

## Task 1: Capture and extraction with immutable evidence

**Files:** create `src/tampu/capture.py`, `src/tampu/extraction.py`, `src/tampu/errors.py`, `tests/test_capture.py`, `tests/test_extraction.py`; update `pyproject.toml` and lockfile for pytest. Preserve existing timestamp dependencies.

**Consumes:** local PDF directory and owner-local store. Read readiness results under the main checkout's `tmp/prototype-readiness/extraction/` if present; image pinning must use an inspected digest, not a mutable `latest` at execution time.

**Produces:** the capture/projection records above and reusable captured PDFs/raw/normalized files. Capture must not require ArangoDB.

- [ ] Write and run failing tests for byte deduplication with both aliases retained, non-PDF and misleading-extension exclusion, symlink exclusion, changed/deleted sources leaving prior captured bytes intact, concurrent-change retry/failure, and enumeration/read failures.
- [ ] Implement recursive no-follow scanning, extension/header validation, best-effort before/after stat change detection with one retry, temporary-copy hashing and atomic installation. Use safe source opens so a discovered regular file replaced by a symlink is not followed. Account for directories and failed subtrees without pretending to observe their contents.
- [ ] Write and run failing extraction tests for one-based pages, raw-field retention, stable text offsets, distinct projection identity after changed output/configuration, zero-text pages, malformed/encrypted input, missing extractor and timeout failures. Small test PDFs may be generated with a minimal PDF fixture helper or a test-only library; do not depend on the research corpus for unit tests.
- [ ] Implement both explicit extraction profiles. Poppler uses page-preserving text and pdfinfo; Unstructured uses a pinned local Docker image, readonly source mount, isolated scratch output, no network, memory/timeout limits. Keep each profile's provenance and limitations distinct; never silently switch between them. Reuse an existing successful matching recipe without overwriting it; failed work can be retried explicitly.
- [ ] Run focused tests, then `uv run pytest tests/test_capture.py tests/test_extraction.py -q`; inspect diff and commit only task files with a signed commit. Report actual public schemas, commands, versions and limitations.

An invariant test must establish independent custody, for example:

```python
scan = capture_tree(source, store)
artifact = scan['artifacts'][0]
captured = store / artifact['store_path']
original = captured.read_bytes()
(source / 'paper.pdf').write_bytes(b'%PDF-invalid replacement')
assert captured.read_bytes() == original
assert len(scan['artifacts']) == 1
assert len([s for s in scan['sources'] if s.get('artifact_id') == artifact['artifact_id']]) == 2
```

## Task 2: ArangoDB revision publication and retrieval

**Files:** create `src/tampu/config.py`, `src/tampu/repository.py`, `tests/conftest.py`, `tests/test_repository.py`; update dependencies with python-arango. Add `scripts/provision-tampu.py` for explicit administrative provisioning without embedding secrets.

**Consumes:** Task 1's record schemas, configured local store, dedicated database credentials. The controller verifies/provisions the owner-local runtime config. Repository construction verifies the configured database and creates only Tampu's schema within it.

**Produces:** immutable published revisions, membership/projection/element records, bounded candidate results and pinned evidence access using the module interfaces above.

- [ ] Write failing real-Arango integration tests for deduplication/counts, revision-specific candidate membership, publication failure retaining the old pointer, source additions/replacements/removals, old captured evidence after source changes, and extraction failure represented as partial coverage.
- [ ] Implement configuration loading with fail-stop errors and no credential logging. The provisioning script accepts admin credentials from an explicit environment/file input, creates a new dedicated database and scoped user with only that database's rights, and writes a mode-0600 runtime config. It must refuse destructive reuse or privilege modification of an existing account.
- [ ] Create exact indexes and ArangoSearch view over immutable elements. Preserve observation records, per-revision memberships and selected projection IDs separately. Successful extracted elements can be shared across revisions. Ingestion stages records, verifies search visibility with `waitForSync`, then atomically publishes the revision and current pointer with a transaction/revision check. Concurrent publication must not overwrite a newer pointer silently.
- [ ] Implement revision resolution rejecting unknown/unpublished state; record additions, removals, source replacements and processing changes separately. Enforce one registered root per collection. Metadata assertions have origin and unknown fields stay unknown.
- [ ] Implement lexical any/all/phrase retrieval, metadata filters (artifact ID, source alias/prefix, explicit work ID, publication status, missing metadata), and named temporal bounds/missing filters (observed time, source modification time, asserted publication date). Bind all query values. Count distinct artifacts before hit limits; report coverage for the searched subset. Candidate cap and query timeout produce typed errors. Scope joins must select only the pinned revision's projections.
- [ ] Test max-element BM25 selection and stable artifact-ID ties, all-terms within one element, phrase semantics, temporal unknown counts, failed projection visibility and missing backing-file errors. Run the task integration suite, inspect diff and signed-commit task files.

## Task 3: Bounded MCP interface and scoped findings

**Files:** create `src/tampu/service.py`, `src/tampu/mcp_server.py`, `src/tampu/cli.py`, `tests/test_service.py`, `tests/test_mcp.py`; replace scaffold entry point in `src/tampu/__init__.py`; add MCP dependency.

**Consumes:** Task 2 repository methods. `search_candidates` supplies a complete candidate set within its cap; the Service stores immutable result ordering for pagination. No parent navigation is exposed.

**Produces:** operational CLI and four discoverable MCP tools. Each tool returns a JSON-compatible envelope with `status`, bounded result/error and explicit omission/scope fields. Final concrete schemas are documented with examples.

- [ ] Write failing tests for default two hits, count-only calls, UTF-8 byte budgets, pagination stability after a successor publication, evidence authorization to node membership, Unicode slices/continuations, expiry/capacity/release and controlled error messages.
- [ ] Implement `describe` with bounded/paged collections, revisions, coverage/failure details, available lenses/limits, capability statuses and honest unavailable features. Facets are artifact counts with at most five values plus unknown/omitted counts and paged detail. Source groups require explicit tags.
- [ ] Implement `search` requiring intent on new journeys, pinning a resolved revision once; subsequent searches can reuse a journey's intent/revision with a newly supplied predicate. Each observation records its effective lens/predicate, projection selection, full count/count-kind, returned count, ordering, coverage and opaque continuation. Cap limits are checked before state mutation.
- [ ] Implement `inspect` for result pagination, bounded metadata and evidence slices from the node's members. Only successfully delivered evidence handles qualify as inspected evidence. Missing stored source/projection bytes never fall back to current files or newer projections. Keep source/printed-page distinctions and original extraction limitations visible.
- [ ] Implement `finish` for positive findings with validated journey evidence, bounded negatives from successful zero-candidate predicates with exact covered scope, and unresolved findings with reasons. Consumer semantic-absence claims remain unresolved machine status. Release is supported without a preservation claim. Default findings remain process-local; opt-in trace mode can persist full experiment content to an explicit path.
- [ ] Emit content-free operational events: operation/lens/counts/time/response bytes/error categories and opaque per-run journey IDs only. No artifact IDs, paths, queries, query hashes, snippets or raw exceptions. Check stderr/default library logging using sentinel tests.
- [ ] Add CLI commands `tampu init`, `tampu ingest COLLECTION ROOT --profile PROFILE`, `tampu describe`, `tampu serve`. MCP stdio has no administration tools. Exercise initialization, tools/list and tools/call over a real MCP client subprocess, not only direct Python calls. Run task tests and signed-commit files.

## Task 4: Corpus growth, diagnostics and consumer evidence

**Files:** create `experiments/growing_corpus/run.py`, `experiments/growing_corpus/README.md`, `docs/experiments/2026-09-08-usable-prototype-results.md`; update README and capability evidence configuration. Add targeted regression tests only where actual validation exposes missing invariants.

**Consumes:** operational CLI/MCP, prepared fixture manifest/snapshots, approved scenario, baseline source assessment. The builder's expected evidence stays outside the consumer's tools and process access.

**Produces:** reproducible ingestion run records, extraction comparison, diagnostics, actual consumer tool transcripts/assessments, evidence-backed limitations and current capabilities.

- [ ] Complete an approximately twelve-PDF extraction pilot covering short/long/multicolumn/proceedings/thin-output PDFs, comparing both available profiles for attribution, coverage, runtime and failures. Pin and record chosen primary profile before the full stages. Renderer-check selected evidence; successful extraction is not semantic-completeness certification.
- [ ] Ingest r0, then add r1 and r2 to the same registered working root. Record actual revision IDs and all counts/coverage/costs. Verify exactly 160/320/473 distinct captured artifacts, allowing explicitly reported processing failures. Recheck old-revision evidence after growth and run a separate tiny add/replace/remove diagnostic.
- [ ] Exercise six core diagnostics: known passage, recovery from misleading initial results, duplicate-vs-work distinction, processing failure, bounded lexical negative, and changed-source revision behavior. Preserve machine assertions and source checks as distinct evidence.
- [ ] Run small labeled negative-scope and count/coverage development comparisons with matched evidence, including present, absent, alias and processing-gap conditions. Existing path-ledger pilot remains inconclusive and optional path machinery remains disabled. Record per-case outcomes; no statistical effectiveness claim.
- [ ] Run an actual isolated consumer investigation over all three stages, retaining its prior assessment between stages. Include the cross-topic eviction question and the separate Legible Consensus revision check. Record real model identity/settings, all tool schemas/arguments/responses, available usage/bytes/time and final findings. The consumer must actually call the MCP tools; scripted answers or builder-authored substitutes do not satisfy this requirement.
- [ ] Review material consumer claims against pinned source passages; separate supported changes, missed changes and unresolved findings. Record any direct-evidence diagnostic separately from original failures. Exposed development tasks cannot become held-out evidence.
- [ ] Update README, reproduction commands and truthful capability statuses with links to observed evidence. Verify no credentials/PDF corpus/hidden answer labels entered tracked runtime configuration. Run all new tests, old pilot regression tests under their documented service, and a clean CLI/MCP smoke check. Request a final whole-branch review and resolve material findings before final signed commits.

## Completion audit

Check each user-goal requirement and the binding design's eight MVP completion criteria against actual files, commands, runtime records and consumer evidence. A prepared fixture, green unit tests, or a plausible plan does not prove a working service or consumer investigation. Keep the goal active until every required implementation and validation step above is complete. Record incomplete or inconclusive scientific results without relabeling them as tool benefit.

## Primary technical references

- [python-arango view API](https://docs.python-arango.com/en/main/view.html)
- [ArangoSearch functions and scoring](https://docs.arango.ai/arangodb/stable/aql/functions/arangosearch/)
- [ArangoSearch information retrieval and changing scores](https://docs.arango.ai/arangodb/stable/indexes-and-search/arangosearch/)

These describe API behavior; local authenticated integration tests must verify the deployed version's behavior.
