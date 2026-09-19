from calendar import monthrange
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from ..core.money import money
from .repository import DashboardRepository


class DashboardService:
    def __init__(self, db: Session): self.repo = DashboardRepository(db)
    def bounds(self, value):
        year, month = map(int, value.split("-")); return year, month, date(year, month, 1), date(year, month, monthrange(year, month)[1])
    def is_owner_category(self, item): return item.category and item.category.name.casefold() != "outras pessoas"
    def is_other_people_category(self, item): return item.category and item.category.name.casefold() == "outras pessoas"
    def dashboard(self, period):
        value = period or date.today().strftime("%Y-%m"); year, _, start, end = self.bounds(value); all_items = self.repo.transactions(); card_purchases = self.repo.card_purchases(); card_invoices = self.repo.card_invoices(); payment_ids = self.repo.payment_transaction_ids(); current = [item for item in all_items if start <= item.date <= end]
        current_expenses = [item for item in current if item.type == "expense" and item.id not in payment_ids]; current_card_purchases = [item for item in card_purchases if item.invoice.reference_month == value]
        owner_expenses = [item for item in current_expenses if self.is_owner_category(item)]
        owner_card_purchases = [item for item in current_card_purchases if self.is_owner_category(item)]
        income = sum((item.amount for item in current if item.type == "income"), Decimal("0")); expense = sum((item.amount for item in current_expenses), Decimal("0")) + sum((item.amount for item in current_card_purchases), Decimal("0")); net_expense = sum((item.amount for item in owner_expenses), Decimal("0")) + sum((item.amount for item in owner_card_purchases), Decimal("0")); card_pending = sum((max(Decimal("0"), sum((purchase.amount for purchase in invoice.purchases if not self.is_other_people_category(purchase)), Decimal("0")) - sum((payment.amount for payment in invoice.payments if payment.paid_by_owner), Decimal("0"))) for invoice in card_invoices if invoice.status == "open"), Decimal("0")); goal_deposits = sum((item.amount for item in self.repo.goal_deposits()), Decimal("0")); balance = sum((item.amount if item.type == "income" else -item.amount for item in all_items), Decimal("0")) - goal_deposits; by_category = {}
        for item in current_expenses:
            if item.type == "expense":
                category = by_category.setdefault(item.category_id, {"id": item.category_id, "name": item.category.name, "color": item.category.color, "amount": Decimal("0")})
                category["amount"] += item.amount
        for item in current_card_purchases:
            if item.category_id and item.category:
                category = by_category.setdefault(item.category_id, {"id": item.category_id, "name": item.category.name, "color": item.category.color, "amount": Decimal("0")})
                category["amount"] += item.amount
        months = [{"month": f"{year}-{current_month:02d}", "income": money(sum((x.amount for x in all_items if x.date.year == year and x.date.month == current_month and x.type == "income"), Decimal("0"))), "expense": money(sum((x.amount for x in all_items if x.date.year == year and x.date.month == current_month and x.type == "expense" and x.id not in payment_ids and self.is_owner_category(x)), Decimal("0")) + sum((x.amount for x in card_purchases if x.invoice.reference_month == f"{year}-{current_month:02d}" and self.is_owner_category(x)), Decimal("0")))} for current_month in range(1, 13)]
        return {"period": value, "balance": money(balance), "income": money(income), "expense": money(expense), "net_expense": money(net_expense), "card_pending": money(card_pending), "by_category": [{**item, "amount": money(item["amount"])} for item in by_category.values()], "monthly_evolution": months}
    def budgets(self, period):
        value = period or date.today().strftime("%Y-%m"); _, _, start, end = self.bounds(value); result = []; payment_ids = self.repo.payment_transaction_ids(); transactions = self.repo.transactions(); card_purchases = self.repo.card_purchases()
        for category in self.repo.categories():
            spent = sum((item.amount for item in transactions if item.category_id == category.id and item.type == "expense" and item.id not in payment_ids and start <= item.date <= end), Decimal("0")) + sum((item.amount for item in card_purchases if item.category_id == category.id and item.invoice.reference_month == value), Decimal("0")); limit = category.budget_limit
            result.append({"id": category.id, "name": category.name, "color": category.color, "budget_limit": money(limit) if limit is not None else None, "spent": money(spent), "percent": round(float(spent / limit * 100), 2) if limit else None})
        return result
