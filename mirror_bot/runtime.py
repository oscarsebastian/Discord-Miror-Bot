"""Runtime orchestration outside the application use case."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable

from .application import MirrorService

LOGGER = logging.getLogger(__name__)


class PollingRunner:
    """Run a mirror service repeatedly and isolate transient failures."""

    def __init__(self, service: MirrorService, interval: float):
        self.service = service
        self.interval = interval

    @property
    def name(self) -> str:
        return self.service.task.name

    def run(self, stop_event: threading.Event) -> None:
        LOGGER.info("Started job %s", self.name)
        while not stop_event.is_set():
            try:
                count = self.service.mirror_pending()
                if count:
                    LOGGER.info("Job %s mirrored %d message(s)", self.name, count)
            except Exception:
                LOGGER.exception("Job %s failed; it will retry", self.name)
            stop_event.wait(self.interval)
        LOGGER.info("Stopped job %s", self.name)


class MirrorApplication:
    """Own polling threads and coordinate graceful shutdown."""

    def __init__(
        self,
        runners: list[PollingRunner],
        thread_factory: Callable[..., threading.Thread] = threading.Thread,
    ):
        self.runners = runners
        self.thread_factory = thread_factory
        self.stop_event = threading.Event()
        self.threads: list[threading.Thread] = []

    def start(self) -> None:
        if self.threads:
            raise RuntimeError("Application has already been started")
        for runner in self.runners:
            thread = self.thread_factory(
                target=runner.run,
                args=(self.stop_event,),
                name=f"mirror-{runner.name}",
            )
            thread.daemon = True
            thread.start()
            self.threads.append(thread)

    def stop(self) -> None:
        self.stop_event.set()
        for thread in self.threads:
            if not thread.is_alive():
                continue
            try:
                thread.join(timeout=1.0)
            except KeyboardInterrupt:
                LOGGER.warning("Interrupted while waiting for worker %s to stop", thread.name)

    def run(self) -> None:
        self.start()
        try:
            while any(thread.is_alive() for thread in self.threads):
                for thread in self.threads:
                    if thread.is_alive():
                        thread.join(timeout=0.25)
        except KeyboardInterrupt:
            LOGGER.info("Stopping mirror workers...")
        finally:
            self.stop()
