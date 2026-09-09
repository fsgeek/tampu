"""Verify custody, actual service trace, navigation replay, and assessment offline."""
import inspect
import json
import sys
from pathlib import Path

from run import Service, assess, navigate, sha, wire


def main():
    capture = Path(sys.argv[1])
    config = json.loads(Path(__file__).with_name("cases.json").read_text())
    record = json.loads((capture / "record.json").read_text())
    expected = json.loads((capture / "results.json").read_text())
    assert record["config_sha256"] == sha(wire(config))
    computed = assess(record, config)
    computed.update(record_sha256=sha(wire(record)), config_sha256=sha(wire(config)))
    assert computed == expected
    trace = [json.loads(line) for line in (capture / "service-trace.jsonl").read_text().splitlines()]
    calls = [call for case in record["cases"] for call in case["calls"]]
    assert len(trace) == len(calls)
    for traced, call in zip(trace, calls, strict=True):
        bound = inspect.signature(getattr(Service, call["operation"])).bind(None, **call["arguments"])
        bound.apply_defaults()
        arguments = {k: v for k, v in bound.arguments.items() if k != "self"}
        assert traced == dict(operation=call["operation"], arguments=arguments, response=call["response"])

    class RecordedService:
        def __init__(self, calls):
            self.calls, self.position = calls, 0

        def __getattr__(self, operation):
            def call(**arguments):
                expected = self.calls[self.position]
                assert operation == expected["operation"]
                assert arguments == expected["arguments"]
                self.position += 1
                return expected["response"]
            return call

    limits = {k: config[k] for k in ("collection", "revision_id", "calls_per_case", "byte_budget")}
    for case, recorded in zip(config["cases"], record["cases"], strict=True):
        service = RecordedService(recorded["calls"])
        inputs = {k: case[k] for k in ("id", "artifact_id", "task", "queries")}
        assert navigate(service, inputs, limits) == recorded["calls"]
        assert service.position == len(recorded["calls"])
    print(f"Verified {len(calls)} calls: exact response accounting, method defaults, navigation replay, and assessment.")


if __name__ == "__main__":
    main()
