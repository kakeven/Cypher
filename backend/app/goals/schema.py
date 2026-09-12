from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class GoalIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    target_amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    deadline: date | None = None
    description: str | None = Field(default=None, max_length=250)


class DepositIn(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    reference_month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    note: str | None = Field(default=None, max_length=250)
