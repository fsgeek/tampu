from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import load_config
from .errors import TampuError
from .mcp_server import run_server
from .repository import Repository
from .service import Service, compact_json


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tampu")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init", help="initialize Tampu storage schema")

    ingest = commands.add_parser("ingest", help="publish a collection revision")
    ingest.add_argument("collection")
    ingest.add_argument("root", type=Path)
    ingest.add_argument("--profile", required=True, choices=("poppler", "unstructured"))
    ingest.add_argument("--image")
    ingest.add_argument("--metadata", type=Path)

    describe = commands.add_parser("describe", help="describe published collections")
    describe.add_argument("--collection")
    describe.add_argument("--byte-budget", type=int, default=8192)

    serve = commands.add_parser("serve", help="serve the four MCP tools over stdio")
    serve.add_argument("--trace", type=Path)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    try:
        config = load_config()
        if args.command == "init":
            Repository(config, initialize=True)
            response = {"status": "ok", "result": {"initialized": True}}
        elif args.command == "ingest":
            metadata = None
            if args.metadata is not None:
                try:
                    metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
                except (OSError, ValueError, TypeError) as error:
                    raise TampuError(
                        "invalid_metadata", "Metadata assertions could not be loaded."
                    ) from error
            revision = Repository(config, initialize=True).ingest(
                args.collection,
                args.root,
                profile=args.profile,
                image=args.image,
                metadata=metadata,
            )
            response = {"status": "ok", "result": revision}
        elif args.command == "describe":
            response = Service(
                Repository(config, initialize=False)
            ).describe(collection=args.collection, byte_budget=args.byte_budget)
        else:
            run_server(trace_path=args.trace)
            return
        sys.stdout.write(compact_json(response) + "\n")
    except TampuError as error:
        sys.stderr.write(
            compact_json(
                {
                    "status": "error",
                    "error": {"code": error.code, "message": error.message},
                }
            )
            + "\n"
        )
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
