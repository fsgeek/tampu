"""CLM lens runner, per the frozen protocol (revision 2). Runs under the GPU lease:

    ayllu-gpu run --holder tampu --purpose "..." --ttl 2h -- python clm_run.py --mode repeatability ...

Starts the Qwen3-8B vLLM encoder with prefix caching disabled, records the
lens identity, runs a synthetic schema check, then either:

  repeatability  three repetitions over Jev's sample, each with a new Engine
                 and Embedder and the vector arena disabled; any state that
                 spent zero encoder tokens is excluded and reported.
  scoring        every element once. Reads only element texts.

Stops the encoder on exit, which lets the lease release the card.
"""
import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import requests

os.environ["CLM_ACTION_CACHE"] = "0"
URL, PORT, ENCODER = "http://127.0.0.1:8090/v1/embeddings", 8090, "Qwen/Qwen3-8B"


def sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def start_encoder(log):
    vllm = str(Path(sys.executable).with_name("vllm"))
    proc = subprocess.Popen([vllm, "serve", ENCODER, "--served-model-name", "qwen3-8b", "--runner", "pooling",
                             "--max-model-len", "2048", "--port", str(PORT), "--no-enable-prefix-caching"],
                            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    deadline = time.monotonic() + 1200
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"encoder exited with {proc.returncode}")
        try:
            if requests.get(f"http://127.0.0.1:{PORT}/v1/models", timeout=2).ok:
                return proc
        except requests.RequestException:
            pass
        time.sleep(5)
    raise RuntimeError("encoder not ready within 20 minutes")


def stop_encoder(proc):
    if proc and proc.poll() is None:
        os.killpg(proc.pid, signal.SIGTERM)
        try:
            proc.wait(90)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)


def new_engine():
    from clm import Engine
    from clm.embedder import Embedder
    return Engine(embedder=Embedder(URL, "qwen3-8b", max_tokens=2048), action_cache=0)


def identity():
    import clm
    from clm.heads import default_checkpoint
    from importlib.metadata import version
    ckpt = default_checkpoint()
    snaps = sorted(Path.home().glob(".cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/*/tokenizer.json"))
    return dict(package=f"contrastive-lm {version('contrastive-lm')}", head_file=ckpt, head_sha256=sha_file(ckpt),
                encoder=ENCODER, encoder_tokenizer_sha256=sha_file(snaps[-1]) if snaps else None,
                vllm=version("vllm"), prefix_caching="disabled", action_cache="disabled")


def score(engine, state, q):
    r = engine.answer(state, {"relevant": q})
    a = r["answers"]["relevant"]
    p = a.get("noul") if isinstance(a, dict) else None
    return (p if isinstance(p, (int, float)) and 0 <= p <= 1 else None), r["usage"]["input_tokens"], r["model"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("repeatability", "scoring"), required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    raw_path = args.out / f"clm-{args.mode}.jsonl"
    assert not raw_path.exists(), "refusing to overwrite an earlier run"
    inputs = json.loads(args.inputs.read_text())
    log = open(args.out / f"clm-{args.mode}-encoder.log", "a")
    proc = None
    try:
        proc = start_encoder(log)
        ident = identity()
        engine = new_engine()
        synthetic = score(engine, "The sky was a pale blue over the harbour that morning.",
                          {"type": "noul", "instructions": "A researcher is investigating this task: Decide whether the "
                           "sky is described. Does this passage contain information that would help complete the task?"})
        header = dict(kind="header", mode=args.mode, at=datetime.now(UTC).isoformat(), identity=ident,
                      inputs_sha256=sha_file(args.inputs), schema_check=dict(noul=synthetic[0], model=synthetic[2]))
        assert synthetic[0] is not None, "schema check failed: no valid answers.relevant.noul"
        with raw_path.open("a") as out:
            out.write(json.dumps(header) + "\n")
            if args.mode == "repeatability":
                for repeat in range(3):
                    engine = new_engine()  # fresh Engine and Embedder: empty text cache
                    for cid, case in inputs.items():
                        texts = {e["ordinal"]: e["text"] for e in case["elements"]}
                        for ordinal in case["repeat_sample"]:
                            t0 = time.monotonic()
                            p, tokens, model = score(engine, texts[ordinal], case["question"])
                            out.write(json.dumps(dict(case=cid, ordinal=ordinal, repeat=repeat, score=p,
                                                      encoder_tokens=tokens, fresh=tokens > 0, model=model,
                                                      latency_s=time.monotonic() - t0)) + "\n")
            else:
                for cid, case in inputs.items():
                    for e in case["elements"]:
                        t0 = time.monotonic()
                        p, tokens, model = score(engine, e["text"], case["question"])
                        out.write(json.dumps(dict(case=cid, ordinal=e["ordinal"], score=p, encoder_tokens=tokens,
                                                  model=model, latency_s=time.monotonic() - t0)) + "\n")
            out.write(json.dumps(dict(kind="footer", at=datetime.now(UTC).isoformat(),
                                      head_sha256_after=sha_file(ident["head_file"]))) + "\n")
    finally:
        stop_encoder(proc)
        log.close()
    print("done", raw_path)


if __name__ == "__main__":
    main()
