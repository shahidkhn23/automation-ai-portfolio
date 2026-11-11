import sqlite3

_COLUMNS = ("id", "customer_id", "status", "amount_eur")
_BY_CUSTOMER = "SELECT id, customer_id, status, amount_eur FROM orders WHERE customer_id = ? ORDER BY id ASC"
_BY_CUSTOMER_AND_STATUS = ("SELECT id, customer_id, status, amount_eur FROM orders "
                           "WHERE customer_id = ? AND status = ? ORDER BY id ASC")


def find_orders(conn: sqlite3.Connection, customer_id: str, status: str | None = None) -> list[dict]:
    """Untrusted input is only ever passed as query parameters, never put into the SQL text."""
    if status is None:
        rows = conn.execute(_BY_CUSTOMER, (customer_id,)).fetchall()
    else:
        rows = conn.execute(_BY_CUSTOMER_AND_STATUS, (customer_id, status)).fetchall()
    return [dict(zip(_COLUMNS, row)) for row in rows]
