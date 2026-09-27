"""Discord source and webhook adapters."""

from .source import DiscordSourceAdapter, DiscordSourceError
from .webhook import DiscordWebhookAdapter, DiscordWebhookError

__all__ = [
    "DiscordSourceAdapter",
    "DiscordSourceError",
    "DiscordWebhookAdapter",
    "DiscordWebhookError",
]
