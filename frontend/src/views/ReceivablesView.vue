<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api, brl } from '@/services/api'
import { useToast } from '@/composables/useToast'
import { formatDateBR, todayISO } from '@/utils/format'
import DateInput from '@/components/DateInput.vue'

const toast = useToast()
const items = ref([])
const selected = ref(null)
const error = ref('')
const loading = ref(false)
const today = todayISO()
const form = reactive({ name: '', client: '', total_amount: '', service_type: '' })
const payment = reactive({ amount: '', received_on: today, note: '' })

const totalPending = computed(() => items.value.reduce((total, item) => total + Number(item.remaining_amount), 0))
const totalReceived = computed(() => items.value.reduce((total, item) => total + Number(item.received_amount), 0))

async function load() {
  loading.value = true
  error.value = ''
  try {
    const receivables = await api.receivables()
    items.value = receivables
    if (selected.value) selected.value = await api.receivable(selected.value.id)
    else if (receivables.length) selected.value = await api.receivable(receivables[0].id)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function create() {
  error.value = ''
  try {
    const created = await api.createReceivable({ ...form, total_amount: Number(form.total_amount), client: form.client.trim() || null })
    Object.assign(form, { name: '', client: '', total_amount: '', service_type: '' })
    await load()
    await choose(created)
    toast.success('Recebível criado.')
  } catch (e) {
    error.value = e.message
  }
}

async function choose(item) {
  try {
    selected.value = await api.receivable(item.id)
  } catch (e) {
    error.value = e.message
  }
}

async function addPayment() {
  if (!selected.value) return
  error.value = ''
  try {
    await api.addReceivablePayment(selected.value.id, { ...payment, amount: Number(payment.amount), note: payment.note.trim() || null })
    Object.assign(payment, { amount: '', received_on: today, note: '' })
    await load()
    toast.success('Recebimento registrado como receita.')
  } catch (e) {
    error.value = e.message
  }
}

onMounted(load)
</script>

<template>
  <div>
    <header class="page-header">
      <div>
        <h1>Recebimentos</h1>
        <p>Controle valores combinados e cada parte que já entrou.</p>
      </div>
      <div class="summary-values">
        <span>Recebido <b>{{ brl(totalReceived) }}</b></span>
        <span>Pendente <b>{{ brl(totalPending) }}</b></span>
      </div>
    </header>

    <p v-if="error" class="message" role="alert">{{ error }}</p>

    <section class="card form">
      <h2>Novo valor a receber</h2>
      <form class="form-grid" @submit.prevent="create">
        <label>
          Projeto ou serviço
          <input v-model="form.name" class="input" maxlength="100" required placeholder="Ex.: Site da empresa" />
        </label>
        <label>
          Valor total combinado
          <input v-model="form.total_amount" class="input" type="number" min="0.01" step="0.01" required placeholder="750,00" />
        </label>
        <label>
          Cliente (opcional)
          <input v-model="form.client" class="input" maxlength="100" placeholder="Ex.: Empresa ACME" />
        </label>
        <label>
          Tipo de serviço
          <select v-model="form.service_type" class="input" required>
            <option disabled value="">Selecione</option>
            <option>Site institucional</option>
            <option>Sistema</option>
            <option>E-commerce</option>
            <option>Landing page</option>
          </select>
        </label>
        <div class="actions"><button class="button">Adicionar recebível</button></div>
      </form>
    </section>

    <div v-if="loading" class="empty" role="status">Carregando recebimentos…</div>
    <p v-else-if="!items.length" class="empty card">Cadastre um projeto ou serviço para acompanhar os pagamentos parciais.</p>

    <section v-else class="receivable-workspace">
      <aside class="receivable-list" aria-label="Projetos a receber">
        <button v-for="item in items" :key="item.id" :class="['receivable', { active: selected?.id === item.id, paid: item.is_paid }]" type="button" @click="choose(item)">
          <span class="receivable-kind">{{ item.service_type }}</span>
          <b>{{ item.name }}</b>
          <small>{{ item.client || 'Cliente não informado' }}</small>
          <strong>{{ brl(item.received_amount) }} <em>de {{ brl(item.total_amount) }}</em></strong>
          <span class="track" :aria-label="`${item.progress}% recebido`"><i :style="{ width: `${item.progress}%` }" /></span>
          <footer><span>{{ item.progress }}% recebido</span><span>{{ brl(item.remaining_amount) }} pendente</span></footer>
        </button>
      </aside>

      <section v-if="selected" class="card details">
        <header><div><span class="receivable-kind">{{ selected.service_type }}</span><h2>{{ selected.name }}</h2><p>{{ selected.client || 'Cliente não informado' }} · {{ brl(selected.remaining_amount) }} pendente</p></div></header>
        <div class="details-value"><span>Recebido</span><strong>{{ brl(selected.received_amount) }} <em>de {{ brl(selected.total_amount) }}</em></strong><div class="track"><i :style="{ width: `${selected.progress}%` }" /></div></div>
        <form v-if="!selected.is_paid" class="payment-form" @submit.prevent="addPayment">
          <label>
            Valor recebido
            <input v-model="payment.amount" class="input" type="number" min="0.01" :max="selected.remaining_amount" step="0.01" required />
          </label>
          <label>
            Data do recebimento
            <DateInput v-model="payment.received_on" :max="today" required aria-label="Data do recebimento" />
          </label>
          <label>
            Observação (opcional)
            <input v-model="payment.note" class="input" maxlength="250" placeholder="Ex.: primeira parcela" />
          </label>
          <button class="button">Registrar pagamento</button>
        </form>
        <p v-else class="paid-message">Valor total recebido.</p>
        <ul v-if="selected.payments?.length" class="payment-list">
          <li v-for="item in selected.payments" :key="item.id"><time>{{ formatDateBR(item.received_on) }}</time><span>{{ item.note || 'Recebimento confirmado' }}</span><b>{{ brl(item.amount) }}</b></li>
        </ul>
        <p v-else class="empty">Ainda não há recebimentos registrados.</p>
      </section>
    </section>
  </div>
</template>

<style scoped>
.form { margin-bottom: 18px; }
.form h2, .details h2 { margin: 0 0 18px; font-size: 16px; letter-spacing: -0.02em; }
.actions { display: flex; }
.summary-values { display: flex; gap: 18px; font-size: 12px; color: var(--color-text-secondary); }
.summary-values span { display: grid; gap: 4px; }
.summary-values b { color: var(--color-text-primary); font-family: var(--font-mono); font-size: 14px; letter-spacing: -0.05em; }
.receivables { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }
.receivable { cursor: pointer; transition: border-color 0.15s, background 0.15s; }
.receivable:hover, .receivable.active { border-color: var(--color-border-strong); background: var(--color-surface-raised); }
.receivable.paid { border-color: var(--color-success); }
.receivable-title { display: flex; justify-content: space-between; gap: 10px; }
.receivable-title h2 { margin: 0; font-size: 16px; }
.receivable-title p { margin: 5px 0 0; color: var(--color-text-muted); font-size: 12px; }
.receivable-title span { color: var(--color-accent); font-family: var(--font-mono); font-size: 10px; }
.receivable > b { display: block; margin: 20px 0 10px; font-family: var(--font-mono); font-size: 18px; letter-spacing: -0.06em; }
.receivable > b small { color: var(--color-text-secondary); font-family: var(--font-family); font-size: 12px; font-weight: 400; letter-spacing: normal; }
.track { height: 7px; overflow: hidden; border-radius: 8px; background: var(--color-surface-raised); }
.track i { display: block; height: 100%; background: var(--color-accent); }
.receivable footer { display: flex; justify-content: space-between; margin-top: 10px; color: var(--color-text-secondary); font-size: 12px; }
.receivable footer strong { color: var(--color-text-primary); font-weight: 500; }
.details { margin-top: 18px; }
.details header { display: flex; justify-content: space-between; align-items: start; }
.details header p { margin: -10px 0 18px; color: var(--color-text-secondary); font-size: 13px; }
.link { border: 0; background: none; color: var(--color-accent); cursor: pointer; font-size: 13px; }
.link:hover { color: var(--color-accent-bright); text-decoration: underline; text-underline-offset: 3px; }
.payment-form { display: grid; grid-template-columns: 1fr 1fr 2fr auto; gap: 10px; align-items: end; }
.payment-form label { display: grid; gap: 7px; color: var(--color-text-secondary); font-size: 13px; }
.payment-list { margin: 22px 0 0; padding: 0; list-style: none; }
.payment-list li { display: flex; justify-content: space-between; padding: 12px 0; border-top: 1px solid var(--color-border); color: var(--color-text-secondary); font-size: 13px; }
.payment-list small { color: var(--color-text-muted); }
.payment-list b { color: var(--color-success); font-family: var(--font-mono); letter-spacing: -0.04em; }
.paid-message { color: var(--color-success); }

.form { margin-bottom: 12px; }
.summary-values { gap: 12px; }
.summary-values span { min-width: 118px; padding: 9px 11px; border: 1px solid var(--color-border); border-radius: 6px; background: var(--color-surface); }
.summary-values b { color: var(--color-text-primary); font-family: var(--font-family); font-size: 13px; letter-spacing: -0.02em; }
.receivable-workspace { display: grid; grid-template-columns: minmax(260px, 0.72fr) minmax(0, 1.4fr); gap: 12px; }
.receivable-list { display: grid; align-content: start; gap: 8px; }
.receivable {
  width: 100%;
  padding: 15px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  color: var(--color-text-primary);
  text-align: left;
  background: var(--color-surface);
  cursor: pointer;
}
.receivable:hover, .receivable.active { border-color: var(--color-border-strong); background: var(--color-surface-raised); }
.receivable.active { box-shadow: inset 3px 0 var(--color-accent); }
.receivable.paid { border-color: var(--color-success); }
.receivable-kind { display: inline-block; padding: 3px 6px; border-radius: 4px; color: var(--color-accent-bright); background: var(--color-accent-bg); font-size: 10px; }
.receivable > b { display: block; margin: 11px 0 3px; font-size: 15px; }
.receivable > small { display: block; color: var(--color-text-muted); font-size: 11px; }
.receivable > strong { display: block; margin: 16px 0 8px; font-size: 18px; letter-spacing: -0.035em; }
.receivable > strong em, .details-value em { color: var(--color-text-secondary); font-size: 11px; font-style: normal; font-weight: 400; letter-spacing: 0; }
.receivable .track { display: block; }
.receivable footer { display: flex; justify-content: space-between; gap: 6px; margin-top: 9px; color: var(--color-text-secondary); font-size: 10px; }
.details { min-height: 100%; margin: 0; padding: 0; overflow: hidden; }
.details > header { padding: 20px; border-bottom: 1px solid var(--color-border); }
.details > header h2 { margin: 10px 0 4px; font-size: 19px; }
.details > header p { margin: 0; color: var(--color-text-secondary); font-size: 12px; }
.details-value { padding: 18px 20px; border-bottom: 1px solid var(--color-border); }
.details-value > span { color: var(--color-text-secondary); font-size: 11px; }
.details-value strong { display: block; margin: 6px 0 12px; font-size: 24px; letter-spacing: -0.04em; }
.details .track { background: var(--color-surface-raised); }
.details .track i { background: var(--color-accent); }
.payment-form { padding: 18px 20px; grid-template-columns: 1fr 1fr 1.5fr auto; border-bottom: 1px solid var(--color-border); background: var(--color-surface-raised); }
.payment-form .button { align-self: end; }
.payment-list { margin: 0; padding: 0 20px; }
.payment-list li { display: grid; grid-template-columns: 110px 1fr auto; gap: 12px; align-items: center; padding: 13px 0; color: var(--color-text-secondary); }
.payment-list time { color: var(--color-text-muted); font-size: 11px; }
.payment-list b { color: var(--color-success); font-family: var(--font-family); font-size: 13px; }
@media (max-width: 1120px) { .receivable-workspace { grid-template-columns: 1fr; } .receivable-list { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
</style>
