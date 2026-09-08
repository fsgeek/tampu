# Tampu initial prototype design

Date: 2026-09-07

Revised: 2026-09-08, following Claude's review and Astra's assessment.

Status: proposed design for review; no prototype implementation or experimental result is claimed.

## Purpose and research questions

Build a local service through which an AI can investigate a changing collection of PDFs using bounded observations, inspectable evidence, and revisitable finding journeys. Evaluate the AI's finding episode and the contribution of the interface. Tampu supplies evidence and scope; the consumer judges its significance.

Tampu's research objective is to establish whether its finding interface improves consumer outcomes over specified retrieval interfaces. The initial questions are:

1. **Does exposing the predicate, revision, and coverage behind a negative result improve stopping and claim calibration?** Measure correct scoped negatives and unresolved outcomes, unsupported answers, and false negatives on matched present/absent tasks. A system that always abstains has not succeeded.
2. **Does exposing candidate counts and coverage improve navigation?** Measure whether consumers select useful refinements or inspections, and whether finding quality, repeated work, and total context cost improve. Counts may sometimes justify inspecting the sample immediately; narrowing is not intrinsically the correct action.
3. **Does a consumer backtrack more effectively when the tool holds the path than when it must reconstruct the path from its own context window?** Backtracking is already observed behavior. The hypothesis concerns the contribution of external path state, not whether consumers backtrack at all. Later-session and human-reader benefits are separate hypotheses.

The first exploratory task performed **using** Tampu is: **When does forgetting produce a detectable miss, and when does it silently change an answer?** Search across caching, memory management, retrieval, and the ayllu's papers. Find a small number of independent works, locate supporting passages, identify mechanisms and assumptions, and distinguish authors' claims from the consumer's analogy. An unresolved comparison is acceptable when the corpus does not supply the necessary evidence.

Companion tasks examine limitations of metrics and representations, recovery from misleading early results, and discovery of qualifications that change a preliminary finding. We are testing whether the interface helps an investigator revise an account as well as support it.

The initial local inventory contains 479 PDF paths, 473 distinct byte contents, and approximately 913.5 MiB of source files. These are observations made during design, not fixed dataset membership. The collection includes articles, books, proceedings, preprint versions, and submissions. For example, a proceedings PDF and a file named after a plagiarism paper have identical bytes. Filenames therefore cannot establish either work identity or independent corroboration.

## Target mechanisms and limits of this corpus

The initial prototype tests interface quality on a small corpus. It does not establish that RAG fails with growing collections. Separate the mechanisms before choosing experiments:

| Candidate failure mechanism | Initial experiment and warranted scope |
| --- | --- |
| Sample ambiguity: a consumer cannot tell whether a small sample represents a small or large candidate set, or how much was processed | Vary matching distractors within nested, recorded corpus subsets; expose or hide counts and coverage while holding hits fixed. Hundreds of PDFs can support this contrast if a pilot verifies sufficiently different candidate counts. |
| Context accumulation: repeated retrieval introduces material that obscures qualifications or consumes the available budget | Measure complete episodes and backtracking under matched runtime context policies; a constant top-k response size by itself is neither evidence of flooding nor proof of bounded episode cost. |
| Missed relationships: separately retrieved passages do not reveal a relevant link or conflicting qualification | Construct tasks with independently verified evidence across artifacts. Chunking can obscure relationships, but does not make their recovery categorically impossible. |
| Candidate crowding in an embedding representation | Deferred scale study requiring measured similarity/recall changes, near-neighbor distractors, multiple corpus sizes, and a working embedding baseline. Artifact count alone neither establishes nor rules out this effect. |
| Stale observations after additions, removals, or revisions | Publish controlled successor revisions and check whether the consumer distinguishes evidence about the old collection from evidence about the new one. |

Do not describe empty results as unrepresentable in RAG. For example, vector retrieval can exclude results using score thresholds [4], and retrieval-augmented systems can include relevance assessment [5]. A thresholded empty list still does not establish semantic absence. Tampu's proposed benefit is making the scope of an observation usable by the consumer; its advantage must be measured against concrete, capable baselines.

## Tooling decisions and alternatives

**Use ArangoDB, the installed Unstructured container, Python 3.14, and an MCP stdio interface.** Use `python-arango` for database access and the existing llm-memory implementation as an interface reference. Tampu gets its own database and scoped credentials on the existing service. It does not add records or indexes to llm-memory's database.

ArangoDB already fits the local operation and offers document storage, graph edges, and ArangoSearch. Its full-text search supports filters and BM25 ranking; its eventual index visibility must be handled explicitly [1]. The deployment target is the local single-server enterprise instance on port 8530, subject to authenticated connection and scoped-database checks before ingestion. The core does not depend on a vector index or cluster transactions.

Read-only verification on September 8 found `arangodb/enterprise:3.12.9.4` running on port 8530 and the older community instance on port 8529; both returned HTTP 401 to unauthenticated version requests. These observations establish running containers and authentication requirements, not authenticated database readiness. The enterprise version supports vector indexes [6]; actual vector enablement, scoped permissions, and a tiny query smoke check remain prerequisites for the later semantic comparison. Embedding deferral is a sequencing choice, not a claimed hardware limitation.

Alternatives considered:

| Approach | MVP benefit | Cost and decision |
| --- | --- | --- |
| ArangoDB plus local immutable files | Reuses existing operational knowledge; one database for metadata, retrieval, and preserved journeys | Requires a running service; selected |
| SQLite plus FTS5 and local files | Could make distribution self-contained | Introduces a different backend before demonstrating a finding benefit; deferred |
| Existing vector-oriented RAG stack | Could accelerate an embedding-based demonstration | Adds representation and integration choices before testing navigation; useful later as a comparison |

Reuse Unstructured's partitioning rather than implementing a document parser. Keep `pdftotext` as a separately named extraction baseline. No external extraction or embedding API is required. Pin the container by manifest digest `sha256:806726e3997d33bce9e32facd86c947b241101c58496f2774ad5f09f86e798bc`. The locally inspected image ID is `sha256:60066fe6bd5c64a64e8060e3ef6c82af7386592c0445b29bc1c263ff4e270ee4`, with reported size 14,846,550,466 bytes. `latest` is a moving tag; the manifest digest identifies the selected image. The image was present but no Unstructured container was running during the September 8 check. Record the actual package versions and extraction settings in each run.

## Architectural commitments and first implementation

Artifact primacy, explicit scope, versioned projections, immutable journey records, plural lenses, provenance, and honest capability discovery remain architectural commitments from the founding document. They are design premises, not empirical findings. Keeping parent references and operation identity in the semantic kernel does not require implementing a graph database, composition engine, or checkpoint service in the first release. No implementation may silently change the meaning of those records.

The first MVP provides:

- One registered local PDF directory per collection; multiple explicit observed revisions.
- Lexical, exact metadata, and temporal lenses, with named versions and distinct coverage.
- Artifact-level candidate counts and samples; inspection down to a page and extracted element.
- Ephemeral result handles and immutable operation records with parent references, plus a minimal path-holding treatment for early backtracking experiments.
- Bounded counts, coverage, and consumer-declared findings, including machine-checked predicate negatives.
- Structural operational measurements and an explicitly enabled research trace mode.

The first path experiment adds only bounded history, parent-based branching, and recorded-result replay within one process. A parent-linked map of immutable records is sufficient. Measure its contribution before building set composition, recursive refresh, durable preservation, or saved-journey database collections. Their contracts below describe optional extensions; they are not MVP completion requirements. A finding of no useful same-session benefit should trigger simplification and a separately justified later-session/human-reader experiment, not automatic construction of the full graph machinery. Results or components that do not earn their cost in Tampu may still inform Yanantin.

General semantic embeddings follow the core interface diagnostics and early path experiment; composition and durable preservation are not prerequisites. Before a comparative vector experiment, freeze the embedding model/version, input projection and chunking, query transformation, corpus revision, index/search settings, filters, deduplication, and consumer settings. Verify the vector index works and expected candidates are retrievable. Give the baselines relevance thresholds and abstention behavior calibrated on separate development tasks. Compare one-shot and iterative retrieval with Tampu using the same semantic candidate provider; vary interface features separately. If a lens change is itself the treatment, report that separately from a navigation-interface claim. These conditions make the comparison possible; availability of a vector-enabled server alone does not.

The storage and tool contracts below label deferred capabilities explicitly. `describe` reports their actual absence, and unimplemented actions are excluded from tool schemas. This preserves an architectural destination without making it a release checklist.

Other deferred capabilities: cloud connectors, continuous filesystem watchers, automatic work/version resolution, citation-graph extraction, ontology construction, automatic summarization, historical query re-execution with identical rankings, managed conversation compaction, and multi-user hosting. The service can expose a useful compact state; the consuming runtime controls whether old tool responses remain in its context.

## Source admission, identity, and revisions

For this prototype an artifact identity is the SHA-256 digest of its PDF bytes. Byte-identical files share an artifact and extraction, while every observed path remains in the source inventory. Modified bytes produce a new artifact. A revised paper and its predecessor remain distinct artifacts, even if they represent the same scholarly work. Optional work IDs and version relationships are explicit metadata assertions with an origin; Tampu does not infer them from similar names.

Registration accepts a local root. Admission recursively enumerates regular files within it without following symlinks. It records non-PDF exclusions, unreadable paths, enumeration failures, and changed-during-read files. Extension and PDF header both participate in validation; a misleading extension is reported. An unreadable subtree makes enumeration incomplete. A scan is an observation over a time interval, not a filesystem-wide atomic snapshot.

Read each admitted source into a temporary local file while hashing it. Check source stat information before and after the read; retry a detected change once and otherwise report it as unresolved admission. This is a best-effort concurrent-change detector, not a proof of source quiescence. Atomically install the captured bytes in the content-addressed store. Extraction always consumes those captured bytes, so its provenance remains valid even if the live source changes later.

A revision contains the source observation record, its exact admitted artifact membership, metadata assertions, and the selected projection ID and processing status for each artifact. The identity of a revision is opaque and immutable after publication. Reconciliation re-enumerates and rehashes sources, reuses unchanged content and matching extraction configurations, and stages a successor. At this corpus size a full scan is preferable to implementing watchers. Additions, removals, changes, and processing-status changes are reported separately.

A changed file at the same path establishes a source replacement, not proof that the two PDFs are versions of one paper. Removing a source path changes the next revision; it does not delete the captured artifact or rewrite an earlier revision. Correcting a title, publication date, or extraction result also creates a successor revision.

Publish only after the membership and processing records are complete and search visibility has been checked for the successfully indexed projections. Partial coverage can be published, but remains explicit. A failed scan or extractor never converts inaccessible content into a claim that it was absent. The current-revision pointer changes atomically after publication; readers continue using the preceding revision while a successor is staged.

## Extraction and evidence addresses

Start with a representative pilot of approximately twelve PDFs: short papers, multicolumn layouts, a long proceedings volume, and image-heavy or scanned pages where present. Compare Unstructured against page-preserving `pdftotext` output for page attribution, reading order, omitted material, runtime, and failures. Inspect actual output before choosing the extraction profile for the first published corpus revision.

Use an explicit Unstructured strategy and record it. The default pilot profile is `fast`; a separate `hi_res` profile can investigate documents whose text extraction is inadequate. Required OCR/model assets must be provisioned and versioned before a run, with no implicit network downloads during corpus processing. Unstructured supports distinct PDF strategies [2]; success of one strategy must not imply that another representation exists.

Preserve raw partitioned elements before retrieval chunking. Each normalized element includes artifact ID, projection ID, ordinal, original element ID, element type, text, one-based PDF page number when available, and the extractor's coordinates when available. Coordinates retain their coordinate system. Printed page labels are separate from PDF page positions. Normalization retains unknown fields in the raw output.

An evidence address is `(artifact_id, projection_id, element_ordinal, text_range)`. It never relies on an extractor element ID alone. Retrieval initially indexes individual text-bearing elements. Long elements are inspectable in bounded slices; offsets refer to the preserved normalized element text. A passage may be opened with neighboring elements on the same page. Page-less elements remain searchable but are explicitly marked as lacking page attribution. A proceedings PDF remains one artifact; a paper found within it is cited using its passages and pages.

Extraction and chunking are separate decisions. If chunking is added, chunks must refer back to original elements; Unstructured documents that consolidated chunks can lose metadata distinctions and provides original-element retention [3]. The PDF remains the source for checking text extraction.

Projection identity includes the source digest, extractor/profile versions, normalization version, and actual normalized-output digest. A recipe identifies reusable work; it does not guarantee deterministic output across reruns. Changing settings creates a new projection, and an explicitly requested rerun cannot overwrite an existing projection.

Record observed PDF page count, pages with extracted elements, zero-text pages, unattributed elements, failures, and elapsed extraction time. These measure extraction coverage, not semantic completeness. A page with some text is not certified as having every table, formula, figure, or qualification represented. Known extraction limitations are exposed as declared losses with their origin. No automatic LLM assertion certifies that all losses were found.

The first ingestion worker is sequential, with a configurable per-file timeout (initially 300 seconds) and container memory limit (initially 8 GiB). Timeouts, encrypted or malformed files, missing extraction dependencies, and resource failures produce per-artifact statuses. Other artifacts continue. There is no silent extractor fallback: running `pdftotext` instead produces a separately identified projection.

## State storage and service boundaries

Use an owner-configured local data directory, defaulting to `~/.local/share/tampu`, outside the repository. It holds content-addressed source PDFs, raw extraction output, and normalized projection files. This custody is intentionally limited to admitted artifacts and derived representations; it is not a general backup service. Automatic garbage collection is outside the prototype: stored source and projection revisions remain available until explicit operator maintenance.

ArangoDB stores the searchable normalized elements and structured records. The saved-journey collections are a deferred schema contract and are not created for the first MVP:

| Collection | Responsibility |
| --- | --- |
| `artifacts` | Content digests and immutable source-file properties |
| `collections`, `revisions` | Registered sources, revision manifests, publication state, and coverage |
| `memberships` | Revision-specific artifact, alias, metadata, and selected projection references |
| `projections`, `elements` | Extraction identity, status, text elements, and evidence addresses |
| `saved_journeys`, `saved_nodes`, `saved_edges`, `saved_results` | Deferred: explicitly preserved graphs and recorded candidate sets |

An ArangoSearch view indexes element text. Exact indexes cover identities and filter fields. Projection content is shared across revisions; there is no full copy of extracted text for every source scan. Large manifests and candidate sets use multiple records rather than an unbounded single database document.

Active journey state lives in the MCP server's memory. It contains queries, effective operations, complete candidate ID sets within a limit, recorded responses, and evidence handles. Initially none of it enters ArangoDB. Once the optional preservation feature exists, an explicit preserve call authorizes saving a checkpoint. An unpreserved journey ends with the server process or its configured expiry. The application refuses expired handles even if cleanup has not run yet. In the baseline treatment, result handles support pagination and evidence reads but do not expose a parent-path shortcut or service-held history; the consumer reconstructs search predicates from its own context. The path treatment exposes parent links and history over the same underlying retrieval behavior.

Use separate Python modules for admission/reconciliation, extraction adapters, revision publication, lens evaluation, journey state, and the MCP boundary. A small lens interface consumes a revision and a typed operation and returns candidates, coverage, ordering, and declared limitations. Do not introduce a generic database abstraction or plugin framework before a second implementation needs one.

## Lenses, counts, and composition

Initial lenses are `lexical/v1`, `metadata/v1`, and `temporal/v1`:

- Lexical search matches indexed element text using a declared analyzer. Expose explicit `any_terms`, `all_terms`, and `phrase` query modes. Their definitions refer to analyzer tokens, not literal character equality. `all_terms` applies within one element. Raw substring searching is not implied.
- Metadata filters cover artifact ID, known source alias, source-relative path prefix, explicit work ID, publication status, and metadata presence. Title and author assertions retain their origin. Filename-derived values remain distinguishable from curated bibliographic metadata.
- Temporal filters require a named field: observed time, captured source modification time, or asserted publication date. A copied file's modification time is not its publication date. Unknown values are excluded from range matches and counted as unknown; they are selectable with a missing-value filter. Date-only publication assertions retain date precision and are not converted into a fictitious exact time.

All lenses evaluate only membership and selected projections of the pinned revision. Lexical matches are grouped by artifact before counting and applying the response limit. The artifact score is the maximum BM25 score of its matching elements, with artifact ID as the tie-breaker. This choice and its limitations are declared: it favors a strong local passage and does not measure whole-artifact support. Retain the best evidence address for each hit. Large documents may yield many matching elements but remain one artifact candidate.

BM25 scores are navigation aids, not probabilities. Search-index statistics can change as other projections enter the index. Record the index generation and lens configuration with each executed node. New operations on an old revision keep its membership and projection constraints, but do not promise historical scores. Recorded-result replay below is how an earlier ordering is recovered.

Deferred composition contract: accept successful nodes from the same journey, revision, and compatible projection selection. Intersection, union, and difference operate on full materialized artifact sets, never just displayed samples. Preserve operand IDs and each lens's evidence. Composite sets use artifact-ID order; no blended score is invented. Difference means absence from an operand's candidate set under its predicate, not absence of a concept from a document. Cross-revision composition is rejected; the optional refresh operation reports changes explicitly.

For the prototype, cap successful materialized candidate sets at 10,000 artifacts and each database operation at 10 seconds by default. Exceeding either limit creates a recorded unsuccessful operation with a typed reason, not a truncated set masquerading as complete. An over-limit query may report a lower bound when observed; a timeout has an unknown count. The consumer can issue a narrower search from an earlier valid node. These limits are configurable and exposed by capability discovery.

## MCP interaction and bounded responses

The core exposes four tools. The early path experiment adds `navigate`; `preserve` is deferred. Schemas explain ordinary usage without loading a separate manual and contain only implemented actions. Baseline and path treatments advertise their own truthful capability profiles.

| Tool | Delivery stage and contract |
| --- | --- |
| `describe` | Core: collection summaries, capabilities, revisions, lenses, coverage, limits, and known omissions; cursors for longer lists |
| `search` | Core: start a journey with an intent, collection, revision, lens, query, and typed filters. Path experiment: additionally create a child of a supplied node |
| `inspect` | Core: page through a result set, read bounded artifact metadata, or open a cited element/page range from the node's revision |
| `navigate` | Path experiment: bounded history, recorded-result replay, and release. Refresh and composition actions are deferred |
| `finish` | Core: record a consumer-declared positive, bounded-negative, or unresolved finding with evidence, scope, rationale, and declared limitations; an explicit release option also frees the active journey |
| `preserve` | Deferred: save a journey and recorded results, returning a checkpoint handle for later inspection/navigation |

The first `search` requires a finding intent. A root search resolves an explicit revision or the latest published revision once. Later core searches accept the journey ID to keep the same intent and revision while supplying a new predicate; they do not need a parent-path shortcut. Without the path treatment, the consumer reconstructs that predicate from its conversation history. In the path treatment, a child search inherits the collection revision and effective filters; an omitted query inherits its parent's query, while an explicitly empty query clears it for metadata-only navigation. If composition is later implemented, its nodes have no single inherited query or filter; a child starts with an empty predicate over the composed candidate set unless it supplies one explicitly. Filter replacement and removal are explicit fields. Refinement intersects the parent's candidate set by default. An explicit `scope=revision` searches the pinned revision again, allowing a branch to broaden beyond earlier candidates. The response reports the effective predicate and scope. Branching is issuing different children from one parent; backtracking is choosing an earlier parent, with no destructive cursor update.

`inspect` can select only artifact IDs in the chosen node's set. To examine something outside it, broaden or create another search node. Each successful inspection records the exact evidence addresses and content slices delivered. Repeated reads and errors remain observable events, and successful inspections become immutable graph nodes. Navigation parameters accept result-producing node IDs or resolve an inspection to its originating result set; they never infer scope from whichever result happened to be read most recently.

Search defaults to two artifact hits, allows zero for a count-only observation, and has a maximum of twenty. Metadata and snippets are bounded separately from full evidence. Default response budget is 8 KiB of serialized UTF-8 application JSON, with a configurable hard maximum of 32 KiB. MCP framing and tool schemas are outside this byte count and measured separately by the evaluation harness. A byte limit is not advertised as a tokenizer-independent token limit.

Each successful result includes journey/node IDs, revision and projection-selection identity, effective lens/predicate, artifact count and count kind, returned count, selection/order policy, compact coverage, and a continuation cursor where applicable. Hits include artifact ID, bounded source aliases or title, one best passage address, page number when known, lens-specific score when applicable, and a short extract.

Available facets are artifact counts by source group, asserted publication year, and processing status. Return at most five values per requested facet with unknown and omitted-value counts; full facet enumeration is separately paged. Source groups are explicit manifest tags, not assumed from a flat directory's filenames.

Reserve space for scope, coverage, errors, and omission declarations before packing optional facets or hits. If they will not fit, return a bounded `budget_too_small` error with the minimum required size. Do not byte-truncate JSON or omit the omission record. Long evidence is sliced at Unicode character boundaries with stable offsets and a continuation; item limits may be underfilled to respect the byte budget. Opaque cursors bind to a stored node and position, preventing later corpus changes from altering pagination.

Distinguish response-budget omissions, incomplete processing, representational limitations, and unknown coverage. Each declaration names its origin and scope. This does not purport to enumerate all information lost by a representation. If an omission list itself is large, return its count and a paged detail handle.

Errors include `unknown_collection`, `revision_not_ready`, `expired_journey`, `missing_evidence`, `incompatible_nodes`, `candidate_limit`, `query_timeout`, `budget_too_small`, and `storage_unavailable`. Errors do not become empty successful searches. Raw database/extractor exception text stays out of tool responses because it can contain paths, queries, or configuration.

## Early replay and deferred refresh/preservation

For the early path experiment, **replay means recorded-result replay**, identified as such by `describe`. It returns the original application response and its recorded rank order; it does not rerun a historical query. The founding document's broader historical re-execution capability remains unimplemented and is explicitly advertised as unavailable. Recorded result sets also permit inspection of previously unseen candidates and pinned passages while the active state exists, which is recorded as a new operation.

Core reconciliation can publish a new revision without implementing graph refresh. A consumer can start a new root search against that revision and compare observations using explicit revision IDs. The following refresh and preservation contracts are optional extensions, contingent on evidence or a concrete later-session/user need.

Refresh copies the selected node's effective operation to the latest published revision and creates new nodes. If the operation depends on parents or composition operands, recompute the dependency graph once per ancestor in topological order. Do not combine an old candidate set with a new revision. Map the refreshed graph back to the original nodes and return bounded counts/samples of added and removed artifact candidates. Refreshed ranking is a new observation.

A preserve operation saves the complete journey known at that moment, including nodes, edges, findings, original response envelopes, full bounded candidate sets, and projection references. Publish the saved checkpoint only after all backing records have been written and verified; an interrupted save cannot return a usable checkpoint handle. It is an immutable checkpoint. Work after that checkpoint is ephemeral until explicitly preserved again. Loading a saved checkpoint into a new process permits new children without modifying saved nodes. Explicitly saved records persist until owner deletion.

Core resource limits apply independently of these extensions: default active-journey expiry is 24 hours, with a 256 MiB aggregate process budget. At the budget boundary the service returns a typed capacity response identifying the supported release operation; it does not silently evict a live journey or advertise preservation before that feature exists. `finish(release=true)` supports release in the core, and `navigate` adds explicit release in the path treatment. Release discards the active in-memory journey, leaving any future saved checkpoint intact; it is measured as an operational event rather than a node in a graph that has been discarded. Without trace mode or preservation, a finished finding is not durably retained by the service.

Saved queries and excerpts are content-bearing retention authorized by that preserve call. If a saved source or projection is missing during inspection, report `missing_evidence`; never substitute current source bytes or a newer extraction. The existence of a saved journey does not guarantee that operator-deleted backing files can be reconstructed.

## Findings and observation

`finish` records the consumer's judgment. Positive findings require valid evidence handles from the journey. Unresolved findings require a reason such as missing coverage, exhausted budget, or insufficient support. Structural validation checks addresses and scope; it cannot certify that cited prose entails the consumer's statement.

For a machine-checkable bounded negative, require a successful zero-candidate node and record the exact predicate, lens, revision, and covered projection subset as the negative claim's scope. Even exhaustive lexical matching establishes only that the declared token/phrase predicate had no matches in that representation. It cannot certify that an idea is absent from the PDFs. Other consumer negative interpretations are retained as unverified rationale with an unresolved machine status. This prevents an empty result from silently becoming a service-endorsed semantic conclusion.

Operational events record operation type, opaque per-run journey identifiers, lens IDs, counts, elapsed time, response bytes, error category, and resource measurements available to the service. They omit query text, source paths, artifact IDs, snippets, and query hashes. Raw exceptions and default library logging must be checked for content leakage. Structural telemetry is still deployment-owner data, not asserted to be anonymous in every context.

Replayable experiment traces require explicit configuration. They may include prompts, queries, evidence, model settings, and outputs in an owner-chosen location. The harness records the actual consumer model, tool schema version, corpus revision, projection versions, and every returned byte/token measurement it can establish. Service observations and consumer self-reports remain distinguishable.

## Evaluation and completion criteria

Create a corpus manifest with hashes and source aliases, then add bibliographic IDs, acquisition URLs, publication status, and version/work assertions where supported. User-supplied publication status is an attributed assertion. Local files stay outside Git. A shareable manifest and extraction recipe define the dataset without requiring PDF redistribution. The conversational story can become another artifact later; transcript search stays the responsibility of llm-memory.

Use six diagnostic tasks before synthesis: locate a known passage; recover from misleading first results; distinguish byte duplicates from independent works; handle an extraction failure; demonstrate a bounded lexical negative without claiming semantic absence; and compare observations across an added, replaced, and removed artifact. A deterministic tiny fixture establishes expected membership, counts, and evidence addresses. Real documents establish extraction behavior and interface usability. The revision diagnostic uses explicit new root searches; it does not require recursive graph refresh.

### Early controlled comparisons

Keep the indexed projections, lexical retrieval, initial samples, model settings, task instructions, and available evidence reads matched. Give all consumers permission to abstain and access to the same answerable tasks. Separate three interventions instead of attributing a bundled improvement to every feature:

1. **Negative-scope information:** compare a successful empty result with and without explicit predicate/coverage information. Include a verified absent target, a present target, an alias/paraphrase case, and a target withheld by an extraction failure. Exact identifier/predicate absence in a completely controlled fixture can be scored mechanically. A claim that an idea is absent from a real PDF collection requires independently reviewed evidence and a rubric; removing one known paper does not establish that no other artifact answers the question. A processing gap should favor unresolved over an unjustified whole-corpus negative.
2. **Counts and coverage:** expose or hide these fields while keeping the displayed hits and other affordances fixed. Test counts and coverage separately before their combined treatment. Never fabricate counts or coverage for the control. Define the experimental response contracts and any scope hints common to both arms, so that counts cannot leak through an omission message or `describe`. Record the entire tool transcript. All non-evidence calls count toward cost, so extra metadata requests are not free.
3. **Path-holding:** compare the same iterative search interface with and without parent-based reuse, bounded history, and recorded-result replay. Counts, coverage, facets, evidence reads, and context policy remain the same. Ordinary pagination handles in the control do not expose path history. Use tasks with checked dead ends and an alternative route; include scripted diagnostic starts and natural starts as separate strata. Measure successful recovery, repeated predicates/reads, reconstructed-filter errors, total context, and latency. This intervention tests a minimal path affordance, not full composition or durable preservation.

One-shot lexical retrieval is an additional reference treatment, not the only baseline. The iterative control is deliberately comparable to llm-memory's useful search/read interaction. When embeddings are available, add the matched semantic baselines described in the capability section; do not relabel these lexical experiments as evidence against RAG as a category.

Pilot at most twenty tool calls and ten minutes per task, counting all calls rather than just `navigate`. Record total application response bytes, schema/framing cost where available, actual model tokens, time to finding, extraction/index/storage cost, and operational failures. These pilot budgets are settings to examine, not measured optimal limits. Keep context management identical between treatment arms and record compaction if the runtime performs it.

Then exercise the three exploratory tasks: detectable versus silent forgetting; distinctions lost by metrics/representations across subject areas; and qualifications or counterevidence that revise a preliminary finding. Build an evidence rubric from passages checked independently of the evaluated consumer, and keep annotations outside its searchable collection. Score whether the consumer found and used warranted evidence, including a warranted unresolved outcome; an interesting literature synthesis alone does not establish interface effectiveness.

### Failure diagnosis and evaluator roles

For a thin or unsuccessful finding, record separate evidence about corpus adequacy, task clarity, consumer reasoning, and interface behavior. A failed run can have several causes or remain unattributed. Check the manifest/extraction and independently known evidence; review ambiguous task wording; in a separate diagnostic run give the consumer verified passages directly; and compare its navigation under matched interfaces. Those interventions can narrow explanations, but a direct-evidence rescue alone does not prove that the interface caused the original failure. Preserve the scored failure and label rescue runs as diagnostics.

Track builder, task-author/adjudicator, and evaluation-consumer roles separately. Reading the design or inspecting target passages is appropriate builder work, but prior exposure to target answers, hidden labels, selected evidence, or treatment outcomes disqualifies that session from being a fresh held-out consumer. The public manifest or task prompt is not automatically contamination if it is an intended, equally available input; record its contents and exposure policy. Use new consumer sessions, held-out tasks, randomized treatment order, and recorded model/configuration identities. Fresh context cannot prove absence of pretraining exposure. Ordinary toolkit use and builder dogfooding remain useful and are labeled accordingly.

Report individual tasks and repeated runs, not just a single aggregate metric. More calls can be worthwhile if they discover a consequential qualification. Fewer tokens alone is not success. The service cannot measure distinctions that neither the rubric nor the investigator recognizes; this remains a declared evaluation limitation.

## Falsification and decisions after the pilot

Architectural commitments state how the service represents evidence; they do not establish that the interface benefits a consumer. Test the benefit claims and revise the implementation scope when they fail. A small or noisy null result is inconclusive unless the study can exclude the predeclared useful effect. Do not treat evidence of equivalence, evidence of harm, and insufficient evidence as the same result.

| Hypothesis and prediction | Observation counting against it | Consequence for Tampu |
| --- | --- | --- |
| Scoped negative information improves warranted stopping and reduces unsupported answers without increasing false negatives on present controls | Equal or worse claim calibration under matched conditions, with uncertainty narrow enough to exclude the predeclared useful effect; or apparent gains explained by indiscriminate abstention | Revise the interface/instructions and retest separately. If the effect remains absent, withdraw the consumer-benefit claim; internal correctness alone does not establish it. |
| Candidate counts/coverage improve finding decisions or lower total work at comparable quality | Consumers ignore or misuse the information, or any observed behavior change brings no quality/cost benefit under the recorded decision rule | Simplify default presentation or keep detailed information available on request; do not claim navigation benefit from field availability alone. Retain truthful coverage semantics. |
| External path state improves recovery from dead ends | No useful same-session improvement, or higher total cost without a compensating quality improvement | Do not build the full journey feature set by default. Test later-session/human-reader value separately if a concrete use case warrants it; absent either benefit, keep only minimal internal provenance in Tampu. |
| A particular optional journey feature benefits later sessions or human readers | Its intended users cannot recover evidence or resume work more effectively than with a simpler evidence export | Drop or simplify that feature in Tampu; preserve the lesson for Yanantin rather than making its broader ambitions an MVP dependency. |
| With a matched semantic provider, Tampu improves the specified finding tasks over the registered RAG baselines | No useful advantage, or improvement disappears against the capable iterative baseline or after matching budgets | Withdraw superiority for those conditions. Report any narrower interface effect and its limits. |
| Explicit revisions help consumers reason about change | Consumers conflate revisions or repeat stale claims as often as the control despite correct service state | Revise revision presentation and test again; immutable storage by itself has not demonstrated the desired consumer behavior. |

These are directional hypotheses and revision rules, not a completed experimental preregistration. Use development-only pilots to set a smallest useful effect, quality/cost trade-off, trial count, task strata, and uncertainty method. Before held-out scoring, write a separate protocol fixing those choices plus dataset/projection hashes, inclusion/exclusion rules, model settings, budgets, treatment contracts, abstention/scoring rubric, and stopping rules. Timestamp its commit before collecting scored outcomes. If the protocol changes afterward, preserve the earlier version and label the new analysis exploratory or collect new held-out data. OpenTimestamps records a commitment's existence; it does not by itself establish experimental independence or validity.

## MVP completion criteria

1. Every enumerated source has a recorded admission outcome; published lens coverage reconciles to admitted membership.
2. Successful hits are artifact-deduplicated, counts precede sample limits, and evidence resolves to pinned source/projection addresses.
3. Budgets, typed errors, unavailable evidence, and processing gaps remain visible. Default operation does not persist journey content.
4. The extraction pilot compares Unstructured with `pdftotext`, with the chosen primary profile and limitations recorded.
5. The six core diagnostic tasks have checked outcomes, and the negative-scope/counts pilots have been exercised with labeled observations.
6. A minimal path treatment preserves parent immutability and recorded replay and has been compared with context-based reconstruction before committing to the full journey machinery. Record the scope decision, including an inconclusive result where appropriate.
7. At least one real cross-topic task has been exercised, with evidence for any failure diagnosis distinguished from the consumer's self-report.
8. Capability discovery and documentation report what exists and what passed. Composition, recursive refresh, durable preservation, embeddings, and historical query re-execution are not required for this completion claim.

This establishes a functioning research prototype and early interface observations. It does not establish scale to millions of artifacts, superiority over RAG generally, or completeness of the real-world source collection. Useful empirical findings may be negative.

## Delivery sequence

1. Build one vertical path: capture a PDF, partition it, publish a revision, search through MCP, inspect a page-addressed passage, and record its scope. Include count/coverage and core `finish` semantics so the first consumer interaction can be evaluated.
2. Run controlled negative-scope and count/coverage pilots, including answerable controls and processing gaps. Add/reconcile a small successor revision and exercise explicit new-revision searches.
3. Add only the minimal in-memory path treatment and run the backtracking comparison. Record whether to retain, simplify, or investigate it further before implementing composition, recursive refresh, or durable preservation.
4. Finish the core diagnostics and one exploratory finding task. This is the first MVP boundary.
5. Prepare the semantic provider and matched RAG baselines using the explicit prerequisites above. Register and run a comparative protocol; the full journey extension is not a prerequisite.
6. Implement composition, recursive refresh, or preservation only against an identified consumer benefit or concrete downstream use case, with its own evaluation. These are separate delivery decisions rather than an automatic second half of the MVP.

Integrate documentation and relevant tests with each deliverable. Changes in scope must update capability discovery and the evaluation record rather than leaving proposed features looking implemented.

## References informing implementation choices

1. [ArangoSearch information retrieval and search visibility](https://docs.arango.ai/arangodb/stable/indexes-and-search/arangosearch/) and [view consistency](https://docs.arango.ai/arangodb/stable/indexes-and-search/arangosearch/arangosearch-views-reference/).
2. [Unstructured partitioning and PDF strategies](https://docs.unstructured.io/open-source/core-functionality/partitioning).
3. [Unstructured chunking and original elements](https://docs.unstructured.io/open-source/core-functionality/chunking).
4. [Qdrant search thresholds and filtering](https://qdrant.tech/documentation/search/search/).
5. [Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection](https://arxiv.org/abs/2310.11511).
6. [ArangoDB vector index capabilities and version requirements](https://docs.arango.ai/arangodb/3.12/indexes-and-search/indexing/working-with-indexes/vector-indexes/).

Local design evidence: `docs/tampu-founding-document.md`; `../llm-memory/llm_memory/search.py` and `mcp_server.py`; `../indaleko/semantic/collectors/unstructured/`; the current `tmp/research` inventory. These sources establish context and reuse opportunities, not validation of this proposed implementation.
