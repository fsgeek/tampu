"""Fixed local diagnostic cases; never use the original consumer database."""

import argparse
import json
import shutil
import time
from pathlib import Path

from run import identity

from tampu.config import load_config
from tampu.repository import Repository
from tampu.service import Service

IMAGE = "downloads.unstructured.io/unstructured-io/unstructured@sha256:806726e3997d33bce9e32facd86c947b241101c58496f2774ad5f09f86e798bc"
S = "3bd6c331a38201a5ead0db2135e0067de43707131962a6314e2cf974755a1578"
L = "d2c7c7af6c801c3ef7657d282bfa8f1b5c6193a758bd74179cb7c5d0e423142e"
V2 = "267a676ecf034576a43dae4f773d169d9fcbed9275ee15287ab778b7bbf68f3f"
V3 = "12bb3bc4a937c115861c6585902d360fef4035ccd79669daa1254ee82e4ede5b"


def write(p, v):
    p.write_text(json.dumps(v, indent=2) + "\n")


def pdf(path, text):
    # Minimal genuine PDF for deterministic controlled lexical/reconciliation cases.
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length "
        + str(len(stream)).encode()
        + b" >>\nstream\n"
        + stream
        + b"\nendstream",
    ]
    data = b"%PDF-1.4\n"
    offsets = [0]
    for n, obj in enumerate(objs, 1):
        offsets.append(len(data))
        data += f"{n} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(data)
    data += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    data += b"".join(f"{off:010} 00000 n \n".encode() for off in offsets[1:])
    data += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    path.write_bytes(data)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    before = identity()
    config = load_config(a.config)
    runtime = load_config()
    assert config["database"] != runtime["database"]
    out = a.output
    out.mkdir(parents=True, exist_ok=False)
    repo = Repository(config)
    store = Path(runtime["store"])
    records = []
    start = time.monotonic()

    def ingest(name, root, profile="poppler", metadata=None):
        t = time.monotonic()
        r = repo.ingest(
            name,
            root,
            profile=profile,
            image=IMAGE if profile == "unstructured" else None,
            metadata=metadata,
        )
        records.append(
            {"collection": name, "revision": r, "wall_seconds": time.monotonic() - t}
        )
        write(out / "ingestion-records.json", records)
        return r

    def copy(aid, dst):
        shutil.copy2(store / "artifacts" / aid[:2] / f"{aid}.pdf", dst)

    root = out / "tiny"
    root.mkdir()
    for n, t in [
        ("keep", "stable known passage"),
        ("replace", "old red passage"),
        ("remove", "departing passage"),
    ]:
        pdf(root / f"{n}.pdf", t)
    first = ingest("tiny", root)
    pdf(root / "replace.pdf", "new blue passage")
    (root / "remove.pdf").unlink()
    pdf(root / "add.pdf", "arriving passage")
    second = ingest("tiny", root)
    assert (
        second["changes"]["added"] == ["add.pdf"]
        and second["changes"]["removed"] == ["remove.pdf"]
        and second["changes"]["replaced"] == ["replace.pdf"]
    )
    assert (
        repo.search_candidates(
            first["revision_id"], "lexical/v1", "old red passage", "phrase", {}
        )["count"]
        == 1
    )
    assert (
        repo.search_candidates(
            second["revision_id"], "lexical/v1", "old red passage", "phrase", {}
        )["count"]
        == 0
    )
    failure = out / "failure"
    failure.mkdir()
    (failure / "broken.pdf").write_bytes(
        b"%PDF-1.4\nDeliberately truncated processing-failure fixture.\n"
    )
    failed = ingest("failure", failure)
    assert failed["counts"]["failed"] == 1
    versions = out / "versions"
    versions.mkdir()
    copy(V2, versions / "v2.pdf")
    copy(V2, versions / "v2-copy.pdf")
    copy(V3, versions / "v3.pdf")
    metadata = json.loads(
        Path(
            "/home/tony/projects/tampu/tmp/prototype-readiness/curated-metadata.json"
        ).read_text()
    )
    metadata = {k: v for k, v in metadata.items() if k in [V2, V3]}
    for v in metadata.values():
        v["publication_date"]["precision"] = "day"
    vr = ingest("versions", versions, "unstructured", metadata)
    assert vr["counts"]["sources"] == 3 and vr["counts"]["artifacts"] == 2
    members = repo.members(vr["revision_id"])
    assert len({m["metadata"]["work_id"]["value"] for m in members}) == 1
    comparisons = out / "comparison-source"
    comparisons.mkdir()
    copy(S, comparisons / "short.pdf")
    copy(L, comparisons / "long.pdf")
    # CORFU is selected from the source inventory by its already recorded identifier.
    corfu = "e334015c41058d0906ec96718624a7009c4d75a8c7ce07ab4fed5d8208983a93"
    copy(corfu, comparisons / "corfu.pdf")
    cr = ingest("comparison", comparisons, "unstructured")
    s = Service(repo, trace_path=out / "service-trace.jsonl")
    observations = {}
    for name, query, filters, limit in [
        ("present", "Blind Oracle", {}, 1),
        ("absent", "tampuabsentpredicateqxz", {"artifact_id": S}, 1),
        ("alias", "PredictiveMarker", {"artifact_id": S}, 1),
        ("processing_gap", "shared log", {"artifact_id": corfu}, 1),
        ("alias_check", "Predictive Marker", {"artifact_id": S}, 1),
    ]:
        request = {
            "collection": "comparison",
            "revision": cr["revision_id"],
            "intent": "Owner diagnostic and frozen response development observation",
            "query": query,
            "mode": "phrase",
            "filters": filters,
            "limit": limit,
        }
        response = s.search(**request)
        assert response["status"] == "ok"
        item = {
            "request": request,
            "response": response,
            "timestamp": time.time(),
            "projection_records": [
                repo.read_projection(m["projection_id"], verify_bytes=True)
                for m in repo.members(cr["revision_id"])
                if not filters or m["artifact_id"] == filters["artifact_id"]
            ],
        }
        if name == "present":
            r = response["result"]
            assert r["full_count"] > r["returned_count"] >= 1
            inspection = s.inspect(
                journey_id=r["journey_id"],
                node_id=r["node_id"],
                artifact_id=S,
                ordinal=38,
                slice_chars=2400,
            )
            item["inspection_listing"] = inspection
            inspection = s.inspect(
                journey_id=r["journey_id"],
                node_id=r["node_id"],
                evidence_handle=inspection["result"]["elements"][0]["evidence_handle"],
                slice_chars=2400,
            )
            item["inspection"] = inspection
            assert "BlindOracle" in inspection["result"]["evidence"]["text"]
            assert inspection["status"] == "ok"
        observations[name] = item
        write(out / "observations.json", observations)
    assert observations["absent"]["response"]["result"]["full_count"] == 0
    absent_result = observations["absent"]["response"]["result"]
    negative = s.finish(
        journey_id=absent_result["journey_id"],
        node_id=absent_result["node_id"],
        kind="bounded_negative",
        statement="The exact text_en phrase tampuabsentpredicateqxz has no lexical match in this pinned short-paper projection; no semantic absence claim.",
        semantic_absence=False,
    )
    assert negative["status"] == "ok"
    observations["bounded_negative_finding"] = negative
    assert (
        observations["alias"]["response"]["result"]["full_count"] == 0
        and observations["alias_check"]["response"]["result"]["full_count"] == 1
    )
    assert (
        observations["processing_gap"]["response"]["result"]["coverage"][
            "pages_with_text"
        ]
        == 0
    )
    assert (
        observations["processing_gap"]["response"]["result"]["coverage"]["pages_total"]
        == 24
    )
    # A real misleading broad search followed by an exact alias refinement.
    broad = s.search(
        collection="comparison",
        intent="Recovery diagnostic",
        query="eviction prediction",
        limit=1,
    )
    recover = s.search(
        journey_id=broad["result"]["journey_id"],
        query="Predictive Marker",
        mode="phrase",
        filters={"artifact_id": S},
    )
    assert recover["result"]["full_count"] == 1
    observations["recovery"] = {
        "initial": broad,
        "refined": recover,
        "classification": "builder-authored navigation diagnostic, not consumer success",
    }
    gaproot = out / "processing-change"
    gaproot.mkdir()
    copy(corfu, gaproot / "corfu.pdf")
    empty = ingest("processing-change", gaproot, "unstructured")
    changed = ingest("processing-change", gaproot, "poppler")
    old = repo.members(empty["revision_id"])[0]
    new = repo.members(changed["revision_id"])[0]
    assert (
        old["artifact_id"] == new["artifact_id"]
        and old["projection_id"] != new["projection_id"]
    )
    assert len(changed["changes"]["processing_changed"]) == 1
    assert (
        repo.read_projection(old["projection_id"], verify_bytes=True)["coverage"][
            "pages_with_text"
        ]
        == 0
    )
    assert (
        repo.read_projection(new["projection_id"], verify_bytes=True)["coverage"][
            "pages_with_text"
        ]
        == 24
    )
    assert (
        repo.search_candidates(
            changed["revision_id"], "lexical/v1", "shared log", "phrase", {}
        )["count"]
        == 1
    )
    write(out / "observations.json", observations)
    write(
        out / "summary.json",
        {
            "database": config["database"],
            "source_before": before,
            "source_after": identity(),
            "wall_seconds": time.monotonic() - start,
            "records": records,
            "assertions": "add/replace/remove; pinned old passage; explicit failed projection; aliases distinct from same-work versions; present/count; bounded lexical zero; alias recovery; CORFU processing-change and old-byte verification passed",
            "source_checks": "Separate builder passage review required; assertions do not establish semantic completeness",
            "corfu": corfu,
        },
    )
    print(
        json.dumps(
            {
                "output": str(out),
                "records": len(records),
                "wall_seconds": time.monotonic() - start,
            }
        )
    )


if __name__ == "__main__":
    main()
