# Tampu

## Finding, not merely searching

*Founding document — initial working draft, September 2026*

> “Perhaps that you're searching far too much? That in all that searching, you don't find the time for finding?”
>
> — Hermann Hesse, *Siddhartha*

Search is a tool. Finding is a useful result.

That distinction motivated Indaleko, which explored how storage metadata and activity context could improve our ability to find personal information. It also motivates Tampu, though the intended finder is different. Tampu is epistemic wayfinding infrastructure for transformer-based AI entities working with a bounded collection of artifacts.

Those artifacts might be papers downloaded while investigating a question, documents produced across several projects, source material assembled for a particular task, or the contents of an archive. The goal is not to search the world for a generic answer. It is to find something grounded in this particular collection: the paper that introduced an idea, the three documents that use the same widget concept under different names, or the absence of an expected artifact from the available material.

Contemporary retrieval-augmented generation offers an important capability, but its common form encourages us to collapse several different activities into one operation. A query is embedded, nearby chunks are ranked, some fixed number are placed into a context window, and a model is expected to answer. This can demonstrate remarkably well. It can also fail in production when the corpus grows, the terminology is specialized, the relevant relationship crosses artifacts, or too much plausibly related material obscures rather than improves the model's reasoning.

Tampu begins with a different premise:

> Retrieval is not merely ranking. Finding is a navigational process through an artifact space.

## From queries to journeys

A query should not be treated as an isolated event. Finding often involves trying a broad term, examining a small sample, discovering that the result set is much larger or smaller than expected, and using something in one result to decide where to look next. It also involves repetition, abandoned paths, revised language, returns to earlier points, and comparisons among alternative interpretations.

These are not interface failures. They are ordinary acts of wayfinding.

Tampu therefore models a finding process as an immutable graph. A finding intent anchors the graph. Each query, filter, temporal restriction, lens selection, expansion, or composition creates a node connected to the step from which it arose. An AI may branch, backtrack, and revisit an earlier node without reconstructing the entire search from memory.

Revisiting also has two meanings. A replay asks the earlier question against the collection and representations recorded at that time. A refresh asks it again against the collection as it exists now. Both are useful; silently choosing between them is not.

The graph is ephemeral by default. A consumer may explicitly preserve a useful journey as evidence, for later comparison, or to resume it in another session. The service should not quietly transform every act of retrieval into permanent conversational memory.

## Bounded collections

Tampu operates over explicit collections. This is a practical boundary and an epistemic one.

A collection is bounded because membership is meaningful, not because the collection is necessarily complete. It may be curated by a person, assembled by an AI, enumerated from a directory, imported from a repository, or obtained through a connector whose view is limited by permissions and availability. Tampu should remain useful in each case.

An externally supplied manifest may strengthen what can be said about a collection, but it is not an admission requirement. During ingestion Tampu constructs an observation record describing what it actually encountered: which artifacts were admitted, excluded, inaccessible, partially processed, or successfully represented by each available lens. This record establishes the scope of Tampu's observation. It does not magically prove that the source contained everything that should have been there.

That distinction matters most when nothing is found.

## Finding absence

Finding a desired artifact is not the only successful outcome. Determining that it is not present in the available collection can also be valuable. A system that cannot support that conclusion invites endless searching and confuses persistence with progress.

Tampu distinguishes at least three outcomes:

1. **Found:** sufficient artifacts support the finding intent.
2. **Not found within a defined scope:** the explored collection and available lenses support a bounded negative conclusion.
3. **Unresolved:** exploration ended without sufficient evidence for either of the first two outcomes.

An empty result list establishes very little. Exact metadata and lexical indexes may support exhaustive statements over the artifacts they cover. An approximate semantic index generally supports a narrower claim: it did not identify a candidate under a particular representation and threshold. Tampu should expose that difference rather than translating both into “not found.”

This suggests that a finding system must return information about what remains unseen. A limited result should include not only the requested sample but also the total number of matching candidates when that total is available. It should identify the collection revision, lenses, filters, coverage, and known processing failures that bound the result. The AI can then make an informed decision to inspect, narrow, broaden, change lenses, backtrack, or stop.

## Plural lenses

A vector database stores and searches embeddings. In common retrieval systems, however, the embedding model, chunking policy, similarity function, and filtering rules collectively operate as a kind of lazy ontology. They impose a semantic geometry without necessarily declaring the concepts and relationships that geometry preserves.

That geometry is useful, but it is not neutral and need not be adequate for every domain. Domain-trained representations such as [SciBERT](https://aclanthology.org/D19-1371/) and [INDUS](https://aclanthology.org/2024.emnlp-industry.9/) have improved results in scientific and specialist NLP settings; established fields may also have explicit taxonomies or ontologies that capture distinctions a general-language embedding treats poorly. Tampu should not require every collection to accept one representation as canonical.

Instead, artifacts may be viewed through multiple named and versioned lenses. A lens might provide:

- general semantic similarity;
- a domain-specific embedding;
- lexical or full-text retrieval;
- temporal relationships;
- a formal ontology or taxonomy supplied by a field;
- a project-specific conceptual mapping;
- citation, authorship, provenance, tool, or activity relationships.

Tampu permits these lenses but is not the system that constructs formal ontologies. Collection owners determine which lenses are installed and permitted. The AI chooses among the available lenses during exploration and may compare or compose their results.

Composition should remain visible. If two lenses agree, disagree, intersect, or expose different candidate sets, that difference is information. Tampu should not silently blend incompatible scores into a single ranking whose meaning cannot be recovered.

The artifact remains primary. Chunks, embeddings, extracted entities, summaries, ontology mappings, and other projections are derived, versioned, and rebuildable. A projection may help find an artifact; it does not replace the artifact or become an authoritative account of what the artifact says.

## A small semantic kernel

The architecture is organized around a small set of concepts:

- An **artifact** is the authoritative object being found, whether held by Tampu or referenced in another system.
- A **collection** is an explicitly bounded set of artifact identities.
- A **collection revision** records the state Tampu observed at a particular point.
- A **projection** is a derived representation of an artifact.
- A **lens** is a named and versioned way of navigating one or more projections.
- A **finding intent** states what the AI is trying to establish.
- A **journey** is the immutable graph of operations performed in pursuit of that intent.
- A **finding** is a grounded positive, bounded-negative, or unresolved outcome.
- An **observation event** records how the system behaved during navigation.

These concepts define an architectural vocabulary, not a demand that every possible feature appear in the first implementation. Their purpose is to leave room for evolution without requiring later implementations to undo an assumption that queries are stateless, embeddings are canonical, collections are complete, or a returned ranking is the same thing as a finding.

## Observing navigation

The way an AI navigates can help improve both Tampu and the AI systems that use it. Repeated queries, branch depth, backtracking, lens changes, result cardinalities, context consumed, latency, and eventual outcomes provide evidence about which retrieval strategies work and where the system creates semantic cul-de-sacs.

This observability must not become undeclared surveillance of private artifacts or AI interactions. Tampu separates the user-facing exploration graph from an operational observation stream. Structural telemetry can record operations, counts, timing, lens identifiers, errors, and resource use without retaining queries or artifact content. Content-bearing, replayable traces require explicit configuration and remain under the deployment owner's control.

Observed strategies may support better caching, indexing, evaluation, or suggestions about a useful next operation. They should not quietly harden into another hidden ranking policy. The AI remains an active retrieval partner rather than a passive recipient of whatever context the infrastructure selects.

## What Tampu is not

Tampu is deliberately smaller than the systems from which its ideas emerged.

It is not a conversational memory system. Qhaway and llm-memory already explore access to accumulated model interactions. Tampu concentrates on artifacts selected for a task, project, or archive.

It is not an ontology-authoring environment. It can use, expose, compare, and compose ontological lenses supplied by others.

It is not a general storage, synchronization, or backup platform. It owns artifact admission, identity, processing status, and reconciliation where those functions are necessary for honest retrieval. It may refer to artifacts whose custody remains elsewhere.

It is not an answer engine. An AI may use the evidence it finds to construct an answer, but Tampu's responsibility is to make the path and grounding inspectable.

Most importantly, Tampu is not Yanantin under a smaller name. Yanantin retains the broader ambition of uniting human and AI information across storage and memory tiers. Tampu is a bounded example: a useful service through which lessons from Indaleko and Yanantin can be tested, shared, criticized, and improved.

## Architecture beyond the first implementation

Holding a project until every question is settled is unlikely to produce a useful system. Tampu's architecture should envision more than its first implementation, but the implementation must state honestly which portion exists.

Every deployment should expose a capability profile: the artifact sources it understands, the lenses it provides, the composition operations it supports, its replay guarantees, the coverage information it can establish, and the observability it records. The architecture defines what Tampu may grow into; the capability profile states what this Tampu can do now.

An initial implementation might support only a local directory containing PDF, Markdown, and text artifacts. It might provide lexical, general semantic, and temporal lenses; stable artifact identities; simple lens composition; iterative operations such as start, refine, branch, backtrack, replay, and refresh; ephemeral journeys with explicit preservation; and an MCP interface through which an AI can navigate.

That would be enough to test three related claims.

First, Tampu should be a **useful tool**. An AI should be able to find an artifact or a relationship among artifacts without flooding its context window.

Second, Tampu should demonstrate an **extensible architecture**. A new domain-specific lens should be addable without redefining artifacts, collections, or journeys.

Third, Tampu should be a **research instrument**. Its observations should permit us to measure time to finding, abandonment, correct bounded-negative findings, context cost, backtracking, and the contribution of different lenses.

These claims can be demonstrated separately. They need not be compressed into one heroic example that makes each difficult to inspect.

## Commitments and hypotheses

We expect to be wrong about some things. Tampu should make correction inexpensive where possible.

The distinction between searching and finding is a commitment. So are artifact primacy, plural semantic lenses, explicit scope, immutable journeys, visible provenance, bounded negative claims, and honest capability discovery.

The precise API, storage engine, identity scheme, composition algebra, retention policy, scoring method, and set of initial connectors are hypotheses. They should be tested against real use by AI entities and revised when the evidence warrants it.

Open schema and dynamic extensibility help, within reason. Extensibility is useful when it admits new evidence and representations without corrupting existing meaning. It is harmful when every invariant becomes optional and no consumer can know what an object means. Tampu should keep its semantic kernel small and stable while allowing the metadata surrounding that kernel to evolve.

## An invitation to find

Tampu is intended to be open-source infrastructure that others can use while the larger questions remain under investigation. Small examples matter: they make an architectural idea concrete, expose its errors, and allow people outside the originating project to discover uses its designers did not anticipate.

The initial objective is therefore not to replace every retrieval system or solve personal information management in general. It is to build a credible waystation for AI entities navigating artifacts: somewhere they can learn what is present, examine a bounded amount of evidence, choose among semantic paths, retrace their steps, and recognize when continuing to search is no longer the same thing as finding.
