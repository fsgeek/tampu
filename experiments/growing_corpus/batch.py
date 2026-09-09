"""Execute the sixteen frozen response-only observations in recorded randomized order."""

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--inputs", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    freeze = json.loads((a.inputs / "freeze.json").read_text())
    order = freeze["execution_order"]
    assert len(order) == 16 and len(set(order)) == 16
    for item in freeze["payloads"]:
        assert (
            hashlib.sha256(
                (a.inputs / (item["label"] + ".txt")).read_bytes()
            ).hexdigest()
            == item["prompt_sha256"]
        )
    a.output.mkdir(parents=True, exist_ok=True)
    record = a.output / "batch-schedule.json"
    if record.exists():
        raise RuntimeError("Refusing to overwrite original response-only batch")
    schedule = {
        "seed": freeze["seed"],
        "maximum_concurrent_processes": 4,
        "launch_order": order,
        "events": [],
        "inputs_freeze_sha256": hashlib.sha256(
            (a.inputs / "freeze.json").read_bytes()
        ).hexdigest(),
    }

    def save():
        record.write_text(json.dumps(schedule, indent=2) + "\n")

    running = {}
    pending = list(order)
    while running or pending:
        while pending and len(running) < 4:
            label = pending.pop(0)
            argv = [
                sys.executable,
                str(Path(__file__).with_name("run.py")),
                "consumer",
                label,
                "--prompt",
                str(a.inputs / (label + ".txt")),
                "--response-only",
                "--output",
                str(a.output),
            ]
            log = (a.output / (label + "-runner.log")).open("w")
            proc = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT)
            running[label] = (proc, log)
            schedule["events"].append(
                {
                    "event": "launch",
                    "label": label,
                    "timestamp": time.time(),
                    "argv": argv,
                }
            )
            save()
        time.sleep(0.25)
        for label, (proc, log) in list(running.items()):
            if proc.poll() is not None:
                log.close()
                del running[label]
                schedule["events"].append(
                    {
                        "event": "completed",
                        "label": label,
                        "timestamp": time.time(),
                        "exit_code": proc.returncode,
                    }
                )
                save()
                print(json.dumps(schedule["events"][-1]), flush=True)
    schedule["completed"] = True
    save()


if __name__ == "__main__":
    main()
