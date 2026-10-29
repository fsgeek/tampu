"""Hard tool-call and byte budget at the evaluation server boundary.

The growing-corpus runner observes an overrun after it happens. This gate
reserves a call slot before the service runs, so an excess or concurrent
request never reaches the service. Errors and exceptions consume their slot.
"""

from __future__ import annotations

import json
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tampu.service import compact_json

OPERATIONS = ("describe", "search", "inspect", "finish")


def _bytes(value) -> int:
    return len(compact_json(value).encode("utf-8"))


class BudgetGate:
    def __init__(self, service, *, max_calls: int, byte_cap: int, ledger_path: Path):
        self._service = service
        self._max_calls = max_calls
        self._byte_cap = byte_cap
        self._ledger_path = Path(ledger_path)
        self._lock = threading.Lock()
        self._admitted = 0
        self._refused = 0
        self._errors = 0
        self._over_cap = 0
        self._response_bytes = 0
        self._sequence = 0

    def __getattr__(self, name):
        if name in OPERATIONS:
            return lambda **kwargs: self._call(name, kwargs)
        raise AttributeError(name)

    def _write(self, row):
        with self._lock:
            with self._ledger_path.open("a") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def _call(self, op, kwargs):
        with self._lock:
            self._sequence += 1
            sequence = self._sequence
            admitted = self._admitted < self._max_calls
            if admitted:
                self._admitted += 1
            else:
                self._refused += 1
        row: dict[str, Any] = dict(sequence=sequence, op=op, at=datetime.now(UTC).isoformat(),
                   admitted=admitted, request=kwargs, request_bytes=_bytes(kwargs))
        if not admitted:
            response = {"status": "refused", "error": {
                "code": "tool_call_budget_exhausted",
                "message": f"This investigation is limited to {self._max_calls} tool calls; "
                           "no further operations will run. Give your final answer now.",
                "limit": self._max_calls}}
            row.update(response_bytes=_bytes(response), status="refused")
            self._write(row)
            return response
        forwarded = dict(kwargs)
        requested = forwarded.get("byte_budget", self._byte_cap)
        if isinstance(requested, int) and not isinstance(requested, bool):
            forwarded["byte_budget"] = min(requested, self._byte_cap)
            if forwarded["byte_budget"] != requested:
                row["clamped_byte_budget"] = forwarded["byte_budget"]
        # Anything else is forwarded unchanged; the service's own validation rejects it.
        started = time.monotonic()
        try:
            response = getattr(self._service, op)(**forwarded)
        except Exception as e:
            row.update(exception=f"{type(e).__name__}: {str(e)[:300]}",
                       latency_s=time.monotonic() - started)
            self._write(row)
            raise
        size = _bytes(response)
        over = size > self._byte_cap
        is_error = isinstance(response, dict) and response.get("status") == "error"
        with self._lock:
            self._response_bytes += size
            self._errors += is_error
            self._over_cap += over
        row.update(status=response.get("status") if isinstance(response, dict) else None,
                   response_bytes=size, over_byte_cap=over,
                   latency_s=time.monotonic() - started)
        self._write(row)
        return response

    def summary(self):
        with self._lock:
            return dict(max_calls=self._max_calls, byte_cap=self._byte_cap,
                        admitted_calls=self._admitted, refused_calls=self._refused,
                        error_responses=self._errors,
                        over_byte_cap_responses=self._over_cap,
                        response_bytes_total=self._response_bytes)
