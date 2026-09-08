# Finding a reason to preserve a path

Author: Astra. Date: 2026-09-08.

Status: exploratory close reading after the completed pilot. These are task-development observations from papers the builder has now inspected; they are not fresh-consumer evaluation results.

## A treatment problem as well as a task problem

The first pilot's optional ledger exposed prior queries, filters, counts, result identifiers and inspected episode identifiers. It retained a branch's purpose or interpretation only if the consumer supplied a note. Its API status `ok` meant an operation succeeded, not that an investigative branch was relevant or resolved. The consumers had their full ordinary context and completed short investigations without writing notes or consulting the ledger.

Making questions harder does not by itself establish demand for that representation. Difficulty might concern a proof, insufficient evidence, or conflicting terminology; none necessarily requires looking up an earlier query. The next exploration should identify the operation or information a consumer actually needs when returning to an unfinished investigation. This may be a query, an evidence location, the reason a candidate was rejected, or an unresolved distinction. Those are different requirements.

## A concrete case in the supplied collection

Two different PDF artifacts concern prediction-assisted caching:

| Local filename under `tmp/research` | PDF pages | SHA-256 |
|---|---:|---|
| `2018 Better Caching with Machine Learning Advice.pdf` | 3 | `3bd6c331a38201a5ead0db2135e0067de43707131962a6314e2cf974755a1578` |
| `2018 Competitive caching with machine learned advice.pdf` | 19 | `d2c7c7af6c801c3ef7657d282bfa8f1b5c6193a758bd74179cb7c5d0e423142e` |

Their title pages identify Thodoris Lykouris and Sergei Vassilvitskii. The longer artifact identifies itself as arXiv:1802.05399v1. The shorter paper's actual title uses “Machine Learned Advice,” despite “Machine Learning Advice” in its local filename.

The short paper's Table 1, PDF page 2, and the long paper's Table 2, PDF page 15, report identical BrightKite competitive ratios: Blind Oracle 2.049, LRU 1.280, Marker 1.310, and Predictive Marker 1.266. Both describe the same selection of 100 long, nontrivial BrightKite user sequences. The longer paper also reports CitiBike results: 2.023, 1.859, 1.869, and 1.810 respectively, using cache size 100 rather than BrightKite's 10.

This is strong evidence of overlapping reported experiments. It does not establish the formal publication/version lineage or prove whether the authors reran any experiment. Treating the two BrightKite tables as independent replications would be unjustified. Treating the artifacts as interchangeable would lose the additional evaluation and detailed argument in the longer one. File count, distinct content count, research contribution count and independent evidence count are different quantities.

The copy-aware-computing paper in the collection offers a relevant perspective: Karlson, Smith and Lee's `2011 Which Version is this Improving the desktop experience within a copy-aware computing ecosystem.pdf`, PDF page 9, describes document grouping as context-sensitive. Content overlap can suggest a shared origin; copy/paste can also connect documents that are related without belonging in the same conceptual document group. This supports keeping relationship evidence available rather than treating a similarity score as a final identity decision. It does not classify this particular caching-paper pair for us.

## Branches worth returning to

The following are observations and open checks, not allegations of errors in the research:

1. **Sampling description.** The longer caching paper's Table 1 on PDF page 14 lists 24 CitiBike sequences; nearby prose describes creating 12 monthly sequences for 2017. Both numbers are visible in a rendered page, so this is not merely a text-extraction discrepancy. The reason for the difference remains unresolved in this reading. It affects what I can say about the additional workload evidence.
2. **Evaluated policy versus bounded policy.** PDF page 14 says the evaluated PredictiveMarker sets its switching constant to cache size and never switches to random evictions. The short paper, PDF page 2, describes an additional random-eviction modification when predictions perform poorly. Understanding how the evaluated parameter choice relates to the formal guarantee requires inspecting the definitions, algorithm and proof together. I have not established that the evaluation violates a guarantee; that would be a premature conclusion.
3. **Error normalization and terminology.** The short paper defines an average absolute prediction error on PDF page 2. The longer paper introduces total absolute loss on PDF page 2 and formal robustness/consistency definitions on PDF page 7. Bounds and terminology need comparison with their definitions intact; similar-looking expressions or words alone are insufficient. Mathematical expressions in the text extraction should be checked against rendered pages before any algebraic comparison.

These branches have different reasons for remaining open. A list of earlier search strings would not express those reasons automatically. A useful retained record would let me recover which comparison I was attempting, where its evidence lives, and what I have and have not established. Whether an explicit note tool, a retrievable operation record, or ordinary working context serves that need best remains an empirical question.

## A question I would pursue

“What evidence in this collection supports using prediction-assisted eviction when predictions deteriorate? Distinguish overlapping reports from additional evaluations, identify which policy and parameter settings were evaluated, and preserve unresolved differences between the evaluated setting and the claimed guarantee.”

This question bears on a real design choice about trusting predictive advice. It also creates reasons to revisit a paper after finding something elsewhere. The discovered pair provides a development example, not a held-out test item. Its usefulness as a navigation study should be judged from an actual investigation and its unresolved needs, rather than assumed from the number of papers or words involved.

Three possible next steps have different purposes: another harder-question A/B would test the current ledger again; a staged resumption exercise would test continuity across a defined interruption; an ordinary investigation would reveal which assistance, if any, is missing. I recommend the ordinary investigation first, with a concrete evidence-supported conclusion as its product. If it proceeds fluently with ordinary context and notes, that observation should stand. If an unfinished branch becomes difficult to recover, its trace can motivate a specific next treatment.

## Local evidence

The PDFs were read using the existing `pdftotext -layout` utility. Extracted text and rendered PDF pages 14 and 15 of the longer paper are retained under the main checkout's ignored `tmp/navigation-exploration-20260908/`. Page references here are one-based PDF page numbers, which differ from printed page numbers in the preprint. The software-reuse paper was also skimmed but supplies no finding above. This note leaves the frozen pilot protocol, harness and results intact.
