from datetime import date
from pathlib import Path

import pytest

from rightscheck import check
from rightscheck.rules import to_number, classify

SAMPLES = Path(__file__).resolve().parents[1] / "samples"
TODAY = date(2026, 11, 8)


def ids(report, severity=None):
    return {f["rule_id"] for f in report["findings"] if severity is None or f["severity"] == severity}


def run(name, today=TODAY):
    return check((SAMPLES / name).read_text(encoding="utf-8"), today)


@pytest.mark.parametrize("raw,expected", [("1.800,00", 1800.0), ("450", 450.0), ("12,50", 12.5), ("sechs", 6.0)])
def test_to_number(raw, expected):
    assert to_number(raw) == expected


def test_classify():
    assert classify((SAMPLES / "abmahnung.txt").read_text())[0] == "copyright"
    assert classify((SAMPLES / "wg_mietvertrag.txt").read_text())[0] == "rental"
    assert "work" in classify((SAMPLES / "praktikum_vertrag.txt").read_text())


def test_wg_lease():
    found = ids(run("wg_mietvertrag.txt"))
    assert {"deposit_max", "deposit_installments", "tenant_notice", "deadline"} <= found
    assert "deposit_max" in ids(run("wg_mietvertrag.txt"), "red_flag")


def test_wg_lease_bad_clauses():
    r = run("wg_mietvertrag_2.txt")
    red = ids(r, "red_flag")
    assert {"landlord_entry", "rent_reduction", "registration"} <= red
    assert "sublet" in ids(r, "check")
    assert "deposit_max" not in ids(r)          # exactly 3 months is legal


def test_werkstudent_contract():
    r = run("werkstudent_vertrag.txt")
    assert {"minimum_wage", "minimum_vacation", "written_termination"} <= ids(r, "red_flag")   # 5 < 2*24/6
    assert "probation_max" in ids(r, "check")
    assert "werkstudent_20h" not in ids(r)      # 16 hours is fine


def test_minijob_contract():
    r = run("minijob_vertrag.txt")
    assert {"sick_pay", "payslip_reference"} <= ids(r, "red_flag")
    assert "minijob_limit" in ids(r, "check")


def test_internship():
    assert "internship_wage" in ids(run("praktikum_vertrag.txt"), "red_flag")


def test_gym_contract():
    assert {"auto_renewal", "consumer_notice"} <= ids(run("fitnessstudio_vertrag.txt"), "red_flag")


def test_abmahnung():
    assert {"abmahnung_cap", "sign_declaration"} <= ids(run("abmahnung.txt"))


def test_fair_contract_has_no_warnings():
    """Precision matters: a fair contract must not be flagged."""
    r = run("fairer_vertrag.txt")
    assert r["summary"]["red_flag"] == 0 and r["summary"]["check"] == 0


def test_minimum_wage_switches_in_2027():
    text = "Arbeitsvertrag Werkstudent. Der Arbeitnehmer erhält 14,00 € brutto pro Stunde."
    assert check(text, date(2026, 12, 31))["summary"]["red_flag"] == 0
    assert check(text, date(2027, 1, 1))["summary"]["red_flag"] == 1


def test_werkstudent_over_20_hours():
    text = "Arbeitsvertrag Werkstudent. Die wöchentliche Arbeitszeit beträgt 25 Stunden."
    assert "werkstudent_20h" in ids(check(text, TODAY))


def test_every_legal_finding_has_a_source():
    for f in sorted(SAMPLES.glob("*.txt")):
        for item in run(f.name)["findings"]:
            if item["is_law"]:
                assert item["source"].startswith("https://") and item["law"]


def test_phone_contract():
    r = run("handyvertrag.txt")
    assert {"phone_contract", "auto_renewal"} <= ids(r, "red_flag")


def test_fixed_term_and_painting_clause():
    r = run("wg_mietvertrag_3.txt")
    assert {"fixed_term_lease", "cosmetic_repairs"} <= ids(r, "check")
