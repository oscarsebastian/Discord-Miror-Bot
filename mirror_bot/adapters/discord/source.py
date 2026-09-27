"""Discord API adapter implementing the message source port."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import requests

from ...domain import Message
from ...properties import (
    build_discord_channel_messages_api_url,
    get_chrome_browser_user_agent,
)
from ..http import RequestExecutor, RetryPolicy, TransportError
from .mapper import DiscordMessageMapper


class DiscordSourceError(RuntimeError):
    """Raised when source messages cannot be read."""


class DiscordSourceAdapter:
    def __init__(
        self,
        token: str,
        timeout: float,
        session: requests.Session | None = None,
        retry_policy: RetryPolicy | None = None,
        sleeper: Callable[[float], None] | None = None,
    ):
        self.session = session or requests.Session()
        authorization = token if token.startswith(("Bot ", "Bearer ")) else f"Bot {token}"
        self.session.headers.update(
            {
                "Authorization": authorization,
                "User-Agent": get_chrome_browser_user_agent(),
            }
        )
        options: dict[str, Any] = {"retry_policy": retry_policy}
        if sleeper is not None:
            options["sleeper"] = sleeper
        self._http = RequestExecutor(self.session, timeout, **options)

    def fetch_messages(
        self, channel_id: str, after: str | None, limit: int
    ) -> list[Message]:
        params: dict[str, str | int] = {"limit": limit}
        if after:
            params["after"] = after
        try:
            response = self._http.request(
                "GET",
                build_discord_channel_messages_api_url(channel_id),
                params=params,
            )
        except TransportError as exc:
            raise DiscordSourceError(f"Could not reach Discord: {exc}") from exc
        if not response.ok:
            raise DiscordSourceError(
                f"Discord returned HTTP {response.status_code} for channel {channel_id}"
            )
        try:
            payload = response.json()
        except ValueError as exc:
            raise DiscordSourceError("Discord returned invalid JSON") from exc
        if not isinstance(payload, list):
            raise DiscordSourceError("Discord returned an unexpected response")
        return [
            DiscordMessageMapper.from_dict(item)
            for item in payload
            if isinstance(item, dict)
        ]
