from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.base import Base


class Receivable(Base):
    __tablename__ = "receivables"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    client: Mapped[str | None] = mapped_column(String(100), nullable=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    service_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    payments: Mapped[list[ReceivablePayment]] = relationship(cascade="all, delete-orphan")


class ReceivablePayment(Base):
    __tablename__ = "receivable_payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    receivable_id: Mapped[int] = mapped_column(ForeignKey("receivables.id"))
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id"), unique=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    received_on: Mapped[date] = mapped_column(Date)
    note: Mapped[str | None] = mapped_column(String(250), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
