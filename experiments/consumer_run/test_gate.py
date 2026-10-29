import json
import threading

import pytest

from experiments.consumer_run.gate import BudgetGate


class FakeService:
    def __init__(self, *, response=None, raise_exc=None, delay=None):
        self.calls = []
        self.response = response or {"status": "ok", "items": ["x"]}
        self.raise_exc = raise_exc
        self.delay = delay
        self.lock = threading.Lock()

    def _record(self, op, kwargs):
        with self.lock:
            self.calls.append((op, kwargs))
        if self.delay:
            self.delay.wait(2)
        if self.raise_exc:
            raise self.raise_exc
        return self.response

    def describe(self, **kw):
        return self._record("describe", kw)

    def search(self, **kw):
        return self._record("search", kw)

    def inspect(self, **kw):
        return self._record("inspect", kw)

    def finish(self, **kw):
        return self._record("finish", kw)


def ledger(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def test_excess_calls_are_refused_without_invoking_service(tmp_path):
    svc = FakeService()
    gate = BudgetGate(svc, max_calls=2, byte_cap=8192, ledger_path=tmp_path / "l.jsonl")
    gate.search(query="a")
    gate.inspect(evidence_handle="h")
    refused = gate.search(query="b")
    assert len(svc.calls) == 2
    assert refused["status"] == "refused"
    assert refused["error"]["code"] == "tool_call_budget_exhausted"
    rows = ledger(tmp_path / "l.jsonl")
    assert [r["admitted"] for r in rows] == [True, True, False]
    assert rows[2]["request"] == {"query": "b"}
    assert gate.summary()["admitted_calls"] == 2
    assert gate.summary()["refused_calls"] == 1


def test_service_errors_consume_allowance(tmp_path):
    svc = FakeService(response={"status": "error", "error": {"code": "bad"}})
    gate = BudgetGate(svc, max_calls=1, byte_cap=8192, ledger_path=tmp_path / "l.jsonl")
    assert gate.search(query="a")["status"] == "error"
    assert gate.search(query="a")["status"] == "refused"
    assert len(svc.calls) == 1
    assert gate.summary()["error_responses"] == 1


def test_exceptions_consume_allowance_and_propagate(tmp_path):
    svc = FakeService(raise_exc=RuntimeError("boom"))
    gate = BudgetGate(svc, max_calls=1, byte_cap=8192, ledger_path=tmp_path / "l.jsonl")
    with pytest.raises(RuntimeError):
        gate.search(query="a")
    assert gate.search(query="a")["status"] == "refused"
    row = ledger(tmp_path / "l.jsonl")[0]
    assert row["admitted"] and row["exception"].startswith("RuntimeError")


def test_concurrent_requests_cannot_exceed_limit(tmp_path):
    release = threading.Event()
    svc = FakeService(delay=release)
    gate = BudgetGate(svc, max_calls=3, byte_cap=8192, ledger_path=tmp_path / "l.jsonl")
    results = []
    threads = [threading.Thread(target=lambda: results.append(gate.search(query="q")))
               for _ in range(10)]
    for t in threads:
        t.start()
    release.set()
    for t in threads:
        t.join()
    assert len(svc.calls) == 3
    assert sum(r["status"] == "refused" for r in results) == 7


def test_byte_budget_is_clamped_to_cap(tmp_path):
    svc = FakeService()
    gate = BudgetGate(svc, max_calls=5, byte_cap=8192, ledger_path=tmp_path / "l.jsonl")
    gate.search(query="a", byte_budget=32768)
    gate.search(query="a")
    gate.search(query="a", byte_budget=1000)
    assert [kw["byte_budget"] for _, kw in svc.calls] == [8192, 8192, 1000]
    rows = ledger(tmp_path / "l.jsonl")
    assert rows[0]["request"]["byte_budget"] == 32768
    assert rows[0]["clamped_byte_budget"] == 8192


def test_recorded_bytes_match_actual_responses(tmp_path):
    from tampu.service import compact_json

    response = {"status": "ok", "text": "ñ" * 50}
    svc = FakeService(response=response)
    gate = BudgetGate(svc, max_calls=5, byte_cap=8192, ledger_path=tmp_path / "l.jsonl")
    out = gate.inspect(evidence_handle="h")
    actual = len(compact_json(out).encode("utf-8"))
    row = ledger(tmp_path / "l.jsonl")[0]
    assert row["response_bytes"] == actual
    assert row["request_bytes"] == len(compact_json({"evidence_handle": "h"}).encode("utf-8"))
    assert gate.summary()["response_bytes_total"] == actual


def test_oversized_response_is_flagged(tmp_path):
    svc = FakeService(response={"status": "ok", "text": "x" * 9000})
    gate = BudgetGate(svc, max_calls=5, byte_cap=8192, ledger_path=tmp_path / "l.jsonl")
    gate.search(query="a")
    assert ledger(tmp_path / "l.jsonl")[0]["over_byte_cap"] is True
    assert gate.summary()["over_byte_cap_responses"] == 1


@pytest.mark.parametrize("bad", ["big", None, 1.5])
def test_malformed_byte_budget_is_forwarded_for_the_service_to_reject(tmp_path, bad):
    svc = FakeService(response={"status": "error", "error": {"code": "invalid_argument"}})
    gate = BudgetGate(svc, max_calls=5, byte_cap=8192, ledger_path=tmp_path / "l.jsonl")
    assert gate.search(query="a", byte_budget=bad)["status"] == "error"
    assert svc.calls[0][1]["byte_budget"] == bad
    assert ledger(tmp_path / "l.jsonl")[0]["admitted"] is True
