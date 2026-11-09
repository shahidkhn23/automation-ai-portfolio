The finance team reports wrong invoice totals. Fix the bugs in the code below and return the complete corrected module as `solution.py`. Keep the function names and signatures.

Business rules:
- `lines` is a list of `(net_unit_price, quantity)` tuples; prices are in EUR.
- The discount (in percent, 0–100) applies to the **net** sum, before VAT.
- VAT is 19 %.
- The result is the gross total, rounded to whole cents with commercial rounding (0.5 cent rounds up), returned as a `Decimal` with two decimal places.
- Invalid input (negative quantity or price, discount outside 0–100) raises `ValueError`.
- `add_line` returns a new list and must not change lists from earlier calls.

```python
VAT = 0.19


def invoice_total(lines, discount_percent=0):
    total = 0
    for price, qty in lines:
        total += price * qty
    total = total * (1 + VAT)
    total = total - total * discount_percent / 100
    return round(total, 2)


def add_line(price, qty, lines=[]):
    lines.append((price, qty))
    return lines
```

Use only the Python standard library.
