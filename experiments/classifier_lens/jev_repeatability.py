"""Jev operational repeatability, per the frozen protocol (revision 2).

Each sampled element's identical request is sent three times, sequentially.
At most eight elements are in flight. Transport errors are retried at most
twice; a returned answer is never retried. Raw records stay owner-local.
"""
import argparse
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

from typesafe_sdk import Noul, TypeSafeClient

from experiments.classifier_lens.common import (
    JEV_MODEL, load_cases, nonempty_elements, question, repeatability_sample, sha, summarize)

REPEATS, WORKERS, RETRIES = 3, 8, 2


class ModelChanged(Exception):
    pass


def call(client, state, payload):
    attempts = []
    for attempt in range(RETRIES + 1):
        started = time.monotonic()
        try:
            r = client.system_one(state=state, questions={"relevant": Noul(**{k: v for k, v in payload.items() if k != "type"})},
                                  model=JEV_MODEL)
        except Exception as e:  # transport or service error: retry within the bound
            attempts.append(dict(error=f"{type(e).__name__}: {str(e)[:300]}", latency_s=time.monotonic() - started))
            continue
        raw = r.model_dump(mode="json")
        return dict(raw=raw, latency_s=time.monotonic() - started, retries=len(attempts), failed_attempts=attempts)
    return dict(raw=None, retries=len(attempts), failed_attempts=attempts)


def valid_score(raw):
    try:
        p = raw["answers"]["relevant"]["noul"]
    except (KeyError, TypeError):
        return None
    return p if isinstance(p, (int, float)) and 0 <= p <= 1 else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="owner-local directory for raw records")
    parser.add_argument("--compact", type=Path, required=True, help="compact results JSON for Git")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    raw_path = args.out / "jev-repeatability.jsonl"
    assert not raw_path.exists(), "refusing to overwrite an earlier run"

    from tampu.config import load_config
    from tampu.repository import Repository
    repo = Repository(load_config(), initialize=False)
    cases = load_cases()

    jobs = []
    overlap = {}
    for case in cases["cases"]:
        probes = case["assessment_probes"]
        elements = nonempty_elements(repo, probes[0]["projection_id"])
        sample, overlap[case["id"]] = repeatability_sample(elements, [p["ordinal"] for p in probes])
        payload = question(case["task"])
        probe_set = {p["ordinal"] for p in probes}
        for e in sample:
            jobs.append(dict(case=case["id"], ordinal=e["ordinal"], state=e["text"], payload=payload,
                             is_probe=e["ordinal"] in probe_set))

    lock = threading.Lock()
    stop = threading.Event()
    records = []
    out = raw_path.open("a")

    def run(job):
        with TypeSafeClient(timeout=60) as client:
            for repeat in range(REPEATS):
                if stop.is_set():
                    return
                res = call(client, job["state"], job["payload"])
                raw = res["raw"]
                model = raw.get("model") if raw else None
                rec = dict(case=job["case"], ordinal=job["ordinal"], is_probe=job["is_probe"], repeat=repeat,
                           state_sha256=sha(job["state"]), question=job["payload"], at=datetime.now(UTC).isoformat(),
                           model=model, score=valid_score(raw) if raw else None,
                           input_tokens=(raw.get("usage") or {}).get("input_tokens") if raw else None,
                           latency_s=res.get("latency_s"), retries=res["retries"],
                           failed_attempts=res["failed_attempts"], raw=raw)
                with lock:
                    records.append(rec)
                    out.write(json.dumps(rec) + "\n"); out.flush()
                if raw and model != JEV_MODEL:
                    stop.set()
                    raise ModelChanged(model)

    started = datetime.now(UTC).isoformat()
    with ThreadPoolExecutor(WORKERS) as pool:
        futures = [pool.submit(run, j) for j in jobs]
        errors = [f.exception() for f in futures if f.exception()]
    out.close()

    per_case = {}
    for case in cases["cases"]:
        values, missing, probe_values = {}, 0, {}
        for rec in records:
            if rec["case"] != case["id"]:
                continue
            if rec["score"] is None:
                missing += 1
                continue
            values.setdefault(rec["ordinal"], []).append(rec["score"])
        complete = {k: v for k, v in values.items() if len(v) == REPEATS}
        for p in case["assessment_probes"]:
            probe_values[str(p["ordinal"])] = values.get(p["ordinal"])
        tokens = [r["input_tokens"] for r in records if r["case"] == case["id"]]
        lat = sorted(r["latency_s"] for r in records if r["case"] == case["id"] and r["latency_s"] is not None)
        first_vs_repeat = {}
        for k in (0, 1, 2):
            ls = sorted(r["latency_s"] for r in records if r["case"] == case["id"] and r["repeat"] == k and r["latency_s"])
            first_vs_repeat[f"repeat_{k}_median_latency_s"] = ls[len(ls) // 2] if ls else None
        per_case[case["id"]] = dict(
            sampled_elements=len({r["ordinal"] for r in records if r["case"] == case["id"]}),
            probes_already_in_random_sample=overlap[case["id"]],
            missing_scores=missing, elements_with_all_repeats=len(complete),
            stats=summarize(complete), probe_scores=probe_values,
            input_tokens_reported=sum(t for t in tokens if t is not None),
            calls_with_unknown_usage=sum(t is None for t in tokens),
            median_latency_s=lat[len(lat) // 2] if lat else None, **first_vs_repeat,
            retries=sum(r["retries"] for r in records if r["case"] == case["id"]))

    compact = dict(protocol="docs/superpowers/specs/2026-09-28-classifier-lens-diagnostic-protocol.md (revision 2)",
                   measurement="Jev operational repeatability; TypeSafe caching undisclosed",
                   model_requested=JEV_MODEL, models_returned=sorted({r["model"] for r in records if r["model"]}),
                   started_at=started, finished_at=datetime.now(UTC).isoformat(), calls=len(records),
                   worker_errors=[f"{type(e).__name__}: {e}" for e in errors],
                   raw_records_sha256=sha(raw_path.read_text()), cases=per_case,
                   note_on_wording="Task text ends with a period; verbatim substitution yields '..' before 'Does'.")
    args.compact.write_text(json.dumps(compact, indent=1) + "\n")
    print(json.dumps({k: v for k, v in compact.items() if k != "cases"}, indent=1))
    for cid, c in per_case.items():
        print(cid, json.dumps(c["stats"]), "missing", c["missing_scores"], "tokens", c["input_tokens_reported"])


if __name__ == "__main__":
    main()
