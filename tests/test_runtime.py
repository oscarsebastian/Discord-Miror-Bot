import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from mirror_bot.runtime import MirrorApplication, PollingRunner


class OneCycleEvent:
    def __init__(self):
        self.stopped = False

    def is_set(self):
        return self.stopped

    def wait(self, timeout):
        self.timeout = timeout
        self.stopped = True


class PollingRunnerTests(unittest.TestCase):
    def test_polls_once_and_honors_interval(self):
        service = Mock()
        service.task.name = "general"
        service.mirror_pending.return_value = 1
        runner = PollingRunner(service, 5)
        event = OneCycleEvent()
        runner.run(event)
        service.mirror_pending.assert_called_once_with()
        self.assertEqual(event.timeout, 5)

    def test_recovers_from_service_error(self):
        service = Mock()
        service.task.name = "general"
        service.mirror_pending.side_effect = RuntimeError("temporary")
        runner = PollingRunner(service, 5)
        with self.assertLogs("mirror_bot.runtime", level="ERROR"):
            runner.run(OneCycleEvent())
        service.mirror_pending.assert_called_once_with()


class MirrorApplicationTests(unittest.TestCase):
    def test_starts_named_threads_and_stops_them(self):
        created_threads = []

        class FakeThread:
            def __init__(self, **options):
                self.options = options
                self.started = False
                self.joins = 0
                created_threads.append(self)

            def start(self):
                self.started = True

            def join(self):
                self.joins += 1

        runner = SimpleNamespace(name="one", run=lambda _: None)
        application = MirrorApplication([runner], thread_factory=FakeThread)
        application.start()
        self.assertTrue(created_threads[0].started)
        self.assertEqual(created_threads[0].options["name"], "mirror-one")
        application.stop()
        self.assertTrue(application.stop_event.is_set())
        self.assertEqual(created_threads[0].joins, 1)

    def test_cannot_be_started_twice(self):
        thread = Mock()
        runner = SimpleNamespace(name="one", run=lambda _: None)
        application = MirrorApplication([runner], thread_factory=Mock(return_value=thread))
        application.start()
        with self.assertRaisesRegex(RuntimeError, "already"):
            application.start()

    def test_run_joins_and_stops(self):
        thread = Mock()
        runner = SimpleNamespace(name="one", run=lambda _: None)
        application = MirrorApplication([runner], thread_factory=Mock(return_value=thread))
        application.run()
        self.assertTrue(application.stop_event.is_set())
        self.assertEqual(thread.join.call_count, 2)

    def test_stops_after_keyboard_interrupt(self):
        thread = Mock()
        thread.join.side_effect = [KeyboardInterrupt, None]
        runner = SimpleNamespace(name="one", run=lambda _: None)
        application = MirrorApplication([runner], thread_factory=Mock(return_value=thread))
        application.run()
        self.assertTrue(application.stop_event.is_set())


if __name__ == "__main__":
    unittest.main()
