from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .model import Transaction


class TransactionRepository:
    def __init__(self, db: Session): self.db = db
    def get(self, item_id: int): return self.db.get(Transaction, item_id)
    def list(self, date_from=None, date_to=None, category_id=None, transaction_type=None):
        query = select(Transaction).order_by(Transaction.date.desc(), Transaction.id.desc())
        if date_from: query = query.where(Transaction.date >= date_from)
        if date_to: query = query.where(Transaction.date <= date_to)
        if category_id: query = query.where(Transaction.category_id == category_id)
        if transaction_type: query = query.where(Transaction.type == transaction_type)
        return list(self.db.scalars(query))
    def add(self, item: Transaction): self.db.add(item); self.db.flush(); return item
    def delete(self, item: Transaction): self.db.delete(item)
    def spent_by_category(self, category_id: int, start: date, end: date):
        return self.db.scalar(select(func.coalesce(func.sum(Transaction.amount), 0)).where(Transaction.category_id == category_id, Transaction.type == "expense", Transaction.date >= start, Transaction.date <= end))
