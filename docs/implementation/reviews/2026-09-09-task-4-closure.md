### Finding Dispositions

1. **ADDRESSED — binding capability profile** (`src/tampu/capability_evidence.py:8-79`, `src/tampu/service.py:153-168,418-495,1256-1263`). `describe` now exposes `validation_scope` separately from live `collection_scope`. The frozen profile includes all six required mechanisms, uses only the accepted enum statuses, links every status to a result, and records protocol, implementation identities, corpus types/revisions/sizes, and task/model conditions. Live selected-revision source/artifact and per-lens represented/failed/unprocessed/unknown counts remain in `collection_scope`; findings carry the content-hashed profile reference. Paging is explicit through `validation_cursor`, and the tests cover both experiment pages, default-budget bounds, live-count changes without evaluation-scope drift, and finding propagation (`tests/test_service.py:970-1070`, `tests/test_mcp.py:154-178`).

2. **ADDRESSED — predecessor publication guard** (`experiments/growing_corpus/run.py:269-283`). Publication now requires `has_final_assessment is True`, `turn_completed is True`, `turn_failed is False`, no stop reason, zero exit, unchanged source, and at least one MCP call. The parameterized regression varies every rejected condition independently for both publication stages and proves valid summaries reach the existing no-overwrite guard without ingesting (`tests/test_growing_corpus.py:95-153`).

3. **ADDRESSED — inspect listing lower bound** (`src/tampu/service.py:852-858`, `src/tampu/mcp_server.py:238-243`). Service validation now enforces 1..20, matching discovery, MCP schema, and documentation, while search retains its separate count-only `limit=0`. Service tests reject 0 and 21, and the actual stdio MCP test checks those failures plus schema minimum 1 (`tests/test_service.py:1073-1086`, `tests/test_mcp.py:154-167,224-231`).

4. **ADDRESSED — profile-choice chronology/provenance limitation.** The durable record preserves the exact mutable-ledger excerpt plus full-source and excerpt hashes and explicitly says it records ordering rather than an authenticated time or signed preregistration (`experiments/growing_corpus/evidence/profile-decision-ledger.json:1-11`). The results now disclose the initial `-layout`/default-Poppler mismatch, corrected 791-page/774-nonblank comparison, unchanged Unstructured restart, and the limit of that practical choice (`docs/experiments/2026-09-08-usable-prototype-results.md:28`). A focused read-only check confirmed that the preserved ledger hashes match the current source/excerpt and that `validation-profile.json` exactly matches the runtime `CAPABILITY_EVIDENCE` and `PROFILE_REFERENCE`.

### New Critical or Important Breakage

None found in the fix diff. The reported 47-test covering run, strengthened 23-test subset, lint/compile checks, actual MCP boundary checks, and live 8,044/7,600-byte validation pages directly exercise the changed contracts; these suites were not rerun during this scoped rereview.

### Resolved Cannot-Verify Items

The controller reports independently checking the named rendered/source pages, all 97 recorded application responses against Service traces and byte budgets, and the owner-local manifest hashes. Together with the newly durable limited-provenance ledger record, no Task 4 cannot-verify item remains open for this gate.

### Assessment

**Spec compliance:** PASS

**Task quality:** APPROVED

**Reasoning:** Fix round 1 closes each prior Important finding with aligned runtime behavior, public contracts, durable evidence, and focused regressions. The changed surfaces preserve the experiment's adverse outcomes and bounded claims without introducing a new blocking defect.
