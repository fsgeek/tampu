"""Disagreement between the Jev and CLM lenses, per the frozen protocol:
Spearman correlation over all non-empty elements, and overlap of the two
8,192-byte reading sets in the shared ordering (score desc, ordinal asc)."""
import json
import sys
from pathlib import Path

import numpy as np

from experiments.classifier_lens.assess import PRIMARY, load_elements
from experiments.classifier_lens.common import HERE, load_cases


def average_ranks(x):
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(len(x))
    sx = x[order]
    i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and sx[j + 1] == sx[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2 + 1
        i = j + 1
    return ranks


def reading_set(ordinals, sizes, scores):
    order = np.lexsort((ordinals, -scores))
    return set(ordinals[order[np.cumsum(sizes[order]) <= PRIMARY]].tolist())


def main():
    from tampu.config import load_config
    from tampu.repository import Repository
    repo = Repository(load_config(), initialize=False)
    jev = json.loads((HERE / "jev-scores.json").read_text())
    clm = json.loads((HERE / "clm-scores.json").read_text())
    out = {}
    for case in load_cases()["cases"]:
        cid = case["id"]
        kept = load_elements(repo, case["assessment_probes"][0]["projection_id"], case["assessment_probes"])
        ordinals = np.array([o for o, _ in kept]); sizes = np.array([s for _, s in kept])
        a = np.array([jev["cases"][cid]["scores"][str(o)] for o in ordinals])
        b = np.array([clm["cases"][cid]["scores"][str(o)] for o in ordinals])
        rho = float(np.corrcoef(average_ranks(a), average_ranks(b))[0, 1])
        ra, rb = reading_set(ordinals, sizes, a), reading_set(ordinals, sizes, b)
        out[cid] = dict(spearman=round(rho, 4), jev_reading_set=len(ra), clm_reading_set=len(rb),
                        overlap=len(ra & rb), jaccard=round(len(ra & rb) / len(ra | rb), 4))
    Path(sys.argv[1]).write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
