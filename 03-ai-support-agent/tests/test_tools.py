import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import tools  # noqa: E402


class ToolTests(unittest.TestCase):
    def test_policy_search_german_keywords(self):
        r = tools.search_policies("Kaution Kreditkarte")
        self.assertEqual(r["results"][0]["title"], "Deposit")

    def test_availability_excludes_booked_car(self):
        r = tools.find_available_cars("Munich", "2026-12-04", "2026-12-06", "SUV")
        self.assertNotIn("MUC-03", [c["car_id"] for c in r["available"]])

    def test_availability_rejects_bad_dates(self):
        self.assertIn("error", tools.find_available_cars("Munich", "2026-12-06", "2026-12-01"))
        self.assertIn("error", tools.find_available_cars("Munich", "12/01/2026", "12/05/2026"))

    def test_booking_requires_matching_last_name(self):
        self.assertIn("error", tools.get_booking("RNT-1001", "Meier"))
        self.assertEqual(tools.get_booking("rnt-1001", "becker")["model"], "VW Polo")

    def test_unknown_tool(self):
        self.assertIn("error", tools.run_tool("delete_everything", {}))


if __name__ == "__main__":
    unittest.main()
