from decimal import Decimal

from pydantic import BaseModel, Field


class CategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    color: str = Field(default="#6D8BFF", pattern=r"^#[0-9A-Fa-f]{6}$")


class BudgetIn(BaseModel):
    budget_limit: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
