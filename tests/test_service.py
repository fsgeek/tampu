from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tampu.repository import Repository
from tampu.service import Service


class FakeRepository:
    def __init__(self, store: Path):
        self.store = store
        self.current_revision = "revision-1"
        self.search_calls: list[tuple] = []
        self._members = [
            {
                "revision_id": "revision-1",
                "artifact_id": f"artifact-{number}",
                "projection_id": f"projection-{number}",
                "projection_status": "ready",
                "aliases": [f"group/paper-{number}.pdf"],
                "source_mtime_ns": number,
                "source_mtimes_ns": {f"group/paper-{number}.pdf": number},
                "metadata": {
                    "title": {"value": f"Paper {number}", "origin": "fixture"},
                    **(
                        {
                            "publication_date": {
                                "value": "2024-03" if number == 0 else "2024",
                                "origin": "fixture",
                                "precision": "month" if number == 0 else "year",
                            }
                        }
                        if number < 2
                        else {}
                    ),
                    **(
                        {
                            "source_group": {
                                "value": "deliberate",
                                "origin": "fixture",
                            }
                        }
                        if number < 2
                        else {}
                    ),
                },
            }
            for number in range(3)
        ]
        elements = [
            "alpha café 東京 😀 evidence zero",
            "alpha café 東京 😀 evidence one",
            "alpha café 東京 😀 evidence two",
        ]
        for number, text in enumerate(elements):
            path = store / "elements" / f"projection-{number}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(
                    [
                        {
                            "ordinal": 0,
                            "original_element_id": f"element-{number}",
                            "type": "NarrativeText",
                            "text": text,
                            "page": number + 1,
                            "coordinates": None,
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            raw = store / "raw" / f"projection-{number}.json"
            raw.parent.mkdir(parents=True, exist_ok=True)
            raw.write_text("{}", encoding="utf-8")

    def describe(self, collection=None):
        if collection not in (None, "papers"):
            raise AssertionError("unexpected collection")
        return {
            "collections": [
                {
                    "name": "papers",
                    "root": "/owner/private/papers",
                    "current_revision": self.current_revision,
                }
            ],
            "lenses": ["lexical/v1", "metadata/v1", "temporal/v1"],
            "candidate_limit": 10_000,
            "query_timeout_seconds": 10,
        }

    def resolve_revision(self, collection, revision):
        selected = revision or self.current_revision
        return {
            "revision_id": selected,
            "collection": collection,
            "parent_revision": None,
            "state": "published",
            "observed_start": "2026-09-08T00:00:00Z",
            "observed_end": "2026-09-08T00:01:00Z",
            "enumeration_complete": True,
            "selection_digest": "selection-1",
            "aggregate_coverage": {
                "artifacts": 3,
                "ready_artifacts": 3,
                "failed_artifacts": 0,
                "pages_total": 3,
                "pages_with_text": 3,
                "blank_or_partial_artifacts": 0,
                "pages_unknown": 0,
            },
            "counts": {"sources": 3, "artifacts": 3, "ready": 3, "failed": 0},
            "changes": {
                "added": [],
                "removed": [],
                "replaced": [],
                "processing_changed": [],
            },
            "published_at": "2026-09-08T00:01:01Z",
        }

    def members(self, revision):
        return [dict(member, revision_id=revision) for member in self._members]

    def published_revisions(self, collection):
        return [
            self.resolve_revision(collection, "revision-1"),
            {
                **self.resolve_revision(collection, "revision-0"),
                "published_at": "2026-09-07T00:01:01Z",
            },
        ]

    def search_candidates(self, revision, lens, query, mode, filters):
        self.search_calls.append((revision, lens, query, mode, filters))
        candidates = [
            {
                "artifact_id": member["artifact_id"],
                "aliases": member["aliases"],
                "metadata": member["metadata"],
                "score": 3.0 - number,
                "evidence": {
                    "artifact_id": member["artifact_id"],
                    "projection_id": member["projection_id"],
                    "ordinal": 0,
                    "page": number + 1,
                    "start": 0,
                    "end": 31,
                },
                "text": f"alpha café 東京 😀 evidence {number}",
            }
            for number, member in enumerate(self._members)
            if query != "none"
        ]
        return {
            "revision_id": revision,
            "lens": lens,
            "query": query,
            "mode": mode,
            "filters": filters,
            "count": len(candidates),
            "count_kind": "exact",
            "unknown_count": 0,
            "candidates": candidates,
            "coverage": {
                "artifacts": 3,
                "ready_artifacts": 3,
                "failed_artifacts": 0,
                "pages_total": 3,
                "pages_with_text": 3,
                "blank_or_partial_artifacts": 0,
                "pages_unknown": 0,
            },
            "selection": "maximum_element_bm25_then_artifact_id",
            "index_generation": {
                "generation_id": "generation-1",
                "projection_count": 3,
                "element_count": 3,
                "observed_at": "2026-09-08T00:01:02Z",
            },
            "index_generation_before": {
                "generation_id": "generation-1",
                "projection_count": 3,
                "element_count": 3,
                "observed_at": "2026-09-08T00:01:02Z",
            },
            "index_generation_stable": True,
            "lens_config": {
                "lens": "lexical/v1",
                "revision_scope": "pinned_projection_selection",
                "analyzer": "text_en",
                "mode": mode,
                "artifact_score": "maximum_matching_element_bm25",
                "tie_breaker": "artifact_id",
            },
        }

    def read_projection(self, projection_id, **_options):
        number = int(projection_id.rsplit("-", 1)[1])
        return {
            "projection_id": projection_id,
            "artifact_id": f"artifact-{number}",
            "recipe": {
                "profile": "poppler",
                "timeout_seconds": 300,
                "output_sha256": "raw-digest",
                "elements_sha256": "element-digest",
            },
            "status": "ready",
            "raw_path": f"raw/{projection_id}.json",
            "elements_path": f"elements/{projection_id}.json",
            "coverage": {"pages_total": 1, "pages_with_text": 1, "elements": 1},
            "losses": [],
            "elapsed_seconds": 0.01,
        }


@pytest.fixture
def service(tmp_path: Path) -> Service:
    return Service(FakeRepository(tmp_path / "store"))


def encoded(value: dict) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def test_search_defaults_to_two_hits_and_count_only_is_exact(service: Service):
    result = service.search(
        collection="papers", intent="find alpha", query="alpha"
    )
    assert result["status"] == "ok"
    assert result["result"]["full_count"] == 3
    assert result["result"]["count_kind"] == "exact"
    assert result["result"]["returned_count"] == 2
    assert len(result["result"]["hits"]) == 2
    assert isinstance(result["result"]["continuation"], str)

    count_only = service.search(
        collection="papers", intent="count alpha", query="alpha", limit=0
    )
    assert count_only["result"]["full_count"] == 3
    assert count_only["result"]["returned_count"] == 0
    assert count_only["result"]["hits"] == []


def test_search_pins_revision_and_result_pagination_is_stable(service: Service):
    first = service.search(
        collection="papers", intent="find alpha", query="alpha", limit=1
    )["result"]
    repository = service.repository
    repository.current_revision = "revision-2"
    page = service.inspect(
        journey_id=first["journey_id"],
        node_id=first["node_id"],
        continuation=first["continuation"],
        limit=2,
    )
    assert page["result"]["revision_id"] == "revision-1"
    assert [hit["artifact_id"] for hit in page["result"]["hits"]] == [
        "artifact-1",
        "artifact-2",
    ]

    later = service.search(
        journey_id=first["journey_id"], query="new predicate", limit=0
    )
    assert later["result"]["revision_id"] == "revision-1"
    assert repository.search_calls[-1][0] == "revision-1"


def test_utf8_budget_counts_actual_bytes_and_keeps_scope(service: Service):
    result = service.search(
        collection="papers",
        intent="find unicode evidence",
        query="alpha",
        byte_budget=900,
    )
    assert len(encoded(result)) <= 900
    assert result["scope"]["revision_id"] == "revision-1"
    assert "omissions" in result


def test_budget_underfill_continues_at_first_undelivered_candidate(service: Service):
    first = service.search(
        collection="papers",
        intent="fit a small response",
        query="alpha",
        limit=2,
        byte_budget=900,
    )
    assert first["status"] == "ok"
    assert first["result"]["returned_count"] == 0
    delivered = {
        hit["evidence_handle"]
        for hit in first["result"]["hits"]
        if "evidence_handle" in hit
    }
    journey = service._journeys[first["result"]["journey_id"]]
    assert set(journey["evidence"]) == delivered
    page = service.inspect(
        journey_id=first["result"]["journey_id"],
        node_id=first["result"]["node_id"],
        continuation=first["result"]["continuation"],
        limit=1,
    )
    assert page["result"]["hits"][0]["artifact_id"] == "artifact-0"


def test_final_search_and_inspect_pages_gain_cursor_when_budget_underfills(
    service: Service,
):
    search = service.search(
        collection="papers",
        intent="final search page",
        query="alpha",
        limit=3,
        byte_budget=1300,
    )
    assert search["status"] == "ok"
    assert search["result"]["returned_count"] < 3
    assert isinstance(search["result"]["continuation"], str)
    next_search = service.inspect(
        journey_id=search["result"]["journey_id"],
        node_id=search["result"]["node_id"],
        continuation=search["result"]["continuation"],
        limit=3,
    )
    assert next_search["result"]["hits"][0]["artifact_id"] == "artifact-1"

    initial = service.search(
        collection="papers", intent="final inspect page", query="alpha", limit=1
    )["result"]
    final_page = service.inspect(
        journey_id=initial["journey_id"],
        node_id=initial["node_id"],
        continuation=initial["continuation"],
        limit=2,
        byte_budget=900,
    )
    assert final_page["result"]["returned_count"] < 2
    assert isinstance(final_page["result"]["continuation"], str)
    resumed = service.inspect(
        journey_id=initial["journey_id"],
        node_id=initial["node_id"],
        continuation=final_page["result"]["continuation"],
        limit=2,
    )
    assert resumed["result"]["hits"][0]["artifact_id"] == "artifact-2"


def test_budget_failure_does_not_create_or_modify_journey(service: Service):
    oversized = service.describe(byte_budget=32_769)
    assert oversized["error"]["code"] == "invalid_input"

    failed = service.search(
        collection="papers",
        intent="cannot fit",
        query="alpha",
        byte_budget=256,
    )
    assert failed["error"]["code"] == "budget_too_small"
    assert isinstance(failed["error"]["minimum_bytes"], int)
    assert failed["error"]["minimum_bytes"] > 256
    assert service.active_journey_count == 0

    created = service.search(
        collection="papers", intent="finish transaction", query="none", limit=0
    )["result"]
    failed_finish = service.finish(
        journey_id=created["journey_id"],
        kind="unresolved",
        statement="x" * 10_000,
        reason="y" * 10_000,
        release=True,
        byte_budget=256,
    )
    assert failed_finish["error"]["code"] == "budget_too_small"
    assert created["journey_id"] in service._journeys
    assert service._journeys[created["journey_id"]]["findings"] == []


def test_inspect_unicode_slice_and_continuation_authorize_only_node_members(
    service: Service,
):
    search = service.search(
        collection="papers", intent="inspect unicode", query="alpha", limit=1
    )["result"]
    evidence_handle = search["hits"][0]["evidence_handle"]
    first = service.inspect(
        journey_id=search["journey_id"],
        node_id=search["node_id"],
        evidence_handle=evidence_handle,
        start=6,
        end=13,
        slice_chars=4,
    )
    assert first["result"]["evidence"]["text"] == "café"
    assert first["result"]["evidence"]["character_range"] == [6, 10]
    continuation = first["result"]["evidence"]["continuation"]
    second = service.inspect(
        journey_id=search["journey_id"],
        node_id=search["node_id"],
        evidence_handle=continuation,
        slice_chars=10,
    )
    assert second["result"]["evidence"]["text"] == " 東京"

    denied = service.inspect(
        journey_id=search["journey_id"],
        node_id=search["node_id"],
        evidence_handle="not-a-handle",
    )
    assert denied["status"] == "error"
    assert denied["error"]["code"] == "missing_evidence"


def test_inspect_opens_unseen_candidate_by_artifact_page_and_ordinal(
    service: Service,
):
    search = service.search(
        collection="papers", intent="inspect later candidate", query="alpha", limit=1
    )["result"]
    opened = service.inspect(
        journey_id=search["journey_id"],
        node_id=search["node_id"],
        artifact_id="artifact-2",
        page=3,
        limit=1,
    )
    element = opened["result"]["elements"][0]
    assert element["ordinal"] == 0
    assert element["physical_page"] == 3
    assert element["printed_page"] is None
    assert isinstance(element["evidence_handle"], str)
    assert opened["result"]["artifact"]["metadata"]["title"]["value"] == "Paper 2"

    by_ordinal = service.inspect(
        journey_id=search["journey_id"],
        node_id=search["node_id"],
        artifact_id="artifact-2",
        ordinal=0,
        limit=1,
    )
    assert by_ordinal["result"]["elements"][0]["extract"].startswith("alpha café")

    denied = service.inspect(
        journey_id=search["journey_id"],
        node_id=search["node_id"],
        artifact_id="outside-node",
        page=1,
    )
    assert denied["error"]["code"] == "missing_evidence"


def test_finish_validates_inspected_evidence_zero_scope_and_semantic_absence(
    service: Service,
):
    positive = service.search(
        collection="papers", intent="support finding", query="alpha", limit=1
    )["result"]
    handle = positive["hits"][0]["evidence_handle"]
    premature = service.finish(
        journey_id=positive["journey_id"],
        kind="positive",
        statement="Alpha is discussed.",
        evidence_handles=[handle],
    )
    assert premature["error"]["code"] == "uninspected_evidence"
    inspected = service.inspect(
        journey_id=positive["journey_id"],
        node_id=positive["node_id"],
        evidence_handle=handle,
    )
    inspected_handle = inspected["result"]["evidence"]["handle"]
    supported = service.finish(
        journey_id=positive["journey_id"],
        kind="positive",
        statement="Alpha is discussed.",
        evidence_handles=[inspected_handle],
    )
    assert supported["result"]["machine_status"] == "structurally_validated"
    delivered = service._journeys[positive["journey_id"]]["evidence"][inspected_handle]
    assert [delivered["start"], delivered["end"]] == inspected["result"][
        "evidence"
    ]["character_range"]

    zero = service.search(
        collection="papers", intent="bound a negative", query="none", limit=0
    )["result"]
    negative = service.finish(
        journey_id=zero["journey_id"],
        kind="bounded_negative",
        statement="No candidates matched this predicate.",
        node_id=zero["node_id"],
    )
    assert negative["result"]["machine_status"] == "bounded_negative"
    assert negative["result"]["scope"]["count_kind"] == "exact"
    semantic = service.finish(
        journey_id=zero["journey_id"],
        kind="bounded_negative",
        statement="The concept is absent from every paper.",
        node_id=zero["node_id"],
        semantic_absence=True,
    )
    assert semantic["result"]["machine_status"] == "unresolved"


def test_expiry_capacity_release_and_errors_are_controlled(
    service: Service, monkeypatch
):
    created = service.search(
        collection="papers", intent="temporary", query="alpha", limit=0
    )["result"]
    service._journeys[created["journey_id"]]["expires_at"] = 0
    expired = service.search(journey_id=created["journey_id"], query="alpha")
    assert expired["error"] == {
        "code": "expired_journey",
        "message": "The journey has expired.",
    }

    releasable = service.search(
        collection="papers", intent="release me", query="none", limit=0
    )["result"]

    monkeypatch.setattr("tampu.service.MAX_STATE_BYTES", 1)
    capacity = service.search(
        collection="papers", intent="too large", query="alpha"
    )
    assert capacity["error"]["code"] == "journey_capacity"
    assert service.active_journey_count == 1

    released = service.finish(
        journey_id=releasable["journey_id"],
        kind="unresolved",
        statement="No conclusion.",
        reason="insufficient support",
        release=True,
    )
    assert released["result"]["released"] is True
    assert released["result"]["preserved"] is False
    assert service.active_journey_count == 0


def test_expired_journeys_are_reclaimed_before_capacity_check(
    service: Service, monkeypatch
):
    expired = service.search(
        collection="papers", intent="expire", query="alpha", limit=0
    )["result"]
    service._journeys[expired["journey_id"]]["expires_at"] = 0
    rejected = service.search(journey_id=expired["journey_id"], query="alpha")
    assert rejected["error"]["code"] == "expired_journey"
    monkeypatch.setattr(
        "tampu.service.MAX_STATE_BYTES", service._total_state_bytes() + 1
    )
    replacement = service.search(
        collection="papers", intent="replacement", query="none", limit=0
    )
    assert replacement["status"] == "ok"
    assert expired["journey_id"] not in service._journeys


def test_describe_facets_are_bounded_and_source_groups_require_tags(service: Service):
    description = service.describe(collection="papers")
    assert description["status"] == "ok"
    collection = description["result"]["collections"][0]
    assert collection["root"] == "owner_configured_source"
    assert collection["coverage"]["pages_with_text"] == 3
    assert collection["coverage"]["ready_does_not_mean_complete_text"] is True
    source_groups = collection["facets"]["source_group"]
    assert source_groups["values"] == [{"value": "deliberate", "artifacts": 2}]
    assert source_groups["unknown_artifacts"] == 1
    assert len(source_groups["values"]) <= 5
    assert collection["facets"]["asserted_publication_year"] == {
        "values": [{"value": "2024", "artifacts": 2}],
        "unknown_artifacts": 1,
        "omitted_values": 0,
        "count_unit": "artifacts",
        "source_group_requires_explicit_assertion": False,
    }
    assert collection["facets"]["processing_status"]["values"] == [
        {"value": "ready", "artifacts": 3}
    ]
    assert [item["revision_id"] for item in collection["revisions"]] == [
        "revision-1",
        "revision-0",
    ]
    first_revision_page = service.describe(
        collection="papers", revision_limit=1
    )["result"]["collections"][0]
    assert [item["revision_id"] for item in first_revision_page["revisions"]] == [
        "revision-1"
    ]
    second_revision_page = service.describe(
        collection="papers",
        revision_limit=1,
        revision_cursor=first_revision_page["revision_continuation"],
    )["result"]["collections"][0]
    assert [item["revision_id"] for item in second_revision_page["revisions"]] == [
        "revision-0"
    ]
    assert second_revision_page["revision_continuation"] is None
    lexical = description["result"]["lenses"]["lexical/v1"]
    metadata = description["result"]["lenses"]["metadata/v1"]
    temporal = description["result"]["lenses"]["temporal/v1"]
    assert lexical["filters"]["common"] == [
        "artifact_id",
        "source_alias",
        "source_prefix",
        "work_id",
        "publication_status",
    ]
    assert metadata["filters"]["missing"]["type"] == "metadata_field_name"
    assert temporal["filters"]["field"]["enum"] == [
        "observed_time",
        "source_modification_time",
        "publication_date",
    ]
    assert temporal["examples"][0]["query"] == ""
    assert description["result"]["capabilities"]["embeddings"] == "unavailable"
    assert description["result"]["schema_version"] == "tampu-tools/v1"


def test_describe_underfills_collection_page_without_losing_continuation(tmp_path: Path):
    repository = FakeRepository(tmp_path / "store")

    def describe(collection=None):
        return {
            "collections": [
                {
                    "name": name,
                    "root": f"/private/{name}",
                    "current_revision": "revision-1",
                }
                for name in ("one", "two", "three")
            ],
            "lenses": ["lexical/v1", "metadata/v1", "temporal/v1"],
            "candidate_limit": 10_000,
            "query_timeout_seconds": 10,
        }

    repository.describe = describe
    service = Service(repository)
    first = service.describe(limit=3, byte_budget=5000)
    assert first["status"] == "ok"
    assert len(first["result"]["collections"]) < 3
    assert isinstance(first["result"]["continuation"], str)
    second = service.describe(
        cursor=first["result"]["continuation"], limit=3, byte_budget=8192
    )
    assert second["result"]["collections"][0]["name"] == "two"


def test_describe_underfills_initial_and_subsequent_revision_pages(tmp_path: Path):
    repository = FakeRepository(tmp_path / "store")
    expected = [f"revision-{number:02}" for number in range(20)]

    def published_revisions(collection):
        base = repository.resolve_revision(collection, None)
        return [
            {
                **base,
                "revision_id": revision_id,
                "selection_digest": f"selection-{revision_id}",
                "published_at": f"2026-09-{20 - number:02}T00:01:01Z",
            }
            for number, revision_id in enumerate(expected)
        ]

    repository.published_revisions = published_revisions
    service = Service(repository)
    cursor = None
    delivered = []
    pages = []

    for _ in range(20):
        response = service.describe(
            collection="papers",
            revision_cursor=cursor,
            revision_limit=20,
        )
        assert response["status"] == "ok"
        assert len(encoded(response)) <= 8192
        assert len(response["result"]["collections"]) == 1
        pages.append(response)
        page = response["result"]["collections"][0]
        revision_ids = [item["revision_id"] for item in page["revisions"]]
        assert revision_ids
        assert not set(revision_ids) & set(delivered)
        delivered.extend(revision_ids)
        cursor = page["revision_continuation"]
        if cursor is None:
            break

    assert delivered == expected
    assert len(pages) > 1
    assert "revisions_underfilled_by_budget" in pages[0]["omissions"]

    too_small = service.describe(
        collection="papers", revision_limit=20, byte_budget=3500
    )
    assert too_small["status"] == "error"
    assert too_small["error"]["code"] == "budget_too_small"
    minimum = too_small["error"]["minimum_bytes"]
    assert minimum > 3500
    at_minimum = service.describe(
        collection="papers", revision_limit=20, byte_budget=minimum
    )
    assert at_minimum["status"] == "ok"
    assert at_minimum["result"]["collections"][0]["revisions"]


def test_trace_is_explicit_and_records_argument_response_pairs(tmp_path: Path):
    trace = tmp_path / "trace.jsonl"
    service = Service(FakeRepository(tmp_path / "store"), trace_path=trace)
    service.search(collection="papers", intent="full trace", query="secret sentinel")
    service.inspect(
        journey_id="missing", node_id="missing", continuation="secret cursor"
    )
    records = [json.loads(line) for line in trace.read_text().splitlines()]
    assert [record["operation"] for record in records] == ["search", "inspect"]
    assert records[0]["arguments"]["query"] == "secret sentinel"
    assert records[1]["response"]["error"]["code"] == "unknown_journey"


def test_telemetry_and_trace_failures_are_controlled_and_atomic(
    tmp_path: Path,
):
    service = Service(FakeRepository(tmp_path / "store"))
    malformed = service.search(
        collection="papers", intent="bad lens", lens=[], query="alpha"
    )
    assert malformed["error"]["code"] == "invalid_input"

    traced = Service(
        FakeRepository(tmp_path / "trace-store"), trace_path=tmp_path
    )
    failed = traced.search(
        collection="papers", intent="trace failure", query="alpha"
    )
    assert failed["error"] == {
        "code": "trace_unavailable",
        "message": "The configured trace could not be written.",
    }
    assert traced.active_journey_count == 0


def test_binary_cursors_round_trip_when_signature_contains_delimiter(
    service: Service,
):
    service._cursor_key = bytes(range(32))
    for offset in range(256):
        token = service._make_cursor("collections", offset)
        assert service._read_cursor(token, "collections") == offset


def test_consumer_repository_and_service_reads_do_not_mutate_durable_state(
    repository_config, monkeypatch, tmp_path: Path
):
    def extract(artifact, store, *, profile, timeout=300, image=None):
        projection_id = hashlib.sha256(
            f"{artifact['artifact_id']}:{profile}".encode()
        ).hexdigest()
        elements_path = Path("elements") / f"{projection_id}.json"
        raw_path = Path("raw") / f"{projection_id}.json"
        (Path(store) / elements_path).parent.mkdir(parents=True, exist_ok=True)
        (Path(store) / raw_path).parent.mkdir(parents=True, exist_ok=True)
        (Path(store) / elements_path).write_text(
            json.dumps(
                [
                    {
                        "ordinal": 0,
                        "original_element_id": "page-1",
                        "type": "Page",
                        "text": "sentinel alpha",
                        "page": 1,
                        "coordinates": None,
                    }
                ]
            ),
            encoding="utf-8",
        )
        (Path(store) / raw_path).write_text("{}", encoding="utf-8")
        elements_digest = hashlib.sha256(
            (Path(store) / elements_path).read_bytes()
        ).hexdigest()
        raw_digest = hashlib.sha256((Path(store) / raw_path).read_bytes()).hexdigest()
        return {
            "projection_id": projection_id,
            "artifact_id": artifact["artifact_id"],
            "recipe": {
                "profile": profile,
                "output_sha256": raw_digest,
                "elements_sha256": elements_digest,
            },
            "status": "ready",
            "raw_path": raw_path.as_posix(),
            "elements_path": elements_path.as_posix(),
            "coverage": {"pages_total": 1, "pages_with_text": 1, "elements": 1},
            "losses": [],
            "elapsed_seconds": 0.01,
        }

    monkeypatch.setattr("tampu.repository.extract_artifact", extract)
    root = tmp_path / "source"
    root.mkdir()
    (root / "paper.pdf").write_bytes(b"%PDF-1.4\nsentinel alpha")
    owner = Repository(repository_config)
    owner.ingest("papers", root, profile="poppler")
    generation_before = owner._db.collection("index_generations").get("current")
    revision_before = list(owner._db.collection("revisions").all())
    collection_before = list(owner._db.collection("collections").all())

    read_store = tmp_path / "consumer-must-not-create-store"
    reader = Repository(dict(repository_config, store=str(read_store)), initialize=False)
    description = Service(reader).describe(collection="papers")
    search = Service(reader).search(
        collection="papers", intent="read only", query="sentinel", limit=0
    )

    assert description["status"] == "ok"
    assert search["status"] == "ok"
    assert not read_store.exists()
    assert owner._db.collection("index_generations").get("current") == generation_before
    assert list(owner._db.collection("revisions").all()) == revision_before
    assert list(owner._db.collection("collections").all()) == collection_before


def test_inspection_rejects_tampered_projection_and_missing_captured_source(
    repository_config, monkeypatch, tmp_path: Path
):
    def extract(artifact, store, *, profile, timeout=300, image=None):
        projection_id = hashlib.sha256(
            f"{artifact['artifact_id']}:{profile}:verified".encode()
        ).hexdigest()
        elements_path = Path("elements") / f"{projection_id}.json"
        raw_path = Path("raw") / f"{projection_id}.json"
        elements_file = Path(store) / elements_path
        raw_file = Path(store) / raw_path
        elements_file.parent.mkdir(parents=True, exist_ok=True)
        raw_file.parent.mkdir(parents=True, exist_ok=True)
        elements_file.write_text(
            json.dumps(
                [
                    {
                        "ordinal": 0,
                        "original_element_id": "page-1",
                        "type": "Page",
                        "text": "verified alpha evidence",
                        "page": 1,
                        "coordinates": None,
                    }
                ],
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )
        raw_file.write_text("{}", encoding="utf-8")
        return {
            "projection_id": projection_id,
            "artifact_id": artifact["artifact_id"],
            "recipe": {
                "profile": profile,
                "output_sha256": hashlib.sha256(raw_file.read_bytes()).hexdigest(),
                "elements_sha256": hashlib.sha256(
                    elements_file.read_bytes()
                ).hexdigest(),
            },
            "status": "ready",
            "raw_path": raw_path.as_posix(),
            "elements_path": elements_path.as_posix(),
            "coverage": {"pages_total": 1, "pages_with_text": 1, "elements": 1},
            "losses": [],
            "elapsed_seconds": 0.01,
        }

    monkeypatch.setattr("tampu.repository.extract_artifact", extract)
    source_root = tmp_path / "source"
    source_root.mkdir()
    source = source_root / "paper.pdf"
    source.write_bytes(b"%PDF-1.4\nverified alpha evidence")
    owner = Repository(repository_config)
    owner.ingest("papers", source_root, profile="poppler")
    service = Service(Repository(repository_config, initialize=False))
    search = service.search(
        collection="papers", intent="verify backing bytes", query="alpha", limit=1
    )["result"]
    handle = search["hits"][0]["evidence_handle"]
    projection = owner.read_projection(
        owner.members(search["revision_id"])[0]["projection_id"]
    )
    elements_file = Path(repository_config["store"]) / projection["elements_path"]
    original_elements = elements_file.read_bytes()
    elements_file.write_text(
        '[{"ordinal":0,"text":"forged alpha","page":1}]', encoding="utf-8"
    )
    tampered = service.inspect(
        journey_id=search["journey_id"],
        node_id=search["node_id"],
        evidence_handle=handle,
    )
    assert tampered["error"]["code"] == "missing_evidence"

    elements_file.write_bytes(original_elements)
    artifact = owner._db.collection("artifacts").get(projection["artifact_id"])
    (Path(repository_config["store"]) / artifact["store_path"]).unlink()
    missing_source = service.inspect(
        journey_id=search["journey_id"],
        node_id=search["node_id"],
        evidence_handle=handle,
    )
    assert missing_source["error"]["code"] == "missing_evidence"


def test_semantic_absence_cannot_be_structurally_validated_positive(service: Service):
    search = service.search(
        collection="papers", intent="semantic claim", query="alpha", limit=1
    )["result"]
    inspected = service.inspect(
        journey_id=search["journey_id"],
        node_id=search["node_id"],
        evidence_handle=search["hits"][0]["evidence_handle"],
    )["result"]["evidence"]["handle"]
    rejected = service.finish(
        journey_id=search["journey_id"],
        kind="positive",
        statement="The concept is absent.",
        evidence_handles=[inspected],
        semantic_absence=True,
    )
    assert rejected["error"]["code"] == "invalid_finding"
