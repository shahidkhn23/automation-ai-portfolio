import unittest

from solution import sales_by_region

CSV = """date,region,product,amount_eur
2026-11-01,Bayern,Kit A,100.00
2026-11-01, bayern ,Kit B,"1.234,50"
2026-11-02,Hessen,Kit A,99.90
2026-11-02,,Kit A,50.00
2026-11-03,Hessen,Kit C,abc
2026-11-03,Berlin,Kit A
2026-11-04,BERLIN,Kit B,"10,10"
"""


class SalesReportTests(unittest.TestCase):
    def setUp(self):
        self.result = sales_by_region(CSV)

    def test_totals(self):
        self.assertEqual(self.result["totals"], {"Bayern": 1334.5, "Hessen": 99.9, "Berlin": 10.1})

    def test_sorted_highest_first(self):
        self.assertEqual(list(self.result["totals"]), ["Bayern", "Hessen", "Berlin"])

    def test_skipped_rows(self):
        self.assertEqual(self.result["skipped_rows"], 3)

    def test_empty_export(self):
        self.assertEqual(sales_by_region("date,region,product,amount_eur\n"), {"totals": {}, "skipped_rows": 0})


if __name__ == "__main__":
    unittest.main()
