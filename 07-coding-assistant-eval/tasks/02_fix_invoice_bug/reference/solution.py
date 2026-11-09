from decimal import ROUND_HALF_UP, Decimal

VAT = Decimal("0.19")


def invoice_total(lines, discount_percent=0):
    discount = Decimal(str(discount_percent))
    if not 0 <= discount <= 100:
        raise ValueError("discount_percent must be between 0 and 100")
    net = Decimal("0")
    for price, qty in lines:
        price, qty = Decimal(str(price)), Decimal(str(qty))
        if price < 0 or qty < 0:
            raise ValueError("price and quantity must not be negative")
        net += price * qty
    net -= net * discount / 100
    gross = net * (1 + VAT)
    return gross.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def add_line(price, qty, lines=None):
    return [*(lines or []), (price, qty)]
