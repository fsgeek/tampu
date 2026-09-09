#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import secrets
import stat
from pathlib import Path

from arango import ArangoClient
from arango.exceptions import ArangoError


def _admin(path: Path | None) -> dict:
    if path is not None:
        value = json.loads(path.read_text(encoding="utf-8"))
    else:
        value = {
            "endpoint": os.environ.get("TAMPU_ADMIN_ENDPOINT"),
            "username": os.environ.get("TAMPU_ADMIN_USERNAME"),
            "password": os.environ.get("TAMPU_ADMIN_PASSWORD"),
        }
    if any(
        not isinstance(value.get(key), str) or not value[key]
        for key in ("endpoint", "username", "password")
    ):
        raise RuntimeError("Explicit administrator credentials are required.")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Provision a dedicated Tampu ArangoDB database and user."
    )
    parser.add_argument("--admin-file", type=Path)
    parser.add_argument("--database", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    created_database = False
    created_user = False
    try:
        admin = _admin(args.admin_file)
        system = ArangoClient(hosts=admin["endpoint"]).db(
            "_system", username=admin["username"], password=admin["password"]
        )
        if system.has_database(args.database) or system.has_user(args.username):
            raise RuntimeError(
                "The requested database or user already exists; refusing reuse."
            )
        password = secrets.token_urlsafe(36)
        system.create_database(args.database)
        created_database = True
        system.create_user(args.username, password=password, active=True)
        created_user = True
        system.update_permission(args.username, "rw", database=args.database)
        args.store.expanduser().resolve().mkdir(parents=True, exist_ok=True)
        payload = {
            "endpoint": admin["endpoint"],
            "database": args.database,
            "username": args.username,
            "password": password,
            "store": str(args.store.expanduser().resolve()),
        }
        args.config.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(
            args.config,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            stat.S_IRUSR | stat.S_IWUSR,
        )
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2)
            stream.write("\n")
        print("Dedicated Tampu database, user, and runtime configuration created.")
        return 0
    except OSError, ValueError, RuntimeError, ArangoError:
        if "system" in locals():
            if created_user:
                system.delete_user(args.username, ignore_missing=True)
            if created_database:
                system.delete_database(args.database, ignore_missing=True)
        print("Provisioning failed; no existing database privileges were changed.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
