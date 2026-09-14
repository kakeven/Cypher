<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '@/services/api'
import { brl, formatDateBR, currentMonth, monthRange } from '@/utils/format'
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
const monthlyValues = computed(() => data.value?.monthly_evolution || [])
const chartMaximum = computed(() => Math.max(1, ...monthlyValues.value.flatMap((item) => [item.income, item.expense])))
function chartPoints(field) {
  const values = monthlyValues.value
  return values.map((item, index) => {
    const x = 2 + (index / Math.max(1, values.length - 1)) * 96
    const y = 96 - (Number(item[field]) / chartMaximum.value) * 90
    return `${x},${y}`
  }).join(' ')
}
const incomePoints = computed(() => chartPoints('income'))
const expensePoints = computed(() => chartPoints('expense'))
const chartScale = computed(() => Array.from({ length: 5 }, (_, index) => chartMaximum.value * (1 - index / 4)))
function compactCurrency(value) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', notation: 'compact', maximumFractionDigits: 0 }).format(value)
}
const categoryRanking = computed(() => [...(data.value?.by_category || [])].sort((a, b) => b.amount - a.amount))
const categoryBreakdown = computed(() => {
  const total = Number(data.value?.expense || 0)
  const items = categoryRanking.value.map((item) => ({ ...item, amount: Number(item.amount) }))
  const categorized = items.reduce((sum, item) => sum + item.amount, 0)
  const uncategorized = Math.max(0, total - categorized)
  if (uncategorized > 0.005) items.push({ id: null, name: 'Sem categoria', color: '#596273', amount: uncategorized })
  let start = 0
  return items.map((item) => {
    const percent = total ? (item.amount / total) * 100 : 0
    const slice = { ...item, percent, start }
    start += percent
    return slice
  })
})
const hoveredCategory = ref(null)
const donutCenter = computed(() => hoveredCategory.value || { name: 'Despesas', amount: Number(data.value?.expense || 0), percent: 100 })
function formatPercent(value) { return `${Number(value).toLocaleString('pt-BR', { maximumFractionDigits: 1 })}%` }
function categoryTransactionQuery(categoryId) {
  const [date_from, date_to] = monthRange(period.value)
  return { category_id: categoryId, date_from, date_to }
}
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
      <DateInput id="dashboard-period" v-model="period" type="month" :max="currentMonth()" class="month" @change="load"/>
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
            <div><span>Despesas</span><b class="negative">{{ brl(data.net_expense) }}</b></div>
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
          <header class="flow-header"><div><h2>Fluxo financeiro</h2><p>Receitas e despesas ao longo do ano.</p></div><div class="flow-legend"><span class="income"><i />Receitas</span><span class="expense"><i />Despesas</span></div></header>
          <div class="chart-layout" aria-label="Evolução mensal de receitas e despesas">
            <div class="chart-scale" aria-hidden="true"><span v-for="value in chartScale" :key="value">{{ compactCurrency(value) }}</span></div>
            <div class="graph">
              <svg viewBox="0 0 100 100" preserveAspectRatio="none" role="img">
                <line v-for="(_, index) in chartScale" :key="index" x1="0" :y1="5 + index * 22.5" x2="100" :y2="5 + index * 22.5" />
                <polyline class="income-line" :points="incomePoints" />
                <polyline class="expense-line" :points="expensePoints" />
              </svg>
            </div>
          </div>
          <div class="graph-months"><span v-for="item in monthlyValues" :key="item.month">{{ item.month.slice(5) }}</span></div>
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

        <section class="category-ranking" aria-labelledby="category-ranking-title">
          <header><div><h2 id="category-ranking-title">Gastos por categoria</h2><p>Onde seu dinheiro mais saiu neste período.</p></div><span>{{ brl(data.expense) }} em despesas</span></header>
          <p v-if="!categoryBreakdown.length" class="empty">Nenhuma despesa neste período.</p>
          <div v-else class="category-visualization">
            <ol class="category-legend">
              <li v-for="item in categoryBreakdown" :key="item.id || 'uncategorized'">
                <RouterLink v-if="item.id" :to="{ path: '/transacoes', query: categoryTransactionQuery(item.id) }" :class="{ active: hoveredCategory?.id === item.id }" :aria-label="`Ver transações de ${item.name}`" @mouseenter="hoveredCategory = item" @mouseleave="hoveredCategory = null" @focus="hoveredCategory = item" @blur="hoveredCategory = null">
                  <i :style="{ background: item.color }" /><b>{{ item.name }}</b><strong>{{ formatPercent(item.percent) }}</strong><small>{{ brl(item.amount) }}</small>
                </RouterLink>
                <div v-else :class="{ active: hoveredCategory?.id === null }" @mouseenter="hoveredCategory = item" @mouseleave="hoveredCategory = null">
                  <i :style="{ background: item.color }" /><b>{{ item.name }}</b><strong>{{ formatPercent(item.percent) }}</strong><small>{{ brl(item.amount) }}</small>
                </div>
              </li>
            </ol>
            <div class="donut-panel">
              <svg class="donut-chart" viewBox="0 0 200 200" role="img" aria-label="Distribuição de despesas por categoria" @mouseleave="hoveredCategory = null">
                <circle class="donut-track" cx="100" cy="100" r="74" />
                <circle v-for="item in categoryBreakdown" :key="item.id || 'uncategorized'" class="donut-segment" cx="100" cy="100" r="74" fill="none" :stroke="item.color" stroke-width="28" pathLength="100" :stroke-dasharray="`${item.percent} ${100 - item.percent}`" :stroke-dashoffset="-item.start" :aria-label="`${item.name}: ${formatPercent(item.percent)}`" tabindex="0" @mouseenter="hoveredCategory = item" @focus="hoveredCategory = item" @blur="hoveredCategory = null" />
              </svg>
              <div class="donut-center" aria-live="polite"><b>{{ formatPercent(donutCenter.percent) }}</b><span>{{ donutCenter.name }}</span><small>{{ brl(donutCenter.amount) }}</small></div>
            </div>
          </div>
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
.flow-header { display: flex; justify-content: space-between; align-items: start; gap: 16px; }
.flow-header p { margin: 5px 0 0; color: var(--color-text-muted); font-size: 11px; }
.flow-legend { display: flex; gap: 13px; color: var(--color-text-secondary); font-size: 11px; }
.flow-legend span { display: inline-flex; align-items: center; gap: 5px; }
.flow-legend i { width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
.flow-legend .income { color: var(--color-accent-bright); }
.flow-legend .expense { color: var(--color-danger); }
.chart-layout { display: grid; grid-template-columns: 58px 1fr; gap: 9px; height: 160px; margin-top: 14px; }
.chart-scale { display: flex; flex-direction: column; justify-content: space-between; color: var(--color-text-muted); font-size: 10px; line-height: 1; text-align: right; }
.graph { min-width: 0; min-height: 0; overflow: hidden; border-bottom: 1px solid var(--color-border); }
.graph svg { display: block; width: 100%; height: 100%; }
.graph line { stroke: rgba(255, 255, 255, 0.07); stroke-width: .5; vector-effect: non-scaling-stroke; }
.graph polyline { fill: none; stroke-width: 1.8; vector-effect: non-scaling-stroke; }
.graph .income-line { stroke: var(--color-accent-bright); }
.graph .expense-line { stroke: var(--color-danger); }
.graph-months { display: grid; grid-template-columns: repeat(12, 1fr); margin: 7px 0 0 67px; color: var(--color-text-muted); font-size: 10px; text-align: center; }
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
.category-ranking { margin-top: 12px; padding: 18px; border: 1px solid var(--color-border); border-radius: 9px; background: var(--color-surface); }
.category-ranking header { display: flex; justify-content: space-between; align-items: start; gap: 16px; }
.category-ranking h2 { margin: 0; font-size: 14px; font-weight: 600; }
.category-ranking header p { margin: 5px 0 0; color: var(--color-text-muted); font-size: 11px; }
.category-ranking header > span { color: var(--color-text-secondary); font-size: 12px; white-space: nowrap; }
.category-visualization { display: grid; grid-template-columns: minmax(260px, 1fr) minmax(260px, .8fr); align-items: center; gap: 38px; margin-top: 17px; }
.category-legend { display: grid; gap: 5px; margin: 0; padding: 0; list-style: none; }
.category-legend a, .category-legend div { display: grid; grid-template-columns: 9px minmax(0, 1fr) auto; column-gap: 9px; align-items: center; padding: 9px 10px; border-radius: 6px; color: inherit; text-decoration: none; }
.category-legend a:hover, .category-legend a:focus-visible, .category-legend .active { outline: 0; background: var(--color-surface-raised); }
.category-legend i { width: 8px; height: 8px; grid-row: span 2; border-radius: 50%; }
.category-legend b { overflow: hidden; font-size: 12px; text-overflow: ellipsis; white-space: nowrap; }
.category-legend strong { color: var(--color-text-primary); font-size: 12px; }
.category-legend small { grid-column: 2 / 4; margin-top: 2px; color: var(--color-text-secondary); font-size: 11px; }
.donut-panel { position: relative; display: grid; place-items: center; min-height: 230px; }
.donut-chart { width: min(100%, 238px); overflow: visible; transform: rotate(-90deg); }
.donut-track { fill: none; stroke: var(--color-surface-raised); stroke-width: 28; }
.donut-segment { cursor: pointer; stroke-linecap: butt; transition: opacity .16s ease, stroke-width .16s ease; }
.donut-chart:has(.donut-segment:hover) .donut-segment:not(:hover) { opacity: .35; }
.donut-segment:hover, .donut-segment:focus-visible { outline: 0; stroke-width: 32; }
.donut-center { position: absolute; display: grid; max-width: 124px; gap: 3px; text-align: center; pointer-events: none; }
.donut-center b { font-size: 25px; letter-spacing: -0.05em; }
.donut-center span { overflow: hidden; color: var(--color-text-primary); font-size: 12px; text-overflow: ellipsis; white-space: nowrap; }
.donut-center small { color: var(--color-text-secondary); font-size: 11px; }
.warning { color: var(--color-warning); }
.empty { margin: 0; padding: 20px; color: var(--color-text-secondary); text-align: center; }
@media (max-width: 1080px) { .quick-stats { grid-template-columns: repeat(2, 1fr); } .month-card { min-height: 116px; } .category-visualization { grid-template-columns: minmax(230px, 1fr) 230px; gap: 18px; } }
</style>
