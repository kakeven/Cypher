from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from .model import SaasClient, SaasInvoice, SaasPayment, SaasPlan, SaasProduct, SaasSubscription


class SubscriptionRepository:
    def __init__(self, db: Session): self.db = db
    def add(self, item): self.db.add(item); self.db.flush(); return item
    def get_client(self, item_id): return self.db.get(SaasClient, item_id)
    def get_product(self, item_id): return self.db.get(SaasProduct, item_id)
    def get_plan(self, item_id): return self.db.get(SaasPlan, item_id)
    def get_subscription(self, item_id): return self.db.scalar(select(SaasSubscription).options(joinedload(SaasSubscription.client), joinedload(SaasSubscription.product), joinedload(SaasSubscription.plan)).where(SaasSubscription.id == item_id))
    def get_invoice(self, item_id): return self.db.scalar(select(SaasInvoice).options(joinedload(SaasInvoice.subscription).joinedload(SaasSubscription.client), joinedload(SaasInvoice.subscription).joinedload(SaasSubscription.product)).where(SaasInvoice.id == item_id))
    def get_payment(self, item_id): return self.db.get(SaasPayment, item_id)
    def clients(self): return list(self.db.scalars(select(SaasClient).order_by(SaasClient.name)))
    def products(self): return list(self.db.scalars(select(SaasProduct).order_by(SaasProduct.name)))
    def plans(self): return list(self.db.scalars(select(SaasPlan).options(joinedload(SaasPlan.product)).order_by(SaasPlan.name)))
    def subscriptions(self): return list(self.db.scalars(select(SaasSubscription).options(joinedload(SaasSubscription.client), joinedload(SaasSubscription.product), joinedload(SaasSubscription.plan)).order_by(SaasSubscription.created_at.desc())))
    def invoices(self, status=None, client_id=None, period=None, due_from=None, due_to=None):
        query = select(SaasInvoice).options(joinedload(SaasInvoice.subscription).joinedload(SaasSubscription.client), joinedload(SaasInvoice.subscription).joinedload(SaasSubscription.product)).order_by(SaasInvoice.due_date, SaasInvoice.id)
        if status: query = query.where(SaasInvoice.status == status)
        if client_id: query = query.join(SaasInvoice.subscription).where(SaasSubscription.client_id == client_id)
        if period: query = query.where(SaasInvoice.reference_period == period)
        if due_from: query = query.where(SaasInvoice.due_date >= due_from)
        if due_to: query = query.where(SaasInvoice.due_date <= due_to)
        return list(self.db.scalars(query))
    def payments(self, invoice_id): return list(self.db.scalars(select(SaasPayment).where(SaasPayment.invoice_id == invoice_id).order_by(SaasPayment.paid_at.desc(), SaasPayment.id.desc())))
    def paid_amount(self, invoice_id): return self.db.scalar(select(func.coalesce(func.sum(SaasPayment.amount), 0)).where(SaasPayment.invoice_id == invoice_id))
    def by_period(self, subscription_id, reference_period): return self.db.scalar(select(SaasInvoice).where(SaasInvoice.subscription_id == subscription_id, SaasInvoice.reference_period == reference_period))
