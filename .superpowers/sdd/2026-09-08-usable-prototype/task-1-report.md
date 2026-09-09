## Task 1 report: capture and extraction with immutable evidence

Status: implemented and verified.

### Public interfaces and schemas

`capture_tree(root: Path, store: Path) -> dict` returns:

```text
{
  "sources": [
    {
      "relative_path": str,
      "status": "captured" | "excluded_extension" | "excluded_invalid_pdf"
                | "excluded_symlink" | "excluded_non_regular"
                | "scanned_directory" | "error",
      "artifact_id"?: str,
      "mtime_ns"?: int,
      "error_code"?: "source_changed" | "source_disappeared" | "unsafe_source"
                     | "read_failed" | "enumeration_failed" | "observation_failed"
    }
  ],
  "artifacts": [
    {
      "artifact_id": str,
      "sha256": str,
      "byte_size": int,
      "store_path": str,
      "captured_at": str
    }
  ],
  "observed_start": str,
  "observed_end": str,
  "enumeration_complete": bool
}
```

Artifact bytes are installed at `artifacts/<digest-prefix>/<sha256>.pdf` by a same-filesystem atomic hard-link from a temporary copy. Existing digest paths are verified instead of overwritten.

`extract_artifact(artifact: dict, store: Path, *, profile: str, timeout: int = 300, image: str | None = None) -> dict` accepts explicit profiles `poppler` and `unstructured` and returns:

```text
{
  "projection_id": str,
  "artifact_id": str,
  "recipe": {
    "profile": str,
    "timeout_seconds": int,
    ... exact profile configuration and extractor versions ...,
    "output_sha256": str
  },
  "status": "ready" | "failed",
  "raw_path": str,
  "elements_path": str,
  "coverage": {"pages_total": int, "pages_with_text": int, "elements": int},
  "losses": list[dict],
  "elapsed_seconds": float
}
```

Normalized element files contain JSON arrays whose entries are exactly:

```text
{
  "ordinal": int,
  "original_element_id": str | null,
  "type": str,
  "text": str,
  "page": int | null,
  "coordinates": object | null
}
```

Raw and normalized files use content-derived projection paths and atomic no-overwrite installation. Successful matching recipes are reused only after their raw digest and both output files are verified. Failed attempts get an `attempted_at` recipe field so an explicit retry cannot overwrite prior evidence.

### Extractor commands and versions

The Poppler profile executes these commands under one per-file deadline:

```text
pdftotext -v
pdfinfo <captured-pdf>
pdftotext -layout <captured-pdf> -
```

The verified development host reports Poppler `pdftotext version 22.02.0`; the exact version line is recorded per projection. Exact stdout, stderr, and return codes are retained in raw JSON.

The Unstructured profile requires an `@sha256:<64 hex>` image reference and executes the equivalent of:

```text
timeout --signal=TERM --kill-after=10s 300s docker run --rm --network=none --memory=8g \
  --tmpfs /tmp:rw,noexec,nosuid,size=1g \
  -e HF_HUB_OFFLINE=1 -e TRANSFORMERS_OFFLINE=1 \
  -v <captured-parent>:/input:ro -v <isolated-scratch>:/output:rw \
  <pinned-image> /app/.venv/bin/python /output/extract_fast.py \
  /input/<captured-pdf> /output/elements.json
```

The real integration check used `downloads.unstructured.io/unstructured-io/unstructured@sha256:806726e3997d33bce9e32facd86c947b241101c58496f2774ad5f09f86e798bc` and recorded `unstructured 0.23.3` plus `unstructured-inference 1.6.12` from inside the container.

### Verification

```text
uv run pytest tests/test_capture.py tests/test_extraction.py -q
17 passed, 1 skipped in 0.70s

TAMPU_TEST_UNSTRUCTURED_IMAGE=<inspected-pinned-image> \
  uv run pytest tests/test_extraction.py::test_real_unstructured_container_runs_offline_and_records_versions -q
1 passed in 8.40s

uv run python -m compileall -q src tests
uvx ruff check src/tampu/capture.py src/tampu/extraction.py src/tampu/errors.py tests/test_capture.py tests/test_extraction.py
All checks passed

git diff --check
clean
```

### Limitations and development observations

- Poppler supplies one normalized page element per PDF page, including empty elements for zero-text pages. Layout text is deterministic for a fixed Poppler version but is not a geometric reconstruction.
- Unstructured uses `strategy="fast"` with page breaks and has no automatic fallback. Its raw output is retained before normalization.
- The readiness sample attributed all pages for both born-digital caching papers. An image-heavy two-page Paxos paper attributed content only to page 1 and retained relatively little text; the adapter records unattributed and zero-text page losses, but OCR/hi-res extraction is outside this task.
- Readiness token overlap against `pdftotext` is comparative lexical coverage only. It does not establish reading order, semantic completeness, or general extractor superiority.
- The Unstructured integration test is opt-in because it requires Docker and the already-inspected pinned local image. Unit tests still verify its command and normalization contract without network access.

### Review fixes

The Poppler recipe now invokes `pdftotext` once for each physical page, using the PDF page count reported by `pdfinfo`:

```text
pdftotext -f <page> -l <page> <captured-pdf> -
```

The `-layout` option was removed. The recipe records `reading_order: "default"` and `physical_pages: true`, so this profile change has a distinct projection identity. Each page command's exact stdout, stderr, return code, and one-based page number are retained under raw `pdftotext_pages`. Embedded form feeds can no longer create extra logical pages, shift attribution, or cause trailing content to be discarded. Regression coverage includes embedded form feeds and a stable stored character slice across repeated extraction.

Projection recipes now record both `output_sha256` for raw JSON and `elements_sha256` for normalized JSON. Successful recipe reuse verifies both immutable files against their recorded digests; missing or corrupted normalized evidence is not accepted. A nonzero or empty Poppler version response produces a failed projection with controlled `extractor_version_failed` loss instead of indexing empty output.

Capture traversal now opens the root and every descended directory with `O_DIRECTORY | O_NOFOLLOW`, compares the opened descriptor with the no-follow observation, enumerates through the directory descriptor, and opens candidate files relative to that descriptor. A symlink root is reported as `unsafe_root`; a directory swapped for a symlink is reported as `unsafe_source`, sets `enumeration_complete` false, and cannot expose files outside the opened root.

Review verification:

```text
uv run pytest tests/test_capture.py tests/test_extraction.py -q
23 passed, 1 skipped in 0.69s

TAMPU_TEST_UNSTRUCTURED_IMAGE=<inspected-pinned-image> \
  uv run pytest tests/test_extraction.py::test_real_unstructured_container_runs_offline_and_records_versions -q
1 passed in 8.29s
```
