from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..categories.model import Category
from ..core.errors import DomainError
from ..core.money import money
from ..transactions.model import Transaction
from ..transactions.repository import TransactionRepository
from .invoice_generation import CYCLE_MONTHS, invoice_dates
from .model import SaasClient, SaasInvoice, SaasPayment, SaasPlan, SaasProduct, SaasSubscription
from .repository import SubscriptionRepository


class SubscriptionService:
    def __init__(self, db: Session): self.db, self.repo = db, SubscriptionRepository(db)
    def clean(self, value): return value.strip() if value and value.strip() else None
    def require(self, value, label):
        if not value: raise DomainError(404, f"{label} não encontrado.")
        return value
    def client_output(self, item): return {"id": item.id, "name": item.name, "business_name": item.business_name, "contact_name": item.contact_name, "whatsapp": item.whatsapp, "email": item.email, "notes": item.notes, "is_active": item.is_active, "created_at": item.created_at.isoformat()}
    def product_output(self, item): return {"id": item.id, "name": item.name, "description": item.description, "is_active": item.is_active, "created_at": item.created_at.isoformat()}
    def plan_output(self, item): return {"id": item.id, "product_id": item.product_id, "product_name": item.product.name, "name": item.name, "default_amount": money(item.default_amount), "billing_cycle": item.billing_cycle, "is_active": item.is_active}
    def payment_output(self, item): return {"id": item.id, "invoice_id": item.invoice_id, "amount": money(item.amount), "paid_at": item.paid_at.isoformat(), "payment_method": item.payment_method, "transaction_id": item.transaction_id, "note": item.note, "created_at": item.created_at.isoformat()}
    def refresh_invoice_status(self, item):
        paid = self.repo.paid_amount(item.id)
        item.status = "paid" if paid >= item.amount else "partial" if paid else "overdue" if item.due_date < date.today() else "pending"
        return paid
    def invoice_output(self, item, payments=False):
        paid = self.refresh_invoice_status(item); result = {"id": item.id, "subscription_id": item.subscription_id, "reference_period": item.reference_period, "due_date": item.due_date.isoformat(), "amount": money(item.amount), "paid_amount": money(paid), "remaining_amount": money(item.amount - paid), "status": item.status, "client_name": item.subscription.client.name, "product_name": item.subscription.product.name, "subscription_name": item.subscription.name, "created_at": item.created_at.isoformat()}
        if payments: result["payments"] = [self.payment_output(p) for p in self.repo.payments(item.id)]
        return result
    def subscription_output(self, item, detail=False):
        invoices = self.repo.invoices() if False else []
        next_invoice = self.db.scalar(select(SaasInvoice).where(SaasInvoice.subscription_id == item.id, SaasInvoice.status.in_(("pending", "partial", "overdue"))).order_by(SaasInvoice.due_date))
        result = {"id": item.id, "client_id": item.client_id, "client_name": item.client.name, "product_id": item.product_id, "product_name": item.product.name, "plan_id": item.plan_id, "plan_name": item.plan.name if item.plan else None, "name": item.name, "amount": money(item.amount), "billing_cycle": item.billing_cycle, "due_day": item.due_day, "start_date": item.start_date.isoformat(), "end_date": item.end_date.isoformat() if item.end_date else None, "status": item.status, "canceled_at": item.canceled_at.isoformat() if item.canceled_at else None, "notes": item.notes, "next_due_date": next_invoice.due_date.isoformat() if next_invoice else None, "created_at": item.created_at.isoformat()}
        if detail:
            result["invoices"] = [self.invoice_output(invoice, True) for invoice in self.repo.invoices() if invoice.subscription_id == item.id]
        return result
    def list_clients(self): return [self.client_output(x) for x in self.repo.clients()]
    def create_client(self, data):
        item = self.repo.add(SaasClient(**{key: self.clean(value) if isinstance(value, str) else value for key, value in data.model_dump().items()})); self.db.commit(); self.db.refresh(item); return self.client_output(item)
    def update_client(self, item_id, data):
        item = self.require(self.repo.get_client(item_id), "Cliente")
        for key, value in data.model_dump().items(): setattr(item, key, self.clean(value) if isinstance(value, str) else value)
        self.db.commit(); self.db.refresh(item); return self.client_output(item)
    def list_products(self): return [self.product_output(x) for x in self.repo.products()]
    def create_product(self, data):
        if any(x.name.lower() == data.name.strip().lower() for x in self.repo.products()): raise DomainError(409, "Já existe um produto com esse nome.")
        item = self.repo.add(SaasProduct(name=data.name.strip(), description=self.clean(data.description), is_active=data.is_active)); self.db.commit(); self.db.refresh(item); return self.product_output(item)
    def update_product(self, item_id, data):
        item = self.require(self.repo.get_product(item_id), "Produto")
        if any(x.id != item.id and x.name.lower() == data.name.strip().lower() for x in self.repo.products()): raise DomainError(409, "Já existe um produto com esse nome.")
        item.name, item.description, item.is_active = data.name.strip(), self.clean(data.description), data.is_active; self.db.commit(); self.db.refresh(item); return self.product_output(item)
    def list_plans(self): return [self.plan_output(x) for x in self.repo.plans()]
    def create_plan(self, data):
        self.require(self.repo.get_product(data.product_id), "Produto")
        if any(x.product_id == data.product_id and x.name.lower() == data.name.strip().lower() for x in self.repo.plans()): raise DomainError(409, "Já existe um plano com esse nome para o produto.")
        item = self.repo.add(SaasPlan(**data.model_dump(exclude={"name"}), name=data.name.strip())); self.db.commit(); self.db.refresh(item); return self.plan_output(item)
    def update_plan(self, item_id, data):
        item = self.require(self.repo.get_plan(item_id), "Plano"); self.require(self.repo.get_product(data.product_id), "Produto")
        if any(x.id != item.id and x.product_id == data.product_id and x.name.lower() == data.name.strip().lower() for x in self.repo.plans()): raise DomainError(409, "Já existe um plano com esse nome para o produto.")
        for key, value in data.model_dump().items(): setattr(item, key, data.name.strip() if key == "name" else value)
        self.db.commit(); self.db.refresh(item); return self.plan_output(item)
    def validate_subscription(self, data):
        client = self.require(self.repo.get_client(data.client_id), "Cliente")
        product = self.require(self.repo.get_product(data.product_id), "Produto")
        if not client.is_active: raise DomainError(422, "Não é possível usar um cliente arquivado.")
        if not product.is_active: raise DomainError(422, "Não é possível usar um produto arquivado.")
        if data.plan_id:
            plan = self.require(self.repo.get_plan(data.plan_id), "Plano")
            if plan.product_id != data.product_id: raise DomainError(422, "O plano deve pertencer ao produto selecionado.")
        return data.model_dump()
    def list_subscriptions(self):
        self.generate_invoices(date.today() + timedelta(days=90), commit=False); self.db.commit()
        return [self.subscription_output(x) for x in self.repo.subscriptions()]
    def create_subscription(self, data):
        values = self.validate_subscription(data); values["name"], values["notes"] = data.name.strip(), self.clean(data.notes)
        item = self.repo.add(SaasSubscription(**values)); self.db.commit(); self.db.refresh(item); return self.subscription_output(self.repo.get_subscription(item.id))
    def get_subscription(self, item_id):
        self.generate_invoices(date.today() + timedelta(days=90), commit=False); self.db.commit()
        return self.subscription_output(self.require(self.repo.get_subscription(item_id), "Assinatura"), True)
    def update_subscription(self, item_id, data):
        item = self.require(self.repo.get_subscription(item_id), "Assinatura")
        if item.status in ("canceled", "ended"): raise DomainError(422, "Não é possível editar uma assinatura cancelada ou encerrada.")
        values = self.validate_subscription(data)
        for key, value in values.items(): setattr(item, key, data.name.strip() if key == "name" else self.clean(value) if key == "notes" else value)
        self.db.commit(); return self.subscription_output(self.repo.get_subscription(item_id))
    def transition(self, item_id, action, canceled_at=None):
        item = self.require(self.repo.get_subscription(item_id), "Assinatura")
        if action == "pause":
            if item.status != "active": raise DomainError(422, "Apenas assinaturas ativas podem ser pausadas.")
            item.status = "paused"
        elif action == "resume":
            if item.status != "paused": raise DomainError(422, "Apenas assinaturas pausadas podem ser reativadas.")
            item.status = "active"
        else:
            if item.status in ("canceled", "ended"): raise DomainError(422, "A assinatura já está encerrada.")
            item.status, item.canceled_at, item.end_date = "canceled", canceled_at, canceled_at
        self.db.commit(); return self.subscription_output(self.repo.get_subscription(item_id))
    def generate_invoices(self, end_date, commit=True):
        end_date = end_date or date.today() + timedelta(days=365)
        created = []
        for subscription in self.repo.subscriptions():
            if subscription.status != "active": continue
            limit = min(end_date, subscription.end_date) if subscription.end_date else end_date
            for due_date in invoice_dates(subscription.start_date, subscription.due_day, subscription.billing_cycle, limit):
                reference = due_date.strftime("%Y-%m")
                if not self.repo.by_period(subscription.id, reference): created.append(self.repo.add(SaasInvoice(subscription_id=subscription.id, reference_period=reference, due_date=due_date, amount=subscription.amount)))
        if commit: self.db.commit()
        return [self.invoice_output(item) for item in created]
    def list_invoices(self, **filters):
        self.generate_invoices(date.today() + timedelta(days=90), commit=False)
        items = self.repo.invoices(**filters)
        result = [self.invoice_output(x, True) for x in items]; self.db.commit(); return result
    def subscription_category(self):
        item = self.db.scalar(select(Category).where(func.lower(Category.name) == "assinaturas saas"))
        if not item: item = self.repo.add(Category(name="Assinaturas SaaS", color="#A855F7"))
        item.is_active = True
        return item
    def add_payment(self, invoice_id, data):
        invoice = self.require(self.repo.get_invoice(invoice_id), "Cobrança")
        self.refresh_invoice_status(invoice)
        if invoice.status == "paid": raise DomainError(422, "Esta cobrança já está totalmente paga.")
        paid = self.repo.paid_amount(invoice.id)
        if data.amount > invoice.amount - paid: raise DomainError(422, "O recebimento não pode ser maior que o valor pendente.")
        category = self.subscription_category(); subscription = invoice.subscription
        description = f"Assinatura SaaS: {subscription.client.name} · {subscription.product.name} · {invoice.reference_period}"
        try:
            transaction = self.repo.add(Transaction(date=data.paid_at, type="income", amount=data.amount, category_id=category.id, description=description))
            payment = self.repo.add(SaasPayment(invoice_id=invoice.id, transaction_id=transaction.id, **data.model_dump()))
            self.refresh_invoice_status(invoice); self.db.commit(); self.db.refresh(payment); return self.payment_output(payment)
        except Exception:
            self.db.rollback(); raise
    def delete_payment(self, payment_id):
        payment = self.require(self.repo.get_payment(payment_id), "Pagamento")
        invoice_id, transaction_id = payment.invoice_id, payment.transaction_id
        transaction = TransactionRepository(self.db).get(transaction_id)
        self.db.delete(payment)
        if transaction: self.db.delete(transaction)
        self.db.flush(); invoice = self.repo.get_invoice(invoice_id); self.refresh_invoice_status(invoice); self.db.commit()
    def dashboard(self, period):
        self.generate_invoices(date.today() + timedelta(days=90), commit=False)
        subscriptions = self.repo.subscriptions(); invoices = self.repo.invoices(period=period)
        for invoice in invoices: self.refresh_invoice_status(invoice)
        mrr = sum((x.amount / CYCLE_MONTHS[x.billing_cycle] for x in subscriptions if x.status == "active"), Decimal("0"))
        received = self.db.scalar(select(func.coalesce(func.sum(SaasPayment.amount), 0)).where(SaasPayment.paid_at >= date.fromisoformat(period + "-01"), SaasPayment.paid_at < (date.fromisoformat(period + "-01").replace(day=28) + timedelta(days=4)).replace(day=1)))
        overdue = sum((invoice.amount - self.repo.paid_amount(invoice.id) for invoice in self.repo.invoices(status="overdue")), Decimal("0"))
        self.db.commit()
        return {"period": period, "mrr": money(mrr), "received": money(received), "expected": money(sum((x.amount for x in invoices), Decimal("0"))), "overdue": money(overdue), "active_subscriptions": sum(x.status == "active" for x in subscriptions), "active_clients": len({x.client_id for x in subscriptions if x.status == "active"}), "cancellations": sum(x.status == "canceled" and x.canceled_at and x.canceled_at.strftime("%Y-%m") == period for x in subscriptions), "upcoming_invoices": [self.invoice_output(x) for x in self.repo.invoices(due_from=date.today(), due_to=date.today() + timedelta(days=30)) if x.status in ("pending", "partial")], "overdue_invoices": [self.invoice_output(x) for x in self.repo.invoices(status="overdue")]}
