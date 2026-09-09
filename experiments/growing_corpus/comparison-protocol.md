# Development response-interpretation comparison protocol

Status: implementation protocol frozen before response-only observations. Development-only, builder-exposed, and too small for efficacy or statistical claims. The Task 4 worker captures the real provider observations and runs consumers only after the response interface is reviewed. The owner-authorized Task 4 run uses isolated diagnostic data and records all actual consumer outputs.

## Question and limits

Question: when shown a frozen real candidate-provider observation, does a model interpret a lexical result more carefully and state a feasible next step when negative scope, candidate count, or coverage is visible?

Each consumer sees one frozen payload and cannot call Tampu or any other tool. The outcome is a **response interpretation and stated next-step choice**. It is not actual navigation, stopping behavior, repeated work, latency benefit, or finding efficacy. Report every response individually, including refusals and no-effect arms. Do not calculate p-values, confidence intervals, effect sizes, win rates, or general model/product claims.

## Frozen observations and case admission

Use one real candidate provider and one published revision/projection selection for every matched pair. Capture the unmasked JSON response, exact provider request, response schema version, revision ID, projection recipe/digest, response SHA-256, byte length, and timestamp before masking. No field may be invented or recomputed differently between arms.

Admit these four negative-scope cases only after an independent builder check agrees with the provider observation:

| Case | Required actual provider observation | Case-question contract | Expected calibrated interpretation when scope is visible |
| --- | --- | --- | --- |
| `present` | Nonempty result for an exact predicate, with one inspected source passage supporting the target | Ask whether the displayed evidence supports the specific proposition stated in the question | Present in the displayed lexical evidence; do not abstain indiscriminately |
| `absent` | Successful zero-candidate exact predicate over a controlled, completely covered fixture/subset | Ask only whether the **exact named predicate** has a match in the stated fixture/subset and representation | No match for that exact predicate in the stated representation and scope; do not claim semantic absence |
| `alias` | Zero candidates for one exact surface form, while an independently checked alias/paraphrase query against the same membership returns the target | Ask whether the **concept**, named independently of the failed surface form, is supported in the collection | Unresolved for the concept; state an alias/paraphrase refinement rather than absence |
| `processing_gap` | Zero candidates for text known to occur in CORFU artifact `e334…a93`, whose selected Unstructured projection has 0/24 text pages while the artifact remains in revision membership | Ask whether the named CORFU source supports the specific proposition, without exposing builder truth or alternate-extractor text | Unresolved because the searched representation lacks usable coverage; mark coverage unavailable/review-needed, with no claim that an automatic fallback exists |

The CORFU diagnosis may establish the processing-gap label, but its hidden direct-extraction text and root-cause notes must not enter a consumer payload. The original selected empty projection remains the observation under test. If any case fails its admission condition, record it as excluded and do not replace it after seeing model responses.

Before masking, write one concrete, grammatical `question` string for each admitted case in the pre-run case sheet. Substitute exact predicates, concepts, sources, and propositions there; do not leave template variables in consumer inputs. That question is a common payload field and must be byte-identical in every arm for that case. Builder-established truth, alias-query results, and alternate-extractor evidence stay only in the sealed case sheet, never in `question` or another consumer-visible field.

For count/coverage, select exactly two of the admitted real observations before consumer runs:

1. one nonempty observation where `candidate_count > returned_count`, so count can change the stated inspection/pagination decision;
2. one observation with incomplete or unavailable coverage, preferably `processing_gap`, so coverage can change claim calibration.

The displayed hits and evidence snippets, their order, and all non-intervention fields must be byte-identical across the four arms for a selected observation.

## Arms and run count

Negative scope uses four cases × two arms = 8 fresh consumer responses:

- `scope_present`: retain the exact predicate contract, lens/representation, pinned revision, searched projection subset, coverage, and typed processing gaps/omissions.
- `scope_absent`: omit that scope block and all equivalent fields. Retain the common result status, frozen hits/evidence, and the same truthful full candidate count/count-kind as `scope_present`.

For this negative-scope family only, `candidate_count` and `count_kind` are invariant common fields in both arms. A successful empty case must show truthful `candidate_count: 0` with a count kind establishing an exact, complete candidate count rather than a returned-hit count. Exclude a zero case if the provider reports only `returned_count`, a lower bound, a capped count, or an unknown count. Thus `hits: []` is never treated as an exact zero merely because a display limit, including limit 0, may have hidden candidates. This family varies only the declared predicate/representation/revision/coverage scope bundle.

Validity gate for the controlled absent pair: `scope_present` contains the case question's exact predicate, an exact full zero candidate count/count-kind, representation/lens, pinned revision, selected projection scope, and complete coverage needed for a predicate-bounded negative. `scope_absent` contains the same exact zero count but lacks the declared representation/revision/coverage scope needed to bound that negative, so its visible-evidence expected class is unresolved.

Count/coverage uses two observations × four arms = 8 fresh consumer responses, run separately from negative scope:

- `neither`: candidate count and coverage absent.
- `count_only`: truthful candidate count/count kind present; coverage absent.
- `coverage_only`: truthful coverage and processing gaps present; candidate count/count kind absent.
- `combined`: both field groups present.

For this family, keep the effective predicate and mode, lens/representation, revision, selected projection identity (without coverage status), operation status, question, hits/evidence, and all other non-coverage identity fields byte-identical in all four arms. Vary only (a) candidate count/count-kind and necessary count qualifiers and (b) processing/text-coverage fields. Learning which query or revision produced the observation is not part of the coverage intervention.

Total: 16 responses. Use a fresh model process for each response, the same model identity, reasoning setting, system prompt, user prompt, temperature/default sampling settings, and supported default output-token settings. The numeric provider/CLI generation cap is not exposed by the verified route; no speculative config key is used. This is an explicit protocol amendment before observations. Prompt length guidance would not enforce a cap. Retain actual usage, truncation and termination. Randomize arm order with a recorded seed before execution. Never retry a substantive response; retain errors/refusals as observed. A transport failure may be rerun once under the same arm and must retain both attempts.

## Payload masks and leakage audit

Produce arm payloads from the captured provider JSON through an allowlist, then serialize canonically. Do not redact text in place because keys, punctuation, `null`, array length, or byte shape can disclose the arm.

Common allowlist:

- public case label (`A`, `B`, etc.; never `present`, `absent`, `alias`, or `processing_gap`);
- the case's explicit `question`, byte-identical across all of its arms;
- operation status and error code/message if genuinely returned;
- fixed displayed hits and inspected evidence, including stable public source/evidence labels required to interpret them;
- the consumer question and generic statement that the payload is one lexical observation.

Negative-scope-family common additions, byte-identical in both arms: truthful full `candidate_count`, its exact `count_kind`, and only the qualifier required to establish that the count is complete and uncapped. `returned_count`, display limit, and visible hit-array length may remain when byte-identical, but cannot substitute for full count/count-kind.

Count group for the **count/coverage family**, present only in `count_only` and `combined`: `candidate_count`, `count_kind`, and any explicit cap/truncation qualifier needed to interpret that count. This conditional mask does not apply to the negative-scope family.

Negative-scope intervention group, present only in `scope_present`: effective lexical predicate and mode, lens/representation identifier, revision identifier, selected projection scope, covered/eligible/failed or unavailable projection counts, enumeration completeness, typed omissions/processing gaps, and coverage qualifiers.

Count/coverage-family identity group, present in all four arms: effective lexical predicate and mode, lens/representation identifier, revision identifier, and selected projection identity stripped of coverage/status facts. Count/coverage-family coverage group, present only in `coverage_only` and `combined`: covered/eligible/failed or unavailable projection and page counts, enumeration completeness, projection processing statuses, typed omissions/processing gaps, and coverage qualifiers.

Remove all direct equivalent-field leaks from arms where the corresponding group is absent: `total`, `matched`, `count`, `count_kind`, `returned_count` (the visible hit-array length remains observable), `has_more`, cursors encoding totals, pagination summaries, facet counts, aggregate counts in prose, coverage percentages/counts, page totals/text-page totals, failure/loss arrays, `projection_status`, extraction profile/recipe, omission strings, negative-claim scope, and nested copies under `meta`, `details`, `scope`, `coverage`, `summary`, `describe`, handles, or errors. In the negative-scope family, exempt only the explicitly invariant exact candidate count/count-kind and necessary exactness qualifier; audit that they are identical across both arms. In the count/coverage family, remove count equivalents from `neither` and `coverage_only`, and coverage equivalents from `neither` and `count_only`, while retaining its common identity group in every arm. Replace opaque handles with arm-local random opaque IDs of equal length if their encoding or lookup could leak values. Do not expose `describe`, inspection beyond the frozen evidence, hidden truth metadata, manifest data, scenario labels, expected answers, or future-revision data.

The audit establishes removal of direct equivalent fields, not information-theoretic concealment. Record logical overlap that remains observable—for example, zero text coverage may strongly imply zero lexical candidates, and visible hit-array length reveals returned hits. Interpret arm differences with those overlaps disclosed.

Before runs, recursively enumerate every JSON path in each arm. The worker must record a path/value diff and schema/UTF-8 byte length for every payload, manually inspect all strings for count/coverage paraphrases, and verify masked groups occur at no alternate path. Differences outside arm-local opaque IDs and the declared intervention fields invalidate the matched set before consumer execution.

## Exact consumer prompt

Use this text verbatim for every run, followed by one canonical JSON payload in a fenced `json` block:

> You are reviewing one frozen lexical-search observation from a PDF collection. Answer the `question` in the payload using only the fields and evidence shown. The observation may omit information; do not infer omitted counts, coverage, aliases, processing status, or corpus completeness. A zero lexical match can support only a predicate-scoped statement when its searched representation and coverage warrant it; it does not prove that an idea is absent from source PDFs. A nonempty hit is evidence only for what its displayed passage supports. Return exactly one JSON object with these keys: `conclusion_class` (`present`, `bounded_negative`, or `unresolved`), `conclusion` (one sentence), `basis` (an array of zero to three shown field names or evidence labels), `next_step` (one sentence describing the single best feasible next action, or `stop`), and `confidence` (`low`, `medium`, or `high`). Do not mention this experiment, hidden conditions, or information not shown.

No system text may contain case truth, desired action, hidden fields, or scoring rules. The consumer receives no prior assessment or cross-arm transcript.

Because this common prompt explicitly teaches lexical-negative calibration and warns about omitted fields, these observations measure payload-field effects **under that instruction**. They do not show how an unaided consumer would reason or whether the same fields change behavior under other prompts.

## Fixed scoring rule

Score mechanically against the pre-run case sheet, then retain adjudicator notes. Maximum 4 points; do not aggregate into an efficacy statistic.

1. **Class (0 or 2):** match the expected class fixed for that exact masked payload from visible evidence. For the negative-scope pairs: `present` expects `present` in both arms because the displayed passage supports the proposition; `absent/scope_present` expects `bounded_negative`; `absent/scope_absent` expects `unresolved` because predicate scope and coverage are hidden; `alias` expects `unresolved` in both arms because an exact-surface-form result cannot answer the concept question; and `processing_gap` expects `unresolved` in both arms, with the gap reason available only when coverage is visible. For count/coverage payloads, assign the expected class separately before runs after applying each mask; never score against hidden case truth.
2. **Claim calibration (0 or 1):** award only if the sentence stays within displayed evidence. A bounded negative must name the exact lexical predicate/representation/scope available in that arm and must not assert semantic/document/corpus absence. A present claim must not exceed its displayed passage. An unresolved claim must not invent the hidden reason.
3. **Stated next step (0 or 1):** award only if it is feasible from the shown observation and appropriate to the stated uncertainty. Accepted examples are inspect/paginate when undisplayed candidates are truthfully visible in the count arm; try a named alias/paraphrase in the alias case; request review or an explicitly supported alternate projection in a processing gap; or `stop` for the controlled exact absence when complete scope is visible. Do not award for inventing a masked value, assuming an automatic fallback, always stopping, always abstaining, or prescribing narrowing merely because a count is large. Asking whether more candidates exist, or requesting another page conditionally if available, is feasible when the count is hidden; do not penalize it merely because additional candidates have not been established.

Malformed JSON, refusal, or no substantive interpretation scores 0 and remains in the record. `basis` is audited for hidden-field invention but adds no separate point. Confidence is descriptive and unscored. For masked arms, a response may be appropriately unresolved because it lacks scope; do not force a bounded negative that cannot be warranted from its payload.

The pre-run case sheet must record the exact question, visible-evidence expected class, acceptable claim boundary, feasible next-step set, and disallowed overclaim for each individual masked payload **before** any consumer response. Freeze its SHA-256 with the payload hashes and prompt hash. A hidden builder label may justify case admission and adjudication boundaries, but cannot create a class penalty for a conclusion that is appropriately unresolved from the consumer-visible payload.

## Run record and reporting

For every observation retain: provider request/response; unmasked and masked payloads; path/value mask diff; schema and UTF-8 byte counts; prompt; model/config identity; randomization seed/order; raw CLI events and final response; input/output/total usage when reported; latency; error/refusal; score fields and rationale; builder/adjudicator exposure; and hashes of all fixed inputs.

Report 16 rows, not a pooled win rate. Describe whether individual responses changed class, calibration, or stated next step under a matched mask. State plainly that the builder authored labels and inspected evidence; these are development observations, not held-out consumers. A response that names a better next step demonstrates only stated interpretation. Actual navigation requires a separate tool-enabled episode measuring calls, inspected evidence, findings, and cost.

## Instantiated inputs

`comparisons.py` consumes actual `diagnostics.py` Service responses. Raw paths are `response.result.full_count`, `count_kind`, `predicate`, `lens_config.analyzer`, `revision_id`, `projection_selection`, `coverage`, `hits`; inspected evidence is `inspection.result.evidence`. Projection records supply exact IDs, recipes, digests, losses and processing status to the sealed observation record. Only explicit allowlisted groups enter visible payloads. Actual payload paths/hashes and arm-specific scoring boundaries are recorded in `comparison-inputs/{freeze,mask-audit,case-sheet}.json` before calls. All full provider records and source-bearing traces remain owner-local.
