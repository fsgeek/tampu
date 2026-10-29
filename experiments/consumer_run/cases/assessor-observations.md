# Assessor observations before rubric freeze

Recorded 2026-10-28 by the builder acting as assessor, against published revision `0ea79b79668943969e5ee21dfdcbdfae` of collection `research`. These describe the corpus and Tampu's view of it. They do not interpret any consumer behavior, because no consumer has run.

## Extraction coverage of the artifacts mapped to the selected cases

The subagent mapped 22 artifacts to the six cases; 20 have full text coverage in the selected projection. Two have none:

| Artifact | Case | Tampu pages with text | pdftotext |
| --- | --- | ---: | --- |
| `e84337d12d0a` 2008 Formal Concept Analaysis and Semantic File Systems.pdf | yanantin_construction (likely present) | 0 of 185, 0 elements, `unattributed_pages` loss | readable; "libferris" occurs 63 times |
| 2018 A systematic review of provenance systems.pdf | pips (likely present) | 0 of 50, 0 elements | not yet checked |

The service declares both losses; the loss is visible, not silent. Lexical search for `libferris` returns an exact count of 0 across the collection.

Decision: no re-extraction before the run. Re-extracting after a case has been seen would change the system under test in response to that case. These gaps are what a consumer faces today. The yanantin_construction case becomes, in the terms of the 2026-09-11 design, an unavailable-extraction case. Its rubric will credit a consumer that locates the title-matching artifact and reports that its text is unavailable, and will not credit an answer that claims content it could not have read.

Collection-wide, `describe` reports 115 of 473 artifacts as blank or partial (12,198 of 16,990 pages with text). The README's "27 returned no text" counts artifacts with no text at all, so the two figures measure different things. The README should state both.

## yanantin_construction: source facts (from the PDF, not from Tampu)

- Page 1: "Martin, Ben, Formal concept analysis and semantic file systems, PhD thesis, School of Information Systems and Technology, University of Wollongong, 2008."
- Page 182, reference [62]: Ben Martin, "Formal concept analysis and semantic file systems", ICFCA 2004, LNCS 2961, pp. 88–95, Springer, 2004.
- The session's "2004" and the file's "2008" are both correct: the same title was used for the 2004 conference paper and the 2008 thesis. Only the thesis is in the corpus.
