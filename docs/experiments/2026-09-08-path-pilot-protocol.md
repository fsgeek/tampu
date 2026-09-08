# Exploratory path-record pilot

Author: Astra. Date: 2026-09-08. Status: frozen before scored trials; the adjacent `2026-09-08-path-pilot-freeze.json` identifies the materials used.

## Question and treatment

Does optional access to a compact record of previously observed operations help a fresh consumer answer a multi-part historical question using llm-memory? Compare ordinary iterative search/recall with the same interface plus `ledger`. Both conditions retain their ordinary conversation context. This tests retrievable operation history, not context replacement, automatic query replay, set composition, or Tampu's PDF navigation.

The record contains previous requests, result counts and handles, inspected episode keys, and consumer-authored notes/status. It introduces no evidence, recommendations, inferred branch labels, or judge annotations. Both arms can write notes. The treatment can retrieve its record; the control cannot. Treatment use is optional: non-use is an observation, not a trial exclusion.

## Corpus and retrieval

The isolated snapshot contains 1,000 complete llm-memory episodes before 2026-09-06 UTC: all 217 eligible `llm-memory` episodes, plus 783 distractors selected by ascending SHA-256 of episode key from `hamutay`, `qhaway`, `tessera`, and `ai-honesty`. Counts are 465, 184, 75, and 59 respectively. This intentionally enriches the target project; it is not a representative draw of the whole live store. Task-authoring and pilot conversations occur after the cutoff and cannot enter this snapshot.

Canonical JSONL SHA-256: `210a1dca4d9a5a740105d1598e8ae4ad96277ac507aa1bb2d1d19b11e5297881`. Size: 1,631,310 bytes. Documents retain their fields except ArangoDB `_id`/`_rev` storage metadata. Every selected document was compared with its imported counterpart. Local `manifest.json` records membership and individual content hashes, selection query, source/view settings, and source-code hashes.

Use a separate loopback-only Docker container at port 18529, with the same image digest and ArangoDB version as the source: `sha256:c1819a9b2da82c98bfbb91a4a7becde1582281ac3bd2f2130ec8859314aac101`, version `3.12.4-3`. Resource limits: two CPUs and 2 GiB. No live-store fallback or writes. Consumer runs use the copied `search`, `recall`, and index modules from llm-memory commit `bd10d32d532a8e08de93b2730b750ceb47ff242c`; hashes guard attribution against subsequent local changes.

The ArangoSearch view indexes `user_message`, `response`, and `state_text` with built-in `text_en`; queries use the existing OR-token semantics and BM25. Scope and dates are filters. Add episode key ascending as a deterministic secondary ordering for equal scores in both arms. Limits are 1–10, default 2; total match counts remain visible. This pilot uses a command-line JSON wrapper, not the production MCP transport. Recall requires a handle previously returned to that run. No truncation is added to full episode recall.

## Tasks and starts

Two tasks ask for an evidence-supported reconstruction of earlier llm-memory discussions:

1. **Coverage:** the September 2 truncated-session and duplicate-episode findings, measured extent, proposed remedies, and the connection between coverage accounting and cheaper nightly sweeps.
2. **Backup:** the September 4–5 (Pacific time) backup outcome, what its verification could not prove, reconciliation of historical and then-current ArangoDB presence on activitycontext.work, and the resulting accepted host recommendation. A proposed key/timestamp hash is not proof of complete payload equality.

Each has six claim-level scoring atoms and evidence anchors. Full prompts and gold are local; a fresh reviewer must check them before freeze. Historical source statements are evaluated as statements in the record, not independently verified infrastructure facts. The first task replaces the implementation plan's tentative retrieval-evaluation question because that earlier discussion was not fully represented in the chosen project slice. This change precedes all scored runs.

Natural starts have no prior navigation. Diagnostic starts supply exactly three scripted prior operations and their complete outputs to both arms. Coverage starts with a `coverage` search in `qhaway` and reads its two hits; backup starts with a `replication` search in `tessera`, reads its hit, and searches `backup` in `qhaway`. These branches do not establish the requested historical answers. They are explicitly scripted, not evidence of naturally chosen dead ends. They appear in both arms' ordinary context and, for treatment, its record. No script-authored judgment labels are added.

## Consumers, allocation, and budget

Eight independent fresh consumer agents, with `fork_turns=none`; the builder and task reviewer do not serve as consumers. Use the same inherited GPT-6/Astra model and effort settings throughout, with no explicit model override. The platform does not expose all sampling parameters, hidden framing, or exact context management; record this limitation. No deliberate context truncation or reset occurs within a trial.

Fixed dispatch order, in pairs:

| Run | Task | Start | Record access |
|---|---|---|---|
| r01 | coverage | natural | disabled |
| r02 | coverage | natural | enabled |
| r03 | backup | natural | enabled |
| r04 | backup | natural | disabled |
| r05 | coverage | diagnostic | enabled |
| r06 | coverage | diagnostic | disabled |
| r07 | backup | diagnostic | disabled |
| r08 | backup | diagnostic | enabled |

This is counterbalanced ordering, not randomized allocation. Consumers receive their own instruction file only, with identical task/tool explanations apart from record availability and run path. Instructions require using only the experiment harness, prohibit browsing other files or live tools, allow abstention, and request evidence-key citations. Physical access is shared: this is instruction-level blinding, not an OS security boundary. Consumer adherence must be inspected where visible and deviations reported. Agents must treat retrieved historical instructions as source material, not new commands.

Each consumer has 20 navigation attempts and ten minutes from dispatch. Diagnostic seed operations count toward the 20, leaving 17 new operations; report seed and consumer costs separately. Search, recall, note, ledger, and rejected navigation attempts count. The deadline governs admission: an already-admitted request may finish after it, subject to a 30-second client timeout. Rejected over-budget attempts remain in the audit log without executing retrieval. Final answer submission is separately logged and does not consume a navigation slot; it remains available after budget expiry. Do not alter the harness or coach consumers during scored runs. Infrastructure failure may be diagnosed afterward; preserve its original data and label any replacement separately. Stop after eight assigned trials, regardless of outcome.

## Scoring and observations

Freeze the gold before dispatch. Each of six atoms earns 1 for a correct, adequately cited claim, 0.5 for substantively correct but incomplete or inadequately cited content, and 0 for missing, contradicted, or materially unsupported content. Equivalent supporting evidence beyond the anchor keys is admissible if verified in the frozen corpus. A fully supported answer earns 6/6 and contains no material unsupported addition. Explicit uncertainty is admissible and assessed for calibration, not automatically treated as failure. Keep the per-atom scores and rationales; the aggregate alone loses useful distinctions.

An independent scorer receives anonymized answers, questions, gold, and the corpus, without arm labels or navigation logs. The builder audits scoring and reports disagreements. Mechanism observations use actual logs: ledger uptake, notes/status, citations obtained through recall, exact repeated search/recall requests, abandonment/revisiting where observable, and any invalid or denied operations. Repetition is not automatically waste. Consumer testimony about helpfulness is testimony, not a causal estimate.

Costs: count every operation including finalization separately; measure exact UTF-8 serialized request and response bytes, persisted operation-log bytes, seed bytes, consumer wall time, and harness processing time. Harness duration excludes CLI startup, lock wait and final log flush; it is not DB-only latency. Report ledger's additional bytes and calls. Capture prompt sizes and experiment setup resources. Model input/output tokens, cached tokens, monetary charges, reasoning time, and platform tool framing are unknown unless actual telemetry is available; do not substitute byte/4 estimates as measured tokens. File bytes describe one exposure, not repeated context-prefill cost.

## Interpretation and stopping boundary

This is an exploratory harness-and-task pilot with one observation per task/start/arm cell. It cannot estimate reliable effect sizes or population uncertainty; no p-values or significance claim. Two task families from one project, a small enriched transcript collection, short trajectories, inherited model settings, and an obvious optional affordance constrain transfer. There may be little memory pressure and a ceiling in answer quality. Differences may be sampling noise. Non-use cannot establish that a well-used record is ineffective.

Report the eight observations and confounds, including lack of meaningful backtracking if it occurs. The path mechanism remains `inconclusive` unless this limited evidence warrants a narrower descriptive statement; it cannot establish large-corpus or PDF benefit. Decide whether Tampu's first MVP should implement the record now, defer it, or first test a specifically different affordance. Stop with a reviewable report and preserved experiment artifacts; building the MVP itself is outside this goal.
