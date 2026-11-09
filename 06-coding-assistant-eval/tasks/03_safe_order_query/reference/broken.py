# Deliberately insecure: builds SQL with an f-string (SQL injection).
COLUMNS = ("id", "customer_id", "status", "amount_eur")


def find_orders(conn, customer_id, status=None):
    sql = f"SELECT id, customer_id, status, amount_eur FROM orders WHERE customer_id = '{customer_id}'"
    if status is not None:
        sql += f" AND status = '{status}'"
    sql += " ORDER BY id"
    return [dict(zip(COLUMNS, row)) for row in conn.execute(sql)]
