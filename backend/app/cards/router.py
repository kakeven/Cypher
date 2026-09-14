from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.errors import DomainError
from .schema import CreditCardIn, CsvImportIn, InvoiceInstallmentPaymentIn, InvoicePaymentIn, PurchaseCategoryIn
from .service import CardService

router = APIRouter(prefix="/credit-cards", tags=["credit-cards"])


def call(operation):
    try: return operation()
    except DomainError as error: raise HTTPException(error.status_code, error.detail) from error


@router.get("")
def list_cards(db: Session = Depends(get_db)): return CardService(db).list()

@router.post("", status_code=201)
def create_card(body: CreditCardIn, db: Session = Depends(get_db)): return call(lambda: CardService(db).create(body))

@router.get("/{card_id}")
def card_detail(card_id: int, db: Session = Depends(get_db)): return call(lambda: CardService(db).detail(card_id))

@router.post("/{card_id}/import-csv")
def import_csv(card_id: int, body: CsvImportIn, db: Session = Depends(get_db)): return call(lambda: CardService(db).import_csv(card_id, body))

@router.get("/invoices/{invoice_id}")
def invoice_detail(invoice_id: int, db: Session = Depends(get_db)): return call(lambda: CardService(db).invoice_detail(invoice_id))

@router.delete("/invoices/{invoice_id}", status_code=204)
def delete_invoice(invoice_id: int, db: Session = Depends(get_db)): call(lambda: CardService(db).delete_invoice(invoice_id))

@router.post("/invoices/{invoice_id}/payments")
def add_payment(invoice_id: int, body: InvoiceInstallmentPaymentIn, db: Session = Depends(get_db)): return call(lambda: CardService(db).add_payment(invoice_id, body))

@router.put("/purchases/{purchase_id}/category")
def categorize_purchase(purchase_id: int, body: PurchaseCategoryIn, db: Session = Depends(get_db)): return call(lambda: CardService(db).categorize_purchase(purchase_id, body))

@router.post("/invoices/{invoice_id}/pay")
def pay_invoice(invoice_id: int, body: InvoiceInstallmentPaymentIn, db: Session = Depends(get_db)): return call(lambda: CardService(db).pay(invoice_id, body))
