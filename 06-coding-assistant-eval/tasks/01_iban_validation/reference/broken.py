# Deliberately incomplete: checks format but not the check digits.
def validate_iban(iban: str) -> bool:
    s = iban.replace(" ", "").upper()
    return len(s) == 22 and s.startswith("DE")
