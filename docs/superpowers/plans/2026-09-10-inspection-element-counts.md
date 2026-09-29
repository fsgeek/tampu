# Inspection element counts implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline, one focused review.

**Goal:** Expose exact selected and remaining element counts without changing inspection traversal or budget-failure semantics.

**Architecture:** Calculate counts from the selected normalized element list in `Service._inspect_elements`. Existing continuation offsets and transactional response fitting remain authoritative.

**Tech stack:** Existing Python service and pytest; no dependencies or schema migration.

## Global constraints

Follow `docs/superpowers/specs/2026-09-10-inspection-element-counts-design.md`. Existing isolated worktree, branch `feat/inspection-element-counts`; signed preservation, no push or merge. This change makes omissions observable, not retrieval more effective by demonstrated evidence.

## Task: Count contract

Files: `src/tampu/service.py`, `src/tampu/mcp_server.py`, `tests/test_service.py`, `README.md`.

- [x] Add tests using a 33-element page plus another page: verify exact total/remaining counts for initial and continuation responses, artifact/ordinal/empty selections, and unchanged continuation after an oversized request. Run `pytest tests/test_service.py -k element_counts`; expect missing-count-field failures.
- [x] Add `total_elements: len(selected)` and `remaining_elements: len(selected) - next_offset` to the element-list result. Keep byte-budget failure behavior. Document count units and scope in the MCP description and README.
- [x] Run targeted tests and the service/MCP test suites. Run a read-only check against the known 33-element page at revision `0ea79b79668943969e5ee21dfdcbdfae`; record output counts and byte ceilings as a contract check, not a new navigation success.
- [x] One focused review of counts, scope, and budget rollback. Resolve material issues, verify diff, and preserve signed commits and a brief implementation record.

Execution completed: seven new tests red then green; 35 service/MCP tests passed; read-only page check and custody verification passed; focused reviewer found no material issue. Oversized element lists retain the existing budget-error behavior. See the implementation record for evidence and limits.
