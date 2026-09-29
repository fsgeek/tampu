# Ordinary retrieval competence: diagnostic test mechanism

Status: proposed design, 2026-09-11. No new consumer observation has been launched. This design follows the corrected retrieval/navigation attribution and does not claim that element counts have improved retrieval.

## Question and initial scope

Can an unfamiliar consumer use the current tools to find and correctly use the evidence required by a bounded research question? When it does not, where is the evidence lost? Start with the long caching paper and the distinction between its evaluated switching setting and its formal robustness qualifications. This is a development case already known to the builder, not held-out evidence of general competence.

Build a small repeatable diagnostic harness, not a single success score. Reuse the existing growing-corpus runner's prompt/schema capture, consumer isolation configuration, source identity, event/usage logging, trace custody, and final-answer checks. Keep new evaluation controls in the experiment harness. The existing runtime tools remain the system under test.

## 1. A case contract with separate consumer and assessor inputs

The consumer-facing case contains the actual research question, collection/revision, allowed tools, resource limits, and any explicitly granted starting information. It contains no target ordinal, physical page, ideal query, or expected conclusion. A case that supplies a relevant artifact is conditional on prior artifact discovery; label it accordingly rather than claiming collection-wide discovery.

The assessor-facing case contains:

- The answer requirements: claims, qualifications, assumptions, and unresolved distinctions that a satisfactory answer must address.
- Verified source addresses and minimal supporting text spans, with artifact/projection identities and source hashes. Whole-element delivery is not required if a shorter visible span supports the necessary qualification.
- Known misleading or insufficient evidence, such as a related-work claim mistaken for this paper's evaluated setting.
- Explicit boundaries on inference: recovering the evaluated setting does not by itself establish a relationship to the guarantee or a violation of it.
- Known extraction gaps and alternative acceptable evidence, with a rubric version.

Known addresses are probes, not an exhaustive relevance set. If a consumer supplies another plausible supporting passage, an assessor checks it against the same answer requirements. Record that adjudication and its source basis separately. Do not silently edit the frozen rubric or turn a newly discovered passage into a predeclared probe success. Assessors may access source material for validation; they must distinguish what they know from what the consumer actually received.

For the first pilot, supply the long paper's artifact identity and label the case **artifact-identified**. This directly tests the next step proposed in the preceding discussion. Collection-wide discovery and paper boundaries inside proceedings are separate subsequent cases; do not mix their difficulty into an unexplained aggregate.

## 2. An adaptive consumer with a bounded, recorded run

Use a fresh session with no prior assessments or builder discussion. Supply the case and current tool descriptions, including the count fields. Let the consumer choose queries, evidence openings, and continuations. Do not script a page-plus-one policy or conditionally feed it hints after a miss.

Initial limits: at most 12 admitted tool calls, 8,192 application-response bytes per call (at most 98,304 across admitted calls), and a 300-second consumer-process deadline. Calls that return service errors consume the allowance. The final prose answer is not a tool call. Record requests and their bytes, actual responses and their bytes, errors, refusals, completion status, usage, and elapsed time separately. These limits do not constitute a hard token or subscription-spend ceiling.

Enforce the tool execution limit at the evaluation server boundary, before another service operation can run. Serialize or synchronize budget accounting so concurrent requests cannot exceed the limit. Additional requests are refused and recorded separately; do not claim that fewer requests were attempted merely because fewer were executed. Keep a wall-time monitor for the process. Record termination lag and incomplete answers instead of labeling a progress message final.

The old runner monitors event counts and can observe an overrun after execution; it cannot be reused unchanged as a hard execution gate. Test the new gate with an instrumented fake service: excess and concurrent requests must not invoke the underlying service, errors consume their allocation, and captured byte totals agree with actual responses. Test completion/termination classification with recorded CLI-event fixtures.

Freeze case, rubric, requested model/settings, effective tool schemas, service commit, corpus revision, extraction identity, and budget settings before the run. Record whatever resolved model identity the backend exposes; do not invent a resolved revision or numeric generation cap. Check current CLI behavior before implementing invocation changes. Existing feature restrictions are a documented tool boundary, not an OS air gap.

## 3. Attribute evidence to the operation that first exposed it

For each answer requirement or known probe, retain the first delivered supporting text and its source span. Trace classification distinguishes:

| Operation role | What may be credited |
|---|---|
| Search | Evidence already visible in the search response |
| Opening a returned hit | Supporting text not previously delivered; opening the same complete text again adds no recovery |
| Further exploration | New supporting text delivered by page/ordinal inspection, continuation, or exploration beyond the original hit |

Also record access method and prior visible anchors so a reformulated search is not silently relabeled as page navigation. Address discovery and text delivery are separate events. Handle issuance alone is not proof that a useful passage was read. Citation eligibility and first text visibility are also separate: the service may require an explicit inspection before accepting a finding even when search already displayed the text.

Track visibility incrementally. Repeated copies do not earn additional recovery. If several deliveries collectively expose a required span, record the actual source intervals and the call at which coverage became sufficient; do not fabricate text across different sources. Human interpretation of semantic sufficiency remains an explicit adjudication, not a substring-based truth oracle.

Unit-test this attribution with synthetic traces for direct-hit-only recovery, additional text from opening a truncated hit, continuation recovery, repeated evidence, and address-only previews. The earlier ordinal-239 trace is a regression example: search earns the recovery; its later opening does not.

## 4. Diagnose a failed case at the appropriate layer

Inspect the trace before adding another run. Classify observable facts: requested predicates did not match known evidence; matching evidence ranked outside a delivered prefix; a qualifying address was available but unopened; relevant text was delivered but not used correctly; extraction was unavailable; or the process failed or exhausted its allowance. Some explanations remain unresolved, and several can apply to a case. Do not turn a post-hoc cutoff into a causal claim about why a client stopped.

Use deterministic replay for frozen queries, index selection, ranking, and response accounting where possible. This can expose a matching or packaging limitation cheaply, but does not substitute for the adaptive run or establish that the original query was adequate.

If the adaptive answer fails and interpretation versus access is still unclear, allow **one additional fresh-session direct-evidence control**: same question, with an assessor-prepared, source-attributed evidence packet. Prepare the packet before observations, include the required context and qualifications, and record its bytes. This is an easier diagnostic condition, not an equal-treatment comparison or a measurement of retrieval gain. Success would support investigating access failures; failure would leave interpretation, task/rubric quality, and run variability in play. One control cannot conclusively identify a cause.

Do not retry unsuccessful answers until they pass. Preserve every run and any infrastructure failure. Start with one adaptive run and at most one conditional control, rather than a large sweep.

## 5. Produce a case report that supports a next-change decision

Each report includes:

- Answer requirements met, qualified, unsupported, or unresolved, with visible source support and assessor rationale.
- Evidence first exposed by search, opening, and further exploration; incremental recovery separately from repeated delivery.
- Missing evidence and observable loss points, with uncertainty about causation.
- Executed and refused calls, application-response/request bytes, usage where available, errors, and final versus incomplete status.
- The exact hypothesis for any proposed change, and which failure that change might address. A useful general engineering improvement must be labeled separately from an experimentally supported retrieval remedy.

Keep these measures separate. No weighted aggregate score should conceal an unsupported mathematical claim, a missing qualification, or a budget failure. More returned passages or calls are not success criteria by themselves.

Once this mechanism produces an interpretable case report, add a small diverse set: collection-wide discovery, paper-locality inside proceedings, vocabulary mismatch, and unavailable extraction. Reserve independently selected cases for later evaluation rather than repeatedly tuning on exposed cases. Repeated model runs and a matched indexed-passage baseline belong to a later effectiveness comparison; a one-case pilot cannot establish general retrieval competence or statistical non-inferiority.

## Concrete implementation deliverable

Create an experiment package containing case validation, the budget-gated consumer launcher, trace attribution, and a report/adjudication format. Reuse the existing runner and repository interfaces where possible; do not rebuild ingestion or create a new search service. Keep source-bearing traces and assessor excerpts owner-local, with hashes and compact results preserved in Git under the existing custody policy.

The first deliverable is a tested mechanism plus one correctly attributed adaptive case report, including a negative or incomplete result if that is what occurs. No benefit claim for counts, no swarm benchmark, and no change to the frozen prior experiments is part of that deliverable.
