import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import tools  # noqa: E402


class ToolTests(unittest.TestCase):
    def test_policy_search_german_keywords(self):
        r = tools.search_policies("Kaution Kreditkarte")
        self.assertEqual(r["results"][0]["title"], "Deposit")

    def test_policy_routing_de_en(self):
        cases = {
            "What is the fuel policy?": "Fuel", "Muss ich volltanken?": "Fuel",
            "How much is the deposit?": "Deposit", "Wie hoch ist die Kaution?": "Deposit",
            "Can I cancel for free?": "Cancellation", "Kann ich kostenlos stornieren?": "Cancellation",
            "How old do I need to be?": "Young drivers", "Wie alt muss ich sein?": "Young drivers",
            "Can my wife also drive?": "Additional driver", "Zweiter Fahrer erlaubt?": "Additional driver",
            "Can I drive to Austria?": "Cross-border travel", "Darf ich ins Ausland fahren?": "Cross-border travel",
            "What happens if I have an accident?": "Damage and accidents", "Wer zahlt einen Kratzer?": "Damage and accidents",
            "What if I return the car late?": "Late return", "Ich bin zu spät bei der Rückgabe": "Late return",
            "How many kilometers are included?": "Mileage", "Wie viele Freikilometer habe ich?": "Mileage",
        }
        for question, section in cases.items():
            with self.subTest(question=question):
                self.assertEqual(tools.search_policies(question)["results"][0]["title"], section)

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

    def test_booking_guardrail_resists_manipulated_names(self):
        # The identity check lives in code, so no prompt can talk it out of the rule.
        for name in ["", "*", "%", "' OR '1'='1", "admin", "Becker OR Meier", " becker x"]:
            result = tools.get_booking("RNT-1001", name)
            self.assertIn("error", result, msg=f"leaked with last_name={name!r}")
            self.assertNotIn("model", result)


if __name__ == "__main__":
    unittest.main()
