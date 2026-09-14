from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..categories.model import Category
from ..core.base import Base


class CreditCard(Base):
    __tablename__ = "credit_cards"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    brand: Mapped[str | None] = mapped_column(String(30), nullable=True)
    credit_limit: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    closing_day: Mapped[int] = mapped_column(Integer)
    due_day: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    invoices: Mapped[list[CreditCardInvoice]] = relationship(cascade="all, delete-orphan")


class CreditCardInvoice(Base):
    __tablename__ = "credit_card_invoices"
    __table_args__ = (UniqueConstraint("card_id", "reference_month", name="uq_card_invoice_month"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("credit_cards.id"))
    reference_month: Mapped[str] = mapped_column(String(7))
    status: Mapped[str] = mapped_column(String(10), default="open")
    payment_transaction_id: Mapped[int | None] = mapped_column(ForeignKey("transactions.id"), unique=True, nullable=True)
    paid_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    card: Mapped[CreditCard] = relationship(back_populates="invoices")
    purchases: Mapped[list[CreditCardPurchase]] = relationship(back_populates="invoice", cascade="all, delete-orphan")
    payments: Mapped[list[CreditCardInvoicePayment]] = relationship(back_populates="invoice", cascade="all, delete-orphan")


class CreditCardInvoicePayment(Base):
    __tablename__ = "credit_card_invoice_payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("credit_card_invoices.id"))
    payer_name: Mapped[str] = mapped_column(String(80))
    paid_by_owner: Mapped[bool] = mapped_column(default=False)
    description: Mapped[str | None] = mapped_column(String(250), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    paid_on: Mapped[date] = mapped_column(Date)
    transaction_id: Mapped[int | None] = mapped_column(ForeignKey("transactions.id"), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    invoice: Mapped[CreditCardInvoice] = relationship(back_populates="payments")


class CreditCardPurchase(Base):
    __tablename__ = "credit_card_purchases"
    __table_args__ = (UniqueConstraint("card_id", "fingerprint", name="uq_card_purchase_fingerprint"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("credit_cards.id"))
    invoice_id: Mapped[int] = mapped_column(ForeignKey("credit_card_invoices.id"))
    purchase_date: Mapped[date] = mapped_column(Date, index=True)
    title: Mapped[str] = mapped_column(String(250))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    installment_current: Mapped[int | None] = mapped_column(Integer, nullable=True)
    installment_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fingerprint: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    invoice: Mapped[CreditCardInvoice] = relationship(back_populates="purchases")
    category: Mapped[Category | None] = relationship()
