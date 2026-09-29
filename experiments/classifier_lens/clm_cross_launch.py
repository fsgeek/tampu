"""Post-hoc, not pre-declared: CLM score differences between two encoder
launches, comparing warm repeatability repeat 2 (launch A) with the
scoring pass (launch B) on the same elements and questions."""
import json
import statistics
import sys
from pathlib import Path

from experiments.classifier_lens.common import HERE

raw = [json.loads(l) for l in Path(sys.argv[1]).read_text().splitlines()][1:-1]
scores = json.loads((HERE / "clm-scores.json").read_text())
out = {}
for cid in ("long", "proceedings"):
    warm = {r["ordinal"]: r["score"] for r in raw if r["case"] == cid and r["repeat"] == 2 and r["fresh"]}
    later = scores["cases"][cid]["scores"]
    d = [abs(v - later[str(o)]) for o, v in warm.items()]
    out[cid] = dict(elements=len(d), identical=sum(x == 0 for x in d), median_abs_diff=round(statistics.median(d), 4),
                    max_abs_diff=round(max(d), 4),
                    label_changes_at_0_5=sum((v > 0.5) != (later[str(o)] > 0.5) for o, v in warm.items()))
Path(sys.argv[2]).write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps(out))
