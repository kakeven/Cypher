from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.base import Base


class SaasClient(Base):
    __tablename__ = "saas_clients"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    business_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    contact_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    whatsapp: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str | None] = mapped_column(String(120), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SaasProduct(Base):
    __tablename__ = "saas_products"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SaasPlan(Base):
    __tablename__ = "saas_plans"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("saas_products.id"))
    name: Mapped[str] = mapped_column(String(100))
    default_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    billing_cycle: Mapped[str] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(default=True)
    product: Mapped[SaasProduct] = relationship()
    __table_args__ = (UniqueConstraint("product_id", "name", name="uq_saas_plan_product_name"),)


class SaasSubscription(Base):
    __tablename__ = "saas_subscriptions"
    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("saas_clients.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("saas_products.id"))
    plan_id: Mapped[int | None] = mapped_column(ForeignKey("saas_plans.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(150))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    billing_cycle: Mapped[str] = mapped_column(String(20))
    due_day: Mapped[int] = mapped_column()
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    canceled_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    client: Mapped[SaasClient] = relationship()
    product: Mapped[SaasProduct] = relationship()
    plan: Mapped[SaasPlan | None] = relationship()
    invoices: Mapped[list[SaasInvoice]] = relationship(back_populates="subscription", cascade="all, delete-orphan")


class SaasInvoice(Base):
    __tablename__ = "saas_invoices"
    id: Mapped[int] = mapped_column(primary_key=True)
    subscription_id: Mapped[int] = mapped_column(ForeignKey("saas_subscriptions.id"))
    reference_period: Mapped[str] = mapped_column(String(7))
    due_date: Mapped[date] = mapped_column(Date)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    subscription: Mapped[SaasSubscription] = relationship(back_populates="invoices")
    payments: Mapped[list[SaasPayment]] = relationship(cascade="all, delete-orphan")
    __table_args__ = (UniqueConstraint("subscription_id", "reference_period", name="uq_saas_invoice_period"),)


class SaasPayment(Base):
    __tablename__ = "saas_payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("saas_invoices.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    paid_at: Mapped[date] = mapped_column(Date)
    payment_method: Mapped[str] = mapped_column(String(20))
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id"), unique=True)
    note: Mapped[str | None] = mapped_column(String(250), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
