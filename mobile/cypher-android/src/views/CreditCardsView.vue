<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { api, brl } from '@/services/api'
import { useToast } from '@/composables/useToast'
import { currentMonth, formatDateBR, todayISO } from '@/utils/format'
import DateInput from '@/components/DateInput.vue'

const toast = useToast()
const cards = ref([])
const selected = ref(null)
const invoice = ref(null)
const categories = ref([])
const csvFile = ref(null)
const importing = ref(false)
const error = ref('')
const referenceMonth = ref(currentMonth())
const today = todayISO()
const form = reactive({ name: 'Nubank', brand: 'Mastercard', credit_limit: '', closing_day: 24, due_day: 1 })
const hasCard = computed(() => cards.value.length > 0)
const paymentMode = ref(null)
const paymentForm = reactive({ paid_by_owner: true, payer_name: '', amount: '', description: '' })

async function load() {
  error.value = ''
  try {
    cards.value = await api.creditCards()
    if (selected.value) selected.value = await api.creditCard(selected.value.id)
    else if (cards.value.length) selected.value = await api.creditCard(cards.value[0].id)
  } catch (e) { error.value = e.message }
}
async function create() {
  try {
    const created = await api.createCreditCard({ ...form, credit_limit: form.credit_limit ? Number(form.credit_limit) : null, brand: form.brand.trim() || null })
    toast.success('Cartão cadastrado.')
    await load()
    selected.value = await api.creditCard(created.id)
  } catch (e) { error.value = e.message }
}
async function choose(card) {
  try { selected.value = await api.creditCard(card.id); invoice.value = null } catch (e) { error.value = e.message }
}
function pickFile(event) { csvFile.value = event.target.files?.[0] || null }
async function importCsv() {
  if (!csvFile.value || !selected.value) return
  importing.value = true
  error.value = ''
  try {
    const content = await csvFile.value.text()
    const result = await api.importCreditCardCsv(selected.value.id, { reference_month: referenceMonth.value, content })
    invoice.value = result.invoice
    await load()
    toast.success(result.imported ? `${result.imported} compra(s) importada(s).` : 'Nenhuma compra nova foi encontrada.')
  } catch (e) { error.value = e.message } finally { importing.value = false }
}
async function openInvoice(item) {
  try { invoice.value = await api.creditCardInvoice(item.id) } catch (e) { error.value = e.message }
}
async function categorize(purchase, event) {
  try {
    purchase.category_id = event.target.value ? Number(event.target.value) : null
    await api.setCreditCardPurchaseCategory(purchase.id, purchase.category_id)
    toast.success('Categoria atualizada.')
  } catch (e) { error.value = e.message }
}
function openPayment(mode) {
  if (!invoice.value) return
  paymentMode.value = mode
  paymentForm.paid_by_owner = true
  paymentForm.payer_name = ''
  paymentForm.amount = mode === 'full' ? invoice.value.remaining_amount : ''
  paymentForm.description = ''
}
async function submitPayment() {
  if (!invoice.value || !paymentMode.value) return
  try {
    const payload = { amount: Number(paymentForm.amount), paid_on: today, paid_by_owner: paymentForm.paid_by_owner, payer_name: paymentForm.paid_by_owner ? null : paymentForm.payer_name.trim(), description: paymentForm.description.trim() || null }
    invoice.value = paymentMode.value === 'full'
      ? await api.payCreditCardInvoice(invoice.value.id, payload)
      : await api.addCreditCardInvoicePayment(invoice.value.id, payload)
    paymentMode.value = null
    await load()
    toast.success('Pagamento registrado.')
  } catch (e) { error.value = e.message }
}
async function deleteInvoice() {
  if (!invoice.value || !window.confirm(`Excluir a fatura de ${invoice.value.reference_month}? Todas as compras importadas nela serão removidas.`)) return
  try {
    await api.deleteCreditCardInvoice(invoice.value.id)
    invoice.value = null
    await load()
    toast.success('Fatura excluída.')
  } catch (e) { error.value = e.message }
}

function handleKeydown(event) {
  if (event.key === 'Escape') paymentMode.value = null
}

onMounted(async () => {
  window.addEventListener('keydown', handleKeydown)
  try { categories.value = await api.categories() } catch (e) { error.value = e.message }
  await load()
})

onBeforeUnmount(() => window.removeEventListener('keydown', handleKeydown))
</script>

<template>
  <div>
    <header class="page-header"><div><h1>Cartões</h1><p>Importe a fatura e pague uma vez, sem duplicar seus gastos.</p></div></header>
    <p v-if="error" class="message" role="alert">{{ error }}</p>

    <section v-if="!hasCard" class="card card-form">
      <h2>Adicionar cartão</h2>
      <form class="form-grid" @submit.prevent="create">
        <label>Nome do cartão<input v-model="form.name" class="input" maxlength="80" required /></label><label>Bandeira<input v-model="form.brand" class="input" maxlength="30" /></label>
        <label>Limite (opcional)<input v-model="form.credit_limit" class="input" type="number" min="0.01" step="0.01" /></label><label>Fechamento<input v-model="form.closing_day" class="input" type="number" min="1" max="31" required /></label>
        <label>Vencimento<input v-model="form.due_day" class="input" type="number" min="1" max="31" required /></label><div class="actions"><button class="button">Adicionar cartão</button></div>
      </form>
    </section>

    <template v-else>
      <section class="card-strip"><button v-for="card in cards" :key="card.id" :class="['card-item', { active: selected?.id === card.id }]" @click="choose(card)"><span>{{ card.brand || 'Cartão' }}</span><b>{{ card.name }}</b><small>Em aberto {{ brl(card.open_total) }}</small></button><button class="new-card" @click="selected = null; cards = []">+ Cartão</button></section>
      <section v-if="selected" class="card import-card"><header><div><span>{{ selected.brand || 'Cartão' }}</span><h2>{{ selected.name }}</h2><p>Fecha dia {{ selected.closing_day }} · vence dia {{ selected.due_day }}</p></div><strong v-if="selected.credit_limit">{{ brl(selected.credit_limit) }}</strong></header><div class="import-controls"><label class="file"><input accept=".csv,text/csv" type="file" @change="pickFile" /><span>{{ csvFile ? csvFile.name : 'Escolher CSV da Nubank' }}</span></label><DateInput v-model="referenceMonth" type="month" :max="currentMonth()" /><button class="button" :disabled="!csvFile || importing" @click="importCsv">{{ importing ? 'Importando…' : 'Importar fatura' }}</button></div><p class="import-note">O arquivo fica apenas neste computador. Compras repetidas são ignoradas automaticamente.</p></section>
      <section v-if="selected" class="invoices"><header><h2>Faturas</h2></header><p v-if="!selected.invoices?.length" class="empty card">Importe um CSV para criar sua primeira fatura.</p><div v-else class="invoice-grid"><button v-for="item in selected.invoices" :key="item.id" :class="['invoice-card', { active: invoice?.id === item.id, paid: item.status === 'paid' }]" @click="openInvoice(item)"><span>{{ item.reference_month }}</span><b>{{ brl(item.status === 'open' ? item.remaining_amount : item.total) }}</b><small>{{ item.status === 'paid' ? 'Paga' : `${brl(item.paid_total)} pago · ${item.purchase_count} compra(s)` }}</small></button></div></section>
      <section v-if="invoice" class="card invoice-detail"><header><div><span>Fatura {{ invoice.reference_month }}</span><h2>{{ brl(invoice.total) }}</h2><p v-if="invoice.status === 'open'">Restante: <b>{{ brl(invoice.remaining_amount) }}</b> · pago: {{ brl(invoice.paid_total) }}</p></div><div v-if="invoice.status === 'open'" class="invoice-actions"><button class="button button--ghost" @click="openPayment('partial')">Pagamento em partes</button><button class="button" @click="openPayment('full')">{{ invoice.paid_total ? 'Pagar restante' : 'Pagar tudo' }}</button><button class="button danger-button" @click="deleteInvoice">Excluir fatura</button></div><b v-else class="paid">Paga em {{ formatDateBR(invoice.paid_on) }}</b></header><section v-if="invoice.payments?.length" class="payment-history"><h3>Pagamentos</h3><div v-for="payment in invoice.payments" :key="payment.id" class="payment-row"><div><b>{{ payment.paid_by_owner ? 'Você' : payment.payer_name }}</b><small>{{ formatDateBR(payment.paid_on) }}<span v-if="payment.description"> · {{ payment.description }}</span></small></div><strong>{{ brl(payment.amount) }}</strong></div></section><div class="purchase-table-scroll" tabindex="0" aria-label="Compras da fatura; tabela rolável horizontalmente"><table><thead><tr><th>Data</th><th>Compra</th><th>Categoria</th><th>Valor</th></tr></thead><tbody><tr v-for="purchase in invoice.purchases" :key="purchase.id"><td>{{ formatDateBR(purchase.purchase_date) }}</td><td>{{ purchase.title }} <small v-if="purchase.installment_total">{{ purchase.installment_current }}/{{ purchase.installment_total }}</small></td><td><select :value="purchase.category_id || ''" class="category-select" @change="categorize(purchase, $event)"><option value="">Sem categoria</option><option v-for="category in categories" :key="category.id" :value="category.id">{{ category.name }}</option></select></td><td :class="purchase.amount < 0 ? 'credit' : ''">{{ brl(purchase.amount) }}</td></tr></tbody></table></div></section>
      <div v-if="paymentMode" class="payment-modal-backdrop" @click.self="paymentMode = null"><form class="card payment-modal" role="dialog" aria-modal="true" @submit.prevent="submitPayment"><header><div><span>{{ paymentMode === 'full' ? 'Quitar fatura' : 'Pagamento em partes' }}</span><h2>{{ paymentMode === 'full' ? brl(invoice.remaining_amount) : 'Registrar valor' }}</h2></div><button type="button" class="close" aria-label="Fechar" @click="paymentMode = null">×</button></header><label v-if="paymentMode === 'partial'">Valor pago<input v-model="paymentForm.amount" class="input" type="number" min="0.01" :max="invoice.remaining_amount" step="0.01" required /></label><fieldset><legend>Quem pagou?</legend><label><input v-model="paymentForm.paid_by_owner" type="radio" :value="true" /> Eu — sai do meu saldo</label><label><input v-model="paymentForm.paid_by_owner" type="radio" :value="false" /> Outra pessoa — baixa só a fatura</label></fieldset><label v-if="!paymentForm.paid_by_owner">Nome de quem pagou<input v-model="paymentForm.payer_name" class="input" maxlength="80" required /></label><label>Descrição <span>(opcional)</span><input v-model="paymentForm.description" class="input" maxlength="250" placeholder="Ex.: parte da compra" /></label><p>Pagamentos de outra pessoa não viram despesa no seu saldo.</p><div class="modal-actions"><button type="button" class="button button--ghost" @click="paymentMode = null">Cancelar</button><button class="button">Confirmar pagamento</button></div></form></div>
    </template>
  </div>
</template>

<style scoped>
.card-form { max-width: 760px; } .card-form h2, .invoices h2 { margin: 0 0 18px; font-size: 16px; } .actions { display: flex; align-items: end; } .card-strip, .invoice-grid, .invoice-actions { display: flex; gap: 10px; flex-wrap: wrap; } .card-item, .new-card, .invoice-card { display: grid; min-width: 190px; border: 1px solid var(--color-border); border-radius: 8px; padding: 14px; color: var(--color-text-primary); text-align: left; background: var(--color-surface); cursor: pointer; } .card-item.active, .invoice-card.active { border-color: var(--color-accent); box-shadow: inset 3px 0 var(--color-accent); } .card-item span, .invoice-card span, .import-card span { color: var(--color-text-muted); font-size: 11px; } .card-item b { margin: 8px 0 14px; } .card-item small, .invoice-card small { color: var(--color-text-secondary); } .new-card { min-width: auto; color: var(--color-accent-bright); background: transparent; } .import-card, .invoice-detail { margin-top: 16px; } .import-card header, .invoice-detail header { display: flex; justify-content: space-between; align-items: start; } .import-card h2, .invoice-detail h2 { margin: 7px 0 3px; font-size: 20px; } .import-card p { margin: 0; color: var(--color-text-secondary); font-size: 12px; } .import-card header > strong { font-size: 18px; } .import-controls { display: flex; gap: 10px; align-items: center; margin-top: 22px; } .file { display: inline-flex; max-width: 360px; min-width: 240px; overflow: hidden; border: 1px dashed var(--color-border-strong); border-radius: 6px; padding: 10px; color: var(--color-text-secondary); cursor: pointer; font-size: 12px; } .file input { display: none; } .file span { overflow: hidden; color: inherit; text-overflow: ellipsis; white-space: nowrap; } .import-note { margin-top: 12px !important; color: var(--color-text-muted) !important; } .invoices { margin-top: 24px; } .invoice-card b { margin: 12px 0 8px; font-size: 18px; } .invoice-card.paid { border-color: rgba(52, 211, 153, .45); } .invoice-detail { overflow: hidden; padding: 0; } .invoice-detail header { padding: 20px; border-bottom: 1px solid var(--color-border); } .invoice-detail table { width: 100%; border-collapse: collapse; font-size: 13px; } .invoice-detail th, .invoice-detail td { padding: 13px 20px; text-align: left; border-bottom: 1px solid var(--color-border); } .invoice-detail th { color: var(--color-text-muted); font-size: 10px; font-weight: 500; } .invoice-detail tbody tr:last-child td { border-bottom: 0; } .invoice-detail small { display: block; color: var(--color-text-muted); font-size: 10px; } .category-select { border: 0; border-bottom: 1px solid var(--color-border); padding: 4px 0; color: var(--color-text-secondary); background: transparent; } .danger-button { border-color: rgba(248, 113, 113, .5); color: var(--color-danger); background: transparent; } .paid, .credit { color: var(--color-success); } @media (max-width: 1120px) { .import-controls { flex-wrap: wrap; } }
.invoice-detail header p { margin: 0; color: var(--color-text-secondary); font-size: 12px; } .payment-history { padding: 16px 20px; border-bottom: 1px solid var(--color-border); background: rgba(255, 255, 255, .018); } .payment-history h3 { margin: 0 0 10px; color: var(--color-text-secondary); font-size: 12px; font-weight: 600; } .payment-row { display: flex; align-items: center; justify-content: space-between; padding: 9px 0; border-top: 1px solid var(--color-border); font-size: 13px; } .payment-row small { margin-top: 3px; } .payment-row strong { color: var(--color-success); } .payment-modal-backdrop { position: fixed; z-index: 20; inset: 0; display: grid; place-items: center; background: rgba(7, 10, 18, .72); } .payment-modal { width: min(460px, calc(100vw - 40px)); display: grid; gap: 16px; padding: 22px; } .payment-modal header { display: flex; align-items: start; justify-content: space-between; } .payment-modal h2 { margin: 5px 0 0; font-size: 20px; } .payment-modal span, .payment-modal p { color: var(--color-text-muted); font-size: 12px; } .payment-modal fieldset { display: grid; gap: 10px; margin: 0; padding: 12px; border: 1px solid var(--color-border); border-radius: 7px; } .payment-modal legend { padding: 0 5px; color: var(--color-text-secondary); font-size: 12px; } .payment-modal fieldset label { display: flex; gap: 8px; align-items: center; font-size: 13px; } .payment-modal > label { display: grid; gap: 7px; color: var(--color-text-secondary); font-size: 12px; } .payment-modal p { margin: -2px 0 0; } .close { border: 0; color: var(--color-text-muted); background: transparent; cursor: pointer; font-size: 24px; line-height: 1; } .modal-actions { display: flex; justify-content: end; gap: 10px; }

@media (max-width: 640px) {
  .card-strip, .invoice-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
  .card-item, .new-card, .invoice-card { width: 100%; min-width: 0; padding: 12px; }
  .card-item { min-height: 112px; }
  .card-item b { margin: 7px 0 8px; }
  .new-card { min-height: 48px; place-items: center; }
  .import-card header, .invoice-detail > header { display: grid; gap: 12px; }
  .import-card header > strong { font-size: 16px; }
  .import-controls { display: grid; grid-template-columns: 1fr; gap: 9px; margin-top: 16px; }
  .import-controls > *, .file { width: 100%; max-width: none; min-width: 0; }
  .file { min-height: 44px; align-items: center; }
  .invoice-grid { grid-template-columns: 1fr 1fr; }
  .invoice-detail { overflow: hidden; }
  .invoice-detail header { padding: 16px 14px; }
  .invoice-detail h2 { font-size: 19px; }
  .invoice-actions { display: grid; grid-template-columns: 1fr; }
  .invoice-actions .button { width: 100%; }
  .payment-history { padding: 14px; }
  .payment-row { gap: 8px; }
  .payment-row > div { min-width: 0; overflow-wrap: anywhere; }
  .purchase-table-scroll { overflow-x: auto; overscroll-behavior-x: contain; -webkit-overflow-scrolling: touch; }
  .invoice-detail table { width: auto; min-width: 570px; }
  .invoice-detail th, .invoice-detail td { padding: 12px 14px; }
  .category-select { min-height: 40px; max-width: 140px; }
  .payment-modal-backdrop { z-index: 50; display: block; overflow-y: auto; padding: 0; background: var(--color-bg); }
  .payment-modal { width: 100%; min-height: 100dvh; gap: 16px; padding: max(18px, env(safe-area-inset-top)) 16px calc(24px + env(safe-area-inset-bottom)); border: 0; border-radius: 0; box-shadow: none; align-content: start; }
  .payment-modal header { position: sticky; top: calc(-1 * max(18px, env(safe-area-inset-top))); z-index: 1; margin: calc(-1 * max(18px, env(safe-area-inset-top))) -16px 0; padding: max(18px, env(safe-area-inset-top)) 16px 12px; border-bottom: 1px solid var(--color-border); background: var(--color-surface); }
  .payment-modal fieldset label { min-height: 44px; }
  .modal-actions { display: grid; grid-template-columns: 1fr; }
  .modal-actions .button { width: 100%; }
}</style>
