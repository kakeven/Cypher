from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.errors import DomainError
from .schema import RecurringTransactionIn
from .service import RecurringService

router = APIRouter(tags=["recurring"])


def call(operation):
    try: return operation()
    except DomainError as error: raise HTTPException(error.status_code, error.detail) from error


@router.get("/recurring-transactions")
def list_recurring(db: Session = Depends(get_db)): return RecurringService(db).list()

@router.post("/recurring-transactions", status_code=201)
def create_recurring(body: RecurringTransactionIn, db: Session = Depends(get_db)): return call(lambda: RecurringService(db).create(body))

@router.put("/recurring-transactions/{recurring_id}")
def update_recurring(recurring_id: int, body: RecurringTransactionIn, db: Session = Depends(get_db)): return call(lambda: RecurringService(db).update(recurring_id, body))

@router.post("/recurring-transactions/{recurring_id}/pause")
def pause_recurring(recurring_id: int, db: Session = Depends(get_db)): return call(lambda: RecurringService(db).set_active(recurring_id, False))

@router.post("/recurring-transactions/{recurring_id}/resume")
def resume_recurring(recurring_id: int, db: Session = Depends(get_db)): return call(lambda: RecurringService(db).set_active(recurring_id, True))

@router.post("/recurring-transactions/{recurring_id}/generate-occurrences")
def generate_occurrences(recurring_id: int, horizon_months: int = Query(default=12, ge=1, le=24), db: Session = Depends(get_db)): return call(lambda: RecurringService(db).generate(recurring_id, horizon_months))

@router.delete("/recurring-transactions/{recurring_id}", status_code=204)
def delete_recurring(recurring_id: int, db: Session = Depends(get_db)):
    call(lambda: RecurringService(db).delete(recurring_id)); return Response(status_code=204)

@router.get("/occurrences")
def list_occurrences(period: str | None = None, type: Literal["income", "expense"] | None = None, status: Literal["pending", "received", "paid"] | None = None, db: Session = Depends(get_db)):
    return RecurringService(db).occurrences(period, type, status)

@router.get("/occurrences/summary")
def occurrence_summary(period: str, db: Session = Depends(get_db)):
    try: date.fromisoformat(f"{period}-01")
    except ValueError: raise HTTPException(422, "Período inválido. Use YYYY-MM.")
    return RecurringService(db).summary(period)

@router.post("/occurrences/{occurrence_id}/confirm")
def confirm_occurrence(occurrence_id: int, db: Session = Depends(get_db)): return call(lambda: RecurringService(db).confirm(occurrence_id))
