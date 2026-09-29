#!/usr/bin/env bash
# Prepare CLM for the classifier lens diagnostic without the GPU lease.
set -euo pipefail
cd /home/tony/projects/tampu/tmp/clm-env
echo "== $(date -u +%FT%TZ) venv"
uv venv --python 3.12 .venv
echo "== $(date -u +%FT%TZ) install contrastive-lm 0.1.0 (pulls torch, vllm)"
VIRTUAL_ENV=$PWD/.venv uv pip install "contrastive-lm==0.1.0" "typesafe-sdk==0.7.1" huggingface_hub
.venv/bin/python -c "import vllm, torch, clm; print('vllm', vllm.__version__, 'torch', torch.__version__, 'cuda', torch.version.cuda)"
echo "== $(date -u +%FT%TZ) download Qwen/Qwen3-8B"
.venv/bin/hf download Qwen/Qwen3-8B
echo "== $(date -u +%FT%TZ) download CLM head"
.venv/bin/clm-download
echo "== $(date -u +%FT%TZ) tokenizer check against the protocol's measurement"
sha256sum ~/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/*/tokenizer.json ~/.cache/huggingface/hub/models--Qwen--Qwen3-4B/snapshots/*/tokenizer.json
echo "== $(date -u +%FT%TZ) done"
