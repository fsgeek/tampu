# Retrieval grouping diagnostic

The [protocol](protocol.md) and [six cases](cases.json) were frozen in signed commit `8d5c04e709fae15b787b3b850cc9fb256326cfb4` before new lexical rankings were inspected. Read the [decision report](../../docs/experiments/2026-09-09-retrieval-grouping-results.md) first. This is an exposed development diagnostic, not a retrieval benchmark or a consumer-model evaluation.

From the repository root, using its existing environment:

```bash
uv run pytest tests/test_retrieval_grouping.py -q
uv run python experiments/retrieval_grouping/run.py --output /absolute/path/to/new-private-capture
uv run python experiments/retrieval_grouping/run.py --capture /absolute/path/to/new-private-capture/capture.json --output /absolute/path/to/new-private-replay
```

The live command requires the existing Tampu configuration and the pinned research revision; it reads the database and stored projections without initializing schema. The replay command requires neither database access nor the corpus. Each output directory must be new. **Capture and response files contain paper text; keep them owner-local.** `results.json` contains evidence addresses and counts without excerpts. Frozen origin paths identify prior local traces; live capture does not require those trace files.

`owner-local-manifest.json` records the original run's file sizes and SHA-256 hashes. Compare a replay's 14 files to the capture's files byte-for-byte. The committed pretty-printed `results.json` has the same parsed content as its compact owner-local counterpart; response hashes are over exact canonical wire bytes. The capture embeds the canonical case-sheet digest and rejects replay with a different case sheet.

The grouped arm uses the production maximum-matching-element selection rule. The experiment's response envelope differs from MCP: it equalizes the two presentations rather than replaying an old journey. Six additional read-only production `search_candidates` calls verified all grouped artifact identities, evidence addresses, scores, and full matching texts against this export. Their compact verification record is committed as `production-parity.json`; they do not supply a second experimental match set.

That file is operator-recorded corroboration, not an independently certified database attestation. The assertion procedure used was the following (adjust the owner-local capture path). A later index change can legitimately prevent historical parity; offline replay remains the reproducibility path for the paired comparison.

```bash
uv run python - <<'PY'
import importlib.util
import json
from pathlib import Path
from tampu.config import load_config
from tampu.repository import Repository

spec = importlib.util.spec_from_file_location("audit", "experiments/retrieval_grouping/run.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
config = json.loads(Path("experiments/retrieval_grouping/cases.json").read_text())
capture = json.loads(Path("/home/tony/projects/tampu/tmp/retrieval-grouping-20260909/capture/capture.json").read_text())
repo = Repository(load_config(), initialize=False)
checks = []
for case, item in zip(config["cases"], capture["cases"], strict=True):
    actual = repo.search_candidates(config["revision_id"], "lexical/v1",
                                   case["query"], case["mode"], case["filters"])
    expected = audit.rank(item["rows"], "grouped")
    comparable = [dict(artifact_id=c["artifact_id"],
                       projection_id=c["evidence"]["projection_id"],
                       ordinal=c["evidence"]["ordinal"], page=c["evidence"]["page"],
                       score=c["score"], text=c["text"])
                  for c in actual["candidates"]]
    assert comparable == expected, case["id"]
    assert actual["index_generation_stable"]
    assert actual["index_generation"]["generation_id"] == capture["index_before"]["generation_id"]
    checks.append(dict(case=case["id"], equal=True, candidates=len(expected)))
print(json.dumps(checks, indent=2))
PY
```

No runtime source, database schema, corpus revision, or extraction changed. The only generated source-bearing output is in the owner-local directory named by the manifest. A 20,000-match ceiling makes an overflowing case inconclusive; a changed observed index generation likewise prevents a paired conclusion. A same-count out-of-band content mutation is outside that generation fingerprint's guarantees.
