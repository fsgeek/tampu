# Classifier lens diagnostic: protocol

Status: **DRAFT, not frozen.** Author: Claude (Opus 5.5), 2026-09-28. Nothing
in this document has been run. The freeze is a signed commit of this file,
made after Tony's review and before the first classifier call. Any change
after that commit is an amendment with its own commit, made before the
affected observations.

## Question

The artifact-local rehearsal delivered one of six assessed passages, by
direct search. Five were not delivered. Its corrected report says counts
cannot tell a client whether the unread remainder is relevant.

Would a typed classifier, used as a Tampu lens, have ranked those five
passages within a bounded reading budget?

This is a deterministic replay diagnostic. It complements Codex's adaptive
consumer design (`2026-09-11-retrieval-competence-test-design.md` §4). It
does not run a consumer. It cannot measure time to finding or abandonment.
It measures whether a lens places evidence where a consumer could reach it,
and what that costs.

## Lenses under test

| Lens | Model | Access |
| --- | --- | --- |
| `jev-relevance` | Jev, TypeSafe hosted API, version as reported in each response | `TYPESAFE_API_KEY` |
| `clm-relevance` | CLM-8B reference head, Qwen3-8B encoder, local `clm-serve` | 4090 under the Hamut'ay GPU lease |
| `lexical` | Existing BM25 index, frozen artifact-local queries | Existing repository, read-only |

Both classifier lenses receive the **same wire request**. CLM serves a
TypeSafe-compatible API, so the request is built once and sent to both. Lens
identity is recorded per call: model identifier and version string for Jev;
package version, head file SHA-256 and encoder name for CLM.

No vendor claim about either classifier is evidence here. Levadura-salvaje
observed Jev label changes on byte-identical inputs. That observation may be
an artifact of how it was used, including chunking, so it is a question this
protocol measures, not a premise.

## Inputs

- Collection `research`, revision `0ea79b79668943969e5ee21dfdcbdfae`, the
  same published revision as the rehearsal.
- The two artifacts and pinned projections named in
  `experiments/artifact_local/cases.json`. Projections pass the repository's
  PDF, raw-output and normalized-output byte verification before any call.
- Every element with non-empty text in each projection. Counted on
  2026-09-28 while drafting, before any classifier call:

| Artifact | Elements | Non-empty | Text characters | Longest element |
| --- | ---: | ---: | ---: | ---: |
| Long caching paper | 379 | 359 | 55,971 | 1,342 |
| NSDI proceedings | 21,628 | 20,989 | 2,890,114 | 2,667 |

  Empty elements are excluded and their count reported. No element needs
  chunking at CLM's default 2048-token limit, so chunking cannot contribute
  to any observed variation.

- The task text for each case, verbatim from `cases.json`. It was frozen on
  2026-09-09 and contains no probe text, ordinal or page.

The scoring run never reads probe ordinals, pages or hashes. Assessment
joins the probes to the scores only after every scoring call has completed.

## The classifier request

One `Noul` question per element. The state is the element text, unchanged.

```json
{
  "state": "<element text>",
  "questions": {
    "relevant": {
      "type": "noul",
      "instructions": "A researcher is investigating this task: <task text>. Does this passage contain information that would help complete the task?"
    }
  }
}
```

The score is the returned probability that the statement is true. Jev's
separate confidence value is a margin from its decision threshold, not a
probability, and is recorded but never used for ranking.

The exact wire form is fixed in the freeze commit after one schema check per
service against a synthetic state containing no corpus text.

## Measures

For each lens and artifact, order all non-empty elements by descending
score. Ties are ordered conservatively: a probe is placed after every
element with an equal score.

For each of the six probes, record:

1. **Rank** and **percentile** among non-empty elements.
2. **Reading cost**: cumulative UTF-8 bytes of element text ranked at or
   above the probe. This is a lower bound on what a consumer would receive.
   It excludes response framing, so any reachability finding is optimistic.
3. **Reachable at one response**: reading cost at most 8,192 bytes, the
   service's default per-response budget. This is the primary threshold.
4. **Reachable at six responses**: at most 49,152 bytes, the rehearsal's
   per-case total. Reported for the proceedings only. For the long paper it
   covers most of the artifact, so it is uninformative there.
5. **Random baseline**: the probability that a random ordering reaches the
   probe within the same budget. It is roughly the budget divided by the
   artifact's total text bytes: about 15% for the long paper and 0.3% for
   the proceedings at one response.

Ordinal 239 was already delivered by search in the rehearsal. Its classifier
rank is reported separately and never counted as new recovery. Recovery is
attributed with Codex's roles, adding one: **classifier lens**, credited only
for probes that search, opening and adjacent-page inspection did not deliver.

**Lexical comparison.** Replay the two frozen queries per case against the
same revision, restricted to the artifact. Record each probe's lexical rank
or "not matched". The grouping diagnostic already found that none of these
five probes matched its query, so this is a consistency check.

**Disagreement.** For each artifact, report the Spearman rank correlation
between the two classifier lenses over all non-empty elements. Also report
the overlap of their one-response reading sets. Disagreement is an
observation, not an error.

**Cost.** Record input tokens as each service reports them, per-call latency,
and total wall time per lens. Jev's published price is $0.042 per million
input tokens, so a full pass should cost well under a dollar. The run stops
if Jev's reported usage passes 20 million input tokens.

## Repeatability

Run this before scoring, per classifier:

- Draw 200 non-empty elements per artifact with Python's `random.Random`
  seeded with `20260928`, sampling from elements in ordinal order. Add the
  three probes of that artifact.
- Send each identical request three times, sequentially.
- Report label changes at 0.5, and the median and maximum absolute
  probability difference.

If a probe's probability varies by more than its distance from a
reachability boundary, report that probe's reachability as **unstable**.
Repeatability results are fixed before the full scoring pass starts. They
are not revised to fit it.

## Interpretation, fixed in advance

These thresholds are arbitrary but declared before any observation. They
concern the five probes not delivered in the rehearsal, at one response.

- **Supports a follow-up:** a lens places at least three of the five within
  reach, and that exceeds its random baseline. This justifies offering the
  lens to Codex's adaptive consumer. It is not evidence of consumer benefit.
- **No support:** a lens places at most one of the five within reach. There
  is then no evidence that this lens remedies these losses.
- **Mixed:** two of five. Reported per probe, without a verdict.

Six builder-selected probes cannot establish general retrieval quality in
either direction. No aggregate score combines the lenses.

## Execution

1. Freeze this protocol in a signed commit. Stamp it.
2. Verify projections. Run schema checks with synthetic states only.
3. **Jev**: repeatability, then the full scoring pass. Concurrency is at
   most 8 requests. Transport errors are retried at most twice, and each
   retry is recorded. A returned answer is never retried.
4. **CLM**: only when the 4090 is free, via

   ```
   ayllu-gpu run --holder tampu --purpose "classifier lens diagnostic: CLM repeatability and scoring" --ttl 2h -- <runner>
   ```

   The runner starts the encoder and `clm-serve`, performs repeatability
   then scoring, and exits, which releases the card. Contention etiquette
   is pending clarification from Hamut'ay. The Jev half does not wait for it.
5. Assessment, lexical replay and the report follow both passes. If CLM
   never gets the card, the Jev result is reported alone, and CLM is
   recorded as not run.

Expected volume per classifier: about 21,350 scoring calls and about 1,218
repeatability calls.

## Custody

Raw requests and responses contain source text and stay owner-local under
`tmp/classifier-lens-<date>/`, with SHA-256 hashes. Compact results, the
runner, tests and the report go in `experiments/classifier_lens/` in Git.

## Not claimed

No consumer ran, so no finding about time to finding, abandonment or answer
quality. No claim that either classifier is calibrated against ground truth.
No claim about other collections, tasks or question wordings. The question
wording is one choice among many, and a different wording could change every
rank. The builder knew the probes when writing the wording, but the wording
is derived only from the frozen task text.
