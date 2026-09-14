from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .model import Receivable, ReceivablePayment


class ReceivableRepository:
    def __init__(self, db: Session): self.db = db
    def get(self, item_id: int): return self.db.get(Receivable, item_id)
    def list(self): return list(self.db.scalars(select(Receivable).order_by(Receivable.created_at.desc())))
    def payments(self, receivable_id: int): return list(self.db.scalars(select(ReceivablePayment).where(ReceivablePayment.receivable_id == receivable_id).order_by(ReceivablePayment.received_on.desc(), ReceivablePayment.id.desc())))
    def received_amount(self, receivable_id: int): return self.db.scalar(select(func.coalesce(func.sum(ReceivablePayment.amount), 0)).where(ReceivablePayment.receivable_id == receivable_id))
    def add(self, item): self.db.add(item); self.db.flush(); return item
    def delete(self, item): self.db.delete(item)
