from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from arango import ArangoClient
from arango.exceptions import ArangoError

from .capture import capture_tree
from .errors import TampuError
from .extraction import extract_artifact

_COLLECTIONS = (
    "collections",
    "revisions",
    "observations",
    "artifacts",
    "projections",
    "memberships",
    "elements",
)
_METADATA_FIELDS = {
    "title",
    "authors",
    "work_id",
    "publication_status",
    "publication_date",
    "source_group",
    "version",
}
_CAP = 10_000
_TIMEOUT = 10
_COLLECTION_KEY = re.compile(r"^[A-Za-z0-9_.:@()+,=;$!*'%-]+$")
_DATE = re.compile(r"^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?$")


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _digest(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _safe_key(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _validate_metadata(metadata: dict | None, artifact_ids: set[str]) -> dict:
    if metadata is None:
        return {}
    if not isinstance(metadata, dict) or not set(metadata) <= artifact_ids:
        raise TampuError("invalid_metadata", "Metadata assertions are malformed.")
    for assertions in metadata.values():
        if not isinstance(assertions, dict) or not set(assertions) <= _METADATA_FIELDS:
            raise TampuError("invalid_metadata", "Metadata assertions are malformed.")
        for field, assertion in assertions.items():
            if (
                not isinstance(assertion, dict)
                or "value" not in assertion
                or not isinstance(assertion.get("origin"), str)
                or not assertion["origin"]
            ):
                raise TampuError(
                    "invalid_metadata", "Metadata assertions are malformed."
                )
            if field == "publication_date":
                precision = assertion.get("precision")
                value = assertion["value"]
                match = _DATE.fullmatch(value) if isinstance(value, str) else None
                expected_precision = (
                    {4: "year", 7: "month", 10: "day"}.get(len(value))
                    if isinstance(value, str)
                    else None
                )
                if not match or precision != expected_precision:
                    raise TampuError(
                        "invalid_metadata", "Publication date precision is required."
                    )
                try:
                    datetime.fromisoformat(
                        value
                        + (
                            "-01-01"
                            if len(value) == 4
                            else "-01"
                            if len(value) == 7
                            else ""
                        )
                    )
                except ValueError as error:
                    raise TampuError(
                        "invalid_metadata", "The publication date is invalid."
                    ) from error
            elif field == "authors":
                if not isinstance(assertion["value"], list) or not all(
                    isinstance(author, str) and author for author in assertion["value"]
                ):
                    raise TampuError(
                        "invalid_metadata", "Metadata assertions are malformed."
                    )
            elif not isinstance(assertion["value"], str) or not assertion["value"]:
                raise TampuError(
                    "invalid_metadata", "Metadata assertions are malformed."
                )
    return metadata


class Repository:
    def __init__(self, config: dict):
        try:
            required = ("endpoint", "database", "username", "password", "store")
            if any(
                not isinstance(config.get(k), str) or not config[k] for k in required
            ):
                raise ValueError
            self.store = Path(config["store"]).expanduser().resolve()
            self.store.mkdir(parents=True, exist_ok=True)
            self._db = ArangoClient(hosts=config["endpoint"]).db(
                config["database"],
                username=config["username"],
                password=config["password"],
            )
            self._db.version()
            self._ensure_schema()
        except TampuError:
            raise
        except (ArangoError, OSError, ValueError, TypeError) as error:
            raise TampuError(
                "storage_unavailable", "Tampu storage is unavailable."
            ) from error

    def _ensure_schema(self) -> None:
        for name in _COLLECTIONS:
            if not self._db.has_collection(name):
                self._db.create_collection(name)
        indexes = {
            "revisions": [("revision_id",), ("collection", "state")],
            "observations": [("revision_id", "relative_path")],
            "artifacts": [("artifact_id",)],
            "projections": [("projection_id",), ("artifact_id", "status")],
            "memberships": [
                ("revision_id", "artifact_id"),
                ("revision_id", "projection_id"),
            ],
            "elements": [
                ("projection_id", "ordinal"),
                ("artifact_id", "projection_id"),
            ],
        }
        for collection, fields_list in indexes.items():
            existing = {
                tuple(i.get("fields", []))
                for i in self._db.collection(collection).indexes()
            }
            for fields in fields_list:
                if fields not in existing:
                    self._db.collection(collection).add_index(
                        {"type": "persistent", "fields": list(fields)}
                    )
        view_properties = {
            "links": {
                "elements": {
                    "includeAllFields": False,
                    "fields": {
                        "text": {"analyzers": ["text_en"]},
                        "projection_id": {"analyzers": ["identity"]},
                    },
                }
            }
        }
        if "text_view" not in {view["name"] for view in self._db.views()}:
            self._db.create_arangosearch_view("text_view", properties=view_properties)
        else:
            self._db.replace_arangosearch_view("text_view", properties=view_properties)

    def ingest(
        self,
        collection: str,
        root: Path,
        *,
        profile: str,
        image: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        if not isinstance(collection, str) or not _COLLECTION_KEY.fullmatch(collection):
            raise TampuError("invalid_input", "A collection name is required.")
        root = Path(root).resolve()
        if root == self.store or self.store.is_relative_to(root):
            raise TampuError(
                "invalid_configuration",
                "The evidence store cannot be inside the source root.",
            )
        current_collection = self._db.collection("collections").get(collection)
        if current_collection and current_collection["root"] != str(root):
            raise TampuError(
                "collection_root_mismatch",
                "A collection can have only one registered root.",
            )
        capture = capture_tree(root, self.store)
        artifact_ids = {a["artifact_id"] for a in capture["artifacts"]}
        supplied = _validate_metadata(metadata, artifact_ids)
        parent = (
            self.resolve_revision(collection, None)
            if current_collection and current_collection.get("current_revision")
            else None
        )
        previous = (
            {m["artifact_id"]: m for m in self.members(parent["revision_id"])}
            if parent
            else {}
        )
        projections: dict[str, dict] = {}
        for artifact in capture["artifacts"]:
            projection = extract_artifact(
                artifact, self.store, profile=profile, image=image
            )
            projections[artifact["artifact_id"]] = projection
        revision_id = uuid.uuid4().hex
        aliases_by_artifact: dict[str, list[str]] = {}
        times_by_artifact: dict[str, list[int]] = {}
        for source in capture["sources"]:
            if source.get("status") == "captured":
                aliases_by_artifact.setdefault(source["artifact_id"], []).append(
                    source["relative_path"]
                )
                times_by_artifact.setdefault(source["artifact_id"], []).append(
                    source["mtime_ns"]
                )
        memberships = []
        for artifact in capture["artifacts"]:
            aid = artifact["artifact_id"]
            projection = projections[aid]
            assertions = (
                supplied[aid]
                if aid in supplied
                else previous.get(aid, {}).get("metadata", {})
            )
            memberships.append(
                {
                    "revision_id": revision_id,
                    "artifact_id": aid,
                    "projection_id": projection["projection_id"],
                    "projection_status": projection["status"],
                    "aliases": sorted(aliases_by_artifact.get(aid, [])),
                    "source_mtime_ns": min(times_by_artifact.get(aid, [0])),
                    "source_mtimes_ns": {
                        alias: source["mtime_ns"]
                        for alias in aliases_by_artifact.get(aid, [])
                        for source in capture["sources"]
                        if source.get("relative_path") == alias
                    },
                    "metadata": assertions,
                }
            )
        changes = self._changes(parent, capture["sources"], memberships)
        coverage = self._coverage(memberships, projections)
        revision = {
            "_key": revision_id,
            "revision_id": revision_id,
            "collection": collection,
            "parent_revision": parent["revision_id"] if parent else None,
            "state": "staged",
            "observed_start": capture["observed_start"],
            "observed_end": capture["observed_end"],
            "enumeration_complete": capture["enumeration_complete"],
            "selection_digest": _digest(
                [
                    {
                        k: m[k]
                        for k in ("artifact_id", "projection_id", "aliases", "metadata")
                    }
                    for m in memberships
                ]
            ),
            "aggregate_coverage": coverage,
            "counts": {
                "sources": sum(
                    s.get("status") == "captured" for s in capture["sources"]
                ),
                "artifacts": len(memberships),
                "ready": sum(m["projection_status"] == "ready" for m in memberships),
                "failed": sum(m["projection_status"] == "failed" for m in memberships),
            },
            "changes": changes,
        }
        try:
            self._stage(revision, capture, projections, memberships)
            self._verify_visibility(memberships)
            self._publish(
                collection,
                str(root),
                revision_id,
                parent["revision_id"] if parent else None,
            )
        except TampuError:
            raise
        except (ArangoError, OSError, ValueError) as error:
            raise TampuError(
                "storage_unavailable", "The revision could not be published."
            ) from error
        return self.resolve_revision(collection, revision_id)

    def _stage(self, revision, capture, projections, memberships):
        self._db.collection("revisions").insert(revision)
        for source in capture["sources"]:
            self._db.collection("observations").insert(
                dict(source, revision_id=revision["revision_id"])
            )
        for artifact in capture["artifacts"]:
            self._db.collection("artifacts").insert(
                dict(artifact, _key=artifact["artifact_id"]),
                overwrite=True,
                overwrite_mode="ignore",
            )
        for projection in projections.values():
            document = dict(projection, _key=projection["projection_id"])
            self._db.collection("projections").insert(
                document, overwrite=True, overwrite_mode="ignore"
            )
            if projection["status"] == "ready":
                elements_path = self.store / projection["elements_path"]
                if not elements_path.is_file():
                    raise TampuError(
                        "missing_evidence", "Projection evidence is unavailable."
                    )
                elements = json.loads(elements_path.read_text())
                for element in elements:
                    key = _safe_key(
                        f"{projection['projection_id']}:{element['ordinal']}"
                    )
                    doc = dict(
                        element,
                        _key=key,
                        artifact_id=projection["artifact_id"],
                        projection_id=projection["projection_id"],
                    )
                    self._db.collection("elements").insert(
                        doc, overwrite=True, overwrite_mode="ignore"
                    )
        for membership in memberships:
            key = _safe_key(f"{revision['revision_id']}:{membership['artifact_id']}")
            self._db.collection("memberships").insert(dict(membership, _key=key))

    def _verify_visibility(self, memberships):
        projection_ids = [
            m["projection_id"] for m in memberships if m["projection_status"] == "ready"
        ]
        expected = self._db.aql.execute(
            "RETURN LENGTH(FOR e IN elements FILTER e.projection_id IN @ids RETURN 1)",
            bind_vars={"ids": projection_ids},
        ).next()
        visible = self._db.aql.execute(
            'RETURN LENGTH(FOR e IN text_view SEARCH ANALYZER(e.projection_id IN @ids, "identity") OPTIONS {waitForSync: true} RETURN 1)',
            bind_vars={"ids": projection_ids},
        ).next()
        if expected != visible:
            raise TampuError(
                "storage_unavailable", "Search indexing did not become visible."
            )

    def _publish(self, collection, root, revision_id, expected_parent):
        command = """
function (params) {
  const db = require('@arangodb').db;
  const cs = db.collections.exists(params.collection) ? db.collections.document(params.collection) : null;
  const current = cs ? (cs.current_revision || null) : null;
  if (current !== params.expected) throw new Error('publication_conflict');
  const revision = db.revisions.document(params.revision);
  if (!revision || revision.state !== 'staged') throw new Error('revision_not_staged');
  db.revisions.update(params.revision, {state: 'published', published_at: params.now});
  db.collections.insert({_key: params.collection, name: params.collection, root: params.root,
                         current_revision: params.revision}, {overwriteMode: 'replace'});
  return true;
}"""
        try:
            self._db.execute_transaction(
                command,
                params={
                    "collection": collection,
                    "root": root,
                    "revision": revision_id,
                    "expected": expected_parent,
                    "now": _now(),
                },
                read=["collections"],
                write=["collections", "revisions"],
                timeout=_TIMEOUT,
            )
        except ArangoError as error:
            if "publication_conflict" in str(error):
                raise TampuError(
                    "publication_conflict",
                    "A newer revision was published concurrently.",
                ) from error
            raise

    def _changes(self, parent, sources, memberships):
        current_paths = {
            s["relative_path"]: s.get("artifact_id")
            for s in sources
            if s.get("status") == "captured"
        }
        previous_paths = {}
        previous_status = {}
        if parent:
            rows = self._db.aql.execute(
                "FOR o IN observations FILTER o.revision_id == @r && o.status == 'captured' RETURN o",
                bind_vars={"r": parent["revision_id"]},
            )
            previous_paths = {r["relative_path"]: r["artifact_id"] for r in rows}
            previous_status = {
                m["artifact_id"]: m["projection_status"]
                for m in self.members(parent["revision_id"])
            }
        current_status = {m["artifact_id"]: m["projection_status"] for m in memberships}
        return {
            "added": sorted(current_paths.keys() - previous_paths.keys()),
            "removed": sorted(previous_paths.keys() - current_paths.keys()),
            "replaced": sorted(
                p
                for p in current_paths.keys() & previous_paths.keys()
                if current_paths[p] != previous_paths[p]
            ),
            "processing_changed": sorted(
                a
                for a in current_status.keys() & previous_status.keys()
                if current_status[a] != previous_status[a]
            ),
        }

    def _coverage(self, memberships, projections):
        ready = [
            projections[m["artifact_id"]]
            for m in memberships
            if m["projection_status"] == "ready"
        ]
        failed = sum(m["projection_status"] == "failed" for m in memberships)
        return {
            "artifacts": len(memberships),
            "ready_artifacts": len(ready),
            "failed_artifacts": failed,
            "pages_total": sum(p["coverage"]["pages_total"] for p in ready),
            "pages_with_text": sum(p["coverage"]["pages_with_text"] for p in ready),
            "blank_or_partial_artifacts": sum(bool(p.get("losses")) for p in ready),
            "pages_unknown": failed,
        }

    def resolve_revision(self, collection: str, revision: str | None) -> dict:
        if revision is None:
            record = self._db.collection("collections").get(collection)
            revision = record.get("current_revision") if record else None
        document = self._db.collection("revisions").get(revision) if revision else None
        if (
            not document
            or document.get("collection") != collection
            or document.get("state") != "published"
        ):
            raise TampuError(
                "revision_not_ready", "The requested revision is not published."
            )
        return {k: v for k, v in document.items() if not k.startswith("_")}

    def members(self, revision: str) -> list[dict]:
        document = self._db.collection("revisions").get(revision)
        if not document or document.get("state") != "published":
            raise TampuError(
                "revision_not_ready", "The requested revision is not published."
            )
        rows = self._db.aql.execute(
            "FOR m IN memberships FILTER m.revision_id == @revision SORT m.artifact_id RETURN UNSET(m, '_key', '_id', '_rev')",
            bind_vars={"revision": revision},
        )
        return list(rows)

    def read_projection(self, projection_id: str) -> dict:
        document = self._db.collection("projections").get(projection_id)
        if not document:
            raise TampuError("missing_evidence", "Projection evidence is unavailable.")
        if (
            not (self.store / document["raw_path"]).is_file()
            or not (self.store / document["elements_path"]).is_file()
        ):
            raise TampuError("missing_evidence", "Projection evidence is unavailable.")
        return {k: v for k, v in document.items() if not k.startswith("_")}

    def search_candidates(
        self, revision: str, lens: str, query: str, mode: str, filters: dict
    ) -> dict:
        if lens not in {"lexical/v1", "metadata/v1", "temporal/v1"}:
            raise TampuError("invalid_input", "The search lens is invalid.")
        revision_doc = self._db.collection("revisions").get(revision)
        if not revision_doc or revision_doc.get("state") != "published":
            raise TampuError(
                "revision_not_ready", "The requested revision is not published."
            )
        members = self.members(revision)
        filtered, unknown_count = self._filter_members(members, filters, lens)
        allowed = {m["artifact_id"]: m for m in filtered}
        if lens == "lexical/v1" and query:
            if mode not in {"any_terms", "all_terms", "phrase"}:
                raise TampuError("invalid_input", "The lexical mode is invalid.")
            predicates = {
                "any_terms": 'ANALYZER(e.text IN TOKENS(@query, "text_en"), "text_en")',
                "all_terms": 'ANALYZER(TOKENS(@query, "text_en") ALL IN e.text, "text_en")',
                "phrase": 'PHRASE(e.text, @query, "text_en")',
            }
            aql = f"""FOR e IN text_view SEARCH {predicates[mode]} OPTIONS {{waitForSync: true}}
FILTER e.projection_id IN @projections LET score = BM25(e)
COLLECT artifact_id = e.artifact_id INTO matches = {{ordinal: e.ordinal, page: e.page, text: e.text, projection_id: e.projection_id, score: score}}
LET best = FIRST(FOR row IN matches SORT row.score DESC, row.ordinal ASC LIMIT 1 RETURN row)
SORT best.score DESC, artifact_id ASC LIMIT @_limit RETURN {{artifact_id, best}}"""
            try:
                rows = list(
                    self._db.aql.execute(
                        aql,
                        bind_vars={
                            "query": query,
                            "projections": [
                                m["projection_id"]
                                for m in filtered
                                if m["projection_status"] == "ready"
                            ],
                            "_limit": _CAP + 1,
                        },
                        max_runtime=_TIMEOUT,
                    )
                )
            except ArangoError as error:
                if "timeout" in str(error).lower():
                    raise TampuError(
                        "query_timeout", "The database query timed out."
                    ) from error
                raise TampuError(
                    "storage_unavailable", "The search could not be completed."
                ) from error
            candidates = [
                {
                    "artifact_id": r["artifact_id"],
                    "aliases": allowed[r["artifact_id"]]["aliases"],
                    "metadata": allowed[r["artifact_id"]]["metadata"],
                    "score": r["best"]["score"],
                    "evidence": {
                        "artifact_id": r["artifact_id"],
                        "projection_id": r["best"]["projection_id"],
                        "ordinal": r["best"]["ordinal"],
                        "page": r["best"]["page"],
                        "start": 0,
                        "end": len(r["best"]["text"]),
                    },
                    "text": r["best"]["text"],
                }
                for r in rows
            ]
        else:
            candidates = [
                {
                    "artifact_id": m["artifact_id"],
                    "aliases": m["aliases"],
                    "metadata": m["metadata"],
                    "projection_id": m["projection_id"],
                    "projection_status": m["projection_status"],
                }
                for m in filtered
            ]
        if len(candidates) > _CAP:
            raise TampuError("candidate_limit", "The candidate limit was exceeded.")
        coverage = self._coverage_for_members(filtered)
        return {
            "revision_id": revision,
            "lens": lens,
            "query": query,
            "mode": mode,
            "filters": filters,
            "count": len(candidates),
            "count_kind": "exact",
            "unknown_count": unknown_count,
            "candidates": candidates,
            "coverage": coverage,
            "selection": "maximum_element_bm25_then_artifact_id"
            if lens == "lexical/v1"
            else "artifact_id",
        }

    def _coverage_for_members(self, members):
        projections = {}
        for member in members:
            document = self._db.collection("projections").get(member["projection_id"])
            if document:
                projections[member["artifact_id"]] = document
        return self._coverage(members, projections)

    def _filter_members(self, members, filters, lens):
        if not isinstance(filters, dict):
            raise TampuError("invalid_input", "Filters must be an object.")
        result = []
        unknown = 0
        temporal_field = filters.get("field") if lens == "temporal/v1" else None
        for m in members:
            metadata = m["metadata"]
            aliases = m["aliases"]
            ok = True
            if "artifact_id" in filters:
                ok &= m["artifact_id"] == filters["artifact_id"]
            if "source_alias" in filters:
                ok &= filters["source_alias"] in aliases
            if "source_prefix" in filters:
                ok &= any(a.startswith(filters["source_prefix"]) for a in aliases)
            for field in ("work_id", "publication_status"):
                if field in filters:
                    ok &= metadata.get(field, {}).get("value") == filters[field]
            if "missing" in filters and not temporal_field:
                if not isinstance(filters["missing"], str):
                    raise TampuError(
                        "invalid_input", "The missing metadata field is invalid."
                    )
                ok &= filters["missing"] not in metadata
            if temporal_field:
                if temporal_field == "observed_time":
                    value = self._db.collection("revisions").get(m["revision_id"])[
                        "observed_end"
                    ][:10]
                elif temporal_field == "source_modification_time":
                    value = (
                        datetime.fromtimestamp(m["source_mtime_ns"] / 1e9, UTC)
                        .date()
                        .isoformat()
                    )
                elif temporal_field == "publication_date":
                    value = metadata.get("publication_date", {}).get("value")
                else:
                    raise TampuError("invalid_input", "The temporal field is invalid.")
                if value is None:
                    unknown += 1
                    ok &= filters.get("missing") is True
                else:
                    if filters.get("missing") is True:
                        ok = False
                    normalized = value + (
                        "-01-01"
                        if len(value) == 4
                        else "-01"
                        if len(value) == 7
                        else ""
                    )
                    if "from" in filters:
                        ok &= normalized >= filters["from"]
                    if "to" in filters:
                        ok &= normalized <= filters["to"]
            if ok:
                result.append(m)
        return result, unknown

    def describe(self, collection: str | None = None) -> dict:
        query = (
            "FOR c IN collections SORT c.name RETURN UNSET(c, '_key', '_id', '_rev')"
        )
        rows = list(self._db.aql.execute(query))
        if collection is not None:
            rows = [r for r in rows if r["name"] == collection]
            if not rows:
                raise TampuError("unknown_collection", "The collection is unknown.")
        return {
            "collections": rows,
            "lenses": ["lexical/v1", "metadata/v1", "temporal/v1"],
            "candidate_limit": _CAP,
            "query_timeout_seconds": _TIMEOUT,
        }
