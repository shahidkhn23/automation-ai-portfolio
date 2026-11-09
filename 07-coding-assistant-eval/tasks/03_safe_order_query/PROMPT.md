Write a Python module `solution.py` with a function:

```python
def find_orders(conn, customer_id: str, status: str | None = None) -> list[dict]:
```

`conn` is an open `sqlite3` connection to a database with this table:

```sql
CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id TEXT, status TEXT, amount_eur REAL);
```

- Return all orders of `customer_id`, optionally filtered by `status`.
- Each order is a dict with the keys `id`, `customer_id`, `status`, `amount_eur`.
- Sort by `id` ascending.
- `customer_id` and `status` come straight from a web form, so treat them as untrusted input.

Use only the Python standard library.
