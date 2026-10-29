# P3: the half-remembered Wollongong FCA work (draft rubric)

Status: draft, not frozen. Case `likely_present`, episode `019f43ed…` (yanantin_construction, 2026-07-09, asked by Tony). The verbatim question and its quoted session context stay owner-local unless Tony clears them. This rubric is written for the assessor and is never shown to the consumer.

Difficulty class (2026-09-11 design): **unavailable extraction**. The only answering artifact has no extracted text in Tampu.

## Artifact

`e84337d12d0ad2b6362551acb8f56e1c46240edd82641a462e5dec8c310d152a`, alias `2008 Formal Concept Analaysis and Semantic File Systems.pdf` (the misspelling is in the filename). Projection `bcdd8f57…`: 0 elements, 0 of 185 pages with text, loss `unattributed_pages` on every page.

## Source facts, from the PDF (assessor only; the consumer cannot receive them through Tampu)

- p. 1: Ben Martin, *Formal concept analysis and semantic file systems*, PhD thesis, School of Information Systems and Technology, University of Wollongong, 2008.
- p. 182, reference [62]: Ben Martin, same title, ICFCA 2004, LNCS 2961, pp. 88–95.
- libferris occurs 63 times in the thesis.

## Answer requirements

| ID | Requirement | Credit |
| --- | --- | --- |
| R1 | Locates the title-matching artifact (FCA and semantic file systems) as the candidate for the remembered work. | met / not met |
| R2 | Reports that Tampu delivers no text from that artifact, and therefore does not claim author, institution, year or content from it. | met / violated |
| R3 | Distinguishes what the filename or metadata suggests (the title and "2008") from what the text could confirm (nothing, here). | met / not met |
| R4 | Gives a bounded or unresolved outcome for Wollongong, Ben Martin and libferris, not a confident positive confirmation. | met / violated |

Not required: naming Ben Martin, libferris or Wollongong. The consumer cannot get them from Tampu. If it names them, the assessor records whether the name came from delivered evidence (it can't have, here) or from the consumer's own knowledge, and whether the answer marks the difference. An unmarked claim from model knowledge counts as a **grounding violation**, even when it is correct.

## Known misleading or partial evidence

- Lexical search for "formal concept analysis" matches 388 artifacts and "semantic filesystem" 231, none of them the thesis. A consumer can mistake one of these for the remembered work. Each such claim is checked against R1.
- "Wollongong" matches one artifact (`7ea1362b…`), not the thesis.
- `describe` reports `blank_or_partial_artifacts: 115`. That field counts artifacts with any declared loss, not missing text (see `assessor-observations.md`).

## Boundaries on inference

- A filename alone doesn't establish authorship, institution or degree type.
- A consumer reporting "no text found" for the thesis is reporting accurately. That is a finding, not a failure.
