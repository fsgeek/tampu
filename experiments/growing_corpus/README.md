# Growing-corpus development run

The thin `run.py` runner records real Codex CLI consumers and publications against the prepared local corpus. It refuses observations with an uncommitted worktree, records source hashes before/after, retains exact prompts, MCP schemas, CLI events, owner-enabled source-bearing service traces, usage and failures. No paper bytes or full traces belong in Git.

Prerequisites: Python 3.14, `uv sync`, configured dedicated Tampu database/user, existing extracted fixtures described in [the scenario](../../docs/experiments/2026-09-08-temporal-growth-scenario.md), authenticated Codex CLI, and its supported automatic approval review. The consumer sees only four MCP tools with temporary process-local state and an explicit owner trace. Shell, apps, browser, skills discovery and external search are disabled. This is a recorded CLI boundary, not an OS air gap. Automatic-review rejection must be retained without bypass.

From this worktree, with owner-local output directories:

```sh
uv run python experiments/growing_corpus/run.py consumer eviction-r0 --question eviction_initial --output /home/tony/projects/tampu/tmp/prototype-readiness/consumers
uv run python experiments/growing_corpus/run.py consumer legible-r0 --question legible_initial --output /home/tony/projects/tampu/tmp/prototype-readiness/consumers
uv run python experiments/growing_corpus/run.py publish 1 --main /home/tony/projects/tampu --consumers /home/tony/projects/tampu/tmp/prototype-readiness/consumers
uv run python experiments/growing_corpus/run.py consumer eviction-r1 --question eviction_successor --prior /home/tony/projects/tampu/tmp/prototype-readiness/consumers/eviction-r0/prior-final-only.txt --output /home/tony/projects/tampu/tmp/prototype-readiness/consumers
uv run python experiments/growing_corpus/run.py publish 2 --main /home/tony/projects/tampu --consumers /home/tony/projects/tampu/tmp/prototype-readiness/consumers
uv run python experiments/growing_corpus/run.py consumer eviction-r2 --question eviction_successor --prior /home/tony/projects/tampu/tmp/prototype-readiness/consumers/eviction-r1/assessment.txt --output /home/tony/projects/tampu/tmp/prototype-readiness/consumers
uv run python experiments/growing_corpus/run.py consumer legible-r2 --question legible_successor --prior /home/tony/projects/tampu/tmp/prototype-readiness/consumers/legible-r0/prior-final-only.txt --output /home/tony/projects/tampu/tmp/prototype-readiness/consumers
```

The first actual r0 publication predates this runner and is deliberately reused. Successors are guarded by the recorded immediate predecessor and completed original prior-stage runs. Each question has a 20-call/600-second instruction; the process monitor detects and records an observed 21st call rather than claiming prevention. Consumers use requested `gpt-5.6-sol`, medium reasoning, CLI default sampling/output limit; CLI does not expose a resolved model revision. Each successor receives only its preceding assessment/citations: staged resumption, not continuous process memory. Never edit source during observations or publish a successor while original consumers at the predecessor are running.

The response-only comparison option takes a frozen `--prompt` with `--response-only` and exposes no MCP tools. Its payloads, masks and visible-evidence scoring sheet must be frozen before those observations. These are exposed development tasks and cannot establish statistical benefit.

## Observed run and source identities

The run is complete as a development observation, including an original failure.
See [results](../../docs/experiments/2026-09-08-usable-prototype-results.md),
[metrics](evidence/original-consumer-metrics.json), [source review](evidence/source-review.md)
and [owner-local evidence hashes](evidence/owner-local-evidence-manifest.json).
The original eviction r2 episode exceeded its budget at 24 calls and has no final
assessment. Its original nonempty `assessment.txt` is a progress message;
`completion-adjudication.json` corrects the original summary without rewriting it.

| Operation | Clean source commit used |
|---|---|
| r0 original consumers | `4995f634ebe487afa25e807cb7ec28280fe01427` |
| r1 publication | `4329f35d12af1c9bdf286d1505f8025f5eedccce` |
| r1 original consumer | `704cdef99d3aed0b36dba1d537273c4761b37a05` |
| r2 publication/original consumers and all 16 comparisons | `427112ba6e3f70f7930b97526c9bf5a3152befb6` |
| Separate direct-evidence diagnostic | `1738ef4f4835eb0034d5b9149c73a6e81ba71e02` |

Use the exact commits and frozen inputs to recreate the **original interface**.
The current interface was revised after those observations to disclose inspection
limits and preview-versus-citation semantics; that correction has not been shown
to improve model investigation outcomes. All original runtime source files had
identical hashes across their runner/input commits. The already published r0
record retains its narrower import-time attribution limitation.

For a fresh replay, use a new dedicated database/configuration and new working,
publication-output and consumer-output directories. Recreate the r0 snapshot from
the manifest, verify its hashes, and register it with the CLI before any consumer:

```sh
uv run tampu init
uv run tampu ingest research /absolute/new/working-root --profile unstructured --image downloads.unstructured.io/unstructured-io/unstructured@sha256:806726e3997d33bce9e32facd86c947b241101c58496f2774ad5f09f86e798bc --metadata /absolute/new/r0-metadata.json
```

The runner intentionally does not republish the existing actual r0 baseline.
For a fresh run, retain the CLI's `result` revision object in a new
`growth/r0-publication.json` with `stage`, measured `wall_seconds` and captured
source identity, and pass that new main/output layout to `publish`. Do not copy an
old revision ID into a new database's record. Only metadata transcribed from the
three specified PDF first pages belongs in the supplied metadata files; no
acquisition-stage dates are bibliographic dates. The two r0 investigations must
finish before r1; the r1 investigation must finish before r2. Asking an r0 question
against the already published r2 collection does not recreate the experiment.

The exact captured run commands above use this owner's established paths. To
reproduce data preparation elsewhere, follow the manifest's snapshot-copy rules
and use the public `tampu ingest` CLI with the same pinned profile at each stage;
source files and fresh opaque revision IDs are required. No paper downloader or
general experiment scheduler is part of this prototype.

## Additional actual diagnostic and comparison commands

The diagnostic database must differ from the consumer database. Provision a
unique database/user with `scripts/provision-tampu.py` and a private config file;
its artifact store may reuse immutable cached files. Failed attempts and alternate
projections must not replace primary research observations.

```sh
uv run python experiments/growing_corpus/diagnostics.py --config /home/tony/.config/tampu/growth-diagnostics-b.json --output /absolute/new/diagnostic-output
uv run python experiments/growing_corpus/comparisons.py --observations /absolute/new/diagnostic-output/observations.json --output /absolute/new/comparison-inputs
# Review and commit the exact masks, source identities, questions and rubrics first.
uv run python experiments/growing_corpus/batch.py --inputs /absolute/new/comparison-inputs --output /absolute/new/comparison-consumers
uv run python experiments/growing_corpus/direct_evidence.py --output /absolute/new/direct-input --prior /absolute/completed/eviction-r1/assessment.txt
uv run python experiments/growing_corpus/run.py consumer eviction-direct --prompt /absolute/new/direct-input/prompt.txt --response-only --output /absolute/new/diagnostic-consumers
uv run python experiments/growing_corpus/audit.py --local /home/tony/projects/tampu/tmp/prototype-readiness --output /absolute/new/compact-evidence
```

The actual corrected diagnostics were followed by a separately recorded full
handle inspection after the first preview-only capture; the frozen comparisons
consumed `task4-diagnostics-corrected/observations-final.json`. The final diagnostic
script now performs that full handle read directly. The direct-evidence command
is a separate, explicitly builder-selected diagnosis after the original failure,
not a rerun or replacement original. It reads only pinned selected artifacts and
records every source ordinal/page and text hash.

Each subprocess gets requested `gpt-5.6-sol`, medium reasoning and supported CLI
default generation/sampling settings. Resolved model revision and numeric output
cap are not exposed; prompt length guidance is not enforcement. All stderr,
errors, usage, termination, schema and response bytes stay in the run directory.
A summary requires `turn.completed`, no failed turn/stop reason and successful
exit before labeling an assessment final. No substantive answer is retried.

The compact audit copies assessments and measurements, not source-bearing full
traces. It corrects legacy completion classification from raw event lifecycle.
Its path manifest identifies owner-local evidence that is unavailable to a reader
without the corpus/trace files; hashes alone do not allow independent semantic
verification. The original schema was 10,833 pretty JSON bytes; result-wrapper
JSON sizes are framing proxies, not measured transport wire bytes.

## Setup and final checks

Python 3.14+, ArangoDB with ArangoSearch `text_en`, Poppler and (for Unstructured)
Docker are required. `scripts/provision-tampu.py --help` describes dedicated
provisioning; default private runtime configuration is
`~/.config/tampu/config.json`, overridable by `TAMPU_CONFIG`. It contains endpoint,
database, scoped username/password and artifact-store path. Do not place actual
credentials in this repository. MCP clients launch `.venv/bin/tampu serve` over
stdio; administrative ingestion stays in the owner CLI.

```sh
uv run pytest tests -q
uvx ruff check src/tampu tests scripts/provision-tampu.py experiments/growing_corpus
uv run python -m compileall -q src tests scripts/provision-tampu.py experiments/growing_corpus
uv run tampu describe --collection research
```

`tests/test_mcp.py` runs a fresh CLI/MCP subprocess smoke against a disposable
isolated database, including actual tools/list and tools/call. Integration tests
use the private `~/.config/tampu/test-admin.json` to create/drop dedicated test
resources, not the published research database. The opt-in real extractor test
is normally skipped; the actual extraction pilot/full run supplies separate
container evidence. The old 21-test path harness requires its documented
separate llm-memory environment and ArangoDB on port 18529; root ran it once,
then stopped only that container while preserving data. Its exact command/result
is in [the retained record](evidence/path-pilot-final-regression.json).
