from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class TransactionIn(BaseModel):
    date: date
    type: Literal["income", "expense"]
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    category_id: int | None = None
    description: str | None = Field(default=None, max_length=250)

    @field_validator("date")
    @classmethod
    def date_cannot_be_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("A data da transação não pode estar no futuro.")
        return value

    @model_validator(mode="after")
    def expense_requires_category(self):
        if self.type == "expense" and self.category_id is None:
            raise ValueError("Categoria é obrigatória para uma despesa.")
        return self
