import unittest
from dataclasses import FrozenInstanceError

from mirror_bot.domain import MessageAuthor


class DomainModelTests(unittest.TestCase):
    def test_author_uses_global_name(self):
        author = MessageAuthor("1", "login", "Display")
        self.assertEqual(author.display_name, "Display")

    def test_author_prefers_server_nickname(self):
        author = MessageAuthor(
            id="1",
            username="login",
            global_name="Display",
            server_name="Server nickname",
        )
        self.assertEqual(author.display_name, "Server nickname")

    def test_author_falls_back_to_username(self):
        self.assertEqual(MessageAuthor("1", "login").display_name, "login")

    def test_models_are_immutable(self):
        author = MessageAuthor("1", "login")
        with self.assertRaises(FrozenInstanceError):
            author.username = "changed"

if __name__ == "__main__":
    unittest.main()
