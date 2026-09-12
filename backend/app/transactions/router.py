from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.errors import DomainError
from .schema import TransactionIn
from .service import TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])


def call(operation):
    try: return operation()
    except DomainError as error: raise HTTPException(error.status_code, error.detail) from error


@router.get("")
def list_transactions(date_from: date | None = None, date_to: date | None = None, category_id: int | None = None, type: Literal["income", "expense"] | None = None, db: Session = Depends(get_db)):
    return TransactionService(db).list(date_from=date_from, date_to=date_to, category_id=category_id, transaction_type=type)

@router.post("", status_code=201)
def create_transaction(body: TransactionIn, db: Session = Depends(get_db)): return call(lambda: TransactionService(db).create(body))

@router.put("/{transaction_id}")
def update_transaction(transaction_id: int, body: TransactionIn, db: Session = Depends(get_db)): return call(lambda: TransactionService(db).update(transaction_id, body))

@router.delete("/{transaction_id}", status_code=204)
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    call(lambda: TransactionService(db).delete(transaction_id))
    return Response(status_code=204)
