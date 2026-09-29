# Whole-branch review — usable Tampu prototype

Reviewed range: `25e2c1b6d8dad3090abc24ec2ec337bba8460312..9d4cc883403b2f47c6fdac7d04ec7579c87aa478`.

Review basis: the supplied log/stat/full-diff package, binding prototype design and accepted follow-up disposition, implementation plan, final-review context, completion audit, progress/rulings, Task 4 reviews, durable implementation reports, experiment protocols/results and compact evidence. I reviewed the package in focused storage/extraction, repository, service/MCP, tests, and experiment/evidence passes. No broad passing suite was rerun. Source was not changed, and no published research database was mutated. Focused probes used temporary files and uniquely provisioned disposable test databases/users, removed afterward.

### Strengths

- The core separation is sound: no-follow capture establishes byte custody; immutable raw/normalized files establish projection provenance; published memberships select projections; the service owns bounded process-local observation state. The public ingestion path preserves the lexical root for no-follow checks. Revision publication verifies index visibility before a transaction checks the expected parent and changes the current pointer (`src/tampu/capture.py:87`, `src/tampu/repository.py:230`, `:392`, `:416`).
- Retrieval counts distinct artifacts before display limits, restricts lexical candidates to the revision's selected projections, states max-element BM25 ordering, and records index observations without claiming reproducible historical scores (`src/tampu/repository.py:630`). The 10-second per-request/AQL bounds are present; the acknowledged N+1/materialization limitation does not justify an architectural rewrite for this prototype.
- Search/inspect/finish stage changes and commit them only after successful response fitting and explicit trace writing. Preview and inspected citation handles are distinct; inspection verifies captured/raw/normalized bytes; actual stdio tests cover the four-tool contract and controlled failure envelopes (`src/tampu/service.py:541`, `:778`, `:1193`, `:1500`; `tests/test_mcp.py`).
- The final capability profile separates current collection counts from frozen evaluation conditions, uses the accepted mechanism statuses, pages the two experiment records, and travels with findings by content hash. The three Task 4 findings are addressed at the reviewed head.
- The scientific reporting is appropriately restrained. It retains the incomplete 24-call eviction-r2 episode, zero-text successful extractions, 0/4 path-ledger uptake, builder-selected direct evidence, and response-only comparison limits. It does not convert those observations into superiority, causal benefit, semantic completeness, or held-out performance.

### Issues

#### Critical (Must Fix)

None found.

#### Important (Should Fix)

1. **Admission failures disappear from consumer coverage and become apparent removals.**

   - **Files:** `src/tampu/repository.py:461`, `:521`; `src/tampu/service.py:659`, `:1290`. Capture correctly records the underlying error at `src/tampu/capture.py:185`.
   - **Problem:** Revision/search coverage counts only admitted memberships and failed projections. It has no admission-error count or unknown-enumeration scope, and search nodes do not retain `enumeration_complete`. A readable directory containing an unreadable PDF can therefore report enumeration complete, zero artifacts, zero failed artifacts, and zero unknown pages. Bounded-negative findings copy that incomplete scope. `_changes` also classifies every previously captured path absent from the new captured set as removed, including a still-present path whose read failed.
   - **Confirmed trigger:** In a disposable real Arango database, publish a genuine one-page `paper.pdf`, leave its bytes/path in place, inject `PermissionError` at the capture copy boundary, and ingest again. The second revision reported `sources=artifacts=ready=failed=0`, `enumeration_complete=true`, and `changes.removed=["paper.pdf"]`, while the file still existed. A separate unreadable-first-ingestion probe returned an exact zero search and accepted bounded negative with all coverage values zero and no admission warning. A symlink-root probe preserved `enumeration_complete=false` in the revision but omitted it entirely from the successful zero search.
   - **Impact:** A consumer cannot distinguish a genuinely empty admitted collection from inaccessible sources using its search/negative observation; the revision change report also implies source removal where the scan established only uncertainty. This conflicts with the binding no-failed-scan-to-absence rule (`prototype-design.md:94`) and the first/third completion criteria.
   - **Fix:** Persist a revision-level admission summary distinct from extraction status, including observed outcome counts, unresolved admissions and enumeration completeness. Carry the relevant compact scope through search and bounded-negative findings as mandatory information, with paged controlled detail where needed. Keep an exact negative permissible over its explicitly admitted/processed subset, while declaring the unresolved source scope. Distinguish confirmed removal from failed or unenumerated observation; do not silently reuse current source bytes or relabel old membership as freshly captured. Cover both an unreadable file and an unreadable/unsafe subtree through public ingestion → search → finish, including response-budget fitting.

2. **Successful extraction reuse does not identify the current extractor/normalizer recipe.**

   - **Files:** `src/tampu/extraction.py:77`, `:348`, `:361`.
   - **Problem:** Cache matching compares the stored recipe only with the requested profile/options. Poppler's actual version is recorded after execution but is absent from the cache key; no normalization version is recorded or compared for either adapter. Consequently the cache returns before checking whether the installed Poppler or normalization implementation has changed.
   - **Confirmed trigger:** Extract a genuine temporary PDF with Poppler, replace the extraction adapter in a focused fixture with one returning changed text and a different version, and call `extract_artifact` again with the same store/profile/options. The changed adapter is never invoked and the old projection is returned. The recorded recipe keys contain `extractor_version`, but neither current-version matching nor a normalization-version field exists. Existing changed-output tests use different stores, so they do not catch reuse after an upgrade in the same store.
   - **Impact:** A later ingestion after an extractor/normalization correction can silently keep the old representation and omit `processing_changed`. Hash verification establishes that the cached old output is intact; it does not establish that it matches the current requested processing recipe. This misses the explicit versioned-projection contract (`prototype-design.md:108`).
   - **Fix:** Determine the current reusable recipe before cache lookup. Include explicit adapter/profile and normalization versions, plus the effective Poppler executable version; the pinned Unstructured image already provides its container identity. Match those identities before reuse and preserve old projections when the recipe changes. Add same-store upgrade regressions, unchanged-recipe reuse, controlled version-probe failure, and old-evidence retention. Do not rewrite or re-extract the historical published experiment merely to update its provenance.

3. **Coarse publication-date assertions are silently treated as exact first-of-period dates.**

   - **File:** `src/tampu/repository.py:878`.
   - **Problem:** The temporal lens pads a year to January 1 and a month to its first day, then compares that invented date with exact daily bounds. It disregards the stored precision and does not declare uncertainty or disclose this interpretation in the lens contract.
   - **Confirmed trigger:** Pass valid fixture assertions `2024`/precision `year` and `2024-03`/precision `month` through the actual `_filter_members` path. Bounds March 15–20, 2024 return no matches and `unknown=0`, although both assertions permit dates in that interval. Bounds January 1 alone return the year-only artifact as a match with `unknown=0`.
   - **Impact:** Supported metadata can produce false exclusions or falsely precise matches and then feed an exact temporal negative. The existing whole-year range test does not exercise this boundary. The binding design requires preservation of publication-date precision (`prototype-design.md:140`). The actual three curated date assertions are day-precise, so this finding does not invalidate the recorded original investigations.
   - **Fix:** Define and disclose precision-aware interval semantics, or classify insufficient precision as unresolved for the requested bounds. Count partial-overlap uncertainty explicitly instead of silently assigning January 1/the first of the month. Test year/month/day assertions against contained, disjoint and partially overlapping ranges, and propagate any unknown/ambiguous scope into negative findings.

4. **Omitted extraction details cannot be paged or attributed to an artifact.**

   - **Files:** `src/tampu/service.py:209`, `:226`, `:292`; `src/tampu/mcp_server.py:48`.
   - **Problem:** Discovery always returns only the first five failure/loss records and five distinct recipes. It exposes omission counts but no processing-detail/recipe continuation. `detail_limit` applies only to facet values. Failure records also omit artifact and projection identifiers, so the caller cannot use the existing inspection path to open the reported affected artifact directly.
   - **Confirmed trigger:** A six-member disposable Service fixture with six declared-loss projections, `detail_limit=100` and the hard maximum 32768-byte budget, still returns five failure records and `omitted_failure_details=1`; the only collection continuation is for revisions. Increasing the budget or following revision/facet cursors cannot obtain that sixth processing record.
   - **Impact:** The promise of cursors for longer omission lists is not implemented (`prototype-design.md:156,175`). The real corpus has many more than five affected artifacts, so this is a current diagnostic limitation, not a hypothetical scale optimization. Larger budgets, as suggested by the results/reproduction prose, recover budget-omitted top-level fields but cannot recover this fixed truncation.
   - **Fix:** Add a bounded, revision-bound processing-detail continuation with artifact/projection identity and access to the complete declared loss/recipe records, including progress-or-controlled-minimum-size behavior. Reuse that facility for omission details rather than adding optional journey machinery. Test more than five affected projections, stable page scope, per-item omissions and default/hard byte bounds; correct the guidance about what increasing the budget retrieves.

#### Minor (Nice to Have)

None separately raised. The declared performance, process-state accounting and SDK sensitivity limits should remain visible in the final handoff.

### Evidence and reproduction assessment

- The controller's exact-head gate records **104 passed, 1 optional extractor skip**, Ruff/compile/diff checks passed; source hashes in that gate still match every current runtime module. I did not rerun it. The unchanged old path harness has its separately recorded 21-pass gate, and the pinned-container readiness/pilot/full extraction evidence covers the ordinarily skipped dependency.
- Independent read-only checks here verified all **32 file/prompt hashes for the 16 frozen comparison payloads**, exact execution-label membership, **473 unique manifest artifacts** with nested **160/320/473** counts, and equality between the durable validation-profile snapshot and runtime profile/reference.
- The retained original-consumer metrics reconcile to **five originals, 97 calls, 270,210 application bytes, 21 application errors and four completed assessments**. The fifth original remains an incomplete observation. These checks establish internal record consistency; they do not independently reproduce model outputs or authenticate every source-semantic judgment.
- Source-bearing traces, PDFs and renders intentionally remain owner-local. The prior task review records the controller's hash/transport checks and material source inspections. I relied on those reported checks for the unredistributed material and did not infer semantic completeness from hashes or page counts.
- Fixed source commits, model-request settings, staged-resumption conditions, masked inputs and original interface schemas are retained. The requested model alias is not a resolved provider revision; generation limits/sampling defaults are partly unknown; the CLI restrictions are not an OS air gap. Fresh replay requires owner-supplied source bytes, dedicated services/configuration and fresh revision IDs. These are adequately declared constraints on reproduction, not missing online-acquisition work.
- N+1 membership/projection reads and materialized discovery history remain acceptable declared prototype limits. The 10-second bound applies per database operation, not to the complete multi-request Service call. The state budget measures serialized journey content, not an OS resident-memory cap. FastMCP schema restoration depends on internals and is justified only against the locked/tested SDK. Preserve these distinctions rather than implying larger-scale performance guarantees.
- The eight MVP criteria have substantial operational evidence. The remaining work is the concrete scope/provenance/discovery contract repair above, plus final documentation/review closure. The inconclusive path pilot, mixed response-only comparisons and adverse original r2 outcome are acceptable results; no replacement consumer study is required to fix these code contracts.

### Recommendations

Address the four Important findings in one consolidated fix wave, with focused regressions and a scoped rereview. Preserve all original schemas, frozen payloads, publication records and observations unchanged; label the corrected interface/recipe behavior as post-observation. Preserve this verdict and its dispositions in the durable implementation handoff before removing the ignored review workspace.

### Assessment

**Ready to merge? With fixes.**

**Reasoning:** This is a working, substantially validated local research prototype with a suitable architecture and candid experimental evidence. Admission uncertainty, cache recipe identity, temporal precision and unreachable processing detail still weaken the core claim that each bounded observation exposes its actual scope; the four targeted repairs should close that gap without broadening the research or architecture.
