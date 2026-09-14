from decimal import Decimal

from sqlalchemy.orm import Session

from ..categories.service import CategoryService
from ..core.errors import DomainError
from ..core.money import money
from ..transactions.model import Transaction
from ..transactions.repository import TransactionRepository
from .model import Receivable, ReceivablePayment
from .repository import ReceivableRepository


class ReceivableService:
    def __init__(self, db: Session): self.db, self.repo, self.categories = db, ReceivableRepository(db), CategoryService(db)
    def output(self, item, include_payments=False):
        payments = self.repo.payments(item.id); received = sum((payment.amount for payment in payments), Decimal("0")); result = {"id": item.id, "name": item.name, "client": item.client, "total_amount": money(item.total_amount), "received_amount": money(received), "remaining_amount": money(item.total_amount - received), "progress": min(round(float(received / item.total_amount * 100), 2), 100), "is_paid": received >= item.total_amount, "service_type": item.service_type or "Não informado", "created_at": item.created_at.isoformat()}
        if include_payments: result["payments"] = [{"id": p.id, "transaction_id": p.transaction_id, "amount": money(p.amount), "received_on": p.received_on.isoformat(), "note": p.note, "created_at": p.created_at.isoformat()} for p in payments]
        return result
    def require(self, item_id):
        item = self.repo.get(item_id)
        if not item: raise DomainError(404, "Recebível não encontrado.")
        return item
    def list(self): return [self.output(item) for item in self.repo.list()]
    def get(self, item_id): return self.output(self.require(item_id), True)
    def create(self, data):
        category = self.categories.receivable_category(); item = self.repo.add(Receivable(name=data.name.strip(), client=data.client.strip() if data.client else None, total_amount=data.total_amount, service_type=data.service_type, category_id=category.id)); self.db.commit(); self.db.refresh(item); return self.output(item)
    def update(self, item_id, data):
        item = self.require(item_id); received = self.repo.received_amount(item_id)
        if data.total_amount < received: raise DomainError(422, "O valor total não pode ser menor que o já recebido.")
        item.name, item.client, item.total_amount, item.service_type = data.name.strip(), data.client.strip() if data.client else None, data.total_amount, data.service_type
        self.db.commit(); self.db.refresh(item); return self.output(item)
    def delete(self, item_id):
        item = self.require(item_id); transactions = TransactionRepository(self.db)
        for payment in self.repo.payments(item_id):
            transaction = transactions.get(payment.transaction_id)
            if transaction: transactions.delete(transaction)
        self.repo.delete(item); self.db.commit()
    def add_payment(self, item_id, data):
        item = self.require(item_id); received = self.repo.received_amount(item_id)
        if data.amount > item.total_amount - received: raise DomainError(422, "O recebimento não pode ser maior que o valor pendente.")
        description = f"Recebimento de {item.name}" + (f": {data.note.strip()}" if data.note and data.note.strip() else "")
        transaction = TransactionRepository(self.db).add(Transaction(date=data.received_on, type="income", amount=data.amount, category_id=item.category_id, description=description)); payment = self.repo.add(ReceivablePayment(receivable_id=item_id, transaction_id=transaction.id, **data.model_dump())); self.db.commit(); self.db.refresh(payment); return {"id": payment.id, "transaction_id": payment.transaction_id, "amount": money(payment.amount), "received_on": payment.received_on.isoformat(), "note": payment.note, "created_at": payment.created_at.isoformat()}
