"""Jev scoring pass, per the frozen protocol (revision 2).

Scores every non-empty element of both artifacts once. This runner never
reads probe ordinals, pages or hashes. At most eight requests in flight.
Transport errors are retried at most twice; a returned answer is never
retried. The pass stops if the returned model changes or if reported
tokens, plus one token per two UTF-8 state bytes for calls with unknown
usage, exceed 20 million.
"""
import argparse
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

from typesafe_sdk import TypeSafeClient

from experiments.classifier_lens.common import JEV_MODEL, load_cases, nonempty_elements, question, sha
from experiments.classifier_lens.jev_repeatability import call, valid_score

WORKERS, TOKEN_CAP = 8, 20_000_000


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--compact", type=Path, required=True)
    args = parser.parse_args()
    raw_path = args.out / "jev-scoring.jsonl"
    assert not raw_path.exists(), "refusing to overwrite an earlier run"

    from tampu.config import load_config
    from tampu.repository import Repository
    repo = Repository(load_config(), initialize=False)
    cases = load_cases()
    jobs = []
    for case in cases["cases"]:
        projection = case["assessment_probes"][0]["projection_id"]  # identity only; probe fields unused
        payload = question(case["task"])
        for e in nonempty_elements(repo, projection):
            jobs.append(dict(case=case["id"], ordinal=e["ordinal"], state=e["text"], payload=payload))

    lock, stop = threading.Lock(), threading.Event()
    spent = [0]
    scores = {c["id"]: {} for c in cases["cases"]}
    missing = {c["id"]: [] for c in cases["cases"]}
    models = set()
    out = raw_path.open("a")
    local = threading.local()

    def client():
        if not hasattr(local, "c"):
            local.c = TypeSafeClient(timeout=60)
        return local.c

    def run(job):
        if stop.is_set():
            with lock:
                missing[job["case"]].append(job["ordinal"])
            return
        res = call(client(), job["state"], job["payload"])
        raw = res["raw"]
        model = raw.get("model") if raw else None
        score = valid_score(raw) if raw and model == JEV_MODEL else None
        tokens = (raw.get("usage") or {}).get("input_tokens") if raw else None
        rec = dict(case=job["case"], ordinal=job["ordinal"], state_sha256=sha(job["state"]), at=datetime.now(UTC).isoformat(),
                   model=model, score=score, input_tokens=tokens, latency_s=res.get("latency_s"),
                   retries=res["retries"], failed_attempts=res["failed_attempts"], raw=raw)
        with lock:
            out.write(json.dumps(rec) + "\n")
            if model:
                models.add(model)
            spent[0] += tokens if tokens is not None else len(job["state"].encode()) // 2
            if score is None:
                missing[job["case"]].append(job["ordinal"])
            else:
                scores[job["case"]][job["ordinal"]] = score
            if (raw and model != JEV_MODEL) or spent[0] > TOKEN_CAP:
                stop.set()

    started = datetime.now(UTC).isoformat()
    with ThreadPoolExecutor(WORKERS) as pool:
        list(pool.map(run, jobs))
    out.close()
    compact = dict(protocol="revision 2", model_requested=JEV_MODEL, models_returned=sorted(models),
                   started_at=started, finished_at=datetime.now(UTC).isoformat(),
                   stopped_early=stop.is_set(), tokens_counted_toward_cap=spent[0],
                   raw_records_sha256=sha(raw_path.read_text()),
                   cases={cid: dict(scored=len(s), missing=sorted(missing[cid]),
                                    scores={str(k): v for k, v in sorted(s.items())})
                          for cid, s in scores.items()})
    args.compact.write_text(json.dumps(compact) + "\n")
    print(json.dumps({k: v for k, v in compact.items() if k != "cases"}, indent=1))
    for cid, c in compact["cases"].items():
        print(cid, "scored", c["scored"], "missing", len(c["missing"]))


if __name__ == "__main__":
    main()
