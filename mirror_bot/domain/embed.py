"""Value objects representing embed content."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EmbedField:
    name: str
    value: str
    inline: bool = False


@dataclass(frozen=True)
class EmbedMedia:
    url: str


@dataclass(frozen=True)
class EmbedAuthor:
    name: str
    url: str | None = None
    icon_url: str | None = None


@dataclass(frozen=True)
class EmbedFooter:
    text: str
    icon_url: str | None = None


@dataclass(frozen=True)
class Embed:
    title: str | None = None
    description: str | None = None
    url: str | None = None
    timestamp: str | None = None
    color: int | None = None
    thumbnail: EmbedMedia | None = None
    image: EmbedMedia | None = None
    author: EmbedAuthor | None = None
    footer: EmbedFooter | None = None
    fields: tuple[EmbedField, ...] = ()

    @property
    def has_content(self) -> bool:
        return any(
            (
                self.title,
                self.description,
                self.url,
                self.thumbnail,
                self.image,
                self.author,
                self.footer,
                self.fields,
            )
        )
