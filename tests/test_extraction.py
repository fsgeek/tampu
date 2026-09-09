import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest

import tampu.extraction as extraction_module
from tampu.errors import TampuError
from tampu.extraction import extract_artifact

UNSTRUCTURED_TEST_IMAGE = os.environ.get("TAMPU_TEST_UNSTRUCTURED_IMAGE")


def make_pdf(pages: list[str]) -> bytes:
    objects: list[bytes] = []
    page_ids = [3 + index * 2 for index in range(len(pages))]
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    kids = b" ".join(f"{number} 0 R".encode() for number in page_ids)
    objects.append(
        b"<< /Type /Pages /Kids ["
        + kids
        + b"] /Count "
        + str(len(pages)).encode()
        + b" >>"
    )
    for index, text in enumerate(pages):
        page_id = page_ids[index]
        content_id = page_id + 1
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 300] /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> /Contents {content_id} 0 R >>".encode()
        )
        escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream = f"BT /F1 12 Tf 20 200 Td ({escaped}) Tj ET".encode()
        objects.append(
            b"<< /Length "
            + str(len(stream)).encode()
            + b" >>\nstream\n"
            + stream
            + b"\nendstream"
        )
    result = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, body in enumerate(objects, 1):
        offsets.append(len(result))
        result.extend(f"{number} 0 obj\n".encode() + body + b"\nendobj\n")
    xref = len(result)
    result.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        result.extend(f"{offset:010d} 00000 n \n".encode())
    result.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    return bytes(result)


def install_artifact(store: Path, data: bytes) -> dict:
    digest = hashlib.sha256(data).hexdigest()
    relative = Path("artifacts") / digest[:2] / f"{digest}.pdf"
    (store / relative).parent.mkdir(parents=True)
    (store / relative).write_bytes(data)
    return {
        "artifact_id": digest,
        "sha256": digest,
        "byte_size": len(data),
        "store_path": relative.as_posix(),
        "captured_at": "2026-09-08T00:00:00.000000Z",
    }


def test_poppler_retains_raw_output_and_one_based_zero_text_pages(
    tmp_path: Path,
) -> None:
    store = tmp_path / "store"
    artifact = install_artifact(store, make_pdf(["alpha beta", "", "omega"]))

    projection = extract_artifact(artifact, store, profile="poppler")

    assert projection["status"] == "ready"
    assert projection["artifact_id"] == artifact["artifact_id"]
    assert projection["recipe"]["profile"] == "poppler"
    assert projection["recipe"]["extractor"] == "pdftotext"
    assert projection["recipe"]["output_sha256"]
    raw = json.loads((store / projection["raw_path"]).read_text())
    elements = json.loads((store / projection["elements_path"]).read_text())
    assert raw["pdfinfo"]["Pages"] == "3"
    assert raw["pdftotext"].count("\f") >= 2
    assert [element["page"] for element in elements] == [1, 2, 3]
    assert [element["text"] for element in elements] == ["alpha beta", "", "omega"]
    assert [element["ordinal"] for element in elements] == [0, 1, 2]
    assert elements[0].keys() == {
        "ordinal",
        "original_element_id",
        "type",
        "text",
        "page",
        "coordinates",
    }
    assert projection["coverage"] == {
        "pages_total": 3,
        "pages_with_text": 2,
        "elements": 3,
    }


def test_same_successful_recipe_is_reused_and_changed_configuration_has_new_identity(
    tmp_path: Path,
) -> None:
    store = tmp_path / "store"
    artifact = install_artifact(store, make_pdf(["evidence"]))

    first = extract_artifact(artifact, store, profile="poppler")
    second = extract_artifact(artifact, store, profile="poppler")
    changed = extract_artifact(artifact, store, profile="poppler", timeout=299)

    assert first == second
    assert changed["projection_id"] != first["projection_id"]
    assert (store / first["raw_path"]).read_bytes() == (
        store / second["raw_path"]
    ).read_bytes()
    assert (store / first["elements_path"]).read_bytes() == (
        store / changed["elements_path"]
    ).read_bytes()

    raw_before = (store / first["raw_path"]).read_bytes()
    elements_before = (store / first["elements_path"]).read_bytes()
    (store / artifact["store_path"]).write_bytes(make_pdf(["changed source"]))
    assert (store / first["raw_path"]).read_bytes() == raw_before
    assert (store / first["elements_path"]).read_bytes() == elements_before


def test_changed_extractor_output_changes_projection_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    artifact_bytes = make_pdf(["evidence"])
    first_store = tmp_path / "first"
    second_store = tmp_path / "second"
    first = extract_artifact(
        install_artifact(first_store, artifact_bytes), first_store, profile="poppler"
    )
    real_poppler = extraction_module._poppler

    def changed_output(source: Path, timeout: int):
        raw, elements, details, losses = real_poppler(source, timeout)
        raw["pdftotext"] += "changed output"
        details["extractor_version"] += " changed"
        return raw, elements, details, losses

    monkeypatch.setattr(extraction_module, "_poppler", changed_output)
    second = extract_artifact(
        install_artifact(second_store, artifact_bytes), second_store, profile="poppler"
    )

    assert second["projection_id"] != first["projection_id"]


@pytest.mark.parametrize(
    "payload", [b"not a pdf", b"%PDF-1.4\nencrypted garbage /Encrypt"]
)
def test_malformed_or_encrypted_pdf_produces_controlled_failed_projection(
    tmp_path: Path, payload: bytes
) -> None:
    store = tmp_path / "store"
    artifact = install_artifact(store, payload)

    projection = extract_artifact(artifact, store, profile="poppler")

    assert projection["status"] == "failed"
    assert projection["losses"][0]["code"] == "malformed_or_encrypted_pdf"
    assert projection["raw_path"]
    raw = json.loads((store / projection["raw_path"]).read_text())
    assert raw["processes"]["pdfinfo"]["stderr"]
    assert "garbage" not in projection["losses"][0]["message"]


def test_missing_extractor_and_timeout_are_controlled_failed_projections(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = tmp_path / "store"
    artifact = install_artifact(store, make_pdf(["evidence"]))
    real_run = extraction_module.subprocess.run

    monkeypatch.setattr(
        extraction_module.subprocess,
        "run",
        lambda *args, **kwargs: (_ for _ in ()).throw(FileNotFoundError()),
    )
    missing = extract_artifact(artifact, store, profile="poppler")
    assert missing["status"] == "failed"
    assert missing["losses"][0]["code"] == "extractor_missing"

    monkeypatch.setattr(
        extraction_module.subprocess,
        "run",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            subprocess.TimeoutExpired(args[0], kwargs.get("timeout"))
        ),
    )
    timed_out = extract_artifact(artifact, store, profile="poppler", timeout=1)
    assert timed_out["status"] == "failed"
    assert timed_out["losses"][0]["code"] == "extraction_timeout"
    monkeypatch.setattr(extraction_module.subprocess, "run", real_run)


def test_unstructured_requires_digest_and_normalizes_complete_raw_elements(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = tmp_path / "store"
    artifact = install_artifact(store, make_pdf(["evidence"]))
    with pytest.raises(TampuError) as raised:
        extract_artifact(
            artifact, store, profile="unstructured", image="vendor/tool:latest"
        )
    assert raised.value.code == "unpinned_extractor_image"

    def fake_run(command, **kwargs):
        assert "--network=none" in command
        assert "--memory=8g" in command
        assert "vendor/tool@sha256:" + "a" * 64 in command
        assert any(part.endswith(":/input:ro") for part in command)
        output_mount = next(part for part in command if part.endswith(":/output:rw"))
        output_dir = Path(output_mount.removesuffix(":/output:rw"))
        raw_elements = [
            {
                "type": "NarrativeText",
                "element_id": "source-id",
                "text": "alpha",
                "metadata": {
                    "page_number": 1,
                    "coordinates": {"points": [[1, 2]], "system": "PixelSpace"},
                    "filename": "artifact.pdf",
                },
            },
            {
                "type": "PageBreak",
                "element_id": "break",
                "text": "",
                "metadata": {"page_number": 2},
            },
        ]
        (output_dir / "elements.json").write_text(json.dumps(raw_elements))
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(extraction_module.subprocess, "run", fake_run)
    projection = extract_artifact(
        artifact,
        store,
        profile="unstructured",
        image="vendor/tool@sha256:" + "a" * 64,
    )

    assert projection["status"] == "ready"
    assert projection["recipe"]["image"] == "vendor/tool@sha256:" + "a" * 64
    assert projection["recipe"]["network"] == "none"
    raw = json.loads((store / projection["raw_path"]).read_text())
    assert raw[0]["metadata"]["filename"] == "artifact.pdf"
    elements = json.loads((store / projection["elements_path"]).read_text())
    assert elements == [
        {
            "ordinal": 0,
            "original_element_id": "source-id",
            "type": "NarrativeText",
            "text": "alpha",
            "page": 1,
            "coordinates": {"points": [[1, 2]], "system": "PixelSpace"},
        },
        {
            "ordinal": 1,
            "original_element_id": "break",
            "type": "PageBreak",
            "text": "",
            "page": 2,
            "coordinates": None,
        },
    ]


@pytest.mark.parametrize(
    ("returncode", "expected_code"),
    [
        (124, "extraction_timeout"),
        (127, "extractor_missing"),
        (125, "extraction_failed"),
    ],
)
def test_unstructured_wrapper_failures_are_classified(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, returncode: int, expected_code: str
) -> None:
    store = tmp_path / "store"
    artifact = install_artifact(store, make_pdf(["evidence"]))
    monkeypatch.setattr(
        extraction_module.subprocess,
        "run",
        lambda command, **kwargs: subprocess.CompletedProcess(
            command, returncode, "", "controlled wrapper failure"
        ),
    )

    projection = extract_artifact(
        artifact,
        store,
        profile="unstructured",
        image="vendor/tool@sha256:" + "a" * 64,
    )

    assert projection["status"] == "failed"
    assert projection["losses"][0]["code"] == expected_code


def test_unknown_profile_is_typed_and_safe(tmp_path: Path) -> None:
    artifact = install_artifact(tmp_path, make_pdf(["x"]))
    with pytest.raises(TampuError) as raised:
        extract_artifact(artifact, tmp_path, profile="automatic")
    assert raised.value.code == "unsupported_extraction_profile"
    assert str(raised.value) == "Unsupported extraction profile."


@pytest.mark.skipif(
    not UNSTRUCTURED_TEST_IMAGE,
    reason="set a locally inspected pinned image to run container integration",
)
def test_real_unstructured_container_runs_offline_and_records_versions(
    tmp_path: Path,
) -> None:
    store = tmp_path / "store"
    artifact = install_artifact(store, make_pdf(["offline evidence"]))

    projection = extract_artifact(
        artifact, store, profile="unstructured", image=UNSTRUCTURED_TEST_IMAGE
    )

    assert projection["status"] == "ready"
    assert projection["recipe"]["extractor_versions"]["unstructured"]
    assert projection["recipe"]["extractor_versions"]["unstructured-inference"]
    assert projection["coverage"]["pages_total"] == 1
    assert "offline evidence" in " ".join(
        element["text"]
        for element in json.loads((store / projection["elements_path"]).read_text())
    )
