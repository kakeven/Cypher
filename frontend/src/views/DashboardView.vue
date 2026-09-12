<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '@/services/api'
import { brl, formatDateBR, currentMonth } from '@/utils/format'
import DateInput from '@/components/DateInput.vue'

const period = ref(currentMonth())
const data = ref(null)
const recent = ref([])
const goals = ref([])
const receivables = ref([])
const budgets = ref([])
const error = ref('')
const loading = ref(true)

const totalSaved = computed(() => goals.value.reduce((total, item) => total + Number(item.saved_amount || 0), 0))
const totalPending = computed(() => receivables.value.reduce((total, item) => total + Number(item.remaining_amount || 0), 0))
const hasTransactions = computed(() => data.value && (data.value.income > 0 || data.value.expense > 0 || recent.value.length > 0))
const monthlyBalance = computed(() => {
  let balance = 0
  return data.value?.monthly_evolution.map((item) => {
    balance += item.income - item.expense
    return balance
  }) || []
})
const linePoints = computed(() => {
  const values = monthlyBalance.value
  if (!values.length) return ''
  const min = Math.min(0, ...values)
  const max = Math.max(1, ...values)
  const range = max - min || 1
  return values.map((value, index) => `${(index / Math.max(1, values.length - 1)) * 100},${92 - ((value - min) / range) * 78}`).join(' ')
})
const lineArea = computed(() => (linePoints.value ? `0,100 ${linePoints.value} 100,100` : ''))
const alerts = computed(() => {
  const budgetAlert = budgets.value.find((item) => item.percent >= 80)
  const receivableAlert = receivables.value.find((item) => !item.is_paid && item.remaining_amount > 0)
  return [
    budgetAlert && { label: budgetAlert.name, detail: `${budgetAlert.percent}% do orçamento usado`, type: budgetAlert.percent >= 100 ? 'negative' : 'warning' },
    receivableAlert && { label: receivableAlert.name, detail: `${brl(receivableAlert.remaining_amount)} pendentes`, type: 'positive' },
  ].filter(Boolean)
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [dashboard, latest, loadedGoals, loadedReceivables, loadedBudgets] = await Promise.all([
      api.dashboard(period.value),
      api.transactions(),
      api.goals(),
      api.receivables(),
      api.budgets(period.value),
    ])
    data.value = dashboard
    recent.value = latest.slice(0, 3)
    goals.value = loadedGoals
    receivables.value = loadedReceivables
    budgets.value = loadedBudgets
  } catch (e) {
    error.value = e.message
    data.value = null
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="dashboard-page">
    <header class="page-header dashboard-header">
      <div>
        <h1>Visão geral</h1>
        <p>Seu dinheiro em movimento, sem ruído.</p>
      </div>
      <label class="sr-only" for="dashboard-period">Período</label>
      <DateInput id="dashboard-period" v-model="period" type="month" :max="currentMonth()" class="month" @change="load" />
    </header>

    <p v-if="error" class="message" role="alert">{{ error }}</p>
    <div v-else-if="loading" class="empty" role="status" aria-live="polite">Carregando seus dados…</div>

    <template v-else-if="data">
      <section class="dashboard-summary" aria-label="Resumo financeiro">
        <article class="balance-card">
          <span>Saldo disponível</span>
          <strong :class="data.balance < 0 ? 'negative' : 'positive'">{{ brl(data.balance) }}</strong>
          <small :class="data.income >= data.expense ? 'positive' : 'negative'">{{ data.income >= data.expense ? 'Saldo positivo no mês' : 'Despesas acima das receitas' }}</small>
        </article>
        <article class="month-card">
          <header><h2>Resumo do mês</h2></header>
          <div class="quick-stats">
            <div><span>Receitas</span><b class="positive">{{ brl(data.income) }}</b></div>
            <div><span>Despesas</span><b class="negative">{{ brl(data.expense) }}</b></div>
            <div><span>Metas</span><b>{{ brl(totalSaved) }}</b></div>
            <div><span>A receber</span><b>{{ brl(totalPending) }}</b></div>
          </div>
        </article>
      </section>

      <section v-if="!hasTransactions" class="card onboarding">
        <h2>Comece pelo primeiro lançamento</h2>
        <p>Registre uma receita ou despesa para acompanhar seu saldo, orçamento e metas em um só lugar.</p>
        <RouterLink class="button" to="/transacoes">Adicionar transação</RouterLink>
      </section>

      <template v-else>
        <section class="flow-card">
          <header class="flow-header"><h2>Fluxo financeiro</h2><span>{{ period }}</span></header>
          <div class="graph" aria-label="Evolução do saldo no período">
            <svg viewBox="0 0 100 100" preserveAspectRatio="none" role="img">
              <polygon :points="lineArea" />
              <polyline :points="linePoints" />
            </svg>
          </div>
          <div class="graph-months"><span v-for="item in data.monthly_evolution" :key="item.month">{{ item.month.slice(5) }}</span></div>
        </section>

        <section class="dashboard-bottom">
          <article class="dashboard-module transactions-module">
            <header><h2>Últimas transações</h2><RouterLink to="/transacoes">Ver todas</RouterLink></header>
            <ul v-if="recent.length">
              <li v-for="item in recent" :key="item.id">
                <span class="transaction-date">{{ formatDateBR(item.date) }}</span>
                <div><b>{{ item.description || item.category_name }}</b><small>{{ item.category_name }}</small></div>
                <strong :class="item.type === 'income' ? 'positive' : 'negative'">{{ item.type === 'income' ? '+' : '-' }} {{ brl(item.amount) }}</strong>
              </li>
            </ul>
            <p v-else class="empty">Nenhuma transação registrada.</p>
          </article>

          <article class="dashboard-module alerts-module">
            <header><h2>Alertas</h2></header>
            <ul v-if="alerts.length">
              <li v-for="alert in alerts" :key="alert.label"><div><b>{{ alert.label }}</b><small>{{ alert.detail }}</small></div><span :class="alert.type">{{ alert.type === 'warning' ? 'Atenção' : alert.type === 'negative' ? 'Excedido' : 'Aberto' }}</span></li>
            </ul>
            <p v-else class="empty">Nenhum alerta no momento.</p>
          </article>
        </section>
      </template>
    </template>
  </div>
</template>

<style scoped>
.dashboard-page { max-width: 1380px; }
.dashboard-header { margin-bottom: 16px; }
.month { width: 162px; }
.dashboard-summary { display: grid; grid-template-columns: minmax(230px, 0.8fr) minmax(0, 2fr); gap: 12px; }
.balance-card, .month-card, .flow-card, .dashboard-module { border: 1px solid var(--color-border); border-radius: 9px; background: var(--color-surface); }
.balance-card { min-height: 116px; padding: 17px; border-top-color: var(--color-accent); box-shadow: inset 0 2px var(--color-accent); }
.balance-card span, .quick-stats span { color: var(--color-text-secondary); font-size: 12px; }
.balance-card strong { display: block; margin: 13px 0 4px; font-size: 28px; letter-spacing: -0.045em; }
.balance-card small { font-size: 11px; }
.month-card { padding: 14px; }
.month-card h2, .flow-card h2, .dashboard-module h2 { margin: 0; font-size: 14px; font-weight: 600; }
.quick-stats { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; margin-top: 12px; }
.quick-stats > div { min-height: 64px; padding: 9px; border: 1px solid var(--color-border); border-radius: 6px; background: var(--color-surface-raised); }
.quick-stats b { display: block; margin-top: 8px; font-size: 14px; letter-spacing: -0.02em; }
.positive { color: var(--color-success); }
.negative { color: var(--color-danger); }
.onboarding { margin-top: 12px; }
.onboarding h2 { margin: 0 0 8px; font-size: 16px; }
.onboarding p { color: var(--color-text-secondary); margin: 0 0 16px; }
.flow-card { min-height: 230px; margin-top: 12px; padding: 15px; }
.flow-header { display: flex; justify-content: space-between; align-items: center; }
.flow-header span { color: var(--color-text-muted); font-size: 11px; }
.graph { height: 160px; margin-top: 10px; border-bottom: 1px solid var(--color-border); background: repeating-linear-gradient(to bottom, transparent 0, transparent 36px, rgba(255, 255, 255, 0.045) 37px); }
.graph svg { width: 100%; height: 100%; overflow: visible; }
.graph polygon { fill: rgba(59, 130, 246, 0.12); }
.graph polyline { fill: none; stroke: var(--color-accent); stroke-width: 1.4; vector-effect: non-scaling-stroke; }
.graph-months { display: grid; grid-template-columns: repeat(12, 1fr); margin-top: 7px; color: var(--color-text-muted); font-size: 10px; text-align: center; }
.dashboard-bottom { display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(250px, 0.65fr); gap: 12px; margin-top: 12px; }
.dashboard-module { overflow: hidden; }
.dashboard-module header { display: flex; justify-content: space-between; align-items: center; padding: 12px 15px; border-bottom: 1px solid var(--color-border); }
.dashboard-module header a { color: var(--color-accent-bright); font-size: 12px; text-decoration: none; }
.dashboard-module ul { margin: 0; padding: 0 15px; list-style: none; }
.transactions-module li { display: grid; grid-template-columns: 85px 1fr auto; gap: 10px; align-items: center; padding: 10px 0; border-bottom: 1px solid var(--color-border); }
.transactions-module li:last-child, .alerts-module li:last-child { border-bottom: 0; }
.transaction-date, .transactions-module small, .alerts-module small { color: var(--color-text-muted); font-size: 11px; }
.transactions-module b, .alerts-module b { font-size: 12px; }
.transactions-module small, .alerts-module small { display: block; margin-top: 2px; }
.transactions-module strong { font-size: 12px; white-space: nowrap; }
.alerts-module li { display: flex; justify-content: space-between; gap: 12px; align-items: center; padding: 13px 0; border-bottom: 1px solid var(--color-border); }
.alerts-module span { font-size: 11px; white-space: nowrap; }
.warning { color: var(--color-warning); }
.empty { margin: 0; padding: 20px; color: var(--color-text-secondary); text-align: center; }
@media (max-width: 1080px) { .quick-stats { grid-template-columns: repeat(2, 1fr); } .month-card { min-height: 116px; } }
</style>
