import time


def call_with_retry(fn, attempts=3, base_delay=0.5, retry_on=(ConnectionError, TimeoutError), sleep=time.sleep):
    if attempts < 1:
        raise ValueError("attempts must be at least 1")
    for i in range(attempts):
        try:
            return fn()
        except retry_on:
            if i == attempts - 1:
                raise                      # last attempt: no wait, re-raise the last exception
            sleep(base_delay * (2 ** i))   # base, 2*base, 4*base, ...
