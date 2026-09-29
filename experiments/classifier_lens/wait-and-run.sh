#!/usr/bin/env bash
# Wait for the shared 4090, then run one CLM pass under the Hamut'ay lease.
# Courtesy: require the card free on two checks five minutes apart.
set -uo pipefail
MODE="$1"
GPU=/home/tony/projects/hamutay/deploy/ayllu-gpu
PY=/home/tony/projects/tampu/tmp/clm-env/.venv/bin/python
RUNNER=/home/tony/projects/tampu/tmp/classifier-lens-worktree/experiments/classifier_lens/clm_run.py
DATA=/home/tony/projects/tampu/tmp/classifier-lens-20260929
free() { "$GPU" status 2>/dev/null | python3 -c 'import json,sys; s=json.load(sys.stdin); sys.exit(0 if s.get("state")=="free" else 1)'; }
consecutive=0
while [ $consecutive -lt 2 ]; do
  if free; then consecutive=$((consecutive+1)); else consecutive=0; fi
  echo "$(date -u +%FT%TZ) free_checks=$consecutive"
  [ $consecutive -lt 2 ] && sleep 300
done
echo "$(date -u +%FT%TZ) leasing for $MODE"
"$GPU" run --holder tampu --purpose "classifier lens diagnostic: CLM $MODE" --ttl 2h -- \
  "$PY" "$RUNNER" --mode "$MODE" --inputs "$DATA/clm-inputs.json" --out "$DATA"
status=$?
echo "$(date -u +%FT%TZ) ayllu-gpu run exited $status"
exit $status
