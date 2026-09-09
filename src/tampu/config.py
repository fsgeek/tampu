from __future__ import annotations

import json
import os
from pathlib import Path

from .errors import TampuError

_REQUIRED = ("endpoint", "database", "username", "password", "store")


def load_config(path: Path | None = None) -> dict:
    selected = (
        Path(path)
        if path is not None
        else Path(
            os.environ.get("TAMPU_CONFIG", "~/.config/tampu/config.json")
        ).expanduser()
    )
    try:
        value = json.loads(selected.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError) as error:
        raise TampuError(
            "invalid_configuration", "Tampu configuration could not be loaded."
        ) from error
    if not isinstance(value, dict) or any(
        not isinstance(value.get(key), str) or not value[key] for key in _REQUIRED
    ):
        raise TampuError("invalid_configuration", "Tampu configuration is incomplete.")
    return {key: value[key] for key in _REQUIRED}
