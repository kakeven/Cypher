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
    def dashboard(self, period):
        value = period or date.today().strftime("%Y-%m"); year, _, start, end = self.bounds(value); all_items = self.repo.transactions(); current = [item for item in all_items if start <= item.date <= end]
        income = sum((item.amount for item in current if item.type == "income"), Decimal("0")); expense = sum((item.amount for item in current if item.type == "expense"), Decimal("0")); goal_deposits = sum((item.amount for item in self.repo.goal_deposits()), Decimal("0")); balance = sum((item.amount if item.type == "income" else -item.amount for item in all_items), Decimal("0")) - goal_deposits; by_category = {}
        for item in current:
            if item.type == "expense": by_category[item.category.name] = by_category.get(item.category.name, Decimal("0")) + item.amount
        months = [{"month": f"{year}-{current_month:02d}", "income": money(sum((x.amount for x in all_items if x.date.year == year and x.date.month == current_month and x.type == "income"), Decimal("0"))), "expense": money(sum((x.amount for x in all_items if x.date.year == year and x.date.month == current_month and x.type == "expense"), Decimal("0")))} for current_month in range(1, 13)]
        return {"period": value, "balance": money(balance), "income": money(income), "expense": money(expense), "by_category": [{"name": name, "amount": money(amount)} for name, amount in by_category.items()], "monthly_evolution": months}
    def budgets(self, period):
        value = period or date.today().strftime("%Y-%m"); _, _, start, end = self.bounds(value); result = []
        for category in self.repo.categories():
            spent, limit = self.repo.spent_by_category(category.id, start, end), category.budget_limit
            result.append({"id": category.id, "name": category.name, "color": category.color, "budget_limit": money(limit) if limit is not None else None, "spent": money(spent), "percent": round(float(spent / limit * 100), 2) if limit else None})
        return result
