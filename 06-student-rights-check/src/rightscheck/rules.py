"""Deterministic red-flag detection.

Why rules and not only an LLM? Because a student who relies on this needs the
legal facts to be right every time. The rules find the clause and the number;
each finding points to an entry in knowledge_base/laws.json that was checked
by hand. The LLM layer (llm.py) only explains these findings in plain words.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

NUMBER_WORDS = {
    "ein": 1, "eine": 1, "einen": 1, "einem": 1, "einer": 1,
    "zwei": 2, "drei": 3, "vier": 4, "fünf": 5, "sechs": 6, "sieben": 7,
    "acht": 8, "neun": 9, "zehn": 10, "elf": 11, "zwölf": 12,
    "achtzehn": 18, "vierundzwanzig": 24,
}

RED = "red_flag"      # clause very likely conflicts with the law
CHECK = "check"       # may be a problem, depends on details -> get it checked
INFO = "info"         # good to know (deadlines, scam patterns, ...)


@dataclass
class Finding:
    rule_id: str          # key in laws.json, or a heuristic id
    severity: str
    evidence: str         # the clause as it appears in the document
    detail: str           # what exactly the tool found (numbers etc.)
    heuristic: bool = False  # True = not a law, a warning pattern


@dataclass
class Analysis:
    doc_types: list[str]
    findings: list[Finding] = field(default_factory=list)


# --------------------------------------------------------------------------- helpers

def to_number(token: str) -> float | None:
    """'1.350,00' -> 1350.0, '450' -> 450.0, 'drei' -> 3.0"""
    token = token.strip().lower()
    if token in NUMBER_WORDS:
        return float(NUMBER_WORDS[token])
    token = token.replace(" ", "")
    if re.fullmatch(r"\d{1,3}(\.\d{3})+(,\d+)?", token):      # 1.350,00
        token = token.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d+,\d+", token):                       # 13,50
        token = token.replace(",", ".")
    try:
        return float(token)
    except ValueError:
        return None


NUM = r"(\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:[,\.]\d+)?|\b(?:" + "|".join(sorted(NUMBER_WORDS, key=len, reverse=True)) + r")\b)"


def sentences(text: str) -> list[str]:
    text = re.sub(r"[ \t]+", " ", text)
    # split on sentence end or line break, but not on "Abs." / "Nr." / numbers like 1.350
    parts = re.split(r"(?<![0-9]\.)(?<!Abs\.)(?<!Nr\.)(?<=[.!?])\s+|\n+", text)
    return [p.strip() for p in parts if p and p.strip()]


def find_sentence(text: str, pattern: str) -> tuple[str, re.Match] | None:
    for s in sentences(text):
        m = re.search(pattern, s, flags=re.IGNORECASE)
        if m:
            return s, m
    return None


# --------------------------------------------------------------------------- classify

KEYWORDS = {
    "rental": ["mietvertrag", "untermiet", "vermieter", "mieter", "kaltmiete", "kaution", "wg-zimmer", "wohnung", "mieterhöhung"],
    "work": ["arbeitsvertrag", "werkstudent", "arbeitgeber", "arbeitnehmer", "stundenlohn", "minijob", "probezeit",
             "praktikum", "praktikant", "geringfügig"],
    "consumer": ["mitgliedschaft", "vertragslaufzeit", "mindestlaufzeit", "abonnement", "tarif", "verlängert sich"],
    "copyright": ["abmahnung", "urheberrecht", "unterlassungserklärung", "filesharing", "tauschbörse", "urhg"],
}


def classify(text: str) -> list[str]:
    low = text.lower()
    scores = {t: sum(low.count(k) for k in kws) for t, kws in KEYWORDS.items()}
    best = max(scores.values())
    if best == 0:
        return ["unknown"]
    # keep every type that is clearly present (>= 40% of the best score)
    return [t for t, s in sorted(scores.items(), key=lambda x: -x[1]) if s >= max(2, 0.4 * best)] or \
           [max(scores, key=scores.get)]


# --------------------------------------------------------------------------- rental

def check_rental(text: str) -> list[Finding]:
    out: list[Finding] = []

    rent = None
    rent_hit = find_sentence(text, r"(?:kaltmiete|grundmiete)\D{0,40}?" + NUM + r"\s*(?:€|eur)")
    if rent_hit:
        rent = to_number(rent_hit[1].group(1))

    months_hit = find_sentence(text, r"(?:kaution|mietsicherheit)[^.]*?" + NUM +
                               r"\s*(?:netto)?(?:kaltmieten|monatsmieten|mieten|monatskaltmieten)")
    amount_hit = find_sentence(text, r"(?:kaution|mietsicherheit)\D{0,60}?" + NUM + r"\s*(?:€|eur)")
    if months_hit and (to_number(months_hit[1].group(1)) or 0) > 3:
        out.append(Finding("deposit_max", RED, months_hit[0],
                           f"The contract asks for {months_hit[1].group(1)} months' rent as deposit. The limit is 3."))
    elif amount_hit and rent:
        dep = to_number(amount_hit[1].group(1))
        if dep and dep > 3 * rent + 0.01:
            out.append(Finding("deposit_max", RED, amount_hit[0],
                               f"Deposit {dep:,.2f} EUR is more than 3 x cold rent "
                               f"({rent:,.2f} EUR x 3 = {3 * rent:,.2f} EUR)."))

    up_front = find_sentence(
        text, r"(?:kaution|mietsicherheit)[^.]*?(?:sofort|vollständig|in voller höhe|vor (?:dem )?einzug|"
              r"bei schlüsselübergabe|einmalig|auf einmal)")
    if up_front:
        out.append(Finding("deposit_installments", CHECK, up_front[0],
                           "The contract asks for the full deposit at once."))

    notice = find_sentence(text, r"kündigungsfrist[^.]*?" + NUM + r"\s*monat")
    if notice:
        n = to_number(notice[1].group(1))
        if n and n > 3:
            out.append(Finding("tenant_notice", CHECK, notice[0],
                               f"Notice period for you is {int(n)} months; the legal standard for tenants is 3."))

    no_reduction = find_sentence(text, r"(?:miet)?minderung[^.]*?ausgeschlossen|ausschluss der (?:miet)?minderung")
    if no_reduction:
        out.append(Finding("rent_reduction", RED, no_reduction[0],
                           "The contract excludes rent reduction for defects. In residential leases that is not allowed."))

    entry = find_sentence(text, r"(?:vermieter|eigentümer)[^.]*?(?:jederzeit|ohne (?:vorherige )?ankündigung)[^.]*?"
                                r"(?:betreten|zutritt|besichtig)")
    if entry:
        out.append(Finding("landlord_entry", RED, entry[0],
                           "The landlord reserves the right to enter at any time / without notice. Such clauses are invalid."))

    sublet = find_sentence(text, r"untervermietung[^.]*?(?:ausgeschlossen|verboten|nicht gestattet|untersagt|nicht erlaubt)")
    if sublet:
        out.append(Finding("sublet", CHECK, sublet[0],
                           "The contract bans subletting completely. You may still be able to demand permission "
                           "for part of the flat if you get a legitimate interest later."))

    no_reg = find_sentence(text, r"(?:anmeldung|ummeldung|wohnsitz anmelden)[^.]*?(?:nicht (?:möglich|gestattet|erlaubt)|untersagt)"
                                 r"|keine wohnungsgeberbestätigung")
    if no_reg:
        out.append(Finding("registration", RED, no_reg[0],
                           "You must register your address within 2 weeks and the landlord must confirm your move-in."))

    incr = find_sentence(text, r"(?:mieterhöhung|erhöh\w*)[^.]*?" + NUM + r"\s*(?:%|prozent)")
    if incr:
        pct = to_number(incr[1].group(1))
        if pct and pct > 15:
            out.append(Finding("rent_increase_cap", CHECK, incr[0],
                               f"Rent increase of {pct:g}%. In Munich the cap is 15% within 3 years (20% where no "
                               "ordinance applies)."))

    paint = find_sentence(text, r"schönheitsreparaturen[^.]*?(?:alle|spätestens nach|jeweils nach)\s*" + NUM + r"\s*jahr"
                                r"|(?:alle|spätestens nach)\s*" + NUM + r"\s*jahr\w*[^.]*?(?:streichen|renovieren|tapezieren)")
    if paint:
        out.append(Finding("cosmetic_repairs", CHECK, paint[0],
                           "Rigid renovation schedule. Such clauses are invalid, and if you moved in unrenovated "
                           "you usually don't have to renovate at all."))

    fixed = find_sentence(text, r"(?:befristet|endet (?:automatisch|ohne kündigung)|mietzeit endet)[^.]*")
    if fixed and not re.search(r"eigenbedarf|selbst nutzen|familienangehörige|beseitig|wesentlich verändert|instand|"
                               r"umbau|sanierung|dienstverpflicht|vorübergehend", text, re.I):
        out.append(Finding("fixed_term_lease", CHECK, fixed[0],
                           "The lease is limited in time but no legal reason is given in writing. "
                           "Then it usually counts as open-ended."))

    scam = find_sentence(text, r"western union|moneygram|bitcoin|krypto|ohne besichtigung|"
                               r"vor der besichtigung|schlüssel (?:per|mit der) post|treuhand(?:service|konto)")
    if scam:
        out.append(Finding("scam_pattern", RED, scam[0],
                           "Payment before viewing / untraceable payment / keys by post is a classic "
                           "WG-scam pattern. Never send money before you have seen the room and signed.",
                           heuristic=True))
    return out


# --------------------------------------------------------------------------- work

def check_work(text: str, today: date) -> list[Finding]:
    out: list[Finding] = []
    min_wage = 14.60 if today >= date(2027, 1, 1) else 13.90

    for s in sentences(text):
        m = re.search(NUM + r"\s*(?:€|eur|euro)\s*(?:brutto\s*)?(?:pro|je|/)\s*(?:arbeits)?(?:stunde|std\.?|h)\b", s, re.I)
        if m:
            wage = to_number(m.group(1))
            if wage and wage < min_wage:
                out.append(Finding("minimum_wage", RED, s,
                                   f"Hourly wage {wage:.2f} EUR is below the minimum wage of {min_wage:.2f} EUR "
                                   f"valid on {today:%d.%m.%Y}."))
            break

    prob = find_sentence(text, r"probezeit[^.]*?" + NUM + r"\s*monat")
    if prob:
        n = to_number(prob[1].group(1))
        if n and n > 6:
            out.append(Finding("probation_max", CHECK, prob[0],
                               f"Probation of {int(n)} months. The short 2-week notice can only apply for 6."))

    form = find_sentence(text, r"(?:kündigung|kündigen|gekündigt)[^.]*?(?:e-mail|email|whatsapp|sms|mündlich|telefonisch)")
    if form:
        out.append(Finding("written_termination", RED, form[0],
                           "The contract allows termination by e-mail/message/verbally. "
                           "By law a job termination must be on signed paper."))

    sick = find_sentence(text, r"kein(?:en)?\s+anspruch auf (?:entgelt|lohn)fortzahlung|keine (?:entgelt|lohn)fortzahlung|"
                               r"krankheitstage werden nicht (?:bezahlt|vergütet)|bei krankheit[^.]*?(?:keine vergütung|unbezahlt)")
    if sick:
        out.append(Finding("sick_pay", RED, sick[0], "The contract excludes sick pay. The law gives up to 6 weeks."))

    ref = find_sentence(text, r"kein(?:en)?\s+(?:anspruch auf (?:ein )?)?(?:arbeits)?zeugnis|zeugnis wird nicht (?:erteilt|ausgestellt)|"
                              r"anspruch auf (?:ein )?(?:arbeits)?zeugnis besteht nicht")
    if ref:
        out.append(Finding("payslip_reference", RED, ref[0], "The contract excludes a job reference. You have a right to one."))

    low = text.lower()
    if "werkstudent" in low:
        hrs = find_sentence(text, NUM + r"\s*(?:wochen)?stunden\s*(?:pro|je|in der|die|/)\s*woche|"
                                  r"wöchentliche arbeitszeit\D{0,30}?" + NUM + r"\s*stunden|arbeitszeit beträgt\D{0,10}?" + NUM + r"\s*stunden")
        if hrs:
            n = next((to_number(g) for g in hrs[1].groups() if g), None)
            if n and n > 20:
                out.append(Finding("werkstudent_20h", CHECK, hrs[0],
                                   f"{n:g} hours a week. Above 20 hours during the semester you can lose the "
                                   "Werkstudent status in social insurance."))

    if re.search(r"minijob|geringfügig", low):
        pay = find_sentence(text, r"(?:monatlich|pro monat|im monat|monatliche vergütung|monatsvergütung)\D{0,40}?" + NUM + r"\s*(?:€|eur)|"
                                  + NUM + r"\s*(?:€|eur)\s*(?:brutto\s*)?(?:pro|im|je)\s*monat")
        if pay:
            v = next((to_number(g) for g in pay[1].groups() if g), None)
            limit = 633 if today >= date(2027, 1, 1) else 603
            if v and v > limit:
                out.append(Finding("minijob_limit", CHECK, pay[0],
                                   f"{v:,.2f} EUR a month is above the Minijob limit of {limit} EUR. "
                                   "Then it is not a Minijob any more."))

    if re.search(r"praktik", low) and "pflichtpraktikum" not in low:
        unpaid = re.search(r"unvergütet|unbezahlt|ohne vergütung|keine vergütung", low)
        dur = re.search(NUM + r"\s*monat", low)
        if unpaid and dur and (to_number(dur.group(1)) or 0) > 3:
            out.append(Finding("internship_wage", RED, find_sentence(text, r"unvergütet|unbezahlt|ohne vergütung|keine vergütung")[0],
                               f"Unpaid voluntary internship of {dur.group(1)} months. Longer than 3 months must pay "
                               "minimum wage from day one."))

    days = re.search(NUM + r"\s*(?:arbeits)?tag(?:e|en)?\s*(?:pro|je|in der|die)\s*woche", text, re.I)
    days_n = to_number(days.group(1)) if days else None
    if re.search(r"kein(?:en)?\s+(?:anspruch auf\s+)?(?:bezahlten\s+)?urlaub|urlaub\s+(?:ist|wird)\s+(?:nur\s+)?unbezahlt",
                 text, re.I):
        s = find_sentence(text, r"kein(?:en)?\s+(?:anspruch auf\s+)?(?:bezahlten\s+)?urlaub|unbezahlt")[0]
        out.append(Finding("minimum_vacation", RED, s, "The contract gives no paid holiday at all."))
    else:
        hit = find_sentence(text, r"urlaub\w*\D{0,40}?" + NUM + r"\s*(?:arbeits|werk|urlaubs)?tage") or \
              find_sentence(text, NUM + r"\s*(?:bezahlte\s*)?(?:urlaubstage|(?:arbeits|werk)?tage\s+(?:bezahlten\s+)?(?:erholungs)?urlaub)")
        if hit and days_n:
            v = to_number(hit[1].group(1))
            legal = 24 * days_n / 6
            if v is not None and v < legal:
                out.append(Finding("minimum_vacation", RED, hit[0],
                                   f"{int(v)} holiday days for a {int(days_n)}-day week. "
                                   f"Legal minimum: {days_n:g} x 24 / 6 = {legal:g} days."))
    return out


# --------------------------------------------------------------------------- consumer contracts

def check_consumer(text: str) -> list[Finding]:
    out: list[Finding] = []
    ren = find_sentence(text, r"verlängert sich[^.]*?um\s*(?:jeweils\s*)?(?:weitere[nm]?\s*)?" + NUM + r"\s*(monat|jahr)")
    if ren and "unbestimmte zeit" not in ren[0].lower():
        n = to_number(ren[1].group(1)) or 0
        months = n * (12 if ren[1].group(2).lower().startswith("jahr") else 1)
        if months > 1:
            out.append(Finding("auto_renewal", RED, ren[0],
                               f"Automatic renewal for another fixed {int(n)} {ren[1].group(2)}(e). "
                               "Since March 2022 only renewal for an indefinite time (cancel monthly) is allowed."))

    if re.search(r"mobilfunk|handyvertrag|telekommunikation|internetanschluss|dsl|tarif", text, re.I):
        term = find_sentence(text, r"(?:mindest)?(?:vertrags)?laufzeit\D{0,40}?" + NUM + r"\s*monat")
        if term and (to_number(term[1].group(1)) or 0) > 24:
            out.append(Finding("phone_contract", RED, term[0],
                               f"Initial term of {term[1].group(1)} months. Phone/internet contracts may bind you "
                               "for at most 24 months."))

    wd = find_sentence(text, r"kein(?:\s+gesetzliches)?\s+widerrufsrecht|widerruf(?:srecht)?[^.]*?ausgeschlossen")
    if wd:
        out.append(Finding("withdrawal_online", CHECK, wd[0],
                           "The contract says there is no right of withdrawal. For online/phone contracts you usually "
                           "have 14 days; some exceptions exist (e.g. custom-made goods)."))

    note = find_sentence(text, r"kündigungsfrist[^.]*?" + NUM + r"\s*(monat|woche)")
    if note:
        n = to_number(note[1].group(1)) or 0
        months = n if note[1].group(2).lower().startswith("monat") else n / 4.345
        if months > 1:
            out.append(Finding("consumer_notice", RED, note[0],
                               f"You must cancel {int(n)} {note[1].group(2)}(e) before the end. Max allowed: 1 month."))
    return out


# --------------------------------------------------------------------------- copyright warning letters

def check_copyright(text: str) -> list[Finding]:
    out: list[Finding] = []
    gw = find_sentence(text, r"gegenstandswert\D{0,40}?" + NUM)
    if gw:
        v = to_number(gw[1].group(1))
        if v and v > 1000:
            out.append(Finding("abmahnung_cap", CHECK, gw[0],
                               f"Lawyer fees are calculated on {v:,.0f} EUR. For a first warning to a private, "
                               "non-commercial user the law caps this value at 1,000 EUR."))
    ue = find_sentence(text, r"unterlassungserklärung")
    if ue:
        out.append(Finding("sign_declaration", CHECK, ue[0],
                           "You are asked to sign a cease-and-desist declaration. It is a binding promise, "
                           "often with a contractual penalty. Do not ignore the letter, and do not sign "
                           "anything before it has been checked.", heuristic=True))
    return out


# --------------------------------------------------------------------------- deadlines (all documents)

def find_deadlines(text: str) -> list[Finding]:
    out = []
    for s in sentences(text):
        m = re.search(r"(?:bis (?:zum |spätestens )?|spätestens (?:am |bis )?|frist[^.]{0,20}?)(\d{1,2}\.\d{1,2}\.\d{2,4})", s, re.I) \
            or re.search(r"innerhalb (?:von )?" + NUM + r"\s*(tag|woche)", s, re.I)
        if m:
            out.append(Finding("deadline", INFO, s, "Deadline found: put it in your calendar.", heuristic=True))
    return out[:5]


# --------------------------------------------------------------------------- entry point

def analyse(text: str, today: date | None = None) -> Analysis:
    today = today or date.today()
    types = classify(text)
    a = Analysis(doc_types=types)
    if "rental" in types:
        a.findings += check_rental(text)
    if "work" in types:
        a.findings += check_work(text, today)
    if "consumer" in types:
        a.findings += check_consumer(text)
    if "copyright" in types:
        a.findings += check_copyright(text)
    a.findings += find_deadlines(text)
    order = {RED: 0, CHECK: 1, INFO: 2}
    a.findings.sort(key=lambda f: order[f.severity])
    return a
