"""Assessment of the Jev lens, per the frozen protocol (revision 2).

Joins the probes to the committed scores for the first time. Computes
ranks, text cost under worst- and best-case tie placement, text-only
budget eligibility with conditional sensitivity, a seeded permutation
comparator, a fresh lexical replay, and the pre-declared verdict.
Writes compact results with no source text.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from experiments.classifier_lens.common import HERE, SEED, load_cases

PRIMARY, SECONDARY, PERMUTATIONS = 8192, 49152, 10_000
DELIVERED_IN_REHEARSAL = {239}
PREDICATES = {
    "any_terms": 'ANALYZER(e.text IN TOKENS(@query, "text_en"), "text_en")',
    "all_terms": 'ANALYZER(TOKENS(@query, "text_en") ALL IN e.text, "text_en")',
}


def load_elements(repo, projection_id, probes):
    doc = repo.read_projection(projection_id, verify_bytes=True)
    raw = (repo.store / doc["elements_path"]).read_text()
    try:
        elements = json.loads(raw)
    except json.JSONDecodeError:
        elements = [json.loads(line) for line in raw.splitlines() if line.strip()]
    by_ordinal = {e["ordinal"]: e for e in elements}
    for p in probes:  # frozen probe identity, checked as in the grouping diagnostic
        e = by_ordinal[p["ordinal"]]
        if (hashlib.sha256(e["text"].encode()).hexdigest() != p["text_sha256"]
                or e["page"] != p["page"] or len(e["text"]) != p["required_chars"]):
            raise ValueError(f"frozen probe {p['ordinal']} changed")
    kept = [(e["ordinal"], len(e["text"].strip().encode())) for e in elements if e["text"].strip()]
    return sorted(kept)


def worst_cost(ordinals, sizes, scores, probe_index, probe_score):
    """Probe after every element with an equal or higher score."""
    others = scores >= probe_score
    others[probe_index] = False
    return int(sizes[others].sum() + sizes[probe_index]), int(others.sum() + 1)


def best_cost(ordinals, sizes, scores, probe_index, probe_score):
    """Probe before every element with an equal score."""
    others = scores > probe_score
    others[probe_index] = False
    return int(sizes[others].sum() + sizes[probe_index]), int(others.sum() + 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compact", type=Path, required=True)
    args = parser.parse_args()
    from tampu.config import load_config
    from tampu.repository import Repository
    repo = Repository(load_config(), initialize=False)
    cases = load_cases()
    jev = json.loads((HERE / "jev-scores.json").read_text())
    rep = json.loads((HERE / "jev-repeatability-results.json").read_text())
    rng = np.random.default_rng(SEED)
    results, perm_counts = {}, np.zeros(PERMUTATIONS, dtype=int)
    perm_counts_secondary = np.zeros(PERMUTATIONS, dtype=int)
    eligible_total = 0

    for case in cases["cases"]:
        probes = case["assessment_probes"]
        projection = probes[0]["projection_id"]
        kept = load_elements(repo, projection, probes)
        ordinals = np.array([o for o, _ in kept])
        sizes = np.array([s for _, s in kept])
        score_map = jev["cases"][case["id"]]["scores"]
        assert len(score_map) == len(kept) and not jev["cases"][case["id"]]["missing"], "incomplete scoring"
        scores = np.array([score_map[str(o)] for o in ordinals], dtype=float)
        order = np.lexsort((ordinals, -scores))  # shared ordering: score desc, ordinal asc
        shared_rank = np.empty(len(order), dtype=int)
        shared_rank[order] = np.arange(1, len(order) + 1)
        index = {int(o): i for i, o in enumerate(ordinals)}
        total = int(sizes.sum())

        probe_rows = []
        for p in probes:
            i = index[p["ordinal"]]
            s = float(scores[i])
            wc, wr = worst_cost(ordinals, sizes, scores, i, s)
            bc, br = best_cost(ordinals, sizes, scores, i, s)
            repeats = rep["cases"][case["id"]]["probe_scores"][str(p["ordinal"])]
            subs = sorted(set(repeats))
            sub_costs = {str(v): worst_cost(ordinals, sizes, scores, i, v)[0] for v in subs}
            row = dict(ordinal=p["ordinal"], page=p["page"], score=s, repeated_scores=repeats,
                       shared_rank=int(shared_rank[i]), worst_rank=wr, best_rank=br,
                       percentile=round(100 * (1 - (shared_rank[i] - 1) / len(kept)), 2),
                       worst_text_cost=wc, best_text_cost=bc, sensitivity_worst_costs=sub_costs,
                       delivered_in_rehearsal=p["ordinal"] in DELIVERED_IN_REHEARSAL)
            for label, budget in (("primary_8192", PRIMARY), ("secondary_49152", SECONDARY)):
                worst_ok = wc <= budget
                subs_ok = [c <= budget for c in sub_costs.values()]
                row[label] = dict(eligible=worst_ok and all(subs_ok),
                                  tie_dependent=(bc <= budget) and not worst_ok,
                                  sensitive=len(set(subs_ok + [worst_ok])) > 1)
            probe_rows.append(row)
            if not row["delivered_in_rehearsal"] and row["primary_8192"]["eligible"]:
                eligible_total += 1

        # Random comparator: seeded permutations, same whole-element text-only rule.
        targets = [index[p["ordinal"]] for p in probes if p["ordinal"] not in DELIVERED_IN_REHEARSAL]
        for k in range(PERMUTATIONS):
            perm = rng.permutation(len(kept))
            cum = np.cumsum(sizes[perm])
            pos = np.empty(len(perm), dtype=int)
            pos[perm] = np.arange(len(perm))
            costs = cum[pos[targets]]
            perm_counts[k] += int((costs <= PRIMARY).sum())
            if case["id"] == "proceedings":
                perm_counts_secondary[k] += int((costs <= SECONDARY).sum())

        # Lexical replay: frozen artifact-local queries, restricted to this projection.
        lexical = []
        for q in case["queries"]:
            aql = (f'FOR e IN text_view SEARCH {PREDICATES[q["mode"]]} OPTIONS {{waitForSync: true}} '
                   'FILTER e.projection_id == @projection LET score = BM25(e) '
                   'SORT score DESC, e.ordinal ASC RETURN e.ordinal')
            hits = list(repo._db.aql.execute(aql, bind_vars=dict(query=q["query"], projection=projection), max_runtime=10))
            lexical.append(dict(query=q["query"], mode=q["mode"], matched=len(hits),
                                probe_ranks={str(p["ordinal"]): (hits.index(p["ordinal"]) + 1 if p["ordinal"] in hits else None)
                                             for p in probes}))

        top = order[np.cumsum(sizes[order]) <= PRIMARY]
        results[case["id"]] = dict(nonempty_elements=len(kept), text_bytes=total,
                                   distinct_scores=int(len(np.unique(scores))),
                                   elements_in_shared_8192_reading_set=int(len(top)),
                                   score_at_8192_boundary=float(scores[top[-1]]) if len(top) else None,
                                   probes=probe_rows, lexical_replay=lexical)

    p_value = float((perm_counts >= eligible_total).mean())
    mean_random = float(perm_counts.mean())
    if eligible_total >= 3 and p_value <= 0.05:
        verdict = "supports a follow-up"
    elif eligible_total <= 1:
        verdict = "no support"
    elif eligible_total == 2:
        verdict = "mixed"
    else:
        verdict = "three or more eligible but not above random baseline"
    tie = sum(r["primary_8192"]["tie_dependent"] for c in results.values() for r in c["probes"] if not r["delivered_in_rehearsal"])
    sens = sum(r["primary_8192"]["sensitive"] for c in results.values() for r in c["probes"] if not r["delivered_in_rehearsal"])
    compact = dict(protocol="revision 2", lens="jev-relevance", model="jev-1.13.0",
                   undelivered_probes_eligible_at_8192=eligible_total,
                   random_comparator=dict(permutations=PERMUTATIONS, seed=SEED, mean_eligible=mean_random,
                                          p_at_least_observed=p_value,
                                          proceedings_mean_eligible_at_49152=float(perm_counts_secondary.mean())),
                   tie_dependent=tie, sensitive=sens, verdict=verdict, cases=results)
    args.compact.write_text(json.dumps(compact, indent=1) + "\n")
    print(json.dumps({k: v for k, v in compact.items() if k != "cases"}, indent=1))
    for cid, c in results.items():
        print(f"\n{cid}: {c['nonempty_elements']} elements, {c['distinct_scores']} distinct scores, "
              f"8192-byte reading set holds {c['elements_in_shared_8192_reading_set']} elements down to score {c['score_at_8192_boundary']}")
        for r in c["probes"]:
            print(f"  ord {r['ordinal']} p{r['page']} score {r['score']} rep {r['repeated_scores']} rank {r['shared_rank']} "
                  f"(worst {r['worst_rank']}, best {r['best_rank']}) pct {r['percentile']} cost worst {r['worst_text_cost']} best {r['best_text_cost']} "
                  f"8192 {r['primary_8192']} 49152 {r['secondary_49152']['eligible']}{' [search-delivered]' if r['delivered_in_rehearsal'] else ''}")
        for l in c["lexical_replay"]:
            print(f"  lexical '{l['query']}' ({l['mode']}): matched {l['matched']}, probe ranks {l['probe_ranks']}")


if __name__ == "__main__":
    main()
