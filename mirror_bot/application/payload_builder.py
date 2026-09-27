"""Build destination payloads from source messages."""

from __future__ import annotations

from ..domain import (
    Embed,
    EmbedAuthor,
    EmbedField,
    EmbedFooter,
    Message,
    WebhookPayload,
)

MAX_CONTENT_LENGTH = 2_000
MAX_EMBEDS = 10
MAX_EMBED_TOTAL = 6_000


def _truncate(value: str | None, limit: int) -> str | None:
    if not value:
        return None
    return value[: max(0, limit)] or None


class WebhookPayloadBuilder:
    """Apply Discord webhook constraints to a source message."""

    @classmethod
    def build(
        cls,
        message: Message,
        username: str,
        avatar_url: str | None,
    ) -> WebhookPayload | None:
        content_parts = [message.content] if message.content else []
        content_parts.extend(
            attachment.url
            for attachment in message.attachments
            if attachment.url not in content_parts
        )
        content_parts.extend(sticker.url for sticker in message.stickers)
        content = "\n".join(content_parts)[:MAX_CONTENT_LENGTH] or None
        embeds = cls._embeds(message.embeds)
        if not content and not embeds:
            return None
        return WebhookPayload(
            username=username[:80],
            content=content,
            avatar_url=avatar_url,
            embeds=embeds,
        )

    @classmethod
    def _embeds(cls, source: tuple[Embed, ...]) -> tuple[Embed, ...]:
        result: list[Embed] = []
        remaining = MAX_EMBED_TOTAL
        for embed in source[:MAX_EMBEDS]:
            if remaining <= 0:
                break
            normalized, used = cls._embed(embed, remaining)
            if normalized.has_content:
                result.append(normalized)
                remaining -= used
        return tuple(result)

    @staticmethod
    def _embed(source: Embed, budget: int) -> tuple[Embed, int]:
        used = 0
        title = _truncate(source.title, min(256, budget))
        used += len(title or "")
        description = _truncate(source.description, min(4_096, budget - used))
        used += len(description or "")

        author = None
        if source.author:
            name = _truncate(source.author.name, min(256, budget - used))
            if name:
                author = EmbedAuthor(name, source.author.url, source.author.icon_url)
                used += len(name)

        footer = None
        if source.footer:
            text = _truncate(source.footer.text, min(2_048, budget - used))
            if text:
                footer = EmbedFooter(text, source.footer.icon_url)
                used += len(text)

        fields: list[EmbedField] = []
        for field in source.fields[:25]:
            name = _truncate(field.name, min(256, budget - used))
            if not name:
                continue
            value = _truncate(field.value, min(1_024, budget - used - len(name)))
            if not value:
                continue
            fields.append(EmbedField(name, value, field.inline))
            used += len(name) + len(value)

        return (
            Embed(
                title=title,
                description=description,
                url=source.url,
                timestamp=source.timestamp,
                color=source.color,
                thumbnail=source.thumbnail,
                image=source.image,
                author=author,
                footer=footer,
                fields=tuple(fields),
            ),
            used,
        )
