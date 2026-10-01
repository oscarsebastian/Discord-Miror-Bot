"""Map Discord API dictionaries into domain models."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ...domain import (
    Attachment,
    Embed,
    EmbedAuthor,
    EmbedField,
    EmbedFooter,
    EmbedMedia,
    Message,
    MessageAuthor,
    Sticker,
)
from ...properties import (
    build_discord_sticker_cdn_url,
    build_discord_user_avatar_cdn_url,
)


def _text(value: Any) -> str | None:
    if value is None:
        return None
    rendered = str(value)
    return rendered or None


def _media(value: Any) -> EmbedMedia | None:
    if not isinstance(value, Mapping):
        return None
    url = _text(value.get("url") or value.get("proxy_url"))
    return EmbedMedia(url) if url else None


def _avatar_url(author_id: str, avatar: str | None) -> str | None:
    if not author_id or not avatar:
        return None
    extension = "gif" if avatar.startswith("a_") else "png"
    return build_discord_user_avatar_cdn_url(author_id, avatar, extension)


def _sticker_url(sticker_id: str, format_type: int | None) -> str:
    extension = {3: "json", 4: "gif"}.get(format_type, "png")
    return build_discord_sticker_cdn_url(sticker_id, extension)


class DiscordMessageMapper:
    """Tolerantly map the subset of Discord data used by the application."""

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Message:
        raw_author = data.get("author")
        author_data = raw_author if isinstance(raw_author, Mapping) else {}
        raw_member = data.get("member")
        member_data = raw_member if isinstance(raw_member, Mapping) else {}
        author_id = _text(author_data.get("id")) or "unknown"
        avatar = _text(author_data.get("avatar"))
        author = MessageAuthor(
            id=author_id,
            username=_text(author_data.get("username")) or "Unknown user",
            global_name=_text(author_data.get("global_name")),
            server_name=_text(member_data.get("nick")),
            avatar_url=_avatar_url(author_id, avatar),
        )
        raw_embeds = data.get("embeds")
        embeds = tuple(
            cls._embed(item)
            for item in (raw_embeds if isinstance(raw_embeds, list) else [])
            if isinstance(item, Mapping)
        )
        raw_attachments = data.get("attachments")
        attachments = tuple(
            Attachment(url)
            for item in (raw_attachments if isinstance(raw_attachments, list) else [])
            if isinstance(item, Mapping)
            if (url := _text(item.get("url") or item.get("proxy_url")))
        )
        raw_stickers = data.get("sticker_items")
        stickers = tuple(
            Sticker(
                id=sticker_id,
                url=_sticker_url(
                    sticker_id,
                    item.get("format_type")
                    if isinstance(item.get("format_type"), int)
                    else None,
                ),
            )
            for item in (raw_stickers if isinstance(raw_stickers, list) else [])
            if isinstance(item, Mapping)
            if (sticker_id := _text(item.get("id")))
        )
        return Message(
            id=_text(data.get("id")) or "",
            author=author,
            content=_text(data.get("content")) or "",
            embeds=embeds,
            attachments=attachments,
            stickers=stickers,
        )

    @staticmethod
    def _embed(data: Mapping[str, Any]) -> Embed:
        raw_author = data.get("author")
        author = None
        if isinstance(raw_author, Mapping) and (name := _text(raw_author.get("name"))):
            author = EmbedAuthor(
                name=name,
                url=_text(raw_author.get("url")),
                icon_url=_text(
                    raw_author.get("icon_url") or raw_author.get("proxy_icon_url")
                ),
            )
        raw_footer = data.get("footer")
        footer = None
        if isinstance(raw_footer, Mapping) and (text := _text(raw_footer.get("text"))):
            footer = EmbedFooter(
                text=text,
                icon_url=_text(
                    raw_footer.get("icon_url") or raw_footer.get("proxy_icon_url")
                ),
            )
        raw_fields = data.get("fields")
        fields = tuple(
            EmbedField(name, value, bool(item.get("inline", False)))
            for item in (raw_fields if isinstance(raw_fields, list) else [])
            if isinstance(item, Mapping)
            if (name := _text(item.get("name")))
            if (value := _text(item.get("value")))
        )
        color = data.get("color")
        return Embed(
            title=_text(data.get("title")),
            description=_text(data.get("description")),
            url=_text(data.get("url")),
            timestamp=_text(data.get("timestamp")),
            color=color if isinstance(color, int) and 0 <= color <= 0xFFFFFF else None,
            thumbnail=_media(data.get("thumbnail")),
            image=_media(data.get("image")),
            author=author,
            footer=footer,
            fields=fields,
        )
