from __future__ import annotations

import asyncio
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from tampu.repository import Repository


def _write_config(repository_config: dict, path: Path) -> None:
    path.write_text(json.dumps(dict(repository_config)), encoding="utf-8")
    path.chmod(0o600)


def _publish_ready_fixture(repository_config, monkeypatch, source: Path) -> None:
    def extract(artifact, store, *, profile, timeout=300, image=None):
        projection_id = hashlib.sha256(
            f"{artifact['artifact_id']}:{profile}:mcp".encode()
        ).hexdigest()
        elements_path = Path("elements") / f"{projection_id}.json"
        raw_path = Path("raw") / f"{projection_id}.json"
        (Path(store) / elements_path).parent.mkdir(parents=True, exist_ok=True)
        (Path(store) / raw_path).parent.mkdir(parents=True, exist_ok=True)
        elements = [
            {
                "ordinal": 0,
                "original_element_id": "page-1",
                "type": "Page",
                "text": "alpha café 東京 😀 transport evidence",
                "page": 1,
                "coordinates": None,
            }
        ]
        (Path(store) / elements_path).write_text(
            json.dumps(elements, ensure_ascii=False), encoding="utf-8"
        )
        (Path(store) / raw_path).write_text("{}", encoding="utf-8")
        return {
            "projection_id": projection_id,
            "artifact_id": artifact["artifact_id"],
            "recipe": {
                "profile": profile,
                "timeout_seconds": timeout,
                "output_sha256": "raw",
                "elements_sha256": "elements",
            },
            "status": "ready",
            "raw_path": raw_path.as_posix(),
            "elements_path": elements_path.as_posix(),
            "coverage": {"pages_total": 1, "pages_with_text": 1, "elements": 1},
            "losses": [],
            "elapsed_seconds": 0.01,
        }

    monkeypatch.setattr("tampu.repository.extract_artifact", extract)
    Repository(repository_config).ingest("papers", source, profile="poppler")


def _application_json(call_result) -> dict:
    assert call_result.isError is False
    assert call_result.structuredContent is None
    assert len(call_result.content) == 1
    return json.loads(call_result.content[0].text)


def test_cli_init_ingest_describe_and_real_mcp_stdio_transport(
    repository_config, monkeypatch, tmp_path: Path
):
    config_path = tmp_path / "runtime.json"
    _write_config(repository_config, config_path)
    environment = {**os.environ, "TAMPU_CONFIG": str(config_path)}

    initialized = subprocess.run(
        [sys.executable, "-m", "tampu.cli", "init"],
        text=True,
        capture_output=True,
        env=environment,
        check=False,
    )
    assert initialized.returncode == 0
    assert json.loads(initialized.stdout)["result"]["initialized"] is True
    assert repository_config["password"] not in initialized.stdout + initialized.stderr

    source = tmp_path / "source"
    source.mkdir()
    paper = source / "paper.pdf"
    paper.write_bytes(b"%PDF-1.4\nalpha transport evidence")
    artifact_id = hashlib.sha256(paper.read_bytes()).hexdigest()
    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                artifact_id: {
                    "title": {"value": "Transport paper", "origin": "fixture"}
                }
            }
        ),
        encoding="utf-8",
    )
    ingested = subprocess.run(
        [
            sys.executable,
            "-m",
            "tampu.cli",
            "ingest",
            "papers",
            str(source),
            "--profile",
            "poppler",
            "--metadata",
            str(metadata_path),
        ],
        text=True,
        capture_output=True,
        env=environment,
        check=False,
    )
    assert ingested.returncode == 0
    assert json.loads(ingested.stdout)["result"]["collection"] == "papers"
    assert repository_config["password"] not in ingested.stdout + ingested.stderr

    _publish_ready_fixture(repository_config, monkeypatch, source)
    described = subprocess.run(
        [sys.executable, "-m", "tampu.cli", "describe"],
        text=True,
        capture_output=True,
        env=environment,
        check=False,
    )
    assert described.returncode == 0
    assert json.loads(described.stdout)["status"] == "ok"

    stderr_path = tmp_path / "mcp.stderr"

    async def probe():
        parameters = StdioServerParameters(
            command=sys.executable,
            args=["-m", "tampu.cli", "serve"],
            env=environment,
            cwd=Path.cwd(),
        )
        with stderr_path.open("w+", encoding="utf-8") as stderr:
            async with (
                stdio_client(parameters, errlog=stderr) as (read, write),
                ClientSession(read, write) as session,
            ):
                await session.initialize()
                listed = await session.list_tools()
                describe_call = await session.call_tool(
                    "describe", {"collection": "papers"}
                )
                search_call = await session.call_tool(
                    "search",
                    {
                        "collection": "papers",
                        "intent": "transport budget",
                        "query": "alpha",
                        "byte_budget": 1000,
                    },
                )
                malformed = await session.call_tool(
                    "search",
                    {
                        "collection": "papers",
                        "intent": "malformed sentinel intent",
                        "journey_id": "RAW_JOURNEY_SENTINEL",
                        "lens": "RAW_LENS_SENTINEL",
                        "query": "RAW_QUERY_SENTINEL",
                        "limit": {"RAW_ARGUMENT_SENTINEL": True},
                    },
                )
            stderr.flush()
        return listed, describe_call, search_call, malformed

    listed, describe_call, search_call, malformed = asyncio.run(probe())
    assert [tool.name for tool in listed.tools] == [
        "describe",
        "search",
        "inspect",
        "finish",
    ]
    descriptions = "\n".join(tool.description or "" for tool in listed.tools)
    for required in (
        "any_terms",
        "all_terms",
        "phrase",
        "pinned revision",
        "limit=0",
        "bounded_negative",
        "unresolved",
        "opaque evidence handle",
    ):
        assert required in descriptions
    annotations = {tool.name: tool.annotations for tool in listed.tools}
    assert annotations["describe"].readOnlyHint is True
    assert annotations["search"].readOnlyHint is False
    assert annotations["inspect"].readOnlyHint is False
    assert annotations["finish"].destructiveHint is True

    assert _application_json(describe_call)["status"] == "ok"
    search_payload = _application_json(search_call)
    assert search_payload["status"] == "ok"
    assert len(search_call.content[0].text.encode("utf-8")) <= 1000
    malformed_payload = _application_json(malformed)
    assert malformed_payload["error"]["code"] == "invalid_input"
    stderr_text = stderr_path.read_text(encoding="utf-8")
    for sentinel in (
        "RAW_QUERY_SENTINEL",
        "RAW_ARGUMENT_SENTINEL",
        "RAW_JOURNEY_SENTINEL",
        "RAW_LENS_SENTINEL",
        "malformed sentinel intent",
        repository_config["password"],
        str(source),
    ):
        assert sentinel not in stderr_text
