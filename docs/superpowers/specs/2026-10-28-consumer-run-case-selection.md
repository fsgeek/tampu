# Consumer run: case selection rule

Status: frozen 2026-10-28, before the builder has seen any candidate. A subagent is assembling the candidate pool from khipumaq while this is written. Its instructions asked for verbatim questions, for every rejection to be recorded with a reason, and for no padding.

## Why real questions

Every Tampu result so far ends with the same limitation: the builder wrote the tasks and chose the probes, and no consumer benefit has been shown. Tampu's first customer is taken to be an ayllu instance doing real work over a real paper collection. Cases therefore come from questions that Tony or an instance actually asked in a past session, where the answer depended on paper content. The mechanism follows `2026-09-11-retrieval-competence-test-design.md`. That design reserved "independently selected cases" for later evaluation. This rule is how they are selected.

## Pool

The pool is every candidate record with `accepted: true` in the subagent's `candidates.jsonl`, after the builder checks two things for each one:

1. `question_verbatim` appears in the recalled episode. If it doesn't, the record is dropped and the drop is logged.
2. The episode is not in the `tampu` project and is not about building or testing Tampu. If it is, the record is dropped and the drop is logged.

The builder may not drop a candidate for any other reason, including difficulty, an expected Tampu failure, or an unclear answer. An unclear answer is a fact to be assessed, not grounds for exclusion.

## Selection

Candidates are split into two strata by the subagent's `absence_likely` field: **likely present** and **likely absent**. Within each stratum, candidates are ordered by SHA-256 of the UTF-8 `episode_key`, in ascending hex order. Walking each ordering from the start, a candidate is taken unless two cases from its `project` have already been taken in that stratum.

- Up to **4** likely-present cases and up to **2** likely-absent cases.
- If a stratum runs short, the cases found are used and the shortfall is reported. There is no backfill from the other stratum.
- If fewer than 3 cases qualify in total, no consumer run proceeds. The result is reported as "khipumaq holds too few real paper questions over this corpus for this design." That is itself a finding about the customer.

The selected list, the full ordering, and every drop are committed before any case's answer requirements are written.

## After selection, before any consumer run

For each case, an assessor-facing record in the form of section 1 of the 2026-09-11 design: answer requirements, verified source spans, known misleading evidence, and known extraction gaps. The session's own conclusion counts as ground truth only when `conclusion_status` is `verified`. Otherwise the assessor establishes it from the PDF. A likely-absent case is assessed by checking the corpus and recording how the check was done and what it covered. The subagent's "likely" is not accepted as the answer.

The consumer prompt is the verbatim question plus a frozen, minimal framing that is identical across cases. The framing says it is a research question from a past session, names the collection, and states the tools and limits. It carries no target, page, query hint or expected answer. Where the verbatim question depends on context from its session, that context is quoted from the episode and labelled as such, never paraphrased.

Rubrics, prompts, consumer model and settings, service commit, corpus revision and budget settings are frozen and timestamped before the first consumer run. A reviewer from another lineage reviews the rubrics before the freeze; that review is committed alongside them.

## Known limits of this rule

- The subagent's judgments (accepted, absence_likely, corpus mapping) shape the pool, and that subagent is the builder's own lineage. Its full considered-and-rejected log is committed so the pool can be audited.
- The builder writes the rubrics. A cross-lineage review reduces this risk but doesn't remove it.
- Questions that were asked of an AI already holding some context are being re-asked here without it. Context quoted from the episode only partly closes that gap.
- Six cases or fewer cannot establish general retrieval competence or consumer benefit. Each case produces a case report under section 5 of the 2026-09-11 design, not a score.
