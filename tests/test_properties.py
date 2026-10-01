import unittest

from mirror_bot.properties import (
    build_discord_channel_messages_api_url,
    build_discord_sticker_cdn_url,
    build_discord_user_avatar_cdn_url,
    get_discord_api_base_url,
    get_discord_cdn_base_url,
    get_chrome_browser_user_agent,
    get_discord_webhook_api_url_prefix,
    get_legacy_discord_webhook_api_url_prefix,
)


class DiscordPropertiesTests(unittest.TestCase):
    def test_returns_discord_api_urls(self):
        self.assertEqual(get_discord_api_base_url(), "https://discord.com/api/v10")
        self.assertEqual(
            build_discord_channel_messages_api_url("123"),
            "https://discord.com/api/v10/channels/123/messages",
        )

    def test_returns_discord_cdn_urls(self):
        self.assertEqual(get_discord_cdn_base_url(), "https://cdn.discordapp.com")
        self.assertEqual(
            build_discord_user_avatar_cdn_url("1", "hash", "png"),
            "https://cdn.discordapp.com/avatars/1/hash.png?size=128",
        )
        self.assertEqual(
            build_discord_sticker_cdn_url("2", "gif"),
            "https://cdn.discordapp.com/stickers/2.gif",
        )

    def test_returns_webhook_prefixes_and_user_agent(self):
        self.assertEqual(
            get_discord_webhook_api_url_prefix(),
            "https://discord.com/api/webhooks/",
        )
        self.assertEqual(
            get_legacy_discord_webhook_api_url_prefix(),
            "https://discordapp.com/api/webhooks/",
        )
        user_agent = get_chrome_browser_user_agent()
        self.assertTrue(user_agent.startswith("Mozilla/5.0 (Windows NT 10.0; Win64; x64)"))
        self.assertIn("Chrome/153.0.0.0", user_agent)
        self.assertTrue(user_agent.endswith("Safari/537.36"))


if __name__ == "__main__":
    unittest.main()
