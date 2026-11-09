# The original buggy code from the prompt.
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
