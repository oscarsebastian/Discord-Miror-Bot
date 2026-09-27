"""Input model for the mirroring use case."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MirrorTask:
    name: str
    source_channel_id: str
    incognito: bool = False
    fetch_limit: int = 50

    @property
    def state_key(self) -> str:
        return f"{self.name}:{self.source_channel_id}"
