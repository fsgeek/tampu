"""Apply the frozen case selection rule (2026-10-28-consumer-run-case-selection.md)."""

import hashlib
import json
import sys
from pathlib import Path

QUOTAS = {"likely_present": 4, "likely_absent": 2}
PER_PROJECT = 2


def h(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def select(rows, verified):
    pool = [r for r in rows if r["accepted"] and verified.get(r["episode_key"])
            and r["project"] != "tampu"]
    result = {}
    for stratum, quota in QUOTAS.items():
        members = sorted((r for r in pool if r["absence_likely"] == (stratum == "likely_absent")),
                         key=lambda r: h(r["episode_key"]))
        taken, per = [], {}
        ordering = []
        for r in members:
            take = len(taken) < quota and per.get(r["project"], 0) < PER_PROJECT
            if take:
                taken.append(r["episode_key"])
                per[r["project"]] = per.get(r["project"], 0) + 1
            ordering.append(dict(episode_key=r["episode_key"], key_sha256=h(r["episode_key"]),
                                 project=r["project"], selected=take))
        result[stratum] = dict(quota=quota, selected=taken, shortfall=quota - len(taken),
                               ordering=ordering)
    return result


def compact(rows, verified):
    return [dict(episode_key=r["episode_key"], project=r["project"], asker=r["asker"],
                 stratum="likely_absent" if r["absence_likely"] else "likely_present",
                 accepted=r["accepted"], reject_reason=r.get("reject_reason") or None,
                 conclusion_status=r["conclusion_status"],
                 verbatim_found=verified.get(r["episode_key"]),
                 question_sha256=h(r["question_verbatim"])) for r in rows]


if __name__ == "__main__":
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    rows = [json.loads(line) for line in (src / "candidates.jsonl").read_text().splitlines()]
    verified = {v["episode_key"]: v["verbatim_found"]
                for v in json.loads((src / "verify-results.json").read_text())}
    (out / "candidates-compact.json").write_text(json.dumps(compact(rows, verified), indent=1) + "\n")
    (out / "selection.json").write_text(json.dumps(select(rows, verified), indent=1) + "\n")
