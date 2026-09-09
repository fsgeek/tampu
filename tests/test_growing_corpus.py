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
