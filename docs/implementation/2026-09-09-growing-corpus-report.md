# Task 4: corpus growth, diagnostics and consumer evidence

Status: **DONE_WITH_CONCERNS**. Implementation and planned verification are complete. Independent Task 4 review and the controller's whole-branch review are pending the signed handoff; this report does not claim those reviews have already passed. No push or merge was performed. The main scientific concern is preserved failure of the original eviction r2 episode, not an unfinished substitute experiment.

## Deliverables and final behavior

The durable [results report](../experiments/2026-09-08-usable-prototype-results.md) contains extraction/publication measurements, all five original outcomes, sixteen per-arm response outcomes, source judgments, limitations and the eight binding MVP completion criteria. Paths in this durable copy are relative to `docs/implementation/`; the ignored scratch copy is the same archival text.

- `experiments/growing_corpus/run.py`: thin real Codex consumer/publication runner; exact prompts/argv, requested model/settings, MCP schemas, owner-local full traces, event/usage/time/byte accounting, clean source identities before/after, predecessor publication guards and explicit observed-overrun termination.
- `diagnostics.py`: actual tiny PDFs and real cached source projections in a separate database, including add/replace/remove, failed processing, byte aliases/work versions, lexical negative/alias recovery and explicit CORFU processing-change behavior.
- `comparisons.py`, `comparison-protocol.md`, `comparison-inputs/`, `batch.py`: actual provider observations, allowlisted masks, exact questions, arm-specific visible-evidence rubric, full path/value diffs/schema/byte/hash audit, seed20260909 order and sixteen fresh response-only processes with at most four concurrent.
- `direct_evidence.py`, `direct-evidence-manifest.json`: separately labeled post-original diagnosis with thirteen builder-selected source passages and the last completed r1 assessment. No original response is replaced.
- `audit.py`, `evidence/`: compact actual assessments/metrics/source judgments, exact old-byte audits, projection/publication records and hashes/locations for owner-local source-bearing traces. The original failed r2 summary/text remain unchanged; explicit adjudication and derived metrics mark the lack of a final assessment.
- `src/tampu/capability_evidence.py` and Service discovery: evidence configuration separate from operational counts; consumer benefit remains unestablished, development outcomes mixed, path machinery inconclusive/disabled. No hidden answer labels or credentials enter runtime configuration.
- MCP/Service inspection guidance now discloses listing limit1..20 and slice1..4000 and explains preview handles versus returned inspected citation handles. This happened **after all originals and comparisons** and has not been evaluated for consumer benefit.
- README now describes working code and observed limitations. Tracked Task1/2 reports were moved unchanged to `docs/implementation/2026-09-08-{capture-extraction,repository}-report.md`. Accepted Task3 report was preserved as `2026-09-08-mcp-service-report.md`. This Task4 report is also preserved in durable docs; the ignored skill-workspace copy is never force-added.

## Actual execution and observations

Reused the completed twelve-PDF extraction pilot, chosen pinned Unstructured fast profile, all473 cached primary projections and actual r0 publication. Did not recreate baseline or publish r1 until both r0 originals finished. Source snapshot953copies were previously verified; stage publication independently verified working-root hashes/counts.

| Stage | Revision | Captured/ready | Physical/text pages | Publication seconds |
|---|---|---:|---:|---:|
| r0 | fa9221b03c3b4aaaa7c54125f23eadb9 |160/160|4467/4327|204.22|
| r1 |7e44b119852a4f16b5f470b321fa91ef|320/320|10565/8464|363.09|
| r2 |0ea79b79668943969e5ee21dfdcbdfae|473/473|16990/12198|528.29|

All original selected profiles remain Unstructured. Ready means processing completed, not semantic coverage:27artifacts have zero text. Full extraction took1796.58s with4workers,353808elements. Twelve-PDF pilot covered791pages/774textpages in both profiles; final per-page Poppler adapter total19.88s. The controller chose Unstructured's paragraph/category/coordinate utility after rendered checks; readiness favored Poppler's speed. Neither establishes semantic equivalence/completeness. CORFU's specific upstream complexity-gate cause was confirmed; other26causes remain unknown.

r1/r2 record identical clean before/after source hashes. r0's record captured HEAD when written, not import-time module hashes; the narrow attribution limitation is preserved. Older short-caching and Legiblev2 PDF/raw/elements bytes matched all six baseline hashes after r2, and fresh Service operations reopened the old r0 membership/projections. This is not historical-score re-execution.

The original consumers actually called MCP using requested `gpt-5.6-sol`, medium reasoning, CodexCLI0.153.4 and the verified on-request/automatic-review route with truthful state-changing annotations. Shell/apps/browser/web/host skills were disabled and only four Tampu tools were exposed. This is a CLI/tool boundary, not an OS air gap. Resolved model revision, numeric generation cap, per-call reviewer reasoning and monetary cost were not exposed. All actual errors/usage/termination remain recorded. Cumulative input includes cached repeated context, not unique evidence.

| Original | Calls | Seconds | Input/output tokens | Result |
|---|---:|---:|---:|---|
|Evictionr0|20|149.66|212496/4077|Completed, supported/unresolved findings.|
|Legibler0|17|204.02|385289/5359|Completed, correct version/explanation/threshold and mathematical concern.|
|Evictionr1|20|203.37|224116/6111|Partial update; positive finding rejected on preview-only handles, unresolved recorded/released.|
|Evictionr2|24|106.33|Unavailable|Budget-overrun failure; no final turn, assessment or finding.|
|Legibler2|16|182.41|276440/4814|Completed, changed justification/unchanged threshold.|

97actual completed tool calls produced270210applicationJSONbytes, all within requested budgets, oneTextContent, no structured duplicate, matching Service traces.21controlled application errors remain part of the observed effort. Original tool schemas occupied10833prettyJSONbytes per episode. Compact wrapper-byte proxies and available usage are in measured records; no exact wire-byte or dollar-cost claim.

Material-source review was performed by the worker and independently by root. Evictionr0 was mostly supported, with unresolved average/aggregate-loss normalization. Evictionr1 correctly observed the long report's outer-factor bound difference but missed empirical overlap, CitiBike and switching-cost-k qualifications, and incorrectly strengthened its own prior scope to global absence. The final eviction episode retrieved the NSDI **artifact** with an unrelated p305 passage and Pichay with a p3preview, but opened neither relevant source. Do not equate artifact retrieval with delivery of LHDpp400–414. It ended after a rapid burst of invalid12000-character slices; the monitor observed24calls rather than preventing21.

The runner initially mislabeled that episode's last progress message as final because text existed, despite no `turn.completed`. Original summary/text were preserved; completion-adjudication.json and derived metrics correct the claim. No original was retried to improve its answer.

Both Legible conclusions were source-supported. v2's pair-overlap justification is mathematically problematic, while its hitting-set threshold is correct; v3 changes the explanation and leaves the stated threshold unchanged. The r2 consumer reopened v2's same projection inside currentr2, while the separate old-revision audit supplies r0membership access. Source rendering also corroborated the longp9 formula transcription without claiming proof validity or actual-performance lower bounds.

All six diagnostics passed in a different database. The first setup selected the other, 2012CORFU paper by title substring; a coverage assertion caught it before any comparison consumer. Its failed records remain, and a corrected fresh isolated database pinned the full2013artifacthash. Corrected diagnostics took3.13s using cached projections. Explicit CORFU reprocessing kept artifact identity, changed one projection selection, produced24/24textpages and preserved the old0/24projection. A preview-only capture initially failed comparison-input construction; the recorded follow-up handle inspection supplied the full passage, and the durable script now follows it directly.

All16response-only comparisons completed with zero tools/no retries. Present arms all chose present/stop (no stated-step effect). Scope-hidden absent wrongly chose boundednegative/stop; alias arms stayed unresolved with terminology variants. CORFU count-only chose a mismatched class but its sentence correctly bounded the lexical negative and left source support unanswered, earning calibration/next-step credit. CORFU's “shown zero matches” wording was treated as ambiguous displayed-hit wording, not categorically penalized as an invented total; initial adjudication is retained locally and the independent-review correction disclosed. Full per-arm scores/questions/rationales are in the results/evidence, without pooled efficacy statistics.

The separate direct-evidence diagnostic completed48.10s,12389input/1554outputtokens,0tools. It correctly qualified the unexercised random switch, Pichay pinning/future prediction and LHD implementation patterns, labeling transfer as inference. It demonstrates useful interpretation with curated passages, not comparative benefit or an isolated explanation of the original failure.

## Commands and verification

Exact stage/original/comparison/direct-diagnostic commands and frozen source commits are in `experiments/growing_corpus/README.md`. Every model invocation is retained in its owner-local run directory. The actual run used `/home/tony/projects/tampu/tmp/prototype-readiness/{growth,consumers,task4-diagnostics-corrected,comparison-consumers,diagnostic-consumers}`; hashes/locations are in durable evidence. The corpus/store/config remain outside Git.

Post-observation regressions first ran:

```
uv run pytest tests/test_growing_corpus.py tests/test_service.py::test_discovery_slice_limits_match_actual_inspection_validation tests/test_mcp.py -q
5 failed, 1 passed in 3.72s
```

Expected red failures were progress-only, failed-turn and interrupted-turn messages incorrectly labeled final, missing Service slice bounds, and missing MCP schema bounds. Minimal fixes made all6cases pass in3.52s. Current runner requires completed/nonfailed/nonstopped lifecycle, successful exit and an agent message; incomplete text is saved separately.

Final planned gate:

```
uv run pytest tests -q
83 passed, 1 skipped in 11.00s

uvx ruff check src/tampu tests scripts/provision-tampu.py experiments/growing_corpus
All checks passed!

uv run python -m compileall -q src tests scripts/provision-tampu.py experiments/growing_corpus
exit0

git diff --check
clean
```

The skip is the opt-in real Unstructured test; actual extraction evidence is retained separately. The MCP test uses fresh CLI/MCP subprocesses with a disposable dedicated database. A separate live final `.venv/bin/tampu describe` and real stdio describe/search/inspect/finish smoke succeeded at r2, recorded a positive finding from an actual inspected citation, released state and ran with trace disabled. Its source hashes and schemas are saved.

Root separately ran the old documented path harness:21passed in1.58s at6ae4ad6 using the llm-memory environment and dedicated18529server, then stopped only that container while preserving data. Its exact command/result is retained; the suite was not duplicated. All960then-manifested owner-local file hashes and both unchanged report migrations were verified. Final local-document-link and tracked-content audits are in the verification record.

## Signed implementation history

The task began on signed/stamped base `6ae4ad6b36a34666a72318b4fc745da84455232f` in the existing isolated `experiment/path-holding-pilot` worktree.

- `c51018ac437f876e2ad213af2d6d7f22d10c1d0b`: initial frozen consumer runner/prompts; stamp4995f63.
- `b54688d2706552207bcf998f0c679a390c605527`: diagnostics and final-only staged resumption; stamp4329f35.
- `cfeb8c809bb2131ce3ae56df35b2567ed18b45ed`: exact CORFU correction and comparison protocol; stamp2f64605.
- `a55d9456c078724800754555abc68602bfaf734f`: static-check correction; stamp704cdef.
- `a5bf55b7950080d33ad9b32be2391e69330d15f1`: all sixteen matched inputs/masks/rubrics frozen before calls; stamp427112b.
- `8ce02342ed54f3d7dd27852903f9add24dac5ff1`: post-observation completion/discovery fixes, direct-diagnostic recipe/input hashes and compact audit; stamp1738ef4.

Final documentation, capability evidence, measurements and preserved implementation reports are committed together in the subsequent signed Task4 results commit; its exact identity is supplied in the handoff and obtainable from this file's Git history. Automatic OpenTimestamps commits accompany each implementation commit. No push or merge.

## Self-review and limitations

The eight binding MVP criteria and every Task4 brief item are mapped to actual evidence in the results report. Processing/coverage, artifact/work identity, source/publication time, original/diagnostic roles, source support/consumer claims and interface benefit are kept distinct. The main unresolved results are scientific: failure of final original eviction synthesis, missed empirical qualifications in r1, lack of efficacy evidence, successful-empty extractions and limited source checks. The direct diagnosis narrows what the model can do with selected passages but does not isolate a cause. Optional path machinery remains disabled after the inconclusive0/4uptake pilot.

The runner is a fixed experiment tool, not a general framework. It refuses overwrites/dirty observation sources, but its tool monitor observes overrun rather than preventing every excess call. The CLI boundary is not an OS air gap; model identity/generation limits are partly unobservable. Full source-bearing records remain owner-local, so readers need those files to reproduce source judgments. Updated discovery has only contract/regression/smoke evidence, not rerun consumer effectiveness evidence. Independent Task4 and whole-branch reviews remain the controller's next step.
