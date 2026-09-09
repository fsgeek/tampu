# Local navigation: a qualification recovered, and a visible stopping point

The existing tools recovered the long caching paper's experimental switching qualification. They also reached the relevant LHD/RankCache neighborhood inside the proceedings, but the fixed navigation strategy stopped before the assessed passages. This is evidence of useful existing capability and a concrete pagination affordance gap. It does not establish unfamiliar-client success or adequate answers to both research questions.

The preceding [grouping diagnostic](2026-09-09-retrieval-grouping-results.md) found that globally returning more passages recovered none of its eight distinct qualification probes. This follow-up asked whether a client that already knew the relevant artifact could explore locally. The distinction matters: Tampu should help an investigator recover relevant evidence without carrying a whole paper or proceedings volume into context. A failed first search is not the same as unavailable evidence, and an available continuation is not evidence that a client will recognize its value.

## What was frozen and run

Two queries per case, existing `artifact_id` filtering, one returned hit per search, then opening its evidence handle and inspecting the following physical PDF page. No probe ordinal or target page steered the runner. Each case allowed six service calls, each capped at 8,192 response bytes; no retries or continuation calls were added after seeing results. Queries and strategy were frozen before execution, but the builder already knew the papers. These are exposed capability rehearsals, not blind usability trials or an A/B comparison against the earlier presentation experiment.

All calls used the same published 473-artifact revision and the actual Python Service methods. This checks the consumer-facing service responses, not MCP transport behavior. Four searches and eight inspections completed without application errors. Observed index generation was stable.

| Case | Fixed queries | Calls | Total response bytes | Whole assessed passages inspected |
|---|---|---:|---:|---:|
| Long caching paper | `switch random` (all terms), `experimental` (any terms) | 6 | 18,645 | 1 of 3 |
| NSDI proceedings | `LHD RankCache` (all terms), `adapt` (any terms) | 6 | 21,488 | 0 of 3 |

The first long-paper query returned ordinal 239 on physical page 14, and inspection exposed its full statement that the evaluated setting never switches to random evictions. Inspecting page 15 supplied table labels and numerical result rows. The second query led to a related-work comparison on page 5, followed by definitions on page 6. The page-12 robustness and switching-parameter probes were not delivered. We therefore recovered a necessary distinction, but have not established how the evaluated parameter choice relates to the formal bound. In particular, this is not a finding that the experiment violates a guarantee.

For the proceedings, `LHD RankCache` returned a short figure label on page 408. That label was a useful locator, not an answer. Inspecting page 409 exposed partial descriptions of monitoring, histograms, sampling, and slab rebalancing. These partial descriptions are useful context even though none of the three frozen probes was delivered. The second query, `adapt`, returned the isolated word “adapters.” on page 584; inspecting page 585 supplied references from elsewhere in the volume. Artifact scoping alone does not establish a paper boundary within proceedings.

## What the cutoff actually hid

The page-409 inspection returned 20 element previews and a continuation. Its result contained an offset and returned count, but no total or remaining count for the page's elements. A **post-run** check against the verified source projection found 33 elements on that page; the background-update probe, ordinal 14087, was the 29th. Thus 13 elements remained, including the desired address. These source positions were not supplied to navigation.

The strategy deliberately stopped instead of following that continuation. A continuation would offer further address discovery; longer elements would still need an evidence inspection to expose their full text. We did not perform those additional calls and do not count them as success. The preview limit, figure fragments among the elements, and query choice all contributed to the result. It would overstate the evidence to blame missing counts alone.

## Chosen next change

Add **exact total and remaining element counts to artifact/page inspection**, with the count unit explicitly identified as elements and the remaining count adjusted after byte-budget packing. Search already makes candidate-set size visible; this inspection path should give the same basic information for the range being explored. Keep continuation semantics and default ranking unchanged.

The concrete before/after is: “20 elements returned; continuation available” becomes “20 of 33 elements returned; 13 remain.” Counts cannot tell a client whether the remainder is relevant, and element count is not a measure of semantic content. This small interface change would make the extent of an unfinished inspection observable. Its effect on navigation decisions still needs evaluation; the rehearsal does not prove that a client would continue because it saw the number 13.

That is a more grounded next implementation than replacing global grouping. It also carries forward Tony's original observation about asking for two memory entries while retaining the size of the complete response set. No larger dataset or new service is needed. A useful human contribution would be to critique the research interpretation above, especially the distinction between recovering the evaluated setting and understanding its relationship to the guarantee.

## Verification and limitations

The compact results were reproduced exactly offline. The 12 recorded responses and normalized arguments match the Service trace; normalization expands default arguments omitted by the caller. An initial verification assertion compared explicit arguments directly with expanded trace arguments and failed; correcting that comparison changed neither calls nor responses. The offline verifier also re-executes the navigation policy against recorded responses and checks every decision, byte ceiling, call ceiling, and assessment.

The runner's navigation inputs exclude assessed ordinals and pages. After the live run, its parameter object was narrowed to exclude the unused assessment configuration as well; offline decision replay verifies the same calls. The source projection used for the post-run page check passed PDF/raw/normalized byte verification. The known probes retain their earlier frozen hashes. No whole-probe claim is inferred from a truncated preview or assembled fragments.

This small strategy is neither optimal nor exhaustive. The builder knew the sources, query vocabulary, and desired distinctions; results cannot estimate discovery by an unfamiliar client. Aggregate response bytes exclude requests, transport overhead, code inspection, and this builder's working context. The index fingerprint retains its documented same-count mutation limitation. No production behavior changed, no consumer-model run was launched, and the corpus was not modified.

Raw source-bearing records remain owner-local. The [experiment directory](../../experiments/artifact_local/README.md) contains reproduction commands, compact results, and custody hashes. One focused read-only reviewer independently passed the 12-call verifier and inspected the captured page-409 pagination response. The review found no material issue in accounting, interpretation, or the bounded recommendation. The reviewer did not independently reconstruct the source projection check, access the database, or test MCP transport; the coordinator's verified post-run source check remains the basis for the 33-element/29th-position observation.

The rehearsal is preserved with signed commits on `experiment/artifact-local-navigation`, descended from the grouping diagnostic branch. The proposed count change is a subsequent implementation task and is not included in these results. No push or merge was performed.
