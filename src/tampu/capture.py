from __future__ import annotations

import errno
import hashlib
import os
import stat
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from .errors import TampuError


class _SourceChanged(Exception):
    pass


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _same_file(left: os.stat_result, right: os.stat_result) -> bool:
    fields = ("st_dev", "st_ino", "st_mode", "st_size", "st_mtime_ns")
    return all(getattr(left, field) == getattr(right, field) for field in fields)


def _copy_stable_candidate(
    path: Path,
    temporary: Path,
    *,
    parent_fd: int | None = None,
    observed: os.stat_result | None = None,
) -> tuple[str, int, int]:
    name: str | Path = path.name if parent_fd is not None else path
    before = observed or os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    descriptor = os.open(
        name, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW, dir_fd=parent_fd
    )
    digest = hashlib.sha256()
    size = 0
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or not _same_file(before, opened):
            raise _SourceChanged
        with (
            os.fdopen(descriptor, "rb", closefd=False) as source,
            temporary.open("wb") as target,
        ):
            while chunk := source.read(1024 * 1024):
                digest.update(chunk)
                size += len(chunk)
                target.write(chunk)
            target.flush()
            os.fsync(target.fileno())
        after_fd = os.fstat(descriptor)
        after_path = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        if (
            not _same_file(opened, after_fd)
            or not _same_file(opened, after_path)
            or size != opened.st_size
        ):
            raise _SourceChanged
    finally:
        os.close(descriptor)
    return digest.hexdigest(), size, opened.st_mtime_ns


def _error_code(error: OSError) -> str:
    if isinstance(error, FileNotFoundError):
        return "source_disappeared"
    if error.errno in {errno.ELOOP, errno.EMLINK}:
        return "unsafe_source"
    return "read_failed"


def _install(temporary: Path, destination: Path, digest: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(temporary, destination)
    except FileExistsError:
        existing = hashlib.sha256(destination.read_bytes()).hexdigest()
        if existing != digest:
            raise TampuError(
                "artifact_store_conflict", "Captured artifact storage is inconsistent."
            )


def _open_directory_nofollow(path: Path) -> int:
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW
    if path.is_absolute():
        descriptor = os.open("/", flags)
        components = path.parts[1:]
    else:
        descriptor = os.open(".", flags)
        components = path.parts
    try:
        for component in components:
            if component in {"", "."}:
                continue
            child = os.open(component, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def capture_tree(root: Path, store: Path) -> dict:
    root = Path(root)
    store = Path(store)
    observed_start = _now()
    sources: list[dict] = []
    artifacts_by_id: dict[str, dict] = {}
    enumeration_complete = True
    temporary_root = store / ".capture-tmp"
    temporary_root.mkdir(parents=True, exist_ok=True)

    def observe_pdf(
        path: Path, relative: str, parent_fd: int, observed: os.stat_result
    ) -> None:
        last_error: BaseException | None = None
        for _attempt in range(2):
            fd, temporary_name = tempfile.mkstemp(
                prefix="candidate-", dir=temporary_root
            )
            os.close(fd)
            temporary = Path(temporary_name)
            try:
                digest, size, mtime_ns = _copy_stable_candidate(
                    path, temporary, parent_fd=parent_fd, observed=observed
                )
                with temporary.open("rb") as copied:
                    header = copied.read(5)
                if header != b"%PDF-":
                    sources.append(
                        {
                            "relative_path": relative,
                            "status": "excluded_invalid_pdf",
                            "mtime_ns": mtime_ns,
                        }
                    )
                    return
                store_path = Path("artifacts") / digest[:2] / f"{digest}.pdf"
                _install(temporary, store / store_path, digest)
                artifact = artifacts_by_id.setdefault(
                    digest,
                    {
                        "artifact_id": digest,
                        "sha256": digest,
                        "byte_size": size,
                        "store_path": store_path.as_posix(),
                        "captured_at": _now(),
                    },
                )
                sources.append(
                    {
                        "relative_path": relative,
                        "status": "captured",
                        "artifact_id": artifact["artifact_id"],
                        "mtime_ns": mtime_ns,
                    }
                )
                return
            except _SourceChanged as error:
                last_error = error
                try:
                    observed = os.stat(
                        path.name, dir_fd=parent_fd, follow_symlinks=False
                    )
                except OSError as stat_error:
                    last_error = stat_error
                    break
            except OSError as error:
                last_error = error
                if isinstance(error, FileNotFoundError) or error.errno in {
                    errno.ELOOP,
                    errno.EMLINK,
                    errno.EACCES,
                    errno.EPERM,
                }:
                    break
            finally:
                temporary.unlink(missing_ok=True)
        code = (
            "source_changed"
            if isinstance(last_error, _SourceChanged)
            else _error_code(last_error)
        )  # type: ignore[arg-type]
        sources.append(
            {"relative_path": relative, "status": "error", "error_code": code}
        )

    def observe_directory(directory_fd: int, relative_directory: Path) -> bool:
        nonlocal enumeration_complete
        try:
            with os.scandir(directory_fd) as iterator:
                entries = sorted(iterator, key=lambda entry: entry.name)
        except OSError:
            enumeration_complete = False
            sources.append(
                {
                    "relative_path": relative_directory.as_posix(),
                    "status": "error",
                    "error_code": "enumeration_failed",
                }
            )
            return False
        for entry in entries:
            relative_path = relative_directory / entry.name
            relative = relative_path.as_posix().removeprefix("./")
            path = root / relative_path
            try:
                if entry.is_symlink():
                    sources.append(
                        {"relative_path": relative, "status": "excluded_symlink"}
                    )
                elif entry.is_dir(follow_symlinks=False):
                    observed = entry.stat(follow_symlinks=False)
                    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW
                    try:
                        child_fd = os.open(entry.name, flags, dir_fd=directory_fd)
                        if not _same_file(observed, os.fstat(child_fd)):
                            os.close(child_fd)
                            raise OSError(errno.ELOOP, "directory changed")
                    except OSError as error:
                        enumeration_complete = False
                        code = (
                            "unsafe_source"
                            if error.errno in {errno.ELOOP, errno.ENOTDIR}
                            else "enumeration_failed"
                        )
                        sources.append(
                            {
                                "relative_path": relative,
                                "status": "error",
                                "error_code": code,
                            }
                        )
                        continue
                    try:
                        if observe_directory(child_fd, relative_path):
                            sources.append(
                                {
                                    "relative_path": relative,
                                    "status": "scanned_directory",
                                }
                            )
                    finally:
                        os.close(child_fd)
                elif not entry.is_file(follow_symlinks=False):
                    sources.append(
                        {"relative_path": relative, "status": "excluded_non_regular"}
                    )
                elif path.suffix.casefold() != ".pdf":
                    info = entry.stat(follow_symlinks=False)
                    sources.append(
                        {
                            "relative_path": relative,
                            "status": "excluded_extension",
                            "mtime_ns": info.st_mtime_ns,
                        }
                    )
                else:
                    observe_pdf(
                        path, relative, directory_fd, entry.stat(follow_symlinks=False)
                    )
            except OSError:
                sources.append(
                    {
                        "relative_path": relative,
                        "status": "error",
                        "error_code": "observation_failed",
                    }
                )
        return True

    try:
        root_fd = _open_directory_nofollow(root)
    except OSError as error:
        enumeration_complete = False
        code = (
            "unsafe_root"
            if error.errno in {errno.ELOOP, errno.ENOTDIR}
            else "enumeration_failed"
        )
        sources.append({"relative_path": ".", "status": "error", "error_code": code})
    else:
        try:
            observe_directory(root_fd, Path("."))
        finally:
            os.close(root_fd)
    try:
        temporary_root.rmdir()
    except OSError:
        pass
    return {
        "sources": sorted(sources, key=lambda item: item["relative_path"]),
        "artifacts": sorted(
            artifacts_by_id.values(), key=lambda item: item["artifact_id"]
        ),
        "observed_start": observed_start,
        "observed_end": _now(),
        "enumeration_complete": enumeration_complete,
    }
