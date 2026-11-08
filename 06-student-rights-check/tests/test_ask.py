import json
from pathlib import Path

import pytest

from rightscheck.ask import RightsIndex, answer

INDEX = RightsIndex()
KB = json.loads((Path(__file__).resolve().parents[1] / "knowledge_base" / "laws.json").read_text())


@pytest.mark.parametrize("question,expected", [
    ("I was sick on my exam day, what can I do?", "exam_sick_withdrawal"),
    ("My landlord came into my room without asking", "landlord_entry"),
    ("How many days can I work as a non-EU student?", "intl_work_days"),
    ("There are cockroaches in my flat", "rent_reduction"),
    ("Can I get my tax back from my student job?", "tax_refund"),
    ("Do I get minimum wage in an internship?", "internship_wage"),
    ("How many hours can a Werkstudent work?", "werkstudent_20h"),
    ("Mein Vermieter will die Miete erhöhen", "rent_increase_cap"),
    ("I want to return something I bought on Amazon", "withdrawal_online"),
    ("I got an Abmahnung for a torrent", "abmahnung_cap"),
    ("A landlord rejected me because of my foreign name", "discrimination_housing"),
    ("Until when can I stay in my parents' health insurance?", "health_insurance"),
    ("Do I have to pay the Rundfunkbeitrag?", "broadcast_fee"),
    ("I failed an exam and think the grade is wrong", "exam_appeal"),
    ("Do I have to paint the walls when I move out?", "cosmetic_repairs"),
    ("My landlord sent the Nebenkostenabrechnung two years late", "utility_bill"),
    ("My lease is befristet, can I still leave early?", "fixed_term_lease"),
    ("My landlord wants to kick me out because of Eigenbedarf", "landlord_termination"),
    ("I worked a 12 hour shift without a break", "working_hours"),
    ("Do I pay social insurance for my summer holiday job?", "short_term_job"),
    ("My Minijob colleague in full-time gets more per hour for the same job", "equal_pay_parttime"),
    ("They asked me in the job interview if I am pregnant", "interview_questions"),
    ("Can I get Wohngeld as a student?", "wohngeld"),
    ("The bank refused to open an account for me", "basic_account"),
    ("My phone contract with Vodafone runs 24 months, when can I cancel?", "phone_contract"),
    ("How do I cancel a streaming subscription online?", "cancel_button"),
    ("A company sent me a package I didn't order and now wants money", "unordered_goods"),
    ("Which questions can a landlord ask in a flat application?", "tenant_selfdisclosure"),
])
def test_finds_the_right_rule(question, expected):
    assert INDEX.search(question)[0] == expected


def test_unknown_question_does_not_guess():
    a = answer("What is the best pizza in Munich?", INDEX)
    assert not a["found"] and a["rules"] == [] and a["free_help"]


def test_answers_only_contain_verified_rules():
    a = answer("deposit too high and landlord enters my room", INDEX)
    assert a["found"]
    for r in a["rules"]:
        assert r["id"] in KB["rules"] and r["summary"] == KB["rules"][r["id"]]["summary"]


def test_every_rule_is_complete():
    for rid, r in KB["rules"].items():
        assert r["area"] in KB["areas"], rid
        assert r["source"].startswith("https://"), rid
        assert r["keywords"], rid
        assert r["area"] in KB["free_help"], rid


def test_deposit_return_question():
    assert INDEX.search("my landlord kept my deposit after I moved out")[0] == "deposit_return"
