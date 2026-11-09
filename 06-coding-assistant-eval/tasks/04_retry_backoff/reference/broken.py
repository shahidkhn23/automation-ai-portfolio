# Deliberately wrong: retries every exception, fixed delay, sleeps after the last attempt.
import time


def call_with_retry(fn, attempts=3, base_delay=0.5, retry_on=(ConnectionError, TimeoutError), sleep=time.sleep):
    last = None
    for _ in range(attempts):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            last = exc
            sleep(base_delay)
    raise last
