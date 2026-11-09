Write a Python module `solution.py` with a function:

```python
def sales_by_region(csv_text: str) -> dict:
```

`csv_text` is a CSV export with the header `date,region,product,amount_eur`. Real exports are messy, so:

- Region names may have different case and extra spaces (`" Bayern"`, `"bayern"`): group them case-insensitively and return the name in title case (`"Bayern"`).
- `amount_eur` may use a German decimal comma (`"1.234,50"`) or a dot (`"99.90"`).
- Skip rows that are malformed: missing fields, empty region, or an amount that is not a number. Count them.
- Return:

```python
{"totals": {"Bayern": 1334.5, ...}, "skipped_rows": 2}
```

with each total rounded to 2 decimals and `totals` sorted by total, highest first.

Use only the Python standard library.
