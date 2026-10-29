import argparse
import asyncio
import json

from experiments.consumer_run.serve import build
from experiments.consumer_run.test_gate import FakeService


def test_mcp_tools_route_through_gate(tmp_path):
    svc = FakeService()
    args = argparse.Namespace(max_calls=2, byte_cap=8192, ledger=tmp_path / "l.jsonl")
    server, gate = build(svc, args)

    async def go():
        out = []
        for _ in range(3):
            content = await server.call_tool("search", {"collection": "papers", "intent": "i",
                                                        "query": "q", "byte_budget": 32768})
            blocks = content[0] if isinstance(content, tuple) else content
            out.append(json.loads(blocks[0].text))
        return out

    results = asyncio.run(go())
    assert [r["status"] for r in results] == ["ok", "ok", "refused"]
    assert len(svc.calls) == 2
    assert all(kw["byte_budget"] == 8192 for _, kw in svc.calls)
    assert gate.summary()["refused_calls"] == 1
