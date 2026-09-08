# Prediction-assisted eviction when predictions deteriorate

Author: Astra. Investigation date: 2026-09-08.

The collection supports using predictions inside a policy that limits the consequences of mistakes. It also supplies a different, complementary approach: continually update predictions from observed accesses. Neither establishes that low measured fault rates imply preservation of an LLM's useful context. Pichay reports failures that make this distinction concrete.

This assessment answers the research goal proposed in the [navigation exploration](2026-09-08-navigation-demand-exploration.md). It is a source investigation, not a reproduction of the papers' experiments or a new Tampu effectiveness trial.

## Evidence and scope

Source identifiers below refer to exact local artifacts in `tmp/research`, not to whichever publication version is currently available online. All page references are one-based PDF pages. The [coverage record](2026-09-08-prediction-assisted-eviction-coverage.json) records filenames, full SHA-256 hashes, extraction diagnostics, search expressions, candidate sets and reading scope. It contains no paper text.

| ID | Work / artifact | Role in this assessment |
|---|---|---|
| S | *Better Caching with Machine Learned Advice*, Lykouris and Vassilvitskii; filename says “Machine Learning Advice”; 3 pages | Short report of prediction-assisted paging |
| L | *Competitive caching with machine learned advice*, same authors; arXiv:1802.05399v1; 19 pages | Detailed theory and experiments |
| D | *LHD: Improving Cache Hit Rate by Maximizing Hit Density*, Beckmann, Chen and Cidon | Independent policy and implementation; inside `nsdi18_full_proceedings.pdf`, PDF pp. 400–414 / printed pp. 389–403 |
| P | *The Missing Memory Hierarchy: Demand Paging for LLM Context Windows*, Mason; `2603.09023v1.pdf` | Context eviction, feedback and observed failures; 15 pages |
| U | *Online Optimization with Uncertain Information*, Mahdian, Nazerzadeh and Saberi (2012) | Earlier framework for combining optimistic predictions with worst-case protection; opening pp. 1–3 inspected |

The inventory has 479 PDF paths and 473 distinct byte sequences. `pdftotext -layout` 22.02.0 returned successfully with nonempty output for every path, but 11 artifacts emitted diagnostics. *Paxos Made Moderately Complex* produced only 427 bytes: success is plainly insufficient evidence of full text coverage. No OCR or page-by-page extraction audit was performed.

Three lexical searches over whitespace-normalized extracted text found 2, 34 and 32 distinct artifacts respectively; their union contains 57. Candidate screening used openings and bounded matching passages, followed by closer reading of the sources above. Several artifacts are whole proceedings or books. This is a bounded discovery method, not a claim that every relevant paper in the collection was found or fully read.

Additional leads were separated by what they actually address. ALACC in the FAST proceedings uses future references available in a restore recipe (PDF pp. 315–316); incomplete look-ahead differs from erroneous learned advice. *Software-Defined Caching* discusses workload objectives, isolation and cache allocation (pp. 1–4). *The Case for Learned Data Structures* concerns indexes; its predicted positions are not next-reference eviction advice. `p620-Wang.pdf` concerns spot-instance procurement and cache availability, with LRU inside memcached (pp. 1–2). Their relevance does not make their measurements replications of PredictiveMarker.

## Overlap is a relation between results

S p. 2 and L p. 15 report the following identical BrightKite values. Both describe selecting 100 long, nontrivial user sequences. L additionally reports CitiBike, using cache size 100; BrightKite uses 10 (L pp. 13–15).

| Policy | BrightKite, both reports | CitiBike, L only |
|---|---:|---:|
| Blind Oracle | 2.049 | 2.023 |
| LRU | 1.280 | 1.859 |
| Marker | 1.310 | 1.869 |
| PredictiveMarker | 1.266 | 1.810 |

These are reported miss-cost ratios relative to the offline optimum under the PLECO predictor. Identical numbers and workload descriptions strongly support overlapping reported evidence. They do not establish independent replication, nor prove whether an experiment was rerun. Conversely, deduplicating one whole artifact away would lose either its distinct presentation or L's additional evaluation and analysis.

L's CitiBike sample description remains inconsistent: Table 1 says 24 sequences, while nearby prose says 12 monthly sequences for 2017 (p. 14, visually checked). No explanation was established. Exact sample size and statistical interpretation therefore remain unresolved. The rounded table values imply approximately 1.1% fewer misses than LRU on BrightKite and 2.6% on CitiBike; the accompanying broad 2.5% description should not replace these dataset-specific comparisons.

External provenance was checked only narrowly: the [official MLSys short paper](https://mlsys.org/Conferences/doc/2018/121.pdf) has the short report's title and authors, and the [arXiv version record](https://arxiv.org/abs/1802.05399v1) identifies the long preprint's February 2018 v1 and subsequent revisions. No external PDF hash comparison or later-version technical reconciliation was performed. Findings here concern the local versions.

## The evaluated policy and the protected policy

L studies ordinary paging with a cache of k equal slots, minimizing misses. Advice predicts the request index of an item's next appearance, not wall-clock time. The request sequence is fixed in advance, oblivious to the algorithm's choices (pp. 6–7).

Blind Oracle evicts whichever cached item is predicted to return last. L constructs sequences where this produces unbounded competitive ratios despite small average absolute error (pp. 7–8). Average prediction quality does not determine how harmful the particular mistakes are.

PredictiveMarker restricts eviction to unmarked items within a phase. L states that this restriction alone provides an O(k) worst-case bound under any tie-breaking rule, and ratio 2 with perfect advice when using oracle tie-breaking (p. 10). Its stronger protection switches an eviction chain from oracle choices to random unmarked eviction after a threshold proportional to the harmonic number H_k. The resulting logarithmic bound is in expectation (pp. 10–12).

But the empirical section explicitly sets the threshold to **k**, so the evaluated policy **never switches to random eviction** (p. 14). The noise experiments show the reported behavior of this configuration as independent lognormal perturbations of next-arrival predictions increase; the PLECO experiments use an existing repeat-consumption model adapted to next-arrival prediction. They do not exercise the logarithmic fallback.

The distinction can be made algebraically. L's Theorem 3 (p. 12) states, for threshold γH_k and γ > 0,

`CR ≤ 2 min{1 + ((1 + γ)/γ) S_l(η/OPT), (1 + γ) H_k}`,

where η is total oracle loss and S_l is a concave bound on loss spread. Substituting the experimental threshold means γ = k/H_k, giving

`CR ≤ 2 min{1 + (1 + H_k/k) S_l(η/OPT), k + H_k}`.

This substitution is our inference from the displayed theorem. Its fallback term is O(k). It does not prove a matching lower bound or rule out a stronger analysis; it establishes that this stated result at this setting does not supply the logarithmic protection. Fixed positive γ supplies O(log k) protection, with the intended absolute-loss dependence of order `1 + sqrt(η_total/OPT)` when predictions are useful.

These guarantees concern expected miss cost under the stated paging model. They establish neither a high-probability latency bound nor a guarantee for variable-sized context objects, differing retrieval costs, or requests that react to prior evictions. The noise experiment is also narrower than arbitrary degradation: its chosen perturbation model is not a test of every correlated error or distribution shift.

Two source issues prevent treating the local first version as an exact implementation specification. S defines average absolute error, whereas L uses total loss (S p. 2; L pp. 5–7). With OPT measured as a miss count, converting average error to L's normalization requires multiplying by sequence length. The short report does not state an alternative normalized OPT. In addition, L's printed clean/stale membership tests reverse its prose definitions, and its displayed theorem and absolute-loss specialization have an apparent coefficient mismatch (pp. 9–12). Rendered pages were checked. These are unresolved textual issues, not findings about unseen author code or a disproof of the intended result.

U shows that balancing an optimistic algorithm with worst-case protection predates these reports, in other online optimization problems (pp. 1–3). It supplies conceptual precedent; it does not extend the paging theorem to context management automatically.

## Adaptation supplies feedback, with its own assumptions

D predicts an object's expected future hits per space-time consumed using observed hit and eviction ages, conditioned on object features. LHD+ adds last-hit and application classes. Its trace evaluation uses commercial Memcachier and Microsoft storage traces; its RankCache implementation approximates ranking through sampling, periodic updates and slab rebalancing (pp. 403–409).

Three details matter when predictions cease to fit:

- The simulation reserves 1% of space for explorer objects allowed to survive to a large age, explicitly to escape local optima (p. 405). This keeps some observations available beyond the policy's current preferences.
- RankCache refreshes ranks periodically and combines histograms with exponential decay. The paper reports sensitivity checks on refresh intervals and decay, while assuming workload behavior is stable over short periods (pp. 408–409).
- Slab classes with few evictions initially lacked fresh information for rebalancing. The implementation performs a sampled “fake eviction” to obtain that information without actually evicting the sampled object (p. 408).

This is concrete evidence about maintaining feedback and making prediction-based ranking practical. It is independent of the S/L experimental program. It does not provide an S/L-style arbitrary-advice competitive guarantee. D's appendix bounds effects of age coarsening under its analysis (p. 414); that concerns representation error, not every possible error in predicted demand. No controlled deterioration sweep or general recovery-time bound was established in this reading.

## What transfers to context eviction—and what does not

P evaluates an age-based FIFO heuristic and describes fault-driven pinning. A repeated request for unchanged evicted file content causes that version to be protected from future eviction; a content change resets the protection (pp. 4–5). Cross-session prediction of next reference is proposed as future work, so these are not measurements of a learned predictor under degradation (p. 13).

The paper exposes two distinct failure mechanisms. Its 681-turn production example reports 659 faults and a cycle of repeated eviction and rereading; the nominal compression benefit was inflated by content introduced through those rereads (p. 9). Separately, its paired continuation study reports two empty treatment outputs among 18 sessions because prompts implicitly referred to tombstoned tool-result content (pp. 11–12). The latter study uses a 20-message recency rule, distinct from the live policy's four-user-turn threshold. Its three judges produce 54 verdicts, not 54 independent sessions.

The paper also reports a very low offline replay fault rate (0.0254%, p. 8). Those observations have different denominators and interventions and should not be pooled. An inference from the mechanism and the reported continuation failures is that **an absent re-request does not establish an absent need**. Replay can recognize recorded repeat calls; it cannot by itself reveal how an agent would change its requests or fail after removal. Pinning learns from observable faults, while implicit references can fail before a useful fault is issued.

P's cost discussion includes retention, restoration and prompt-cache invalidation, rather than only miss counts (pp. 10–11). Its pin-decay and cost-optimal policies remain proposals (p. 13). No cost-aware theorem for those policies, broad quality guarantee, or learned eviction deterioration experiment was established here. Its performance and quality results are reported evidence from a limited corpus, not independently reproduced measurements.

For Tampu, these sources motivate retaining an addressable route to evidence, information about what a compact representation omits, and feedback about unsuccessful navigation. The connection is a design inference. A cache policy's mathematical guarantee cannot supply a guarantee that an LLM will notice missing meaning or know what to retrieve.

## Navigation difficulties actually encountered

| Observed difficulty | What helped here | Candidate Tampu assistance |
|---|---|---|
| A useful paper was inside a proceedings artifact; another had an opaque arXiv filename | Search inside extracted text, then inspect the work's opening and page boundaries | Discover contained works while preserving their containing artifact and exact page anchors |
| Two artifacts repeated a result but differed in additional evidence | Compare tables, workloads, versions and parameters | Preserve supported overlap relations at result level; keep identity decisions revisable |
| An abstract's guarantee needed qualification by a distant experimental parameter | Return across definitions, theorem, configuration and results | Retrieve connected evidence locations with the comparison's purpose and unresolved status |
| Formula extraction and page numbering could change the interpretation | Render the relevant PDF pages; record PDF and printed page numbers | Expose extraction provenance and the underlying page, with bounded retrieval |
| Broad candidate reads exceeded tool output limits and were truncated | Narrow by work and page, then reread bounded passages | Return counts and explicit truncation/coverage information so an incomplete view is recognizable |
| Extraction succeeded while at least one artifact yielded almost no text | Inspect byte counts and diagnostics | Separate successful processing from evidence of searchable coverage |

The earlier exploration note preserved three concrete unfinished comparisons, which made the return purposeful. Ordinary notes, filesystem search and bounded reads were sufficient to finish this investigation. I did not measure a resumption failure, a benefit from the pilot's ledger, or a Tampu speed advantage. Output truncation was directly observed; its cost was not timed. The proposed assistance is motivated by this work and remains to be evaluated.

## Unresolved questions and the next useful experiment

Source reconciliation would require the authors' exact experimental configuration/data and a comparison against later corrected versions: resolve CitiBike's 12/24 count, the short report's error normalization, and the first version's pseudocode and constants. LHD's behavior under deliberately shifted or corrupted demand estimates would require additional evidence. Pichay's implicit-reference failures warrant a test that distinguishes successful recovery, unsuccessful recovery and failure to request missing content at all.

For Tampu, this investigation provides a concrete development case: preserve and recover the evidence behind “the evaluated setting differs from the guaranteed setting,” including why the distinction matters. A future consumer test should assess whether the consumer can make that qualification and find its sources after intervening work. A record of queries alone may not preserve the reason for the comparison. This case is now exposed to the builder and must not be described as held-out evaluation evidence.

## Verification

All 479 recorded PDF hashes and sizes were checked against the local collection after writing the assessment. The coverage JSON, candidate counts and local document links were checked. An independent source reviewer checked the S/L guarantee and overlap claims and P's continuation-failure evidence, finding no substantive corrections needed within that scope. LHD was read by the author of this assessment and was outside that independent review. No paper implementation or experiment was reproduced, and no product code changed.
