# Classifier lens diagnostic: results

Protocol: `docs/superpowers/specs/2026-09-28-classifier-lens-diagnostic-protocol.md`, revision 2, frozen in `357deae` before any corpus call. Amendment 1 (`1ba719b`) added a warm-up and re-check to the CLM scoring pass before it ran. Each lens's repeatability results were committed before its scoring pass, and its scores before its assessment. This file replaced an interim Jev-only report committed in `f3dd8a7`.

## Result

The two lenses reach different verdicts under the pre-declared rule. Jev **supports a follow-up**. CLM is **mixed**. The lenses also disagree with each other far more than either disagrees with chance on these probes.

| Passage | Page | Jev rank | CLM rank | Out of |
| --- | ---: | ---: | ---: | ---: |
| Long paper 206 | 12 | 2 | 23 | 359 |
| Long paper 194 | 12 | 14 | 61 | 359 |
| Proceedings 14048 | 408 | 3 | 38 | 20,989 |
| Proceedings 13846 | 405 | 5 | 18 | 20,989 |
| Proceedings 14087 | 409 | 7 | 263 | 20,989 |

| Lens | Eligible within 8,192 bytes | Permutation p, at least that many | Verdict |
| --- | ---: | ---: | --- |
| Jev | 5 of 5 | below 0.0001 | Supports a follow-up |
| CLM | 2 of 5 | 0.019 | Mixed |

The random comparator averaged 0.29 eligible passages. No passage was tie-dependent or sensitive under the frozen conditional sensitivity check. Ordinal 239, delivered by search in the rehearsal, ranks 3rd under Jev and 12th under CLM and is not counted.

This says where each lens places known evidence. It does not show that a consumer would read it, that an interface would deliver it within the budget, or that answers would improve.

## The lenses disagree

| Artifact | Spearman correlation | Shared elements in the two 8,192-byte reading sets |
| --- | ---: | ---: |
| Long paper | 0.20 | 6 of 36 |
| Proceedings | 0.05 | 4 of 30 |

Over the whole proceedings, the two rankings are nearly uncorrelated. They agree mainly at the very top, near the evidence. Tampu's founding document asks for lens disagreement to stay visible rather than be blended into one ranking. This is a concrete case where blending would destroy information.

## What the lexical replay adds

The fresh lexical replay changes how the rehearsal's long-paper losses should be read. `switch random` matches all three long-paper probes, at ranks 1, 3 and 4 of 6. The rehearsal took one hit per search, so those losses came from that strategy, not from lexical search failing.

In the proceedings, neither frozen query matches 13846 or 14048, and `LHD RankCache` matches 14087 at rank 15 of 23. Jev ranks all three in its top seven.

## Repeatability and its limits

**Jev** did not return identical probabilities for identical requests. 123 of 406 sampled elements scored the same on all three repeats; most others differed by 0.01, the output precision; the largest spread was 0.07. No element needed chunking. TypeSafe's caching is undisclosed, so this is operational repeatability. The variation changed no probe's eligibility.

**CLM** has two separate effects.

- **Cold start.** The first inference after the encoder starts is off, by a different amount each start. The same synthetic request scored 0.860 and 0.857 as the first request after two starts, and 0.836 on all ten warm repeats. In the repeatability pass, this shifted every long-paper score in the first repetition, because CLM embeds each question's answer options once per engine. Amendment 1's warm-up addressed it. The scoring pass's re-check matched exactly.
- **Across launches.** Within one warm encoder process, CLM is exactly repeatable. Across two processes, every sampled element differs: median 0.009 in the long paper and 0.020 in the proceedings, maximum 0.058, 17 label changes. This was found after the fact. The frozen design used one process, and conditional sensitivity holds competitors fixed, so neither sees this. Passage 206 sits near the budget boundary, so CLM's verdict could differ on another launch.

## Observed but not pre-declared

Ten of Jev's twelve highest-scoring proceedings elements lie on pages 401 to 409, the LHD paper. The lens located the paper inside the volume, which bears on the paper-boundary limitation of artifact scoping. This is an observation, not a tested claim.

## Cost

| | Jev | CLM |
| --- | ---: | ---: |
| Scoring calls | 21,348 | 21,348 |
| Input tokens | about 7.3 million reported | about 1.3 million encoder tokens |
| Scoring time | 4 min 40 s, 8 in flight | about 5 min, sequential, plus about 90 s encoder start |
| Money | about $0.31 | local GPU under a lease |

## Limits

The builder wrote the task texts and selected the probes, and the proceedings task names LHD/RankCache. Both lenses were asked a question closely aligned with the probes. Six builder-selected probes cannot establish retrieval quality in general, and one question wording was tested. The instruction contains a double period from verbatim substitution of the task text, as frozen. CLM's scores come from one scoring launch.

Raw records stay owner-local under `tmp/classifier-lens-20260929/`. Compact results are in `experiments/classifier_lens/`.
