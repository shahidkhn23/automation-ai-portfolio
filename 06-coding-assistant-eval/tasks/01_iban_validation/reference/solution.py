def validate_iban(iban: str) -> bool:
    if not isinstance(iban, str):
        return False
    s = iban.replace(" ", "").upper()
    if len(s) != 22 or not s.startswith("DE") or not s[2:].isdigit() or not s[2:].isascii():
        return False
    rearranged = s[4:] + s[:4]
    digits = "".join(str(int(ch, 36)) for ch in rearranged)
    return int(digits) % 97 == 1
