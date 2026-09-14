from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .model import CreditCard, CreditCardInvoice, CreditCardPurchase


class CardRepository:
    def __init__(self, db: Session): self.db = db
    def card(self, item_id): return self.db.get(CreditCard, item_id)
    def cards(self): return list(self.db.scalars(select(CreditCard).order_by(CreditCard.name)))
    def invoice(self, item_id): return self.db.scalar(select(CreditCardInvoice).options(selectinload(CreditCardInvoice.purchases), selectinload(CreditCardInvoice.payments)).where(CreditCardInvoice.id == item_id))
    def invoice_for(self, card_id, reference_month): return self.db.scalar(select(CreditCardInvoice).where(CreditCardInvoice.card_id == card_id, CreditCardInvoice.reference_month == reference_month))
    def purchase(self, item_id): return self.db.get(CreditCardPurchase, item_id)
    def has_fingerprint(self, card_id, fingerprint): return self.db.scalar(select(CreditCardPurchase.id).where(CreditCardPurchase.card_id == card_id, CreditCardPurchase.fingerprint == fingerprint)) is not None
    def add(self, item): self.db.add(item); self.db.flush(); return item
    def delete(self, item): self.db.delete(item)
