"""Discord webhook adapter implementing the destination port."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import requests

from ...domain import Embed, WebhookPayload
from ..http import RequestExecutor, RetryPolicy, TransportError


class DiscordWebhookError(RuntimeError):
    """Raised when a payload cannot be delivered."""


def _without_none(values: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}


def _serialize_embed(embed: Embed) -> dict[str, Any]:
    result = _without_none(
        {
            "title": embed.title,
            "description": embed.description,
            "url": embed.url,
            "timestamp": embed.timestamp,
            "color": embed.color,
            "thumbnail": {"url": embed.thumbnail.url} if embed.thumbnail else None,
            "image": {"url": embed.image.url} if embed.image else None,
            "author": _without_none(
                {
                    "name": embed.author.name,
                    "url": embed.author.url,
                    "icon_url": embed.author.icon_url,
                }
            )
            if embed.author
            else None,
            "footer": _without_none(
                {"text": embed.footer.text, "icon_url": embed.footer.icon_url}
            )
            if embed.footer
            else None,
        }
    )
    if embed.fields:
        result["fields"] = [
            {"name": field.name, "value": field.value, "inline": field.inline}
            for field in embed.fields
        ]
    return result


def serialize_payload(payload: WebhookPayload) -> dict[str, Any]:
    """Serialize the destination model at the HTTP boundary."""
    result = _without_none(
        {
            "username": payload.username,
            "content": payload.content,
            "avatar_url": payload.avatar_url,
        }
    )
    if payload.embeds:
        result["embeds"] = [_serialize_embed(embed) for embed in payload.embeds]
    if payload.suppress_mentions:
        result["allowed_mentions"] = {"parse": []}
    return result


class DiscordWebhookAdapter:
    def __init__(
        self,
        url: str,
        timeout: float,
        session: requests.Session | None = None,
        retry_policy: RetryPolicy | None = None,
        sleeper: Callable[[float], None] | None = None,
    ):
        self.url = url
        self.session = session or requests.Session()
        options: dict[str, Any] = {"retry_policy": retry_policy}
        if sleeper is not None:
            options["sleeper"] = sleeper
        self._http = RequestExecutor(self.session, timeout, **options)

    def send(self, payload: WebhookPayload) -> None:
        try:
            response = self._http.request(
                "POST",
                self.url,
                params={"wait": "true"},
                json=serialize_payload(payload),
            )
        except TransportError as exc:
            raise DiscordWebhookError(
                f"Could not reach the destination webhook: {exc}"
            ) from exc
        if not response.ok:
            raise DiscordWebhookError(
                f"Webhook returned HTTP {response.status_code}: {response.text[:200]}"
            )
