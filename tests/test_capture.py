import errno
import hashlib
from pathlib import Path

import pytest

import tampu.capture as capture_module
from tampu.capture import capture_tree

PDF = b"%PDF-1.4\nindependent evidence\n%%EOF\n"


def test_deduplicates_bytes_but_retains_every_alias_and_custody(tmp_path: Path) -> None:
    source = tmp_path / "source"
    store = tmp_path / "store"
    source.mkdir()
    (source / "paper.pdf").write_bytes(PDF)
    (source / "alias.PDF").write_bytes(PDF)

    scan = capture_tree(source, store)

    digest = hashlib.sha256(PDF).hexdigest()
    assert scan["enumeration_complete"] is True
    assert scan["observed_start"].endswith("Z")
    assert scan["observed_end"].endswith("Z")
    assert scan["artifacts"] == [
        {
            "artifact_id": digest,
            "sha256": digest,
            "byte_size": len(PDF),
            "store_path": f"artifacts/{digest[:2]}/{digest}.pdf",
            "captured_at": scan["artifacts"][0]["captured_at"],
        }
    ]
    captured = store / scan["artifacts"][0]["store_path"]
    assert captured.read_bytes() == PDF
    observed = {item["relative_path"]: item for item in scan["sources"]}
    assert observed["alias.PDF"]["artifact_id"] == digest
    assert observed["paper.pdf"]["artifact_id"] == digest

    (source / "paper.pdf").write_bytes(b"%PDF-invalid replacement")
    (source / "alias.PDF").unlink()
    assert captured.read_bytes() == PDF


def test_excludes_non_pdf_misleading_extension_and_symlink(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "notes.txt").write_bytes(PDF)
    (source / "fake.pdf").write_text("not a pdf")
    (source / "real.pdf").write_bytes(PDF)
    (source / "linked.pdf").symlink_to(source / "real.pdf")
    (source / "empty").mkdir()

    scan = capture_tree(source, tmp_path / "store")

    statuses = {item["relative_path"]: item["status"] for item in scan["sources"]}
    assert statuses == {
        "empty": "scanned_directory",
        "fake.pdf": "excluded_invalid_pdf",
        "linked.pdf": "excluded_symlink",
        "notes.txt": "excluded_extension",
        "real.pdf": "captured",
    }


def test_changed_source_is_retried_once_then_captured(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    candidate = source / "paper.pdf"
    candidate.write_bytes(PDF)
    real_copy = capture_module._copy_stable_candidate
    calls = 0

    def changes_once(path: Path, temporary: Path):
        nonlocal calls
        calls += 1
        if calls == 1:
            candidate.write_bytes(PDF + b"changed")
            raise capture_module._SourceChanged
        return real_copy(path, temporary)

    monkeypatch.setattr(capture_module, "_copy_stable_candidate", changes_once)

    scan = capture_tree(source, tmp_path / "store")

    assert calls == 2
    assert scan["sources"][0]["status"] == "captured"
    assert (
        tmp_path / "store" / scan["artifacts"][0]["store_path"]
    ).read_bytes() == PDF + b"changed"


def test_repeated_change_and_disappearance_are_controlled_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "changed.pdf").write_bytes(PDF)
    (source / "gone.pdf").write_bytes(PDF)

    def never_stable(path: Path, temporary: Path):
        if path.name == "gone.pdf":
            raise FileNotFoundError(path)
        raise capture_module._SourceChanged

    monkeypatch.setattr(capture_module, "_copy_stable_candidate", never_stable)
    scan = capture_tree(source, tmp_path / "store")

    outcomes = {item["relative_path"]: item for item in scan["sources"]}
    assert outcomes["changed.pdf"]["status"] == "error"
    assert outcomes["changed.pdf"]["error_code"] == "source_changed"
    assert outcomes["gone.pdf"]["status"] == "error"
    assert outcomes["gone.pdf"]["error_code"] == "source_disappeared"
    assert scan["artifacts"] == []


def test_safe_open_rejects_file_replaced_by_symlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    target = tmp_path / "outside.pdf"
    target.write_bytes(PDF)
    candidate = source / "paper.pdf"
    candidate.write_bytes(PDF)
    real_open = capture_module.os.open

    def replace_then_open(path, flags, *args, **kwargs):
        candidate.unlink(missing_ok=True)
        candidate.symlink_to(target)
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(capture_module.os, "open", replace_then_open)
    scan = capture_tree(source, tmp_path / "store")

    assert scan["sources"][0]["status"] == "error"
    assert scan["sources"][0]["error_code"] == "unsafe_source"
    assert scan["artifacts"] == []


def test_read_and_subtree_enumeration_failures_are_recorded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source"
    blocked = source / "blocked"
    blocked.mkdir(parents=True)
    unreadable = source / "unreadable.pdf"
    unreadable.write_bytes(PDF)
    real_scandir = capture_module.os.scandir
    real_open = capture_module.os.open

    def failing_scandir(path):
        if Path(path) == blocked:
            raise PermissionError(errno.EACCES, "denied")
        return real_scandir(path)

    def failing_open(path, flags, *args, **kwargs):
        if Path(path) == unreadable:
            raise PermissionError(errno.EACCES, "denied")
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(capture_module.os, "scandir", failing_scandir)
    monkeypatch.setattr(capture_module.os, "open", failing_open)
    scan = capture_tree(source, tmp_path / "store")

    outcomes = {item["relative_path"]: item for item in scan["sources"]}
    assert outcomes["blocked"]["status"] == "error"
    assert outcomes["blocked"]["error_code"] == "enumeration_failed"
    assert outcomes["unreadable.pdf"]["error_code"] == "read_failed"
    assert scan["enumeration_complete"] is False
