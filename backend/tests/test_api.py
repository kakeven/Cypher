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


def test_allows_cors_from_android_preview():
    response = client.options(
        "/api/categories",
        headers={
            "Origin": "http://localhost:5174",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5174"


def test_categories_are_seeded():
    response = client.get("/api/categories")
    assert response.status_code == 200
    assert len(response.json()) >= 7
    assert any(item["name"] == "Assinaturas SaaS" for item in response.json())


def test_creates_category_and_rejects_duplicate_name():
    response = client.post("/api/categories", json={"name": "Assinaturas", "color": "#A855F7"})
    assert response.status_code == 201
    assert response.json()["name"] == "Assinaturas"
    duplicate = client.post("/api/categories", json={"name": "assinaturas", "color": "#A855F7"})
    assert duplicate.status_code == 409


def test_updates_category_name_and_color_without_changing_budget():
    created = client.post("/api/categories", json={"name": "Editável", "color": "#A855F7"}).json()
    client.put(f"/api/categories/{created['id']}/budget", json={"budget_limit": 120})
    updated = client.put(f"/api/categories/{created['id']}", json={"name": "Renomeada", "color": "#10B981"})
    assert updated.status_code == 200
    assert updated.json()["name"] == "Renomeada"
    assert updated.json()["color"] == "#10B981"
    assert updated.json()["budget_limit"] == 120.0
    assert client.put(f"/api/categories/{created['id']}", json={"name": "Assinaturas", "color": "#10B981"}).status_code == 409


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


def test_income_does_not_require_category_but_expense_does():
    income = client.post("/api/transactions", json={"date": date.today().isoformat(), "type": "income", "amount": 100, "description": "Freela"})
    assert income.status_code == 201
    assert client.post("/api/transactions", json={"date": date.today().isoformat(), "type": "expense", "amount": 100}).status_code == 422


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
    assert all("id" in row and "color" in row for row in dashboard["by_category"])
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


def test_goal_deposit_reduces_available_balance():
    category = category_id()
    client.post("/api/transactions", json={"date": date.today().isoformat(), "type": "income", "amount": 500, "category_id": category})
    balance_before_deposit = client.get("/api/dashboard").json()["balance"]
    goal = client.post("/api/goals", json={"name": "Reserva", "target_amount": 1000}).json()

    response = client.post(f"/api/goals/{goal['id']}/deposits", json={"amount": 125, "reference_month": date.today().strftime("%Y-%m")})

    assert response.status_code == 201
    assert client.get("/api/dashboard").json()["balance"] == balance_before_deposit - 125


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


def test_receivable_can_be_updated_and_deleted_with_its_payments():
    created = client.post("/api/receivables", json={"name": "Projeto", "client": "Cliente", "total_amount": 300, "service_type": "Sistema"}).json()
    payment = client.post(f"/api/receivables/{created['id']}/payments", json={"amount": 100, "received_on": date.today().isoformat()}).json()

    updated = client.put(f"/api/receivables/{created['id']}", json={"name": "Projeto revisado", "client": None, "total_amount": 400, "service_type": "E-commerce"})
    assert updated.status_code == 200
    assert updated.json()["name"] == "Projeto revisado"
    assert client.put(f"/api/receivables/{created['id']}", json={"name": "Projeto", "total_amount": 99, "service_type": "Sistema"}).status_code == 422

    assert client.delete(f"/api/receivables/{created['id']}").status_code == 204
    assert client.get(f"/api/receivables/{created['id']}").status_code == 404
    assert all(item["id"] != payment["transaction_id"] for item in client.get("/api/transactions").json())


def test_receivable_accepts_only_service_types():
    response = client.post("/api/receivables", json={"name": "Projeto", "total_amount": 100, "service_type": "Aplicativo"})
    assert response.status_code == 422


def test_recurring_generates_occurrences_and_confirmation_creates_transaction():
    category = category_id()
    recurring = client.post("/api/recurring-transactions", json={
        "name": "Assinatura", "type": "expense", "amount": 39.9, "category_id": category,
        "frequency": "monthly", "interval": 1, "day_of_month": date.today().day, "start_date": date.today().isoformat(),
    })
    assert recurring.status_code == 201
    generated = client.post(f"/api/recurring-transactions/{recurring.json()['id']}/generate-occurrences").json()
    assert generated
    occurrence = next(value for value in generated if value["due_date"] == date.today().isoformat())
    assert client.get("/api/occurrences", params={"period": date.today().strftime("%Y-%m")}).status_code == 200
    confirmed = client.post(f"/api/occurrences/{occurrence['id']}/confirm")
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "paid"
    assert any(row["id"] == confirmed.json()["transaction_id"] for row in client.get("/api/transactions").json())


def test_recurring_pause_prevents_generation():
    category = category_id()
    recurring = client.post("/api/recurring-transactions", json={
        "name": "Salário", "type": "income", "amount": 1000, "category_id": category,
        "frequency": "weekly", "interval": 1, "day_of_week": date.today().weekday(), "start_date": date.today().isoformat(),
    }).json()
    client.post(f"/api/recurring-transactions/{recurring['id']}/generate-occurrences")
    assert client.post(f"/api/recurring-transactions/{recurring['id']}/pause").json()["is_active"] is False
    assert client.post(f"/api/recurring-transactions/{recurring['id']}/generate-occurrences").status_code == 422
    assert client.post(f"/api/recurring-transactions/{recurring['id']}/resume").json()["is_active"] is True


def test_recurring_update_refreshes_pending_occurrences_in_agenda():
    category = category_id()
    recurring = client.post("/api/recurring-transactions", json={
        "name": "Freelance", "type": "income", "amount": 1000, "category_id": category,
        "frequency": "monthly", "interval": 1, "day_of_month": date.today().day, "start_date": date.today().isoformat(),
    }).json()
    generated = client.post(f"/api/recurring-transactions/{recurring['id']}/generate-occurrences").json()
    assert any(item["due_date"] == date.today().isoformat() for item in generated)

    updated = client.put(f"/api/recurring-transactions/{recurring['id']}", json={
        "name": "Freelance revisado", "type": "income", "amount": 1250, "category_id": category,
        "frequency": "monthly", "interval": 1, "day_of_month": date.today().day, "start_date": date.today().isoformat(),
    })

    assert updated.status_code == 200
    agenda = client.get("/api/occurrences", params={"period": date.today().strftime("%Y-%m")}).json()
    current = next(item for item in agenda if item["recurring_id"] == recurring["id"] and item["due_date"] == date.today().isoformat())
    assert current["recurring_name"] == "Freelance revisado"
    assert current["amount"] == 1250


def test_nubank_csv_import_deduplicates_and_pays_invoice():
    card = client.post("/api/credit-cards", json={"name": "Nubank", "brand": "Mastercard", "credit_limit": 5000, "closing_day": 24, "due_day": 1})
    assert card.status_code == 201
    content = "date,title,amount\n2026-08-11,Openai,\"41,61\"\n2026-08-09,Loja - Parcela 1/3,\"69,31\"\n2026-08-08,Estorno,\"- 10,00\"\n"
    imported = client.post(f"/api/credit-cards/{card.json()['id']}/import-csv", json={"reference_month": "2026-08", "content": content})
    assert imported.status_code == 200
    assert imported.json()["imported"] == 3
    invoice = imported.json()["invoice"]
    assert invoice["total"] == 100.92
    assert invoice["purchases"][1]["installment_current"] == 1
    repeated = client.post(f"/api/credit-cards/{card.json()['id']}/import-csv", json={"reference_month": "2026-08", "content": content}).json()
    assert repeated["imported"] == 0
    assert repeated["duplicates"] == 3
    paid = client.post(f"/api/credit-cards/invoices/{invoice['id']}/pay", json={"paid_on": date.today().isoformat(), "amount": 100.92, "paid_by_owner": True})
    assert paid.status_code == 200
    assert paid.json()["status"] == "paid"
    assert any(item["id"] == paid.json()["payment_transaction_id"] and item["amount"] == 100.92 for item in client.get("/api/transactions").json())


def test_nubank_csv_ignores_payment_received_and_keeps_refund():
    card = client.post("/api/credit-cards", json={"name": "Nubank créditos", "closing_day": 24, "due_day": 1}).json()
    content = "date,title,amount\n2026-08-11,Compra,100.00\n2026-08-10,Pagamento recebido,-100.00\n2026-08-09,Estorno de compra,-10.00\n"
    imported = client.post(f"/api/credit-cards/{card['id']}/import-csv", json={"reference_month": "2026-08", "content": content}).json()
    assert imported["imported"] == 2
    assert imported["ignored"] == 1
    assert imported["invoice"]["total"] == 90.0
    assert all(purchase["title"] != "Pagamento recebido" for purchase in imported["invoice"]["purchases"])
    repeated = client.post(f"/api/credit-cards/{card['id']}/import-csv", json={"reference_month": "2026-08", "content": content}).json()
    assert repeated["ignored"] == 1
    assert repeated["invoice"]["total"] == 90.0


def test_category_deletion_removes_unused_and_archives_history():
    unused = client.post("/api/categories", json={"name": "Temporária", "color": "#A855F7"}).json()
    removed = client.delete(f"/api/categories/{unused['id']}")
    assert removed.status_code == 200
    assert removed.json()["archived"] is False
    assert all(item["id"] != unused["id"] for item in client.get("/api/categories").json())

    used = client.post("/api/categories", json={"name": "Histórica", "color": "#A855F7"}).json()
    client.post("/api/transactions", json={"date": date.today().isoformat(), "type": "expense", "amount": 10, "category_id": used["id"]})
    archived = client.delete(f"/api/categories/{used['id']}")
    assert archived.status_code == 200
    assert archived.json()["archived"] is True
    assert all(item["id"] != used["id"] for item in client.get("/api/categories").json())


def test_categorized_card_purchase_counts_in_budget_and_dashboard_without_payment_duplicate():
    category = client.post("/api/categories", json={"name": "Cartão teste", "color": "#3B82F6"}).json()
    client.put(f"/api/categories/{category['id']}/budget", json={"budget_limit": 100})
    card = client.post("/api/credit-cards", json={"name": "Cartão analítico", "closing_day": 20, "due_day": 1}).json()
    period = date.today().strftime("%Y-%m")
    purchase_date = (date.today().replace(day=1) - timedelta(days=1)).isoformat()
    imported = client.post(f"/api/credit-cards/{card['id']}/import-csv", json={"reference_month": period, "content": f"date,title,amount\n{purchase_date},Compra categorizada,\"25,00\"\n"}).json()["invoice"]
    purchase = imported["purchases"][0]
    assert client.put(f"/api/credit-cards/purchases/{purchase['id']}/category", json={"category_id": category["id"]}).status_code == 200
    dashboard = client.get("/api/dashboard", params={"period": period}).json()
    assert next(item for item in dashboard["by_category"] if item["id"] == category["id"])["amount"] == 25.0
    budget = next(item for item in client.get("/api/budgets", params={"period": period}).json() if item["id"] == category["id"])
    assert budget["spent"] == 25.0
    client.post(f"/api/credit-cards/invoices/{imported['id']}/pay", json={"paid_on": date.today().isoformat(), "amount": 25, "paid_by_owner": True})
    dashboard_after_payment = client.get("/api/dashboard", params={"period": period}).json()
    assert next(item for item in dashboard_after_payment["by_category"] if item["id"] == category["id"])["amount"] == 25.0


def test_deletes_open_credit_card_invoice_and_its_purchases():
    card = client.post("/api/credit-cards", json={"name": "Cartão para excluir", "closing_day": 20, "due_day": 1}).json()
    period = date.today().strftime("%Y-%m")
    imported = client.post(f"/api/credit-cards/{card['id']}/import-csv", json={"reference_month": period, "content": f"date,title,amount\n{date.today().isoformat()},Compra removível,10.00\n"}).json()["invoice"]
    assert client.delete(f"/api/credit-cards/invoices/{imported['id']}").status_code == 204
    assert client.get(f"/api/credit-cards/invoices/{imported['id']}").status_code == 404
    assert client.get(f"/api/credit-cards/{card['id']}").json()["invoices"] == []


def test_card_invoice_payment_records_payer_and_only_owner_changes_balance():
    card = client.post("/api/credit-cards", json={"name": "Cartão compartilhado", "closing_day": 20, "due_day": 1}).json()
    invoice = client.post(f"/api/credit-cards/{card['id']}/import-csv", json={"reference_month": date.today().strftime("%Y-%m"), "content": f"date,title,amount\n{date.today().isoformat()},Compra compartilhada,100.00\n"}).json()["invoice"]
    balance_before = client.get("/api/dashboard").json()["balance"]
    expense_card_before = client.get("/api/dashboard").json()["net_expense"]

    external = client.post(f"/api/credit-cards/invoices/{invoice['id']}/payments", json={"amount": 30, "paid_on": date.today().isoformat(), "paid_by_owner": False, "payer_name": "Ana", "description": "Parte dela"})
    assert external.status_code == 200
    assert external.json()["status"] == "open"
    assert external.json()["paid_total"] == 30.0
    assert external.json()["remaining_amount"] == 70.0
    dashboard_after_external_payment = client.get("/api/dashboard").json()
    assert dashboard_after_external_payment["balance"] == balance_before
    assert dashboard_after_external_payment["net_expense"] == expense_card_before

    paid = client.post(f"/api/credit-cards/invoices/{invoice['id']}/pay", json={"amount": 70, "paid_on": date.today().isoformat(), "paid_by_owner": True})
    assert paid.status_code == 200
    assert paid.json()["status"] == "paid"
    assert paid.json()["paid_total"] == 100.0
    assert paid.json()["remaining_amount"] == 0.0
    assert any(payment["payer_name"] == "Ana" and payment["paid_by_owner"] is False for payment in paid.json()["payments"])
    dashboard = client.get("/api/dashboard").json()
    assert dashboard["balance"] == balance_before - 70
    assert dashboard["net_expense"] == expense_card_before


def test_dashboard_includes_total_pending_credit_card_invoices():
    pending_before = client.get("/api/dashboard").json()["card_pending"]
    other_people = client.post("/api/categories", json={"name": "Outras pessoas", "color": "#A855F7"}).json()
    card = client.post("/api/credit-cards", json={"name": "Cartão pendente", "closing_day": 20, "due_day": 1}).json()
    invoice = client.post(f"/api/credit-cards/{card['id']}/import-csv", json={"reference_month": date.today().strftime("%Y-%m"), "content": f"date,title,amount\n{date.today().isoformat()},Compra pendente,100.00\n{date.today().isoformat()},Compra da Ana,40.00\n"}).json()["invoice"]
    purchase_from_other_person = next(item for item in invoice["purchases"] if item["title"] == "Compra da Ana")
    assert client.put(f"/api/credit-cards/purchases/{purchase_from_other_person['id']}/category", json={"category_id": other_people["id"]}).status_code == 200
    client.post(f"/api/credit-cards/invoices/{invoice['id']}/payments", json={"amount": 35, "paid_on": date.today().isoformat(), "paid_by_owner": False, "payer_name": "Ana"})

    dashboard = client.get("/api/dashboard").json()

    assert dashboard["card_pending"] == pending_before + 100.0


def test_saas_subscription_generates_invoices_and_records_partial_payment_once():
    client_item = client.post("/api/saas-clients", json={"name": "Loja Tervo"})
    assert client_item.status_code == 201
    product = client.post("/api/saas-products", json={"name": "Gestão de Loja"})
    assert product.status_code == 201
    subscription = client.post("/api/saas-subscriptions", json={
        "client_id": client_item.json()["id"], "product_id": product.json()["id"], "name": "Plano mensal",
        "amount": 99, "billing_cycle": "monthly", "due_day": date.today().day,
        "start_date": date.today().isoformat(),
    })
    assert subscription.status_code == 201
    generated = client.post("/api/saas-subscriptions/generate-invoices", json={"end_date": date.today().isoformat()})
    assert generated.status_code == 200
    invoices = client.get("/api/saas-invoices", params={"period": date.today().strftime("%Y-%m")}).json()
    invoice = next(item for item in invoices if item["subscription_id"] == subscription.json()["id"])
    again = client.post("/api/saas-subscriptions/generate-invoices", json={"end_date": date.today().isoformat()})
    assert again.json() == []

    payment = client.post(f"/api/saas-invoices/{invoice['id']}/payments", json={"amount": 50, "paid_at": date.today().isoformat(), "payment_method": "pix"})
    assert payment.status_code == 201
    partial = next(item for item in client.get("/api/saas-invoices", params={"period": date.today().strftime("%Y-%m")}).json() if item["id"] == invoice["id"])
    assert partial["status"] == "partial"
    assert partial["remaining_amount"] == 49.0
    transaction = next(item for item in client.get("/api/transactions", params={"type": "income"}).json() if item["id"] == payment.json()["transaction_id"])
    assert transaction["amount"] == 50.0
    assert transaction["category_name"] == "Assinaturas SaaS"


def test_saas_cancellation_preserves_history_and_stops_future_invoices():
    client_item = client.post("/api/saas-clients", json={"name": "Cliente cancelado"}).json()
    product = client.post("/api/saas-products", json={"name": "Produto cancelado"}).json()
    subscription = client.post("/api/saas-subscriptions", json={
        "client_id": client_item["id"], "product_id": product["id"], "name": "Contrato cancelável",
        "amount": 100, "billing_cycle": "monthly", "due_day": 1, "start_date": date.today().replace(day=1).isoformat(),
    }).json()
    client.post("/api/saas-subscriptions/generate-invoices", json={"end_date": (date.today() + timedelta(days=90)).isoformat()})
    before = [item for item in client.get("/api/saas-invoices").json() if item["subscription_id"] == subscription["id"]]
    canceled = client.post(f"/api/saas-subscriptions/{subscription['id']}/cancel", json={"canceled_at": date.today().isoformat()})
    assert canceled.status_code == 200
    client.post("/api/saas-subscriptions/generate-invoices", json={"end_date": (date.today() + timedelta(days=365)).isoformat()})
    after = [item for item in client.get("/api/saas-invoices").json() if item["subscription_id"] == subscription["id"]]
    assert len(after) == len(before)


def test_dashboard_expense_card_excludes_other_people_category():
    own_category = client.post("/api/categories", json={"name": "Despesa própria", "color": "#10B981"}).json()
    other_people = next(item for item in client.get("/api/categories").json() if item["name"] == "Outras pessoas")
    period = date.today().strftime("%Y-%m")
    before_dashboard = client.get("/api/dashboard", params={"period": period}).json()
    before = before_dashboard["net_expense"]
    before_flow = next(item for item in before_dashboard["monthly_evolution"] if item["month"] == period)["expense"]
    client.post("/api/transactions", json={"date": date.today().isoformat(), "type": "expense", "amount": 80, "category_id": own_category["id"]})
    client.post("/api/transactions", json={"date": date.today().isoformat(), "type": "expense", "amount": 120, "category_id": other_people["id"]})
    dashboard = client.get("/api/dashboard", params={"period": period}).json()
    assert dashboard["net_expense"] == before + 80
    assert next(item for item in dashboard["monthly_evolution"] if item["month"] == period)["expense"] == before_flow + 80
