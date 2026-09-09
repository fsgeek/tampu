"""Compact owner-local observations without copying paper bytes or full traces."""

import argparse
import collections
import hashlib
import json
from pathlib import Path

from tampu.config import load_config
from tampu.repository import Repository


def compact(v):
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(p, v):
    p.write_text(json.dumps(v, ensure_ascii=False, indent=2) + "\n")


def audit_run(path):
    summary = json.loads((path / "summary.json").read_text())
    events = [
        json.loads(x)
        for x in (path / "events.jsonl").read_text().splitlines()
        if x.strip()
    ]
    items = {e["item"]["id"]: e["item"] for e in events if "item" in e}
    traces = []
    if (path / "service-trace.jsonl").exists():
        traces = [
            json.loads(x)
            for x in (path / "service-trace.jsonl").read_text().splitlines()
            if x.strip()
        ]
    calls = []
    warnings = []
    for item in items.values():
        if item.get("type") == "error":
            warnings.append(item.get("message"))
        if item.get("type") != "mcp_tool_call":
            continue
        call = {
            "tool": item["tool"],
            "status": item.get("status"),
            "transport_error": item.get("error"),
            "request_bytes": len(compact(item["arguments"]).encode()),
            "mcp_result_json_bytes": len(compact(item.get("result")).encode()),
        }
        result = item.get("result")
        if result:
            content = result.get("content", [])
            assert (
                len(content) == 1
                and content[0]["type"] == "text"
                and not result.get("structuredContent")
            )
            text = content[0]["text"]
            response = json.loads(text)
            size = len(text.encode())
            assert size <= item["arguments"].get("byte_budget", 8192)
            matching = [
                e
                for e in traces
                if e["operation"] == item["tool"] and e["response"] == response
            ]
            assert matching
            call.update(
                {
                    "application_response_bytes": size,
                    "application_status": response["status"],
                    "application_error": response.get("error", {}).get("code"),
                    "within_requested_budget": True,
                    "matches_service_trace": True,
                }
            )
        calls.append(call)
    completed = any(e.get("type") == "turn.completed" for e in events)
    failed = any(e.get("type") == "turn.failed" for e in events)
    actual_final = (
        bool(summary.get("has_final_assessment"))
        and completed
        and not failed
        and summary.get("stop_reason") is None
        and summary["exit_code"] == 0
    )
    summary = {
        **summary,
        "original_summary_has_final_assessment": summary.get("has_final_assessment"),
        "has_final_assessment": actual_final,
        "turn_completed_observed": completed,
    }
    return {
        "local_path": str(path),
        "summary": {
            k: v for k, v in summary.items() if k not in ["files", "source_after"]
        },
        "source_commit": summary["source_after"]["commit"],
        "calls": calls,
        "operation_counts": dict(collections.Counter(c["tool"] for c in calls)),
        "application_response_bytes": sum(
            c.get("application_response_bytes", 0) for c in calls
        ),
        "mcp_result_json_bytes": sum(c.get("mcp_result_json_bytes", 0) for c in calls),
        "tool_schema_json_bytes": (path / "tool-schemas.json").stat().st_size
        if (path / "tool-schemas.json").exists()
        else 0,
        "events_file_bytes": (path / "events.jsonl").stat().st_size,
        "cli_warnings": warnings,
        "accounting_limits": "Application JSON bytes exclude MCP wrappers. Compact serialized result wrapper size is an observed framing proxy, not wire bytes. Pretty tools/list schema bytes are separate. Cumulative model input includes cached repeated context, not unique evidence.",
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--local", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    out = a.output
    out.mkdir(parents=True, exist_ok=True)
    originals = {
        name: audit_run(a.local / "consumers" / name)
        for name in [
            "eviction-r0",
            "legible-r0",
            "eviction-r1",
            "eviction-r2",
            "legible-r2",
        ]
    }
    write(out / "original-consumer-metrics.json", originals)
    assessments = out / "assessments"
    assessments.mkdir(exist_ok=True)
    for name in originals:
        path = a.local / "consumers" / name
        src = (
            path / "prior-final-only.txt"
            if (path / "prior-final-only.txt").exists()
            else path / "assessment.txt"
        )
        suffix = (
            ".txt"
            if originals[name]["summary"]["has_final_assessment"]
            else "-progress-only.txt"
        )
        (assessments / (name + suffix)).write_bytes(src.read_bytes())
    comparisons = {
        name.name: audit_run(name)
        for name in (a.local / "comparison-consumers").iterdir()
        if (name / "summary.json").exists()
    }
    assert len(comparisons) == 16
    write(out / "comparison-metrics.json", comparisons)
    write(
        out / "comparison-responses.json",
        {
            name: (
                a.local / "comparison-consumers" / name / "assessment.txt"
            ).read_text()
            for name in comparisons
        },
    )
    publications = [
        json.loads((a.local / "growth" / f"r{i}-publication.json").read_text())
        for i in range(3)
    ]
    assert [p["revision"]["counts"]["artifacts"] for p in publications] == [
        160,
        320,
        473,
    ]
    write(out / "publications.json", publications)
    # Reopen the old revision, selected projections and original backing files after r2.
    repo = Repository(load_config(), initialize=False)
    baseline = json.loads(
        (a.local / "growth/r0-earlier-evidence-baseline.json").read_text()
    )
    checked = []
    for e in baseline["evidence"]:
        members = repo.members(e["revision_id"])
        member = next(m for m in members if m["artifact_id"] == e["artifact_id"])
        assert member["projection_id"] == e["projection_id"]
        repo.read_projection(e["projection_id"], verify_bytes=True)
        files = {
            label: digest(repo.store / v["path"]) for label, v in e["files"].items()
        }
        assert all(files[label] == v["sha256"] for label, v in e["files"].items())
        checked.append(
            {
                "artifact_id": e["artifact_id"],
                "revision_id": e["revision_id"],
                "projection_id": e["projection_id"],
                "backing_sha256": files,
                "old_membership_and_projection_verified": True,
            }
        )
    write(
        out / "old-evidence-after-growth.json",
        {
            "current_revision": repo.resolve_revision("research", None)["revision_id"],
            "checks": checked,
            "historical_scores_reexecuted": False,
        },
    )
    for source, target in [
        ("extraction/summary.json", "extraction-pilot.json"),
        ("adapter-pilot-poppler.json", "poppler-adapter-pilot.json"),
        ("full-extraction/aggregate-corrected.json", "full-extraction.json"),
        ("growth/r0-code-attribution-note.json", "r0-attribution-limitation.json"),
        ("path-pilot-final-regression.json", "path-pilot-final-regression.json"),
        ("task4-diagnostics/failed-attempt.json", "diagnostic-failed-attempt.json"),
        ("task4-diagnostics-corrected/summary.json", "diagnostics.json"),
    ]:
        write(out / target, json.loads((a.local / source).read_text()))
    files = []
    for folder in [
        "consumers",
        "comparison-consumers",
        "task4-diagnostics",
        "task4-diagnostics-corrected",
        "growth",
        "extraction",
        "full-extraction",
        "zero-text-diagnosis",
    ]:
        for file in sorted((a.local / folder).rglob("*")):
            if file.is_file() and file.suffix not in [".pdf", ".png", ".pyc"]:
                files.append(
                    {
                        "owner_local_path": str(file),
                        "sha256": digest(file),
                        "bytes": file.stat().st_size,
                    }
                )
    write(
        out / "owner-local-evidence-manifest.json",
        {
            "files": files,
            "policy": "Full source-bearing evidence stays owner-local. Hashes identify bytes, not semantic validity.",
        },
    )
    print(
        json.dumps(
            {
                "originals": len(originals),
                "comparisons": len(comparisons),
                "old_artifacts_verified": len(checked),
                "output": str(out),
            }
        )
    )


if __name__ == "__main__":
    main()
