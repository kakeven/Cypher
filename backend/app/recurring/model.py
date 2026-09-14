from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.base import Base


class RecurringTransaction(Base):
    __tablename__ = "recurring_transactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    type: Mapped[str] = mapped_column(String(10))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    frequency: Mapped[str] = mapped_column(String(10))
    interval: Mapped[int] = mapped_column(Integer, default=1)
    day_of_month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    day_of_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    occurrences: Mapped[list[RecurringOccurrence]] = relationship(back_populates="recurring")


class RecurringOccurrence(Base):
    __tablename__ = "recurring_occurrences"
    __table_args__ = (UniqueConstraint("recurring_id", "due_date", name="uq_recurring_occurrence_date"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    recurring_id: Mapped[int | None] = mapped_column(ForeignKey("recurring_transactions.id"), nullable=True)
    recurring_name: Mapped[str] = mapped_column(String(100))
    due_date: Mapped[date] = mapped_column(Date, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    type: Mapped[str] = mapped_column(String(10))
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    status: Mapped[str] = mapped_column(String(12), default="pending")
    transaction_id: Mapped[int | None] = mapped_column(ForeignKey("transactions.id"), unique=True, nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    recurring: Mapped[RecurringTransaction | None] = relationship(back_populates="occurrences")
