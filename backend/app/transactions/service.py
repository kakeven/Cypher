from sqlalchemy.orm import Session

from ..categories.service import CategoryService
from ..core.errors import DomainError
from ..core.money import money
from .model import Transaction
from .repository import TransactionRepository


class TransactionService:
    def __init__(self, db: Session): self.db, self.repo, self.categories = db, TransactionRepository(db), CategoryService(db)
    def output(self, item): return {"id": item.id, "date": item.date.isoformat(), "type": item.type, "amount": money(item.amount), "category_id": item.category_id, "category_name": item.category.name, "description": item.description, "created_at": item.created_at.isoformat()}
    def list(self, **filters): return [self.output(item) for item in self.repo.list(**filters)]
    def create(self, data):
        values = data.model_dump()
        values["category_id"] = self.categories.receivable_category().id if data.type == "income" else self.categories.require(data.category_id).id
        item = self.repo.add(Transaction(**values)); self.db.commit(); self.db.refresh(item); return self.output(item)
    def update(self, item_id, data):
        item = self.repo.get(item_id)
        if not item: raise DomainError(404, "Transação não encontrada.")
        values = data.model_dump()
        values["category_id"] = self.categories.receivable_category().id if data.type == "income" else self.categories.require(data.category_id).id
        for key, value in values.items(): setattr(item, key, value)
        self.db.commit(); self.db.refresh(item); return self.output(item)
    def delete(self, item_id):
        item = self.repo.get(item_id)
        if not item: raise DomainError(404, "Transação não encontrada.")
        self.repo.delete(item); self.db.commit()
