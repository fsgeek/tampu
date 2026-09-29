# Path-record pilot harness

This is a research adapter for llm-memory, separate from Tampu's product code. See the [protocol](../../docs/experiments/2026-09-08-path-pilot-protocol.md). Private corpus, vendor copies, configuration, prompts, and logs are kept in ignored `tmp/path-pilot/` in the experiment worktree. They are not a distributable transcript dataset.

## Dependencies and isolated server

The recorded run uses Python 3.14 and `python-arango==8.3.3` from `/home/tony/projects/llm-memory/.venv/bin/python`. The existing llm-memory checkout supplies `llm_memory/{__init__,index,search,recall}.py`; copy those four files to a private `vendor/llm_memory/` directory and retain their hashes. Source commit and actual copied hashes are in the protocol/manifest. No source config or database credentials are copied.

The server was created with:

```bash
docker run -d --name tampu-path-pilot-20260908 \
  --label tampu.experiment=path-pilot --memory 2g --cpus 2 \
  -p 127.0.0.1:18529:8529 -e ARANGO_NO_AUTH=1 \
  sha256:c1819a9b2da82c98bfbb91a4a7becde1582281ac3bd2f2130ec8859314aac101
```

The selected image is local, not a moving tag. The endpoint is intentionally fixed in the harness. Setup creates a separate `pilot` database, calls the copied `ensure_index` there, imports the frozen JSONL, and compares all imported documents after removing `_id` and `_rev`. The source-store query, complete membership, per-document hashes and view properties are in the private manifest. Replaying requires that private bundle or a separately approved replacement corpus; a different snapshot constitutes a different experiment.

The no-auth container is loopback-bound and disposable. Its interface restrictions are not an OS sandbox: trusted setup and instructed consumers share a host. No consumer may call the database directly. Stop the named experiment container after the pilot; preserve its filesystem until the report is reviewed.

## Run configuration and calls

Each fresh run directory has a trusted `config.json`:

```json
{
  "arm": "record",
  "endpoint": "http://127.0.0.1:18529",
  "database": "pilot",
  "vendor_path": "/absolute/private/vendor",
  "corpus_path": "/absolute/private/corpus.jsonl",
  "corpus_sha256": "the verified SHA-256 of that JSONL",
  "max_calls": 20,
  "max_seconds": 600,
  "started_at": 1788886209.0
}
```

The displayed time is an example; the runner writes the actual dispatch epoch. Set `arm` to `control` to disable ledger retrieval. Diagnostic operations are issued before dispatch and supplied verbatim in the prompt; the runner then sets the dispatch clock, so setup waiting does not reduce the consumer's ten minutes. Seed operations still consume navigation slots.

```bash
/home/tony/projects/llm-memory/.venv/bin/python experiments/path_holding/harness.py \
  /absolute/private/runs/r01 '{"op":"search","query":"coverage","limit":2}'
```

Requests:

- `search`: `query` required; optional `scope` (default `all`), `limit` (default 2, range 1–10), inclusive `since`, exclusive `until`. Search uses OR tokens, not an implicit conjunction.
- `recall`: `key` required, previously returned by that run's search; returns the complete episode.
- `note`: consumer-authored `text` and `status` required. Both arms can record a declaration.
- `ledger`: optional `offset` (default 0), `limit` (default 10, range 1–10); record arm only. Returns prior requests, counts, handles, inspected keys and declared status, excluding the current call.
- `finalize`: `answer` required, a JSON string or structured value. Saves the answer and terminates navigation. Submission is available after navigation exhaustion and counted separately.

Every invocation is serialized under a per-run lock and appended to `operations.jsonl`, including errors. The log contains exact request/response JSON, UTF-8 byte counts excluding the transport newline, wall-clock timestamps and harness duration. The wrapper's `operation_id` identifies that observation. Full logs contain evidence text and are private. Corpus-file hashing prevents silent changes to the on-disk snapshot; runner audits verify database equality and vendor hashes before/after trials. Runtime file hashing alone does not attest database contents.

## Verification

```bash
/home/tony/projects/llm-memory/.venv/bin/python -m pytest \
  experiments/path_holding/test_harness.py -q
```

Tests create a uniquely named fixture database on port 18529 and clean up only that fixture. They exercise real Arango retrieval, matched arms, scoped counts/date filters, deterministic ordering, handle restrictions, history isolation, byte accounting, budget/time limits and terminal behavior. They require the isolated server to be running and never consult the live llm-memory configuration.
