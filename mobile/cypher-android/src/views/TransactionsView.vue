<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api, brl } from '@/services/api'
import { useTransactionsStore } from '@/stores/transactions'
import { useToast } from '@/composables/useToast'
import { todayISO, currentMonth, monthRange, formatDateBR } from '@/utils/format'
import DateInput from '@/components/DateInput.vue'
import DateRangePicker from '@/components/DateRangePicker.vue'

const store = useTransactionsStore()
const route = useRoute()
const toast = useToast()
const categories = ref([])
const categoriesError = ref('')
const formError = ref('')
const editingId = ref(null)
const showForm = ref(window.innerWidth > 640)
const today = todayISO()
const currentMonthValue = currentMonth()

const emptyForm = () => ({ date: today, type: 'expense', amount: '', category_id: '', description: '' })
const form = reactive(emptyForm())
const filters = reactive({ type: '', category_id: '', date_from: '', date_to: '' })

const filterActive = computed(() => Boolean(filters.type || filters.category_id || filters.date_from || filters.date_to))

function payload() {
  return {
    date: form.date,
    type: form.type,
    amount: Number(form.amount),
    category_id: form.type === 'expense' ? Number(form.category_id) : null,
    description: form.description?.trim() || null,
  }
}

function applyFilters() {
  store.load({ ...filters })
}

function clearFilters() {
  filters.type = ''
  filters.category_id = ''
  filters.date_from = ''
  filters.date_to = ''
  store.load()
}

async function save() {
  formError.value = ''
  try {
    if (editingId.value) {
      await store.update(editingId.value, payload())
      toast.success('Transação atualizada.')
    } else {
      await store.create(payload())
      toast.success('Transação adicionada.')
    }
    resetForm()
    if (window.innerWidth <= 640) showForm.value = false
  } catch (e) {
    formError.value = e.message
  }
}

function startEdit(item) {
  showForm.value = true
  editingId.value = item.id
  form.date = item.date
  form.type = item.type
  form.amount = item.amount
  form.category_id = item.category_id
  form.description = item.description || ''
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function resetForm() {
  editingId.value = null
  Object.assign(form, emptyForm())
  formError.value = ''
}

function closeForm() {
  resetForm()
  if (window.innerWidth <= 640) showForm.value = false
}

const contextMenu = ref(null)
function openContextMenu(event, item) {
  contextMenu.value = { item, x: Math.min(event.clientX, window.innerWidth - 168), y: Math.min(event.clientY, window.innerHeight - 100) }
}
function closeContextMenu() { contextMenu.value = null }
function editTransaction() {
  const item = contextMenu.value?.item
  if (!item) return
  closeContextMenu()
  startEdit(item)
}
async function deleteTransaction() {
  const item = contextMenu.value?.item
  closeContextMenu()
  if (!item || !window.confirm(`Excluir a transação “${item.description || item.category_name}”?`)) return
  try {
    await store.remove(item.id)
    toast.success('Transação excluída.')
  } catch (e) {
    formError.value = e.message
  }
}

function setMonth(value) {
  const [from, to] = monthRange(value)
  filters.date_from = from
  filters.date_to = to
  applyFilters()
}

onMounted(async () => {
  try {
    categories.value = await api.categories()
  } catch (e) {
    categoriesError.value = e.message
  }
  filters.category_id = route.query.category_id || ''
  filters.date_from = route.query.date_from || ''
  filters.date_to = route.query.date_to || ''
  filters.type = route.query.type || ''
  await store.load({ ...filters })
  window.addEventListener('click', closeContextMenu)
  window.addEventListener('scroll', closeContextMenu, true)
})

onBeforeUnmount(() => {
  window.removeEventListener('click', closeContextMenu)
  window.removeEventListener('scroll', closeContextMenu, true)
})
</script>

<template>
  <div class="transactions-page">
    <header class="page-header">
      <div>
        <h1>Transações</h1>
        <p>Registre e acompanhe cada entrada e saída.</p>
      </div>
      <button type="button" class="button mobile-new" @click="showForm = true">Nova</button>
    </header>

    <p v-if="categoriesError" class="message" role="alert">{{ categoriesError }}</p>

    <div v-if="showForm || editingId" class="form-modal" @click.self="closeForm">
    <section class="card form" @click.stop>
      <div class="form-heading"><h2>{{ editingId ? 'Editar transação' : 'Nova transação' }}</h2><button type="button" class="form-close" aria-label="Fechar formulário" @click="closeForm">×</button></div>
      <form class="form-grid" @submit.prevent="save">
        <label>
          Tipo
          <select v-model="form.type" class="input">
            <option value="expense">Despesa</option>
            <option value="income">Receita</option>
          </select>
        </label>
        <label>
          Valor
          <input v-model="form.amount" class="input" type="number" min="0.01" step="0.01" required aria-required="true" />
        </label>
        <label>
          Data
          <DateInput v-model="form.date" required :max="today" aria-label="Data da transação" />
        </label>
        <label v-if="form.type === 'expense'">
          Categoria
          <select v-model="form.category_id" required class="input" aria-required="true">
            <option disabled value="">Selecione</option>
            <option v-for="category in categories" :key="category.id" :value="category.id">
              {{ category.name }}
            </option>
          </select>
        </label>
        <label class="full">
          Descrição (opcional)
          <input v-model="form.description" class="input" maxlength="250" />
        </label>
        <p v-if="formError" class="message message--inline" role="alert">{{ formError }}</p>
        <div class="actions">
          <button class="button">{{ editingId ? 'Salvar alterações' : 'Adicionar transação' }}</button>
          <button v-if="editingId" type="button" class="button button--ghost" @click="closeForm">Cancelar</button>
        </div>
      </form>
    </section>
    </div>

    <section class="card list">
      <div class="list-header">
        <div class="history-heading">
          <h2>Histórico</h2>
          <p>Use o botão direito em um lançamento para editar ou excluir.</p>
        </div>
        <div class="filters">
          <label class="sr-only" for="filter-type">Filtrar por tipo</label>
          <select id="filter-type" v-model="filters.type" class="input" @change="applyFilters">
            <option value="">Tipos</option>
            <option value="income">Receitas</option>
            <option value="expense">Despesas</option>
          </select>
          <label class="sr-only" for="filter-category">Filtrar por categoria</label>
          <select id="filter-category" v-model="filters.category_id" class="input" @change="applyFilters">
            <option value="">Categorias</option>
            <option v-for="category in categories" :key="category.id" :value="category.id">
              {{ category.name }}
            </option>
          </select>
          <DateRangePicker v-model:start="filters.date_from" v-model:end="filters.date_to" :max="today" compact @change="applyFilters" />
          <button v-if="filterActive" type="button" class="button button--ghost" @click="clearFilters">Limpar</button>
        </div>
      </div>
      <div class="quick-ranges">
        <button type="button" class="chip" @click="setMonth(currentMonthValue)">Este mês</button>
        <button type="button" class="chip" @click="clearFilters">Tudo</button>
      </div>
      <div v-if="store.loading" class="empty" role="status" aria-live="polite">Carregando…</div>
      <p v-else-if="store.error" class="message" role="alert">{{ store.error }}</p>
      <p v-else-if="!store.items.length" class="empty" role="status">Nenhuma transação encontrada.</p>
      <table v-else>
        <caption class="sr-only">Lista de transações registradas</caption>
        <thead>
          <tr>
            <th scope="col">Data</th>
            <th scope="col">Descrição</th>
            <th scope="col">Categoria</th>
            <th scope="col">Tipo</th>
            <th scope="col" class="amount">Valor</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in store.items" :key="item.id" @contextmenu.prevent="openContextMenu($event, item)">
            <td><time>{{ formatDateBR(item.date) }}</time></td>
            <td class="description-cell">{{ item.description || 'Sem descrição' }}</td>
            <td class="category-cell">{{ item.type === 'expense' ? item.category_name : '—' }}</td>
            <td><span :class="['type-tag', item.type]">{{ item.type === 'income' ? 'Receita' : 'Despesa' }}</span></td>
            <td class="amount" :class="item.type === 'income' ? 'positive' : 'negative'">
              <span :aria-label="item.type === 'income' ? 'Receita de' : 'Despesa de'">{{ item.type === 'income' ? '+' : '-' }} {{ brl(item.amount) }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </section>
    <div v-if="contextMenu" class="context-menu" :style="{ left: `${contextMenu.x}px`, top: `${contextMenu.y}px` }" role="menu" @click.stop>
      <button type="button" role="menuitem" @click="editTransaction">Editar</button>
      <button type="button" class="danger" role="menuitem" @click="deleteTransaction">Excluir</button>
    </div>
  </div>
</template>

<style scoped>
.form, .list { margin-bottom: 18px; }
.form-modal { display: contents; }
.form h2 { font-size: 16px; margin: 0 0 18px; letter-spacing: -0.02em; }
.form-heading { display: flex; justify-content: space-between; align-items: center; }
.form-close, .mobile-new { display: none; }
.list { padding: 0; overflow: hidden; border-color: var(--color-border-strong); box-shadow: none; }
.actions { display: flex; gap: 10px; }
.message--inline { grid-column: 1 / -1; margin: 4px 0 0; }
.list-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 18px; padding: 18px 20px 14px; }
.history-heading h2 { margin: 0; font-size: 16px; letter-spacing: -0.02em; }
.history-heading p { margin: 5px 0 0; color: var(--color-text-muted); font-size: 11px; }
.filters { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.filters .input { width: auto; min-width: 140px; }
.quick-ranges { display: flex; gap: 6px; margin: 0; padding: 0 20px 14px; border-bottom: 1px solid var(--color-border); }
.chip { background: transparent; border: 1px solid transparent; color: var(--color-text-secondary); padding: 5px 9px; border-radius: 5px; font-size: 11px; cursor: pointer; }
.chip:hover { color: var(--color-accent-bright); border-color: var(--color-accent); background: var(--color-accent-bg); }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { padding: 14px 20px; border-bottom: 1px solid var(--color-border); text-align: left; }
th { color: var(--color-text-muted); background: rgba(255, 255, 255, 0.015); font-size: 10px; font-weight: var(--font-weight-medium); letter-spacing: 0.025em; }
tbody tr { transition: background 0.14s ease, box-shadow 0.14s ease; }
tbody tr:hover { background: var(--color-surface-raised); box-shadow: inset 2px 0 var(--color-accent); }
tbody tr:last-child td { border-bottom: 0; }
td time { color: var(--color-text-secondary); font-variant-numeric: tabular-nums; font-size: 12px; }
.description-cell { color: var(--color-text-primary); font-weight: 520; }
.category-cell { color: var(--color-text-secondary); }
.type-tag { display: inline-flex; padding: 3px 7px; border: 1px solid currentColor; border-radius: 4px; font-size: 10px; font-weight: 600; line-height: 1.2; }
.type-tag.income { color: var(--color-success); background: color-mix(in srgb, var(--color-success) 8%, transparent); }
.type-tag.expense { color: var(--color-danger); background: color-mix(in srgb, var(--color-danger) 8%, transparent); }
th.amount, td.amount { text-align: right; }
.context-menu { position: fixed; z-index: 10; display: grid; width: 160px; padding: 4px; border: 1px solid var(--color-border-strong); border-radius: 7px; background: var(--color-surface-raised); box-shadow: 0 10px 30px rgba(0, 0, 0, 0.28); }
.context-menu button { border: 0; border-radius: 4px; padding: 8px 10px; color: var(--color-text-primary); text-align: left; background: transparent; cursor: pointer; font-size: 13px; }
.context-menu button:hover { background: var(--color-surface); }
.context-menu .danger { color: var(--color-danger); }
.positive { color: var(--color-success); }
.negative { color: var(--color-danger); }
@media (max-width: 1100px) { .list-header { align-items: start; } th, td { padding-left: 14px; padding-right: 14px; } .quick-ranges { padding-left: 14px; } }
@media (max-width: 640px) {
  .transactions-page { display: flex; height: calc(100dvh - 116px); min-height: 0; flex-direction: column; overflow: hidden; overscroll-behavior: none; }
  .transactions-page > .page-header { flex: 0 0 auto; }
  .mobile-new { display: inline-flex; min-height: 36px; padding: 7px 14px; align-items: center; }
  .form-modal { position: fixed; z-index: 30; inset: 0; display: flex; align-items: center; padding: 14px; background: rgba(2, 7, 14, .7); backdrop-filter: blur(4px); }
  .form { width: 100%; max-height: min(680px, calc(100dvh - 28px)); margin: 0; padding: 18px 14px max(18px, env(safe-area-inset-bottom)); overflow-y: auto; border-color: var(--color-border-strong); border-radius: 16px; box-shadow: 0 -16px 42px rgba(0, 0, 0, .36); }
  .form-heading h2 { margin-bottom: 14px; }
  .form-close { display: block; width: 32px; height: 32px; border: 0; border-radius: 50%; color: var(--color-text-secondary); background: var(--color-surface-raised); font-size: 23px; line-height: 1; }
  .actions .button { flex: 1; }
  .list { display: flex; min-height: 0; flex: 1 1 auto; flex-direction: column; margin-bottom: 0; border-radius: 12px; overflow: hidden; }
  .list-header { padding: 14px 14px 8px; }
  .history-heading p { display: none; }
  .filters { width: 100%; flex-wrap: wrap; overflow: visible; padding-bottom: 4px; }
  .filters .input { flex: 1 1 0; min-width: 0; }
  .quick-ranges { padding: 0 14px 10px; }
  table { display: block; min-height: 0; flex: 1 1 auto; overflow: hidden; }
  tbody { display: block; height: 100%; overflow-y: auto; overscroll-behavior: contain; -webkit-overflow-scrolling: touch; }
  thead { display: none; }
  tbody { padding: 0 14px 4px; }
  tbody tr { display: grid; grid-template-columns: 1fr auto; gap: 3px 12px; padding: 12px 0; border-bottom: 1px solid var(--color-border); }
  tbody tr:last-child { border-bottom: 0; }
  td { display: none; padding: 0; border: 0; }
  td.description-cell, td.amount, td.category-cell { display: block; }
  td.description-cell { grid-column: 1; grid-row: 1; font-size: 13px; }
  td.category-cell { grid-column: 1; grid-row: 2; font-size: 11px; }
  td.amount { grid-column: 2; grid-row: 1 / span 2; align-self: center; font-size: 13px; }
}
</style>
