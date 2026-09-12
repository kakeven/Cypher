from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ReceivableIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    client: str | None = Field(default=None, max_length=100)
    total_amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    service_type: Literal["Site institucional", "Sistema", "E-commerce", "Landing page"]


class ReceivablePaymentIn(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    received_on: date
    note: str | None = Field(default=None, max_length=250)

    @field_validator("received_on")
    @classmethod
    def date_cannot_be_future(cls, value: date) -> date:
        if value > date.today(): raise ValueError("A data do recebimento não pode estar no futuro.")
        return value
