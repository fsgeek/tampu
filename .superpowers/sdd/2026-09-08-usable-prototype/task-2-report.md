# Task 2 report: ArangoDB revision publication and retrieval

Status: implemented and verified against ArangoDB 3.12.9-4 using a fresh disposable database and scoped user per test.

## Public records and responses

`Repository.ingest(collection, root, *, profile, image=None, metadata=None)` returns the newly published revision record. `resolve_revision` returns the same shape:

```text
{
  "revision_id": str,
  "collection": str,
  "parent_revision": str | null,
  "state": "published",
  "observed_start": ISO-8601 str,
  "observed_end": ISO-8601 str,
  "enumeration_complete": bool,
  "selection_digest": sha256 str,
  "aggregate_coverage": {
    "artifacts": int,
    "ready_artifacts": int,
    "failed_artifacts": int,
    "pages_total": int,
    "pages_with_text": int,
    "blank_or_partial_artifacts": int,
    "pages_unknown": int
  },
  "counts": {"sources": int, "artifacts": int, "ready": int, "failed": int},
  "changes": {
    "added": [relative_path],
    "removed": [relative_path],
    "replaced": [relative_path],
    "processing_changed": [artifact_id]
  },
  "published_at": ISO-8601 str
}
```

`members(revision_id)` returns artifact-ID-sorted records:

```text
{
  "revision_id": str,
  "artifact_id": sha256 str,
  "projection_id": sha256 str,
  "projection_status": "ready" | "failed",
  "aliases": [relative_path],
  "source_mtime_ns": int,                 # earliest alias mtime
  "source_mtimes_ns": {relative_path: int},
  "metadata": {
    <supported field>: {
      "value": JSON value,
      "origin": nonempty str,
      "precision"?: "year" | "month" | "day"  # publication_date only
    }
  }
}
```

Supported assertion fields are `title`, `authors`, `work_id`, `publication_status`, `publication_date`, `source_group`, and `version`. Authors are a string list; the other values are nonempty strings. Publication dates must be valid `YYYY`, `YYYY-MM`, or `YYYY-MM-DD` values with matching precision. Unknown fields remain absent. Omitting the whole metadata argument preserves assertions for unchanged artifact IDs. Supplying an artifact entry replaces that artifact's complete assertion mapping.

`search_candidates(revision, lens, query, mode, filters)` returns:

```text
{
  "revision_id": str,
  "lens": "lexical/v1" | "metadata/v1" | "temporal/v1",
  "query": str,
  "mode": str,
  "filters": object,
  "count": int,
  "count_kind": "exact",
  "unknown_count": int,
  "candidates": [candidate],
  "coverage": aggregate-coverage object for the metadata-filtered searched subset,
  "selection": "maximum_element_bm25_then_artifact_id" | "artifact_id"
}
```

Lexical candidates have this exact shape:

```text
{
  "artifact_id": str,
  "aliases": [str],
  "metadata": object,
  "score": number,
  "evidence": {
    "artifact_id": str,
    "projection_id": str,
    "ordinal": int,
    "page": int | null,
    "start": 0,
    "end": int
  },
  "text": str
}
```

Metadata-only and temporal candidates have this exact shape:

```text
{
  "artifact_id": str,
  "aliases": [str],
  "metadata": object,
  "projection_id": str,
  "projection_status": "ready" | "failed"
}
```

Lexical modes are `any_terms`, `all_terms` (all analyzed terms in one element), and `phrase`. Candidates are distinct artifacts. The score is the maximum matching-element BM25; ties use artifact ID. The repository returns the full candidate set up to 10,000 so Task 3 can materialize exact node membership before applying its display limit. Exceeding the cap raises `candidate_limit`; a database max-runtime failure raises `query_timeout` rather than returning a partial exact count.

Filters are conjunctive and use these keys:

```text
artifact_id: exact artifact digest
source_alias: exact relative path
source_prefix: relative path prefix
work_id: exact asserted value
publication_status: exact asserted value
missing: supported metadata field name                 # metadata/v1
field: "observed_time" | "source_modification_time" | "publication_date"
from: inclusive ISO date/time lower bound              # temporal/v1
to: inclusive ISO date/time upper bound                # temporal/v1
missing: true                                           # temporal/v1; select unknown field values
```

`unknown_count` for a temporal operation counts scoped artifacts with no value for its named field, independently of how many candidates meet the bounds. `observed_time` means the current revision scan's `observed_end`; it is not first admission or acquisition time. Unchanged artifacts are reobserved during every full scan. Use the revision's path-scoped `changes` and immutable parent memberships to distinguish additions, removals, and replacements. `source_modification_time` comes from the observed alias mtimes, and asserted publication dates preserve supplied precision.

## Storage and publication

The dedicated database contains `collections`, `revisions`, `observations`, `artifacts`, `projections`, `memberships`, and `elements`. Exact persistent indexes cover revision identity/state, observation paths, artifact/projection identities, membership revision joins, and element projection/ordinal joins. `text_view` links only `elements.text` with `text_en` and `elements.projection_id` with `identity`.

Artifacts, projection records, and normalized elements are shared by content/projection identity. Observations and memberships remain revision-specific. Ingestion writes a staged revision, verifies indexed element visibility with `waitForSync`, then uses an Arango transaction to change the staged record to published and replace the collection pointer only if its expected parent is still current. Failed visibility or a concurrent pointer change leaves the old pointer intact and the staged successor unreadable through public revision methods.

`scripts/provision-tampu.py` accepts administrator credentials from `--admin-file` or the explicit `TAMPU_ADMIN_ENDPOINT`, `TAMPU_ADMIN_USERNAME`, and `TAMPU_ADMIN_PASSWORD` environment variables. It refuses any existing target database or username, creates one database and one user with rights only on that database, and creates the runtime JSON with mode 0600 and a generated password. It does not alter an existing user's privileges or print credentials.

## Verification

```text
uv run pytest tests/test_repository.py -q
12 passed in 2.41s

uv run pytest tests/test_capture.py tests/test_extraction.py tests/test_repository.py -q
36 passed, 1 skipped in 3.14s

uvx ruff check src/tampu/config.py src/tampu/repository.py tests/conftest.py tests/test_repository.py scripts/provision-tampu.py
All checks passed

uv run python -m compileall -q src tests scripts/provision-tampu.py
git diff --check
clean
```

The skipped test is Task 1's opt-in real Unstructured container test. Repository tests use real isolated Arango databases; extraction is replaced at the external extractor boundary with complete Task 1 projection/elements records so the tests remain fast and deterministic. Each test database and scoped user is removed afterward. Test configuration representations redact credentials.

## Limitations and development observations

- `observed_time` describes the revision scan interval, so it cannot by itself answer when unchanged bytes first entered owner custody. Artifact `captured_at`, revision lineage, and path changes remain separate facts.
- Source modification time is filesystem-reported and is not a publication or acquisition assertion. When an artifact has multiple aliases, the membership retains every alias mtime; the initial temporal comparison uses the earliest alias mtime.
- Ready projections with declared losses count separately from failed projections. A failed projection with zero reported pages contributes one artifact to `pages_unknown`; it is not treated as evidence for a zero-page source.
- Search scores are current ArangoSearch BM25 navigation scores. Pinned revision membership and projections remain fixed, while index statistics may change as later immutable projections are added.
- The repository returns full candidate records up to its hard cap. Task 3 owns response packing, hit display limits, cursors, and byte budgets.
