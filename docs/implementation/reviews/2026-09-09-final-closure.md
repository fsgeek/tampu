# Scoped final fix review

Reviewed range: `9d4cc883403b2f47c6fdac7d04ec7579c87aa478..86f7c33b535e4197836831406af36abe1249fa7f` using the supplied `review-final-fix.md` package, fix report and original four findings. This is the single scoped rereview of the consolidated wave. Review was read-only except this report; no broad suite or model observation was rerun and no published research database was touched.

### Finding dispositions

1. **ADDRESSED — admission uncertainty and apparent removals.** `src/tampu/repository.py:480,527,549,800` now separates unresolved observations/exclusions from confirmed removals, persists admission outcomes for new revisions and derives them read-only for legacy revisions. `src/tampu/service.py:768,1400,1553` retains that admission scope in search nodes, search responses and bounded-negative findings; the fields are not optional packing targets. `src/tampu/capture.py:271` conservatively marks an unknown entry type as incomplete enumeration. The six public ingestion regressions cover file/subtree/unsafe-root failure both with and without a predecessor, including search-to-finish propagation; the legacy-revision test checks that reading the derived summary does not alter the stored document (`tests/test_repository.py:705,798`). Exact zero is appropriately limited to the selected representation while unresolved source scope remains explicit. There is a small report-wording correction below, not an unresolved original defect.

2. **ADDRESSED — current extraction recipe identity.** `src/tampu/extraction.py:16,351,382` establishes adapter, profile and normalization versions and probes current Poppler identity before cache lookup. The pinned Unstructured image remains part of the recipe. A failed version probe produces a controlled failed projection and retains its raw diagnostic. Same-store tests cover Poppler/adapter/normalization changes, unchanged-recipe reuse, failed probing and retained old files (`tests/test_extraction.py:442,477,494`); the real-repository successor test checks `processing_changed`, unchanged old membership/projection, and searchable old evidence (`tests/test_repository.py:862`). The repair does not migrate historical projections or reprocess the published experiment. Version constants now create an explicit maintenance obligation: behavior changes require the appropriate version bump.

3. **ADDRESSED — publication-date precision.** `src/tampu/repository.py:953` uses year/month/day calendar intervals with definite containment, disjoint exclusion and explicitly ambiguous partial overlap. Missing and ambiguous counts are separate, and `temporal_scope` survives into the search and negative finding even when optional lens configuration is omitted (`src/tampu/repository.py:800`; `src/tampu/service.py:1400,1553`). Nine interval cases cover the original January-1 and mid-March triggers as well as contained/disjoint ranges, and the real-repository test checks the ambiguous count in an exact selected-subset negative (`tests/test_repository.py:778,798`). Discovery documents these semantics. The unchanged day-precise original experiment metadata does not need retrospective reinterpretation.

4. **ADDRESSED — reachable, attributed processing detail.** `src/tampu/service.py:128` adds processing/admission detail pages; each processing recipe and individual loss carries artifact/projection identity. The cursor binds collection, selected revision, detail kind and offset, and its arguments are exposed through the real MCP wrapper (`src/tampu/mcp_server.py:48`). Packing removes only whole trailing records and advances the cursor, or returns a controlled minimum-size error identifying the blocking processing record when the error budget permits (`src/tampu/service.py:1714`). Tests traverse seven recipes and 56 losses after current revision changes, reject a mismatched revision, check small/default/hard budgets and oversized-record identity, and exercise both detail routes through actual stdio MCP (`tests/test_service.py:1089,1174`; `tests/test_mcp.py:287`). README, results and reproduction guidance now distinguish fixed summary caps from optional fields omitted for budget.

### New Critical or Important issues

None found in the fix diff. All four original Important findings are closed.

### Nonblocking documentation correction

**Minor — `docs/implementation/2026-09-09-final-review-fixes.md:9` overstates repeated pagination disclosure.** The sentence “Search/result continuations retain the summary in mandatory response/state” should distinguish retained node state from each returned envelope. The new admission summary is present in search responses and negative findings and remains in the node; the existing `inspect` candidate-pagination envelope does not repeat it. A temporary Service-only probe confirmed successful pagination with the admission summary retained in the node and absent from that page's result/scope. Narrow the report sentence to “Search responses and stored result nodes retain the admission summary; bounded negatives copy it.” This is a documentation correction, not a request to expand the unchanged inspection response contract or reopen the original finding.

### Verification and retained limits

- The fix report records meaningful red/green evidence followed by **130 passed, 1 optional extractor skip**, plus clean Ruff, compile and diff checks. The changed real-MCP tests cover the new arguments and pagination; the prior 1000-byte search test was adjusted to 1600 bytes to fit the additional mandatory scope while still asserting a byte bound. I did not rerun these passing suites.
- An independent hash check here confirmed that all five changed runtime modules match the verified implementation hashes in the fix report. Its later documentation/receipt commits do not change those runtime bytes.
- The reported read-only live summary/processing/admission checks fit default budgets at **8003/7982/5764 bytes**. These are application JSON measurements, not wire framing. No additional live database probe was necessary for this rereview.
- One complete record exceeding the 32768-byte ceiling remains unavailable through MCP; the service returns a controlled error without skipping it, and the documentation explicitly directs owner-local access. This is a declared representation limit, not a claim that every arbitrary record can be serialized into the public budget.
- Detail discovery still materializes records and performs N+1 reads. The 10-second timeout is per database operation, journey capacity measures serialized state, and schema restoration depends on the locked/tested FastMCP internals. Those existing limits remain honestly described and do not require new architecture in this fix.
- Frozen inputs, original tool schemas, publication observations and consumer records are outside this fix diff. The documentation labels the new behavior post-observation and preserves the adverse/inconclusive outcomes without inferring new consumer benefit.

### Assessment

**Spec compliance of the four repairs: PASS.**

**Quality: APPROVED. Ready to merge: Yes.**

The consolidated changes close the material scope, provenance, precision and detail-access defects with focused regression and actual transport evidence. The minor report wording can be corrected during durable closure; it does not require another implementation wave or rereview. This verdict assesses the working local research prototype and its declared limits, not production-scale readiness or established consumer benefit.
