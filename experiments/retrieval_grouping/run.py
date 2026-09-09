"""Read-only lexical capture and deterministic, equal-budget presentation audit."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def address(row):
    return row["artifact_id"], row["projection_id"], row["ordinal"]


def rank(rows, presentation):
    if presentation not in {"grouped", "passage"}:
        raise ValueError("unknown presentation")
    ordered = sorted(rows, key=lambda r: (-r["score"], r["artifact_id"], r["ordinal"]))
    if presentation == "passage":
        return ordered
    seen, result = set(), []
    for row in ordered:
        if row["artifact_id"] not in seen:
            seen.add(row["artifact_id"])
            result.append(row)
    return result


def pack(rows, scope, presentation, budget=8192, limit=20, excerpt_chars=800):
    payload = dict(presentation=presentation, scope=scope, hits=[], omitted_entries=len(rows))
    if len(encoded(payload)) > budget:
        raise ValueError("scope envelope exceeds byte budget")
    for row in rows[:limit]:
        hit = {k: row[k] for k in ("artifact_id", "projection_id", "ordinal", "page", "score")}
        hit["excerpt"] = row["text"][:excerpt_chars]
        trial = {**payload, "hits": payload["hits"] + [hit],
                 "omitted_entries": payload["omitted_entries"] - 1}
        if len(encoded(trial)) > budget:
            break
        payload = trial
    return payload


def assess_probe(probe, rows, grouped, passage):
    ordered = rank(rows, "passage")
    lookup = {address(r): i for i, r in enumerate(ordered)}
    key = address(probe)
    result = {**probe, "matched": key in lookup, "global_rank": None,
              "within_artifact_rank": None, "grouped_rank": None}
    if key in lookup:
        i = lookup[key]
        source = ordered[i]
        if (hashlib.sha256(source["text"].encode()).hexdigest() != probe["text_sha256"]
                or source["page"] != probe["page"]):
            raise ValueError("captured probe differs from frozen source")
        result["global_rank"] = i + 1
        result["within_artifact_rank"] = sum(r["artifact_id"] == probe["artifact_id"] for r in ordered[:i + 1])
    grouped_keys = [address(r) for r in rank(rows, "grouped")]
    if key in grouped_keys:
        result["grouped_rank"] = grouped_keys.index(key) + 1
    for name, payload in (("grouped", grouped), ("passage", passage)):
        shown = next((r for r in payload["hits"] if address(r) == key), None)
        if not result["matched"]:
            status = "not_matched"
        elif name == "grouped" and key not in grouped_keys:
            status = "grouped_away"
        elif shown is None:
            status = "rank_or_capacity"
        elif len(shown["excerpt"]) < probe["required_chars"]:
            status = "excerpt_clipped"
        else:
            status = "visible"
        result[name] = dict(status=status, address_visible=shown is not None,
                            whole_probe_visible=status == "visible")
    return result


def compare(capture, config):
    results, responses = {"schema": "retrieval-grouping-results/v1", "cases": []}, {}
    captured = {c["id"]: c for c in capture["cases"]}
    for case in config["cases"]:
        item = captured[case["id"]]
        summary = {"id": case["id"]}
        results["cases"].append(summary)
        if not capture["index_stable"] or not item["complete"]:
            summary.update(status="inconclusive", reason=item.get("error") or
                           ("index changed" if not capture["index_stable"] else "match export overflow"))
            continue
        rows = item["rows"]
        try:
            payloads = {name: pack(rank(rows, name), item["scope"], name,
                                  config["budget_bytes"], config["entry_limit"], config["excerpt_chars"])
                        for name in ("grouped", "passage")}
            probes = [assess_probe(p, rows, payloads["grouped"], payloads["passage"])
                      for p in case["probes"]]
        except ValueError as error:
            summary.update(status="inconclusive", reason=str(error))
            continue
        summary.update(status="complete", matched_passages=len(rows),
                       matched_artifacts=len({r["artifact_id"] for r in rows}),
                       probes=probes, coverage=item["scope"]["coverage"], presentations={})
        responses[case["id"]] = payloads
        for name, payload in payloads.items():
            unique = len({r["artifact_id"] for r in payload["hits"]})
            summary["presentations"][name] = dict(
                bytes=len(encoded(payload)), entries=len(payload["hits"]),
                unique_artifacts=unique, repeated_artifact_entries=len(payload["hits"]) - unique,
                omitted_entries=payload["omitted_entries"], response_sha256=digest(payload),
                returned=[{k: r[k] for k in ("artifact_id", "projection_id", "ordinal", "page", "score")}
                          for r in payload["hits"]])
    return results, responses


def capture_live(config):
    from tampu.config import load_config
    from tampu.repository import Repository

    repo = Repository(load_config(), initialize=False)
    revision = repo.resolve_revision(config["collection"], config["revision_id"])
    members = repo.members(config["revision_id"])
    membership = {m["artifact_id"]: m for m in members}
    # Validate frozen evidence before any search. Empty controls also pin their projection.
    for artifact, expected in config["control_projection_coverage"].items():
        if membership[artifact]["projection_id"] != expected["projection_id"]:
            raise ValueError("frozen projection is not selected by revision")
        projection = repo.read_projection(expected["projection_id"], verify_bytes=True)
        if projection["coverage"] != expected["coverage"]:
            raise ValueError("frozen coverage changed")
        elements = {e["ordinal"]: e for e in json.loads((repo.store / projection["elements_path"]).read_text())}
        for case in config["cases"]:
            for probe in case["probes"]:
                if probe["artifact_id"] == artifact:
                    element = elements[probe["ordinal"]]
                    if (hashlib.sha256(element["text"].encode()).hexdigest() != probe["text_sha256"]
                            or element["page"] != probe["page"]
                            or len(element["text"]) != probe["required_chars"]):
                        raise ValueError("frozen probe changed")
    predicates = {
        "any_terms": 'ANALYZER(e.text IN TOKENS(@query, "text_en"), "text_en")',
        "all_terms": 'ANALYZER(TOKENS(@query, "text_en") ALL IN e.text, "text_en")',
        "phrase": 'PHRASE(e.text, @query, "text_en")',
    }
    before = repo._observe_index_generation()
    capture = {"started_at": datetime.now(UTC).isoformat(), "revision_id": config["revision_id"],
               "config_sha256": digest(config), "index_before": before, "cases": []}
    coverage_cache = {}
    for case in config["cases"]:
        print("Capturing " + case["id"], flush=True)
        item = dict(id=case["id"], complete=False, rows=[])
        capture["cases"].append(item)
        try:
            filtered, _ = repo._filter_members(members, case["filters"], "lexical/v1")
            projections = sorted(m["projection_id"] for m in filtered if m["projection_status"] == "ready")
            selection = digest(projections)
            if selection not in coverage_cache:
                coverage_cache[selection] = repo._coverage_for_members(filtered)
            scope = dict(revision_id=config["revision_id"], admission=revision["admission"],
                         enumeration_complete=revision["enumeration_complete"],
                         coverage=coverage_cache[selection], projection_selection=selection,
                         predicate={k: case[k] for k in ("query", "mode", "filters")},
                         representation="text_en", lens="lexical/v1")
            query = f'''FOR e IN text_view SEARCH {predicates[case["mode"]]}
OPTIONS {{waitForSync: true}} FILTER e.projection_id IN @projections
LET score = BM25(e) SORT score DESC, e.artifact_id ASC, e.ordinal ASC
LIMIT @cap RETURN {{artifact_id:e.artifact_id,projection_id:e.projection_id,
ordinal:e.ordinal,page:e.page,text:e.text,score:score}}'''
            rows = list(repo._db.aql.execute(query, bind_vars=dict(query=case["query"],
                        projections=projections, cap=config["match_cap"] + 1), max_runtime=10))
            if len({address(r) for r in rows}) != len(rows):
                raise ValueError("duplicate evidence addresses")
            for row in rows:
                if membership[row["artifact_id"]]["projection_id"] != row["projection_id"]:
                    raise ValueError("match outside selected membership")
            complete = len(rows) <= config["match_cap"]
            scope.update(matched_passages=len(rows) if complete else None,
                         matched_artifacts=len({r["artifact_id"] for r in rows}) if complete else None,
                         count_kind="exact" if complete else "incomplete")
            item.update(scope=scope, rows=rows, complete=complete)
        except Exception as error:
            # Preserve a bounded failure without leaking connection credentials in error text.
            item["error"] = type(error).__name__
    after = repo._observe_index_generation()
    capture.update(index_after=after, index_stable=before["generation_id"] == after["generation_id"],
                   finished_at=datetime.now(UTC).isoformat())
    return capture


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=Path(__file__).with_name("cases.json"))
    parser.add_argument("--capture", type=Path, help="Replay saved capture; no database access")
    parser.add_argument("--output", type=Path, required=True, help="New owner-local directory")
    args = parser.parse_args()
    config = json.loads(args.cases.read_text())
    args.output.mkdir(parents=True, exist_ok=False)
    capture = json.loads(args.capture.read_text()) if args.capture else capture_live(config)
    if capture["config_sha256"] != digest(config):
        raise ValueError("capture does not match case sheet")
    (args.output / "capture.json").write_bytes(encoded(capture))
    results, responses = compare(capture, config)
    results.update(config_sha256=digest(config), capture_sha256=digest(capture),
                   index_generation=capture["index_before"]["generation_id"],
                   index_stable=capture["index_stable"])
    (args.output / "results.json").write_bytes(encoded(results))
    for case, payloads in responses.items():
        for name, payload in payloads.items():
            (args.output / f"{case}-{name}.json").write_bytes(encoded(payload))
    print(json.dumps({r["id"]: r["status"] for r in results["cases"]}), flush=True)


if __name__ == "__main__":
    main()
