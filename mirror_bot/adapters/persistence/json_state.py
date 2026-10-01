"""Atomic JSON implementation of the mirror state port."""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any


class JsonStateAdapter:
    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.RLock()
        self._state = self._read()

    def _read(self) -> dict[str, Any]:
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {"channels": {}, "incognito_names": {}}
        except (json.JSONDecodeError, OSError) as exc:
            raise ValueError(f"Could not read state file {self.path}: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"State file {self.path} must contain a JSON object")
        value.setdefault("channels", {})
        value.setdefault("incognito_names", {})
        if not isinstance(value["channels"], dict) or not isinstance(
            value["incognito_names"], dict
        ):
            raise ValueError(f"State file {self.path} has an invalid structure")
        return value

    def last_message_id(self, key: str) -> str | None:
        with self._lock:
            value = self._state["channels"].get(key)
            return str(value) if value else None

    def mark_processed(self, key: str, message_id: str) -> None:
        with self._lock:
            self._state["channels"][key] = message_id
            self._write()

    def incognito_name(self, author_id: str) -> str:
        with self._lock:
            names: dict[str, str] = self._state["incognito_names"]
            if author_id not in names:
                names[author_id] = f"user{len(names) + 1}"
                self._write()
            return names[author_id]

    def _write(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(f"{self.path.suffix}.tmp")
        temporary.write_text(
            json.dumps(self._state, indent=2, sort_keys=True), encoding="utf-8"
        )
        os.replace(temporary, self.path)
