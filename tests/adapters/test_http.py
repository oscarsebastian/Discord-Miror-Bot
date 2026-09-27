import unittest

import requests

from mirror_bot.adapters.http import RequestExecutor, RetryPolicy, TransportError
from tests.adapters.fakes import FakeResponse, FakeSession


class RequestExecutorTests(unittest.TestCase):
    def test_retries_rate_limit_using_server_delay(self):
        session = FakeSession([
            FakeResponse(429, {"retry_after": 2.5}),
            FakeResponse(200),
        ])
        delays = []
        response = RequestExecutor(session, 10, sleeper=delays.append).request(
            "GET", "https://example.test"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(delays, [2.5])
        self.assertEqual(len(session.calls), 2)

    def test_retries_server_error_with_exponential_backoff(self):
        session = FakeSession([
            FakeResponse(500),
            FakeResponse(502),
            FakeResponse(200),
        ])
        delays = []
        RequestExecutor(session, 10, sleeper=delays.append).request(
            "GET", "https://example.test"
        )
        self.assertEqual(delays, [1.0, 2.0])

    def test_raises_transport_error_after_last_attempt(self):
        error = requests.ConnectionError("offline")
        session = FakeSession([error, error])
        executor = RequestExecutor(
            session,
            10,
            retry_policy=RetryPolicy(max_attempts=2, base_delay=0),
            sleeper=lambda _: None,
        )
        with self.assertRaisesRegex(TransportError, "offline"):
            executor.request("GET", "https://example.test")

    def test_does_not_retry_client_error(self):
        session = FakeSession([FakeResponse(404)])
        response = RequestExecutor(session, 10).request("GET", "https://example.test")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(len(session.calls), 1)

    def test_validates_retry_policy(self):
        with self.assertRaises(ValueError):
            RetryPolicy(max_attempts=0)
        with self.assertRaises(ValueError):
            RetryPolicy(base_delay=-1)

    def test_retries_transport_error_then_succeeds(self):
        session = FakeSession([
            requests.ConnectionError("temporary"),
            FakeResponse(200),
        ])
        delays = []
        response = RequestExecutor(session, 10, sleeper=delays.append).request(
            "GET", "https://example.test"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(delays, [1.0])

    def test_rate_limit_header_takes_priority_and_is_bounded(self):
        session = FakeSession([
            FakeResponse(429, {"retry_after": 1}, headers={"Retry-After": "99"}),
            FakeResponse(200),
        ])
        delays = []
        RequestExecutor(
            session,
            10,
            retry_policy=RetryPolicy(max_delay=5),
            sleeper=delays.append,
        ).request("GET", "https://example.test")
        self.assertEqual(delays, [5])

    def test_invalid_rate_limit_metadata_falls_back_to_backoff(self):
        session = FakeSession([
            FakeResponse(429, None, headers={"Retry-After": "invalid"}),
            FakeResponse(200),
        ])
        delays = []
        RequestExecutor(session, 10, sleeper=delays.append).request(
            "GET", "https://example.test"
        )
        self.assertEqual(delays, [1.0])


if __name__ == "__main__":
    unittest.main()
