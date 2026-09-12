<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api, brl } from '@/services/api'
import { useTransactionsStore } from '@/stores/transactions'
import { useToast } from '@/composables/useToast'
import { todayISO, currentMonth, monthRange, formatDateBR } from '@/utils/format'
import DateInput from '@/components/DateInput.vue'

const store = useTransactionsStore()
const toast = useToast()
const categories = ref([])
const categoriesError = ref('')
const formError = ref('')
const editingId = ref(null)
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
    category_id: Number(form.category_id),
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
  } catch (e) {
    formError.value = e.message
  }
}

function startEdit(item) {
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

const pendingDelete = ref(null)
function askRemove(item) {
  pendingDelete.value = item.id
}
function cancelRemove() {
  pendingDelete.value = null
}
async function confirmRemove(item) {
  try {
    await store.remove(item.id)
    pendingDelete.value = null
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
  await store.load()
})
</script>

<template>
  <div>
    <header class="page-header">
      <div>
        <h1>Transações</h1>
        <p>Registre e acompanhe cada entrada e saída.</p>
      </div>
    </header>

    <p v-if="categoriesError" class="message" role="alert">{{ categoriesError }}</p>

    <section class="card form">
      <h2>{{ editingId ? 'Editar transação' : 'Nova transação' }}</h2>
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
        <label>
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
          <button v-if="editingId" type="button" class="button button--ghost" @click="resetForm">Cancelar</button>
        </div>
      </form>
    </section>

    <section class="card list">
      <div class="list-header">
        <h2>Histórico</h2>
        <div class="filters">
          <label class="sr-only" for="filter-type">Filtrar por tipo</label>
          <select id="filter-type" v-model="filters.type" class="input" @change="applyFilters">
            <option value="">Todos os tipos</option>
            <option value="income">Receitas</option>
            <option value="expense">Despesas</option>
          </select>
          <label class="sr-only" for="filter-category">Filtrar por categoria</label>
          <select id="filter-category" v-model="filters.category_id" class="input" @change="applyFilters">
            <option value="">Todas categorias</option>
            <option v-for="category in categories" :key="category.id" :value="category.id">
              {{ category.name }}
            </option>
          </select>
          <label class="sr-only" for="filter-from">Data inicial</label>
          <DateInput id="filter-from" v-model="filters.date_from" :max="filters.date_to || today" aria-label="Data inicial" @change="applyFilters" />
          <label class="sr-only" for="filter-to">Data final</label>
          <DateInput id="filter-to" v-model="filters.date_to" :min="filters.date_from" :max="today" aria-label="Data final" @change="applyFilters" />
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
            <th scope="col"><span class="sr-only">Ações</span></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in store.items" :key="item.id">
            <td>{{ formatDateBR(item.date) }}</td>
            <td>{{ item.description || 'Sem descrição' }}</td>
            <td>{{ item.category_name }}</td>
            <td>{{ item.type === 'income' ? 'Receita' : 'Despesa' }}</td>
            <td class="amount" :class="item.type === 'income' ? 'positive' : 'negative'">
              <span :aria-label="item.type === 'income' ? 'Receita de' : 'Despesa de'">{{ item.type === 'income' ? '+' : '-' }} {{ brl(item.amount) }}</span>
            </td>
            <td class="row-actions">
              <template v-if="pendingDelete === item.id">
                <button class="link link--danger" @click="confirmRemove(item)">Confirmar exclusão</button>
                <button class="link" @click="cancelRemove">Cancelar</button>
              </template>
              <template v-else>
                <button class="link" :aria-label="`Editar transação ${item.description || item.category_name}`" @click="startEdit(item)">Editar</button>
                <button class="link link--danger" :aria-label="`Excluir transação ${item.description || item.category_name}`" @click="askRemove(item)">Excluir</button>
              </template>
            </td>
          </tr>
        </tbody>
      </table>
    </section>
  </div>
</template>

<style scoped>
.form, .list { margin-bottom: 18px; }
.form h2, .list h2 { font-size: 16px; margin: 0 0 18px; letter-spacing: -0.02em; }
.actions { display: flex; gap: 10px; }
.message--inline { grid-column: 1 / -1; margin: 4px 0 0; }
.list-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; }
.filters { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.filters .input { width: auto; min-width: 140px; }
.quick-ranges { display: flex; gap: 8px; margin: 12px 0; }
.chip { background: transparent; border: 1px solid var(--color-border); color: var(--color-text-secondary); padding: 6px 12px; border-radius: 999px; font-size: 12px; cursor: pointer; }
.chip:hover { color: var(--color-accent-bright); border-color: var(--color-accent); background: var(--color-accent-bg); }
table { width: 100%; border-collapse: collapse; font-size: 14px; }
th, td { padding: 13px 8px; border-bottom: 1px solid var(--color-border); text-align: left; }
th { color: var(--color-text-muted); font-family: var(--font-mono); font-size: 10px; font-weight: var(--font-weight-medium); letter-spacing: 0.03em; }
tbody tr:hover { background: var(--color-surface-raised); }
th.amount, td.amount { text-align: right; }
.row-actions { text-align: right; white-space: nowrap; }
.link { border: 0; background: none; color: var(--color-accent); cursor: pointer; padding: 0 6px; font-size: 13px; }
.link:hover { color: var(--color-accent-bright); text-decoration: underline; text-underline-offset: 3px; }
.link--danger { color: var(--color-danger); }
.positive { color: var(--color-success); }
.negative { color: var(--color-danger); }
</style>
