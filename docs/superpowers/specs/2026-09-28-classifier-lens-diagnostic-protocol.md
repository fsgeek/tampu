# Classifier lens diagnostic: protocol

Status: **FROZEN**, revision 2, 2026-09-29. Author: Claude (Opus 5.5).
Revision 1 was the draft reviewed by Astra; both are committed in
`f741acf`. This revision addresses that review; dispositions are at the end.
The signed commit of this file is the freeze. No corpus text has been sent
to either classifier. Any later change is an amendment, committed before
the observations it affects.

## Question

The artifact-local rehearsal delivered one of six assessed passages, by
direct search. Five were not delivered. Its corrected report says counts
cannot tell a client whether the unread remainder is relevant.

Would a typed classifier, used as a Tampu lens, rank those five passages
within a bounded text budget?

The experiment makes new classifier measurements, then analyses the
captured responses deterministically. It complements Codex's adaptive
consumer design (`2026-09-11-retrieval-competence-test-design.md`). It runs
no consumer, so it cannot measure time to finding or abandonment. It
measures where a lens places known evidence, and what scoring costs.

## Lenses under test

| Lens | Model | Access |
| --- | --- | --- |
| `jev-relevance` | Jev, pinned `jev-1.13.0`, TypeSafe hosted API, `typesafe_sdk` 0.7.1 | `TYPESAFE_API_KEY` |
| `clm-relevance` | CLM default head, Qwen3-8B encoder, in-process `clm.Engine` | 4090 under the Hamut'ay GPU lease |
| `lexical` | Existing BM25 index, the four frozen artifact-local queries | Existing repository, read-only |

Both classifier lenses receive **identical state and question payloads**.
Model selection is service-specific and recorded per call: the returned
model string for Jev; the `contrastive-lm` package version, head file
SHA-256 and encoder name for CLM.

No vendor claim about either classifier is evidence here. Levadura-salvaje
observed Jev label changes on byte-identical inputs. That may be an artifact
of how it was used, so this protocol measures repeatability rather than
assuming it.

## Inputs

- Collection `research`, revision `0ea79b79668943969e5ee21dfdcbdfae`, the
  rehearsal's revision.
- The two artifacts and pinned projections named in
  `experiments/artifact_local/cases.json`. Projections pass the repository's
  PDF, raw-output and normalized-output byte verification before any call.
- Every element whose text is non-empty after stripping whitespace. Measured
  on 2026-09-28 and 2026-09-29, before any classifier call:

| Artifact | Elements | Non-empty | UTF-8 text bytes | Longest CLM input, tokens |
| --- | ---: | ---: | ---: | ---: |
| Long caching paper | 379 | 359 | 56,719 | 377 |
| NSDI proceedings | 21,628 | 20,989 | 2,921,695 | 735 |

  The CLM input is the stripped element, two newlines, then the question,
  which is how `clm.schema.state_text` joins them. Token counts used the
  Qwen3-4B `tokenizer.json`, SHA-256 prefix `aeb13307a71acd8f`. Before CLM
  scoring, the Qwen3-8B tokenizer file is hashed. If it differs, lengths
  are re-measured and any input over 2,048 tokens stops the CLM pass for an
  amendment.

- The task text for each case, verbatim from `cases.json`, frozen on
  2026-09-09. It contains no probe text, ordinal or page.

The scoring runner never reads probe ordinals, pages or hashes. Assessment
joins probes to scores only after every scoring call has completed.

## The classifier request

One Noul question per element. The state is the stripped element text, as
a plain string. The question payload, identical for both services:

```json
{"type": "noul", "instructions": "A researcher is investigating this task: <task text>. Does this passage contain information that would help complete the task?"}
```

`<task text>` is replaced verbatim. Jev is called as
`system_one(state=<text>, questions={"relevant": Noul(...)}, model="jev-1.13.0")`.
CLM is called as `Engine.answer(<text>, {"relevant": Noul(...)})`.

A synthetic check on 2026-09-29 established the Jev response form. It
returns `answers.relevant.noul`, a probability given to **two decimal
places**, and no separate confidence field. It reported 304 input tokens
for a one-sentence state. The record is owner-local at
`tmp/classifier-lens-20260929/jev-schema-check.json`.

CLM's response form is checked the same way, with a synthetic state, after
it gets the card and before any corpus call. A difference from
`answers.relevant.noul` is recorded as an amendment before CLM scoring.

**A valid score** is a number in [0, 1] at `answers.relevant.noul`, with a
returned model equal to the pin for Jev, or an unchanged head hash for CLM.
If Jev returns a different model, the pass stops. Scores under the pin
remain valid and the artifact is incomplete for that lens. Continuing under
a new version would be a new lens, which requires an amendment.

## Ordering and ties

Jev's two-decimal output makes ties common, so the analysis handles them
explicitly.

- **Shared ordering**, used for reading sets and lens overlap: descending
  score, then ascending ordinal. It is independent of the probes.
- **Per-probe bounds**, used for eligibility: the *worst case* places the
  probe after every element with an equal score. The *best case* places it
  before them.

## Measures

For each of the six probes, per lens:

1. **Rank** and **percentile** in the shared ordering, plus worst-case and
   best-case ranks.
2. **Text cost**: cumulative UTF-8 bytes of element text up to and
   including the probe, in worst-case and in best-case placement.
3. **Text-only budget eligibility at 8,192 bytes**, the service's default
   per-response budget. This is the primary threshold. It counts element
   text only. Response framing, evidence addresses and packing would add
   bytes, so eligibility is necessary but not sufficient for delivery in
   one response. No claim is made that an implemented interface would
   deliver an eligible probe.
4. **Text-only eligibility at 49,152 bytes**, for the proceedings only.
   For the long paper this budget covers most of the artifact, so it would
   be uninformative.

A probe is **eligible** only if it is eligible under worst-case placement,
and under every conditional-sensitivity substitution below. A probe
eligible under best-case placement only is reported as **tie-dependent**.

Ordinal 239 was delivered by search in the rehearsal. Its classifier ranks
are reported separately and never counted as recovery. Attribution uses
Codex's roles plus one: **classifier lens**, credited only for the five
probes that search, opening and adjacent-page inspection did not deliver.

**Random comparator.** Draw 10,000 permutations of each artifact's
non-empty elements with `numpy.random.default_rng(20260928)`. Apply the
same eligibility rule to each permutation. Record how many of the five
probes are eligible in each, pooling the two artifacts. A lens **exceeds
the random baseline** when the fraction of permutations with at least as
many eligible probes as the lens is at most 0.05. This needs no model
calls.

**Lexical replay.** A fresh measurement. Run the four frozen artifact-local
queries against the same revision, restricted to each artifact, and record
each probe's rank or "not matched". The earlier grouping diagnostic used
different queries, so its results don't predict this one.

**Disagreement.** Per artifact, the Spearman correlation between the two
classifier lenses over all non-empty elements, and the overlap of their
8,192-byte reading sets in the shared ordering.

**Cost.** Per call, record reported input tokens, latency and retries.
Unreported usage is recorded as unknown, never zero. At the synthetic
check's rate, a full Jev pass should use roughly 7 to 10 million input
tokens, well under a dollar at the published price. The Jev pass stops if
reported tokens, plus one token per two UTF-8 bytes of state for calls
with unknown usage, exceed 20 million.

## Repeatability

Run before the scoring pass, per classifier. The sample is 200 non-empty
elements per artifact, drawn by `random.Random(20260928).sample` from the
elements in ordinal order, plus the three probes of that artifact. Each
request is sent three times, sequentially.

- **Jev: operational repeatability.** TypeSafe's caching is not disclosed
  and cannot be controlled. Per-repeat latency and usage are recorded as
  evidence about possible caching, not proof.
- **CLM: fresh-inference repeatability.** Each repetition uses a new
  in-process `Engine` with a new `Embedder`, with `CLM_ACTION_CACHE=0`.
  The vLLM encoder is started with prefix caching disabled. The embedder
  reports encoder tokens spent on cache misses. Any repeated state with
  zero encoder tokens is invalid and excluded, and the exclusion is
  reported.

Report label changes at 0.5, and the median and maximum absolute
difference in probability. These results are committed before the scoring
pass starts.

**Conditional sensitivity.** After scoring, each probe's score is replaced
in turn by each of its repeated values, holding every other score fixed,
and eligibility is recomputed. This tests the probe's own variation. It
does not test competitors moving past the probe, so it does not establish
full ranking stability.

## Incomplete scoring

Transport errors are retried at most twice, and each retry is recorded. A
returned answer is never retried. After retries, an element without a
valid score is **missing**.

With missing scores, eligibility is bounded. The worst case scores every
missing element 1.0, and the best case scores them 0.0. A probe's
eligibility is **resolved** if both bounds agree, and **unresolved**
otherwise. Unresolved probes do not count as eligible. A lens verdict is
**incomplete** if the unresolved probes could change it. An incomplete pass
is not negative evidence about the lens.

## Interpretation, fixed in advance

These thresholds are arbitrary but declared before any observation. They
concern the five probes the rehearsal did not deliver, at 8,192 text bytes.

- **Supports a follow-up:** at least three of the five are eligible, and
  the lens exceeds the random baseline. That justifies offering the lens to
  Codex's adaptive consumer. It is not evidence of consumer benefit.
- **No support:** at most one of the five is eligible.
- **Mixed:** two of the five. Reported per probe, with no verdict.
- **Incomplete:** as defined above.

Counts of tie-dependent and sensitive probes are reported next to each
verdict. Six builder-selected probes cannot establish retrieval quality in
general. No aggregate score combines the lenses.

## Execution

1. Freeze this protocol in a signed, stamped commit.
2. Verify projections.
3. **Jev**: repeatability, commit its results, then the scoring pass. At
   most 8 concurrent requests.
4. **CLM**: only when the 4090 is free, via

   ```
   ayllu-gpu run --holder tampu --purpose "classifier lens diagnostic: CLM repeatability and scoring" --ttl 2h -- <runner>
   ```

   The runner starts the encoder, runs the schema check, repeatability and
   scoring, then exits, which releases the card. Contention etiquette is
   pending clarification from Hamut'ay. The Jev half does not wait for it.
5. Assessment, random comparator, lexical replay and the report follow.
   If CLM never gets the card, Jev is reported alone and CLM is recorded as
   not run.

Expected volume per classifier: 21,348 scoring calls and 1,218
repeatability calls.

## Custody

Raw requests and responses contain source text and stay owner-local under
`tmp/classifier-lens-<date>/`, with SHA-256 hashes. Compact results, the
runner, tests and the report go in `experiments/classifier_lens/` in Git.

## Not claimed

No consumer ran, so nothing about time to finding, abandonment or answer
quality. Eligibility is text-only and says nothing about delivery through
an implemented interface. No claim that either classifier is calibrated
against ground truth. No claim about other collections, tasks or question
wordings. The wording is one choice among many, and another could change
every rank. The builder knew the probes when writing it, but it is derived
only from the frozen task text.

## Dispositions of Astra's review

| Item | Disposition |
| --- | --- |
| 1. Cache reuse vs fresh inference | Accepted. CLM repeats use fresh engines with caches disabled, verified by encoder tokens. Jev is labeled operational repeatability. Verified against `clm/embedder.py` and `clm/engine.py`. |
| 2. Text-only cost vs reachability | Accepted. Renamed text-only budget eligibility throughout, including the verdict rule. No delivery claim. |
| 3. Instability rule not computable | Accepted. Replaced with conditional sensitivity, computed after scoring, and a stated effect on the verdict. |
| 4. Incomplete scoring undefined | Accepted. Valid score defined, bounds over missing scores, unknown usage never zero, incomplete verdict defined. |
| 5. API contract | Accepted. Identical payloads, service-specific model selection, Jev pinned. The synthetic check confirmed Astra's point: there is no separate confidence field. It also found two-decimal probabilities, which led to the tie section. Schema checks now precede the freeze for Jev. For CLM they precede its corpus calls. |
| 6. Ties and random comparator | Accepted. Shared probe-independent ordering, per-probe bounds, and a seeded permutation comparator with a defined threshold. |
| Smaller 1. Encoded lengths | Accepted and measured: longest input is 735 tokens. The tokenizer assumption is checked before CLM scoring. |
| Smaller 2. Lexical replay | Accepted. Now a fresh measurement with no expected result. |
| Smaller 3. Naming | Accepted. "Deterministic replay" removed. |

## Amendment 1, 2026-09-29, before CLM scoring

**Observation.** CLM fresh-inference repeatability (`eb46ed5`) found the
proceedings identical on all three repeats. In the long paper, repeats 1
and 2 were identical, but repeat 0 differed on every element. The
difference ends exactly where the long paper ends in repeat 0. CLM's
Noul option texts contain the question, so each artifact has its own
option vectors, embedded once per engine. The long paper's were
embedded on the first corpus request after the encoder started. The
likely cause is cold-start inference in the encoder. That is not proven.

**Change to the CLM scoring pass.** Scoring as frozen would start with
the long paper immediately after encoder start, the affected condition.

1. **Warm-up.** After the schema check, send 30 synthetic requests,
   using three synthetic questions ten times each, on an engine that is
   then discarded. No corpus text is used. Warm-up scores are recorded.
2. **Scoring** proceeds as frozen, with a new engine.
3. **Built-in check.** After scoring, a new engine re-scores the first
   20 elements of each artifact, in ordinal order. For each artifact,
   if any re-score differs from its scoring-pass value by more than
   1e-6, that artifact's CLM scores are marked **unstable**, and its
   CLM verdict is reported as incomplete.

**Unchanged.** Repeatability results stand as recorded, including
repeat 0. Conditional sensitivity uses all three repeated values, as
frozen. For the long paper this is conservative, because repeat 0
includes the cold-start shift.
