from __future__ import annotations

import json
import secrets
from pathlib import Path

import pytest
from arango import ArangoClient


@pytest.fixture(scope="session")
def arango_admin() -> dict:
    path = Path.home() / ".config/tampu/test-admin.json"
    if not path.is_file():
        pytest.skip("disposable ArangoDB administrator configuration is unavailable")
    return json.loads(path.read_text())


@pytest.fixture
def repository_config(arango_admin: dict, tmp_path: Path):
    database = f"tampu_test_{secrets.token_hex(8)}"
    username = f"tampu_test_{secrets.token_hex(8)}"
    password = secrets.token_urlsafe(24)
    client = ArangoClient(hosts=arango_admin["endpoint"])
    system = client.db(
        "_system", username=arango_admin["username"], password=arango_admin["password"]
    )
    system.create_database(database)
    system.create_user(username, password=password, active=True)
    system.update_permission(username, "rw", database=database)
    config = SecretConfig(
        {
            "endpoint": arango_admin["endpoint"],
            "database": database,
            "username": username,
            "password": password,
            "store": str(tmp_path / "store"),
        }
    )
    try:
        yield config
    finally:
        system.delete_database(database)
        system.delete_user(username)


class SecretConfig(dict):
    def __repr__(self):
        return "<redacted repository configuration>"
