# Artifact-local rehearsal: a direct retrieval hit, no additional probe recovery

The first lexical search directly returned one of six assessed passages. Opening that hit confirmed its evidence address but added no text to that passage. The four adjacent-page inspections recovered **zero additional assessed passages**. This run therefore demonstrates one successful artifact-scoped retrieval, not a benefit of the local navigation strategy built on top of it. Five assessed passages remained undelivered: four were not reached by the selected queries and inspection steps, and one lay beyond the element limit on a page that was inspected.

Interpretation revised on 2026-09-10 following Claude's review supplied by Tony. The frozen protocol, queries, raw responses, and numeric results are unchanged. The original report gave the direct search hit and the missing pagination counts more interpretive weight than this evidence supports; the [review response](../superpowers/specs/2026-09-10-artifact-local-interpretation-review.md) records the correction.

The preceding [grouping diagnostic](2026-09-09-retrieval-grouping-results.md) found that globally returning more passages recovered none of its eight distinct qualification probes. This follow-up asked whether a client that already knew the relevant artifact could explore locally. The distinction matters: Tampu should help an investigator recover relevant evidence without carrying a whole paper or proceedings volume into context. A failed first search is not the same as unavailable evidence, and an available continuation is not evidence that a client will recognize its value.

## What was frozen and run

Two queries per case, existing `artifact_id` filtering, one returned hit per search, then opening its evidence handle and inspecting the following physical PDF page. No probe ordinal or target page steered the runner. Each case allowed six service calls, each capped at 8,192 response bytes; no retries or continuation calls were added after seeing results. Queries and strategy were frozen before execution, but the builder already knew the papers. These are exposed capability rehearsals, not blind usability trials or an A/B comparison against the earlier presentation experiment.

All calls used the same published 473-artifact revision and the actual Python Service methods. This checks the consumer-facing service responses, not MCP transport behavior. Four searches and eight inspections completed without application errors. Observed index generation was stable.

| Case | Fixed queries | Calls | Total response bytes | Direct search recovery | Additional recovery by adjacent-page inspection |
|---|---|---:|---:|---:|---:|
| Long caching paper | `switch random` (all terms), `experimental` (any terms) | 6 | 18,645 | 1 of 3 probes | 0 |
| NSDI proceedings | `LHD RankCache` (all terms), `adapt` (any terms) | 6 | 21,488 | 0 of 3 probes | 0 |

The first long-paper query returned ordinal 239 on physical page 14. Its search extract already contained the entire 138-character statement that the evaluated setting never switches to random evictions; call 2 opened the same passage. This is ordinary lexical retrieval working for a builder-informed query. Inspecting page 15 supplied table labels and numerical result rows. The second query led to a related-work comparison on page 5, followed by definitions on page 6. These are descriptions of returned material, not measured usefulness. The page-12 robustness and switching-parameter probes were not delivered. We have not established how the evaluated parameter choice relates to the formal bound. In particular, this is not a finding that the experiment violates a guarantee.

For the proceedings, `LHD RankCache` returned a short figure label on page 408. Its page number placed the next inspection in the relevant paper, but neither the label nor the following-page inspection delivered a probe. Page 409 exposed partial descriptions of monitoring, histograms, sampling, and slab rebalancing; the experiment did not assess their contribution to an answer. The second query, `adapt`, returned the isolated word “adapters.” on page 584; inspecting page 585 supplied references from elsewhere in the volume. Artifact scoping alone does not establish a paper boundary within proceedings. This is a substantive limitation of the tested strategy: the second search was free to leave the relevant paper while staying in the same artifact.

## Where the six probes ended up

| Artifact / ordinal | Physical page | Observed path |
|---|---:|---|
| Long paper / 239 | 14 | Entire text returned by the first search; opened directly |
| Long paper / 194 | 12 | No search hit or page inspection reached this page |
| Long paper / 206 | 12 | No search hit or page inspection reached this page |
| Proceedings / 13846 | 405 | No search hit or page inspection reached this page |
| Proceedings / 14048 | 408 | Search returned another element on this page; strategy opened that hit and inspected page 409, not the other page-408 elements |
| Proceedings / 14087 | 409 | Page inspected, but probe was its 29th element and only the first 20 were returned |

Four of the five undelivered probes were outside the chosen inspection paths. One was beyond a returned page prefix. This is descriptive attribution within the fixed trace, not a controlled causal comparison of alternative queries or strategies. Neither query reformulation nor following continuations was tested against this strategy. The outcome is negative for incremental probe recovery by adjacent-page navigation; it is not proof that all local exploration is ineffective. Likewise, the earlier grouping diagnostic found no probe recovery from its tested replacement, not that grouping can never be a bottleneck.

## What the cutoff actually hid

The page-409 inspection returned 20 element previews and a continuation. Its result contained an offset and returned count, but no total or remaining count for the page's elements. A **post-run** check against the verified source projection found 33 elements on that page; the background-update probe, ordinal 14087, was the 29th. Thus 13 elements remained, including the desired address. These source positions were not supplied to navigation.

The strategy was programmed not to follow continuations. It did not decide to stop because counts were missing: adding counts alone would not change this runner's calls. Pagination describes where one probe was excluded from a response, not why an autonomous client abandoned an investigation. A continuation would offer further address discovery; longer elements would still need an evidence inspection to expose their full text. We did not perform those additional calls and do not count them as success. The other four undelivered probes would not be exposed by continuing this page.

## Separate engineering and research decisions

**Element counts remain a proposed observability improvement, not the retrieval remedy established by this run.** Exact total and remaining element counts would make the extent of a partial artifact/page inspection explicit, with the count unit identified as elements and the remaining count adjusted after byte-budget packing. The justification is the project's general principle of exposing omissions, consistent with Tony's earlier observation about returning two memory entries together with the size of the complete result set. The trace supplies a concrete instance of absent counts; it does not demonstrate that supplying them improves evidence discovery.

The concrete before/after is: “20 elements returned; continuation available” becomes “20 of 33 elements returned; 13 remain.” Counts cannot tell a client whether the remainder is relevant, and element count is not a measure of semantic content. This small interface change would make the extent of an unfinished inspection observable. Its effect on navigation decisions still needs evaluation; the rehearsal does not prove that a client would continue because it saw the number 13.

**The retrieval research question remains unresolved.** Query formulation determined the search starting points, and the fixed inspection strategy did not recover missing qualifications from those points. Proceedings also require distinguishing a paper's locality from the containing artifact. Any follow-up intended to improve retrieval needs to examine those constraints directly and attribute evidence recovery to search, direct opening, and navigation separately. The present data do not select a successful remedy. Adding counts must not be reported as resolving these failures or establishing ordinary retrieval competence.

## Verification and limitations

The compact results were reproduced exactly offline. The 12 recorded responses and normalized arguments match the Service trace; normalization expands default arguments omitted by the caller. An initial verification assertion compared explicit arguments directly with expanded trace arguments and failed; correcting that comparison changed neither calls nor responses. The offline verifier also re-executes the navigation policy against recorded responses and checks every decision, byte ceiling, call ceiling, and assessment.

The runner's navigation inputs exclude assessed ordinals and pages. After the live run, its parameter object was narrowed to exclude the unused assessment configuration as well; offline decision replay verifies the same calls. The source projection used for the post-run page check passed PDF/raw/normalized byte verification. The known probes retain their earlier frozen hashes. No whole-probe claim is inferred from a truncated preview or assembled fragments.

This small strategy is neither optimal nor exhaustive. The builder knew the sources, query vocabulary, and desired distinctions; results cannot estimate discovery by an unfamiliar client. Aggregate response bytes exclude requests, transport overhead, code inspection, and this builder's working context. The index fingerprint retains its documented same-count mutation limitation. No production behavior changed, no consumer-model run was launched, and the corpus was not modified.

Raw source-bearing records remain owner-local. The [experiment directory](../../experiments/artifact_local/README.md) contains reproduction commands, compact results, and custody hashes. The original focused read-only reviewer independently passed the 12-call verifier and inspected the captured page-409 pagination response, but did not identify the interpretive overreach corrected here. Its original approval is preserved as history, not as a validation of this revised interpretation. The reviewer did not independently reconstruct the source projection check, access the database, or test MCP transport; the coordinator's verified post-run source check remains the basis for the 33-element/29th-position observation. During the 2026-09-10 revision the verifier passed again, and a direct hash check confirmed that the first search extract already equaled the full frozen ordinal-239 probe text.

The rehearsal is preserved with signed commits on `experiment/artifact-local-navigation`, descended from the grouping diagnostic branch. The proposed count change is a subsequent implementation task and is not included in these results. No push or merge was performed.
