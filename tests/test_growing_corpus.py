"""Regressions for actual consumer lifecycle evidence, without invoking a model."""

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "growth_runner", Path(__file__).parents[1] / "experiments/growing_corpus/run.py"
)
runner = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(runner)


@pytest.mark.parametrize(
    ("completed", "failed", "overrun", "expected"),
    [
        (False, False, False, False),
        (False, True, False, False),
        (True, False, False, True),
        (True, False, True, False),
    ],
)
def test_final_assessment_requires_completed_uninterrupted_turn(
    tmp_path, monkeypatch, completed, failed, overrun, expected
):
    # These are the actual CLI event shapes: an item.completed agent_message may
    # be progress, and graceful process exit after SIGTERM may still return zero.
    events = [
        {
            "type": "item.completed",
            "item": {
                "id": "message",
                "type": "agent_message",
                "text": "Observed agent text",
            },
        }
    ]
    if completed:
        events.append(
            {"type": "turn.completed", "usage": {"input_tokens": 1, "output_tokens": 1}}
        )
    if failed:
        events.append({"type": "turn.failed", "error": {"message": "failure"}})
    if overrun:
        events.append(
            {
                "type": "item.completed",
                "item": {"id": "unexpected-tool", "type": "mcp_tool_call"},
            }
        )

    class Process:
        returncode = 0
        pid = 99999999
        stopped = False

        def poll(self):
            return None if overrun and not self.stopped else 0

        def wait(self, timeout=None):
            self.stopped = True
            return 0

    def popen(argv, *, stdout, stderr, start_new_session):
        for event in events:
            stdout.write(json.dumps(event) + "\n")
        stdout.flush()
        return Process()

    monkeypatch.setattr(runner, "identity", lambda: {"commit": "frozen"})
    monkeypatch.setattr(runner.subprocess, "Popen", popen)
    monkeypatch.setattr(runner.os, "killpg", lambda *_: None)
    monkeypatch.setattr(runner.time, "sleep", lambda *_: None)
    prompt = tmp_path / "input.txt"
    prompt.write_text("Fixed observation")
    runner.consumer(
        SimpleNamespace(
            output=tmp_path,
            label="run",
            prompt=prompt,
            question=None,
            prior=None,
            codex="unused",
            response_only=True,
            seconds=600,
        )
    )
    summary = json.loads((tmp_path / "run/summary.json").read_text())
    assert summary["has_final_assessment"] is expected


@pytest.mark.parametrize("stage", [1, 2])
@pytest.mark.parametrize(
    "invalid",
    [
        {"has_final_assessment": False},
        {"turn_completed": False},
        {"turn_failed": True},
        {"stop_reason": "tool_call_budget_overrun_observed"},
        {"exit_code": 1},
        {"source_unchanged": False},
        {"mcp_tool_calls": 0},
        {"turn_completed": None},
        {},
    ],
)
def test_publication_requires_completed_predecessors(
    tmp_path, monkeypatch, stage, invalid
):
    from tampu import config, repository

    summary = {
        "has_final_assessment": True,
        "turn_completed": True,
        "turn_failed": False,
        "stop_reason": None,
        "exit_code": 0,
        "source_unchanged": True,
        "mcp_tool_calls": 1,
    }
    growth = tmp_path / "tmp/prototype-readiness/growth"
    growth.mkdir(parents=True)
    (growth / f"r{stage - 1}-publication.json").write_text(
        json.dumps({"revision": {"revision_id": "previous"}})
    )
    # A valid predecessor must reach this existing-observation guard; no ingestion
    # or corpus mutation is allowed in this regression.
    (growth / f"r{stage}-publication.json").write_text("{}")
    manifest = tmp_path / "docs/experiments/2026-09-08-temporal-growth-manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text('{"artifacts": []}')
    consumers = tmp_path / "consumers"
    labels = ["eviction-r0", "legible-r0"] if stage == 1 else ["eviction-r1"]
    for label in labels:
        directory = consumers / label
        directory.mkdir(parents=True)
        (directory / "summary.json").write_text(json.dumps(summary | invalid))
    monkeypatch.setattr(runner, "identity", lambda: {"commit": "frozen"})
    monkeypatch.setattr(runner, "WT", tmp_path)
    monkeypatch.setattr(config, "load_config", dict)
    monkeypatch.setattr(
        repository,
        "Repository",
        lambda _: SimpleNamespace(
            resolve_revision=lambda *_: {"revision_id": "previous"}
        ),
    )
    match = "Predecessor" if invalid else "Refusing to overwrite"
    with pytest.raises(RuntimeError, match=match):
        runner.publish(SimpleNamespace(stage=stage, main=tmp_path, consumers=consumers))
