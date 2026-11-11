from decimal import Decimal, ROUND_HALF_UP

VAT = Decimal("0.19")


def _dec(value) -> Decimal:
    # str() first, so a float like 0.1 becomes exactly 0.1 instead of 0.1000000000000000055...
    return Decimal(str(value))


def invoice_total(lines, discount_percent=0):
    discount = _dec(discount_percent)
    if discount < 0 or discount > 100:
        raise ValueError("discount_percent must be between 0 and 100")
    net = Decimal("0")
    for price, qty in lines:
        price, qty = _dec(price), _dec(qty)
        if price < 0 or qty < 0:
            raise ValueError("price and quantity must not be negative")
        net += price * qty
    net = net * (1 - discount / 100)          # discount on the net sum, before VAT
    gross = net * (1 + VAT)
    return gross.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def add_line(price, qty, lines=None):
    # Never mutate the caller's list or a shared default list.
    return list(lines or []) + [(price, qty)]
