<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { api, brl } from '@/services/api'
import { useToast } from '@/composables/useToast'
import { currentMonth, formatDateBR, todayISO } from '@/utils/format'
import DateInput from '@/components/DateInput.vue'

const toast = useToast()
const categories = ref([])
const recurring = ref([])
const occurrences = ref([])
const summary = ref(null)
const error = ref('')
const loading = ref(false)
const period = ref(currentMonth())
const today = todayISO()
const editingId = ref(null)
const contextMenu = ref(null)
const filters = reactive({ type: '', status: '' })
const form = reactive({ name: '', type: 'expense', amount: '', category_id: '', frequency: 'monthly', interval: 1, day_of_month: String(new Date().getDate()), day_of_week: String(new Date().getDay() === 0 ? 6 : new Date().getDay() - 1), start_date: today, end_date: '' })

const pending = computed(() => occurrences.value.filter((item) => item.status === 'pending'))

function payload() {
  return {
    name: form.name.trim(), type: form.type, amount: Number(form.amount), category_id: Number(form.category_id), frequency: form.frequency, interval: Number(form.interval),
    day_of_month: form.frequency === 'monthly' ? Number(form.day_of_month) : null,
    day_of_week: form.frequency === 'weekly' ? Number(form.day_of_week) : null,
    start_date: form.start_date, end_date: form.end_date || null,
  }
}

function reset() {
  editingId.value = null
  Object.assign(form, { name: '', type: 'expense', amount: '', category_id: '', frequency: 'monthly', interval: 1, day_of_month: String(new Date().getDate()), day_of_week: String(new Date().getDay() === 0 ? 6 : new Date().getDay() - 1), start_date: today, end_date: '' })
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const occurrenceParams = { period: period.value }
    if (filters.type) occurrenceParams.type = filters.type
    if (filters.status) occurrenceParams.status = filters.status
    const [loadedRecurring, loadedOccurrences, loadedSummary] = await Promise.all([api.recurringTransactions(), api.occurrences(occurrenceParams), api.occurrenceSummary(period.value)])
    recurring.value = loadedRecurring
    occurrences.value = loadedOccurrences
    summary.value = loadedSummary
  } catch (e) { error.value = e.message } finally { loading.value = false }
}

async function save() {
  error.value = ''
  try {
    if (editingId.value) await api.updateRecurringTransaction(editingId.value, payload())
    else await api.createRecurringTransaction(payload())
    toast.success(editingId.value ? 'Recorrência atualizada.' : 'Recorrência criada.')
    reset(); await load()
  } catch (e) { error.value = e.message }
}

function edit(item) {
  editingId.value = item.id
  Object.assign(form, { ...item, amount: item.amount, category_id: String(item.category_id), day_of_month: item.day_of_month ? String(item.day_of_month) : '', day_of_week: item.day_of_week === null ? '' : String(item.day_of_week), end_date: item.end_date || '' })
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function generate(item) {
  try { const created = await api.generateOccurrences(item.id); toast.success(created.length ? `${created.length} ocorrências geradas.` : 'A agenda já está atualizada.'); await load() } catch (e) { error.value = e.message }
}
async function toggle(item) {
  try { await (item.is_active ? api.pauseRecurringTransaction(item.id) : api.resumeRecurringTransaction(item.id)); toast.success(item.is_active ? 'Recorrência pausada.' : 'Recorrência reativada.'); await load() } catch (e) { error.value = e.message }
}
async function remove(item) {
  if (!window.confirm(`Excluir a recorrência “${item.name}”? Ocorrências já confirmadas serão preservadas.`)) return
  try { await api.deleteRecurringTransaction(item.id); toast.success('Recorrência excluída.'); await load() } catch (e) { error.value = e.message }
}
function openContextMenu(event, item) { contextMenu.value = { item, x: Math.min(event.clientX, window.innerWidth - 168), y: Math.min(event.clientY, window.innerHeight - 100) } }
function closeContextMenu() { contextMenu.value = null }
function editRecurring() {
  const item = contextMenu.value?.item
  if (!item) return
  closeContextMenu()
  edit(item)
}
async function deleteRecurring() {
  const item = contextMenu.value?.item
  closeContextMenu()
  if (item) await remove(item)
}
async function confirm(item) {
  try { await api.confirmOccurrence(item.id); toast.success(item.type === 'income' ? 'Recebimento confirmado como receita.' : 'Pagamento confirmado como despesa.'); await load() } catch (e) { error.value = e.message }
}

onMounted(async () => {
  try { categories.value = await api.categories() } catch (e) { error.value = e.message }
  await load()
  window.addEventListener('click', closeContextMenu)
  window.addEventListener('scroll', closeContextMenu, true)
})

onBeforeUnmount(() => {
  window.removeEventListener('click', closeContextMenu)
  window.removeEventListener('scroll', closeContextMenu, true)
})
</script>

<template>
  <div>
    <header class="page-header"><div><h1>Agenda e recorrências</h1><p>Planeje compromissos; o saldo só muda quando você confirma.</p></div></header>
    <p v-if="error" class="message" role="alert">{{ error }}</p>

    <section class="card form-card">
      <h2>{{ editingId ? 'Editar recorrência' : 'Nova recorrência' }}</h2>
      <form class="form-grid" @submit.prevent="save">
        <label>Nome<input v-model="form.name" class="input" maxlength="100" required placeholder="Ex.: Aluguel" /></label>
        <label>Tipo<select v-model="form.type" class="input"><option value="expense">Despesa</option><option value="income">Receita</option></select></label>
        <label>Valor<input v-model="form.amount" class="input" type="number" min="0.01" step="0.01" required /></label>
        <label>Categoria<select v-model="form.category_id" class="input" required><option disabled value="">Selecione</option><option v-for="category in categories" :key="category.id" :value="String(category.id)">{{ category.name }}</option></select></label>
        <label>Frequência<select v-model="form.frequency" class="input"><option value="monthly">Mensal</option><option value="weekly">Semanal</option><option value="yearly">Anual</option><option value="daily">Diária</option></select></label>
        <label>Repetir a cada<input v-model="form.interval" class="input" type="number" min="1" max="365" required /></label>
        <label v-if="form.frequency === 'monthly'">Dia do mês<input v-model="form.day_of_month" class="input" type="number" min="1" max="31" required /></label>
        <label v-if="form.frequency === 'weekly'">Dia da semana<select v-model="form.day_of_week" class="input"><option value="0">Segunda</option><option value="1">Terça</option><option value="2">Quarta</option><option value="3">Quinta</option><option value="4">Sexta</option><option value="5">Sábado</option><option value="6">Domingo</option></select></label>
        <label>Começa em<DateInput v-model="form.start_date" required /></label>
        <label>Termina em (opcional)<DateInput v-model="form.end_date" :min="form.start_date" /></label>
        <div class="actions full"><button class="button">{{ editingId ? 'Salvar alterações' : 'Criar recorrência' }}</button><button v-if="editingId" type="button" class="button button--ghost" @click="reset">Cancelar</button></div>
      </form>
    </section>

    <section class="recurring-section">
      <header><h2>Suas recorrências</h2></header>
      <div v-if="loading" class="empty">Carregando…</div>
      <p v-else-if="!recurring.length" class="empty card">Nenhuma recorrência cadastrada.</p>
      <div v-else class="recurring-grid">
        <article v-for="item in recurring" :key="item.id" class="card recurring-card" @contextmenu.prevent="openContextMenu($event, item)">
          <span :class="item.is_active ? 'active' : 'paused'">{{ item.is_active ? 'Ativa' : 'Pausada' }}</span><h3>{{ item.name }}</h3>
          <p>{{ item.type === 'income' ? 'Receita' : 'Despesa' }} de <b>{{ brl(item.amount) }}</b></p>
          <small>{{ item.frequency === 'monthly' ? `Todo dia ${item.day_of_month}` : item.frequency === 'weekly' ? 'Semanal' : item.frequency === 'yearly' ? 'Anual' : 'Diária' }}</small>
          <div><button class="link" @click="generate(item)">Gerar 12 meses</button><button class="link" @click="edit(item)">Editar</button><button class="link" @click="toggle(item)">{{ item.is_active ? 'Pausar' : 'Reativar' }}</button><button class="link danger" @click="remove(item)">Excluir</button></div>
        </article>
      </div>
    </section>

    <section class="agenda"><header class="agenda-header"><div><h2>Agenda financeira</h2><p>{{ pending.length }} pendência(s) neste mês.</p></div><div class="filters"><DateInput v-model="period" type="month" @change="load" /><select v-model="filters.type" class="input" @change="load"><option value="">Todos os tipos</option><option value="expense">Despesas</option><option value="income">Receitas</option></select><select v-model="filters.status" class="input" @change="load"><option value="">Todos os estados</option><option value="pending">Pendentes</option><option value="paid">Pagas</option><option value="received">Recebidas</option></select></div></header>
      <div v-if="summary" class="summary"><span>Despesas previstas <b class="negative">{{ brl(summary.expense_expected) }}</b></span><span>Receitas previstas <b class="positive">{{ brl(summary.income_expected) }}</b></span></div>
      <div v-if="!occurrences.length" class="empty card">Não há ocorrências para este período.</div><ul v-else class="occurrence-list"><li v-for="item in occurrences" :key="item.id"><time>{{ formatDateBR(item.due_date) }}</time><div><b>{{ item.recurring_name }}</b><small>{{ item.status === 'pending' ? 'Aguardando confirmação' : item.status === 'paid' ? 'Pago' : 'Recebido' }}</small></div><strong :class="item.type === 'income' ? 'positive' : 'negative'">{{ item.type === 'income' ? '+' : '-' }} {{ brl(item.amount) }}</strong><button v-if="item.status === 'pending' && item.due_date <= today" class="button" @click="confirm(item)">{{ item.type === 'income' ? 'Confirmar receita' : 'Confirmar pagamento' }}</button><span v-else-if="item.status === 'pending'" class="future">Programado</span></li></ul>
    </section>
    <div v-if="contextMenu" class="context-menu" :style="{ left: `${contextMenu.x}px`, top: `${contextMenu.y}px` }" role="menu" @click.stop>
      <button type="button" role="menuitem" @click="editRecurring">Editar</button>
      <button type="button" class="danger" role="menuitem" @click="deleteRecurring">Excluir</button>
    </div>
  </div>
</template>

<style scoped>
.form-card h2, .recurring-section h2, .agenda h2 { margin: 0 0 16px; font-size: 16px; } .actions { display: flex; gap: 8px; } .recurring-section, .agenda { margin-top: 22px; } .recurring-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; } .recurring-card { position: relative; padding: 16px; } .recurring-card h3 { margin: 16px 0 7px; font-size: 16px; } .recurring-card p { margin: 0 0 5px; color: var(--color-text-secondary); font-size: 13px; } .recurring-card small { color: var(--color-text-muted); } .recurring-card div { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 16px; } .active, .paused { position: absolute; top: 14px; right: 14px; font-size: 10px; } .active { color: var(--color-success); } .paused { color: var(--color-warning); } .link { padding: 0; border: 0; background: none; color: var(--color-accent-bright); cursor: pointer; font-size: 12px; } .danger { color: var(--color-danger); } .agenda-header { display: flex; justify-content: space-between; gap: 16px; align-items: start; } .agenda-header p { margin: -10px 0 0; color: var(--color-text-secondary); font-size: 12px; } .filters { display: flex; gap: 8px; } .filters .input { padding: 7px; } .summary { display: flex; gap: 12px; margin: 14px 0; } .summary span { padding: 10px 12px; border: 1px solid var(--color-border); border-radius: 7px; color: var(--color-text-secondary); font-size: 12px; } .summary b { display: block; margin-top: 4px; font-size: 15px; } .occurrence-list { margin: 0; padding: 0; list-style: none; border: 1px solid var(--color-border); border-radius: 9px; overflow: hidden; } .occurrence-list li { display: grid; grid-template-columns: 94px 1fr auto auto; align-items: center; gap: 15px; padding: 13px 15px; border-bottom: 1px solid var(--color-border); background: var(--color-surface); } .occurrence-list li:last-child { border-bottom: 0; } time, small, .future { color: var(--color-text-muted); font-size: 12px; } .occurrence-list small { display: block; margin-top: 3px; } .occurrence-list strong { font-size: 13px; white-space: nowrap; } .positive { color: var(--color-success); } .negative { color: var(--color-danger); } .occurrence-list .button { padding: 7px 10px; font-size: 12px; } .context-menu { position: fixed; z-index: 10; display: grid; width: 160px; padding: 4px; border: 1px solid var(--color-border-strong); border-radius: 7px; background: var(--color-surface-raised); box-shadow: 0 10px 30px rgba(0, 0, 0, 0.28); } .context-menu button { border: 0; border-radius: 4px; padding: 8px 10px; color: var(--color-text-primary); text-align: left; background: transparent; cursor: pointer; font-size: 13px; } .context-menu button:hover { background: var(--color-surface); } .context-menu .danger { color: var(--color-danger); } @media (max-width: 1150px) { .recurring-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
</style>
