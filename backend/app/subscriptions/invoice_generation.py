from datetime import date

CYCLE_MONTHS = {"monthly": 1, "quarterly": 3, "semiannual": 6, "yearly": 12}


def add_months(value: date, months: int) -> date:
    month = value.month - 1 + months
    return date(value.year + month // 12, month % 12 + 1, value.day)


def invoice_dates(start_date: date, due_day: int, billing_cycle: str, end_date: date):
    first = date(start_date.year, start_date.month, due_day)
    if first < start_date:
        first = add_months(first, CYCLE_MONTHS[billing_cycle])
    current = first
    while current <= end_date:
        yield current
        current = add_months(current, CYCLE_MONTHS[billing_cycle])
