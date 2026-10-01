"""Application service for mirroring pending messages."""

from __future__ import annotations

import logging

from .payload_builder import WebhookPayloadBuilder
from .ports import MessageDestination, MessageSource, MirrorState
from .task import MirrorTask

LOGGER = logging.getLogger(__name__)


class MirrorService:
    """Mirror one available batch in chronological order."""

    def __init__(
        self,
        task: MirrorTask,
        state: MirrorState,
        source: MessageSource,
        destination: MessageDestination,
    ):
        self.task = task
        self.state = state
        self.source = source
        self.destination = destination

    def mirror_pending(self) -> int:
        cursor = self.state.last_message_id(self.task.state_key)
        messages = self.source.fetch_messages(
            self.task.source_channel_id, cursor, self.task.fetch_limit
        )
        valid_messages = []
        for message in messages:
            if not message.id.isdigit():
                LOGGER.warning(
                    "Skipping a message with an invalid id in job %s",
                    self.task.name,
                )
                continue
            valid_messages.append(message)
        valid_messages.sort(key=lambda message: int(message.id))

        mirrored = 0
        for message in valid_messages:
            if self.task.incognito:
                username = self.state.incognito_name(message.author.id)
                avatar_url = None
            else:
                username = message.author.display_name
                avatar_url = message.author.avatar_url

            payload = WebhookPayloadBuilder.build(message, username, avatar_url)
            if payload:
                self.destination.send(payload)
                mirrored += 1
                LOGGER.info(
                    "Mirrored message %s for job %s", message.id, self.task.name
                )
            else:
                LOGGER.info(
                    "Ignored empty message %s for job %s", message.id, self.task.name
                )
            self.state.mark_processed(self.task.state_key, message.id)
        return mirrored
