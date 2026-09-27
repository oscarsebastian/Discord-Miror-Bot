"""Destination webhook domain model."""

from __future__ import annotations

from dataclasses import dataclass

from .embed import Embed


@dataclass(frozen=True)
class WebhookPayload:
    username: str
    content: str | None = None
    avatar_url: str | None = None
    embeds: tuple[Embed, ...] = ()
    suppress_mentions: bool = True
