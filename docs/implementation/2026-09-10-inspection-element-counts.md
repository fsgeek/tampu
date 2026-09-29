# Inspection element counts

Artifact, physical-page, and exact-ordinal element listings now return `total_elements` and `remaining_elements`. Totals cover the complete selected range in the pinned projection. Remaining elements are those after `offset + returned_count`. Empty selections report zero; continuation pages retain the original total.

The two fields are separate from the search node's candidate-artifact count. They do not count relevant passages or summarize semantic content. Evidence slices and search result pagination retain their existing contracts. README and the MCP inspect description explain the fields and how to retry an oversized element listing.

The implementation adds two result fields in `Service._inspect_elements`. Contrary to the initial assumption during experiment planning, the existing byte-budget fitter does not trim element lists. This change preserves `budget_too_small` on an oversized listing and transactional continuation behavior, instead of introducing a new packing strategy. Successful responses retain both counts. The extra fields consume response bytes, so a request at a former exact byte boundary can require a slightly larger budget or smaller limit.

## Validation

Seven new test cases failed on the missing count fields before implementation, then passed. They verify physical-page continuation (33 total, 20 returned, 13 remaining; then 13 returned, zero remaining), whole-artifact and exact-ordinal scope, empty scope, distinct search-count units, and unchanged journey state after rejecting an oversized continuation response. Retrying the same continuation returns the correct remaining elements.

`python -m pytest tests/test_service.py tests/test_mcp.py -q`: **35 passed**. This covers the service, MCP interface, and the existing service integration tests; it is not a claim that every repository test was rerun.

A read-only check used the already known physical page 409 of the pinned proceedings artifact. It returned `(total, returned, remaining) = (33,20,13)` in 6,646 response bytes, followed by `(33,13,0)` in 4,500 bytes. All 33 delivered ordinals were distinct, and the observed index fingerprint was stable. Exact response hashes, revision identity, and owner-local trace paths are in [the check record](2026-09-10-inspection-counts-check.json).

This check supplied the known page explicitly and is **not a navigation experiment**. It does not revise the earlier finding that the fixed adjacent-page strategy recovered no additional assessed passages. Counts expose the amount of unfinished inspection; their effect on client decisions and retrieval effectiveness remains untested.

The work is preserved on `feat/inspection-element-counts` in the existing isolated worktree. No extraction, index or database mutation, consumer-model run, push, or merge is part of this change.

One focused read-only review (`/root/element_counts_review`) found no material issue in range semantics, mandatory count fields, byte-budget rollback, or documentation. The reviewer independently ran the seven new test cases successfully. The coordinator verified the four owner-local live-check files against their recorded byte sizes and SHA-256 hashes.
