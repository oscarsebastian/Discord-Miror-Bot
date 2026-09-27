import unittest

import requests

from mirror_bot.adapters.discord.webhook import (
    DiscordWebhookAdapter,
    DiscordWebhookError,
    serialize_payload,
)
from mirror_bot.adapters.http import RetryPolicy
from mirror_bot.domain import (
    Embed,
    EmbedAuthor,
    EmbedField,
    EmbedFooter,
    EmbedMedia,
    WebhookPayload,
)
from tests.adapters.fakes import FakeResponse, FakeSession


class DiscordWebhookAdapterTests(unittest.TestCase):
    def test_posts_payload_and_waits_for_confirmation(self):
        session = FakeSession([FakeResponse(200)])
        client = DiscordWebhookAdapter(
            "https://discord.com/api/webhooks/1/token", 9, session
        )
        payload = WebhookPayload(username="Alice", content="hello")
        client.send(payload)
        method, _, options = session.calls[0]
        self.assertEqual(method, "POST")
        self.assertEqual(options["params"], {"wait": "true"})
        self.assertEqual(
            options["json"],
            {
                "username": "Alice",
                "content": "hello",
                "allowed_mentions": {"parse": []},
            },
        )
        self.assertEqual(options["timeout"], 9)

    def test_reports_webhook_response_error(self):
        session = FakeSession([FakeResponse(400, text="invalid payload")])
        client = DiscordWebhookAdapter(
            "https://discord.com/api/webhooks/1/token", 10, session
        )
        with self.assertRaisesRegex(DiscordWebhookError, "invalid payload"):
            client.send(WebhookPayload(username="Alice", content="hello"))

    def test_wraps_transport_error(self):
        session = FakeSession([requests.ConnectionError("offline")])
        client = DiscordWebhookAdapter(
            "https://discord.com/api/webhooks/1/token",
            10,
            session,
            retry_policy=RetryPolicy(max_attempts=1),
        )
        with self.assertRaisesRegex(DiscordWebhookError, "offline"):
            client.send(WebhookPayload(username="Alice", content="hello"))

    def test_accepts_an_injected_sleeper(self):
        session = FakeSession([FakeResponse(500), FakeResponse(200)])
        delays = []
        client = DiscordWebhookAdapter(
            "https://discord.com/api/webhooks/1/token",
            10,
            session,
            sleeper=delays.append,
        )
        client.send(WebhookPayload(username="Alice", content="hello"))
        self.assertEqual(delays, [1.0])

    def test_serializes_complete_embed_and_omits_none(self):
        payload = WebhookPayload(
            username="Alice",
            embeds=(
                Embed(
                    title="Title",
                    description="Description",
                    url="https://example.test",
                    timestamp="2026-01-01T00:00:00Z",
                    color=123,
                    thumbnail=EmbedMedia("https://cdn.example/thumb"),
                    image=EmbedMedia("https://cdn.example/image"),
                    author=EmbedAuthor("Author", icon_url="https://cdn.example/icon"),
                    footer=EmbedFooter("Footer"),
                    fields=(EmbedField("A", "B", True),),
                ),
            ),
        )
        serialized = serialize_payload(payload)
        embed = serialized["embeds"][0]
        self.assertEqual(embed["author"]["name"], "Author")
        self.assertNotIn("url", embed["author"])
        self.assertEqual(embed["fields"][0], {"name": "A", "value": "B", "inline": True})

    def test_can_allow_mentions(self):
        serialized = serialize_payload(
            WebhookPayload(username="Alice", content="hello", suppress_mentions=False)
        )
        self.assertNotIn("allowed_mentions", serialized)


if __name__ == "__main__":
    unittest.main()
