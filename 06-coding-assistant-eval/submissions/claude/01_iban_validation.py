def validate_iban(iban: str) -> bool:
    """Validate a German IBAN (format + ISO 13616 mod-97 check digits). Never raises."""
    try:
        if not isinstance(iban, str):
            return False
        s = "".join(iban.split()).upper()
        if len(s) != 22 or not s.startswith("DE"):
            return False
        if not all(c in "0123456789" for c in s[2:]):
            return False
        rearranged = s[4:] + s[:4]
        number = "".join(str(int(c, 36)) for c in rearranged)
        return int(number) % 97 == 1
    except Exception:
        return False
