from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

Cycle = Literal["monthly", "quarterly", "semiannual", "yearly"]
Method = Literal["pix", "cash", "card", "transfer", "other"]


class ClientIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    business_name: str | None = Field(default=None, max_length=120)
    contact_name: str | None = Field(default=None, max_length=100)
    whatsapp: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=500)
    is_active: bool = True


class ProductIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    is_active: bool = True


class PlanIn(BaseModel):
    product_id: int
    name: str = Field(min_length=1, max_length=100)
    default_amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    billing_cycle: Cycle
    is_active: bool = True


class SubscriptionIn(BaseModel):
    client_id: int
    product_id: int
    plan_id: int | None = None
    name: str = Field(min_length=1, max_length=150)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    billing_cycle: Cycle
    due_day: int = Field(ge=1, le=28)
    start_date: date
    end_date: date | None = None
    notes: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def valid_dates(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("A data de término não pode ser anterior ao início.")
        return self


class CancelIn(BaseModel):
    canceled_at: date = Field(default_factory=date.today)


class InvoiceGenerationIn(BaseModel):
    end_date: date | None = None


class PaymentIn(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    paid_at: date
    payment_method: Method
    note: str | None = Field(default=None, max_length=250)

    @field_validator("paid_at")
    @classmethod
    def not_future(cls, value):
        if value > date.today(): raise ValueError("A data do recebimento não pode estar no futuro.")
        return value
