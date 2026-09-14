from calendar import monthrange
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from ..categories.service import CategoryService
from ..core.errors import DomainError
from ..core.money import money
from ..transactions.model import Transaction
from .model import RecurringOccurrence, RecurringTransaction
from .repository import RecurringRepository


class RecurringService:
    def __init__(self, db: Session): self.db, self.repo, self.categories = db, RecurringRepository(db), CategoryService(db)
    def output(self, item):
        return {"id": item.id, "name": item.name, "type": item.type, "amount": money(item.amount), "category_id": item.category_id, "frequency": item.frequency, "interval": item.interval, "day_of_month": item.day_of_month, "day_of_week": item.day_of_week, "start_date": item.start_date.isoformat(), "end_date": item.end_date.isoformat() if item.end_date else None, "is_active": item.is_active, "created_at": item.created_at.isoformat()}
    def occurrence_output(self, item):
        return {"id": item.id, "recurring_id": item.recurring_id, "recurring_name": item.recurring_name, "due_date": item.due_date.isoformat(), "amount": money(item.amount), "type": item.type, "category_id": item.category_id, "status": item.status, "transaction_id": item.transaction_id, "confirmed_at": item.confirmed_at.isoformat() if item.confirmed_at else None}
    def list(self): return [self.output(item) for item in self.repo.list()]
    def create(self, data):
        self.categories.require(data.category_id)
        item = self.repo.add(RecurringTransaction(**data.model_dump()))
        self.db.commit(); self.db.refresh(item); return self.output(item)
    def update(self, item_id, data):
        item = self.repo.get(item_id)
        if not item: raise DomainError(404, "Recorrência não encontrada.")
        self.categories.require(data.category_id)
        for key, value in data.model_dump().items(): setattr(item, key, value)
        self.db.commit(); self.db.refresh(item); return self.output(item)
    def set_active(self, item_id, active):
        item = self.repo.get(item_id)
        if not item: raise DomainError(404, "Recorrência não encontrada.")
        item.is_active = active; self.db.commit(); self.db.refresh(item); return self.output(item)
    def delete(self, item_id):
        item = self.repo.get(item_id)
        if not item: raise DomainError(404, "Recorrência não encontrada.")
        for occurrence in self.repo.pending_for(item.id): self.db.delete(occurrence)
        for occurrence in item.occurrences:
            if occurrence.status != "pending": occurrence.recurring_id = None
        self.db.delete(item); self.db.commit()
    def first_due(self, item, start):
        start = max(start, item.start_date)
        if item.frequency == "daily": return start
        if item.frequency == "weekly": return start + timedelta(days=(item.day_of_week - start.weekday()) % 7)
        if item.frequency == "monthly": return date(start.year, start.month, min(item.day_of_month, monthrange(start.year, start.month)[1])) if start.day <= min(item.day_of_month, monthrange(start.year, start.month)[1]) else self.next_due(item, date(start.year, start.month, 1))
        month, day = item.start_date.month, item.start_date.day
        candidate = date(start.year, month, min(day, monthrange(start.year, month)[1]))
        return candidate if candidate >= start else date(start.year + 1, month, min(day, monthrange(start.year + 1, month)[1]))
    def next_due(self, item, due):
        if item.frequency == "daily": return due + timedelta(days=item.interval)
        if item.frequency == "weekly": return due + timedelta(weeks=item.interval)
        if item.frequency == "monthly":
            index = due.year * 12 + due.month - 1 + item.interval; year, month = divmod(index, 12); month += 1
            return date(year, month, min(item.day_of_month, monthrange(year, month)[1]))
        year = due.year + item.interval; month, day = item.start_date.month, item.start_date.day
        return date(year, month, min(day, monthrange(year, month)[1]))
    def generate(self, item_id, months):
        item = self.repo.get(item_id)
        if not item: raise DomainError(404, "Recorrência não encontrada.")
        if not item.is_active: raise DomainError(422, "Reative a recorrência antes de gerar ocorrências.")
        today = date.today(); month_index = today.year * 12 + today.month - 1 + months; year, month = divmod(month_index, 12); horizon = date(year, month + 1, 1) - timedelta(days=1)
        existing = {occurrence.due_date for occurrence in item.occurrences}; created = []
        due = self.first_due(item, today)
        while due <= horizon and (not item.end_date or due <= item.end_date):
            if due not in existing: created.append(self.repo.add_occurrence(RecurringOccurrence(recurring_id=item.id, recurring_name=item.name, due_date=due, amount=item.amount, type=item.type, category_id=item.category_id)))
            due = self.next_due(item, due)
        self.db.commit()
        return [self.occurrence_output(occurrence) for occurrence in created]
    def occurrences(self, period=None, transaction_type=None, status=None): return [self.occurrence_output(item) for item in self.repo.occurrences(period, transaction_type, status)]
    def summary(self, period):
        items = self.repo.occurrences(period)
        return {"period": period, "income_expected": money(sum((item.amount for item in items if item.type == "income" and item.status == "pending"), 0)), "expense_expected": money(sum((item.amount for item in items if item.type == "expense" and item.status == "pending"), 0)), "income_realized": money(sum((item.amount for item in items if item.type == "income" and item.status == "received"), 0)), "expense_realized": money(sum((item.amount for item in items if item.type == "expense" and item.status == "paid"), 0))}
    def confirm(self, occurrence_id):
        item = self.repo.occurrence(occurrence_id)
        if not item: raise DomainError(404, "Ocorrência não encontrada.")
        if item.status != "pending": raise DomainError(409, "Esta ocorrência já foi confirmada.")
        if item.due_date > date.today(): raise DomainError(422, "Não é possível confirmar uma ocorrência futura.")
        transaction = Transaction(date=item.due_date, type=item.type, amount=item.amount, category_id=item.category_id, description=f"Recorrência: {item.recurring_name}")
        self.db.add(transaction); self.db.flush()
        item.status = "received" if item.type == "income" else "paid"; item.transaction_id = transaction.id; item.confirmed_at = datetime.utcnow()
        self.db.commit(); self.db.refresh(item); return self.occurrence_output(item)
