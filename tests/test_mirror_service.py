import tempfile
import unittest
from pathlib import Path

from mirror_bot.adapters.discord.mapper import DiscordMessageMapper
from mirror_bot.adapters.persistence import JsonStateAdapter
from mirror_bot.application import MirrorService, MirrorTask


class FakeSource:
    def __init__(self, messages):
        self.messages = [DiscordMessageMapper.from_dict(item) for item in messages]
        self.calls = []

    def fetch_messages(self, channel_id, after, limit):
        self.calls.append((channel_id, after, limit))
        return list(self.messages)


class FakeDestination:
    def __init__(self, fail=False):
        self.payloads = []
        self.fail = fail

    def send(self, payload):
        if self.fail:
            raise RuntimeError("delivery failed")
        self.payloads.append(payload)


class MirrorServiceTests(unittest.TestCase):
    def setUp(self):
        self.task = MirrorTask(
            name="general",
            source_channel_id="123",
        )
        self.temp = tempfile.TemporaryDirectory()
        self.state = JsonStateAdapter(Path(self.temp.name) / "state.json")

    def tearDown(self):
        self.temp.cleanup()

    def service(self, source, destination=None, task=None):
        return MirrorService(
            task or self.task,
            self.state,
            source,
            destination or FakeDestination(),
        )

    def test_sends_oldest_first_and_advances_after_delivery(self):
        source = FakeSource([
            {"id": "20", "content": "second", "author": {"id": "1"}},
            {"id": "10", "content": "first", "author": {"id": "1"}},
        ])
        destination = FakeDestination()
        self.assertEqual(self.service(source, destination).mirror_pending(), 2)
        self.assertEqual(
            [payload.content for payload in destination.payloads],
            ["first", "second"],
        )
        self.assertEqual(self.state.last_message_id("general:123"), "20")

    def test_does_not_advance_cursor_when_delivery_fails(self):
        source = FakeSource([{"id": "10", "content": "hello"}])
        with self.assertRaisesRegex(RuntimeError, "delivery failed"):
            self.service(source, FakeDestination(fail=True)).mirror_pending()
        self.assertIsNone(self.state.last_message_id("general:123"))

    def test_incognito_mode_uses_stable_alias_without_avatar(self):
        task = MirrorTask(
            name="private",
            source_channel_id="123",
            incognito=True,
        )
        source = FakeSource([
            {
                "id": "10",
                "content": "hello",
                "author": {"id": "author-1", "username": "Real", "avatar": "hash"},
            },
            {
                "id": "11",
                "content": "again",
                "author": {"id": "author-1", "username": "Real", "avatar": "hash"},
            },
        ])
        destination = FakeDestination()
        self.service(source, destination, task).mirror_pending()
        self.assertEqual(
            [payload.username for payload in destination.payloads],
            ["user1", "user1"],
        )
        self.assertTrue(
            all(payload.avatar_url is None for payload in destination.payloads)
        )

    def test_passes_saved_cursor_to_source(self):
        self.state.mark_processed("general:123", "8")
        source = FakeSource([])
        self.service(source).mirror_pending()
        self.assertEqual(source.calls, [("123", "8", 50)])

    def test_skips_invalid_ids_and_processes_empty_messages(self):
        source = FakeSource([
            {"content": "missing"},
            {"id": "invalid", "content": "bad"},
            {"id": "10"},
        ])
        destination = FakeDestination()
        with self.assertLogs("mirror_bot.application.mirror_service", level="WARNING"):
            count = self.service(source, destination).mirror_pending()
        self.assertEqual(count, 0)
        self.assertEqual(destination.payloads, [])
        self.assertEqual(self.state.last_message_id("general:123"), "10")

    def test_uses_global_name_and_animated_avatar(self):
        source = FakeSource([
            {
                "id": "10",
                "content": "hello",
                "author": {
                    "id": "1",
                    "username": "login",
                    "global_name": "Display name",
                    "avatar": "a_hash",
                },
            }
        ])
        destination = FakeDestination()
        self.service(source, destination).mirror_pending()
        payload = destination.payloads[0]
        self.assertEqual(payload.username, "Display name")
        self.assertIn("a_hash.gif", payload.avatar_url)


if __name__ == "__main__":
    unittest.main()
