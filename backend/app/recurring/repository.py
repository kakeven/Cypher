from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .model import RecurringOccurrence, RecurringTransaction


class RecurringRepository:
    def __init__(self, db: Session): self.db = db
    def get(self, item_id): return self.db.get(RecurringTransaction, item_id)
    def list(self): return list(self.db.scalars(select(RecurringTransaction).order_by(RecurringTransaction.is_active.desc(), RecurringTransaction.name)))
    def add(self, item): self.db.add(item); self.db.flush(); return item
    def occurrence(self, item_id): return self.db.get(RecurringOccurrence, item_id)
    def occurrences(self, period=None, transaction_type=None, status=None):
        query = select(RecurringOccurrence).options(selectinload(RecurringOccurrence.recurring)).order_by(RecurringOccurrence.due_date, RecurringOccurrence.id)
        if period:
            year, month = map(int, period.split("-")); query = query.where(RecurringOccurrence.due_date >= date(year, month, 1), RecurringOccurrence.due_date < date(year + (month == 12), month % 12 + 1, 1))
        if transaction_type: query = query.where(RecurringOccurrence.type == transaction_type)
        if status: query = query.where(RecurringOccurrence.status == status)
        return list(self.db.scalars(query))
    def add_occurrence(self, item): self.db.add(item); self.db.flush(); return item
    def pending_for(self, recurring_id): return list(self.db.scalars(select(RecurringOccurrence).where(RecurringOccurrence.recurring_id == recurring_id, RecurringOccurrence.status == "pending")))
