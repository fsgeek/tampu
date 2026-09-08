# Path-holding pilot implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run eight fresh-consumer trials on an isolated llm-memory snapshot and leave a reviewable report, including an inconclusive outcome.

**Architecture:** A disposable local ArangoDB uses the existing llm-memory search/recall implementation. A small command-line harness records every operation and exposes that record only in the treatment arm. Research materials live under ignored `tmp/path-pilot`; reusable experiment code and the protocol/report are tracked, separate from Tampu's product package.

**Tech Stack:** Python 3.14, python-arango from the existing llm-memory environment, ArangoDB's existing local image, pytest, fresh Codex consumer agents.

## Global constraints

- Governing design: `docs/superpowers/specs/2026-09-08-disposition-of-claude-follow-up.md`.
- Both arms retain ordinary conversation context. Only retrievable operation history differs.
- No live-store writes, model-generated ledger summaries, judge annotations, automatic replay, or hidden evidence in the consumer surface.
- Maximum 20 navigation operations and ten minutes per consumer, counting ledger accesses and diagnostic seed operations.
- Eight exploratory trials: two tasks × two start types × two arms. No optional stopping based on results, no significance claim, no PDF transfer claim.
- Freeze protocol, task/evidence hashes, snapshot membership, code, index configuration, and consumer instructions before scored runs. Report departures explicitly.
- Corpus and full run logs remain local and ignored; publish hashes and aggregate observations, not private transcripts.

## Task 1: Isolated corpus and navigation harness

**Files:** Create `experiments/path_holding/harness.py`, `experiments/path_holding/test_harness.py`, `experiments/path_holding/README.md`; local materials at `tmp/path-pilot/`.

**Interfaces:** `invoke(run: Path, request: dict) -> dict` accepts `search(query,scope='all',limit=2,since=None,until=None)`, `recall(key)`, `note(text,status)`, and `ledger(offset=0,limit=10)`. Results and requests append to that run's JSONL log; result bytes and elapsed time are measured. `ledger` returns only compact operations already visible to that run, never hidden gold or episode bodies. Baseline rejects ledger access. Notes are available to both arms; they store consumer declarations, not system inferences.

- [ ] Write behavioral tests using a three-episode Arango fixture: search count exceeds limit; scope/date restriction; recall from snapshot; identical results in both arms; record excludes unseen evidence and the current ledger call; rejected access and all calls count toward budget; run separation; finalization; hash mismatch rejection.
- [ ] Run `/home/tony/projects/llm-memory/.venv/bin/python -m pytest experiments/path_holding/test_harness.py -q` and record the expected failure before implementing.
- [ ] Implement the interface with the existing `llm_memory.search.search` and `llm_memory.recall.recall`, copied into the private snapshot vendor directory with source hashes. Add `_key` ascending only as a deterministic score-tie breaker in both arms. A fixed loopback-only experiment endpoint has no live-store fallback.
- [ ] Export llm-memory episodes before 2026-09-06 UTC and a deterministic hash-selected distractor sample from hamutay/qhaway/tessera/ai-honesty, up to 1,000 episodes total. Preserve complete documents except database revision metadata; record source and content hashes. Import into the separate server and check content equality and repeated-query ordering.
- [ ] Run the full harness tests against the separate server, review all evidence surfaces, and commit explicit experiment files.

## Task 2: Freeze independently checked tasks and protocol

**Files:** Create `docs/experiments/2026-09-08-path-pilot-protocol.md`; private `tmp/path-pilot/tasks.json`, `gold.json`, `manifest.json`, and per-run prompts.

**Interfaces:** Tasks contain task ID, question, and scripted diagnostic operations. Gold contains claim-level evidence keys and known tempting errors. Consumer prompts contain the task and tool contract only, plus the same diagnostic history for both arms when applicable.

- [ ] Author two multi-part questions grounded in actual earlier llm-memory episodes: the retrieval evaluation correction, and the distinction between current freshness and historical coverage. Adjust wording to actual corpus evidence before freeze.
- [ ] Have an independent fresh reviewer verify questions against full evidence and assess whether each diagnostic start fails to settle its task. Revise before any scored consumers run.
- [ ] Freeze the eight-cell order, scoring rubric, access policy, model declaration, budget, and exclusions in the protocol. Preserve exact prompts and hashes. Commit the protocol before collecting scored outcomes; this is an exploratory development pilot, not a powered confirmatory preregistration.

## Task 3: Fresh consumers, audit, and report

**Files:** Private per-run JSONL logs and answer files; create `docs/experiments/2026-09-08-path-pilot-report.md` and a public aggregate result JSON.

**Interfaces:** Each consumer receives exactly one run directory and instruction file, with no parent history or other runs. Final answers use episode keys as citations and may explicitly abstain. Scoring checks required claims against frozen gold; an independent audit checks scoring and report claims.

- [ ] Run two natural-start pairs and two diagnostic-start pairs with fresh consumers. Keep both arms on the same model and inherited context settings. Do not coach consumers or change the harness mid-run.
- [ ] Compute actual search/recall/note/ledger calls, exact repeated requests, response bytes, log storage, elapsed time, task completion and unsupported-claim observations. Distinguish harness time from consumer wall time. Mark inaccessible model tokens, pricing, and hidden platform framing as unknown.
- [ ] Audit snapshot and harness hashes after runs; verify citations and score both arms against the same rubric. Retain errors and failures; only demonstrated infrastructure failures can be excluded, with original logs preserved.
- [ ] Write and independently review the report. State implications for the smallest Tampu MVP and limitations of transcript-to-PDF transfer. Run final tests, preserve the branch, and mark the goal complete only after the report is reviewable.

## Planning decisions

The tasks share the frozen corpus and harness, so implementation is inline. Fresh independent agents are appropriate for evidence review, scored consumption, and the final audit; the dispatching-parallel-agents skill governs their isolated instructions. Worktree: `tmp/path-pilot-worktree`, branch `experiment/path-holding-pilot`. Main had no pre-existing tests; its locked environment installed successfully. The existing Arango image is reused by digest to match the source server's version. No Tampu product behavior is introduced.
