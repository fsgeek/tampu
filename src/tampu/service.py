from __future__ import annotations

import base64
import copy
import hashlib
import hmac
import json
import logging
import secrets
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .errors import TampuError

DEFAULT_BYTE_BUDGET = 8_192
HARD_BYTE_BUDGET = 32_768
MAX_HITS = 20
MAX_CANDIDATES = 10_000
JOURNEY_TTL_SECONDS = 24 * 60 * 60
MAX_STATE_BYTES = 256 * 1024 * 1024
SCHEMA_VERSION = "tampu-tools/v1"

_LOGGER = logging.getLogger("tampu.operations")


class _BudgetError(TampuError):
    def __init__(self, message: str, minimum_bytes: int):
        super().__init__("budget_too_small", message)
        self.minimum_bytes = minimum_bytes


def compact_json(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def _size(value: Any) -> int:
    return len(compact_json(value).encode("utf-8"))


class Service:
    """Bounded consumer interface over published repository state."""

    def __init__(self, repository, *, trace_path: Path | None = None):
        self.repository = repository
        self.trace_path = Path(trace_path) if trace_path is not None else None
        self._journeys: dict[str, dict] = {}
        self._cursor_key = secrets.token_bytes(32)

    @property
    def active_journey_count(self) -> int:
        self._reclaim_expired()
        return len(self._journeys)

    def describe(
        self,
        *,
        collection: str | None = None,
        cursor: str | None = None,
        limit: int = 10,
        facet: str | None = None,
        facet_cursor: str | None = None,
        detail_limit: int = 20,
        revision_cursor: str | None = None,
        revision_limit: int = 2,
        byte_budget: int = DEFAULT_BYTE_BUDGET,
    ) -> dict:
        arguments = {
            "collection": collection,
            "cursor": cursor,
            "limit": limit,
            "facet": facet,
            "facet_cursor": facet_cursor,
            "detail_limit": detail_limit,
            "revision_cursor": revision_cursor,
            "revision_limit": revision_limit,
            "byte_budget": byte_budget,
        }
        revision_starts: dict[str, int] = {}

        def preserve_revision_underfill(collection_result: dict) -> None:
            name = collection_result["name"]
            next_offset = revision_starts[name] + len(
                collection_result["revisions"]
            )
            collection_result["revision_continuation"] = self._make_cursor(
                f"revisions:{name}", next_offset
            )

        return self._run(
            "describe",
            arguments,
            byte_budget,
            lambda: self._describe(
                collection,
                cursor,
                limit,
                facet,
                facet_cursor,
                detail_limit,
                revision_cursor,
                revision_limit,
                revision_starts,
            ),
            on_revisions_underfilled=preserve_revision_underfill,
        )

    def _describe(
        self,
        collection: str | None,
        cursor: str | None,
        limit: int,
        facet: str | None,
        facet_cursor: str | None,
        detail_limit: int,
        revision_cursor: str | None,
        revision_limit: int,
        revision_starts: dict[str, int],
    ) -> tuple[dict, dict, list[str]]:
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 20:
            raise TampuError("invalid_input", "The collection page limit is invalid.")
        if (
            not isinstance(detail_limit, int)
            or isinstance(detail_limit, bool)
            or not 1 <= detail_limit <= 100
        ):
            raise TampuError("invalid_input", "The facet detail limit is invalid.")
        if collection is not None and not isinstance(collection, str):
            raise TampuError("invalid_input", "The collection filter is invalid.")
        if facet is not None and not isinstance(facet, str):
            raise TampuError("invalid_input", "The requested facet is invalid.")
        if (
            not isinstance(revision_limit, int)
            or isinstance(revision_limit, bool)
            or not 1 <= revision_limit <= 20
        ):
            raise TampuError("invalid_input", "The revision page limit is invalid.")
        if revision_cursor is not None and (
            not isinstance(revision_cursor, str) or collection is None
        ):
            raise TampuError(
                "invalid_input",
                "Revision pagination requires one collection and a valid cursor.",
            )
        start = self._read_cursor(cursor, "collections") if cursor else 0
        repository_description = self.repository.describe(collection)
        raw_collections = repository_description["collections"]
        selected = raw_collections[start : start + limit]
        collections = []
        for raw in selected:
            revision = self.repository.resolve_revision(
                raw["name"], raw["current_revision"]
            )
            published_revisions = self.repository.published_revisions(raw["name"])
            revision_start = (
                self._read_cursor(revision_cursor, f"revisions:{raw['name']}")
                if revision_cursor is not None
                else 0
            )
            revision_starts[raw["name"]] = revision_start
            revision_page = published_revisions[
                revision_start : revision_start + revision_limit
            ]
            revision_summaries = [
                {
                    key: item[key]
                    for key in (
                        "revision_id",
                        "state",
                        "observed_start",
                        "observed_end",
                        "enumeration_complete",
                        "selection_digest",
                        "counts",
                        "aggregate_coverage",
                        "published_at",
                    )
                    if key in item
                }
                for item in revision_page
            ]
            revision_next = revision_start + len(revision_page)
            members = self.repository.members(revision["revision_id"])
            facets = self._facets(members)
            failures = []
            recipes: list[dict] = []
            recipe_seen: set[str] = set()
            for member in members:
                try:
                    projection = self.repository.read_projection(
                        member["projection_id"]
                    )
                except TampuError:
                    if member["projection_status"] == "failed":
                        failures.append(
                            {
                                "projection_status": "failed",
                                "details": "unavailable",
                            }
                        )
                    continue
                recipe = projection.get("recipe", {})
                recipe_key = compact_json(recipe)
                if recipe_key not in recipe_seen:
                    recipe_seen.add(recipe_key)
                    if len(recipes) < 5:
                        recipes.append(recipe)
                if projection["status"] == "failed" or projection.get("losses"):
                    failures.append(
                        {
                            "projection_status": projection["status"],
                            "coverage": projection["coverage"],
                            "losses": projection.get("losses", [])[:5],
                            "omitted_losses": max(
                                0, len(projection.get("losses", [])) - 5
                            ),
                        }
                    )
            facet_detail = None
            if facet is not None:
                if facet not in facets:
                    raise TampuError("invalid_input", "The requested facet is invalid.")
                detail_start = (
                    self._read_cursor(facet_cursor, f"facet:{facet}")
                    if facet_cursor
                    else 0
                )
                all_values = self._facet_values(members, facet)
                detail_values = all_values[detail_start : detail_start + detail_limit]
                facet_detail = {
                    "field": facet,
                    "values": detail_values,
                    "continuation": self._make_cursor(
                        f"facet:{facet}", detail_start + len(detail_values)
                    )
                    if detail_start + len(detail_values) < len(all_values)
                    else None,
                }
            coverage = dict(revision["aggregate_coverage"])
            coverage["ready_does_not_mean_complete_text"] = True
            coverage["semantic_coverage_claim"] = "not_available"
            collections.append(
                {
                    "name": raw["name"],
                    "root": "owner_configured_source",
                    "revision": {
                        key: revision[key]
                        for key in (
                            "revision_id",
                            "state",
                            "observed_start",
                            "observed_end",
                            "enumeration_complete",
                            "selection_digest",
                            "counts",
                            "published_at",
                        )
                        if key in revision
                    },
                    "coverage": coverage,
                    "revisions": revision_summaries,
                    "revision_continuation": self._make_cursor(
                        f"revisions:{raw['name']}", revision_next
                    )
                    if revision_next < len(published_revisions)
                    else None,
                    "facets": facets,
                    "facet_detail": facet_detail,
                    "failure_details": failures[:5],
                    "omitted_failure_details": max(0, len(failures) - 5),
                    "projection_recipes": recipes,
                    "omitted_projection_recipes": max(0, len(recipe_seen) - 5),
                }
            )
        next_offset = start + len(selected)
        result = {
            "schema_version": SCHEMA_VERSION,
            "collections": collections,
            "continuation": self._make_cursor("collections", next_offset)
            if next_offset < len(raw_collections)
            else None,
            "lenses": {
                "lexical/v1": {
                    "query": "required_nonempty",
                    "modes": ["any_terms", "all_terms", "phrase"],
                    "analyzer": "text_en",
                    "ordering": "maximum_element_bm25_then_artifact_id",
                    "filters": {
                        "common": [
                            "artifact_id",
                            "source_alias",
                            "source_prefix",
                            "work_id",
                            "publication_status",
                        ],
                        "combination": "conjunctive",
                    },
                    "examples": [
                        {
                            "query": "lease renewal",
                            "mode": "all_terms",
                            "filters": {"publication_status": "published"},
                        }
                    ],
                },
                "metadata/v1": {
                    "query": "must_be_empty",
                    "mode": "filter",
                    "typed_filters": True,
                    "ordering": "artifact_id",
                    "filters": {
                        "common": [
                            "artifact_id",
                            "source_alias",
                            "source_prefix",
                            "work_id",
                            "publication_status",
                        ],
                        "missing": {
                            "type": "metadata_field_name",
                            "enum": [
                                "title",
                                "authors",
                                "work_id",
                                "publication_status",
                                "publication_date",
                                "source_group",
                                "version",
                            ],
                        },
                        "combination": "conjunctive",
                    },
                    "examples": [
                        {
                            "query": "",
                            "mode": "filter",
                            "filters": {"missing": "publication_date"},
                        }
                    ],
                },
                "temporal/v1": {
                    "query": "must_be_empty",
                    "mode": "filter",
                    "typed_filters": True,
                    "ordering": "artifact_id",
                    "filters": {
                        "common": [
                            "artifact_id",
                            "source_alias",
                            "source_prefix",
                            "work_id",
                            "publication_status",
                        ],
                        "field": {
                            "required": True,
                            "enum": [
                                "observed_time",
                                "source_modification_time",
                                "publication_date",
                            ],
                        },
                        "from": "inclusive ISO date/instant lower bound; publication_date requires YYYY-MM-DD",
                        "to": "inclusive ISO date/instant upper bound; publication_date requires YYYY-MM-DD",
                        "missing": "boolean selecting unknown values for the named field",
                        "timezone": "timezone-free instants are interpreted as UTC",
                        "combination": "conjunctive",
                    },
                    "examples": [
                        {
                            "query": "",
                            "mode": "filter",
                            "filters": {
                                "field": "publication_date",
                                "from": "2024-01-01",
                                "to": "2024-12-31",
                            },
                        },
                        {
                            "query": "",
                            "mode": "filter",
                            "filters": {
                                "field": "source_modification_time",
                                "missing": True,
                            },
                        },
                    ],
                },
            },
            "limits": {
                "default_hits": 2,
                "maximum_hits": MAX_HITS,
                "count_only_limit": 0,
                "default_response_utf8_bytes": DEFAULT_BYTE_BUDGET,
                "maximum_response_utf8_bytes": HARD_BYTE_BUDGET,
                "candidate_limit": repository_description.get(
                    "candidate_limit", MAX_CANDIDATES
                ),
                "query_timeout_seconds": repository_description.get(
                    "query_timeout_seconds", 10
                ),
                "journey_expiry_seconds": JOURNEY_TTL_SECONDS,
                "process_journey_budget_bytes": MAX_STATE_BYTES,
                "revision_page_default": 2,
                "revision_page_maximum": 20,
            },
            "capabilities": {
                "lexical_search": "available",
                "metadata_filter": "available",
                "temporal_filter": "available",
                "evidence_slices": "available",
                "bounded_findings": "available",
                "embeddings": "unavailable",
                "composition": "unavailable",
                "history_navigation": "unavailable",
                "preservation": "unavailable",
                "historical_score_reexecution": "unavailable",
            },
            "validation": {
                "consumer_benefit": "not_tested",
                "evaluated_scale": "not_established",
            },
        }
        scope = {
            "collection_filter": collection,
            "published_revisions_only": True,
            "collection_offset": start,
        }
        return result, scope, []

    def search(
        self,
        *,
        collection: str | None = None,
        revision: str | None = None,
        intent: str | None = None,
        journey_id: str | None = None,
        lens: str = "lexical/v1",
        query: str = "",
        mode: str = "any_terms",
        filters: dict | None = None,
        limit: int = 2,
        byte_budget: int = DEFAULT_BYTE_BUDGET,
    ) -> dict:
        arguments = {
            "collection": collection,
            "revision": revision,
            "intent": intent,
            "journey_id": journey_id,
            "lens": lens,
            "query": query,
            "mode": mode,
            "filters": filters,
            "limit": limit,
            "byte_budget": byte_budget,
        }
        pending: dict[str, Any] = {}

        def preserve_underfill(result: dict) -> None:
            journey = pending["journey"]
            node = journey["nodes"][pending["node_id"]]
            token = result.get("continuation")
            if token is None:
                token = self._handle("continuation")
                result["continuation"] = token
                journey["continuations"][token] = {
                    "kind": "results",
                    "node_id": node["node_id"],
                    "offset": result["returned_count"],
                }
            else:
                journey["continuations"][token]["offset"] = result[
                    "returned_count"
                ]
            if not self._within_capacity(journey, pending.get("original")):
                raise TampuError(
                    "journey_capacity",
                    "The active journey capacity is exhausted; release a journey with finish.",
                )

        response = self._run(
            "search",
            arguments,
            byte_budget,
            lambda: self._search(
                collection,
                revision,
                intent,
                journey_id,
                lens,
                query,
                mode,
                filters,
                limit,
                pending,
            ),
            lens=lens,
            on_hits_underfilled=preserve_underfill,
        )
        if response.get("status") == "ok":
            journey = pending["journey"]
            delivered = {
                hit["evidence_handle"]
                for hit in response["result"].get("hits", [])
                if "evidence_handle" in hit
            }
            for handle in pending["new_evidence_handles"] - delivered:
                journey["evidence"].pop(handle, None)
            continuation = response["result"].get("continuation")
            if continuation is not None:
                journey["continuations"][continuation]["offset"] = response[
                    "result"
                ]["returned_count"]
            self._journeys[journey["journey_id"]] = journey
        return response

    def _search(
        self,
        collection: str | None,
        revision: str | None,
        intent: str | None,
        journey_id: str | None,
        lens: str,
        query: str,
        mode: str,
        filters: dict | None,
        limit: int,
        pending: dict,
    ) -> tuple[dict, dict, list[str]]:
        if (
            not isinstance(limit, int)
            or isinstance(limit, bool)
            or not 0 <= limit <= MAX_HITS
        ):
            raise TampuError("invalid_input", "The search hit limit is invalid.")
        if (
            not isinstance(lens, str)
            or not isinstance(query, str)
            or not isinstance(mode, str)
        ):
            raise TampuError("invalid_input", "The search operation is malformed.")
        if not isinstance(filters if filters is not None else {}, dict):
            raise TampuError("invalid_input", "The search filters are invalid.")
        for optional in (collection, revision, intent, journey_id):
            if optional is not None and not isinstance(optional, str):
                raise TampuError("invalid_input", "The search operation is malformed.")
        predicate_filters = {} if filters is None else filters
        now = time.time()
        is_new = journey_id is None
        if is_new:
            if not isinstance(collection, str) or not collection:
                raise TampuError("invalid_input", "A collection is required.")
            if not isinstance(intent, str) or not intent.strip():
                raise TampuError("invalid_input", "A finding intent is required.")
            resolved = self.repository.resolve_revision(collection, revision)
            selected_journey_id = self._handle("journey")
            journey = {
                "journey_id": selected_journey_id,
                "collection": collection,
                "revision_id": resolved["revision_id"],
                "selection_digest": resolved["selection_digest"],
                "intent": intent,
                "created_at": now,
                "expires_at": now + JOURNEY_TTL_SECONDS,
                "nodes": {},
                "continuations": {},
                "evidence": {},
                "inspected": set(),
                "findings": [],
            }
        else:
            original = self._journey(journey_id)
            journey = copy.deepcopy(original)
            pending["original"] = original
            selected_journey_id = journey["journey_id"]
            if collection is not None and collection != journey["collection"]:
                raise TampuError(
                    "invalid_input", "A journey cannot change collections."
                )
            if revision is not None and revision != journey["revision_id"]:
                raise TampuError("invalid_input", "A journey cannot change revisions.")
            if intent is not None and intent != journey["intent"]:
                raise TampuError("invalid_input", "A journey cannot change intent.")
        search = self.repository.search_candidates(
            journey["revision_id"], lens, query, mode, predicate_filters
        )
        if search["count"] > MAX_CANDIDATES:
            raise TampuError("candidate_limit", "The candidate limit was exceeded.")
        node_id = self._handle("node")
        candidates = search["candidates"]
        selection = {
            member["artifact_id"]: member["projection_id"]
            for member in self.repository.members(journey["revision_id"])
        }
        node = {
            "node_id": node_id,
            "lens": lens,
            "predicate": {
                "query": query,
                "mode": mode,
                "filters": predicate_filters,
            },
            "candidates": candidates,
            "selection": selection,
            "full_count": search["count"],
            "count_kind": search["count_kind"],
            "unknown_count": search.get("unknown_count", 0),
            "ordering": search["selection"],
            "coverage": search["coverage"],
            "index_generation": search.get("index_generation"),
            "index_generation_before": search.get("index_generation_before"),
            "index_generation_stable": search.get("index_generation_stable"),
            "lens_config": search.get("lens_config", {}),
        }
        journey["nodes"][node_id] = node
        handles_before = set(journey["evidence"])
        hits = self._hits(journey, node, 0, limit)
        continuation = self._result_continuation(journey, node, len(hits))
        pending.update(
            {
                "journey": journey,
                "node_id": node_id,
                "new_evidence_handles": set(journey["evidence"]) - handles_before,
            }
        )
        if not self._within_capacity(journey, pending.get("original")):
            raise TampuError(
                "journey_capacity",
                "The active journey capacity is exhausted; release a journey with finish.",
            )
        result = self._search_result(journey, node, hits, continuation)
        scope = self._node_scope(journey, node)
        omissions = []
        if len(hits) < search["count"]:
            omissions.append("additional_candidates_available_by_continuation")
        return result, scope, omissions

    def inspect(
        self,
        *,
        journey_id: str,
        node_id: str,
        continuation: str | None = None,
        limit: int = 2,
        evidence_handle: str | None = None,
        artifact_id: str | None = None,
        ordinal: int | None = None,
        page: int | None = None,
        start: int | None = None,
        end: int | None = None,
        slice_chars: int = 800,
        byte_budget: int = DEFAULT_BYTE_BUDGET,
    ) -> dict:
        arguments = {
            "journey_id": journey_id,
            "node_id": node_id,
            "continuation": continuation,
            "limit": limit,
            "evidence_handle": evidence_handle,
            "artifact_id": artifact_id,
            "ordinal": ordinal,
            "page": page,
            "start": start,
            "end": end,
            "slice_chars": slice_chars,
            "byte_budget": byte_budget,
        }
        pending: dict[str, Any] = {}

        def preserve_underfill(result: dict) -> None:
            journey = pending["journey"]
            offset = result.get("offset", 0) + result["returned_count"]
            token = result.get("continuation")
            if token is None:
                token = self._handle("continuation")
                result["continuation"] = token
                journey["continuations"][token] = {
                    "kind": "results",
                    "node_id": node_id,
                    "offset": offset,
                }
            else:
                journey["continuations"][token]["offset"] = offset
            if not self._within_capacity(journey, pending["original"]):
                raise TampuError(
                    "journey_capacity",
                    "The active journey capacity is exhausted; release a journey with finish.",
                )

        def operation():
            value = self._inspect(
                journey_id,
                node_id,
                continuation,
                limit,
                evidence_handle,
                artifact_id,
                ordinal,
                page,
                start,
                end,
                slice_chars,
                pending,
            )
            journey = pending["journey"]
            pending["new_evidence_handles"] = (
                set(journey["evidence"]) - pending["handles_before"]
            )
            if not self._within_capacity(journey, pending["original"]):
                raise TampuError(
                    "journey_capacity",
                    "The active journey capacity is exhausted; release a journey with finish.",
                )
            return value

        response = self._run(
            "inspect",
            arguments,
            byte_budget,
            operation,
            on_hits_underfilled=preserve_underfill,
        )
        if response.get("status") == "ok":
            journey = pending["journey"]
            result = response["result"]
            delivered_handles = {
                item["evidence_handle"]
                for key in ("hits", "elements")
                for item in result.get(key, [])
                if "evidence_handle" in item
            }
            evidence_result = result.get("evidence")
            if isinstance(evidence_result, dict):
                delivered_handles.add(evidence_result["handle"])
                journey["inspected"].add(evidence_result["handle"])
                next_handle = evidence_result.get("continuation")
                if next_handle is not None:
                    delivered_handles.add(next_handle)
                    journey["evidence"][next_handle]["next_start"] = evidence_result[
                        "character_range"
                    ][1]
            for handle in pending["new_evidence_handles"] - delivered_handles:
                journey["evidence"].pop(handle, None)
            next_cursor = result.get("continuation")
            if next_cursor is not None:
                journey["continuations"][next_cursor]["offset"] = result.get(
                    "offset", 0
                ) + result.get("returned_count", 0)
            self._journeys[journey_id] = journey
        return response

    def _inspect(
        self,
        journey_id: str,
        node_id: str,
        continuation: str | None,
        limit: int,
        evidence_handle: str | None,
        artifact_id: str | None,
        ordinal: int | None,
        page: int | None,
        start: int | None,
        end: int | None,
        slice_chars: int,
        pending: dict,
    ) -> tuple[dict, dict, list[str]]:
        original = self._journey(journey_id)
        journey = copy.deepcopy(original)
        pending.update(
            {
                "original": original,
                "journey": journey,
                "handles_before": set(journey["evidence"]),
            }
        )
        if not isinstance(node_id, str) or any(
            value is not None and not isinstance(value, str)
            for value in (continuation, evidence_handle, artifact_id)
        ):
            raise TampuError("invalid_input", "The inspection request is malformed.")
        node = self._node(journey, node_id)
        if evidence_handle is not None and (
            continuation is not None or artifact_id is not None
        ):
            raise TampuError(
                "invalid_input", "Choose result pagination or one evidence slice."
            )
        if evidence_handle is None:
            if (
                not isinstance(limit, int)
                or isinstance(limit, bool)
                or not 0 <= limit <= MAX_HITS
            ):
                raise TampuError("invalid_input", "The inspection limit is invalid.")
            saved = journey["continuations"].get(continuation) if continuation else None
            if continuation and not saved:
                raise TampuError(
                    "invalid_continuation", "The continuation is invalid."
                )
            if artifact_id is not None or (saved and saved.get("kind") == "elements"):
                return self._inspect_elements(
                    journey,
                    node,
                    artifact_id,
                    ordinal,
                    page,
                    limit,
                    saved,
                )
            if ordinal is not None or page is not None or start is not None or end is not None:
                raise TampuError(
                    "invalid_input", "An artifact is required for page or ordinal inspection."
                )
            offset = 0
            if continuation:
                if not saved or saved.get("kind") != "results":
                    raise TampuError(
                        "invalid_continuation", "The continuation is invalid."
                    )
                if saved["node_id"] != node_id:
                    raise TampuError(
                        "invalid_continuation", "The continuation is invalid."
                    )
                offset = saved["offset"]
            hits = self._hits(journey, node, offset, limit)
            next_cursor = self._result_continuation(
                journey, node, offset + len(hits)
            )
            result = {
                "journey_id": journey_id,
                "node_id": node_id,
                "revision_id": journey["revision_id"],
                "offset": offset,
                "returned_count": len(hits),
                "full_count": node["full_count"],
                "count_kind": node["count_kind"],
                "hits": hits,
                "continuation": next_cursor,
            }
            omissions = (
                ["additional_candidates_available_by_continuation"]
                if next_cursor
                else []
            )
            return result, self._node_scope(journey, node), omissions
        if (
            not isinstance(slice_chars, int)
            or isinstance(slice_chars, bool)
            or not 1 <= slice_chars <= 4_000
        ):
            raise TampuError("invalid_input", "The evidence slice limit is invalid.")
        evidence = journey["evidence"].get(evidence_handle)
        if not evidence or evidence["node_id"] != node_id:
            raise TampuError("missing_evidence", "Projection evidence is unavailable.")
        artifact_id = evidence["artifact_id"]
        projection_id = evidence["projection_id"]
        if (
            artifact_id not in node["selection"]
            or node["selection"][artifact_id] != projection_id
        ):
            raise TampuError("missing_evidence", "Projection evidence is unavailable.")
        projection = self.repository.read_projection(projection_id, verify_bytes=True)
        if (
            projection.get("artifact_id") != artifact_id
            or projection.get("projection_id") != projection_id
        ):
            raise TampuError("missing_evidence", "Projection evidence is unavailable.")
        elements = self._read_elements(projection)
        try:
            element = next(
                item for item in elements if item.get("ordinal") == evidence["ordinal"]
            )
            text = element["text"]
            if not isinstance(text, str):
                raise TypeError
        except (ValueError, TypeError, StopIteration) as error:
            raise TampuError(
                "missing_evidence", "Projection evidence is unavailable."
            ) from error
        lower = evidence["next_start"] if start is None else start
        upper = evidence["end"] if end is None else end
        if (
            not isinstance(lower, int)
            or isinstance(lower, bool)
            or not isinstance(upper, int)
            or isinstance(upper, bool)
            or lower < evidence["start"]
            or upper > evidence["end"]
            or lower > upper
        ):
            raise TampuError("invalid_input", "The evidence range is invalid.")
        delivered_end = min(upper, lower + slice_chars)
        delivered_handle = self._handle("evidence")
        journey["evidence"][delivered_handle] = {
            **evidence,
            "start": lower,
            "next_start": lower,
            "end": delivered_end,
        }
        journey["inspected"].add(delivered_handle)
        next_handle = None
        if delivered_end < upper:
            next_handle = self._handle("evidence")
            journey["evidence"][next_handle] = {
                **evidence,
                "next_start": delivered_end,
                "end": upper,
            }
        member_aliases = next(
            (
                candidate.get("aliases", [])
                for candidate in node["candidates"]
                if candidate["artifact_id"] == artifact_id
            ),
            [],
        )
        result = {
            "journey_id": journey_id,
            "node_id": node_id,
            "revision_id": journey["revision_id"],
            "evidence": {
                "handle": delivered_handle,
                "text": text[lower:delivered_end],
                "character_range": [lower, delivered_end],
                "continuation": next_handle,
                "artifact_id": artifact_id,
                "projection_id": projection_id,
                "ordinal": evidence["ordinal"],
                "physical_page": element.get("page"),
                "printed_page": None,
                "page_semantics": "one_based_physical_pdf_page; printed_page_unknown",
                "source_aliases": member_aliases[:2],
                "omitted_source_aliases": max(0, len(member_aliases) - 2),
                "projection": {
                    "status": projection["status"],
                    "recipe": projection["recipe"],
                    "coverage": projection["coverage"],
                    "losses": projection.get("losses", [])[:5],
                    "omitted_losses": max(0, len(projection.get("losses", [])) - 5),
                },
            },
        }
        omissions = (
            ["evidence_slice_continues"] if next_handle is not None else []
        )
        return result, self._node_scope(journey, node), omissions

    def _inspect_elements(
        self,
        journey: dict,
        node: dict,
        artifact_id: str | None,
        ordinal: int | None,
        page: int | None,
        limit: int,
        saved: dict | None,
    ) -> tuple[dict, dict, list[str]]:
        if saved is not None:
            if any(value is not None for value in (artifact_id, ordinal, page)):
                raise TampuError(
                    "invalid_input", "A continuation already identifies the artifact range."
                )
            artifact_id = saved["artifact_id"]
            ordinal = saved["ordinal"]
            page = saved["page"]
            offset = saved["offset"]
        else:
            offset = 0
        if not isinstance(artifact_id, str):
            raise TampuError("invalid_input", "An artifact identifier is required.")
        candidate = next(
            (
                item
                for item in node["candidates"]
                if item.get("artifact_id") == artifact_id
            ),
            None,
        )
        if candidate is None:
            raise TampuError("missing_evidence", "Projection evidence is unavailable.")
        if ordinal is not None and page is not None:
            raise TampuError("invalid_input", "Choose an ordinal or a printed page.")
        if ordinal is not None and (
            not isinstance(ordinal, int) or isinstance(ordinal, bool) or ordinal < 0
        ):
            raise TampuError("invalid_input", "The element ordinal is invalid.")
        if page is not None and (
            not isinstance(page, int) or isinstance(page, bool) or page < 1
        ):
            raise TampuError("invalid_input", "The physical PDF page is invalid.")
        projection_id = node["selection"].get(artifact_id)
        if not isinstance(projection_id, str):
            raise TampuError("missing_evidence", "Projection evidence is unavailable.")
        projection = self.repository.read_projection(projection_id, verify_bytes=True)
        if projection.get("artifact_id") != artifact_id:
            raise TampuError("missing_evidence", "Projection evidence is unavailable.")
        elements = self._read_elements(projection)
        selected = [
            element
            for element in elements
            if (ordinal is None or element.get("ordinal") == ordinal)
            and (page is None or element.get("page") == page)
        ]
        returned = []
        for element in selected[offset : offset + limit]:
            text = element.get("text")
            if not isinstance(text, str):
                continue
            handle = self._handle("evidence")
            journey["evidence"][handle] = {
                "node_id": node["node_id"],
                "artifact_id": artifact_id,
                "projection_id": projection_id,
                "ordinal": element["ordinal"],
                "start": 0,
                "next_start": 0,
                "end": len(text),
            }
            returned.append(
                {
                    "ordinal": element["ordinal"],
                    "physical_page": element.get("page"),
                    "printed_page": None,
                    "type": element.get("type"),
                    "evidence_handle": handle,
                    "extract": text[:240],
                    "extract_truncated": len(text) > 240,
                }
            )
        next_offset = offset + len(returned)
        continuation = None
        if next_offset < len(selected):
            continuation = self._handle("continuation")
            journey["continuations"][continuation] = {
                "kind": "elements",
                "node_id": node["node_id"],
                "artifact_id": artifact_id,
                "ordinal": ordinal,
                "page": page,
                "offset": next_offset,
            }
        metadata = self._bounded_metadata(candidate.get("metadata", {}))
        result = {
            "journey_id": journey["journey_id"],
            "node_id": node["node_id"],
            "revision_id": journey["revision_id"],
            "artifact": {
                "artifact_id": artifact_id,
                "metadata": metadata,
                "source_aliases": candidate.get("aliases", [])[:2],
                "omitted_source_aliases": max(
                    0, len(candidate.get("aliases", [])) - 2
                ),
                "projection_status": projection["status"],
                "projection_coverage": projection["coverage"],
                "projection_losses": projection.get("losses", [])[:5],
                "omitted_projection_losses": max(
                    0, len(projection.get("losses", [])) - 5
                ),
            },
            "selection": {"ordinal": ordinal, "physical_page": page},
            "offset": offset,
            "returned_count": len(returned),
            "elements": returned,
            "continuation": continuation,
        }
        omissions = ["additional_elements_available_by_continuation"] if continuation else []
        return result, self._node_scope(journey, node), omissions

    def _read_elements(self, projection: dict) -> list[dict]:
        path = self.repository.store / projection["elements_path"]
        try:
            elements = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(elements, list) or not all(
                isinstance(element, dict) for element in elements
            ):
                raise ValueError
            return elements
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
            raise TampuError(
                "missing_evidence", "Projection evidence is unavailable."
            ) from error

    @staticmethod
    def _bounded_metadata(metadata: dict) -> dict:
        result = {}
        for field in sorted(metadata)[:7]:
            assertion = metadata[field]
            if not isinstance(assertion, dict):
                continue
            bounded = dict(assertion)
            value = bounded.get("value")
            if isinstance(value, str):
                bounded["value"] = value[:500]
                bounded["value_truncated"] = len(value) > 500
            elif isinstance(value, list):
                bounded["value"] = value[:10]
                bounded["omitted_values"] = max(0, len(value) - 10)
            result[field] = bounded
        return result

    def finish(
        self,
        *,
        journey_id: str,
        kind: str,
        statement: str,
        evidence_handles: list[str] | None = None,
        node_id: str | None = None,
        reason: str | None = None,
        semantic_absence: bool = False,
        release: bool = False,
        byte_budget: int = DEFAULT_BYTE_BUDGET,
    ) -> dict:
        arguments = {
            "journey_id": journey_id,
            "kind": kind,
            "statement": statement,
            "evidence_handles": evidence_handles,
            "node_id": node_id,
            "reason": reason,
            "semantic_absence": semantic_absence,
            "release": release,
            "byte_budget": byte_budget,
        }
        pending: dict[str, Any] = {}

        def operation():
            value = self._finish(
                journey_id,
                kind,
                statement,
                evidence_handles,
                node_id,
                reason,
                semantic_absence,
                release,
                pending,
            )
            if not release and not self._within_capacity(
                pending["journey"], pending["original"]
            ):
                raise TampuError(
                    "journey_capacity",
                    "The active journey capacity is exhausted; release a journey with finish.",
                )
            return value

        response = self._run(
            "finish",
            arguments,
            byte_budget,
            operation,
        )
        if response.get("status") == "ok":
            if release:
                self._journeys.pop(journey_id, None)
            else:
                self._journeys[journey_id] = pending["journey"]
        return response

    def _finish(
        self,
        journey_id: str,
        kind: str,
        statement: str,
        evidence_handles: list[str] | None,
        node_id: str | None,
        reason: str | None,
        semantic_absence: bool,
        release: bool,
        pending: dict,
    ) -> tuple[dict, dict, list[str]]:
        original = self._journey(journey_id)
        journey = copy.deepcopy(original)
        pending.update({"original": original, "journey": journey})
        if (
            not isinstance(kind, str)
            or not isinstance(semantic_absence, bool)
            or not isinstance(release, bool)
        ):
            raise TampuError("invalid_input", "The finding request is malformed.")
        if semantic_absence and kind == "positive":
            raise TampuError(
                "invalid_finding",
                "A semantic-absence claim cannot be structurally validated.",
            )
        if not isinstance(statement, str) or not statement.strip():
            raise TampuError("invalid_input", "A finding statement is required.")
        handles = [] if evidence_handles is None else evidence_handles
        finding: dict[str, Any] = {
            "finding_id": self._handle("finding"),
            "kind": kind,
            "statement": statement,
            "durability": "process_local",
            "preserved": False,
        }
        if kind == "positive":
            if not isinstance(handles, list) or not handles or not all(
                isinstance(handle, str) for handle in handles
            ):
                raise TampuError(
                    "invalid_input", "Positive findings require evidence handles."
                )
            if any(handle not in journey["inspected"] for handle in handles):
                raise TampuError(
                    "uninspected_evidence",
                    "Positive findings require successfully inspected evidence.",
                )
            finding.update(
                {
                    "machine_status": "structurally_validated",
                    "evidence_handles": handles,
                    "semantic_entailment": "consumer_judgment_not_certified",
                }
            )
        elif kind == "bounded_negative":
            if not isinstance(node_id, str):
                raise TampuError(
                    "invalid_input", "A bounded negative requires a search node."
                )
            node = self._node(journey, node_id)
            if node["full_count"] != 0 or node["count_kind"] != "exact":
                raise TampuError(
                    "invalid_finding",
                    "A bounded negative requires an exact zero-candidate search.",
                )
            finding.update(
                {
                    "machine_status": "unresolved"
                    if semantic_absence
                    else "bounded_negative",
                    "scope": {
                        **self._node_scope(journey, node),
                        "predicate": node["predicate"],
                        "full_count": 0,
                        "count_kind": "exact",
                        "coverage": node["coverage"],
                    },
                    "semantic_absence": semantic_absence,
                    "limitation": "candidate_absence_does_not_establish_semantic_absence",
                }
            )
        elif kind == "unresolved":
            if not isinstance(reason, str) or not reason.strip():
                raise TampuError(
                    "invalid_input", "An unresolved finding requires a reason."
                )
            finding.update(
                {
                    "machine_status": "unresolved",
                    "reason": reason,
                    "semantic_absence": semantic_absence,
                }
            )
        else:
            raise TampuError("invalid_input", "The finding kind is invalid.")
        finding["released"] = bool(release)
        journey["findings"].append(finding)
        scope = {
            "collection": journey["collection"],
            "revision_id": journey["revision_id"],
            "journey_id": journey_id,
        }
        return finding, scope, []

    def _facets(self, members: list[dict]) -> dict:
        fields = (
            "source_group",
            "asserted_publication_year",
            "processing_status",
            "publication_status",
            "work_id",
        )
        result = {}
        for field in fields:
            values = self._facet_values(members, field)
            known = sum(item["artifacts"] for item in values)
            result[field] = {
                "values": values[:5],
                "unknown_artifacts": len(members) - known,
                "omitted_values": max(0, len(values) - 5),
                "count_unit": "artifacts",
                "source_group_requires_explicit_assertion": field == "source_group",
            }
        return result

    def _facet_values(self, members: list[dict], field: str) -> list[dict]:
        counts: dict[str, int] = {}
        for member in members:
            if field == "processing_status":
                value = member.get("projection_status")
            elif field == "asserted_publication_year":
                assertion = member.get("metadata", {}).get("publication_date")
                value = (
                    assertion.get("value", "")[:4]
                    if isinstance(assertion, dict)
                    and isinstance(assertion.get("value"), str)
                    and len(assertion["value"]) >= 4
                    else None
                )
            else:
                assertion = member.get("metadata", {}).get(field)
                value = assertion.get("value") if isinstance(assertion, dict) else None
            if value is None:
                continue
            key = compact_json(value)
            counts[key] = counts.get(key, 0) + 1
        return [
            {"value": json.loads(key), "artifacts": count}
            for key, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        ]

    def _hits(self, journey: dict, node: dict, offset: int, limit: int) -> list[dict]:
        hits = []
        for candidate in node["candidates"][offset : offset + limit]:
            hit = {
                "artifact_id": candidate["artifact_id"],
                "title": candidate.get("metadata", {}).get("title"),
                "source_aliases": candidate.get("aliases", [])[:2],
                "omitted_source_aliases": max(
                    0, len(candidate.get("aliases", [])) - 2
                ),
                "score": candidate.get("score"),
                "projection_status": candidate.get("projection_status", "ready"),
            }
            if "evidence" in candidate:
                address = candidate["evidence"]
                if (
                    node["selection"].get(candidate["artifact_id"])
                    == address.get("projection_id")
                ):
                    handle = self._handle("evidence")
                    journey["evidence"][handle] = {
                        "node_id": node["node_id"],
                        "artifact_id": candidate["artifact_id"],
                        "projection_id": address["projection_id"],
                        "ordinal": address["ordinal"],
                        "start": address["start"],
                        "next_start": address["start"],
                        "end": address["end"],
                    }
                    hit.update(
                        {
                            "evidence_handle": handle,
                            "physical_page": address.get("page"),
                            "printed_page": None,
                            "page_semantics": "one_based_physical_pdf_page; printed_page_unknown",
                            "extract": candidate.get("text", "")[:240],
                            "extract_truncated": len(candidate.get("text", "")) > 240,
                        }
                    )
            hits.append(hit)
        return hits

    def _result_continuation(self, journey: dict, node: dict, offset: int) -> str | None:
        if offset >= len(node["candidates"]):
            return None
        token = self._handle("continuation")
        journey["continuations"][token] = {
            "kind": "results",
            "node_id": node["node_id"],
            "offset": offset,
        }
        return token

    def _search_result(
        self, journey: dict, node: dict, hits: list[dict], continuation: str | None
    ) -> dict:
        return {
            "journey_id": journey["journey_id"],
            "node_id": node["node_id"],
            "intent": journey["intent"],
            "revision_id": journey["revision_id"],
            "projection_selection": journey["selection_digest"],
            "lens": node["lens"],
            "predicate": node["predicate"],
            "full_count": node["full_count"],
            "count_kind": node["count_kind"],
            "unknown_count": node["unknown_count"],
            "returned_count": len(hits),
            "ordering": node["ordering"],
            "coverage": node["coverage"],
            "index_generation": node["index_generation"],
            "index_generation_before": node["index_generation_before"],
            "index_generation_stable": node["index_generation_stable"],
            "lens_config": node["lens_config"],
            "hits": hits,
            "continuation": continuation,
        }

    def _node_scope(self, journey: dict, node: dict) -> dict:
        return {
            "collection": journey["collection"],
            "revision_id": journey["revision_id"],
            "projection_selection": journey["selection_digest"],
            "lens": node["lens"],
            "full_count": node["full_count"],
            "count_kind": node["count_kind"],
        }

    def _journey(self, journey_id: str | None) -> dict:
        journey = self._journeys.get(journey_id) if isinstance(journey_id, str) else None
        if journey is None:
            raise TampuError("unknown_journey", "The journey is unknown.")
        if time.time() >= journey["expires_at"]:
            raise TampuError("expired_journey", "The journey has expired.")
        return journey

    @staticmethod
    def _node(journey: dict, node_id: str) -> dict:
        node = journey["nodes"].get(node_id)
        if node is None:
            raise TampuError("unknown_node", "The search node is unknown.")
        return node

    def _run(
        self,
        operation: str,
        arguments: dict,
        byte_budget: int,
        callback: Callable[[], tuple[dict, dict, list[str]]],
        *,
        lens: str | None = None,
        on_hits_underfilled: Callable[[dict], None] | None = None,
        on_revisions_underfilled: Callable[[dict], None] | None = None,
    ) -> dict:
        started = time.monotonic()
        error_code = None
        try:
            budget = self._budget(byte_budget)
            result, scope, omissions = callback()
            response = self._fit(
                {
                    "status": "ok",
                    "result": result,
                    "scope": scope,
                    "omissions": omissions,
                },
                budget,
                on_hits_underfilled=on_hits_underfilled,
                on_revisions_underfilled=on_revisions_underfilled,
            )
        except TampuError as error:
            error_code = error.code
            error_payload = {"code": error.code, "message": error.message}
            if isinstance(error, _BudgetError):
                error_payload["minimum_bytes"] = error.minimum_bytes
            response = {
                "status": "error",
                "error": error_payload,
                "scope": {"operation": operation},
                "omissions": [],
            }
        except Exception:  # noqa: BLE001 - raw dependency failures stop at this boundary
            error_code = "internal_error"
            response = {
                "status": "error",
                "error": {
                    "code": "internal_error",
                    "message": "The operation could not be completed.",
                },
                "scope": {"operation": operation},
                "omissions": [],
            }
        try:
            self._trace(operation, arguments, response)
        except (OSError, ValueError, TypeError):
            error_code = "trace_unavailable"
            response = {
                "status": "error",
                "error": {
                    "code": "trace_unavailable",
                    "message": "The configured trace could not be written.",
                },
                "scope": {"operation": operation},
                "omissions": [],
            }
        response_bytes = _size(response)
        elapsed_ms = round((time.monotonic() - started) * 1000, 3)
        journey = response.get("result", {}).get("journey_id")
        supplied_journey = arguments.get("journey_id")
        if (
            journey is None
            and isinstance(supplied_journey, str)
            and supplied_journey in self._journeys
        ):
            journey = supplied_journey
        event_lens = (
            lens
            if isinstance(lens, str)
            and lens in {"lexical/v1", "metadata/v1", "temporal/v1"}
            else None
        )
        event = {
            "operation": operation,
            "journey_id": journey,
            "lens": event_lens,
            "full_count": response.get("scope", {}).get("full_count"),
            "returned_count": response.get("result", {}).get("returned_count"),
            "elapsed_ms": elapsed_ms,
            "response_bytes": response_bytes,
            "error_category": error_code,
        }
        _LOGGER.info(compact_json(event))
        return response

    @staticmethod
    def _budget(value: int) -> int:
        if not isinstance(value, int) or isinstance(value, bool):
            raise TampuError("invalid_input", "The response byte budget is invalid.")
        if value > HARD_BYTE_BUDGET:
            raise TampuError(
                "invalid_input",
                "The response byte budget exceeds the hard maximum.",
            )
        if value < 256:
            raise _BudgetError(
                "The UTF-8 application JSON byte budget is too small.",
                256,
            )
        return value

    def _fit(
        self,
        response: dict,
        budget: int,
        *,
        on_hits_underfilled: Callable[[dict], None] | None = None,
        on_revisions_underfilled: Callable[[dict], None] | None = None,
    ) -> dict:
        if _size(response) <= budget:
            return response
        result = response.get("result", {})
        for key in (
            "projection_recipes",
            "failure_details",
            "facets",
            "facet_detail",
            "index_generation_before",
            "index_generation",
            "lens_config",
            "intent",
            "index_generation_stable",
        ):
            if key in result:
                result.pop(key)
                response["omissions"].append(key)
                if _size(response) <= budget:
                    return response
            for collection in result.get("collections", []):
                if key in collection:
                    collection.pop(key)
                    response["omissions"].append(f"collections.{key}")
                    if _size(response) <= budget:
                        return response
        collections = result.get("collections")
        if isinstance(collections, list):
            if on_revisions_underfilled is not None:
                for collection in collections:
                    revisions = collection.get("revisions")
                    while (
                        isinstance(revisions, list)
                        and len(revisions) > 1
                        and _size(response) > budget
                    ):
                        revisions.pop()
                        on_revisions_underfilled(collection)
                        if (
                            "revisions_underfilled_by_budget"
                            not in response["omissions"]
                        ):
                            response["omissions"].append(
                                "revisions_underfilled_by_budget"
                            )
                    if _size(response) <= budget:
                        return response
            while len(collections) > 1 and _size(response) > budget:
                collections.pop()
                next_offset = response.get("scope", {}).get(
                    "collection_offset", 0
                ) + len(collections)
                result["continuation"] = self._make_cursor(
                    "collections", next_offset
                )
                if "collections_underfilled_by_budget" not in response["omissions"]:
                    response["omissions"].append(
                        "collections_underfilled_by_budget"
                    )
            if _size(response) <= budget:
                return response
            if collections:
                raise _BudgetError(
                    "One revision summary cannot fit; increase byte_budget or narrow the request.",
                    _size(response),
                )
        for hit in result.get("hits", []):
            for key in ("extract", "title", "source_aliases", "score"):
                if key in hit:
                    hit.pop(key)
                    if key not in response["omissions"]:
                        response["omissions"].append(key)
                    if _size(response) <= budget:
                        return response
        while result.get("hits"):
            result["hits"].pop()
            result["returned_count"] = len(result["hits"])
            if on_hits_underfilled is not None:
                on_hits_underfilled(result)
                if (
                    "additional_candidates_available_by_continuation"
                    not in response["omissions"]
                ):
                    response["omissions"].append(
                        "additional_candidates_available_by_continuation"
                    )
            if "hits" not in response["omissions"]:
                response["omissions"].append("hits")
            if _size(response) <= budget:
                return response
        if "hits" in response["omissions"]:
            response["omissions"] = [
                item
                for item in response["omissions"]
                if item not in {"extract", "title", "source_aliases", "score"}
            ]
            for key in (
                "revision_id",
                "projection_selection",
                "lens",
                "full_count",
                "count_kind",
            ):
                result.pop(key, None)
            if _size(response) <= budget:
                return response
        evidence = result.get("evidence")
        if isinstance(evidence, dict):
            for key in ("projection", "source_aliases"):
                if key in evidence:
                    evidence.pop(key)
                    response["omissions"].append(f"evidence.{key}")
                    if _size(response) <= budget:
                        return response
        raise _BudgetError(
            "The mandatory response scope cannot fit the requested budget.",
            _size(response),
        )

    def _make_cursor(self, kind: str, offset: int) -> str:
        payload = f"{kind}:{offset}".encode()
        signature = hmac.new(self._cursor_key, payload, hashlib.sha256).digest()[:12]
        return base64.urlsafe_b64encode(payload + b"." + signature).decode().rstrip("=")

    def _read_cursor(self, token: str, kind: str) -> int:
        try:
            raw = base64.urlsafe_b64decode(token + "=" * (-len(token) % 4))
            if len(raw) < 14 or raw[-13:-12] != b".":
                raise ValueError
            payload, signature = raw[:-13], raw[-12:]
            expected = hmac.new(self._cursor_key, payload, hashlib.sha256).digest()[:12]
            cursor_kind, offset = payload.decode().rsplit(":", 1)
            if not hmac.compare_digest(signature, expected) or cursor_kind != kind:
                raise ValueError
            parsed = int(offset)
            if parsed < 0:
                raise ValueError
            return parsed
        except (ValueError, UnicodeError, TypeError) as error:
            raise TampuError(
                "invalid_continuation", "The continuation is invalid."
            ) from error

    @staticmethod
    def _handle(prefix: str) -> str:
        return f"{prefix}_{secrets.token_urlsafe(18)}"

    @staticmethod
    def _state_size(value: Any) -> int:
        def default(item):
            if isinstance(item, set):
                return sorted(item)
            raise TypeError

        return len(
            json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                default=default,
            ).encode("utf-8")
        )

    def _total_state_bytes(self) -> int:
        return sum(self._state_size(journey) for journey in self._journeys.values())

    def _within_capacity(self, staged: dict, original: dict | None) -> bool:
        self._reclaim_expired()
        current = self._total_state_bytes()
        if original is not None and original["journey_id"] in self._journeys:
            current -= self._state_size(original)
        return current + self._state_size(staged) <= MAX_STATE_BYTES

    def _reclaim_expired(self) -> None:
        now = time.time()
        expired = [
            journey_id
            for journey_id, journey in self._journeys.items()
            if now >= journey["expires_at"]
        ]
        for journey_id in expired:
            self._journeys.pop(journey_id, None)

    def _trace(self, operation: str, arguments: dict, response: dict) -> None:
        if self.trace_path is None:
            return
        record = {
            "operation": operation,
            "arguments": arguments,
            "response": response,
        }
        self.trace_path.parent.mkdir(parents=True, exist_ok=True)
        with self.trace_path.open("a", encoding="utf-8") as stream:
            stream.write(compact_json(record) + "\n")
