"""Source message domain models."""

from __future__ import annotations

from dataclasses import dataclass

from .embed import Embed


@dataclass(frozen=True)
class MessageAuthor:
    id: str
    username: str
    global_name: str | None = None
    server_name: str | None = None
    avatar_url: str | None = None

    @property
    def display_name(self) -> str:
        return self.server_name or self.global_name or self.username or "Unknown user"

@dataclass(frozen=True)
class Attachment:
    url: str


@dataclass(frozen=True)
class Sticker:
    id: str
    url: str


@dataclass(frozen=True)
class Message:
    id: str
    author: MessageAuthor
    content: str = ""
    embeds: tuple[Embed, ...] = ()
    attachments: tuple[Attachment, ...] = ()
    stickers: tuple[Sticker, ...] = ()
