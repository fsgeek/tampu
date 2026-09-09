# Retrieval grouping: first bounded diagnostic

The six-case diagnostic does **not support replacing Tampu's artifact grouping with globally ranked passages as the next default change**. Neither presentation exposed any of the eight distinct, previously identified qualification passages within the common budget. The reasons were mostly upstream of presentation: six passages did not match their frozen queries, and the other two ranked too low to fit even after removing grouping. Global passage ranking also reduced the number of distinct papers shown in two cases.

The purpose is to protect the distinction between Tampu's research idea and ordinary retrieval competence. We want an AI to explore evidence without carrying an accumulating midden of irrelevant context. Before attributing earlier consumer difficulties to that idea—or changing retrieval on intuition—we need to locate where known evidence disappears. This report preserves that motivation as well as the runnable procedure.

## Comparison

The [protocol](../../experiments/retrieval_grouping/protocol.md) and [case sheet](../../experiments/retrieval_grouping/cases.json) were signed and frozen before new rankings were inspected. Queries came from earlier consumer traces and controls. All six were evaluated at the same 473-artifact revision, using the existing lexical index and BM25 scores. Both arms used the same captured matches, 800-character prefix excerpts, response metadata, 20-entry ceiling, and 8192-byte complete JSON ceiling. This is a normalized presentation audit, not an exact replay of the MCP wire format or historical rankings.

| Case | Matching passages / papers | Grouped: entries / papers / bytes | Passage: entries / papers / bytes | Frozen evidence outcome |
|---|---:|---:|---:|---|
| Short paper; broad prior query | 10,273 / 406 | 18 / 18 / 8,115 | 19 / 11 / 7,438 | Two probes match; neither shown |
| Long paper; all-terms query | 7 / 2 | 2 / 2 / 2,348 | 7 / 2 / 6,939 | Three probes do not match |
| Proceedings; all-terms query | 65 / 26 | 13 / 13 / 8,090 | 12 / 8 / 7,376 | Three probes do not match |
| Spaced-name alias control | 0 / 0 | 0 / 0 / 782 | 0 / 0 / 782 | Known related passage does not match |
| Lexical-negative control | 0 / 0 | 0 / 0 / 789 | 0 / 0 / 789 | Exact lexical zero only |
| Extraction-gap control | 0 / 0 | 0 / 0 / 777 | 0 / 0 / 777 | Zero text pages out of 24 |

The alias control reuses a short-paper probe, so there are nine probe observations but eight distinct source passages. No evidence address is invented for the blank CORFU projection. A zero-hit response retains extraction coverage and admission scope; it does not establish source or conceptual absence.

The short-paper probes are ordinals 38 and 39, both on physical page 2. They rank 318 and 4,640 globally, and seventh and nineteenth within that artifact. Grouping suppresses them, but removing grouping still leaves both outside the output budget. Ordinal 39 is 817 characters long: even if selected, the common excerpt would not display the entire probe. This is a conservative whole-element visibility measure, not a judgment that all 817 characters are necessary for an answer.

The long-paper probes (ordinals 194, 206, and 239) concern switching, robustness, and experimental configuration. The proceedings probes (13846, 14048, and 14087) concern adaptation mechanisms. None matches all terms of its respective frozen query. Grouping cannot recover an element missing from the lexical match set. This observation does not establish that better lexical reformulation, neighboring context, or semantic retrieval would succeed; those were not tested.

## Additional evidence, inspected after the run

The long-paper passage response adds material that is relevant to the broader research question: ordinal 131 on page 10 discusses how the Marker policy uses predictions and its worst-case bound; ordinal 10 on page 1 summarizes the claimed robustness result and empirical evaluation. These are useful additions beyond the grouped arm's page-8 counterexample fragment. They were identified after observing rankings and are **not additions to the frozen probe score**. Their usefulness also does not resolve the missing experimental qualifications on pages 12 and 14.

The proceedings response still leads to the page-305 ResQ passage seen in the earlier consumer trace. The extra passage from that same artifact is another ResQ passage on page 304, rather than the sought LHD material around pages 405–409. More passages from an artifact can remain in the wrong part of it.

Repeated-artifact entries number eight, five, and four in the short, long, and proceedings passage responses. That describes reduced breadth, not proven semantic redundancy. The long-paper example shows why those concepts must remain separate.

## Decision and next question

Keep the current default grouping for now. These results rule out a simple explanation—"one passage per artifact is the bottleneck, so removing the grouping should recover these qualifications"—for this frozen set under this budget. They do not establish that grouping is generally preferable or that ordinary retrieval is now adequate.

The next narrow test should exercise **local exploration within an already identified paper**, using Tampu's existing `artifact_id` search filter and bounded `inspect` ranges. The two concrete tasks are finding the long paper's experimental switching qualification and finding the proceedings' LHD adaptation mechanisms. Freeze the navigation prompts and budget before attempting them. This would distinguish a missing capability from a capability whose affordance or query requirements are hard for an AI client to discover. No new retrieval feature is justified by this diagnostic alone.

Tony's most useful contribution is a source-level judgment: are those two distinctions—the experimental qualification and the adaptation mechanisms—necessary to a satisfactory answer to the original research questions? They are good probes of missing qualifications as selected by the builder; an independent domain judgment would strengthen that selection. There is no need to supply a larger corpus for this decision.

## Validation and limits

- All six exports completed below the 20,000-match ceiling. The observed index-generation fingerprint was stable.
- Seven focused tests passed, covering grouping/ties, UTF-8 packing, whole-prefix behavior, entry limits, evidence truncation, failure attribution, changed probes, and incomplete/unstable captures.
- Offline replay reproduced all 14 capture/result/response files byte-for-byte.
- Six read-only production queries returned exactly the same grouped artifact order, addresses, pages, scores, and full matching texts as the corresponding derived baseline; observed index generation remained equal.
- Source probes were checked against the pinned projections with the repository's PDF/raw-output/normalized-output byte verification. No ingestion, extraction, index mutation, runtime change, or consumer-model call occurred.

This is a small, exposed, builder-selected diagnostic. It measures recovery of selected known passages and response breadth, not exhaustive relevance, answer quality, latency, or general non-inferiority. The production index-generation fingerprint tracks projection IDs and counts, so it does not independently detect every possible out-of-band mutation. Source-bearing captures remain owner-local; [compact results](../../experiments/retrieval_grouping/results.json), [custody manifest](../../experiments/retrieval_grouping/owner-local-manifest.json), and [reproduction instructions](../../experiments/retrieval_grouping/README.md) are preserved in Git.

One read-only reviewer independently passed the seven focused tests, verified the 12 response files against the reported hashes and limits, and checked the post-run excerpt descriptions. The review found no material flaw in the comparison or its bounded conclusion. Its request for a reproducible production-parity procedure is addressed in the README; that parity record is explicitly operator-recorded corroboration.

One implementation deviation from the protocol remains: a live source-validation failure before capture begins aborts the command rather than producing per-case inconclusive records. This fails closed and did not occur in this run, but it limits failure-report convenience. The index observation also cannot certify against all out-of-band changes. Neither limitation is evidence of a failed recorded case.

The work was performed on `experiment/retrieval-grouping-audit` in the existing isolated worktree, with the initial one-hour timebox beginning at 14:32:13 UTC. The six-query capture ran from 14:43:05 to 14:43:07 UTC; that duration excludes source validation, implementation, review, and production-parity checks and is not a latency benchmark. Protocol, code, compact results, tests, and this report are preserved with signed commits. No push or merge is part of this diagnostic.
