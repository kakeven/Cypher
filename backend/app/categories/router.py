from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.errors import DomainError
from .schema import BudgetIn, CategoryIn
from .service import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])


def call(operation):
    try: return operation()
    except DomainError as error: raise HTTPException(error.status_code, error.detail) from error


@router.get("")
def list_categories(db: Session = Depends(get_db)): return CategoryService(db).list()

@router.post("", status_code=201)
def create_category(body: CategoryIn, db: Session = Depends(get_db)): return call(lambda: CategoryService(db).create(body))

@router.put("/{category_id}")
def update_category(category_id: int, body: CategoryIn, db: Session = Depends(get_db)): return call(lambda: CategoryService(db).update(category_id, body))

@router.put("/{category_id}/budget")
def update_budget(category_id: int, body: BudgetIn, db: Session = Depends(get_db)): return call(lambda: CategoryService(db).update_budget(category_id, body))

@router.delete("/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)): return call(lambda: CategoryService(db).delete(category_id))
