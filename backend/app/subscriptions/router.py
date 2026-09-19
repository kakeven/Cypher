from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.errors import DomainError
from .schema import CancelIn, ClientIn, InvoiceGenerationIn, PaymentIn, PlanIn, ProductIn, SubscriptionIn
from .service import SubscriptionService

router = APIRouter(tags=["subscriptions"])
def call(operation):
    try: return operation()
    except DomainError as error: raise HTTPException(error.status_code, error.detail) from error

@router.get("/saas-clients")
def clients(db: Session = Depends(get_db)): return SubscriptionService(db).list_clients()
@router.post("/saas-clients", status_code=201)
def create_client(body: ClientIn, db: Session = Depends(get_db)): return SubscriptionService(db).create_client(body)
@router.put("/saas-clients/{item_id}")
def update_client(item_id: int, body: ClientIn, db: Session = Depends(get_db)): return call(lambda: SubscriptionService(db).update_client(item_id, body))
@router.get("/saas-products")
def products(db: Session = Depends(get_db)): return SubscriptionService(db).list_products()
@router.post("/saas-products", status_code=201)
def create_product(body: ProductIn, db: Session = Depends(get_db)): return call(lambda: SubscriptionService(db).create_product(body))
@router.put("/saas-products/{item_id}")
def update_product(item_id: int, body: ProductIn, db: Session = Depends(get_db)): return call(lambda: SubscriptionService(db).update_product(item_id, body))
@router.get("/saas-plans")
def plans(db: Session = Depends(get_db)): return SubscriptionService(db).list_plans()
@router.post("/saas-plans", status_code=201)
def create_plan(body: PlanIn, db: Session = Depends(get_db)): return call(lambda: SubscriptionService(db).create_plan(body))
@router.put("/saas-plans/{item_id}")
def update_plan(item_id: int, body: PlanIn, db: Session = Depends(get_db)): return call(lambda: SubscriptionService(db).update_plan(item_id, body))
@router.post("/saas-subscriptions/generate-invoices")
def generate_invoices(body: InvoiceGenerationIn, db: Session = Depends(get_db)): return SubscriptionService(db).generate_invoices(body.end_date)
@router.get("/saas-subscriptions")
def subscriptions(db: Session = Depends(get_db)): return SubscriptionService(db).list_subscriptions()
@router.post("/saas-subscriptions", status_code=201)
def create_subscription(body: SubscriptionIn, db: Session = Depends(get_db)): return call(lambda: SubscriptionService(db).create_subscription(body))
@router.get("/saas-subscriptions/{item_id}")
def subscription(item_id: int, db: Session = Depends(get_db)): return call(lambda: SubscriptionService(db).get_subscription(item_id))
@router.put("/saas-subscriptions/{item_id}")
def update_subscription(item_id: int, body: SubscriptionIn, db: Session = Depends(get_db)): return call(lambda: SubscriptionService(db).update_subscription(item_id, body))
@router.post("/saas-subscriptions/{item_id}/pause")
def pause(item_id: int, db: Session = Depends(get_db)): return call(lambda: SubscriptionService(db).transition(item_id, "pause"))
@router.post("/saas-subscriptions/{item_id}/resume")
def resume(item_id: int, db: Session = Depends(get_db)): return call(lambda: SubscriptionService(db).transition(item_id, "resume"))
@router.post("/saas-subscriptions/{item_id}/cancel")
def cancel(item_id: int, body: CancelIn, db: Session = Depends(get_db)): return call(lambda: SubscriptionService(db).transition(item_id, "cancel", body.canceled_at))
@router.get("/saas-invoices")
def invoices(status: str | None = None, client_id: int | None = None, period: str | None = None, due_from: date | None = None, due_to: date | None = None, db: Session = Depends(get_db)): return SubscriptionService(db).list_invoices(status=status, client_id=client_id, period=period, due_from=due_from, due_to=due_to)
@router.post("/saas-invoices/{item_id}/payments", status_code=201)
def payment(item_id: int, body: PaymentIn, db: Session = Depends(get_db)): return call(lambda: SubscriptionService(db).add_payment(item_id, body))
@router.delete("/saas-payments/{item_id}", status_code=204)
def delete_payment(item_id: int, db: Session = Depends(get_db)):
    call(lambda: SubscriptionService(db).delete_payment(item_id)); return Response(status_code=204)
@router.get("/saas-dashboard")
def dashboard(period: str = date.today().strftime("%Y-%m"), db: Session = Depends(get_db)): return SubscriptionService(db).dashboard(period)
