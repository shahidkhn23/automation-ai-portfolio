import unittest
from decimal import Decimal

from solution import add_line, invoice_total


class InvoiceTests(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(invoice_total([(10, 2)]), Decimal("23.80"))

    def test_returns_decimal_with_cents(self):
        result = invoice_total([(1, 1)])
        self.assertIsInstance(result, Decimal)
        self.assertEqual(result, Decimal("1.19"))
        self.assertEqual(result.as_tuple().exponent, -2)

    def test_discount_on_net(self):
        self.assertEqual(invoice_total([(100, 1)], discount_percent=10), Decimal("107.10"))

    def test_commercial_rounding(self):
        # 0.05 * 3 * 1.19 = 0.1785 -> 0.18 ; 2.50 * 1.19 = 2.975 -> 2.98 (float round() gives 2.97)
        self.assertEqual(invoice_total([(0.05, 3)]), Decimal("0.18"))
        self.assertEqual(invoice_total([(2.5, 1)]), Decimal("2.98"))

    def test_many_small_lines_no_float_drift(self):
        self.assertEqual(invoice_total([(0.1, 1)] * 10), Decimal("1.19"))

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            invoice_total([(10, -1)])
        with self.assertRaises(ValueError):
            invoice_total([(-10, 1)])
        with self.assertRaises(ValueError):
            invoice_total([(10, 1)], discount_percent=120)

    def test_add_line_does_not_share_state(self):
        first = add_line(10, 1)
        second = add_line(20, 1)
        self.assertEqual(first, [(10, 1)])
        self.assertEqual(second, [(20, 1)])

    def test_add_line_does_not_mutate_input(self):
        base = [(5, 1)]
        new = add_line(10, 2, base)
        self.assertEqual(base, [(5, 1)])
        self.assertEqual(new, [(5, 1), (10, 2)])


if __name__ == "__main__":
    unittest.main()
