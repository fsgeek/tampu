"""Summarize CLM fresh-inference repeatability from the owner-local raw record."""
import hashlib
import json
import sys
from pathlib import Path

from experiments.classifier_lens.common import load_cases, summarize

raw = Path(sys.argv[1])
rows = [json.loads(l) for l in raw.read_text().splitlines()]
header, footer = rows[0], rows[-1]
recs = [r for r in rows[1:-1]]
cases = {}
for case in load_cases()["cases"]:
    cid = case["id"]
    mine = [r for r in recs if r["case"] == cid]
    stale = [r for r in mine if not r["fresh"]]
    invalid = [r for r in mine if r["score"] is None]
    values = {}
    for r in mine:
        if r["fresh"] and r["score"] is not None:
            values.setdefault(r["ordinal"], []).append(r["score"])
    complete = {k: v for k, v in values.items() if len(v) == 3}
    cases[cid] = dict(sampled_elements=len({r["ordinal"] for r in mine}), calls=len(mine),
                      excluded_zero_encoder_tokens=len(stale), invalid_scores=len(invalid),
                      elements_with_three_fresh_repeats=len(complete), stats=summarize(complete),
                      probe_scores={str(p["ordinal"]): values.get(p["ordinal"]) for p in case["assessment_probes"]},
                      encoder_tokens=sum(r["encoder_tokens"] for r in mine))
out = dict(protocol="revision 2", measurement="CLM fresh-inference repeatability: new Engine and Embedder per "
           "repetition, vector arena disabled, vLLM prefix caching disabled",
           identity=header["identity"], schema_check=header["schema_check"], inputs_sha256=header["inputs_sha256"],
           started_at=header["at"], finished_at=footer["at"],
           head_unchanged=footer["head_sha256_after"] == header["identity"]["head_sha256"],
           raw_records_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(), cases=cases)
Path(sys.argv[2]).write_text(json.dumps(out, indent=1) + "\n")
for cid, c in cases.items():
    print(cid, json.dumps(c["stats"]), "excluded", c["excluded_zero_encoder_tokens"], "invalid", c["invalid_scores"])
    print("   probes", {k: [round(x, 4) for x in v] if v else v for k, v in c["probe_scores"].items()})
print("head unchanged", out["head_unchanged"], "schema", out["schema_check"])
