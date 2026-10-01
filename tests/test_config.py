import json
import tempfile
import unittest
from pathlib import Path

from mirror_bot.config import AppConfig, ConfigurationError, MirrorJobConfig


class AppConfigTests(unittest.TestCase):
    def test_loads_single_job_from_environment(self):
        env = {
            "DISCORD_TOKEN": "secret",
            "SOURCE_CHANNEL_ID": "123456",
            "DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/1/token",
            "INCOGNITO_MODE": "yes",
            "POLL_INTERVAL_SECONDS": "2.5",
        }
        config = AppConfig.from_environment(env, Path("/tmp"))
        self.assertEqual(config.jobs[0].source_channel_id, "123456")
        self.assertTrue(config.jobs[0].incognito)
        self.assertEqual(config.jobs[0].poll_interval, 2.5)
        self.assertNotIn("secret", repr(config.jobs[0]))
        self.assertNotIn("/1/token", repr(config.jobs[0]))

    def test_rejects_missing_secrets(self):
        with self.assertRaisesRegex(ConfigurationError, "DISCORD_TOKEN"):
            AppConfig.from_environment({}, Path("/tmp"))

    def test_loads_multiple_jobs_and_resolves_secret_names(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "jobs.json").write_text(json.dumps([
                {
                    "name": "alerts",
                    "token_env": "BOT_TOKEN",
                    "source_channel_id": "42",
                    "webhook_env": "ALERT_HOOK",
                }
            ]), encoding="utf-8")
            config = AppConfig.from_environment({
                "MIRROR_JOBS_FILE": "jobs.json",
                "BOT_TOKEN": "secret",
                "ALERT_HOOK": "https://discord.com/api/webhooks/1/token",
            }, root)
            self.assertEqual(config.jobs[0].name, "alerts")
            self.assertEqual(config.jobs[0].token, "secret")

    def test_rejects_duplicate_job_state_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            job = {
                "name": "duplicate",
                "source_channel_id": "42",
            }
            (root / "jobs.json").write_text(
                json.dumps([job, job]), encoding="utf-8"
            )
            with self.assertRaisesRegex(ConfigurationError, "unique"):
                AppConfig.from_environment(
                    {
                        "MIRROR_JOBS_FILE": "jobs.json",
                        "DISCORD_TOKEN": "secret",
                        "DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/1/token",
                    },
                    root,
                )

    def test_rejects_invalid_scalar_environment_values(self):
        base = {
            "DISCORD_TOKEN": "secret",
            "SOURCE_CHANNEL_ID": "123",
            "DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/1/token",
        }
        cases = [
            ({"INCOGNITO_MODE": "perhaps"}, "true or false"),
            ({"POLL_INTERVAL_SECONDS": "soon"}, "must be a number"),
            ({"POLL_INTERVAL_SECONDS": "0"}, "greater than zero"),
            ({"FETCH_LIMIT": "many"}, "must be an integer"),
            ({"FETCH_LIMIT": "101"}, "between 1 and 100"),
        ]
        for additions, expected in cases:
            with self.subTest(additions=additions):
                with self.assertRaisesRegex(ConfigurationError, expected):
                    AppConfig.from_environment({**base, **additions}, Path("/tmp"))

    def test_rejects_invalid_job_fields(self):
        valid = {
            "name": "job",
            "token": "secret",
            "source_channel_id": "123",
            "webhook_url": "https://discord.com/api/webhooks/1/token",
        }
        cases = [
            ({"name": ""}, "name"),
            ({"token": ""}, "Token"),
            ({"source_channel_id": "abc"}, "digits"),
            ({"webhook_url": "https://example.test"}, "webhook"),
            ({"poll_interval": 0}, "interval"),
            ({"fetch_limit": 0}, "limit"),
        ]
        for changes, expected in cases:
            with self.subTest(changes=changes):
                with self.assertRaisesRegex(ConfigurationError, expected):
                    MirrorJobConfig(**{**valid, **changes})

    def test_rejects_invalid_jobs_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base_env = {
                "MIRROR_JOBS_FILE": "jobs.json",
                "DISCORD_TOKEN": "secret",
                "DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/1/token",
            }
            with self.assertRaisesRegex(ConfigurationError, "not found"):
                AppConfig.from_environment(base_env, root)

            cases = [
                ("not json", "valid JSON"),
                ('{"job": 1}', "JSON array"),
                ("[]", "At least one"),
                ('["invalid"]', "JSON object"),
                (
                    '[{"name":"x","source_channel_id":"1","token_env":"MISSING"}]',
                    "MISSING",
                ),
            ]
            for contents, expected in cases:
                with self.subTest(contents=contents):
                    (root / "jobs.json").write_text(contents, encoding="utf-8")
                    with self.assertRaisesRegex(ConfigurationError, expected):
                        AppConfig.from_environment(base_env, root)


if __name__ == "__main__":
    unittest.main()
