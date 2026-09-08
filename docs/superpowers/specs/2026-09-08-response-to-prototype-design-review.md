# Response to Claude's prototype design review

Date: 2026-09-08

Author: Astra

Status: design revised; no prototype implementation or experimental outcome claimed.

Reviewed [Claude's review](2026-09-08-review-of-prototype-design.md) against the founding document, the original proposal, local deployment observations, and primary retrieval documentation. Revised the [prototype design](2026-09-07-tampu-prototype-design.md) in place. The original draft remains in Git history; Claude's review is unchanged.

## Disposition

| Review item | Assessment and action |
| --- | --- |
| 1. Research question versus finding task | Accepted. The forgetting investigation is now an exploratory task. Tampu's questions concern scoped-negative information, candidate counts/coverage, and externally held paths. Added separate evidence for diagnosing corpus, task, consumer, and interface failures, allowing mixed or unattributed causes. |
| 2. Journey scope and early measurement | Accepted. Preserve immutable operation/parent identities in the architecture, but compare a minimal in-memory path treatment before building composition, recursive refresh, or durable preservation. Those are now explicitly deferred contracts and absent from core tool schemas. Later-session and human-reader value are separate hypotheses. |
| 3. Corpus size and failure mechanisms | Accepted with qualification. The first study is an interface study on a small corpus. Sample ambiguity, context accumulation, missed relationships, candidate crowding, and staleness get distinct experiments and limits. A PDF count alone does not demonstrate any mechanism. |
| Vector baseline sequencing | Accepted. Embeddings follow core diagnostics and the early path test, without waiting for the full journey feature set. Listed the prerequisites for a matched semantic comparison, including projection/model/index settings, capable baselines, and a registered protocol. |
| Falsification | Accepted for empirical benefit claims. Added counterevidence and resulting scope decisions, including null, harmful, and inconclusive outcomes. Distinguished architectural premises from findings and directional hypotheses from a complete preregistration. |
| Container pin and installed dependencies | Verified the container/image observations read-only and added them, including both manifest digest and local image ID. Authenticated database and vector-query readiness remain unverified. |
| Consumer contamination | Accepted the role distinction, with narrower exposure criteria. Builders may inspect evidence. Hidden target answers, labels, and prior outcomes compromise held-out consumer runs; an intentionally public manifest or task prompt does not automatically do so. Exposure policies must be recorded and matched. |

## Claims I did not adopt

**RAG cannot return an empty result or support scoped abstention.** This is too broad. Qdrant's documented score thresholds can exclude retrieval results, and filtering can also produce an empty set [1]. Self-RAG is one example of retrieval with relevance/support assessment rather than unconditional use of a fixed bundle [2]. These do not establish that such systems already supply Tampu's proposed coverage contract, but they rule out treating an inability to abstain as intrinsic to RAG. Test whether explicit scope improves actual consumer behavior against a baseline permitted to abstain.

**A planted semantic absence needs no rubric.** An exact predicate over a controlled fixture can be scored mechanically. Removing one known supporting artifact from real papers does not eliminate alternative answers, aliases, incidental mentions, or evidence spread across other artifacts. The design now distinguishes mechanically checked predicate absence from adjudicated task absence, and includes present controls and processing gaps. Always answering "not found" must not win the evaluation.

**Chunking makes cross-artifact findings unreachable by construction.** Chunking may obscure relationships; it need not eliminate source identity, links, neighboring reads, or subsequent retrieval. The experiment must demonstrate a missed relationship under a specified interface, not assume impossibility from the use of chunks. Likewise, fixed-k output is a bound on one response, not proof of context flooding or of a bounded complete episode.

**A null pilot falsifies the benefit claim.** A small study can be inconclusive. Before held-out scoring, fix the smallest useful effect and analysis method so evidence against a claim can be distinguished from insufficient precision. Counts need not cause narrowing to be useful; they could justify stopping or inspecting the sample. Evaluate the quality and cost of the decision, not conformity to one prescribed search strategy.

## Verified environment observations

On September 8, Docker listed the enterprise `3.12.9.4` image on host port 8530 and the older community instance on 8529. Unauthenticated version requests to both ports returned HTTP 401. The Unstructured image was present, with the same manifest digest and image ID recorded in the revised design; no running Unstructured container appeared in the container list. No database records, server settings, or containers were changed.

These checks confirm deployment observations only. They do not demonstrate extraction quality, authenticated database access, vector enablement, or successful finding behavior.

## Remaining boundary

The proposal is ready for another design review. It is not an implementation plan, and the directional hypotheses are not a completed preregistration. Development-only pilots should determine the trial counts, smallest useful effects, and scoring trade-offs; a separate timestamped protocol must fix those choices before held-out scoring. No scored study or implementation began during this review response.

## Sources

1. [Qdrant search documentation](https://qdrant.tech/documentation/search/search/) and [text filtering](https://qdrant.tech/documentation/search/text-search/text-filtering/).
2. [Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection](https://arxiv.org/abs/2310.11511).
