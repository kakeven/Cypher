from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from .categories.model import Category
from .categories.router import router as categories_router
from .categories.service import CategoryService
from .cards.model import CreditCard, CreditCardInvoice, CreditCardInvoicePayment, CreditCardPurchase
from .cards.router import router as cards_router
from .core.base import Base
from .core.database import SessionLocal, engine
from .dashboard.router import router as dashboard_router
from .goals.model import Goal, GoalDeposit
from .goals.router import router as goals_router
from .receivables.model import Receivable, ReceivablePayment
from .receivables.router import router as receivables_router
from .recurring.model import RecurringOccurrence, RecurringTransaction
from .recurring.router import router as recurring_router
from .transactions.model import Transaction
from .transactions.router import router as transactions_router


def startup() -> None:
    Base.metadata.create_all(engine)
    if "receivables" in inspect(engine).get_table_names():
        columns = {column["name"] for column in inspect(engine).get_columns("receivables")}
        if "service_type" not in columns:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE receivables ADD COLUMN service_type VARCHAR(30)"))
    if "categories" in inspect(engine).get_table_names():
        columns = {column["name"] for column in inspect(engine).get_columns("categories")}
        if "is_active" not in columns:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE categories ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1"))
    with SessionLocal() as db:
        CategoryService(db).ensure_defaults()


def create_app() -> FastAPI:
    app = FastAPI(title="Cypher API", version="0.1.0")
    app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    app.include_router(categories_router, prefix="/api")
    app.include_router(cards_router, prefix="/api")
    app.include_router(transactions_router, prefix="/api")
    app.include_router(dashboard_router, prefix="/api")
    app.include_router(goals_router, prefix="/api")
    app.include_router(receivables_router, prefix="/api")
    app.include_router(recurring_router, prefix="/api")
    app.on_event("startup")(startup)
    return app
