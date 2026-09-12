import os
import sys
from datetime import date, timedelta
from pathlib import Path

TEST_DATABASE_PATH = Path(__file__).with_name("cypher-test.db")
TEST_DATABASE_PATH.unlink(missing_ok=True)
os.environ["CYPHER_DATABASE_URL"] = f"sqlite:///{TEST_DATABASE_PATH}"
sys.path.insert(0, str(Path(__file__).parents[1]))

from fastapi.testclient import TestClient
from main import app, startup

startup()
client = TestClient(app)


def category_id():
    return client.get("/api/categories").json()[0]["id"]


def second_category_id():
    return client.get("/api/categories").json()[1]["id"]


def test_health():
    assert client.get("/api/health").json() == {"status": "ok"}


def test_categories_are_seeded():
    response = client.get("/api/categories")
    assert response.status_code == 200
    assert len(response.json()) == 7


def test_creates_category_and_rejects_duplicate_name():
    response = client.post("/api/categories", json={"name": "Assinaturas", "color": "#A855F7"})
    assert response.status_code == 201
    assert response.json()["name"] == "Assinaturas"
    duplicate = client.post("/api/categories", json={"name": "assinaturas", "color": "#A855F7"})
    assert duplicate.status_code == 409


def test_rejects_invalid_category_color():
    assert client.post("/api/categories", json={"name": "Pet", "color": "not-a-hex"}).status_code == 422


def test_transaction_crud_full_cycle():
    category = category_id()
    balance_before = client.get("/api/dashboard").json()["balance"]
    created = client.post("/api/transactions", json={"date": date.today().isoformat(), "type": "income", "amount": "2000.00", "category_id": category, "description": "Salário"})
    assert created.status_code == 201
    item = created.json()
    assert item["type"] == "income"
    assert item["amount"] == 2000.0
    assert item["category_name"]

    updated = client.put(f"/api/transactions/{item['id']}", json={"date": date.today().isoformat(), "type": "expense", "amount": "250.00", "category_id": category})
    assert updated.status_code == 200
    assert updated.json()["type"] == "expense"

    dashboard = client.get("/api/dashboard").json()
    assert dashboard["balance"] == balance_before - 250

    assert client.delete(f"/api/transactions/{item['id']}").status_code == 204
    after_delete = client.get(f"/api/transactions")
    assert all(row["id"] != item["id"] for row in after_delete.json())


def test_404_on_missing_transaction():
    assert client.get("/api/transactions").status_code == 200
    assert client.put("/api/transactions/9999", json={"date": date.today().isoformat(), "type": "expense", "amount": 1, "category_id": 1}).status_code == 404
    assert client.delete("/api/transactions/9999").status_code == 404


def test_rejects_future_transaction_and_invalid_amount():
    category = category_id()
    future = (date.today() + timedelta(days=1)).isoformat()
    assert client.post("/api/transactions", json={"date": future, "type": "income", "amount": 1, "category_id": category}).status_code == 422
    assert client.post("/api/transactions", json={"date": date.today().isoformat(), "type": "income", "amount": 0, "category_id": category}).status_code == 422
    assert client.post("/api/transactions", json={"date": date.today().isoformat(), "type": "income", "amount": -10, "category_id": category}).status_code == 422


def test_rejects_invalid_type_and_missing_category():
    category = category_id()
    assert client.post("/api/transactions", json={"date": date.today().isoformat(), "type": "transfer", "amount": 1, "category_id": category}).status_code == 422
    assert client.post("/api/transactions", json={"date": date.today().isoformat(), "type": "expense", "amount": 1, "category_id": 9999}).status_code == 404


def test_transaction_filters_by_category_and_type():
    cat_a, cat_b = category_id(), second_category_id()
    today = date.today().isoformat()
    client.post("/api/transactions", json={"date": today, "type": "expense", "amount": 10, "category_id": cat_a})
    client.post("/api/transactions", json={"date": today, "type": "income", "amount": 20, "category_id": cat_b})

    by_type = client.get("/api/transactions", params={"type": "income"}).json()
    assert all(row["type"] == "income" for row in by_type)

    by_category = client.get("/api/transactions", params={"category_id": cat_a}).json()
    assert all(row["category_id"] == cat_a for row in by_category)


def test_transaction_filters_by_date_range():
    category = category_id()
    old = (date.today() - timedelta(days=30)).isoformat()
    recent = date.today().isoformat()
    client.post("/api/transactions", json={"date": old, "type": "expense", "amount": 5, "category_id": category})
    client.post("/api/transactions", json={"date": recent, "type": "expense", "amount": 7, "category_id": category})

    start = (date.today() - timedelta(days=7)).isoformat()
    filtered = client.get("/api/transactions", params={"date_from": start}).json()
    assert all(row["date"] >= start for row in filtered)
    assert any(row["amount"] == 7 for row in filtered)
    assert not any(row["amount"] == 5 for row in filtered)


def test_dashboard_aggregates_current_period_and_balance():
    category = category_id()
    today = date.today().isoformat()
    previous_month = (date.today().replace(day=1) - timedelta(days=1)).isoformat()
    client.post("/api/transactions", json={"date": today, "type": "income", "amount": 500, "category_id": category})
    client.post("/api/transactions", json={"date": today, "type": "expense", "amount": 200, "category_id": category})
    client.post("/api/transactions", json={"date": previous_month, "type": "expense", "amount": 100, "category_id": category})

    period = date.today().strftime("%Y-%m")
    dashboard = client.get("/api/dashboard", params={"period": period}).json()
    assert dashboard["period"] == period
    assert dashboard["income"] >= 500
    assert dashboard["expense"] >= 200
    assert any(row["name"] for row in dashboard["by_category"])
    assert len(dashboard["monthly_evolution"]) == 12


def test_dashboard_rejects_invalid_period():
    assert client.get("/api/dashboard", params={"period": "2026-13"}).status_code == 422
    assert client.get("/api/dashboard", params={"period": "not-a-date"}).status_code == 422


def test_budget_and_goal_completion():
    category = category_id()
    assert client.put(f"/api/categories/{category}/budget", json={"budget_limit": 100}).status_code == 200
    goal = client.post("/api/goals", json={"name": "Viagem", "target_amount": 1000}).json()
    assert client.post(f"/api/goals/{goal['id']}/deposits", json={"amount": 1000, "reference_month": date.today().strftime("%Y-%m")}).status_code == 201
    loaded = client.get(f"/api/goals/{goal['id']}").json()
    assert loaded["is_completed"] is True


def test_receivable_records_partial_payments_as_income():
    created = client.post("/api/receivables", json={"name": "Projeto ACME", "client": "ACME", "total_amount": 750, "service_type": "Site institucional"})
    assert created.status_code == 201
    receivable = created.json()
    assert receivable["remaining_amount"] == 750.0
    assert receivable["service_type"] == "Site institucional"

    first = client.post(f"/api/receivables/{receivable['id']}/payments", json={"amount": 100, "received_on": date.today().isoformat(), "note": "Entrada"})
    assert first.status_code == 201
    second = client.post(f"/api/receivables/{receivable['id']}/payments", json={"amount": 400, "received_on": date.today().isoformat()})
    assert second.status_code == 201

    loaded = client.get(f"/api/receivables/{receivable['id']}").json()
    assert loaded["received_amount"] == 500.0
    assert loaded["remaining_amount"] == 250.0
    assert len(loaded["payments"]) == 2
    assert client.post(f"/api/receivables/{receivable['id']}/payments", json={"amount": 251, "received_on": date.today().isoformat()}).status_code == 422

    transactions = client.get("/api/transactions", params={"type": "income"}).json()
    assert any(item["id"] == first.json()["transaction_id"] and item["amount"] == 100.0 for item in transactions)


def test_receivable_accepts_only_service_types():
    response = client.post("/api/receivables", json={"name": "Projeto", "total_amount": 100, "service_type": "Aplicativo"})
    assert response.status_code == 422
