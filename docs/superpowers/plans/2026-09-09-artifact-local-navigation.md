# Artifact-local navigation execution plan

> **For agentic workers:** Use superpowers:executing-plans inline; one focused read-only review.

**Goal:** Establish what one bounded navigation strategy can expose using existing tools, and preserve its remaining losses.

**Architecture:** Fixed query inputs feed actual service calls; navigation uses only returned handles/pages. A separate assessment uses the prior frozen source probes.

**Tech stack:** Existing Python, Tampu Service, ArangoDB; no new dependency.

## Global constraints

Follow `docs/superpowers/specs/2026-09-09-artifact-local-navigation-design.md`: two cases, six calls and 49,152 response bytes per case, no new consumer-model runs or runtime mutations, 30-minute initial timebox.

## Task: Navigation record and decision

- [x] Write `experiments/artifact_local/cases.json` with two fixed queries per artifact and references to the prior frozen probes; sign the inputs before searches.
- [x] Write `experiments/artifact_local/run.py`: instantiate existing read-only repository and Service, run each query with `artifact_id` filter, inspect the returned handle, inspect returned physical page plus one, stop at fixed call ceilings. Preserve exact compact responses and trace in a new private directory.
- [x] Run the script once. Assess probe recovery by matching returned evidence identities and prefix/full text; verify byte/call ceilings, stable index, and summary agreement with source-bearing outputs. Failures remain observed failures; no selective retry.
- [x] Write `docs/experiments/2026-09-09-artifact-local-navigation-results.md`, compact results and custody manifest. Distinguish observed capability, research-answer adequacy, and untested unfamiliar-client behavior.
- [x] Obtain one focused read-only review, correct material accounting or claim errors, run `git diff --check`, and preserve signed commits. Verify clean tree and unchanged runtime source; do not push or merge.

Execution: one live rehearsal, 12 calls without application errors, exact offline decision/assessment replay, one read-only review. No production change. The decision report selects explicit element totals and remaining counts as the next implementation task. Final signed preservation closes this plan.

2026-09-10 interpretation correction: the single recovered probe was returned directly by search; adjacent-page navigation recovered none. Counts remain a separate observability proposal, not a remedy established by this rehearsal. See `docs/superpowers/specs/2026-09-10-artifact-local-interpretation-review.md`. Frozen inputs and recorded execution are unchanged.
