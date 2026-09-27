import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mirror_bot import app
from mirror_bot.adapters.discord import DiscordSourceAdapter, DiscordWebhookAdapter
from mirror_bot.adapters.persistence import JsonStateAdapter
from mirror_bot.config import AppConfig, ConfigurationError, MirrorJobConfig


class AppTests(unittest.TestCase):
    def test_builds_one_runner_per_job_with_expected_adapters(self):
        with tempfile.TemporaryDirectory() as directory:
            jobs = tuple(
                MirrorJobConfig(
                    name=f"job-{index}",
                    token="secret",
                    source_channel_id=str(index),
                    webhook_url=f"https://discord.com/api/webhooks/{index}/token",
                )
                for index in (1, 2)
            )
            config = AppConfig(jobs=jobs, state_file=Path(directory) / "state.json")
            state = JsonStateAdapter(config.state_file)
            runners = app.build_runners(config, state)
            self.assertEqual(len(runners), 2)
            self.assertTrue(
                all(isinstance(item.service.source, DiscordSourceAdapter) for item in runners)
            )
            self.assertTrue(
                all(
                    isinstance(item.service.destination, DiscordWebhookAdapter)
                    for item in runners
                )
            )
            self.assertTrue(all(item.service.state is state for item in runners))

    @patch("mirror_bot.app.MirrorApplication")
    @patch("mirror_bot.app.build_runners", return_value=[])
    @patch("mirror_bot.app.JsonStateAdapter")
    @patch("mirror_bot.app.AppConfig.from_environment")
    @patch("mirror_bot.app.load_dotenv")
    @patch("mirror_bot.app.logging.basicConfig")
    def test_bootstrap_loads_configuration_and_runs_application(
        self, _, load_dotenv, from_environment, state_adapter, build, application
    ):
        config = AppConfig(jobs=(), state_file=Path("state.json"))
        from_environment.return_value = config
        app.run()
        load_dotenv.assert_called_once_with()
        state_adapter.assert_called_once_with(config.state_file)
        build.assert_called_once()
        application.return_value.run.assert_called_once_with()

    @patch("mirror_bot.app.AppConfig.from_environment")
    @patch("mirror_bot.app.load_dotenv")
    @patch("mirror_bot.app.logging.basicConfig")
    def test_bootstrap_reports_configuration_error(self, _, __, from_environment):
        from_environment.side_effect = ConfigurationError("bad config")
        with self.assertRaisesRegex(SystemExit, "bad config"):
            app.run()


if __name__ == "__main__":
    unittest.main()
