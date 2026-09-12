from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class TransactionIn(BaseModel):
    date: date
    type: Literal["income", "expense"]
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    category_id: int
    description: str | None = Field(default=None, max_length=250)

    @field_validator("date")
    @classmethod
    def date_cannot_be_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("A data da transação não pode estar no futuro.")
        return value
