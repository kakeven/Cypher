from decimal import Decimal

from sqlalchemy.orm import Session

from ..core.errors import DomainError
from ..core.money import money
from .model import Goal, GoalDeposit
from .repository import GoalRepository


class GoalService:
    def __init__(self, db: Session): self.db, self.repo = db, GoalRepository(db)
    def output(self, goal, include_deposits=False):
        deposits = self.repo.deposits(goal.id); saved = sum((item.amount for item in deposits), Decimal("0")); result = {"id": goal.id, "name": goal.name, "target_amount": money(goal.target_amount), "saved_amount": money(saved), "progress": min(round(float(saved / goal.target_amount * 100), 2), 100), "is_completed": saved >= goal.target_amount, "deadline": goal.deadline.isoformat() if goal.deadline else None, "description": goal.description, "created_at": goal.created_at.isoformat()}
        if include_deposits: result["deposits"] = [{"id": item.id, "amount": money(item.amount), "reference_month": item.reference_month, "note": item.note, "created_at": item.created_at.isoformat()} for item in deposits]
        return result
    def require(self, item_id):
        item = self.repo.get(item_id)
        if not item: raise DomainError(404, "Meta não encontrada.")
        return item
    def list(self): return [self.output(item) for item in self.repo.list()]
    def get(self, item_id): return self.output(self.require(item_id), True)
    def create(self, data): item = self.repo.add(Goal(**data.model_dump())); self.db.commit(); self.db.refresh(item); return self.output(item)
    def update(self, item_id, data):
        item = self.require(item_id)
        for key, value in data.model_dump().items(): setattr(item, key, value)
        self.db.commit(); self.db.refresh(item); return self.output(item)
    def delete(self, item_id): self.repo.delete(self.require(item_id)); self.db.commit()
    def add_deposit(self, item_id, data):
        self.require(item_id); item = self.repo.add(GoalDeposit(goal_id=item_id, **data.model_dump())); self.db.commit(); self.db.refresh(item); return {"id": item.id, "amount": money(item.amount), "reference_month": item.reference_month, "note": item.note, "created_at": item.created_at.isoformat()}
