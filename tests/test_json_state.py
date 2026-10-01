import json
import tempfile
import unittest
from pathlib import Path

from mirror_bot.adapters.persistence import JsonStateAdapter


class JsonStateAdapterTests(unittest.TestCase):
    def test_persists_cursor_and_stable_alias(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "state.json"
            state = JsonStateAdapter(path)
            self.assertEqual(state.incognito_name("author-1"), "user1")
            self.assertEqual(state.incognito_name("author-1"), "user1")
            state.mark_processed("general:123", "999")
            reloaded = JsonStateAdapter(path)
            self.assertEqual(reloaded.last_message_id("general:123"), "999")
            self.assertEqual(reloaded.incognito_name("author-1"), "user1")
            self.assertIn("channels", json.loads(path.read_text(encoding="utf-8")))

    def test_rejects_corrupt_or_structurally_invalid_state(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            path.write_text("not json", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Could not read"):
                JsonStateAdapter(path)
            path.write_text('{"channels": []}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid structure"):
                JsonStateAdapter(path)
            path.write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "JSON object"):
                JsonStateAdapter(path)


if __name__ == "__main__":
    unittest.main()
