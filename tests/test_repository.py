from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tampu.config import load_config
from tampu.errors import TampuError
from tampu.repository import Repository


def write_pdf(root: Path, name: str, body: str) -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(("%PDF-1.4\n" + body).encode())
    return path


@pytest.fixture
def fake_extraction(monkeypatch):
    failures: set[str] = set()

    def extract(artifact, store, *, profile, timeout=300, image=None):
        artifact_path = Path(store) / artifact["store_path"]
        text = artifact_path.read_text(errors="ignore").split("\n", 1)[-1]
        projection_id = hashlib.sha256(
            f"{artifact['artifact_id']}:{profile}".encode()
        ).hexdigest()
        elements_path = Path("elements") / f"{projection_id}.json"
        raw_path = Path("raw") / f"{projection_id}.json"
        (Path(store) / elements_path).parent.mkdir(parents=True, exist_ok=True)
        (Path(store) / raw_path).parent.mkdir(parents=True, exist_ok=True)
        failed = artifact["artifact_id"] in failures
        texts = text.split("|ELEMENT|")
        elements = (
            []
            if failed
            else [
                {
                    "ordinal": ordinal,
                    "original_element_id": f"page-{ordinal + 1}",
                    "type": "Page",
                    "text": element_text,
                    "page": ordinal + 1,
                    "coordinates": None,
                }
                for ordinal, element_text in enumerate(texts)
            ]
        )
        (Path(store) / elements_path).write_text(json.dumps(elements))
        (Path(store) / raw_path).write_text("{}")
        return {
            "projection_id": projection_id,
            "artifact_id": artifact["artifact_id"],
            "recipe": {
                "profile": profile,
                "output_sha256": "unused",
                "elements_sha256": "unused",
            },
            "status": "failed" if failed else "ready",
            "raw_path": raw_path.as_posix(),
            "elements_path": elements_path.as_posix(),
            "coverage": {
                "pages_total": 0 if failed else 1,
                "pages_with_text": 0 if failed or not text else 1,
                "elements": len(elements),
            },
            "losses": [{"code": "test_failure"}] if failed else [],
            "elapsed_seconds": 0.01,
        }

    monkeypatch.setattr("tampu.repository.extract_artifact", extract)
    return failures


def test_load_config_validates_required_fields_without_exposing_secret(tmp_path: Path):
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps({"endpoint": "http://localhost:8529", "password": "hush"})
    )
    with pytest.raises(TampuError) as raised:
        load_config(path)
    assert raised.value.code == "invalid_configuration"
    assert "hush" not in str(raised.value)


def test_ingest_deduplicates_artifacts_and_preserves_revision_membership(
    repository_config, fake_extraction, tmp_path
):
    root = tmp_path / "source"
    write_pdf(root, "a.pdf", "alpha quorum")
    write_pdf(root, "copy.pdf", "alpha quorum")
    repo = Repository(repository_config)
    first = repo.ingest("papers", root, profile="poppler")
    assert first["counts"] == {"sources": 2, "artifacts": 1, "ready": 1, "failed": 0}
    assert len(repo.members(first["revision_id"])) == 1
    write_pdf(root, "b.pdf", "beta lease")
    second = repo.ingest("papers", root, profile="poppler")
    assert {m["artifact_id"] for m in repo.members(first["revision_id"])} != {
        m["artifact_id"] for m in repo.members(second["revision_id"])
    }


def test_reconciliation_reports_add_replace_remove_and_keeps_old_evidence(
    repository_config, fake_extraction, tmp_path
):
    root = tmp_path / "source"
    write_pdf(root, "keep.pdf", "stable evidence")
    write_pdf(root, "replace.pdf", "old passage")
    write_pdf(root, "remove.pdf", "departing")
    repo = Repository(repository_config)
    first = repo.ingest("papers", root, profile="poppler")
    old_projection = next(
        m["projection_id"]
        for m in repo.members(first["revision_id"])
        if "replace.pdf" in m["aliases"]
    )
    (root / "remove.pdf").unlink()
    write_pdf(root, "replace.pdf", "new passage")
    write_pdf(root, "added.pdf", "arrival")
    second = repo.ingest("papers", root, profile="poppler")
    assert second["changes"]["added"] == ["added.pdf"]
    assert second["changes"]["removed"] == ["remove.pdf"]
    assert second["changes"]["replaced"] == ["replace.pdf"]
    assert repo.read_projection(old_projection)["status"] == "ready"


def test_failed_projection_is_visible_as_partial_coverage_but_not_searchable(
    repository_config, fake_extraction, tmp_path
):
    root = tmp_path / "source"
    failed_path = write_pdf(root, "failed.pdf", "hidden needle")
    failed_id = hashlib.sha256(failed_path.read_bytes()).hexdigest()
    fake_extraction.add(failed_id)
    repo = Repository(repository_config)
    revision = repo.ingest("papers", root, profile="poppler")
    result = repo.search_candidates(
        revision["revision_id"], "lexical/v1", "needle", "any_terms", {}
    )
    assert result["count"] == 0
    assert result["coverage"]["failed_artifacts"] == 1
    assert result["coverage"]["pages_unknown"] == 1


def test_lexical_modes_choose_max_element_and_stable_artifact_ties(
    repository_config, fake_extraction, tmp_path
):
    root = tmp_path / "source"
    write_pdf(
        root,
        "a.pdf",
        "alpha noise noise noise noise noise noise noise|ELEMENT|alpha alpha beta exact phrase",
    )
    write_pdf(root, "b.pdf", "alpha beta")
    write_pdf(root, "c.pdf", "alpha|ELEMENT|noise beta")
    write_pdf(root, "d.pdf", "alpha tie unique-d")
    write_pdf(root, "e.pdf", "alpha tie unique-e")
    repo = Repository(repository_config)
    revision = repo.ingest("papers", root, profile="poppler")
    any_result = repo.search_candidates(
        revision["revision_id"], "lexical/v1", "alpha", "any_terms", {}
    )
    assert any_result["count"] == 5
    best_a = next(hit for hit in any_result["candidates"] if "a.pdf" in hit["aliases"])
    assert best_a["evidence"]["ordinal"] == 1
    tied = [
        hit
        for hit in any_result["candidates"]
        if hit["aliases"] in (["d.pdf"], ["e.pdf"])
    ]
    assert tied[0]["score"] == tied[1]["score"]
    assert [hit["artifact_id"] for hit in tied] == sorted(
        hit["artifact_id"] for hit in tied
    )
    assert (
        repo.search_candidates(
            revision["revision_id"], "lexical/v1", "alpha beta", "all_terms", {}
        )["count"]
        == 2
    )
    assert (
        repo.search_candidates(
            revision["revision_id"], "lexical/v1", "exact phrase", "phrase", {}
        )["count"]
        == 1
    )


def test_metadata_and_temporal_filters_keep_unknowns_distinct(
    repository_config, fake_extraction, tmp_path
):
    root = tmp_path / "source"
    one = write_pdf(root, "group/one.pdf", "alpha")
    two = write_pdf(root, "two.pdf", "beta")
    one_id = hashlib.sha256(one.read_bytes()).hexdigest()
    two_id = hashlib.sha256(two.read_bytes()).hexdigest()
    repo = Repository(repository_config)
    revision = repo.ingest(
        "papers",
        root,
        profile="poppler",
        metadata={
            one_id: {
                "work_id": {"value": "work:1", "origin": "fixture"},
                "publication_status": {"value": "published", "origin": "fixture"},
                "publication_date": {
                    "value": "2024-03",
                    "origin": "fixture",
                    "precision": "month",
                },
            }
        },
    )
    rid = revision["revision_id"]
    assert (
        repo.search_candidates(rid, "metadata/v1", "", "filter", {"work_id": "work:1"})[
            "count"
        ]
        == 1
    )
    missing = repo.search_candidates(
        rid, "metadata/v1", "", "filter", {"missing": "publication_date"}
    )
    assert [x["artifact_id"] for x in missing["candidates"]] == [two_id]
    temporal = repo.search_candidates(
        rid,
        "temporal/v1",
        "",
        "filter",
        {"field": "publication_date", "from": "2024-01-01", "to": "2024-12-31"},
    )
    assert temporal["count"] == 1
    assert temporal["unknown_count"] == 1


def test_metadata_replacement_and_omission_semantics(
    repository_config, fake_extraction, tmp_path
):
    root = tmp_path / "source"
    path = write_pdf(root, "one.pdf", "alpha")
    artifact_id = hashlib.sha256(path.read_bytes()).hexdigest()
    repo = Repository(repository_config)
    repo.ingest(
        "papers",
        root,
        profile="poppler",
        metadata={artifact_id: {"title": {"value": "First", "origin": "fixture"}}},
    )
    second = repo.ingest("papers", root, profile="poppler")
    assert (
        repo.members(second["revision_id"])[0]["metadata"]["title"]["value"] == "First"
    )
    third = repo.ingest(
        "papers",
        root,
        profile="poppler",
        metadata={artifact_id: {"authors": {"value": ["A"], "origin": "fixture"}}},
    )
    assert "title" not in repo.members(third["revision_id"])[0]["metadata"]


def test_rejects_store_inside_root_and_second_root(
    repository_config, fake_extraction, tmp_path
):
    root = tmp_path / "source"
    write_pdf(root, "one.pdf", "alpha")
    inside = dict(repository_config, store=str(root / ".tampu"))
    with pytest.raises(TampuError, match="store") as raised:
        Repository(inside).ingest("papers", root, profile="poppler")
    assert raised.value.code == "invalid_configuration"
    repo = Repository(repository_config)
    repo.ingest("papers", root, profile="poppler")
    other = tmp_path / "other"
    write_pdf(other, "two.pdf", "beta")
    with pytest.raises(TampuError) as raised:
        repo.ingest("papers", other, profile="poppler")
    assert raised.value.code == "collection_root_mismatch"


def test_unknown_revision_and_missing_backing_file_are_typed(
    repository_config, fake_extraction, tmp_path
):
    repo = Repository(repository_config)
    with pytest.raises(TampuError) as raised:
        repo.resolve_revision("papers", "missing")
    assert raised.value.code == "revision_not_ready"
    root = tmp_path / "source"
    write_pdf(root, "one.pdf", "alpha")
    revision = repo.ingest("papers", root, profile="poppler")
    projection = repo.read_projection(
        repo.members(revision["revision_id"])[0]["projection_id"]
    )
    (Path(repository_config["store"]) / projection["elements_path"]).unlink()
    with pytest.raises(TampuError) as raised:
        repo.read_projection(projection["projection_id"])
    assert raised.value.code == "missing_evidence"


def test_failed_publication_keeps_previous_current_pointer(
    repository_config, fake_extraction, tmp_path, monkeypatch
):
    root = tmp_path / "source"
    write_pdf(root, "one.pdf", "alpha")
    repo = Repository(repository_config)
    first = repo.ingest("papers", root, profile="poppler")
    write_pdf(root, "two.pdf", "beta")

    def fail(_memberships):
        raise TampuError(
            "storage_unavailable", "Search indexing did not become visible."
        )

    monkeypatch.setattr(repo, "_verify_visibility", fail)
    with pytest.raises(TampuError):
        repo.ingest("papers", root, profile="poppler")
    assert repo.resolve_revision("papers", None)["revision_id"] == first["revision_id"]


def test_concurrent_publication_cannot_overwrite_newer_pointer(
    repository_config, fake_extraction, tmp_path
):
    root = tmp_path / "source"
    write_pdf(root, "one.pdf", "alpha")
    repo = Repository(repository_config)
    first = repo.ingest("papers", root, profile="poppler")
    staged = "staged-conflict"
    repo._db.collection("revisions").insert(
        {
            "_key": staged,
            "revision_id": staged,
            "collection": "papers",
            "state": "staged",
        }
    )
    with pytest.raises(TampuError) as raised:
        repo._publish("papers", str(root.resolve()), staged, "stale-parent")
    assert raised.value.code == "publication_conflict"
    assert repo.resolve_revision("papers", None)["revision_id"] == first["revision_id"]
    assert repo._db.collection("revisions").get(staged)["state"] == "staged"


def test_candidate_cap_never_returns_a_partial_exact_count(
    repository_config, fake_extraction, tmp_path, monkeypatch
):
    root = tmp_path / "source"
    write_pdf(root, "one.pdf", "alpha one")
    write_pdf(root, "two.pdf", "alpha two")
    repo = Repository(repository_config)
    revision = repo.ingest("papers", root, profile="poppler")
    monkeypatch.setattr("tampu.repository._CAP", 1)
    with pytest.raises(TampuError) as raised:
        repo.search_candidates(
            revision["revision_id"], "lexical/v1", "alpha", "any_terms", {}
        )
    assert raised.value.code == "candidate_limit"
