Write a Python module `solution.py` with a function:

```python
def call_with_retry(fn, attempts=3, base_delay=0.5, retry_on=(ConnectionError, TimeoutError), sleep=time.sleep):
```

It calls `fn()` and returns its result. Requirements:

- If `fn` raises an exception whose type is in `retry_on`, wait and try again, up to `attempts` calls in total.
- Exponential backoff: wait `base_delay`, then `2 * base_delay`, then `4 * base_delay`, … between calls. Use the `sleep` parameter for waiting (tests pass a fake).
- Do not wait after the last attempt.
- Any other exception is raised immediately, without retrying.
- If all attempts fail, raise the last exception.
- `attempts` smaller than 1 raises `ValueError`.

Use only the Python standard library.
