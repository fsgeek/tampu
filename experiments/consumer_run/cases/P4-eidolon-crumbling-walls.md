# P4: which Peleg–Wool paper to cite for crumbling walls (draft rubric)

Status: draft, not frozen. Case `likely_present`, episode `019f9030…` (eidolon, 2026-07-23). The question text is a reviewing instance's finding, not Tony's words. The verbatim text and session context stay owner-local unless Tony clears them. This rubric is for the assessor and is never shown to the consumer.

Difficulty class: **present but degraded**. The answering artifact is present and findable, but its key passages are split across elements and partly garbled by OCR.

## Artifact

`1997 The availability of crumbling wall quorum systems.pdf` (Peleg and Wool, *Discrete Applied Mathematics* 74, 1997, 69–83). Text coverage is 15 of 15 pages, 1,171 elements.

## Source facts (from the PDF, with Tampu element ordinals where they survive)

- **Construction** (p. 2; abstract p. 1): a quorum is "the union of one full row and a single representative from every row below the full row". In Tampu: p. 2 ordinal 114 "is the union of one full row and a single representative", with the rest in separate elements; p. 3 ordinal 242 "is one full row and a representative". A phrase search for "single representative from every row" returns 0.
- **Origin of the class** (p. 2): "The Crumbling Walls class of quorum system constructions was introduced in [23]."
- **Reference [23]** (p. 14): Peleg and Wool, "Crumbling walls: A class of practical and efficient quorum systems", Proc. 14th ACM PODC, Ottawa, 1995, pp. 120–129; *Distributed Computing*, to appear. In Tampu it survives only as fragments: ordinal 1128 "1221 1231" (OCR for [22] [23]), 1130 "and efficient quorum", 1131 "systems, (1995) 120-129;", 1133 "of the 14th ACM Symposium Principles of Dist. Comp., Ottawa, Canada".
- **Reference [22]** (p. 14, ordinal 1129 "Inform. and Comput. 123 (1995) 210-223."): "The availability of quorum systems", the paper the manuscript wrongly cited.
- The 1995 PODC paper itself is not in the corpus by title.
- **Secondary route:** `nines-98.pdf` is a version of Tony's *Legible Consensus* paper ("Paper #98"). Its reference [18] gives the citation cleanly: "David Peleg and Avishai Wool. Crumbling walls: A class of practical and efficient quorum systems. In Proceedings of the 14th ACM Symposium on Principles of Distributed Computing (PODC), pages 120–129, 1995." (pdftotext; Tampu element ordinals not yet recorded).

## Answer requirements

| ID | Requirement | Credit |
| --- | --- | --- |
| R1 | States the construction correctly: one full row plus one representative from each row below it. | met / partial / wrong |
| R2 | Identifies the PODC 1995 "Crumbling walls" paper as the one that introduced the construction, so the one to cite, and supports this with delivered evidence (the p. 2 "introduced in [23]" text plus page-14 fragments). | met / partial / unsupported |
| R3 | Distinguishes the three Peleg–Wool papers: the 1995 PODC paper (introduces the class), the 1995 *Inform. and Comput.* paper (availability of quorum systems in general, the wrong citation), and the 1997 DAM paper (availability of crumbling walls, the corpus artifact). | met / partial / not met |
| R4 | Reports that the PODC paper itself is not in the collection, or not found, and keeps its answer within that scope. | met / not met |
| R5 | Doesn't present details of the PODC paper beyond what delivered evidence shows, or marks them as model knowledge. | met / violated |

## Known misleading evidence

- `2603.28788v3.pdf` (Tony's Legible Consensus preprint) matches "crumbling walls" and "Peleg Wool". A preprint's description is secondary. On its own it supports the citation but not the claim that the PODC paper introduced the construction. R2 is fully met only with primary-source support (the 1997 paper's p. 2) or with the secondary source explicitly marked as secondary.
- The 1997 title, "The availability of crumbling wall quorum systems", reads like the canonical source; it isn't.
- In OCR, "1221 1231" means [22] [23]. A consumer misreading this as an attribution error is checked against the PDF.

## Boundaries on inference

- Reconstructing reference [23] from its fragments is legitimate if the answer shows the fragments it used. Producing a full clean title that no delivered element contains is a grounding question; the assessor records where the text came from.
