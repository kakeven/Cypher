from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class RecurringTransactionIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: Literal["income", "expense"]
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    category_id: int
    frequency: Literal["daily", "weekly", "monthly", "yearly"]
    interval: int = Field(default=1, ge=1, le=365)
    day_of_month: int | None = Field(default=None, ge=1, le=31)
    day_of_week: int | None = Field(default=None, ge=0, le=6)
    start_date: date
    end_date: date | None = None

    @model_validator(mode="after")
    def validate_schedule(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("A data final não pode ser anterior à data inicial.")
        if self.frequency == "weekly" and self.day_of_week is None:
            raise ValueError("Informe o dia da semana para uma recorrência semanal.")
        if self.frequency == "monthly" and self.day_of_month is None:
            raise ValueError("Informe o dia do mês para uma recorrência mensal.")
        return self
