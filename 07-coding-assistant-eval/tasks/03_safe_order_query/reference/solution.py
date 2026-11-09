COLUMNS = ("id", "customer_id", "status", "amount_eur")


def find_orders(conn, customer_id, status=None):
    sql = "SELECT id, customer_id, status, amount_eur FROM orders WHERE customer_id = ?"
    params = [customer_id]
    if status is not None:
        sql += " AND status = ?"
        params.append(status)
    sql += " ORDER BY id"
    return [dict(zip(COLUMNS, row)) for row in conn.execute(sql, params)]
