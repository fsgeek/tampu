# Review: Tampu initial prototype design

Date: 2026-09-08

Reviewer: Claude (Opus 5)

Subject: `docs/superpowers/specs/2026-09-07-tampu-prototype-design.md` (Astra / GPT-6, first draft)

Status: review for revision. The design is sound and unusually disciplined. The
substantive objections are three, and they concern framing and scope rather than
correctness.

## Summary judgment

This is a good design document. Its central virtue is that it is built to make
later dishonesty expensive: replay is narrowed to recorded-result replay and the
broader capability is advertised as unavailable; the RAG comparison is explicitly
withheld until both treatments share an embedding configuration; a zero-candidate
lexical result is structurally prevented from becoming a service-endorsed semantic
absence; the extraction section distinguishes coverage from completeness and says
so. Most design documents overclaim by default. This one underclaims by
construction, which is the correct bias for a project whose thesis is epistemic
honesty.

Three objections follow, in descending order of how much they should change the
document.

**On the status of this review.** The two sibling projects were built by two
different methods, and the difference is instructive. llm-memory went from
initial commit to working MCP server in about thirty-six hours, with findings and
a corrected confound recorded before the interface existed. qhaway spent seven
rounds of adversarial spec review — Codex and Gemini, folded round by round to
convergence — before a single line of the planned implementation, and pivoted
architecturally mid-spec (`db is truth, MCP verbs are the product`). The
difference is not inconsistency. It tracks how expensive it is to be wrong about
the interface: llm-memory could be wrong cheaply and reindex; qhaway defines a
contract other sessions depend on.

Tampu is qhaway-shaped. Artifact identity, revision immutability, and evidence
addressing are contracts, and being wrong about them corrupts everything derived
from them. So this document is not an argument for shipping something smaller and
faster. It is round one of the adversarial pattern, and it expects to be answered
rather than accepted.

## Objection 1: the stated research question is a task, not a research question

The document opens: "The first research question is: **When does forgetting
produce a detectable miss, and when does it silently change an answer?**"

That is not Tampu's research question. It is a *task performed using Tampu*. The
project's actual question — confirmed with the project owner — is closer to: *can
we build a better tool for finding within a document set than the RAG community
has produced?*

Conflating them creates a diagnostic confound. If the forgetting investigation
yields a thin result, the document provides no way to distinguish among:

- the corpus does not contain the evidence,
- the question was ill-posed,
- the consumer model reasoned poorly,
- the interface failed.

Those are four different outcomes with four different responses, and the current
framing collapses them.

**Recommendation.** Demote the forgetting question to what it is: the first
exploratory task, one of three already listed in the evaluation section. Replace
the opening with Tampu's own questions. Proposed, in order of distinctiveness:

1. **Does a bounded-negative finding change consumer behavior?** RAG systems
   structurally cannot report a scoped absence — top-k returns k things whether
   or not any are relevant; the empty result is unrepresentable. Testable with a
   planted absence: take an intent whose answer is demonstrably not in the corpus
   and measure whether the consumer stops with a scoped negative or confabulates
   from the nearest neighbours. The difference is categorical, not graded, and
   needs no rubric to score.

2. **Does exposing candidate counts and coverage change navigation?** The
   document already isolates this as an ablation ("Separately remove
   counts/coverage to investigate their contribution"). It should be promoted to
   a primary question. The hypothesis is specific and falsifiable: a consumer
   that knows its query matched 340 artifacts narrows, where a consumer handed
   the top 5 of 340 without being told answers from the sample. There is
   anecdotal support — on first contact with llm-memory, a consumer chose
   `limit=2` unprompted and found its target with minimal context consumption.
   A negative result here would itself be worth reporting.

3. **Does the journey graph improve backtracking?** See Objection 2; the question
   needs restating before it can be asked.

## Objection 2: the journey graph is scoped as MVP but justified as hypothesis

Branching, backtracking, composition, replay, preservation, immutability. This is
the most expensive machinery in the design and the least evidenced. The document
treats it as settled and schedules it into the delivery sequence immediately after
the first vertical path.

An earlier draft of this review asked whether consumers would use it at all. That
framing was wrong and the project owner corrected it: search-descend-deadend-
backtrack is *already observed* behaviour in both LLMs and humans. It is the
ordinary consequence of the tool being "search" while the goal is "find" — the
founding document's own distinction. The behaviour is not in question.

The open question is narrower and better:

> Does a consumer backtrack *more effectively* when the tool holds the path than
> when it must reconstruct the path from its own context window?

This is testable and cheap. It is also the question the design's cost is actually
buying an answer to. Note that a negative result does not necessarily condemn the
feature: the graph may earn its cost by serving a later session or a human reader
rather than the model that produced it. That is a different and still-valuable
claim, and the evaluation should be able to tell the two apart.

**Recommendation.** Two changes.

First, restate the question as above — and note that answering it **does not
require Tampu**. This follows the method llm-memory actually used: its third
commit records a finding (`Confirm conversation-inclusive memory search`), its
fourth corrects a confound in that finding and adds a controlled A/B, and the
MCP server does not appear until commit fifteen. The experiment preceded the
interface. The same move is available here. llm-memory already exposes search
over ~26,600 episodes through an MCP server; that is an instrumented finding
environment that exists today. A consumer can be given a multi-step finding task
in two conditions — one reconstructing its path from its own context, one handed
an explicit record of visited nodes and dead ends — and the difference measured
in days, against a corpus that already exists.

Run that before Tampu commits to the journey machinery. If path-holding does not
improve backtracking, that is a design finding that should reshape the prototype
rather than a result discovered after the machinery is built. If it does, the
graph is justified by evidence instead of intuition, and the justification is
citable.

Second — and this is the scope objection — separate *architecture* from *MVP
implementation* explicitly. The semantic kernel should accommodate journeys,
composition, and preservation from the start; the concepts are load-bearing and
retrofitting them would corrupt artifact and revision identity. But the first
implementation need not deliver all of them. The document's own §"Delivery
sequence" nearly does this; it should say plainly which of these features are
architectural commitments and which are experiments whose results may send them
back to Yanantin rather than forward into Tampu. Findings that do not benefit
Tampu can still benefit Yanantin, where the ambition is higher. The document
should be willing to say so.

## Objection 3: the corpus may be too small to exhibit the failure being targeted

The document reports 479 PDF paths, 473 distinct byte contents, ~913.5 MiB. It
never states the failure mode it claims RAG suffers from, which leaves the corpus
size unjustifiable in either direction.

The project rests on a two-year conclusion that RAG is the wrong solution for a
*growing* corpus. But "growing" implicates at least three distinct mechanisms:

- **Density.** Embedding similarity stops discriminating as the corpus fills the
  representation space; the question shifts from "is there related material?" to
  "which of these near-identical candidates is the one?"
- **Relational loss.** Chunking severs cross-artifact relationships, so a finding
  that spans artifacts is unreachable by construction.
- **Context flooding.** Fixed-k retrieval delivers a constant volume regardless
  of whether 3 or 3,000 candidates matched, and the consumer cannot tell which.

These predict different experiments and different corpus requirements. Density
failure in particular may not manifest at 479 artifacts — that is plausibly the
regime where RAG *works*. A null comparison result there would prove nothing, and,
more dangerously, a *positive* result would be a claim about interface quality
that could be misread as a claim about scale.

**Recommendation.** State the mechanism. Then either (a) argue that 479 artifacts
suffice to exhibit it — relational loss and context flooding are plausibly
demonstrable at this scale, density is not — or (b) declare explicitly that the
prototype tests interface quality on a small corpus and that scale claims are
out of scope. Either is defensible. Silence is not, because it lets a reader
assume the stronger claim.

A related note on the baseline. The document defers embeddings, correctly, to
avoid claiming a comparison it cannot support. But it does not say *when* the
comparison becomes possible or what it requires. Reviewers will read an
unexplained deferral as evasion. The hardware is present — the local ArangoDB
enterprise instance (3.12.9.4, port 8530) has vector index support — so the
deferral is a sequencing choice, not a capability limit, and should be described
as one.

## Missing section: falsification

The document is scrupulous about what it does not claim. It never says what
result would make it abandon a commitment.

The founding document names commitments — artifact primacy, plural lenses,
explicit scope, immutable journeys, visible provenance, bounded negative claims,
honest capability discovery — and separates them from hypotheses. Good. But a
commitment that no evidence could disturb is a premise, not a finding, and the
prototype is supposed to be a research instrument.

**Recommendation.** Add a short section stating, per major claim, what observation
would count against it. Examples:

- If consumers ignore candidate counts and answer from the sample regardless,
  the counts-and-coverage claim fails.
- If path-holding does not improve backtracking over context-reconstruction, and
  no later-session or human-reader value is demonstrated, the journey graph does
  not earn its cost *in Tampu*.
- If consumers using a bounded-negative-capable interface confabulate at the same
  rate as RAG consumers, the epistemic-honesty claim fails at the level that
  matters, whatever the service reports internally.

This project stamps every commit with OpenTimestamps. That machinery exists to
make pre-registration credible. At present it is anchoring commits with no
pre-registered prediction to protect. A falsification section would give the
`WHEN` layer something worth timestamping.

## Smaller notes

- **Container pin.** The document pins the Unstructured container by digest
  (`sha256:806726e3...`). The locally present image is tagged `latest`, image ID
  `60066fe6bd5c`, 14.8 GiB. Record both the manifest digest and the local image
  ID, and note that `latest` is a moving tag — the pin is the point.

- **Dependencies verified.** Two ArangoDB instances are running locally: an
  Indaleko-era community instance on 8529 and `arangodb/enterprise:3.12.9.4` on
  8530. Both respond and require authentication. The Unstructured image is
  present but not currently running. The document says connection and version are
  checked before ingestion; this remains correct and is now partially discharged.

- **Consumer contamination.** The evaluation section requires recording author
  familiarity and using fresh sessions for comparison. Worth making explicit that
  contamination is role-specific: an instance that has read the corpus manifest
  and the research questions is compromised as an evaluation *consumer* and
  unaffected as a *builder*. The harness should track the two roles separately.
  As a practical matter, Tampu is intended as a usable toolkit as much as a
  scientific instrument, and toolkit users will not care about the confound —
  but the evaluation should still not launder a contaminated run as a clean one.

## What this review does not establish

It does not establish that the design will work. It has not been implemented, no
ingestion has been run, no lens has been evaluated, and no consumer has navigated
anything. The three objections concern framing, scoping, and justification. The
technical content — identity by content digest, revision immutability, evidence
addressing, artifact-level deduplication before counting, the refusal to blend
lens scores, the typed failure modes — I did not find fault with on reading, and
reading is not testing.
