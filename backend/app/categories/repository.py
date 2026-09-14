from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .model import Category


class CategoryRepository:
    def __init__(self, db: Session): self.db = db
    def list(self): return list(self.db.scalars(select(Category).where(Category.is_active.is_(True)).order_by(Category.name)))
    def get(self, item_id: int): return self.db.get(Category, item_id)
    def by_name(self, name: str): return self.db.scalar(select(Category).where(func.lower(Category.name) == name.lower()))
    def has_any(self): return self.db.scalar(select(Category.id).limit(1)) is not None
    def add(self, item: Category): self.db.add(item); self.db.flush(); return item
