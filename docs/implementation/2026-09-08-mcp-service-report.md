# Task 3 report: bounded MCP consumer interface

## Status

Implemented on `experiment/path-holding-pilot` from base `2b4bab7`. The implementation exposes exactly four MCP tools over stdio, supplies the owner CLI, keeps consumer navigation/finding state process-local unless trace mode is explicitly selected, and removes the two durable read-path writes identified by the Task 3 context.

The implementation uses MCP Python SDK 1.30.0 through the declared dependency `mcp>=1.28,<2`.

## Files

- Created `src/tampu/service.py`, `src/tampu/mcp_server.py`, `src/tampu/cli.py`, `tests/test_service.py`, and `tests/test_mcp.py`.
- Replaced the scaffold entry point in `src/tampu/__init__.py`.
- Updated `src/tampu/repository.py` for a noninitializing consumer constructor, nonpersisted generation observation on search, verified backing bytes during evidence inspection, and no-follow source-root admission.
- Updated `tests/test_repository.py`, `pyproject.toml`, and `uv.lock`.

## Public Python and CLI signatures

```python
Service(repository: Repository, *, trace_path: Path | None = None)

Service.describe(
    *, collection: str | None = None, cursor: str | None = None,
    limit: int = 10, facet: str | None = None,
    facet_cursor: str | None = None, detail_limit: int = 20,
    byte_budget: int = 8192,
) -> dict

Service.search(
    *, collection: str | None = None, revision: str | None = None,
    intent: str | None = None, journey_id: str | None = None,
    lens: str = "lexical/v1", query: str = "",
    mode: str = "any_terms", filters: dict | None = None,
    limit: int = 2, byte_budget: int = 8192,
) -> dict

Service.inspect(
    *, journey_id: str, node_id: str,
    continuation: str | None = None, limit: int = 2,
    evidence_handle: str | None = None, artifact_id: str | None = None,
    ordinal: int | None = None, page: int | None = None,
    start: int | None = None, end: int | None = None,
    slice_chars: int = 800, byte_budget: int = 8192,
) -> dict

Service.finish(
    *, journey_id: str, kind: str, statement: str,
    evidence_handles: list[str] | None = None,
    node_id: str | None = None, reason: str | None = None,
    semantic_absence: bool = False, release: bool = False,
    byte_budget: int = 8192,
) -> dict
```

```text
tampu init
tampu ingest COLLECTION ROOT --profile {poppler,unstructured} [--image IMAGE] [--metadata PATH]
tampu describe [--collection COLLECTION] [--byte-budget BYTES]
tampu serve [--trace PATH]
```

`init` and `ingest` own schema/storage mutation. `describe` and `serve` construct `Repository(config, initialize=False)`, which verifies the existing schema without creating collections/indexes, replacing the ArangoSearch view, refreshing durable generation records, or creating the configured store directory.

## Actual tools/list schemas and annotations

FastMCP generates these JSON Schema inputs. `SkipValidation` retains these consumer-facing types while passing malformed transport values to Service so controlled error envelopes replace Pydantic errors that could echo input.

```text
describe object
  collection: string|null = null
  cursor: string|null = null
  limit: integer = 10
  facet: string|null = null
  facet_cursor: string|null = null
  detail_limit: integer = 20
  byte_budget: integer = 8192
  required: []
  annotations: readOnlyHint=true, destructiveHint=false,
               idempotentHint=true, openWorldHint=false

search object
  collection: string|null = null
  revision: string|null = null
  intent: string|null = null
  journey_id: string|null = null
  lens: string = "lexical/v1"
  query: string = ""
  mode: string = "any_terms"
  filters: object|null = null
  limit: integer = 2
  byte_budget: integer = 8192
  required: []
  annotations: readOnlyHint=false, destructiveHint=false,
               idempotentHint=false, openWorldHint=false

inspect object
  journey_id: string (required)
  node_id: string (required)
  continuation: string|null = null
  limit: integer = 2
  evidence_handle: string|null = null
  artifact_id: string|null = null
  ordinal: integer|null = null
  page: integer|null = null
  start: integer|null = null
  end: integer|null = null
  slice_chars: integer = 800
  byte_budget: integer = 8192
  annotations: readOnlyHint=false, destructiveHint=false,
               idempotentHint=false, openWorldHint=false

finish object
  journey_id: string (required)
  kind: string (required)
  statement: string (required)
  evidence_handles: array[string]|null = null
  node_id: string|null = null
  reason: string|null = null
  semantic_absence: boolean = false
  release: boolean = false
  byte_budget: integer = 8192
  annotations: readOnlyHint=false, destructiveHint=true,
               idempotentHint=false, openWorldHint=false
```

The descriptions returned by `tools/list` state the lexical modes, query applicability, pinned revision behavior, `limit=0`, opaque continuation/evidence semantics, physical-page versus printed-page distinction, finding kinds, release semantics, process-local effects, and trace exception. Search and inspect are intentionally not labeled read-only because they create process-local navigation/delivery state. Finish is destructive because `release=true` discards that state and may write a full-content trace when the owner started trace mode. The controller separately verified that these truthful stateful annotations can run through supported automatic approval review; they were not weakened to avoid review.

## Application envelopes

Every application result uses compact UTF-8 JSON and one MCP `TextContent`; `structuredContent` is absent, so FastMCP does not pretty-print or duplicate the application envelope. Success:

```json
{"status":"ok","result":{},"scope":{},"omissions":[]}
```

Controlled failure:

```json
{"status":"error","error":{"code":"invalid_input","message":"The search hit limit is invalid."},"scope":{"operation":"search"},"omissions":[]}
```

A search result has this concrete shape (opaque values abbreviated):

```json
{
  "status": "ok",
  "result": {
    "journey_id": "journey_…",
    "node_id": "node_…",
    "intent": "consumer supplied intent",
    "revision_id": "published revision ID",
    "projection_selection": "selection digest",
    "lens": "lexical/v1",
    "predicate": {"query": "alpha", "mode": "any_terms", "filters": {}},
    "full_count": 3,
    "count_kind": "exact",
    "unknown_count": 0,
    "returned_count": 2,
    "ordering": "maximum_element_bm25_then_artifact_id",
    "coverage": {"artifacts": 3, "ready_artifacts": 3, "failed_artifacts": 0, "pages_total": 3, "pages_with_text": 3, "blank_or_partial_artifacts": 0, "pages_unknown": 0},
    "index_generation": {"generation_id": "…", "projection_count": 3, "element_count": 3, "observed_at": "…"},
    "index_generation_before": {"generation_id": "…", "projection_count": 3, "element_count": 3, "observed_at": "…"},
    "index_generation_stable": true,
    "lens_config": {"lens": "lexical/v1", "revision_scope": "pinned_projection_selection", "analyzer": "text_en", "mode": "any_terms", "artifact_score": "maximum_matching_element_bm25", "tie_breaker": "artifact_id"},
    "hits": [{"artifact_id": "…", "title": {"value": "…", "origin": "…"}, "source_aliases": ["…"], "omitted_source_aliases": 0, "score": 1.0, "projection_status": "ready", "evidence_handle": "evidence_…", "physical_page": 10, "printed_page": null, "page_semantics": "one_based_physical_pdf_page; printed_page_unknown", "extract": "…", "extract_truncated": false}],
    "continuation": "continuation_…"
  },
  "scope": {"collection": "papers", "revision_id": "…", "projection_selection": "…", "lens": "lexical/v1", "full_count": 3, "count_kind": "exact"},
  "omissions": ["additional_candidates_available_by_continuation"]
}
```

`limit=0` retains the full/count-kind/coverage/ordering/predicate observation, returns `hits: []`, and supplies a continuation when candidates exist. A byte budget may underfill hits; the continuation is reset to the first candidate not actually delivered and undelivered evidence handles are discarded.

`inspect` has three result forms:

1. Candidate pagination returns journey/node/revision, offset, full/count kind, bounded `hits`, and continuation.
2. `artifact_id` plus optional physical `page` or `ordinal` opens any artifact in the node's complete candidate set, including one not previously displayed. It returns bounded attributed metadata, projection status/coverage/losses, element descriptors, extracts, opaque evidence handles, and an element continuation.
3. `evidence_handle` returns one Unicode-character slice with `character_range`, exact artifact/projection/ordinal, `physical_page`, `printed_page: null`, projection recipe/coverage/losses, and a continuation when the requested range remains.

An inspected slice returns a new citation handle whose stored start/end exactly match the text delivered. Only that successfully delivered handle becomes eligible for a positive finding. Navigation handles that merely appeared in search/element listings remain ineligible.

`describe` returns `schema_version: "tampu-tools/v1"`, paged published collections, current revision identity and times/counts, extraction coverage with `ready_does_not_mean_complete_text: true`, artifact-count facets, bounded failure details, up to five actual projection recipes, lens contracts, limits, capability availability, and `consumer_benefit: "not_tested"`. Roots are represented as `owner_configured_source`, not emitted as paths. Facets return at most five values plus `unknown_artifacts` and `omitted_values`; `source_group` counts only explicit metadata assertions. Facet detail and collections have opaque paged cursors. Response packing can underfill a requested collection page and places the first omitted collection behind the returned continuation.

`finish` returns a process-local finding with an opaque ID and `preserved: false`. Positive results use `machine_status: "structurally_validated"` and explicitly leave semantic entailment to consumer judgment. Bounded negatives require an exact zero-candidate node and copy its effective predicate, pinned projection selection, coverage, and count scope. A claimed semantic absence is forced to `machine_status: "unresolved"`. Unresolved findings require a reason. `release=true` reports release without preservation and deletes state only after its response fits and is successfully delivered.

## State, byte, evidence, and telemetry behavior

- Default/max hits are 2/20; zero is supported. Candidate cap is 10,000 and query timeout is 10 seconds through Repository.
- Default/hard application budgets are 8,192/32,768 UTF-8 bytes. Service measures the exact compact serialization that the MCP wrapper places in its single text content item. MCP framing and tools/list schema bytes remain separate.
- Search, inspect, and finish stage copies of journey changes. Budget/capacity failures commit no node, continuation, evidence delivery, inspection, finding, release, or new journey.
- Capacity accounting serializes all nodes, full candidate records, selection maps, continuations, generated evidence handles, inspected-handle sets, and findings. The aggregate maximum is 256 MiB and no live journey is silently evicted.
- Handles expire at 24 hours and remain invalid even if expired state has not yet been cleaned up.
- Inspection verifies node candidate membership and its exact pinned projection. It then verifies the captured artifact digest plus raw-output and normalized-elements SHA-256 values before reading. Missing or changed captured/raw/elements bytes return controlled `missing_evidence`; there is no current-source or newer-projection fallback.
- Element `page` is exposed as a one-based physical PDF page. Printed-page label is explicitly unknown; the implementation does not conflate the two.
- Default operational events contain only operation, an existing/generated opaque journey ID, an allowlisted lens ID, counts, elapsed milliseconds, compact response bytes, and controlled error category. They contain no artifact IDs, paths, query text/hash, snippets, unknown caller-supplied journey/lens strings, credentials, or raw exceptions.
- `serve --trace PATH` is the only durable journey-content option. It appends every complete argument/response pair, including errors, as JSONL. The owner-selected trace is deliberately content-bearing and is not described as preservation.

## TDD evidence

Observed red phases included:

- `tests/test_service.py` initially failed collection with `ModuleNotFoundError: tampu.service`.
- Initial service tests then failed UTF-8 packing and expired/release behavior before the bounded envelopes and release semantics were implemented.
- The no-follow ingest and consumer repository tests failed with one artifact captured through the symlink and `Repository.__init__()` rejecting `initialize=False`.
- Member inspection failed because `artifact_id` was not accepted.
- Transaction tests showed an underfilled search skipped directly to artifact 2 and a 256-byte budget failure left a live journey/finding.
- Real MCP testing failed because `tampu.cli` did not exist.
- Backing-integrity testing showed changed normalized text was accepted before verified inspection was added.
- Multi-collection description returned `budget_too_small` before collection underfill/cursor packing was implemented.

Each failure was rerun green after the minimum corresponding implementation. Tests exercise real Service behavior. Repository integration uses real ArangoDB with a unique disposable database/user per test. The MCP test launches `python -m tampu.cli serve`, initializes a real `ClientSession`, calls `tools/list` and `tools/call`, and uses the same disposable database. Extraction is replaced only at the external extractor boundary for deterministic published projection fixtures; the CLI ingest path itself is also invoked in a subprocess.

## Fresh verification

```text
uv run pytest tests/test_service.py tests/test_mcp.py tests/test_repository.py -q
46 passed in 10.28s

uv run pytest tests -q
71 passed, 1 skipped in 10.79s

uvx ruff check src/tampu tests scripts/provision-tampu.py
All checks passed!

uv run python -m compileall -q src tests scripts/provision-tampu.py
exit 0

git diff --check
clean
```

The single skip remains Task 1's opt-in real Unstructured container test.

The actual transport test additionally established:

- exactly `describe`, `search`, `inspect`, and `finish` are discoverable;
- returned descriptions contain the required mode/pinning/count/finding/opaque-handle semantics;
- MCP `structuredContent` is absent and one compact text item carries application JSON;
- a near-cap search's actual delivered text bytes are at most its requested 1,000-byte budget;
- malformed JSON argument types are handled by Service and the query, intent, fake journey/lens, nested invalid argument, source path, and database password sentinels are absent from captured server stderr.

## Limits and concerns

- Search/inspect/finish truthfully advertise process-local mutation, so approval-policy-never consumers can reject them. The controller verified a supported `on-request` plus automatic-review route for the exact process-local record/release pattern; no annotation was falsified and any review rejection remains binding.
- Description performs bounded output but currently reads projection records per member to summarize recipes/losses. This was acceptable for the current corpus but is an N+1 read path, not a claim of large-scale efficiency.
- Evidence integrity verification hashes the captured PDF, raw extraction output, and normalized element file on each evidence opening. This prioritizes pinned-evidence correctness over cached speed in the prototype.
- Active state is process-local and a process restart invalidates all handles. Trace mode records evaluation content but does not restore journeys.
- ArangoSearch navigation scores remain current index-statistics observations; pinned membership/projections do not claim historical score reexecution. Before/after generation observations remain visible and are now read-only.
- `ready` means extraction completed. It does not mean every physical page has text or that semantic coverage is complete. Coverage, loss details, unknown pages, and this limitation remain explicit.
- The implementation and tests establish operational behavior only. They do not establish finding quality, navigation benefit, literature completeness, untested-scale performance, or superiority over another retrieval interface.

## Additional admission-contract correction

Task 3 integration exposed that `Repository.ingest` called `Path.resolve()` before `capture_tree`, which erased root/ancestor symlinks and bypassed Task 1's no-follow admission rule. Ingest now preserves the absolute lexical path for capture and collection identity while using a separately resolved path only for the evidence-store containment comparison. The public regression confirms a symlinked source root publishes zero artifacts with incomplete enumeration instead of observing the target. The primary runtime r0 used real directory components and was not affected by this development correction.

## Commits

- `5e18a2369e4e68be494649946ce49a4d07faabd4` — signed implementation commit, `feat: add bounded MCP consumer interface`
- `cc333baea5c8f45ca829dde1b7f02c12b8beb4b9` — signed automatic OpenTimestamps stamp commit for the implementation commit

`git log --show-signature` reports good signatures from `Tampu Project <tampu@wamason.com>` for both commits.

## Fix round 1 — independent review findings

All ten findings in `task-3-findings.md` were reproduced and corrected together on base `cc333baea5c8f45ca829dde1b7f02c12b8beb4b9`.

1. Search and inspect response fitting now creates a results continuation when budget fitting removes a hit from an otherwise final requested page. Its staged offset is the first candidate not actually delivered. A continuation and its state are included in both capacity and serialized-response fitting before any journey is committed.
2. Expired journeys are reclaimed before aggregate capacity checks and active-count reporting. An expired handle still returns `expired_journey` on its attempted use; reclamation never evicts a live journey.
3. The MCP wrappers accept omitted required fields at the Python validation boundary so Tampu can return its controlled compact application envelope. The published tools/list JSON schemas are restored after registration and remain truthful: inspect still requires `journey_id` and `node_id`; finish still requires `journey_id`, `kind`, and `statement`. An actual stdio MCP test sends both omissions and verifies application errors plus stderr non-disclosure.
4. Telemetry allowlists the lens only after a string type check. Trace creation/append/serialization failures become `trace_unavailable` without raw exceptions or trace paths. Trace succeeds before success telemetry and before search/inspect/finish public state commit, so a trace failure cannot leave live journey state or a recorded/released finding.
5. Cursor decoding now treats the final 12 bytes as the binary HMAC and validates the single separator at the fixed position. It does not split inside arbitrary signature bytes.
6. `semantic_absence=true` with a positive finding is rejected as `invalid_finding`. Bounded-negative and unresolved findings retain the declaration and remain unresolved where semantic absence is claimed.
7. Describe now enumerates only published revisions through a repository query whose AQL predicate is `r.state == 'published'`. Each bounded revision summary includes available revision ID/state, observation bounds, enumeration completeness, selection digest, counts, aggregate coverage, and publication time. A staged-revision integration fixture is excluded.
8. Facets now include the required `source_group`, `asserted_publication_year`, and `processing_status` dimensions, as well as `publication_status` and `work_id`. Publication dates with different valid precision but the same asserted year aggregate into one artifact count. All fields retain at-most-five values, unknown artifact counts, omitted value counts, and paged facet detail.
9. Describe now publishes concrete lexical, metadata, and temporal filter construction contracts with supported common keys, missing-value form, temporal field enum, inclusive bound semantics, UTC handling for timezone-free instants, conjunctive combination semantics, and request examples.
10. `budget_too_small` errors now carry integer `minimum_bytes`. A mandatory-envelope packing failure reports the actual compact UTF-8 size after permitted omissions; a budget below the protocol minimum reports 256. A budget above the 32,768-byte hard maximum is separately rejected as `invalid_input`.

### Public schema additions

The four tool names and annotations are unchanged. Describe adds two optional inputs:

```text
revision_cursor: string|null = null
revision_limit: integer = 2 (range 1..20)
```

`revision_cursor` requires an exact `collection` and is scoped to that collection. Each described collection adds:

```text
revisions: array of published revision summaries
revision_continuation: opaque string|null
```

The describe lens contracts now expose these filter fields:

```text
common: artifact_id, source_alias, source_prefix, work_id, publication_status
metadata missing: title, authors, work_id, publication_status,
                  publication_date, source_group, version
temporal field: observed_time, source_modification_time, publication_date
temporal bounds: from/to inclusive; publication_date uses YYYY-MM-DD
temporal missing: boolean for unknown values of the named field
temporal timezone: timezone-free instants are interpreted as UTC
all combinations: conjunctive
```

The application error addition is:

```json
{"code":"budget_too_small","message":"…","minimum_bytes":1234}
```

All application responses remain one compact UTF-8 JSON `TextContent` with no structured-content duplicate. Tool annotations remain truthful: describe is read-only; search and inspect mutate only expiring process-local state; finish may record or release that state and remains destructive-hinted.

### Fix-round TDD evidence

Focused regressions were written before their implementation changes. The red runs reproduced the review observations: final-page continuations were null after hit removal; expired state blocked replacement capacity; omitted required MCP fields produced a FastMCP/Pydantic transport error; malformed lens telemetry raised `TypeError`; an invalid trace destination escaped with its path; 19 of 256 fixed-key binary cursors failed; a positive semantic-absence finding was accepted; revision/facet/filter discovery keys were absent; staged filtering had no repository operation; and budget errors lacked `minimum_bytes`.

After the corresponding minimal changes, the focused service group covering all ten issues passed 9 tests, the published-revision repository integration passed, and the real MCP subprocess test passed. A final schema assertion checks that describe publishes `revision_cursor`/`revision_limit` and that inspect/finish retain their required arrays. The final budget-bound correction was also driven red: a 32,769-byte request initially returned the misleading `budget_too_small`, then passed as controlled `invalid_input` after separating the hard maximum from the numeric minimum.

### Fix-round verification

```text
uv run pytest tests/test_service.py -q
19 passed in 0.97s

uv run pytest tests/test_repository.py -q
33 passed in 7.36s

uv run pytest tests/test_mcp.py -q
1 passed in 3.51s

uv run pytest tests -q
77 passed, 1 skipped in 11.01s

uvx ruff check src/tampu tests scripts/provision-tampu.py
All checks passed!

uv run python -m compileall -q src tests scripts/provision-tampu.py
exit 0

git diff --check
clean
```

The single skip remains the opt-in real Unstructured container test. Repository and MCP integration tests use unique disposable database fixtures and do not mutate the main runtime database.

### Fix-round limits and concerns

- Required-field sanitization uses the FastMCP registration manager to restore the consumer-facing required arrays after callable defaults are made transport-tolerant. This is intentionally narrow and covered through actual stdio tools/list and tools/call behavior. The project currently constrains the MCP dependency version; a future FastMCP upgrade should rerun this transport test before release.
- Revision discovery performs a bounded response page but currently retrieves the published revision list before slicing it in Service. This is suitable for the prototype's revision count, not a large-history scalability claim.
- The earlier truthful-annotation approval concern remains unchanged. The controller established a supported on-request automatic-review route for these already-authorized process-local operations; this implementation did not weaken annotations or permissions.

### Fix-round commits

- `54bb65bc501b4ec5485dc2a4fb44946028448821` — signed implementation commit, `fix: harden bounded MCP interface`
- `4e4276a936179914ddb05ea20a3662946360a6ee` — signed automatic OpenTimestamps stamp commit for the implementation commit

`git log --show-signature` reports good signatures from `Tampu Project <tampu@wamason.com>` for both commits. The tracked worktree is clean at the stamped head.

## Fix round 2 — revision-page packing progress

The second review accepted all ten prior findings and identified one additional describe packing defect on base `4e4276a936179914ddb05ea20a3662946360a6ee`. When one collection exposed 20 published revision summaries, the default 8,192-byte budget caused the fitter to remove the entire collection and return its collection cursor at offset zero. Repeating the same request therefore repeated an empty successful page forever.

Describe packing now removes revision summaries from the end of the selected revision page before considering collection-page underfill. Every removal resets `revision_continuation` to the absolute offset of the first unpublished-to-the-response summary, including when the originally selected page reached the end of revision history and initially had no continuation. The response adds `revisions_underfilled_by_budget` to `omissions`. A continuation call begins at that absolute offset, so initial and subsequent pages deliver every selected published revision once and in repository order.

A successful describe page containing a selected collection must retain at least one revision summary. If the collection plus one summary cannot fit after permitted optional omissions, describe returns controlled `budget_too_small` with integer `minimum_bytes` and a message to increase the budget or narrow the request. Retrying the regression fixture at exactly that reported minimum returns a nonempty successful page. The public tool signature and JSON field schema are unchanged in this round; only packing and omission semantics changed.

### Fix-round 2 TDD and verification

The new 20-revision regression first failed with `len(response["result"]["collections"]) == 0` on the initial default-budget request, matching the reviewer reproduction. After the packing change, it walks the returned `revision_continuation` values through all 20 revision IDs without empty pages, repeats, or overlap, and covers both initial and subsequent pages. It also verifies exact compact UTF-8 size at each page and the controlled one-summary minimum behavior.

```text
uv run pytest tests/test_service.py::test_describe_underfills_initial_and_subsequent_revision_pages tests/test_service.py::test_describe_underfills_collection_page_without_losing_continuation -q
2 passed in 0.46s

uv run pytest tests/test_service.py tests/test_mcp.py -q
21 passed in 4.12s

uvx ruff check src/tampu/service.py tests/test_service.py
All checks passed!

uv run python -m compileall -q src/tampu/service.py tests/test_service.py
exit 0

git diff --check
clean
```

### Fix-round 2 commits

- `b549e34900d96afba0b486acb5fb042cff586de8` — signed implementation commit, `fix: preserve describe revision progress`
- `2b78c6a312eff20c3f39622648e66d06db595988` — signed automatic OpenTimestamps stamp commit for the implementation commit

`git log --show-signature` reports good signatures from `Tampu Project <tampu@wamason.com>` for both commits. The tracked worktree is clean at the stamped head.

## Fix round 3 — minimum-budget error serialization

The third review accepted revision pagination and identified a one-byte application-budget overflow in its new narrowing error: `describe(collection="papers", revision_limit=20, byte_budget=256)` serialized to 257 compact UTF-8 bytes. The regression now asserts that this exact 256-byte-budget response retains `budget_too_small`, an integer `minimum_bytes` greater than 256, and a total compact encoding of at most 256 bytes.

The message is now `One revision summary cannot fit; increase byte_budget or narrow the request.` This preserves the actionable retry/narrowing guidance and numeric useful-page minimum while fitting the application envelope. No signature, schema, packing, cursor, or state semantics changed.

The focused test was first observed red at `assert 257 <= 256`, then green after shortening only this message:

```text
uv run pytest tests/test_service.py::test_describe_underfills_initial_and_subsequent_revision_pages -q
1 passed in 0.39s

git diff --check
clean
```

### Fix-round 3 commits

- `ee074b6998cc2411da8c5508f46ce565406cf90b` — signed implementation commit, `fix: fit revision budget error`
- `6ae4ad6b36a34666a72318b4fc745da84455232f` — signed automatic OpenTimestamps stamp commit for the implementation commit

`git log --show-signature` reports good signatures from `Tampu Project <tampu@wamason.com>` for both commits. The tracked worktree is clean at the stamped head.
