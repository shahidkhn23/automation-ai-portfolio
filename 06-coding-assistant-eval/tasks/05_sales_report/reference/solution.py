import csv
import io


def _amount(raw):
    raw = raw.strip()
    if "," in raw:
        raw = raw.replace(".", "").replace(",", ".")
    return float(raw)


def sales_by_region(csv_text):
    totals, skipped = {}, 0
    for row in csv.DictReader(io.StringIO(csv_text)):
        region = (row.get("region") or "").strip()
        try:
            if not region or row.get("amount_eur") is None:
                raise ValueError
            amount = _amount(row["amount_eur"])
        except ValueError:
            skipped += 1
            continue
        key = region.title()
        totals[key] = totals.get(key, 0) + amount
    ordered = dict(sorted(((k, round(v, 2)) for k, v in totals.items()), key=lambda kv: -kv[1]))
    return {"totals": ordered, "skipped_rows": skipped}
