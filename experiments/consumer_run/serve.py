"""Serve the four Tampu tools over stdio behind a hard BudgetGate."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from experiments.consumer_run.gate import BudgetGate


def build(service, args):
    from tampu.mcp_server import create_server

    gate = BudgetGate(service, max_calls=args.max_calls, byte_cap=args.byte_cap,
                      ledger_path=args.ledger)
    return create_server(gate), gate


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--max-calls", type=int, required=True)
    p.add_argument("--byte-cap", type=int, required=True)
    p.add_argument("--ledger", type=Path, required=True)
    p.add_argument("--trace", type=Path, required=True)
    args = p.parse_args(argv)

    from tampu.config import load_config
    from tampu.repository import Repository
    from tampu.service import Service

    operations = logging.getLogger("tampu.operations")
    if not operations.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("%(message)s"))
        operations.addHandler(handler)
    operations.setLevel(logging.INFO)
    operations.propagate = False
    service = Service(Repository(load_config(), initialize=False), trace_path=args.trace)
    server, _ = build(service, args)
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
