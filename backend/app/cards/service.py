import csv
import hashlib
import io
import re
from datetime import date
from decimal import Decimal, InvalidOperation

from sqlalchemy.orm import Session

from ..categories.service import CategoryService
from ..core.errors import DomainError
from ..core.money import money
from ..transactions.model import Transaction
from .model import CreditCard, CreditCardInvoice, CreditCardInvoicePayment, CreditCardPurchase
from .repository import CardRepository


class CardService:
    def __init__(self, db: Session): self.db, self.repo, self.categories = db, CardRepository(db), CategoryService(db)
    def card_output(self, item):
        invoices = item.invoices
        open_total = sum((self.remaining_amount(invoice) for invoice in invoices if invoice.status == "open"), Decimal("0"))
        return {"id": item.id, "name": item.name, "brand": item.brand, "credit_limit": money(item.credit_limit) if item.credit_limit is not None else None, "closing_day": item.closing_day, "due_day": item.due_day, "open_total": money(open_total)}
    def total_amount(self, item): return sum((purchase.amount for purchase in item.purchases), Decimal("0"))
    def paid_total(self, item): return sum((payment.amount for payment in item.payments), Decimal("0"))
    def remaining_amount(self, item): return max(Decimal("0"), self.total_amount(item) - self.paid_total(item))
    def purchase_output(self, item):
        return {"id": item.id, "purchase_date": item.purchase_date.isoformat(), "title": item.title, "amount": money(item.amount), "category_id": item.category_id, "installment_current": item.installment_current, "installment_total": item.installment_total}
    def payment_output(self, item):
        return {"id": item.id, "payer_name": item.payer_name, "paid_by_owner": item.paid_by_owner, "description": item.description, "amount": money(item.amount), "paid_on": item.paid_on.isoformat(), "transaction_id": item.transaction_id}
    def invoice_output(self, item, detail=False):
        total = self.total_amount(item); paid_total = self.paid_total(item)
        result = {"id": item.id, "card_id": item.card_id, "reference_month": item.reference_month, "status": item.status, "paid_on": item.paid_on.isoformat() if item.paid_on else None, "payment_transaction_id": item.payment_transaction_id, "total": money(total), "paid_total": money(paid_total), "remaining_amount": money(self.remaining_amount(item)), "purchase_count": len(item.purchases)}
        if detail:
            result["purchases"] = [self.purchase_output(purchase) for purchase in sorted(item.purchases, key=lambda value: (value.purchase_date, value.id), reverse=True)]
            result["payments"] = [self.payment_output(payment) for payment in sorted(item.payments, key=lambda value: (value.paid_on, value.id), reverse=True)]
        return result
    def list(self): return [self.card_output(item) for item in self.repo.cards()]
    def create(self, data):
        item = self.repo.add(CreditCard(**data.model_dump())); self.db.commit(); self.db.refresh(item); return self.card_output(item)
    def detail(self, card_id):
        item = self.repo.card(card_id)
        if not item: raise DomainError(404, "Cartão não encontrado.")
        result = self.card_output(item)
        result["invoices"] = [self.invoice_output(invoice) for invoice in sorted(item.invoices, key=lambda value: value.reference_month, reverse=True)]
        return result
    def parse_amount(self, raw):
        try: return Decimal(re.sub(r"\s+", "", raw).replace(",", "."))
        except (InvalidOperation, AttributeError): raise DomainError(422, "O CSV contém um valor inválido.")
    def is_payment_received(self, title): return title.strip().casefold().startswith("pagamento recebido")
    def import_csv(self, card_id, data):
        card = self.repo.card(card_id)
        if not card: raise DomainError(404, "Cartão não encontrado.")
        reader = csv.DictReader(io.StringIO(data.content.lstrip("\ufeff")))
        if not reader.fieldnames or set(["date", "title", "amount"]) - set(reader.fieldnames): raise DomainError(422, "CSV Nubank inválido. Use as colunas date, title e amount.")
        invoice = self.repo.invoice_for(card_id, data.reference_month)
        if not invoice: invoice = self.repo.add(CreditCardInvoice(card_id=card_id, reference_month=data.reference_month))
        imported = duplicates = ignored = 0
        for purchase in invoice.purchases:
            if self.is_payment_received(purchase.title):
                self.repo.delete(purchase); ignored += 1
        self.db.flush()
        for row in reader:
            try: purchase_date = date.fromisoformat(row["date"])
            except (ValueError, TypeError): raise DomainError(422, "O CSV contém uma data inválida.")
            title, amount = (row["title"] or "").strip(), self.parse_amount(row["amount"])
            if not title: raise DomainError(422, "O CSV contém uma compra sem descrição.")
            if self.is_payment_received(title): ignored += 1; continue
            fingerprint = hashlib.sha256(f"{purchase_date.isoformat()}|{title.lower()}|{amount}".encode()).hexdigest()
            if self.repo.has_fingerprint(card_id, fingerprint): duplicates += 1; continue
            match = re.search(r"Parcela\s+(\d+)\s*/\s*(\d+)", title, re.IGNORECASE)
            self.repo.add(CreditCardPurchase(card_id=card_id, invoice_id=invoice.id, purchase_date=purchase_date, title=title, amount=amount, installment_current=int(match.group(1)) if match else None, installment_total=int(match.group(2)) if match else None, fingerprint=fingerprint))
            imported += 1
        self.db.commit(); self.db.refresh(invoice)
        return {"invoice": self.invoice_output(invoice, detail=True), "imported": imported, "duplicates": duplicates, "ignored": ignored}
    def invoice_detail(self, invoice_id):
        item = self.repo.invoice(invoice_id)
        if not item: raise DomainError(404, "Fatura não encontrada.")
        return self.invoice_output(item, detail=True)
    def delete_invoice(self, invoice_id):
        item = self.repo.invoice(invoice_id)
        if not item: raise DomainError(404, "Fatura não encontrada.")
        if item.status == "paid": raise DomainError(409, "Uma fatura paga não pode ser excluída.")
        self.repo.delete(item); self.db.commit()
    def categorize_purchase(self, purchase_id, data):
        item = self.repo.purchase(purchase_id)
        if not item: raise DomainError(404, "Compra não encontrada.")
        if data.category_id is not None: self.categories.require(data.category_id)
        item.category_id = data.category_id; self.db.commit(); self.db.refresh(item); return self.purchase_output(item)
    def register_payment(self, invoice, data):
        remaining = self.remaining_amount(invoice)
        if data.amount > remaining: raise DomainError(422, "O pagamento não pode ultrapassar o saldo restante da fatura.")
        payer_name = "Você" if data.paid_by_owner else (data.payer_name or "").strip()
        if not payer_name: raise DomainError(422, "Informe quem realizou o pagamento.")
        transaction = None
        if data.paid_by_owner:
            category = self.categories.credit_card_category()
            transaction = Transaction(date=data.paid_on, type="expense", amount=data.amount, category_id=category.id, description=f"Pagamento fatura {invoice.card.name} · {invoice.reference_month}")
            self.db.add(transaction); self.db.flush()
        payment = self.repo.add(CreditCardInvoicePayment(invoice_id=invoice.id, payer_name=payer_name, paid_by_owner=data.paid_by_owner, description=data.description.strip() if data.description else None, amount=data.amount, paid_on=data.paid_on, transaction_id=transaction.id if transaction else None))
        if self.remaining_amount(invoice) - data.amount <= 0:
            invoice.status, invoice.paid_on = "paid", data.paid_on
            if transaction: invoice.payment_transaction_id = transaction.id
        return payment
    def add_payment(self, invoice_id, data):
        invoice = self.repo.invoice(invoice_id)
        if not invoice: raise DomainError(404, "Fatura não encontrada.")
        if invoice.status == "paid": raise DomainError(409, "Esta fatura já foi paga.")
        if self.remaining_amount(invoice) <= 0: raise DomainError(422, "Não há valor pendente para pagar nesta fatura.")
        self.register_payment(invoice, data)
        self.db.commit(); self.db.refresh(invoice); return self.invoice_output(invoice, detail=True)
    def pay(self, invoice_id, data):
        invoice = self.repo.invoice(invoice_id)
        if not invoice: raise DomainError(404, "Fatura não encontrada.")
        if invoice.status == "paid": raise DomainError(409, "Esta fatura já foi paga.")
        if self.remaining_amount(invoice) <= 0: raise DomainError(422, "Não há valor pendente para pagar nesta fatura.")
        data.amount = self.remaining_amount(invoice)
        self.register_payment(invoice, data)
        self.db.commit(); self.db.refresh(invoice); return self.invoice_output(invoice, detail=True)
