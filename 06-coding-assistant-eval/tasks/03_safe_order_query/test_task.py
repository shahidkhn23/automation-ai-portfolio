import sqlite3
import unittest

from solution import find_orders


def make_db():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id TEXT, status TEXT, amount_eur REAL)")
    conn.executemany("INSERT INTO orders VALUES (?, ?, ?, ?)", [
        (1, "C-1", "open", 100.0),
        (2, "C-2", "open", 50.0),
        (3, "C-1", "shipped", 20.0),
        (4, "O'Brien", "open", 75.0),
    ])
    return conn


class OrderQueryTests(unittest.TestCase):
    def setUp(self):
        self.conn = make_db()

    def test_by_customer(self):
        rows = find_orders(self.conn, "C-1")
        self.assertEqual([r["id"] for r in rows], [1, 3])
        self.assertEqual(rows[0], {"id": 1, "customer_id": "C-1", "status": "open", "amount_eur": 100.0})

    def test_status_filter(self):
        self.assertEqual([r["id"] for r in find_orders(self.conn, "C-1", "shipped")], [3])

    def test_quote_in_value(self):
        self.assertEqual([r["id"] for r in find_orders(self.conn, "O'Brien")], [4])

    def test_injection_does_not_leak_other_customers(self):
        self.assertEqual(find_orders(self.conn, "x' OR '1'='1"), [])
        self.assertEqual(find_orders(self.conn, "C-1", "open' OR '1'='1"), [])

    def test_injection_does_not_modify_data(self):
        find_orders(self.conn, "C-1'; DROP TABLE orders; --")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0], 4)


if __name__ == "__main__":
    unittest.main()
