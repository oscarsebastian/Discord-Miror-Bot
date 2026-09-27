import unittest

from mirror_bot.adapters.discord.mapper import DiscordMessageMapper


class DiscordMessageMapperTests(unittest.TestCase):
    def test_maps_supported_message_and_embed_fields(self):
        message = DiscordMessageMapper.from_dict(
            {
                "id": "10",
                "content": "hello",
                "author": {
                    "id": "1",
                    "username": "alice",
                    "global_name": "Alice",
                    "avatar": "hash",
                },
                "member": {"nick": "Server nickname"},
                "attachments": [{"proxy_url": "https://cdn.example/file"}],
                "sticker_items": [{"id": "2", "format_type": 4}],
                "embeds": [
                    {
                        "title": "Title",
                        "description": "Description",
                        "url": "https://example.test",
                        "timestamp": "2026-01-01T00:00:00Z",
                        "color": 123,
                        "thumbnail": {"proxy_url": "https://cdn.example/thumb"},
                        "image": {"url": "https://cdn.example/image"},
                        "author": {"name": "Embed author"},
                        "footer": {"text": "Footer"},
                        "fields": [{"name": "A", "value": "B", "inline": True}],
                    }
                ],
            }
        )
        self.assertEqual(message.author.display_name, "Server nickname")
        self.assertEqual(message.attachments[0].url, "https://cdn.example/file")
        self.assertTrue(message.stickers[0].url.endswith(".gif"))
        self.assertEqual(message.embeds[0].fields[0].name, "A")
        self.assertEqual(message.embeds[0].thumbnail.url, "https://cdn.example/thumb")

    def test_tolerates_missing_and_malformed_optional_collections(self):
        message = DiscordMessageMapper.from_dict(
            {
                "embeds": {"not": "a list"},
                "attachments": [None, {}],
                "sticker_items": [None, {}],
            }
        )
        self.assertEqual(message.id, "")
        self.assertEqual(message.author.id, "unknown")
        self.assertEqual(message.embeds, ())
        self.assertEqual(message.attachments, ())
        self.assertEqual(message.stickers, ())


if __name__ == "__main__":
    unittest.main()
