from sqlalchemy.orm import Session

from ..cards.model import CreditCardPurchase
from ..core.errors import DomainError
from ..core.money import money
from ..transactions.model import Transaction
from .model import Category
from .repository import CategoryRepository

DEFAULT_CATEGORIES = [("Moradia", "#8B5CF6"), ("Alimentação", "#F59E0B"), ("Transporte", "#3B82F6"), ("Lazer", "#EC4899"), ("Saúde", "#10B981"), ("Educação", "#06B6D4"), ("Outros", "#6B7280")]


class CategoryService:
    def __init__(self, db: Session): self.db, self.repo = db, CategoryRepository(db)
    def output(self, item): return {"id": item.id, "name": item.name, "color": item.color, "budget_limit": money(item.budget_limit) if item.budget_limit is not None else None, "is_active": item.is_active}
    def list(self): return [self.output(item) for item in self.repo.list()]
    def require(self, item_id):
        item = self.repo.get(item_id)
        if not item or not item.is_active: raise DomainError(404, "Categoria não encontrada.")
        return item
    def create(self, data):
        name = data.name.strip()
        if self.repo.by_name(name): raise DomainError(409, "Já existe uma categoria com esse nome.")
        item = self.repo.add(Category(name=name, color=data.color)); self.db.commit(); self.db.refresh(item); return self.output(item)
    def update(self, item_id, data):
        item = self.require(item_id); name = data.name.strip(); existing = self.repo.by_name(name)
        if existing and existing.id != item.id: raise DomainError(409, "Já existe uma categoria com esse nome.")
        item.name, item.color = name, data.color; self.db.commit(); self.db.refresh(item); return self.output(item)
    def update_budget(self, item_id, data):
        item = self.require(item_id); item.budget_limit = data.budget_limit; self.db.commit(); self.db.refresh(item); return self.output(item)
    def delete(self, item_id):
        item = self.require(item_id)
        has_history = self.db.query(Transaction.id).filter(Transaction.category_id == item.id).first() is not None or self.db.query(CreditCardPurchase.id).filter(CreditCardPurchase.category_id == item.id).first() is not None
        if has_history:
            item.is_active = False
            item.budget_limit = None
            self.db.commit()
            return {"archived": True, "message": "Categoria arquivada; o histórico foi preservado."}
        self.db.delete(item)
        self.db.commit()
        return {"archived": False, "message": "Categoria excluída."}
    def ensure_defaults(self):
        if not self.repo.has_any():
            for name, color in DEFAULT_CATEGORIES: self.repo.add(Category(name=name, color=color))
            self.db.commit()
    def receivable_category(self):
        item = self.repo.by_name("Outros")
        if not item: item = self.repo.add(Category(name="Outros", color="#6B7280"))
        item.is_active = True
        return item
    def credit_card_category(self):
        item = self.repo.by_name("Cartão de crédito")
        if not item: item = self.repo.add(Category(name="Cartão de crédito", color="#8B5CF6"))
        item.is_active = True
        return item
    def subscription_category(self):
        item = self.repo.by_name("Assinaturas SaaS")
        if not item: item = self.repo.add(Category(name="Assinaturas SaaS", color="#A855F7"))
        item.is_active = True
        return item
