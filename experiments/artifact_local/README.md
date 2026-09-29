# Artifact-local rehearsal

Read the [decision report](../../docs/experiments/2026-09-09-artifact-local-navigation-results.md). The [design](../../docs/superpowers/specs/2026-09-09-artifact-local-navigation-design.md) and `cases.json` were signed and frozen in commit `0e784089f13e26eea5153ac88a25e01ad5f8ab54` before these searches.

From the repository root:

```bash
uv run python experiments/artifact_local/run.py --output /absolute/path/to/new-private-capture
uv run python experiments/artifact_local/run.py --replay /absolute/path/to/new-private-capture/record.json --output /absolute/path/to/new-private-replay
uv run python experiments/artifact_local/verify.py /absolute/path/to/new-private-capture
```

Live execution requires the existing configured Tampu database and pinned revision. It uses actual Service methods, not an MCP transport or a fresh consumer model. Only ephemeral in-process journeys are created. No database initialization, writes, extraction, or runtime changes occur. Raw records and traces contain source text and stay owner-local. The output directory must be new.

Offline replay regenerates the exact `record.json` and `results.json` bytes. It does not regenerate the service trace. `verify.py` checks the original trace after expanding method defaults, replays the navigation decisions against recorded responses, and recomputes the assessment and response/call ceilings. Navigation inputs omit all assessment probes. The builder's prior knowledge still influenced the fixed queries and strategy; this separation does not make the experiment blind.

`results.json` in Git is pretty-printed and contains addresses and counts without source excerpts; its parsed content equals the compact captured result. `owner-local-manifest.json` records the original capture's file sizes and hashes. `post-run-page-check.json` records a later source check of the page-409 cutoff, not a navigation input or an additional successful tool call.

Whole-probe visibility requires a single inspected text to match its frozen SHA-256. Element listings count as address discovery and show at most 240 characters. No synthetic union of fragments is treated as complete evidence. The assessment counts verified inspection outputs, not unidentified search snippets. Service errors remain in the trace and budget; an unstable observed index makes the case inconclusive. An unexpected exception or failed accounting assertion aborts the script; the ordinary service trace may survive, but final records are not guaranteed in that situation.
