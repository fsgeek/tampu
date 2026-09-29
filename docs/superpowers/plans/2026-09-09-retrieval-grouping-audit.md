# Retrieval grouping audit implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline. The agreed scope is one diagnostic and one focused reviewer, not a new multi-agent implementation campaign.

**Goal:** Produce an inspectable comparison that identifies whether matching, ranking, artifact grouping, or output packing hides known evidence.

**Architecture:** Freeze six exposed development cases before reading new rankings. Capture a single ranked lexical match set per case from a pinned revision, then compare two deterministic presentations offline.

**Tech stack:** Existing Python 3.14 environment, python-arango, pytest; no new dependencies.

## Global constraints

- Initial timebox: 2026-09-09 14:32:13–15:32:13 UTC; report incomplete findings if necessary.
- No consumer-model calls, ingestion, index changes, production changes, push, or merge.
- Read-only database access through `Repository(..., initialize=False)`.
- Same revision, predicates, scores, metadata, 800-character prefix excerpts, 20-entry ceiling, and 8192-byte UTF-8 JSON ceiling for both arms.
- One best passage per artifact versus globally ranked passages. This is a normalized presentation audit, not an exact MCP replay.
- Capture at most 20,001 matches per case; more than 20,000 makes the paired conclusion inconclusive. No selective query retries.
- Full source-bearing captures and responses stay owner-local. Commit protocol, case identities/hashes, executable comparison, tests, and compact results.
- Freeze cases and protocol in a signed commit before executing new lexical queries. These are builder-selected development probes, not exhaustive relevance judgments or a general benchmark.

## Task 1: Auditable paired diagnostic

Files: `experiments/retrieval_grouping/{cases.json,protocol.md,run.py,results.json,README.md}`, `tests/test_retrieval_grouping.py`, `docs/experiments/2026-09-09-retrieval-grouping-results.md`.

Interfaces: `rank(rows, presentation) -> list[dict]`; `pack(rows, scope, presentation, budget=8192, limit=20, excerpt_chars=800) -> dict`; `compare(capture, cases) -> dict`. The CLI captures once into a new owner-local directory or replays an existing capture into a new directory.

- [x] Freeze cases with exact trace/control origin, revision, artifact/projection/ordinal, page, text SHA-256, and required excerpt length. Validate source bytes through existing projection custody checks.
- [x] Write failing tests for artifact grouping and ties, UTF-8 whole-prefix packing, clipped evidence, stage attribution, and refusal of incomplete/unstable captures. Run `uv run pytest tests/test_retrieval_grouping.py -q`; expect missing module failure.
- [x] Implement pure deterministic comparison plus bounded read-only capture and offline replay. Ranking key is `(-score, artifact_id, ordinal)`; grouping keeps the first row for each artifact. Packing appends whole entries in order and stops at the first entry that violates either ceiling. Probe analysis distinguishes unmatched, grouped away, selected but omitted by rank/capacity, and excerpt truncation.
- [x] Run focused tests to green. Capture the six frozen cases once; compare index-generation fingerprints before and after. Preserve overflow/errors as inconclusive instead of manufacturing exact counts.
- [x] Replay offline and compare outputs byte-for-byte. Review source-bearing outputs locally; write compact results without full paper excerpts. Record known-probe recovery and artifact breadth separately.
- [x] Request one read-only focused review of fairness, accounting, and claims. Resolve material issues within the timebox; record remaining limitations.
- [x] Verify focused tests, `git diff --check`, signed commits, unchanged production files, and clean tree. Preserve the report in a signed commit without pushing or merging.

Execution record: completed inline with one read-only review. Seven focused tests passed; all six captures were complete, all 14 offline replay files identical, and six production grouped queries matched the export. Source preflight failures abort without per-case records; this deviation is disclosed in the report. Final verification and signed preservation are performed as the closing step.
