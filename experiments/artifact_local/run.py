"""Fixed, builder-informed rehearsal of existing artifact-local navigation."""
import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from tampu.service import Service, compact_json


def wire(value):
    return compact_json(value).encode("utf-8")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def navigate(service, case, config):
    """Navigation receives no assessed ordinals, target pages, or source texts."""
    calls = []

    def call(operation, **arguments):
        assert len(calls) < config["calls_per_case"]
        arguments["byte_budget"] = config["byte_budget"]
        response = getattr(service, operation)(**arguments)
        assert len(wire(response)) <= config["byte_budget"]
        calls.append(dict(operation=operation, arguments=arguments, response=response))
        return response

    for query in case["queries"]:
        found = call("search", collection=config["collection"], revision=config["revision_id"],
                     intent=case["task"], filters={"artifact_id": case["artifact_id"]},
                     limit=1, **query)
        if found["status"] != "ok" or not found["result"]["hits"]:
            continue
        result, hit = found["result"], found["result"]["hits"][0]
        context = dict(journey_id=result["journey_id"], node_id=result["node_id"])
        if hit.get("evidence_handle"):
            call("inspect", **context, evidence_handle=hit["evidence_handle"], slice_chars=4000)
        if isinstance(hit.get("physical_page"), int):
            call("inspect", **context, artifact_id=hit["artifact_id"],
                 page=hit["physical_page"] + 1, limit=20)
    return calls


def assess(record, config):
    output = dict(index_stable=record["index_stable"], cases=[])
    for case, captured in zip(config["cases"], record["cases"], strict=True):
        assert case["id"] == captured["id"]
        delivered, calls = [], []
        for number, call in enumerate(captured["calls"], 1):
            response, args = call["response"], call["arguments"]
            nbytes = len(wire(response))
            assert nbytes <= config["byte_budget"]
            summary = dict(call=number, operation=call["operation"], status=response["status"],
                           bytes=nbytes, response_sha256=sha(wire(response)),
                           omissions=response.get("omissions", []))
            if call["operation"] == "search":
                summary["query"] = args["query"]
            if "page" in args:
                summary["requested_page"] = args["page"]
            result = response.get("result", {})
            summary["returned_pages"] = sorted({r["physical_page"] for r in result.get("hits", [])
                                               if r.get("physical_page") is not None})
            evidence = result.get("evidence")
            if evidence:
                assert evidence["artifact_id"] == case["artifact_id"]
                assert evidence["projection_id"] == captured["projection_id"]
                delivered.append(dict(call=number, ordinal=evidence["ordinal"],
                                      page=evidence["physical_page"], text=evidence["text"],
                                      start=evidence["character_range"][0]))
            for element in result.get("elements", []):
                assert result["artifact"]["artifact_id"] == case["artifact_id"]
                delivered.append(dict(call=number, ordinal=element["ordinal"],
                                      page=element["physical_page"], text=element["extract"], start=0))
            calls.append(summary)
        probes = []
        for probe in case["assessment_probes"]:
            assert probe["projection_id"] == captured["projection_id"]
            matches = [r for r in delivered if r["ordinal"] == probe["ordinal"] and r["page"] == probe["page"]]
            full = [r for r in matches if r["start"] == 0 and sha(r["text"].encode()) == probe["text_sha256"]]
            probes.append({**probe, "address_visible": bool(matches), "whole_probe_visible": bool(full),
                           "calls": [r["call"] for r in matches]})
        total = sum(c["bytes"] for c in calls)
        assert len(calls) <= config["calls_per_case"]
        assert total <= config["calls_per_case"] * config["byte_budget"]
        output["cases"].append(dict(id=case["id"],
            status="observed" if record["index_stable"] else "inconclusive",
            call_count=len(calls), response_bytes=total, calls=calls, probes=probes,
            inspected=[{k: r[k] for k in ("call", "ordinal", "page")} for r in delivered]))
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replay", type=Path)
    args = parser.parse_args()
    config = json.loads(Path(__file__).with_name("cases.json").read_text())
    args.output.mkdir(parents=True, exist_ok=False)
    if args.replay:
        record = json.loads(args.replay.read_text())
    else:
        from tampu.config import load_config
        from tampu.repository import Repository

        repo = Repository(load_config(), initialize=False)
        repo.resolve_revision(config["collection"], config["revision_id"])
        members = {m["artifact_id"]: m for m in repo.members(config["revision_id"])}
        before = repo._observe_index_generation()
        record = dict(config_sha256=sha(wire(config)), started_at=datetime.now(UTC).isoformat(),
                      index_before=before, cases=[])
        for case in config["cases"]:
            print("Navigating " + case["id"], flush=True)
            service = Service(repo, trace_path=args.output / "service-trace.jsonl")
            inputs = {k: case[k] for k in ("id", "artifact_id", "task", "queries")}
            limits = {k: config[k] for k in ("collection", "revision_id", "calls_per_case", "byte_budget")}
            calls = navigate(service, inputs, limits)
            record["cases"].append(dict(id=case["id"], calls=calls,
                                        projection_id=members[case["artifact_id"]]["projection_id"]))
        after = repo._observe_index_generation()
        record.update(index_after=after, index_stable=before["generation_id"] == after["generation_id"],
                      finished_at=datetime.now(UTC).isoformat())
    assert record["config_sha256"] == sha(wire(config))
    (args.output / "record.json").write_bytes(wire(record))
    summary = assess(record, config)
    summary.update(record_sha256=sha(wire(record)), config_sha256=sha(wire(config)))
    (args.output / "results.json").write_bytes(wire(summary))
    print(json.dumps({c["id"]: dict(calls=c["call_count"], bytes=c["response_bytes"],
          whole_probes=sum(p["whole_probe_visible"] for p in c["probes"])) for c in summary["cases"]}))


if __name__ == "__main__":
    main()
