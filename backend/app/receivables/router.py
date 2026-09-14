from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.errors import DomainError
from .schema import ReceivableIn, ReceivablePaymentIn
from .service import ReceivableService

router = APIRouter(prefix="/receivables", tags=["receivables"])


def call(operation):
    try: return operation()
    except DomainError as error: raise HTTPException(error.status_code, error.detail) from error


@router.get("")
def list_receivables(db: Session = Depends(get_db)): return ReceivableService(db).list()

@router.post("", status_code=201)
def create_receivable(body: ReceivableIn, db: Session = Depends(get_db)): return ReceivableService(db).create(body)

@router.get("/{receivable_id}")
def get_receivable(receivable_id: int, db: Session = Depends(get_db)): return call(lambda: ReceivableService(db).get(receivable_id))

@router.put("/{receivable_id}")
def update_receivable(receivable_id: int, body: ReceivableIn, db: Session = Depends(get_db)): return call(lambda: ReceivableService(db).update(receivable_id, body))

@router.delete("/{receivable_id}", status_code=204)
def delete_receivable(receivable_id: int, db: Session = Depends(get_db)):
    call(lambda: ReceivableService(db).delete(receivable_id))
    return Response(status_code=204)

@router.post("/{receivable_id}/payments", status_code=201)
def create_receivable_payment(receivable_id: int, body: ReceivablePaymentIn, db: Session = Depends(get_db)): return call(lambda: ReceivableService(db).add_payment(receivable_id, body))
