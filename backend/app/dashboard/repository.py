from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..cards.model import CreditCardInvoice, CreditCardInvoicePayment, CreditCardPurchase
from ..categories.repository import CategoryRepository
from ..goals.model import GoalDeposit
from ..transactions.repository import TransactionRepository


class DashboardRepository:
    def __init__(self, db: Session):
        self.db = db
        self._categories = CategoryRepository(db)
        self._transactions = TransactionRepository(db)
    def transactions(self): return self._transactions.list()
    def goal_deposits(self): return list(self.db.scalars(select(GoalDeposit)))
    def categories(self): return self._categories.list()
    def card_purchases(self): return list(self.db.scalars(select(CreditCardPurchase).options(selectinload(CreditCardPurchase.category), selectinload(CreditCardPurchase.invoice))))
    def card_invoices(self): return list(self.db.scalars(select(CreditCardInvoice).options(selectinload(CreditCardInvoice.purchases), selectinload(CreditCardInvoice.payments))))
    def card_payments(self): return list(self.db.scalars(select(CreditCardInvoicePayment).options(selectinload(CreditCardInvoicePayment.invoice))))
    def payment_transaction_ids(self):
        legacy_ids = set(self.db.scalars(select(CreditCardInvoice.payment_transaction_id).where(CreditCardInvoice.payment_transaction_id.is_not(None))))
        payment_ids = set(self.db.scalars(select(CreditCardInvoicePayment.transaction_id).where(CreditCardInvoicePayment.transaction_id.is_not(None))))
        return legacy_ids | payment_ids
