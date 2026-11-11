import csv
import io
import math


def _parse_amount(text: str) -> float:
    s = text.strip().replace(" ", "")
    if "," in s:                       # German format: 1.234,50
        s = s.replace(".", "").replace(",", ".")
    value = float(s)                   # raises ValueError if not a number
    if not math.isfinite(value):
        raise ValueError("not a finite number")
    return value


def sales_by_region(csv_text: str) -> dict:
    totals: dict[str, float] = {}
    names: dict[str, str] = {}
    skipped = 0
    for row in csv.DictReader(io.StringIO(csv_text)):
        try:
            if None in row or any(v is None for v in row.values()):
                raise ValueError("missing or extra fields")
            region = " ".join(row["region"].split())
            if not region:
                raise ValueError("empty region")
            amount = _parse_amount(row["amount_eur"])
        except (ValueError, KeyError, AttributeError):
            skipped += 1
            continue
        key = region.casefold()
        names.setdefault(key, region.title())
        totals[key] = totals.get(key, 0.0) + amount
    result = {names[k]: round(v, 2) for k, v in totals.items()}
    return {"totals": dict(sorted(result.items(), key=lambda kv: kv[1], reverse=True)),
            "skipped_rows": skipped}
