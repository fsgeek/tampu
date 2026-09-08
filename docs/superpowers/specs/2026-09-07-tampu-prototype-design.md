# Tampu initial prototype design

Date: 2026-09-07

Status: proposed design for review; no prototype implementation is claimed.

## Purpose and first finding experiment

Build a local service through which an AI can investigate a changing collection of PDFs using bounded observations, inspectable evidence, and revisitable finding journeys. Evaluate the AI's finding episode and the contribution of the interface. Tampu supplies evidence and scope; the consumer judges its significance.

The first research question is: **When does forgetting produce a detectable miss, and when does it silently change an answer?** Search across caching, memory management, retrieval, and the ayllu's papers. Find a small number of independent works, locate supporting passages, identify mechanisms and assumptions, and distinguish authors' claims from the consumer's analogy. An unresolved comparison is acceptable when the corpus does not supply the necessary evidence.

Companion tasks examine limitations of metrics and representations, recovery from misleading early results, and discovery of qualifications that change a preliminary finding. We are testing whether the interface helps an investigator revise an account as well as support it.

The initial local inventory contains 479 PDF paths, 473 distinct byte contents, and approximately 913.5 MiB of source files. These are observations made during design, not fixed dataset membership. The collection includes articles, books, proceedings, preprint versions, and submissions. For example, a proceedings PDF and a file named after a plagiarism paper have identical bytes. Filenames therefore cannot establish either work identity or independent corroboration.

## Tooling decisions and alternatives

**Use ArangoDB, the installed Unstructured container, Python 3.14, and an MCP stdio interface.** Use `python-arango` for database access and the existing llm-memory implementation as an interface reference. Tampu gets its own database and scoped credentials on the existing service. It does not add records or indexes to llm-memory's database.

ArangoDB already fits the local operation and offers document storage, graph edges, and ArangoSearch. Its full-text search supports filters and BM25 ranking; its eventual index visibility must be handled explicitly [1]. The deployment target is a single server. Connection, server version, supported search behavior, and the Python client are checked during implementation before ingestion. The design does not depend on a vector index or cluster transactions.

Alternatives considered:

| Approach | MVP benefit | Cost and decision |
| --- | --- | --- |
| ArangoDB plus local immutable files | Reuses existing operational knowledge; one database for metadata, retrieval, and preserved journeys | Requires a running service; selected |
| SQLite plus FTS5 and local files | Could make distribution self-contained | Introduces a different backend before demonstrating a finding benefit; deferred |
| Existing vector-oriented RAG stack | Could accelerate an embedding-based demonstration | Adds representation and integration choices before testing navigation; useful later as a comparison |

Reuse Unstructured's partitioning rather than implementing a document parser. Keep `pdftotext` as a separately named extraction baseline. No external extraction or embedding API is required. Pin the container by digest, not `latest`; the installed digest observed during design is `sha256:806726e3997d33bce9e32facd86c947b241101c58496f2774ad5f09f86e798bc`. Record the actual package versions and extraction settings in each run.

## Capability boundary

The first capability profile provides:

- One registered local PDF directory per collection; multiple explicit observed revisions.
- Lexical, exact metadata, and temporal lenses, with named versions and distinct coverage.
- Artifact-level candidate counts and samples; inspection down to a page and extracted element.
- Branching from any previous node, set composition, recorded-result replay, and refresh.
- Ephemeral journeys, explicit preservation, and consumer-declared findings.
- Structural operational measurements and an explicitly enabled research trace mode.

General semantic embeddings are the first extension, after the lexical prototype can complete a real finding episode. They are not silently included in the initial capability claim. We will not call the initial experiment a comparison with vector RAG until both treatments actually use the same embedding and projection configuration.

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

ArangoDB stores the searchable normalized elements and structured records:

| Collection | Responsibility |
| --- | --- |
| `artifacts` | Content digests and immutable source-file properties |
| `collections`, `revisions` | Registered sources, revision manifests, publication state, and coverage |
| `memberships` | Revision-specific artifact, alias, metadata, and selected projection references |
| `projections`, `elements` | Extraction identity, status, text elements, and evidence addresses |
| `saved_journeys`, `saved_nodes`, `saved_edges`, `saved_results` | Explicitly preserved graphs and recorded candidate sets |

An ArangoSearch view indexes element text. Exact indexes cover identities and filter fields. Projection content is shared across revisions; there is no full copy of extracted text for every source scan. Large manifests and candidate sets use multiple records rather than an unbounded single database document.

Active journey state lives in the MCP server's memory. It contains queries, effective operations, complete candidate ID sets within a limit, recorded responses, and evidence handles. It does not enter ArangoDB unless the consumer explicitly preserves it. This makes the default retention boundary concrete: an unpreserved journey ends with the server process or its configured expiry. The application refuses expired handles even if cleanup has not run yet.

Use separate Python modules for admission/reconciliation, extraction adapters, revision publication, lens evaluation, journey state, and the MCP boundary. A small lens interface consumes a revision and a typed operation and returns candidates, coverage, ordering, and declared limitations. Do not introduce a generic database abstraction or plugin framework before a second implementation needs one.

## Lenses, counts, and composition

Initial lenses are `lexical/v1`, `metadata/v1`, and `temporal/v1`:

- Lexical search matches indexed element text using a declared analyzer. Expose explicit `any_terms`, `all_terms`, and `phrase` query modes. Their definitions refer to analyzer tokens, not literal character equality. `all_terms` applies within one element. Raw substring searching is not implied.
- Metadata filters cover artifact ID, known source alias, source-relative path prefix, explicit work ID, publication status, and metadata presence. Title and author assertions retain their origin. Filename-derived values remain distinguishable from curated bibliographic metadata.
- Temporal filters require a named field: observed time, captured source modification time, or asserted publication date. A copied file's modification time is not its publication date. Unknown values are excluded from range matches and counted as unknown; they are selectable with a missing-value filter. Date-only publication assertions retain date precision and are not converted into a fictitious exact time.

All lenses evaluate only membership and selected projections of the pinned revision. Lexical matches are grouped by artifact before counting and applying the response limit. The artifact score is the maximum BM25 score of its matching elements, with artifact ID as the tie-breaker. This choice and its limitations are declared: it favors a strong local passage and does not measure whole-artifact support. Retain the best evidence address for each hit. Large documents may yield many matching elements but remain one artifact candidate.

BM25 scores are navigation aids, not probabilities. Search-index statistics can change as other projections enter the index. Record the index generation and lens configuration with each executed node. New operations on an old revision keep its membership and projection constraints, but do not promise historical scores. Recorded-result replay below is how an earlier ordering is recovered.

Composition accepts successful nodes from the same journey, revision, and compatible projection selection. Intersection, union, and difference operate on full materialized artifact sets, never just displayed samples. Preserve operand IDs and each lens's evidence. Composite sets use artifact-ID order; no blended score is invented. Difference means absence from an operand's candidate set under its predicate, not absence of a concept from a document. Cross-revision composition is rejected; refresh reports changes explicitly.

For the prototype, cap successful materialized candidate sets at 10,000 artifacts and each database operation at 10 seconds by default. Exceeding either limit creates a recorded unsuccessful operation with a typed reason, not a truncated set masquerading as complete. An over-limit query may report a lower bound when observed; a timeout has an unknown count. The consumer can issue a narrower search from an earlier valid node. These limits are configurable and exposed by capability discovery.

## MCP interaction and bounded responses

Expose six tools. Their schemas should explain ordinary usage without loading a separate manual.

| Tool | Contract |
| --- | --- |
| `describe` | List collection summaries or inspect one collection's capabilities, revisions, lenses, coverage, limits, and known omissions; use cursors for longer lists |
| `search` | Start a journey with an intent and collection, or create a child of a supplied node; provide lens, query, typed filters, and result limit |
| `inspect` | Page through an existing result set, read an artifact's bounded metadata, or open a cited element/page range; all material comes from the node's revision |
| `navigate` | Read bounded history, replay a recorded response, refresh an operation against the latest published revision, compose compatible candidate sets, or explicitly release an active journey |
| `finish` | Append a consumer-declared positive, bounded-negative, or unresolved finding with evidence, scope, rationale, and declared limitations |
| `preserve` | Explicitly save a journey and its recorded results; return a handle that later `navigate` or `inspect` calls can load |

The first `search` requires a finding intent. A child search inherits the collection revision and effective filters; an omitted query inherits its parent's query, while an explicitly empty query clears it for metadata-only navigation. A composition node has no single inherited query or filter; a child starts with an empty predicate over the composed candidate set unless it supplies one explicitly. Filter replacement and removal are explicit fields. Refinement intersects the parent's candidate set by default. An explicit `scope=revision` searches the pinned revision again, allowing a branch to broaden beyond earlier candidates. The response reports the effective predicate and scope. Branching is simply issuing different children from one parent; backtracking is choosing an earlier parent, with no destructive cursor update.

`inspect` can select only artifact IDs in the chosen node's set. To examine something outside it, broaden or create another search node. Each successful inspection records the exact evidence addresses and content slices delivered. Repeated reads and errors remain observable events, and successful inspections become immutable graph nodes. Navigation parameters accept result-producing node IDs or resolve an inspection to its originating result set; they never infer scope from whichever result happened to be read most recently.

Search defaults to two artifact hits, allows zero for a count-only observation, and has a maximum of twenty. Metadata and snippets are bounded separately from full evidence. Default response budget is 8 KiB of serialized UTF-8 application JSON, with a configurable hard maximum of 32 KiB. MCP framing and tool schemas are outside this byte count and measured separately by the evaluation harness. A byte limit is not advertised as a tokenizer-independent token limit.

Each successful result includes journey/node IDs, revision and projection-selection identity, effective lens/predicate, artifact count and count kind, returned count, selection/order policy, compact coverage, and a continuation cursor where applicable. Hits include artifact ID, bounded source aliases or title, one best passage address, page number when known, lens-specific score when applicable, and a short extract.

Available facets are artifact counts by source group, asserted publication year, and processing status. Return at most five values per requested facet with unknown and omitted-value counts; full facet enumeration is separately paged. Source groups are explicit manifest tags, not assumed from a flat directory's filenames.

Reserve space for scope, coverage, errors, and omission declarations before packing optional facets or hits. If they will not fit, return a bounded `budget_too_small` error with the minimum required size. Do not byte-truncate JSON or omit the omission record. Long evidence is sliced at Unicode character boundaries with stable offsets and a continuation; item limits may be underfilled to respect the byte budget. Opaque cursors bind to a stored node and position, preventing later corpus changes from altering pagination.

Distinguish response-budget omissions, incomplete processing, representational limitations, and unknown coverage. Each declaration names its origin and scope. This does not purport to enumerate all information lost by a representation. If an omission list itself is large, return its count and a paged detail handle.

Errors include `unknown_collection`, `revision_not_ready`, `expired_journey`, `missing_evidence`, `incompatible_nodes`, `candidate_limit`, `query_timeout`, `budget_too_small`, and `storage_unavailable`. Errors do not become empty successful searches. Raw database/extractor exception text stays out of tool responses because it can contain paths, queries, or configuration.

## Replay, refresh, and preservation

For the MVP, **replay means recorded-result replay**, identified as such by `describe`. It returns the original application response and its recorded rank order; it does not rerun a historical query. The founding document's broader historical re-execution capability remains unimplemented and is explicitly advertised as unavailable. Recorded result sets also permit inspection of previously unseen candidates and preserved passages, which is recorded as a new operation.

Refresh copies the selected node's effective operation to the latest published revision and creates new nodes. If the operation depends on parents or composition operands, recompute the dependency graph once per ancestor in topological order. Do not combine an old candidate set with a new revision. Map the refreshed graph back to the original nodes and return bounded counts/samples of added and removed artifact candidates. Refreshed ranking is a new observation.

A preserve operation saves the complete journey known at that moment, including nodes, edges, findings, original response envelopes, full bounded candidate sets, and projection references. Publish the saved checkpoint only after all backing records have been written and verified; an interrupted save cannot return a usable checkpoint handle. It is an immutable checkpoint. Work after that checkpoint is ephemeral until explicitly preserved again. Loading a saved checkpoint into a new process permits new children without modifying saved nodes. Explicitly saved records persist until owner deletion; default active-journey expiry is 24 hours, with a 256 MiB aggregate process budget. At the budget boundary the service asks the consumer to preserve/release state through a typed capacity response; it does not silently evict a live journey. Explicit release discards only the active in-memory journey, leaving any saved checkpoint intact; it is measured as an operational event rather than a node in a graph that has been discarded.

Saved queries and excerpts are content-bearing retention authorized by that preserve call. If a saved source or projection is missing during inspection, report `missing_evidence`; never substitute current source bytes or a newer extraction. The existence of a saved journey does not guarantee that operator-deleted backing files can be reconstructed.

## Findings and observation

`finish` records the consumer's judgment. Positive findings require valid evidence handles from the journey. Unresolved findings require a reason such as missing coverage, exhausted budget, or insufficient support. Structural validation checks addresses and scope; it cannot certify that cited prose entails the consumer's statement.

For a machine-checkable bounded negative, require a successful zero-candidate node and record the exact predicate, lens, revision, and covered projection subset as the negative claim's scope. Even exhaustive lexical matching establishes only that the declared token/phrase predicate had no matches in that representation. It cannot certify that an idea is absent from the PDFs. Other consumer negative interpretations are retained as unverified rationale with an unresolved machine status. This prevents an empty result from silently becoming a service-endorsed semantic conclusion.

Operational events record operation type, opaque per-run journey identifiers, lens IDs, counts, elapsed time, response bytes, error category, and resource measurements available to the service. They omit query text, source paths, artifact IDs, snippets, and query hashes. Raw exceptions and default library logging must be checked for content leakage. Structural telemetry is still deployment-owner data, not asserted to be anonymous in every context.

Replayable experiment traces require explicit configuration. They may include prompts, queries, evidence, model settings, and outputs in an owner-chosen location. The harness records the actual consumer model, tool schema version, corpus revision, projection versions, and every returned byte/token measurement it can establish. Service observations and consumer self-reports remain distinguishable.

## Evaluation and completion criteria

Create a corpus manifest with hashes and source aliases, then add bibliographic IDs, acquisition URLs, publication status, and version/work assertions where supported. User-supplied publication status is an attributed assertion. Local files stay outside Git. A shareable manifest and extraction recipe define the dataset without requiring PDF redistribution. The conversational story can become another artifact later; transcript search stays the responsibility of llm-memory.

Use six diagnostic tasks before synthesis: locate a known passage; recover from misleading first results; distinguish byte duplicates from independent works; handle an extraction failure; demonstrate a bounded lexical negative without claiming semantic absence; and revisit/refresh across an added, replaced, and removed artifact. A deterministic tiny fixture establishes expected membership, counts, and evidence addresses. Real documents establish extraction behavior and interface usability.

Then run three exploratory questions: detectable versus silent forgetting; distinctions lost by metrics/representations across subject areas; and qualifications or counterevidence that revise a preliminary finding. Build an evidence rubric from passages checked independently of the evaluated consumer. Keep those annotations outside its searchable collection. The author familiarity and prior exposure present in this founding conversation must be recorded; use fresh sessions for comparisons.

Compare three treatments with the same indexed projections and consumer model: one-shot lexical ranked retrieval; iterative lexical search with bounded reads and counts; and the full Tampu interface including journeys, facets, and composition. The second is a deliberately strong llm-memory-like baseline. Separately remove counts/coverage to investigate their contribution. Report exploratory trials as exploratory; choose and record budgets before scored runs. An initial pilot uses at most twenty navigation calls and ten minutes per task, and records total returned bytes and actual model token usage rather than presuming that two results are always cheap.

Measure grounded finding quality, unsupported claims, corrections prompted by discovered evidence, repeated searches/reads, abandoned branches, context consumed, time to finding, and extraction/index/storage costs. Report individual tasks and repeated runs, not just a single aggregate metric. More calls can be worthwhile if they discover a consequential qualification. Fewer tokens alone is not success. The service cannot measure invisible distinctions that neither the rubric nor the investigator recognizes; this is a declared evaluation limitation.

Prototype completion requires:

1. Every enumerated source has a recorded admission outcome; published lens coverage reconciles to admitted membership.
2. Successful hits are artifact-deduplicated, counts precede sample limits, and evidence resolves to pinned source/projection addresses.
3. Branches do not mutate ancestors; composition uses complete compatible candidate sets; replay reproduces recorded responses; refresh uses the new revision consistently.
4. Budgets, errors, unavailable evidence, and processing gaps remain visible. Default operation does not persist journey content.
5. Both extraction profiles can be compared on the pilot, with the chosen primary profile and limitations recorded.
6. The six diagnostic tasks have checked outcomes, and at least one real cross-topic finding journey has been exercised with a recorded evaluation.
7. Capability discovery and project documentation describe what actually passed, including absent semantic retrieval and historical re-execution.

This establishes a functioning research prototype. It does not establish scale to millions of artifacts, superiority over RAG generally, or completeness of the real-world source collection.

## Delivery sequence

Implement one vertical path first: capture a PDF, partition it, publish a revision, search it through MCP, inspect a page-addressed passage, and record its scope. Then add immutable journeys and composition, recorded replay and explicit preservation, reconciliation and refresh, and the diagnostic/evaluation workflow. Integrate documentation and relevant tests with each deliverable. Only after this path works should an embedding lens be added as an extension experiment using unchanged artifact and journey concepts.

## References informing implementation choices

1. [ArangoSearch information retrieval and search visibility](https://docs.arango.ai/arangodb/stable/indexes-and-search/arangosearch/) and [view consistency](https://docs.arango.ai/arangodb/stable/indexes-and-search/arangosearch/arangosearch-views-reference/).
2. [Unstructured partitioning and PDF strategies](https://docs.unstructured.io/open-source/core-functionality/partitioning).
3. [Unstructured chunking and original elements](https://docs.unstructured.io/open-source/core-functionality/chunking).

Local design evidence: `docs/tampu-founding-document.md`; `../llm-memory/llm_memory/search.py` and `mcp_server.py`; `../indaleko/semantic/collectors/unstructured/`; the current `tmp/research` inventory. These sources establish context and reuse opportunities, not validation of this proposed implementation.
