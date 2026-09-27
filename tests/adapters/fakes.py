from __future__ import annotations

from typing import Any


class FakeResponse:
    def __init__(
        self,
        status_code: int = 200,
        payload: Any = None,
        text: str = "",
        headers: dict[str, str] | None = None,
        json_error: ValueError | None = None,
    ):
        self.status_code = status_code
        self.payload = payload
        self.text = text
        self.headers = headers or {}
        self.json_error = json_error

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 400

    def json(self):
        if self.json_error:
            raise self.json_error
        return self.payload


class FakeSession:
    def __init__(self, outcomes=None):
        self.headers: dict[str, str] = {}
        self.outcomes = list(outcomes or [])
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def request(self, method: str, url: str, **kwargs: Any):
        self.calls.append((method, url, kwargs))
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome
