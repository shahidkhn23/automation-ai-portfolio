# Deliberately naive: no normalisation of regions or German decimal commas.
import csv
import io


def sales_by_region(csv_text):
    totals, skipped = {}, 0
    for row in csv.DictReader(io.StringIO(csv_text)):
        try:
            totals[row["region"]] = totals.get(row["region"], 0) + float(row["amount_eur"])
        except (ValueError, TypeError):
            skipped += 1
    return {"totals": totals, "skipped_rows": skipped}
