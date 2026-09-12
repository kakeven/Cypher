from sqlalchemy import select
from sqlalchemy.orm import Session

from .model import Goal, GoalDeposit


class GoalRepository:
    def __init__(self, db: Session): self.db = db
    def get(self, item_id: int): return self.db.get(Goal, item_id)
    def list(self): return list(self.db.scalars(select(Goal).order_by(Goal.created_at.desc())))
    def deposits(self, goal_id: int): return list(self.db.scalars(select(GoalDeposit).where(GoalDeposit.goal_id == goal_id).order_by(GoalDeposit.created_at.desc())))
    def add(self, item): self.db.add(item); self.db.flush(); return item
    def delete(self, item): self.db.delete(item)
