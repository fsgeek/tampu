import hashlib
import importlib.util
from pathlib import Path

import pytest


SPEC = importlib.util.spec_from_file_location(
    "retrieval_grouping", Path(__file__).parents[1] / "experiments/retrieval_grouping/run.py"
)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def row(artifact, ordinal, score, text="evidence"):
    return dict(artifact_id=artifact, projection_id="p" + artifact,
                ordinal=ordinal, page=1, score=score, text=text)


def probe(r):
    return {**{k: r[k] for k in ("artifact_id", "projection_id", "ordinal", "page")},
            "required_chars": len(r["text"]),
            "text_sha256": hashlib.sha256(r["text"].encode()).hexdigest()}


def test_grouping_retains_best_with_deterministic_ties():
    rows = [row("b", 3, 8), row("a", 2, 9), row("a", 1, 9)]
    assert [(r["artifact_id"], r["ordinal"]) for r in audit.rank(rows, "grouped")] == [("a", 1), ("b", 3)]
    assert [r["ordinal"] for r in audit.rank(rows, "passage")] == [1, 2, 3]
    assert rows[0]["artifact_id"] == "b"  # no input mutation


def test_byte_budget_counts_utf8_and_never_skips_large_next_entry():
    rows = [row("a", 1, 3, "small"), row("b", 2, 2, "é" * 700), row("c", 3, 1, "small")]
    packed = audit.pack(rows, {}, "passage", budget=600)
    assert [h["artifact_id"] for h in packed["hits"]] == ["a"]
    assert len(audit.encoded(packed)) <= 600
    assert packed["omitted_entries"] == 2
    assert len(audit.encoded({"text": "é"})) > len(audit.encoded({"text": "e"}))


def test_limits_and_impossible_envelope():
    rows = [row(str(i), i, 1) for i in range(5)]
    assert len(audit.pack(rows, {}, "passage", limit=2)["hits"]) == 2
    with pytest.raises(ValueError, match="envelope"):
        audit.pack(rows, {"large": "x" * 9000}, "passage")


def test_attribution_separates_matching_grouping_capacity_and_clipping():
    first, second, late = row("a", 1, 9), row("a", 2, 8, "x" * 801), row("b", 1, 1)
    rows = [first, second, late]
    grouped = audit.pack(audit.rank(rows, "grouped"), {}, "grouped", limit=1)
    passage = audit.pack(audit.rank(rows, "passage"), {}, "passage", limit=2)
    result = audit.assess_probe(probe(second), rows, grouped, passage)
    assert result["grouped"]["status"] == "grouped_away"
    assert result["passage"]["status"] == "excerpt_clipped"
    assert result["global_rank"] == 2
    assert audit.assess_probe(probe(late), rows, grouped, passage)["grouped"]["status"] == "rank_or_capacity"
    missing = audit.assess_probe(probe(row("z", 1, 0)), rows, grouped, passage)
    assert missing["matched"] is False
    assert missing["passage"]["status"] == "not_matched"
    assert audit.assess_probe(probe(first), rows, grouped, passage)["grouped"]["status"] == "visible"


@pytest.mark.parametrize("stable,complete", [(False, True), (True, False)])
def test_incomplete_capture_cannot_produce_paired_conclusions(stable, complete):
    config = {"cases": [{"id": "case", "probes": []}]}
    capture = {"index_stable": stable, "cases": [{"id": "case", "complete": complete, "rows": []}]}
    results, responses = audit.compare(capture, config)
    assert results["cases"][0]["status"] == "inconclusive"
    assert responses == {}


def test_changed_probe_bytes_refuse_positive_attribution():
    r = row("a", 1, 1)
    p = probe(r)
    p["text_sha256"] = "wrong"
    with pytest.raises(ValueError, match="probe"):
        audit.assess_probe(p, [r], audit.pack([r], {}, "grouped"), audit.pack([r], {}, "passage"))
