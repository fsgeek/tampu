"""Thin owner-local runner for the fixed growing-corpus development observation."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import shutil
import signal
import subprocess
import time
from pathlib import Path

WT = Path(__file__).resolve().parents[2]
IMAGE = "downloads.unstructured.io/unstructured-io/unstructured@sha256:806726e3997d33bce9e32facd86c947b241101c58496f2774ad5f09f86e798bc"


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity():
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=normal"], cwd=WT, text=True
    )
    if dirty:
        raise RuntimeError(
            "Freeze and commit tracked implementation/inputs before observation"
        )
    return {
        "commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=WT, text=True
        ).strip(),
        "source_sha256": {
            str(p.relative_to(WT)): digest(p)
            for base in ["src/tampu", "experiments/growing_corpus"]
            for p in sorted((WT / base).rglob("*"))
            if p.is_file() and "__pycache__" not in str(p)
        },
    }


def consumer(args):
    before = identity()
    out = args.output / args.label
    out.mkdir(parents=True, exist_ok=False)
    prompts = json.loads((WT / "experiments/growing_corpus/prompts.json").read_text())
    if args.prompt:
        prompt = args.prompt.read_text()
    else:
        prompt = prompts["common_instructions"] + prompts[args.question]
        if args.prior:
            prompt += (
                "\n\nPrior consumer assessment (staged resumption):\n"
                + args.prior.read_text()
            )
    (out / "prompt.txt").write_text(prompt)
    empty = args.output / "empty-cwd"
    empty.mkdir(exist_ok=True)
    argv = [
        args.codex,
        "exec",
        "--ignore-user-config",
        "--skip-git-repo-check",
        "--ephemeral",
        "--json",
        "--sandbox",
        "read-only",
        "-C",
        str(empty),
    ]
    for name in [
        "shell_tool",
        "multi_agent",
        "apps",
        "browser_use",
        "computer_use",
        "image_generation",
        "view_image",
        "skill_search",
    ]:
        argv += ["--disable", name]
    argv += [
        "--enable",
        "skip_host_skill_discovery",
        "-c",
        'web_search="disabled"',
        "-c",
        "project_doc_max_bytes=0",
        "-c",
        'model_reasoning_effort="medium"',
        "-m",
        "gpt-5.6-sol",
        "-c",
        'approval_policy="on-request"',
        "-c",
        'approvals_reviewer="auto_review"',
    ]
    if not args.response_only:
        from tampu.config import load_config
        from tampu.mcp_server import create_server
        from tampu.repository import Repository
        from tampu.service import Service

        server = create_server(Service(Repository(load_config(), initialize=False)))
        schemas = [x.model_dump(mode="json") for x in asyncio.run(server.list_tools())]
        write(out / "tool-schemas.json", schemas)
        for tool in ["describe", "search", "inspect", "finish"]:
            argv += ["-c", f"mcp_servers.tampu.tools.{tool}.output_token_limit=32768"]
        argv += [
            "-c",
            "mcp_servers.tampu.command=" + json.dumps(str(WT / ".venv/bin/tampu")),
            "-c",
            "mcp_servers.tampu.args="
            + json.dumps(["serve", "--trace", str(out / "service-trace.jsonl")]),
            "-c",
            "mcp_servers.tampu.enabled_tools="
            + json.dumps(["describe", "search", "inspect", "finish"]),
        ]
    argv.append(prompt)
    write(
        out / "invocation.json",
        {
            "argv": argv[:-1] + ["<prompt.txt>"],
            "requested_model": "gpt-5.6-sol",
            "resolved_model_revision": "not exposed by CLI events",
            "reasoning_effort": "medium",
            "sampling": "CLI/model defaults; no temperature override",
            "output_token_cap": "CLI/model default; not explicitly configurable in this invocation",
            "prompt_sha256": digest(out / "prompt.txt"),
            "source_before": before,
            "limits": {
                "seconds": args.seconds,
                "tool_calls": 0 if args.response_only else 20,
            },
            "boundary": "CLI feature/tool restrictions; not an OS air gap",
        },
    )
    start = time.monotonic()
    reason = None
    with (
        (out / "events.jsonl").open("w") as stdout,
        (out / "stderr.txt").open("w") as stderr,
    ):
        process = subprocess.Popen(
            argv, stdout=stdout, stderr=stderr, start_new_session=True
        )
        while process.poll() is None:
            time.sleep(0.25)
            calls = set()
            for event in events(out):
                item = event.get("item", {})
                if item.get("type") == "mcp_tool_call":
                    calls.add(item["id"])
            if time.monotonic() - start > args.seconds:
                reason = "wall_time_budget"
            elif len(calls) > (0 if args.response_only else 20):
                reason = "tool_call_budget_overrun_observed"
            if reason:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                break
    items, usage = {}, []
    for event in events(out):
        if "item" in event:
            items[event["item"]["id"]] = event["item"]
        if event.get("type") == "turn.completed":
            usage.append(event.get("usage"))
    final = "\n\n".join(
        x.get("text", "") for x in items.values() if x.get("type") == "agent_message"
    )
    (out / "assessment.txt").write_text(final)
    after = identity()
    summary = {
        "exit_code": process.returncode,
        "stop_reason": reason,
        "wall_seconds": time.monotonic() - start,
        "mcp_tool_calls": sum(x.get("type") == "mcp_tool_call" for x in items.values()),
        "usage": usage,
        "item_types": sorted({x.get("type", "unknown") for x in items.values()}),
        "has_final_assessment": bool(final),
        "source_after": after,
        "source_unchanged": before == after,
        "files": {
            p.name: {"sha256": digest(p), "bytes": p.stat().st_size}
            for p in sorted(out.iterdir())
            if p.is_file()
        },
    }
    write(out / "summary.json", summary)
    print(
        json.dumps(
            {
                "run": str(out),
                **{
                    k: v
                    for k, v in summary.items()
                    if k not in ["files", "source_after"]
                },
            }
        ),
        flush=True,
    )


def events(out):
    for line in (out / "events.jsonl").read_text().splitlines():
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def publish(args):
    from tampu.config import load_config
    from tampu.repository import Repository

    before = identity()
    stage, main = args.stage, args.main
    out, root = (
        main / "tmp/prototype-readiness/growth",
        main / "tmp/prototype-growth-working",
    )
    manifest = json.loads(
        (WT / "docs/experiments/2026-09-08-temporal-growth-manifest.json").read_text()
    )
    expected = {
        x["sha256"]: x for x in manifest["artifacts"] if x["first_stage"] <= stage
    }
    repo = Repository(load_config())
    previous = json.loads((out / f"r{stage - 1}-publication.json").read_text())[
        "revision"
    ]
    if (
        repo.resolve_revision("research", None)["revision_id"]
        != previous["revision_id"]
    ):
        raise RuntimeError(
            "Current revision must equal the recorded immediate predecessor"
        )
    prerequisites = ["eviction-r0", "legible-r0"] if stage == 1 else ["eviction-r1"]
    for label in prerequisites:
        summary = json.loads((args.consumers / label / "summary.json").read_text())
        if not summary["source_unchanged"] or summary["mcp_tool_calls"] < 1:
            raise RuntimeError(
                "Predecessor original observation must be recorded before growth"
            )
    if (out / f"r{stage}-publication.json").exists():
        raise RuntimeError("Refusing to overwrite a publication observation")
    started = time.monotonic()
    for aid, entry in expected.items():
        src = main / f"tmp/temporal-growth-20260908/r{stage}" / entry["replay_path"]
        dst = root / entry["replay_path"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            shutil.copy2(src, dst)
        if digest(dst) != aid:
            raise RuntimeError("Fixture hash mismatch")
    if {digest(p) for p in root.rglob("*.pdf")} != set(expected):
        raise RuntimeError("Unexpected working-root membership")
    metadata = {
        k: v
        for k, v in json.loads(
            (main / "tmp/prototype-readiness/curated-metadata.json").read_text()
        ).items()
        if k in expected
    }
    for value in metadata.values():
        value["publication_date"]["precision"] = "day"
    write(out / f"r{stage}-metadata.json", metadata)
    revision = repo.ingest(
        "research", root, profile="unstructured", image=IMAGE, metadata=metadata
    )
    after = identity()
    record = {
        "stage": f"r{stage}",
        "source_before": before,
        "source_after": after,
        "source_unchanged": before == after,
        "wall_seconds": time.monotonic() - started,
        "revision": revision,
    }
    write(out / f"r{stage}-publication.json", record)
    assert revision["counts"]["artifacts"] == [160, 320, 473][stage]
    assert revision["parent_revision"] == previous["revision_id"]
    print(json.dumps(record), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    p = sub.add_parser("consumer")
    p.add_argument("label")
    p.add_argument(
        "--question",
        choices=[
            "eviction_initial",
            "eviction_successor",
            "legible_initial",
            "legible_successor",
        ],
    )
    p.add_argument("--prior", type=Path)
    p.add_argument("--prompt", type=Path)
    p.add_argument("--response-only", action="store_true")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--codex", default="/home/tony/.bun/bin/codex")
    p.add_argument("--seconds", type=int, default=600)
    p.set_defaults(func=consumer)
    p = sub.add_parser("publish")
    p.add_argument("stage", type=int, choices=[1, 2])
    p.add_argument("--main", type=Path, required=True)
    p.add_argument("--consumers", type=Path, required=True)
    p.set_defaults(func=publish)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
