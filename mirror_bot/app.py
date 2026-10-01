"""Composition root: wire application ports to concrete adapters."""

from __future__ import annotations

import logging

from dotenv import load_dotenv

from .adapters.discord import DiscordSourceAdapter, DiscordWebhookAdapter
from .adapters.persistence import JsonStateAdapter
from .application import MirrorService, MirrorTask
from .config import AppConfig, ConfigurationError
from .runtime import MirrorApplication, PollingRunner


def build_runners(
    config: AppConfig, state: JsonStateAdapter
) -> list[PollingRunner]:
    """Build the object graph without starting external work."""
    return [
        PollingRunner(
            service=MirrorService(
                task=MirrorTask(
                    name=job.name,
                    source_channel_id=job.source_channel_id,
                    incognito=job.incognito,
                    fetch_limit=job.fetch_limit,
                ),
                state=state,
                source=DiscordSourceAdapter(job.token, config.http_timeout),
                destination=DiscordWebhookAdapter(job.webhook_url, config.http_timeout),
            ),
            interval=job.poll_interval,
        )
        for job in config.jobs
    ]


def run() -> None:
    load_dotenv()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    try:
        config = AppConfig.from_environment()
    except ConfigurationError as exc:
        raise SystemExit(f"Configuration error: {exc}") from exc

    state = JsonStateAdapter(config.state_file)
    MirrorApplication(build_runners(config, state)).run()
