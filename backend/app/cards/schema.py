from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class CreditCardIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    brand: str | None = Field(default=None, max_length=30)
    credit_limit: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    closing_day: int = Field(ge=1, le=31)
    due_day: int = Field(ge=1, le=31)


class CsvImportIn(BaseModel):
    reference_month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    content: str = Field(min_length=1)


class PurchaseCategoryIn(BaseModel):
    category_id: int | None = None


class InvoicePaymentIn(BaseModel):
    paid_on: date

    @field_validator("paid_on")
    @classmethod
    def date_cannot_be_future(cls, value):
        if value > date.today(): raise ValueError("A data do pagamento não pode estar no futuro.")
        return value


class InvoiceInstallmentPaymentIn(InvoicePaymentIn):
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    paid_by_owner: bool
    payer_name: str | None = Field(default=None, max_length=80)
    description: str | None = Field(default=None, max_length=250)
