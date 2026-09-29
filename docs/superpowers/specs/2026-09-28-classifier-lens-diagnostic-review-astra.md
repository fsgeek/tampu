# Review: classifier lens diagnostic protocol

Author: Astra, 2026-09-28.

Reviewed: `2026-09-28-classifier-lens-diagnostic-protocol.md`, the 199-line draft marked **DRAFT, not frozen**. Line references below refer to that draft.

Disposition: **Support the diagnostic; revise the measurement definitions before freezing.**

The question is useful and appropriately narrower than consumer benefit. Keep the two artifacts, frozen task wording, separate classifier lenses, and distinction between ranking evidence and helping a consumer. The concerns below are about whether the measurements support their stated interpretations, not reasons to abandon the experiment.

## 1. High: distinguish cache reuse from fresh-inference repeatability

Protocol lines 134–141 propose three identical requests. In the local CLM implementation, `src/clm/embedder.py:59` caches embeddings by input text, and `src/clm/engine.py:74` can also cache projected vectors. Repeated requests can reuse the first inference. Identical answers would then not establish fresh-inference stability. Cache hits also change reported input-token usage and latency.

Specify the intended measurement. Operational repeatability with caching is legitimate, but must be labeled accordingly. To measure fresh inference, bypass both caches and verify that encoder calls actually occurred. Report cached performance separately if useful. For the hosted service, record what is known about caching rather than claim control over undisclosed internals.

## 2. High: text-only cost does not establish response reachability

Lines 98–106 exclude response framing from reading cost, but call the resulting threshold “reachable at one response” and use it in the follow-up decision. A text prefix smaller than 8,192 bytes may exceed the response limit after evidence addresses and metadata are added. Similarly, 49,152 aggregate text bytes do not establish packability into six separately bounded responses.

Either freeze a minimal response format and packing procedure, or call the measurement **text-only budget eligibility** throughout, including the interpretation rule. The latter is enough for this initial diagnostic. An optimistic eligibility result can justify further investigation without asserting that an implemented interface can deliver the evidence within that budget.

## 3. High: make the instability rule computable and bounded in meaning

Lines 143–146 compare probability variation with “distance from a reachability boundary.” That boundary depends on competitors' scores, element lengths, and ties; it is unavailable before the full scoring pass. A probe can also keep an identical score while competitors move across it.

Freeze an explicit sensitivity calculation. One inexpensive option is to substitute each repeated probe score into the completed ranking, hold other elements' scores fixed, and recompute budget eligibility. Call this **conditional sensitivity**, not full ranking stability. Distinguish freezing the repeated observations before scoring from analyzing their implications afterward. Specify how unstable or unresolved probes affect the three-of-five follow-up rule.

## 4. High: specify the outcome of incomplete scoring

Lines 167–169 limit retries but do not define the outcome after exhausted retries, malformed answers, or a usage-limit stop. Silently dropping unscored competitors would make probe ranks artificially favorable.

Require complete valid scoring for an ordinary artifact/lens verdict. Otherwise mark it incomplete, or compute explicit best/worst bounds over missing scores. Define score validation and missing-usage handling; unknown usage must not become zero. Preserve completed observations and failures without relabeling an incomplete pass as negative evidence about the lens.

## 5. Medium: correct and freeze the API contract

The example at lines 71–80 omits TypeSafe's required `model` field. Lines 83–85 say a separate confidence field will be recorded, but the current Noul response has no separate confidence field. Its returned `noul` value is the probability used for this ranking.

Primary documentation checked on 2026-09-28:

- [TypeSafe API reference](https://docs.typesafe.ai/api)
- [Noul request and response documentation](https://docs.typesafe.ai/primitives/noul)

Define identical **state and question payloads**, with explicitly recorded service-specific model selection, rather than require byte-identical complete wire requests. Pin the requested model where supported and define what happens if the returned version changes during a pass.

Resolve the sequencing contradiction as well: line 87 places synthetic schema checks before the freeze, whereas Execution places them afterward. Synthetic compatibility checks can precede a freeze of the final request form, with corpus scoring starting only after that freeze.

## 6. Medium: define ties and the random comparator operationally

Lines 92–94 put each probe after all elements with the same score. This is useful as a per-probe worst-case bound, but does not define a single shared ordering for the reading-set overlap at lines 122–125. Specify a probe-independent tie-break for actual reading sets and retain worst-case bounds separately.

Lines 107–110 approximate random inclusion probability by budget divided by total text bytes. Under random element ordering, whole-element inclusion also depends on the elements' unequal lengths and the packing rule. Use seeded random permutations under the same budget/packing policy. Define whether “exceeds its random baseline” means exceeding expected probe recovery or a specified tail threshold, and calculate it for the same five-probe outcome used by the decision rule. This requires no additional model experiment.

## Smaller corrections

1. **Verify encoded lengths.** Character counts alone do not establish the absence of truncation. CLM appends instructions to the state (`src/clm/schema.py:62`) and sends `truncate_prompt_tokens` to the encoder (`src/clm/embedder.py:40`). Check the actual encoded inputs, including instructions and relevant tokenizer behavior, before making the claim at lines 57–59. This review has not established that any input actually exceeds the limit.
2. **Treat lexical replay as a fresh measurement.** The grouping diagnostic used different queries from the subsequent artifact-local rehearsal. Its non-match results do not establish that all five probes fail to match both artifact-local queries. Retain the proposed replay, but remove the expectation that it merely confirms an already-known result.
3. **Name the deterministic part precisely.** These are new classifier measurements followed by deterministic analysis of captured responses. Calling the entire experiment “deterministic replay” obscures the repeatability question the protocol explicitly investigates.

## Review scope

I read the protocol, the frozen artifact-local cases, prior diagnostic reports, relevant local CLM source, TypeSafe's current API documentation, and the khipumaq record of Tony's caution about transferring Levadura's Jev observations. I did not run classifiers, start a GPU workload, independently verify projection bytes or token lengths, or change the protocol. This review does not assert that either classifier is unstable or that Levadura's observations generalize to Tampu.

The diagnostic remains worth doing after these definitions are tightened. No broader benchmark or consumer study is required to resolve these review items.
