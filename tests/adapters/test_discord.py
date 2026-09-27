import unittest

import requests

from mirror_bot.adapters.discord.source import DiscordSourceAdapter, DiscordSourceError
from mirror_bot.adapters.http import RetryPolicy
from tests.adapters.fakes import FakeResponse, FakeSession


class DiscordSourceAdapterTests(unittest.TestCase):
    def test_fetches_messages_with_cursor_and_bot_authorization(self):
        session = FakeSession([FakeResponse(200, [{"id": "2"}, "invalid"])])
        client = DiscordSourceAdapter("secret", 8, session)
        messages = client.fetch_messages("123", "1", 50)
        self.assertEqual([message.id for message in messages], ["2"])
        self.assertEqual(session.headers["Authorization"], "Bot secret")
        self.assertIn("Chrome/153.0.0.0", session.headers["User-Agent"])
        method, url, options = session.calls[0]
        self.assertEqual(method, "GET")
        self.assertTrue(url.endswith("/channels/123/messages"))
        self.assertEqual(options["params"], {"limit": 50, "after": "1"})
        self.assertEqual(options["timeout"], 8)

    def test_preserves_explicit_authorization_scheme(self):
        session = FakeSession([FakeResponse(200, [])])
        DiscordSourceAdapter("Bearer secret", 10, session)
        self.assertEqual(session.headers["Authorization"], "Bearer secret")

    def test_accepts_an_injected_sleeper(self):
        session = FakeSession([FakeResponse(500), FakeResponse(200, [])])
        delays = []
        client = DiscordSourceAdapter("secret", 10, session, sleeper=delays.append)
        client.fetch_messages("123", None, 10)
        self.assertEqual(delays, [1.0])

    def test_rejects_non_list_response(self):
        client = DiscordSourceAdapter("secret", 10, FakeSession([FakeResponse(200, {})]))
        with self.assertRaisesRegex(DiscordSourceError, "unexpected"):
            client.fetch_messages("123", None, 10)

    def test_rejects_invalid_json(self):
        response = FakeResponse(200, json_error=ValueError("bad json"))
        client = DiscordSourceAdapter("secret", 10, FakeSession([response]))
        with self.assertRaisesRegex(DiscordSourceError, "invalid JSON"):
            client.fetch_messages("123", None, 10)

    def test_wraps_http_and_transport_errors(self):
        http_client = DiscordSourceAdapter("secret", 10, FakeSession([FakeResponse(403)]))
        with self.assertRaisesRegex(DiscordSourceError, "HTTP 403"):
            http_client.fetch_messages("123", None, 10)

        network_client = DiscordSourceAdapter(
            "secret",
            10,
            FakeSession([requests.ConnectionError("offline")]),
            retry_policy=RetryPolicy(max_attempts=1),
        )
        with self.assertRaisesRegex(DiscordSourceError, "offline"):
            network_client.fetch_messages("123", None, 10)


if __name__ == "__main__":
    unittest.main()
