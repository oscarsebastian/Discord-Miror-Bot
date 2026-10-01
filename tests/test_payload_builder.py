import unittest

from mirror_bot.adapters.discord.mapper import DiscordMessageMapper
from mirror_bot.application.payload_builder import (
    MAX_CONTENT_LENGTH,
    WebhookPayloadBuilder,
)


def build(raw_message, username="Alice", avatar_url=None):
    message = DiscordMessageMapper.from_dict(raw_message)
    return WebhookPayloadBuilder.build(message, username, avatar_url)


class WebhookPayloadBuilderTests(unittest.TestCase):
    def test_preserves_text_attachments_and_multiple_rich_embeds(self):
        payload = build(
            {
                "content": "hello",
                "attachments": [{"url": "https://cdn.example/file.png"}],
                "embeds": [
                    {
                        "title": "First",
                        "description": "Description",
                        "color": 123,
                        "author": {
                            "name": "Author",
                            "icon_url": "https://cdn.example/a.png",
                        },
                        "footer": {"text": "Footer"},
                        "image": {"url": "https://cdn.example/image.png"},
                        "fields": [{"name": "A", "value": "B", "inline": True}],
                    },
                    {"thumbnail": {"url": "https://cdn.example/thumb.png"}},
                ],
            },
            avatar_url="https://cdn.example/avatar.png",
        )
        self.assertIn("hello", payload.content)
        self.assertIn("https://cdn.example/file.png", payload.content)
        self.assertEqual(len(payload.embeds), 2)
        self.assertTrue(payload.embeds[0].fields[0].inline)
        self.assertEqual(
            payload.embeds[1].thumbnail.url,
            "https://cdn.example/thumb.png",
        )
        self.assertEqual(payload.avatar_url, "https://cdn.example/avatar.png")

    def test_empty_message_is_ignored(self):
        self.assertIsNone(build({}))

    def test_uses_the_correct_sticker_extension(self):
        payload = build(
            {
                "sticker_items": [
                    {"id": "1", "format_type": 1},
                    {"id": "2", "format_type": 4},
                ]
            }
        )
        self.assertEqual(
            payload.content,
            "https://cdn.discordapp.com/stickers/1.png\n"
            "https://cdn.discordapp.com/stickers/2.gif",
        )

    def test_discord_limits_are_applied(self):
        payload = build(
            {
                "content": "x" * (MAX_CONTENT_LENGTH + 50),
                "embeds": [{"title": "t"}] * 15,
            },
            username="u" * 100,
        )
        self.assertEqual(len(payload.content), MAX_CONTENT_LENGTH)
        self.assertEqual(len(payload.username), 80)
        self.assertEqual(len(payload.embeds), 10)

    def test_embed_text_budget_and_field_limits_are_applied(self):
        payload = build(
            {
                "embeds": [
                    {
                        "title": "t" * 300,
                        "description": "d" * 5_000,
                        "author": {"name": "a" * 300},
                        "footer": {"text": "f" * 3_000},
                        "fields": [
                            {"name": "name", "value": "value"}
                        ] * 30,
                    }
                ]
            }
        )
        embed = payload.embeds[0]
        self.assertEqual(len(embed.title), 256)
        self.assertLessEqual(len(embed.description), 4_096)
        total = len(embed.title) + len(embed.description)
        total += len(embed.author.name) if embed.author else 0
        total += len(embed.footer.text) if embed.footer else 0
        total += sum(len(field.name) + len(field.value) for field in embed.fields)
        self.assertLessEqual(total, 6_000)
        self.assertLessEqual(len(embed.fields), 25)


if __name__ == "__main__":
    unittest.main()
