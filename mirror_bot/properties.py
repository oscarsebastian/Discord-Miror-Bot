"""Stable Discord endpoint and client properties.

Runtime values such as bot tokens and destination webhook URLs do not belong
here. They remain environment-backed secrets in :mod:`mirror_bot.config`.
"""


def get_discord_api_base_url() -> str:
    """Return the versioned base URL for Discord's REST API."""
    return "https://discord.com/api/v10"


def build_discord_channel_messages_api_url(channel_id: str) -> str:
    """Return the REST endpoint used to retrieve a channel's messages."""
    return f"{get_discord_api_base_url()}/channels/{channel_id}/messages"


def get_discord_cdn_base_url() -> str:
    """Return the base URL for Discord-hosted media."""
    return "https://cdn.discordapp.com"


def build_discord_user_avatar_cdn_url(
    user_id: str,
    avatar_hash: str,
    file_extension: str,
) -> str:
    """Return the CDN URL for a Discord user's avatar."""
    return (
        f"{get_discord_cdn_base_url()}/avatars/"
        f"{user_id}/{avatar_hash}.{file_extension}?size=128"
    )


def build_discord_sticker_cdn_url(sticker_id: str, file_extension: str) -> str:
    """Return the CDN URL for a Discord sticker asset."""
    return f"{get_discord_cdn_base_url()}/stickers/{sticker_id}.{file_extension}"


def get_discord_webhook_api_url_prefix() -> str:
    """Return the canonical prefix expected for Discord webhook URLs."""
    return "https://discord.com/api/webhooks/"


def get_legacy_discord_webhook_api_url_prefix() -> str:
    """Return the legacy Discord webhook prefix accepted for compatibility."""
    return "https://discordapp.com/api/webhooks/"


def get_discord_mirror_user_agent() -> str:
    """Return the HTTP user agent sent by this application."""
    return "DiscordMirror/2.0"
