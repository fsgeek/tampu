# Usable prototype: growing-corpus development observations

Observed 2026-09-08–09. Tampu now completes the capture → extraction → immutable publication → lexical search → bounded inspection → scoped finding path. The consumer evidence is **mixed**: the Legible Consensus revisit identified a changed justification and unchanged threshold; the final eviction investigation exceeded its tool budget without a final assessment. These are builder-exposed development observations, not held-out evaluation, statistical effectiveness evidence, or superiority over another retrieval system.

The [reproduction guide](../../experiments/growing_corpus/README.md), [fixed scenario](2026-09-08-temporal-growth-scenario.md), [source manifest](2026-09-08-temporal-growth-manifest.json), [compact measurements](../../experiments/growing_corpus/evidence/) and [independent source review](../../experiments/growing_corpus/evidence/source-review.md) retain the operational and scientific distinctions. Full source-bearing traces remain owner-local; the [manifest](../../experiments/growing_corpus/evidence/owner-local-evidence-manifest.json) records their locations, sizes and SHA-256 hashes. Hashes establish byte identity, not truth or semantic completeness.

## Extraction and publication

The twelve-PDF pilot covered short and long caching papers, theory, two-column systems/HCI papers, a thin-output PDF, historical scanned material, two real versions, and a 635-page proceedings artifact. Both profiles attributed text to 774 of 791 physical pages. Their outputs are comparison representations, not ground truth. Successful extraction does not certify equations, figures, reading order or semantic completeness.

| PDF | Physical / text pages | Unstructured container seconds | Poppler adapter seconds |
|---|---:|---:|---:|
| Short caching | 3 / 3 | 24.87 | 0.09 |
| Long caching | 19 / 19 | 11.95 | 0.27 |
| Thin Paxos | 2 / 1 | 9.10 | 0.05 |
| Pichay | 15 / 15 | 17.83 | 0.28 |
| Legible v2 | 15 / 15 | 14.59 | 0.20 |
| Legible v3 | 16 / 16 | 11.09 | 0.24 |
| Online optimization | 29 / 29 | 19.09 | 0.36 |
| Software-defined caching | 8 / 8 | 11.47 | 0.14 |
| Learned data structures | 27 / 27 | 15.89 | 0.38 |
| Copy-aware desktop | 10 / 10 | 10.91 | 0.29 |
| Multics | 12 / 12 | 11.08 | 0.16 |
| NSDI proceedings | 635 / 619 | 199.85 | 17.42 |

[Per-file profiles, versions, losses, attribution and overlap measurements](../../experiments/growing_corpus/evidence/extraction-pilot.json) and [final per-page Poppler adapter measurements](../../experiments/growing_corpus/evidence/poppler-adapter-pilot.json) preserve the comparison. Poppler's final adapter total was 19.88 seconds; the earlier separate explicit-page NSDI comparison was 17.22 seconds. Whole-document form-feed splitting was rejected because it yielded 637 separators for 635 physical pages; the supported Poppler profile extracts each physical page explicitly.

The controller chose pinned Unstructured fast for paragraph/category/coordinate utility after rendered spot checks, while the readiness recommendation favored Poppler's speed. These are different priorities, not evidence of semantic equivalence. The primary image was `downloads.unstructured.io/unstructured-io/unstructured@sha256:806726e3997d33bce9e32facd86c947b241101c58496f2774ad5f09f86e798bc`, Unstructured 0.23.3, with no network, 8 GiB container memory and a 300-second per-file timeout. The [mutable controller ledger excerpt](../../experiments/growing_corpus/evidence/profile-decision-ledger.json) records this choice before prewarming, but does not authenticate its time or constitute signed preregistration. The initial adapter used `-layout` while the readiness comparison used default Poppler; the initial reading-order comparison therefore mixed configurations. The corrected adapter comparison used default Poppler independently per physical page (791 pages, 774 nonblank across twelve PDFs). After that correction, prewarming restarted with the unchanged Unstructured primary selection. This is recorded process ordering and a reaffirmed practical choice, not proof that Unstructured has better semantic coverage. Poppler was version 22.02.0.

Rendered checks of long caching p.14, Pichay p.12, Legible v2/v3 p.10 and proceedings p.409 confirmed selected material claims and revealed reading-order/equation limitations. For example, long caching's CitiBike table says 24 sequences while prose says 12; the unresolved discrepancy is in the rendered source. No full paper or render is redistributed in Git.

The cached full extraction completed in **1,796.58 seconds with four workers**: 473 `ready` projections, 353,808 normalized elements, 16,990 physical pages and 12,198 text pages. **27 artifacts returned no text despite successful processing.** CORFU's specific cause was reproduced: the upstream complexity gate flags page 4's 11,459 graphics operations versus 45 text operations, skips extractable elements and lets explicit fast extraction return empty success. A separate internal diagnostic recovered 24 pages; this was not a product patch or automatic fallback. The other 26 causes remain untested. [Full measurements](../../experiments/growing_corpus/evidence/full-extraction.json)

One registered working root grew monotonically from the prepared snapshots. The inventory contains 479 aliases for 473 byte-distinct artifacts; six duplicate aliases were collapsed in this fixture, with original aliases retained in the manifest. Simulated admission stages are not publication dates. Only three source-checked metadata records have version-posting dates; the other 470 remain unknown.

| Stage | Actual revision ID | Captured / ready / failed | Physical / text pages | Publish wall seconds |
|---|---|---:|---:|---:|
| r0 | `fa9221b03c3b4aaaa7c54125f23eadb9` | 160 / 160 / 0 | 4,467 / 4,327 | 204.22 |
| r1 | `7e44b119852a4f16b5f470b321fa91ef` | 320 / 320 / 0 | 10,565 / 8,464 | 363.09 |
| r2 | `0ea79b79668943969e5ee21dfdcbdfae` | 473 / 473 / 0 | 16,990 / 12,198 | 528.29 |

These publication times include copying/hash verification and cached ingestion/indexing, not fresh full extraction. r1/r2 record clean source identities before and after, the immediate predecessor and exact counts. r0 was already published and was deliberately reused: its original source commit records HEAD when the record was written, not import-time module hashes. Concurrent changes concerned timeout/search handling rather than ingestion code; [the narrow attribution limitation is preserved](../../experiments/growing_corpus/evidence/r0-attribution-limitation.json). [Publication records](../../experiments/growing_corpus/evidence/publications.json)

After r2, both baseline PDFs, raw outputs and normalized element files matched all six earlier hashes; the old r0 memberships retained the exact projection selections. Fresh Service searches and slices reopened the pinned old evidence. This verifies earlier evidence, not historical BM25 score re-execution. [Old-evidence audit](../../experiments/growing_corpus/evidence/old-evidence-after-growth.json)

The selected 473 artifacts occupied 952,559,194 PDF bytes, 235,070,019 raw-extraction bytes and 155,828,193 normalized-element bytes. These logical file sizes exclude duplicate snapshots, alternate diagnostics and ArangoDB disk/index overhead. Runtime versions were Python 3.14.3, ArangoDB 3.12.9-4, python-arango 8.3.5 and MCP SDK 1.30.0. [Storage/runtime record](../../experiments/growing_corpus/evidence/storage-runtime.json)

## Diagnostics and actual consumers

All extra diagnostic collections used a **different database** from the original consumers, so future diagnostic sources and shared BM25 statistics did not contaminate the staged research collection. They reused immutable cached artifact/projection files, with explicitly selected alternate projections only in the diagnostic database.

| Required diagnostic | Observed check |
|---|---|
| Known passage | Real short-paper p.2 ordinal 38 inspected; deterministic old-red passage searchable in its original tiny revision. |
| Recovery from misleading results | Controlled broad-to-alias refinement succeeded. Original Legible r0 independently recovered from `Earth-node` zero to a spaced variant; these are distinct evidence. |
| Duplicate versus work | Three paths containing a v2 byte copy and v3 produced two artifacts sharing one source-attributed arXiv work ID. Similar caching reports were not asserted to be formal versions. |
| Processing failure | A deliberately truncated PDF remained captured with a failed projection. CORFU separately demonstrated successful-empty processing. |
| Bounded lexical negative | Exact `tampuabsentpredicateqxz` phrase zero in the short-paper's fully covered selected representation; a bounded finding was recorded without semantic absence. `PredictiveMarker` zero versus `Predictive Marker` one demonstrates why surface-form failure cannot settle concept absence. |
| Changed source/revision | A tiny genuine-PDF fixture added, replaced and removed one path each; old text remained searchable in the old revision. Explicit CORFU Unstructured → Poppler reprocessing kept the artifact hash, changed one projection selection, produced `processing_changed: 1`, recovered 24/24 text pages and preserved the old empty projection. |

[Diagnostic records](../../experiments/growing_corpus/evidence/diagnostics.json) distinguish machine assertions from source interpretation. The first diagnostic setup incorrectly selected the other, 2012 CORFU paper by title substring; a coverage assertion caught it before model comparisons. That [failed attempt](../../experiments/growing_corpus/evidence/diagnostic-failed-attempt.json) is preserved. The corrected setup pinned the full required 2013 artifact hash and used a fresh isolated database/output. A preview-only evidence capture also failed comparison-input construction; an actual follow-up handle inspection supplied the final frozen passage. No substantive model response was replaced.

Five originals used requested `gpt-5.6-sol`, medium reasoning, Codex CLI 0.153.4, identical default sampling, an instruction of at most 20 tool calls/600 seconds, and actual Tampu MCP tools. The CLI does not expose the resolved model revision or a verified numeric generation cap. Every schema, argument, response, prompt, usage report and termination is retained. Each successor received only its prior completed assessment/citations: **staged resumption**, not continuous process memory. The consumer had an empty working directory, no shell/apps/browser/web tools or host skill discovery, and only Tampu's four tools. These recorded restrictions are not an OS air gap or a proof against pretraining exposure.

Truthful state-changing tool annotations were retained. The owner authorized temporary process-local journeys/findings and full-content local tracing; the supported `on-request`/`auto_review` route was used without bypass. No actual approval rejection occurred. The CLI warning about under-development skill-discovery suppression is retained separately from application errors. Per-call reviewer reasoning was not exposed.

| Original | MCP calls | Seconds | Application JSON bytes | Input / cached input / output tokens | Outcome |
|---|---:|---:|---:|---:|---|
| Eviction r0 | 20 | 149.66 | 61,212 | 212,496 / 178,688 / 4,077 | Completed; supported and unresolved findings. |
| Legible r0 | 17 | 204.02 | 44,822 | 385,289 / 352,896 / 5,359 | Completed; version/justification/threshold and mathematical concern. |
| Eviction r1 | 20 | 203.37 | 60,220 | 224,116 / 189,568 / 6,111 | Partial update; positive finding rejected, unresolved finding recorded. |
| Eviction r2 | **24** | 106.33 | 75,215 | Not reported | **Budget overrun; no final assessment or finding.** |
| Legible r2 | 16 | 182.41 | 28,741 | 276,440 / 226,176 / 4,814 | Completed; changed explanation, unchanged threshold. |

All 97 completed MCP calls returned one valid JSON TextContent within the requested application byte budget, without a structured-content duplicate, matching the Service trace. There were 21 controlled application errors. Application JSON totaled 270,210 bytes; each original's saved pretty-printed tool schemas were 10,833 bytes. [Metrics](../../experiments/growing_corpus/evidence/original-consumer-metrics.json) also record compact result-wrapper sizes as a framing proxy, not exact wire bytes. Cumulative input includes repeated/cached context and is not unique evidence or information efficiency. Monetary cost is not exposed by this ChatGPT-authenticated CLI route and was not inferred from token totals. [Independent transport audit](../../experiments/growing_corpus/evidence/transport-audit.json)

The r2 monitor detected an overrun after a burst of calls; it did not prevent call 21, and 24 calls completed. No `turn.completed` or final usage event followed. The original summary incorrectly set `has_final_assessment: true` because a progress message existed, even though process exit zero did not imply completion. The original files remain unchanged; [explicit adjudication](../../experiments/growing_corpus/evidence/eviction-r2-completion-adjudication.json) and derived metrics correct the classification. Its [retained text is progress only](../../experiments/growing_corpus/evidence/assessments/eviction-r2-progress-only.txt).

## What the source evidence supports

The worker assessed the actual findings against pinned passages, with root independently checking material claims and selected PDF text/rendered sources. This review accepted warranted evidence from any accessible artifact, rather than forcing the reserved-paper subset into an answer key.

- [Eviction r0](../../experiments/growing_corpus/evidence/assessments/eviction-r0.txt) correctly distinguished Blind Oracle, PredictiveMarker, preliminary noise/BrightKite evaluation and theorem claims. Its `eta1` “aggregate/average” wording remains ambiguous: the short paper says average error, while the long treatment's total-loss normalization is not automatically interchangeable. Three oversized slices were rejected before recovery.
- [Eviction r1](../../experiments/growing_corpus/evidence/assessments/eviction-r1.txt) found the long report and correctly noticed its displayed outer-factor/constant difference. It missed the additional CitiBike evaluation, overlap with BrightKite numbers, unresolved 24-versus-12 sequence discrepancy, and the experimental setting that never switches to random eviction. It also overstated its own earlier scope as a global claim that the full treatment was unavailable; r0 had said “inspected here.” All its inspections were listings, so none of the preview handles qualified for the rejected positive finding; it did record an unresolved finding and disclose the rejection.
- Eviction r2 produced no final synthesis. Importantly, the **NSDI proceedings artifact was retrieved**, but its leading passage concerned a different paper on physical p.305, not LHD on pp.400–414. Pichay was also returned with a prompt-caching preview. Neither relevant source was opened. Artifact retrieval therefore did not establish relevant-passage retrieval or cross-topic understanding. A single maximum-scoring snippet for a proceedings artifact and poorly disclosed inspection contracts are plausible contributors; the failure does not isolate their causal contributions.
- [Legible r0](../../experiments/growing_corpus/evidence/assessments/legible-r0.txt) correctly recorded v2's Phase-2 pair-overlap explanation and the `|E| - k + 1` Phase-1 requirement. Its criticism is mathematically valid: two 3-of-5 sets may intersect in one element, whereas three elements suffice to hit every 3-of-5 set.
- [Legible r2](../../experiments/growing_corpus/evidence/assessments/legible-r2.txt) correctly found v3's complement/hitting-set explanation and unchanged stated threshold, with version and physical-page evidence. It reopened the same v2 projection inside current r2; the separate old-revision audit, not that consumer action, establishes continued r0 membership access. It did not establish that every other part of the paper was unchanged.

A **separate direct-evidence diagnostic** supplied 13 builder-selected, hashed passages from long caching, LHD and Pichay plus the last completed r1 assessment. It used no tools, took 48.10 seconds and reported 12,389 input/1,554 output tokens. The [actual response](../../experiments/growing_corpus/evidence/assessments/eviction-direct-diagnostic.txt) correctly qualified the unexercised randomized switch, identified fault-driven pinning and implicit-reference failures, treated cross-session prediction as future work, and separated ordinary-cache theory from untested LLM transfer. It explicitly noted the incomplete theorem excerpt. This shows useful interpretation under direct provision of selected evidence; it neither replaces the original failure nor proves the interface caused it. Its proposed combined policy is an inference, not a tested implementation. [Input identities](../../experiments/growing_corpus/direct-evidence-manifest.json), [metrics](../../experiments/growing_corpus/evidence/direct-diagnostic-metrics.json)

## Sixteen matched response observations

The [protocol](../../experiments/growing_corpus/comparison-protocol.md), [payloads and masks](../../experiments/growing_corpus/comparison-inputs/), exact questions, visible-evidence rubrics and hashes were frozen in signed commit `a5bf55b7950080d33ad9b32be2391e69330d15f1` before responses. Seed 20260909 determined launch order; at most four independent fresh processes ran concurrently. No tools were exposed, no substantive response was retried, and no hidden truth or alternate-source evidence entered prompts. The numeric CLI generation cap was explicitly recorded as unresolved before runs, using identical supported default settings.

The common prompt teaches lexical-negative calibration, so these are field observations **under that instruction**. They measure interpretation and a stated next step, not navigation, stopping behavior or cost benefit. Direct equivalent fields were allowlisted/masked and common fields compared exactly. Visible hit-array length and zero-text coverage still convey logically related information; masking does not establish information-theoretic concealment.

Scores are individual rubric bookkeeping (class 0/2, calibration 0/1, next step 0/1), not an aggregate effectiveness measure. [Actual responses](../../experiments/growing_corpus/evidence/comparison-responses.json), [per-response usage/time](../../experiments/growing_corpus/evidence/comparison-metrics.json), [adjudication](../../experiments/growing_corpus/evidence/comparison-adjudication.json)

| Case | Arm | Actual class | Stated next step | Score / 4 |
|---|---|---|---|---:|
| Present | Scope shown | present | stop | 4 |
| Present | Scope hidden | present | stop | 4 |
| Present | Neither count nor coverage | present | stop | 4 |
| Present | Count only | present | stop | 4 |
| Present | Coverage only | present | stop | 4 |
| Present | Combined | present | stop | 4 |
| Exact absent predicate | Scope shown | bounded_negative | stop | 4 |
| Exact absent predicate | Scope hidden | bounded_negative | stop | 0 |
| Alias | Scope shown | unresolved | terminology variants | 4 |
| Alias | Scope hidden | unresolved | terminology variants | 4 |
| CORFU processing gap | Scope shown | unresolved | explicit extraction/search | 4 |
| CORFU processing gap | Scope hidden | unresolved | source review | 4 |
| CORFU processing gap | Neither count nor coverage | unresolved | source review/broader terms | 4 |
| CORFU processing gap | Count only | bounded_negative | source review | 2 |
| CORFU processing gap | Coverage only | unresolved | extraction/OCR/search | 4 |
| CORFU processing gap | Combined | unresolved | extraction/OCR/search | 4 |

There was no stated-step effect in the narrow present control. The scope-hidden absent response assumed unspecified representation/coverage scope and stopped with high confidence. CORFU count-only used the wrong class for the source-support question but its sentence correctly limited the predicate negative and left the broader question unanswered; it received calibration and feasible-next-step credit. CORFU neither said “shown zero matches,” which may mean the visible empty hit array rather than a hidden total; the ambiguity is recorded without a categorical count-invention penalty. A prior harsher adjudication was retained locally and revised after independent review. Extraction/OCR suggestions are proposed interventions, not claims that the source is image-only or that automatic fallback exists. All responses reported high confidence; no p-values, confidence intervals, pooled win rates or causal effectiveness claims are made.

The earlier external path-ledger pilot remains **inconclusive**, with 0/4 observed uptake; optional Tampu history/path machinery remains disabled. Its 21 regression tests passed under the documented separate service. This result is not relabeled as evidence of either benefit or equivalence.

## Interface changes after observation and completion audit

After all five originals and sixteen comparisons completed, discovery was corrected to expose `inspect.limit: 1..20`, `slice_chars: 1..4000`, and the distinction between preview handles and inspected citation handles. Runner completion now requires an actual completed turn, no failed turn or stop reason, successful exit and a message; incomplete text is retained as a last message, not labeled final. Five targeted regressions first failed on the actual missing contracts/lifecycle classification; six focused cases then passed. Original schemas, source hashes and failures remain intact. Current-interface reproduction is therefore different from recreating the originals at their recorded commits.

The post-observation review fix exposes `validation_scope` with frozen PDF and transcript conditions, implementation commits, corpus revisions/sizes, per-mechanism enum statuses and result links. Experiment records are paged one per call using `validation_cursor`; every page retains the mechanism statuses and a content-hashed profile reference. Exported findings carry that same reference, also preserved with this report in the [profile snapshot](../../experiments/growing_corpus/evidence/validation-profile.json). Sample ambiguity, missed relationships, staleness and the transcript path affordance remain `inconclusive`; context accumulation and embedding candidate crowding remain `not_tested`. No implementation feature is credited as empirical benefit. Live selected-revision counts and per-lens count meanings are under each collection's `collection_scope`, with a compact startup statement. Revision-list records retain their historical counts. At the default 8,192-byte budget, optional summary fields may be omitted explicitly; a larger budget can recover budget-omitted fields. The fixed five-record recipe/loss summary caps require `describe` detail pagination to reach later records. This is the revised current interface, not the schema delivered to the original consumers.

The same post-observation review fix rejects inspection listing limits outside 1..20 while retaining search count-only `limit=0`, and requires a completed, nonfailed, uninterrupted, zero-exit, source-unchanged predecessor with a final assessment and at least one MCP call before publication. Legacy original summaries and schemas are retained unchanged; their original sequencing is documented separately. These fixes have regression/interface evidence, without rerunning the original experiments. The capture/extraction and repository implementation reports were migrated from tracked skill workspace paths to [durable implementation records](../implementation/), preserving their contents.

| Binding MVP criterion | Evidence and limit |
|---|---|
| Every enumerated source has an outcome; coverage reconciles | Actual 160/320/473 publication records, capture tests and declared extraction gaps. |
| Deduplicated hits, full counts, pinned evidence | Real duplicate/work diagnostic, matched exact counts, transport and old-byte/pinned-membership audits. |
| Budgets, typed failures, unavailable coverage, ephemeral default | 97 real bounded JSON responses, 21 preserved application errors, failed/stopped consumer and state tests; trace persistence explicitly owner-enabled. |
| Two-profile extraction pilot | Twelve PDFs, fixed primary choice, costs/losses and rendered spot checks; no semantic-completeness certificate. |
| Six core diagnostics and labeled field pilots | Actual separate-database fixtures and sixteen fresh recorded responses, with per-arm judgments. |
| External path result and scope decision | Inconclusive earlier pilot retained; optional path machinery disabled; 21 old regressions passed. |
| Real cross-topic task and distinct failure diagnosis | Original final eviction attempt failed; direct-evidence cross-topic diagnostic separately completed, without causal attribution. |
| Truthful discovery and documentation | Linked runtime evidence statuses and post-observation disclosure correction; deferred capabilities remain unavailable. |

The original Task 4 verification is recorded in the [Task 4 implementation report](../implementation/2026-09-09-growing-corpus-report.md) and [verification record](../../experiments/growing_corpus/evidence/verification.json). Independent Task 4 and whole-branch reviews passed after the recorded corrections; the [completion and review record](../implementation/2026-09-09-prototype-completion.md) preserves their findings, dispositions and final 130-pass/1-optional-skip gate. The result is a functioning research prototype with early, limited observations—not established consumer benefit, semantic completeness, production scale or generally superior retrieval.

### Final review boundary corrections (post-observation)

The current interface adds revision-pinned `describe(detail="processing"|"admission")` pages. Pass one collection, then repeat the returned `revision_id` as `revision` and `continuation` as `detail_cursor`. Processing pages attribute every recipe/coverage record and individual loss to artifact/projection IDs; admission pages expose recorded source outcomes. `detail_limit` is 1..100. The 8192-byte default and 32768-byte ceiling remain. Pages advance by complete records or report a controlled `budget_too_small`/`minimum_bytes`; a single record above the ceiling requires owner-local record access. Increasing a budget alone never removes a fixed summary cap.

New revision summaries distinguish capture failures from extraction failures. Search and bounded negatives retain admission outcome counts and enumeration completeness; absent captures under failed scans are unresolved rather than confirmed removals. Old revisions derive their admission scope from stored observations without rewriting the publication. Publication dates now use versioned inclusive calendar intervals: full containment matches, disjointness excludes, and partial overlap is explicitly ambiguous. `temporal_scope` carries separate ambiguous-interval and missing-value counts into negatives, which remain exact only over the known selected representation. The original three curated assertions were day-precise and admission completed in the recorded stages; these boundary regressions do not change those consumer outcomes.

Extraction cache reuse now checks the current adapter/profile and normalization versions plus Poppler's effective version or the pinned Unstructured image identity before returning old successful output. Upgrades affect new processing attempts, with earlier projections/evidence retained. No published research database was re-ingested, no frozen input/schema/result was regenerated, and no model observation was rerun for this fix wave. Corrected scope and provenance are implementation evidence, with no retrospective consumer-benefit claim. Existing N+1/materialization, per-operation database timeout, process-state accounting and SDK sensitivity limitations still apply.
