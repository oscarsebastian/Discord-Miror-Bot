"""Ports required by the mirroring application."""

from __future__ import annotations

from typing import Protocol

from ..domain import Message, WebhookPayload


class MessageSource(Protocol):
    """Read source messages without exposing transport details."""

    def fetch_messages(
        self, channel_id: str, after: str | None, limit: int
    ) -> list[Message]:
        ...


class MessageDestination(Protocol):
    """Deliver one normalized message."""

    def send(self, payload: WebhookPayload) -> None:
        ...


class MirrorState(Protocol):
    """Persist cursors and incognito aliases."""

    def last_message_id(self, key: str) -> str | None:
        ...

    def mark_processed(self, key: str, message_id: str) -> None:
        ...

    def incognito_name(self, author_id: str) -> str:
        ...
