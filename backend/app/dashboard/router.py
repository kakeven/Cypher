from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..core.database import get_db
from .service import DashboardService

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
def dashboard(period: str | None = Query(default=None, pattern=r"^\d{4}-(0[1-9]|1[0-2])$"), db: Session = Depends(get_db)): return DashboardService(db).dashboard(period)

@router.get("/budgets")
def budgets(period: str | None = Query(default=None, pattern=r"^\d{4}-(0[1-9]|1[0-2])$"), db: Session = Depends(get_db)): return DashboardService(db).budgets(period)
