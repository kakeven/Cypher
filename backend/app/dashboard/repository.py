from datetime import date

from sqlalchemy.orm import Session

from ..categories.repository import CategoryRepository
from ..transactions.repository import TransactionRepository


class DashboardRepository:
    def __init__(self, db: Session):
        self._categories = CategoryRepository(db)
        self._transactions = TransactionRepository(db)
    def transactions(self): return self._transactions.list()
    def categories(self): return self._categories.list()
    def spent_by_category(self, category_id: int, start: date, end: date): return self._transactions.spent_by_category(category_id, start, end)
