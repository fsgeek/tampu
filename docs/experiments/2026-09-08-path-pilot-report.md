# Path-record pilot: completed, benefit inconclusive

Author: Astra. Date: 2026-09-08.

Eight fresh consumers completed the pilot. Answer scores were identical between conditions, and **none of the four consumers offered an operation record consulted it**. No consumer wrote a branch-status note. This demonstrates a working experimental harness and non-use of this optional affordance on these tasks. It does not establish that external path records help, hurt, or are unnecessary during harder navigation.

My recommendation is to **defer the consumer-facing path record from Tampu's first MVP**. Proceed with a small PDF finding-and-inspection slice, preserving artifact identity, provenance, counts, and explicit coverage. Keep operation logging as experiment instrumentation. Reconsider a consumer-facing record when actual PDF use exposes a navigation problem it might address. This is a scope decision under uncertainty, not a negative finding about all journey designs.

## What was actually compared

The [frozen protocol](2026-09-08-path-pilot-protocol.md), [freeze receipt](2026-09-08-path-pilot-freeze.json), and [per-run results](2026-09-08-path-pilot-results.json) provide the detailed record. Protocol and harness were committed as `18c3f448085b2e248a0f22481f654f3dbc1256be` before scored dispatch. The commit has a verified project signature and an OpenTimestamps calendar receipt; a calendar receipt is not a claim of completed Bitcoin anchoring.

The isolated corpus contained 1,000 transcript episodes, including all 217 eligible llm-memory-project episodes and 783 deterministically selected distractors. Its 1,631,310-byte JSONL snapshot has SHA-256 `210a1dca4d9a5a740105d1598e8ae4ad96277ac507aa1bb2d1d19b11e5297881`. It excludes this study's authoring and consumer conversations by a September 6 cutoff. An independent reviewer checked both questions, twelve scoring atoms, and diagnostic evidence before freeze.

Both conditions used the same copied llm-memory search/recall code, ArangoDB version, index fields, analyzer, counts, filters and deterministic score-tie ordering. The separate server used the source server's image digest. Both retained ordinary conversation context. The sole offered difference was optional retrieval of compact prior operations; both could write their own notes. No automatic replay, generated recommendations, or hidden judge annotations were supplied.

The two questions concerned the September 2 ingestion-coverage/duplication discussion and the September 4–5 backup discussion. Each had a natural start and a separately labeled diagnostic start containing three identical scripted, unhelpful prior operations. These were deliberately wrong-project branches, readily recognizable from the task wording. There was one consumer per task/start/arm cell, with a fixed counterbalanced dispatch order, a 20-navigation-attempt budget and a ten-minute admission deadline.

Local transcript metadata confirms all consumers used `gpt-6-astra`, effort `high`, provider `openai`. Parent dispatch records specify `fork_turns=none`. A separate trace audit found identical visible initial platform context, no visible inherited research history, no incoming coaching, and no access outside each consumer's instruction file and harness. All evidence outputs were complete, including the scripted starting histories. Launch-message text remains encrypted in the archived parent and child records, so its plaintext cannot be independently audited there; the fork setting and actual instruction-file exposure are verifiable. This verifies visible adherence to the instructions, not OS-enforced isolation or unknown pretraining exposure.

## Observations

Search and recall columns below count new consumer operations. Diagnostic starts additionally cost three seed operations. Every run submitted one final answer; no run used a ledger or note, encountered an error, exhausted its budget, or required replacement.

| Run | Task | Start | Record offered | Searches | Recalls | Score / 6 | Seconds to submission |
|---|---|---|---|---:|---:|---:|---:|
| r01 | Coverage | Natural | No | 3 | 6 | 6 | 90.6 |
| r02 | Coverage | Natural | Yes | 2 | 5 | 6 | 90.2 |
| r03 | Backup | Natural | Yes | 4 | 6 | 5.5 | 110.7 |
| r04 | Backup | Natural | No | 4 | 5 | 5.5 | 107.5 |
| r05 | Coverage | Diagnostic | Yes | 3 | 5 | 6 | 102.7 |
| r06 | Coverage | Diagnostic | No | 2 | 5 | 6 | 82.3 |
| r07 | Backup | Diagnostic | No | 3 | 6 | 5.5 | 109.0 |
| r08 | Backup | Diagnostic | Yes | 5 | 6 | 5.5 | 129.9 |

The independent scorer received anonymized answers and the frozen rubric/corpus, without arm, start or run identities. All citations were checked against complete episode text. Each condition earned 23/24 points. All backup answers omitted the same explicit qualification: matching hashes of keys or keys plus timestamps still cannot establish equality of complete payloads. They correctly distinguished counts from contents and described the proposed stronger check without claiming it had been implemented. The scorer consistently assigned half credit for that incomplete atom, finding no material unsupported additions. I accept that scoring; the deduction reflects the frozen rubric's demand for an explicit qualification, not an observed false claim that key hashes prove payload equality.

Two coverage answers had minor ambiguity about the date of the historical spec commit; neither asserted a contradictory date, so the scorer did not deduct. The six atoms within each question share evidence and are not independent trials.

There were **no repeated identical search/recall request objects**, including query, filters and limit, and no repeated episode recalls. This is narrower than “no repeated queries” or “no backtracking”: two consumers reused the word `backup` with changed date filters. The exact-request count does not measure semantic redundancy, overlapping hit sets, or conceptual revisiting. All consumers moved away from the supplied wrong-project branches without repeating those operations.

The record condition made 36 new navigation calls versus 34 for control, with identical scores. Those two extra calls cannot be interpreted as a cost caused by record use: nobody accessed the record. One control consumer also batched two pairs of recalls, reducing model round trips. Sampling variation, different search choices and batching are enough to explain small differences here.

## Measured costs and their boundaries

All eight trials together made **26 new searches, 44 new recalls, eight finalizations and twelve seed operations**: 90 persisted harness invocations. The consumers made 84 outer tool calls containing 86 shell commands, including eight instruction-file reads. The distinction matters because batching can reduce outer calls without reducing evidence operations.

| Measure | Control, four runs | Record offered, four runs |
|---|---:|---:|
| New navigation attempts | 34 | 36 |
| Consumer response bytes, including finalization acknowledgments | 93,140 | 95,384 |
| Provider-reported input tokens | 998,919 | 1,104,726 |
| Cached input tokens, included above | 909,696 | 990,208 |
| Provider-reported output tokens | 7,993 | 8,582 |
| Sum of seconds to answer submission | 389.4 | 433.5 |

Across the eight consumers, telemetry reports **2,103,645 input tokens, including 1,899,904 cached input tokens, and 16,575 output tokens**, over 92 model responses. Input minus cached input is 203,741 tokens. Reported reasoning-output tokens are a subset of output, not an additional chargeable total. Per-response usage sums exactly match each final cumulative thread/event total; duplicate telemetry streams were not added together. These are platform token records, not byte estimates or invoices. Monetary charges and cache pricing remain unknown.

The input total is cumulative repeated exposure across model calls, not a two-million-token context window. The largest individual request contained 30,850 input tokens; the reported context window was 258,400. No compaction event was recorded. There was ample context capacity, and this study did not compare cache policies or establish that any particular replay was wasteful.

The complete consumer prompts occupied 58,748 UTF-8 bytes, including diagnostic history. Seed response payloads accounted for 24,396 bytes already included in those prompts; do not add them again as a separate consumer exposure. New consumer requests occupied 29,652 bytes and new responses 188,524 bytes. The operation logs occupied 519,407 bytes. They retain both parsed and raw representations for auditing, so this storage cost is not an estimate of a minimal production journey record. Logging was enabled in both conditions; its isolated overhead against an uninstrumented system was not measured. Actual ledger-access overhead was zero because uptake was zero, not because ledger access is free.

The paired runs spanned 493.2 seconds from the first configured dispatch clock to the last answer submission. Individual wall times include dispatch scheduling and end at finalization; token telemetry additionally includes the brief completion message afterward. Summed harness processing time for consumer operations was 9.05 seconds. That includes hashing, imports and retrieval, but excludes process startup, lock wait and final log flush; it is not DB-only latency. The experiment container had limits of two CPUs and 2 GiB, with pre/post-trial memory samples of 269.2 and 263.9 MiB. These samples are not peak-memory measurements. No image download was needed.

Preparation and review were substantial. At **17:21:47 UTC**, the controller plus four implementation/evidence/audit/scoring agents had reported an additional **9,925,236 input tokens, including 9,492,736 cached, and 75,215 output tokens**, since goal activation at 16:50:09 UTC. This checkpoint excludes the eight consumers, subsequent report review and completion. It includes repeated inherited controller context. It is a partial preparation-cost account, not a complete total for the goal; the completed consumer costs above should not be presented as the cost of constructing and auditing the experiment.

## What this does and does not tell us

The observable result is optional-affordance non-use under these conditions. We did not observe a consumer try the ledger and fail, or a baseline consumer repeatedly lose a prior operation that the ledger condition recovered. This leaves its navigation benefit **inconclusive**. It also gives no empirical reason to make that affordance a prerequisite for a useful MVP.

The corpus is small, target-project enriched, and composed of transcripts that explicitly narrate decisions. Questions name the relevant project and dates. The diagnostic branches are conspicuously in the wrong projects; trajectories are short, and ordinary context remains comfortably available. These conditions offer little pressure to consult an external record. Results are descriptive: eight runs across two task families cannot support a reliable effect estimate, and non-use prevents a comparison of actual ledger consumption. The fixed order, CLI transport, platform instructions, unknown sampling details, batching, and caching further constrain cost interpretation.

Our measurements also omit things. Atom scores emphasize answer particulars and explicit qualifications; they do not measure every useful explanation or preserve every reason for a choice. Exact-request repetition misses conceptual revisiting. Byte counts miss relevance and cognitive burden. Token counts do not reveal the value of a thought or the computation saved by caching. We preserved answers, operations and visible traces locally so these projections can be challenged against richer evidence.

Counts and coverage were available to both arms; their benefit was not experimentally isolated. No PDFs, growing-corpus behavior, semantic rankers, embedding crowding, automatic path restoration or cross-instance memory were tested. Transcript results must not become claims about Tampu's eventual artifact collection.

## Verification and preserved work

The final harness suite passed **21 tests**. Independent reviews led to pre-freeze fixes for omitted rejected-call logging and malformed Unicode/non-finite JSON accounting. After the eight trials, all frozen code, prompt, rubric, corpus and vendor hashes still matched; the isolated database's complete documents and view properties matched the frozen import. There were no exclusions, replacement trials, post-freeze treatment changes or unreported rescoring.

The [harness and reproduction notes](../../experiments/path_holding/README.md) are tracked on `experiment/path-holding-pilot`. The main checkout remains separate. The local, ignored [experiment bundle](../../tmp/path-pilot/) contains the corpus, exact prompts, gold, answers, operation logs, archived consumer traces, independent reviews, [analysis program](../../tmp/path-pilot/analyze.py), and resource checkpoint. The result record identifies supporting artifacts by hash. Private transcripts are not committed or claimed to be a distributable dataset. The final independent review found no blocking issue. After verification, `tampu-path-pilot-20260908` was stopped cleanly with exit code 0, retaining its data; `docker start tampu-path-pilot-20260908` makes the isolated server available for reproduction.

For Tampu's capability record, the path affordance remains `inconclusive` for this transcript pilot; PDF transfer and larger-scale navigation remain `not_tested`. The next product step I recommend is the smallest usable PDF search-and-inspect path, with visible evidence and collection coverage, allowing actual consumer difficulties to determine which navigation support earns a place.
