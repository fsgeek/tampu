from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .errors import TampuError

_PINNED_IMAGE = re.compile(r"^[^@\s]+@sha256:[0-9a-f]{64}$")
_UNSTRUCTURED_SCRIPT = """
import importlib.metadata
import json
import sys
from pypdf import PdfReader
from unstructured.partition.pdf import partition_pdf
from unstructured.staging.base import elements_to_dicts

source, destination = sys.argv[1:3]
elements = partition_pdf(filename=source, strategy="fast", include_page_breaks=True)
payload = {
    "elements": elements_to_dicts(elements),
    "page_count": len(PdfReader(source).pages),
    "versions": {
        "unstructured": importlib.metadata.version("unstructured"),
        "unstructured-inference": importlib.metadata.version("unstructured-inference"),
        "pypdf": importlib.metadata.version("pypdf"),
    },
}
with open(destination, "w", encoding="utf-8") as stream:
    json.dump(payload, stream, ensure_ascii=False)
""".strip()


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _write_immutable(path: Path, payload: Any) -> None:
    data = _canonical_bytes(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise TampuError(
                "projection_store_conflict", "Projection storage is inconsistent."
            )
        return
    descriptor, temporary_name = tempfile.mkstemp(prefix="projection-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary_name, path)
        except FileExistsError:
            if path.read_bytes() != data:
                raise TampuError(
                    "projection_store_conflict", "Projection storage is inconsistent."
                )
    finally:
        Path(temporary_name).unlink(missing_ok=True)


def _successful_match(store: Path, artifact_id: str, requested: dict) -> dict | None:
    directory = store / "projections"
    if not directory.exists():
        return None
    for path in sorted(directory.glob("*.json")):
        try:
            record = json.loads(path.read_text())
        except OSError, ValueError:
            continue
        recipe = record.get("recipe", {})
        if (
            record.get("status") == "ready"
            and record.get("artifact_id") == artifact_id
            and all(recipe.get(key) == value for key, value in requested.items())
        ):
            raw_path = store / record.get("raw_path", "")
            elements_path = store / record.get("elements_path", "")
            if (
                raw_path.is_file()
                and elements_path.is_file()
                and hashlib.sha256(raw_path.read_bytes()).hexdigest()
                == recipe.get("output_sha256")
            ):
                return record
    return None


def _pdfinfo_map(text: str) -> dict[str, str]:
    return {
        key.strip(): value.strip()
        for line in text.splitlines()
        if ":" in line
        for key, value in [line.split(":", 1)]
    }


def _run(command: list[str], timeout: float) -> subprocess.CompletedProcess:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=max(timeout, 0.001),
        check=False,
    )


def _poppler(source: Path, timeout: int) -> tuple[dict, list[dict], dict, list[dict]]:
    deadline = time.monotonic() + timeout
    version = _run(["pdftotext", "-v"], deadline - time.monotonic())
    version_text = (version.stderr or version.stdout).splitlines()[0]
    info = _run(["pdfinfo", str(source)], deadline - time.monotonic())
    if info.returncode:
        return (
            {
                "pdfinfo": {},
                "pdftotext": "",
                "processes": {
                    "pdfinfo": {
                        "stdout": info.stdout,
                        "stderr": info.stderr,
                        "returncode": info.returncode,
                    },
                    "pdftotext": None,
                },
            },
            [],
            {"extractor_version": version_text},
            [
                {
                    "code": "malformed_or_encrypted_pdf",
                    "message": "The PDF could not be read by Poppler.",
                }
            ],
        )
    text = _run(["pdftotext", "-layout", str(source), "-"], deadline - time.monotonic())
    raw = {
        "pdfinfo": _pdfinfo_map(info.stdout),
        "pdftotext": text.stdout,
        "processes": {
            "pdfinfo": {
                "stdout": info.stdout,
                "stderr": info.stderr,
                "returncode": info.returncode,
            },
            "pdftotext": {
                "stdout": text.stdout,
                "stderr": text.stderr,
                "returncode": text.returncode,
            },
        },
    }
    if text.returncode:
        return (
            raw,
            [],
            {"extractor_version": version_text},
            [
                {
                    "code": "malformed_or_encrypted_pdf",
                    "message": "The PDF could not be read by Poppler.",
                }
            ],
        )
    page_count = int(raw["pdfinfo"].get("Pages", "0"))
    pages = text.stdout.split("\f")
    if pages and pages[-1] == "":
        pages.pop()
    pages.extend([""] * max(0, page_count - len(pages)))
    pages = pages[:page_count]
    elements = []
    for ordinal, page_text in enumerate(pages):
        normalized = page_text.strip("\r\n\f")
        elements.append(
            {
                "ordinal": ordinal,
                "original_element_id": f"page-{ordinal + 1}",
                "type": "Page",
                "text": normalized,
                "page": ordinal + 1,
                "coordinates": None,
            }
        )
    losses = []
    empty_pages = [element["page"] for element in elements if not element["text"]]
    if empty_pages:
        losses.append(
            {
                "code": "zero_text_pages",
                "pages": empty_pages,
                "message": "Some PDF pages produced no text.",
            }
        )
    return raw, elements, {"extractor_version": version_text}, losses


def _unstructured(
    source: Path, timeout: int, image: str, scratch: Path
) -> tuple[Any, list[dict], dict, list[dict]]:
    script = scratch / "extract_fast.py"
    script.write_text(_UNSTRUCTURED_SCRIPT)
    command = [
        "timeout",
        "--signal=TERM",
        "--kill-after=10s",
        f"{timeout}s",
        "docker",
        "run",
        "--rm",
        "--network=none",
        "--memory=8g",
        "--tmpfs",
        "/tmp:rw,noexec,nosuid,size=1g",
        "-e",
        "HF_HUB_OFFLINE=1",
        "-e",
        "TRANSFORMERS_OFFLINE=1",
        "-v",
        f"{source.parent.resolve()}:/input:ro",
        "-v",
        f"{scratch.resolve()}:/output:rw",
        image,
        "/app/.venv/bin/python",
        "/output/extract_fast.py",
        f"/input/{source.name}",
        "/output/elements.json",
    ]
    result = _run(command, timeout + 15)
    if result.returncode == 124:
        raise subprocess.TimeoutExpired(command, timeout)
    if result.returncode == 127:
        raise FileNotFoundError("container runtime is unavailable")
    output = scratch / "elements.json"
    if result.returncode or not output.exists():
        return (
            {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            },
            [],
            {},
            [
                {
                    "code": "extraction_failed",
                    "message": "Unstructured could not extract the PDF.",
                }
            ],
        )
    raw = json.loads(output.read_text())
    source_elements = raw.get("elements", []) if isinstance(raw, dict) else raw
    versions = raw.get("versions", {}) if isinstance(raw, dict) else {}
    page_count = raw.get("page_count") if isinstance(raw, dict) else None
    elements = []
    for ordinal, element in enumerate(source_elements):
        metadata = element.get("metadata") or {}
        elements.append(
            {
                "ordinal": ordinal,
                "original_element_id": element.get("element_id"),
                "type": element.get("type", "Unknown"),
                "text": element.get("text", ""),
                "page": metadata.get("page_number"),
                "coordinates": metadata.get("coordinates"),
            }
        )
    attributed = {item["page"] for item in elements if isinstance(item["page"], int)}
    losses = []
    if page_count:
        missing = sorted(set(range(1, page_count + 1)) - attributed)
        if missing:
            losses.append(
                {
                    "code": "unattributed_pages",
                    "pages": missing,
                    "message": "Some PDF pages have no attributed elements.",
                }
            )
    zero_text = sorted(
        {item["page"] for item in elements if item["page"] and not item["text"]}
    )
    if zero_text:
        losses.append(
            {
                "code": "zero_text_elements",
                "pages": zero_text,
                "message": "Some attributed elements contain no text.",
            }
        )
    return raw, elements, {"extractor_versions": versions}, losses


def extract_artifact(
    artifact: dict,
    store: Path,
    *,
    profile: str,
    timeout: int = 300,
    image: str | None = None,
) -> dict:
    store = Path(store)
    if profile not in {"poppler", "unstructured"}:
        raise TampuError(
            "unsupported_extraction_profile", "Unsupported extraction profile."
        )
    if timeout <= 0 or timeout > 300:
        raise TampuError(
            "invalid_extraction_timeout",
            "Extraction timeout must be between 1 and 300 seconds.",
        )
    if profile == "unstructured" and (
        image is None or not _PINNED_IMAGE.fullmatch(image)
    ):
        raise TampuError(
            "unpinned_extractor_image",
            "Unstructured requires an image pinned by SHA-256 digest.",
        )
    requested = {"profile": profile, "timeout_seconds": timeout}
    if profile == "unstructured":
        requested.update(
            {"image": image, "strategy": "fast", "network": "none", "memory": "8g"}
        )
    else:
        requested.update(
            {"extractor": "pdftotext", "layout": True, "page_breaks": True}
        )
    existing = _successful_match(store, artifact["artifact_id"], requested)
    if existing is not None:
        return existing
    source = store / artifact["store_path"]
    started = time.monotonic()
    raw: Any
    elements: list[dict]
    details: dict
    losses: list[dict]
    try:
        with tempfile.TemporaryDirectory(prefix="tampu-extract-") as temporary:
            if profile == "poppler":
                raw, elements, details, losses = _poppler(source, timeout)
            else:
                raw, elements, details, losses = _unstructured(
                    source, timeout, image, Path(temporary)
                )  # type: ignore[arg-type]
        fatal_codes = {"malformed_or_encrypted_pdf", "extraction_failed"}
        status = (
            "failed" if any(loss["code"] in fatal_codes for loss in losses) else "ready"
        )
    except FileNotFoundError:
        raw, elements, details, losses, status = (
            {"stderr": "Extractor executable was not found."},
            [],
            {},
            [
                {
                    "code": "extractor_missing",
                    "message": "The configured extractor is unavailable.",
                }
            ],
            "failed",
        )
    except subprocess.TimeoutExpired:
        raw, elements, details, losses, status = (
            {"stderr": "Extraction exceeded its time limit."},
            [],
            {},
            [
                {
                    "code": "extraction_timeout",
                    "message": "Extraction exceeded its time limit.",
                }
            ],
            "failed",
        )
    except json.JSONDecodeError, OSError, ValueError:
        raw, elements, details, losses, status = (
            {"stderr": "Extractor output was invalid."},
            [],
            {},
            [
                {
                    "code": "invalid_extractor_output",
                    "message": "The extractor returned invalid output.",
                }
            ],
            "failed",
        )
    elapsed = time.monotonic() - started
    if status == "failed":
        details["attempted_at"] = (
            datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
        )
    recipe = {
        **requested,
        **details,
        "output_sha256": hashlib.sha256(_canonical_bytes(raw)).hexdigest(),
    }
    projection_id = _digest({"artifact_id": artifact["artifact_id"], "recipe": recipe})
    raw_path = Path("raw") / f"{projection_id}.json"
    elements_path = Path("elements") / f"{projection_id}.json"
    page_values = {
        item["page"] for item in elements if isinstance(item.get("page"), int)
    }
    pdfinfo = raw.get("pdfinfo") if isinstance(raw, dict) else None
    pages_total = (
        int(pdfinfo.get("Pages", 0))
        if profile == "poppler" and isinstance(pdfinfo, dict)
        else (
            raw.get("page_count")
            if isinstance(raw, dict)
            else max(page_values, default=0)
        )
    )
    coverage = {
        "pages_total": pages_total or 0,
        "pages_with_text": len(
            {item["page"] for item in elements if item.get("page") and item.get("text")}
        ),
        "elements": len(elements),
    }
    record = {
        "projection_id": projection_id,
        "artifact_id": artifact["artifact_id"],
        "recipe": recipe,
        "status": status,
        "raw_path": raw_path.as_posix(),
        "elements_path": elements_path.as_posix(),
        "coverage": coverage,
        "losses": losses,
        "elapsed_seconds": round(elapsed, 6),
    }
    _write_immutable(store / raw_path, raw)
    _write_immutable(store / elements_path, elements)
    try:
        _write_immutable(store / "projections" / f"{projection_id}.json", record)
    except TampuError as error:
        concurrent = _successful_match(store, artifact["artifact_id"], requested)
        if error.code == "projection_store_conflict" and concurrent is not None:
            return concurrent
        raise
    return record
