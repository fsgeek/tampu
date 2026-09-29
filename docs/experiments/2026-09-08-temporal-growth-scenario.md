# Returning to a growing research collection

Date: 2026-09-08. Author: Astra.

Status: prepared development fixture. The PDF snapshots exist locally and their membership can be reproduced from the accompanying manifest. No Tampu consumer trial has run on them. This is not a preregistration, a held-out benchmark, or completion of the Tampu service.

## Decision and purpose

Use the existing corpus to simulate acquisition over time, then attach live arXiv acquisition after a useful end-to-end example works. This follows Tony's approval of the growing-collection use case and his preference to demonstrate benefit in one example before expanding to other preprint services. Local replay avoids repeated external acquisition during development. No network acquisition, scheduler, arXiv library, or additional provider integration is needed for this fixture.

The consumer's recurring question is: **what has arrived or changed since I last investigated this, and which earlier findings warrant reconsideration?** The service must preserve the earlier observation's scope and evidence while making a successor collection available. The consumer assesses significance; Tampu does not infer that a newer artifact invalidates an earlier finding.

QuantumOS provides a working precedent for candidate discovery tied to named questions. Its [surveillance protocol](/home/tony/projects/quantumos/docs/superpowers/specs/2026-07-25-literature-surveillance-protocol.md) is available in the sibling repository; its cloud sweep's [PR #5](https://github.com/fsgeek/quantumos/pull/5) explicitly accounted for an earlier unmerged sweep in PR #4. Discovery, download, admission, reading and review can advance separately. This scenario exercises admitted collection growth; it does not pretend to implement all of those states.

## Fixed input sequence

The [manifest](2026-09-08-temporal-growth-manifest.json) records every source hash, byte size, known source alias, replay path, and first admission stage. The source inventory has 479 PDF paths and 473 distinct byte sequences. Six duplicate aliases are collapsed for this fixture; aliases remain recorded in the manifest. Both versions of a work remain distinct artifacts when their bytes differ.

| Stage | Simulated acquisition day | Newly admitted distinct artifacts | Cumulative distinct artifacts | Deliberately placed evidence |
|---|---:|---:|---:|---|
| r0 | 0 | 160 | 160 | Short caching report; *Online Optimization with Uncertain Information*; *Legible Consensus* v2 |
| r1 | 7 | 160 | 320 | Long caching report, including its additional evaluation, definitions and experimental switching threshold |
| r2 | 14 | 153 | 473 | NSDI proceedings containing LHD; Pichay; *Legible Consensus* v3 |

The seven deliberate placements are development controls. All remaining artifacts are sorted by their full SHA-256 values, then assigned to fill the three first-admission batches to 160, 160 and 153. This is deterministic background assignment, not relevance sampling or a claim about how researchers acquire papers in practice. The final stage contains every distinct artifact in the observed source inventory.

The simulated day offsets represent acquisition order only. They are not fabricated publication dates or historical observations. Actual capture time and future Tampu admission time must be recorded separately. Filesystem modification times on the generated copies have no bibliographic meaning. Unknown publication dates stay unknown.

The snapshots contain independent PDF copies with read-only file permissions, not symlinks or hard links to the mutable original collection. Earlier stages remain available. Their membership checksums are checksums of this fixture, not substitutes for the prototype's opaque service revision identifiers.

## Investigations

### Prediction-assisted eviction

Initial prompt at r0:

> What does this collection establish about using prediction-assisted eviction when predictions deteriorate? Separate evaluated behavior from theoretical guarantees, identify the policies and assumptions involved, and record anything unresolved. Cite the artifact and PDF page for each material conclusion.

At each successor stage:

> Revisit your earlier assessment using the current collection. What new or changed evidence warrants reconsideration, what remains supported, and what remains unresolved? Distinguish evidence newly acquired by this collection from newly published research. Preserve the earlier assessment's scope and cite the evidence for any change.

The [completed source investigation](2026-09-08-prediction-assisted-eviction-assessment.md) provides development guidance. The short and long caching reports overlap in reported BrightKite results; the long one adds CitiBike and explicitly specifies a switching threshold that never invokes the randomized fallback. LHD introduces independent evidence about prediction-based ranking and feedback. Pichay includes context-eviction failure evidence relevant to what an explicit fault metric misses.

These placements are reasons to investigate, not an exhaustive answer key. Other papers or works inside proceedings may already support a conclusion at an earlier stage. Withholding a selected artifact does not establish the absence of its idea. A consumer can correctly retain an earlier conclusion while adding qualification or independent support.

### A real revision of a known work

Use a separate, bounded revision check so that papers about quorum geometry are not forced into the eviction question:

> Examine how *Legible Consensus*, arXiv:2603.28788, justifies the Earth-node intersection requirement in Section 7.1. Record the version, explanation, resulting requirement and evidence location.

At r2:

> Revisit that explanation. Has a newer version become available in this collection? Identify any change in the justification and whether the stated requirement changes. Keep the earlier version's evidence address valid.

Both local PDFs identify the same arXiv work: v2 and v3. Their page-10 text changes the justification from a statement about overlap between two Phase 2 quorums to a statement about a set intersecting every Phase 2 quorum. The stated `|E| - k + 1` Phase 1 requirement remains in both passages. This was checked in extracted text; it is a development comparison, not a complete audit of either version or proof that every other section is unchanged. A scored answer would require checking the rendered passages and fixing a rubric before trials.

Revision order and same-work identity are supported here by the identifiers on the PDFs. The differently titled caching pair is represented separately as overlapping reports; no formal version relation is inferred from similarity alone.

## Running the example

The prepared snapshots are under the main Tampu checkout's ignored directory:

```text
tmp/temporal-growth-20260908/r0/
tmp/temporal-growth-20260908/r1/
tmp/temporal-growth-20260908/r2/
```

The manifest's `source_paths` are relative to that checkout. To recreate a snapshot elsewhere, select entries whose `first_stage` is at most the desired stage number, locate an alias with the recorded SHA-256 and byte size, and copy those bytes to `replay_path` under a new destination. Verify the output hashes. For the stage membership checksum, sort its full lowercase SHA-256 strings, append an ASCII newline to each, concatenate, and hash those bytes. The manifest records the expected checksums.

When the service's admission path is ready, populate one registered working directory from r0 and publish its first revision. Add r1's new files to that same registered directory, reconcile and publish a successor; repeat for r2. Retain the frozen snapshots separately. The snapshots themselves are input directories, not published Tampu revisions. Their successfully copied files have not thereby been successfully extracted or indexed.

Give a consumer access only to the current published revision, its legitimately available earlier observations, and permitted earlier evidence. The full fixture manifest, this scenario, the final assessment and future snapshot directories are builder materials; do not expose them as search results. Running a consumer with unrestricted shell access to the parent workspace would defeat that boundary. A later trial must establish actual tool/process isolation before claiming that future evidence was withheld.

## What to observe

For an initial development run, retain the consumer's initial and revised assessments, all retrieval responses, exact service revision/projection identifiers, and a brief comparison against the source evidence. Observe:

- Whether the consumer identifies a consequential addition or revision and cites the correct version.
- Whether it distinguishes overlapping results from additional evaluation or independent evidence.
- Whether it preserves warranted earlier claims and qualifies or retracts those that need revision.
- Whether unknown dates, extraction gaps, empty results and older snapshots receive appropriate scope qualifications.
- Reading effort, tool calls and context volume, including unsuccessful navigation; counts of downloaded papers alone do not measure benefit.

A comparison condition can supply the same newly added PDFs, prior PDFs and earlier assessment through a simple directory/search interface. It must have equal access to evidence and the same underlying extraction where extraction is not the treatment. This fixture does not fix a statistical trial design or justify claims of superiority. The cases are already exposed to the builder and are development cases.

## Implementation boundary

The next service increment remains the approved prototype's vertical path: capture a PDF, extract it with page provenance, publish a revision, search, inspect bounded evidence and record a scoped finding. Reconciliation then runs against these prepared stages. This scenario selects the use case and prepares its input; it does not replace admission, extraction diagnostics, database publication or MCP tools with a special-purpose answer script.

Live acquisition follows that working example. Start with one source and a concrete research question. Record retrieval provenance, version identifiers and acquisition failures; maintain the distinction between a candidate's possible relevance and a finding supported by reading. Additional preprint services can be community adaptations once the example demonstrates benefit. No general connector framework is an MVP prerequisite.

## Fixture verification

After materialization, all 953 PDF copies across the three snapshots were reread and checked against their recorded SHA-256 and byte size. Exact stage membership, cumulative inclusion, addition counts and all three membership checksums matched the manifest. The copies have distinct filesystem inodes, share no inode with a source alias, contain no symlinks and have read-only file permissions. The manifest accounts for all 479 source aliases. Local document links were checked. Verification output is retained beside the ignored snapshots in `verification.json`; no PDFs were staged for Git.
