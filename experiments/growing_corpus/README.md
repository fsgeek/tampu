# Growing-corpus development run

The thin `run.py` runner records real Codex CLI consumers and publications against the prepared local corpus. It refuses observations with an uncommitted worktree, records source hashes before/after, retains exact prompts, MCP schemas, CLI events, owner-enabled source-bearing service traces, usage and failures. No paper bytes or full traces belong in Git.

Prerequisites: Python 3.14, `uv sync`, configured dedicated Tampu database/user, existing extracted fixtures described in [the scenario](../../docs/experiments/2026-09-08-temporal-growth-scenario.md), authenticated Codex CLI, and its supported automatic approval review. The consumer sees only four MCP tools with temporary process-local state and an explicit owner trace. Shell, apps, browser, skills discovery and external search are disabled. This is a recorded CLI boundary, not an OS air gap. Automatic-review rejection must be retained without bypass.

From this worktree, with owner-local output directories:

```sh
uv run python experiments/growing_corpus/run.py consumer eviction-r0 --question eviction_initial --output /home/tony/projects/tampu/tmp/prototype-readiness/consumers
uv run python experiments/growing_corpus/run.py consumer legible-r0 --question legible_initial --output /home/tony/projects/tampu/tmp/prototype-readiness/consumers
uv run python experiments/growing_corpus/run.py publish 1 --main /home/tony/projects/tampu --consumers /home/tony/projects/tampu/tmp/prototype-readiness/consumers
uv run python experiments/growing_corpus/run.py consumer eviction-r1 --question eviction_successor --prior /home/tony/projects/tampu/tmp/prototype-readiness/consumers/eviction-r0/assessment.txt --output /home/tony/projects/tampu/tmp/prototype-readiness/consumers
uv run python experiments/growing_corpus/run.py publish 2 --main /home/tony/projects/tampu --consumers /home/tony/projects/tampu/tmp/prototype-readiness/consumers
uv run python experiments/growing_corpus/run.py consumer eviction-r2 --question eviction_successor --prior /home/tony/projects/tampu/tmp/prototype-readiness/consumers/eviction-r1/assessment.txt --output /home/tony/projects/tampu/tmp/prototype-readiness/consumers
uv run python experiments/growing_corpus/run.py consumer legible-r2 --question legible_successor --prior /home/tony/projects/tampu/tmp/prototype-readiness/consumers/legible-r0/assessment.txt --output /home/tony/projects/tampu/tmp/prototype-readiness/consumers
```

The first actual r0 publication predates this runner and is deliberately reused. Successors are guarded by the recorded immediate predecessor and completed original prior-stage runs. Each question has a 20-call/600-second instruction; the process monitor detects and records an observed 21st call rather than claiming prevention. Consumers use requested `gpt-5.6-sol`, medium reasoning, CLI default sampling/output limit; CLI does not expose a resolved model revision. Each successor receives only its preceding assessment/citations: staged resumption, not continuous process memory. Never edit source during observations or publish a successor while original consumers at the predecessor are running.

The response-only comparison option takes a frozen `--prompt` with `--response-only` and exposes no MCP tools. Its payloads, masks and visible-evidence scoring sheet must be frozen before those observations. These are exposed development tasks and cannot establish statistical benefit.
