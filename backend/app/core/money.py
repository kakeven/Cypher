from decimal import Decimal


def money(value: Decimal | None) -> float:
    return float(value or 0)
