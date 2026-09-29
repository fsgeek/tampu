# Classifier lens diagnostic: Jev results (interim; CLM not yet run)

Protocol: `docs/superpowers/specs/2026-09-28-classifier-lens-diagnostic-protocol.md`, revision 2, frozen in `357deae` before any corpus call. Repeatability results were committed in `054f2be` before scoring, and scores in `31ba8b9` before assessment.

## Result

Under the pre-declared rule, the Jev lens **supports a follow-up**. All five passages the artifact-local rehearsal failed to deliver are text-only eligible within 8,192 bytes. None is tie-dependent or sensitive to Jev's repeat variation. No seeded random permutation out of 10,000 made five eligible; the mean was 0.29.

| Probe | Page | Jev score | Rank | Of | Worst-case text cost, bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| Long paper 206 | 12 | 0.69 | 2 | 359 | 868 |
| Long paper 194 | 12 | 0.40 | 14 | 359 | 6,075 |
| Proceedings 14048 | 408 | 0.90 | 3 | 20,989 | 1,383 |
| Proceedings 13846 | 405 | 0.88 | 5 | 20,989 | 3,225 |
| Proceedings 14087 | 409 | 0.86 | 7 | 20,989 | 4,355 |

Ordinal 239, already delivered by search in the rehearsal, ranks 3rd in the long paper. It is not counted.

This says a relevance lens places these passages where a consumer could read them. It does not show that any consumer would, that an implemented interface would deliver them within the budget, or that answers would improve.

## What the lexical replay adds

The replay is a fresh measurement with the four frozen artifact-local queries. It changes how the rehearsal's long-paper losses should be read. `switch random` matches all three long-paper probes, at ranks 1, 3 and 4 of 6 matches. The rehearsal took one hit per search, so its long-paper losses came from that strategy, not from lexical search failing. Jev's advantage there is modest.

The proceedings are different. Neither frozen query matches 13846 or 14048. `LHD RankCache` matches 14087 at rank 15 of 23. Jev ranks all three in its top seven of 20,989.

## Observed but not pre-declared

Ten of the twelve highest-scoring proceedings elements lie on pages 401 to 409, the LHD paper. The lens located the relevant paper inside the volume, which bears on the paper-boundary limitation of artifact scoping. This is a post-hoc observation, not a tested claim.

## Repeatability

Identical requests did not return identical probabilities. 123 of 406 sampled elements scored the same on all three repeats; 193 differed by 0.01, the output precision; the largest spread was 0.07. One element crossed 0.5. No element needed chunking. Reported input tokens were identical across repeats, and later repeats were slightly faster, about 88 ms against 107 ms at the median. TypeSafe's caching is undisclosed, so this is operational repeatability. The variation did not change any probe's eligibility.

## Cost

21,348 scoring calls and 1,218 repeatability calls. About 7.3 million reported input tokens for scoring, roughly $0.31 at the published price, in 4 minutes 40 seconds with eight requests in flight.

## Limits

The task texts were written by the builder, who selected the probes, and the proceedings task names LHD/RankCache. Jev was asked a question closely aligned with the probes. Six builder-selected probes cannot establish retrieval quality in general. The wording is one choice among many. The instruction contains a double period from verbatim substitution of the task text, as frozen.

CLM has not run. It waits for the shared GPU and for Hamut'ay's guidance on contention. The disagreement measures need both lenses.

Raw records stay owner-local under `tmp/classifier-lens-20260929/`. Compact results: `experiments/classifier_lens/jev-assessment.json`.
