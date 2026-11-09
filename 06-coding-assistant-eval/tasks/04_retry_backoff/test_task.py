import unittest

from solution import call_with_retry


class Flaky:
    def __init__(self, failures, exc=ConnectionError):
        self.failures, self.exc, self.calls = failures, exc, 0

    def __call__(self):
        self.calls += 1
        if self.calls <= self.failures:
            raise self.exc("temporary problem")
        return "ok"


class RetryTests(unittest.TestCase):
    def setUp(self):
        self.waits = []

    def sleep(self, seconds):
        self.waits.append(seconds)

    def test_success_first_try(self):
        fn = Flaky(0)
        self.assertEqual(call_with_retry(fn, sleep=self.sleep), "ok")
        self.assertEqual((fn.calls, self.waits), (1, []))

    def test_retries_with_exponential_backoff(self):
        fn = Flaky(2)
        self.assertEqual(call_with_retry(fn, attempts=3, base_delay=1, sleep=self.sleep), "ok")
        self.assertEqual(fn.calls, 3)
        self.assertEqual(self.waits, [1, 2])

    def test_gives_up_and_raises_last_error(self):
        fn = Flaky(10)
        with self.assertRaises(ConnectionError):
            call_with_retry(fn, attempts=4, base_delay=0.5, sleep=self.sleep)
        self.assertEqual(fn.calls, 4)
        self.assertEqual(self.waits, [0.5, 1.0, 2.0])

    def test_other_errors_not_retried(self):
        fn = Flaky(1, exc=ValueError)
        with self.assertRaises(ValueError):
            call_with_retry(fn, sleep=self.sleep)
        self.assertEqual((fn.calls, self.waits), (1, []))

    def test_custom_retry_on(self):
        fn = Flaky(1, exc=KeyError)
        self.assertEqual(call_with_retry(fn, retry_on=(KeyError,), base_delay=0, sleep=self.sleep), "ok")

    def test_invalid_attempts(self):
        with self.assertRaises(ValueError):
            call_with_retry(Flaky(0), attempts=0, sleep=self.sleep)


if __name__ == "__main__":
    unittest.main()
