# Tampu

**Epistemic wayfinding infrastructure for AI working with a bounded collection of artifacts.**

> "Perhaps that you're searching far too much? That in all that searching, you don't find the time for finding?"
>
> — Hermann Hesse, *Siddhartha*

Search is a tool. Finding is a result. Most retrieval systems provide the first
and are assumed to deliver the second.

*Tampu* is a Quechua word for a waystation — a place on a road where a traveller
stops, takes stock, and decides where to go next. Not a destination, and not the
whole journey.

## Status

**Design stage. No implementation exists yet.**

What is in this repository today: a founding document, a prototype design, and an
adversarial review exchange between two AI systems that produced substantive
corrections to both. No code has been written, no corpus ingested, no experiment
run. The next deliverable is an experiment protocol, not a release.

This README describes what Tampu is *for*. It does not describe working software.

## The problem

Retrieval-augmented generation collapses several distinct activities into one
operation: a query is embedded, nearby chunks are ranked, some fixed number are
placed in a context window, and a model is expected to answer.

This demonstrates well. It also tends to fail as the corpus grows, the
terminology becomes specialized, the relevant relationship crosses artifacts, or
plausibly-related material obscures rather than aids the model's reasoning.

The deeper issue is what the interface cannot say. Ask a typical retrieval system
for something that is not in the collection, and it returns the nearest
neighbours anyway — ranked, confident, and indistinguishable from a real hit. The
model receives no signal that it is looking at the best of a bad set. It has no
way to learn that the query matched 3,000 candidates rather than 3, that a lens
covered only part of the collection, or that eleven documents failed to process.

The system knows all of this. It just does not say it.

## The premise

> Retrieval is not merely ranking. Finding is a navigational process through an
> artifact space.

Tampu is built on a handful of commitments that follow from that:

**Finding is a journey, not a query.** Real investigation involves trying a broad
term, sampling results, discovering the set is far larger or smaller than
expected, and using something found in one result to decide where to look next.
It involves dead ends, revised language, and returning to earlier points. These
are not interface failures — they are ordinary wayfinding. Tampu models the
process as an immutable graph, so an AI can branch and backtrack without
reconstructing its path from memory.

**Absence is a finding.** Determining that something is *not* in a collection can
be as valuable as locating it. Tampu distinguishes *found*, *not found within a
defined scope*, and *unresolved* — and refuses to let an empty result silently
become a claim of absence. An exhaustive lexical index can support "this token
does not appear." An approximate semantic index supports only "no candidate was
identified under this representation and threshold." Those are different
statements and Tampu reports them differently.

**Results carry their own limits.** A bounded sample is returned with the total
number of matching candidates, the collection revision, the lenses used, coverage,
and known processing failures. The AI can then decide to inspect, narrow, broaden,
change lenses, backtrack, or stop — rather than reasoning from an unmarked
fragment.

**One representation is not enough.** An embedding model, chunking policy, and
similarity function together act as an undeclared ontology: they impose a semantic
geometry without stating which concepts it preserves. Tampu lets artifacts be
viewed through multiple named, versioned lenses — lexical, temporal, domain-
specific embeddings, formal taxonomies, citation or provenance relationships — and
keeps their disagreements visible instead of blending incompatible scores into one
ranking whose meaning cannot be recovered.

**The artifact is primary.** Chunks, embeddings, summaries, and extracted entities
are derived, versioned, and rebuildable. A projection may help you find a
document; it does not replace it or become an authoritative account of what it
says.

**Collections are bounded, and the boundary is honest.** A collection is bounded
because membership is meaningful, not because it is complete. Ingestion produces
an observation record of what was actually encountered — admitted, excluded,
unreadable, partially processed — establishing the scope of Tampu's observation
without pretending the source contained everything it should have.

## Who this is for

Tampu is infrastructure for an AI entity investigating a specific, bounded body
of material: papers gathered while pursuing a question, documents produced across
several projects, source material assembled for a task, the contents of an
archive.

It is not for searching the world. It is for finding something grounded in *this*
collection — the paper that introduced an idea, the three documents using one
concept under different names, or the absence of an expected artifact from the
material available.

## What Tampu is not

- **Not a conversational memory system.** [qhaway](https://github.com/fsgeek/qhaway)
  and llm-memory address accumulated model interactions. Tampu concerns artifacts
  selected for a task or archive.
- **Not an ontology-authoring environment.** It can use, expose, compare, and
  compose ontological lenses supplied by others. It does not build them.
- **Not a storage, sync, or backup platform.** It owns artifact admission,
  identity, and processing status where those are needed for honest retrieval. It
  may refer to artifacts held elsewhere.
- **Not an answer engine.** An AI may use what it finds to construct an answer.
  Tampu's job is to make the path and the grounding inspectable.

## Method

Every deployment is expected to publish a **capability profile** separating what
it can do from what has been shown to work: current collection scope on one side;
on the other, per-mechanism evaluation status defaulting to `not_tested` and
changeable only with a linked result. Adding documents updates the operational
counts. It does not enlarge the evidence.

The same discipline applies to this repository. Commits are signed and stamped
with [OpenTimestamps](https://opentimestamps.org/), anchoring each to the Bitcoin
blockchain — so design commitments and falsification criteria are demonstrably
recorded *before* results exist, not adjusted afterward. Verifying an anchor
against the chain requires a Bitcoin node; without one, the calendar servers'
attestation is taken on trust.

Design proceeds through adversarial review between AI systems, with disagreements,
errors, and corrections committed to the record rather than resolved silently. The
review exchange in [`docs/superpowers/specs/`](docs/superpowers/specs/) includes
claims that did not survive scrutiny, and who refuted them.

## Repository

| Path | Contents |
| --- | --- |
| [`docs/tampu-founding-document.md`](docs/tampu-founding-document.md) | The architectural argument and its commitments |
| [`docs/superpowers/specs/`](docs/superpowers/specs/) | Prototype design, review, response, and dispositions |
| `scripts/` | OpenTimestamps hooks for the commit record |
| `timestamps/` | Pending and Bitcoin-anchored proofs |

Start with the founding document.

## Origins

Tampu draws on [Indaleko](https://github.com/fsgeek/indaleko), which explored
whether storage metadata and activity context could improve how people find their
own information, and on [Yanantin](https://github.com/fsgeek/yanantin), which
extends that ambition to unifying human and AI information across storage and
memory tiers.

Tampu is deliberately smaller than either. It is a bounded example through which
those ideas can be tested, shared, criticized, and improved — a waystation, not
the road.

## License

[Apache License 2.0](LICENSE). Chosen over MIT — the ayllu's usual choice for a
service this size — for its patent grant: Tampu proposes a retrieval architecture
and asks others to build on it, in a field where patents are dense and copyright,
here, is weak.

Substantial portions of this repository were generated by AI systems and may not
be copyrightable in the United States. [`NOTICE`](NOTICE) states what is
protected, what is uncertain, and how to determine authorship from the commit
record rather than taking the question on trust.
