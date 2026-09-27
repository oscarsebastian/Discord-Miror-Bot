"""Environment-backed application configuration."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

from .properties import (
    get_discord_webhook_api_url_prefix,
    get_legacy_discord_webhook_api_url_prefix,
)


class ConfigurationError(ValueError):
    """Raised when the application configuration is incomplete or invalid."""


def _as_bool(value: str, field_name: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ConfigurationError(f"{field_name} must be true or false")


def _as_positive_float(value: str, field_name: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(f"{field_name} must be a number") from exc
    if parsed <= 0:
        raise ConfigurationError(f"{field_name} must be greater than zero")
    return parsed


def _as_limit(value: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ConfigurationError("FETCH_LIMIT must be an integer") from exc
    if not 1 <= parsed <= 100:
        raise ConfigurationError("FETCH_LIMIT must be between 1 and 100")
    return parsed


@dataclass(frozen=True)
class MirrorJobConfig:
    """Configuration for one source channel and destination webhook."""

    name: str
    token: str = field(repr=False)
    source_channel_id: str
    webhook_url: str = field(repr=False)
    poll_interval: float = 5.0
    incognito: bool = False
    fetch_limit: int = 50

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ConfigurationError("Job name cannot be empty")
        if not self.token.strip():
            raise ConfigurationError(f"Token is missing for job {self.name!r}")
        if not self.source_channel_id.isdigit():
            raise ConfigurationError(
                f"Source channel id for job {self.name!r} must contain only digits"
            )
        if not self.webhook_url.startswith(
            (
                get_discord_webhook_api_url_prefix(),
                get_legacy_discord_webhook_api_url_prefix(),
            )
        ):
            raise ConfigurationError(f"Invalid Discord webhook URL for job {self.name!r}")
        if self.poll_interval <= 0:
            raise ConfigurationError(f"Poll interval for job {self.name!r} must be positive")
        if not 1 <= self.fetch_limit <= 100:
            raise ConfigurationError(f"Fetch limit for job {self.name!r} must be 1..100")


@dataclass(frozen=True)
class AppConfig:
    """Complete application configuration."""

    jobs: tuple[MirrorJobConfig, ...]
    state_file: Path
    http_timeout: float = 15.0

    @classmethod
    def from_environment(
        cls,
        environment: Mapping[str, str] | None = None,
        base_dir: Path | None = None,
    ) -> "AppConfig":
        env = os.environ if environment is None else environment
        root = Path.cwd() if base_dir is None else base_dir
        state_file = root / env.get("STATE_FILE", "data/state.json")
        timeout = _as_positive_float(
            env.get("HTTP_TIMEOUT_SECONDS", "15"), "HTTP_TIMEOUT_SECONDS"
        )

        jobs_file = env.get("MIRROR_JOBS_FILE")
        jobs = (
            cls._load_jobs_file(root / jobs_file, env)
            if jobs_file
            else (cls._load_single_job(env),)
        )
        if not jobs:
            raise ConfigurationError("At least one mirror job is required")
        state_keys = [f"{job.name}:{job.source_channel_id}" for job in jobs]
        if len(state_keys) != len(set(state_keys)):
            raise ConfigurationError("Job names must be unique for each source channel")
        return cls(jobs=jobs, state_file=state_file, http_timeout=timeout)

    @staticmethod
    def _load_single_job(env: Mapping[str, str]) -> MirrorJobConfig:
        missing = [
            key for key in ("DISCORD_TOKEN", "SOURCE_CHANNEL_ID", "DISCORD_WEBHOOK_URL")
            if not env.get(key)
        ]
        if missing:
            raise ConfigurationError(f"Missing environment variables: {', '.join(missing)}")
        return MirrorJobConfig(
            name=env.get("MIRROR_NAME", "default"),
            token=env["DISCORD_TOKEN"],
            source_channel_id=env["SOURCE_CHANNEL_ID"],
            webhook_url=env["DISCORD_WEBHOOK_URL"],
            poll_interval=_as_positive_float(
                env.get("POLL_INTERVAL_SECONDS", "5"), "POLL_INTERVAL_SECONDS"
            ),
            incognito=_as_bool(env.get("INCOGNITO_MODE", "false"), "INCOGNITO_MODE"),
            fetch_limit=_as_limit(env.get("FETCH_LIMIT", "50")),
        )

    @staticmethod
    def _load_jobs_file(path: Path, env: Mapping[str, str]) -> tuple[MirrorJobConfig, ...]:
        try:
            raw_jobs = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise ConfigurationError(f"Jobs file not found: {path}") from exc
        except json.JSONDecodeError as exc:
            raise ConfigurationError(f"Jobs file is not valid JSON: {exc}") from exc
        if not isinstance(raw_jobs, list):
            raise ConfigurationError("Jobs file must contain a JSON array")

        jobs: list[MirrorJobConfig] = []
        for index, raw in enumerate(raw_jobs, start=1):
            if not isinstance(raw, dict):
                raise ConfigurationError(f"Job #{index} must be a JSON object")
            name = str(raw.get("name", f"job-{index}"))
            token_key = str(raw.get("token_env", "DISCORD_TOKEN"))
            webhook_key = str(raw.get("webhook_env", "DISCORD_WEBHOOK_URL"))
            missing = [key for key in (token_key, webhook_key) if not env.get(key)]
            if missing:
                raise ConfigurationError(
                    f"Missing environment variables for job {name!r}: {', '.join(missing)}"
                )
            jobs.append(
                MirrorJobConfig(
                    name=name,
                    token=env[token_key],
                    source_channel_id=str(raw.get("source_channel_id", "")),
                    webhook_url=env[webhook_key],
                    poll_interval=_as_positive_float(
                        str(raw.get("poll_interval_seconds", 5)),
                        "poll_interval_seconds",
                    ),
                    incognito=_as_bool(str(raw.get("incognito", False)), "incognito"),
                    fetch_limit=_as_limit(str(raw.get("fetch_limit", 50))),
                )
            )
        return tuple(jobs)
