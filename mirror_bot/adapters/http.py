"""Shared HTTP retry infrastructure for outbound adapters."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import requests


class TransportError(RuntimeError):
    """Raised after all attempts fail before a usable response is received."""


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if self.base_delay < 0 or self.max_delay < 0:
            raise ValueError("retry delays cannot be negative")


class RequestExecutor:
    """Retry transport failures, rate limits and server errors."""

    def __init__(
        self,
        session: requests.Session,
        timeout: float,
        retry_policy: RetryPolicy | None = None,
        sleeper: Callable[[float], None] = time.sleep,
    ):
        self.session = session
        self.timeout = timeout
        self.retry_policy = retry_policy or RetryPolicy()
        self.sleeper = sleeper

    def request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        kwargs.setdefault("timeout", self.timeout)
        for attempt in range(1, self.retry_policy.max_attempts + 1):
            try:
                response = self.session.request(method, url, **kwargs)
            except requests.RequestException as exc:
                if attempt == self.retry_policy.max_attempts:
                    raise TransportError(str(exc)) from exc
                self.sleeper(self._backoff(attempt))
                continue

            if (
                self._is_retryable(response.status_code)
                and attempt < self.retry_policy.max_attempts
            ):
                self.sleeper(self._response_delay(response, attempt))
                continue
            return response
        raise AssertionError("retry loop ended unexpectedly")  # pragma: no cover

    @staticmethod
    def _is_retryable(status_code: int) -> bool:
        return status_code == 429 or 500 <= status_code < 600

    def _response_delay(self, response: requests.Response, attempt: int) -> float:
        if response.status_code == 429:
            header_delay = response.headers.get("Retry-After")
            if header_delay is not None:
                try:
                    return self._bounded(float(header_delay))
                except ValueError:
                    pass
            try:
                body_delay = response.json().get("retry_after")
                if body_delay is not None:
                    return self._bounded(float(body_delay))
            except (AttributeError, TypeError, ValueError):
                pass
        return self._backoff(attempt)

    def _backoff(self, attempt: int) -> float:
        return self._bounded(self.retry_policy.base_delay * (2 ** (attempt - 1)))

    def _bounded(self, delay: float) -> float:
        return min(max(delay, 0), self.retry_policy.max_delay)
