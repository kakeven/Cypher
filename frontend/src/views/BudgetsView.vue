<script setup>
import { onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { api, brl } from '@/services/api'
import { useToast } from '@/composables/useToast'
import { currentMonth } from '@/utils/format'
import DateInput from '@/components/DateInput.vue'

const toast = useToast()
const period = ref(currentMonth())
const items = ref([])
const error = ref('')
const loading = ref(false)
const values = reactive({})
const newCategory = reactive({ name: '', color: '#6D8BFF' })
const contextMenu = ref(null)

async function load() {
  loading.value = true
  error.value = ''
  try {
    items.value = await api.budgets(period.value)
    for (const item of items.value) values[item.id] = item.budget_limit ?? ''
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function save(item) {
  try {
    const raw = values[item.id]
    const budget_limit = raw === '' || raw === null ? null : Number(raw)
    await api.setBudget(item.id, budget_limit)
    toast.success(`Limite de ${item.name} atualizado.`)
    await load()
  } catch (e) {
    error.value = e.message
  }
}

async function createCategory() {
  try {
    await api.createCategory({ ...newCategory })
    newCategory.name = ''
    newCategory.color = '#6D8BFF'
    toast.success('Categoria criada.')
    await load()
  } catch (e) {
    error.value = e.message
  }
}

function openContextMenu(event, item) {
  contextMenu.value = {
    item,
    x: Math.min(event.clientX, window.innerWidth - 168),
    y: Math.min(event.clientY, window.innerHeight - 100),
  }
}

function closeContextMenu() {
  contextMenu.value = null
}

function editBudget() {
  const item = contextMenu.value?.item
  if (!item) return
  closeContextMenu()
  requestAnimationFrame(() => {
    const input = document.getElementById(`limit-${item.id}`)
    input?.focus()
    input?.select()
  })
}

async function deleteBudget() {
  const item = contextMenu.value?.item
  if (!item || !window.confirm(`Remover o limite de orçamento para “${item.name}”?`)) return
  closeContextMenu()
  try {
    await api.setBudget(item.id, null)
    toast.success(`Limite de ${item.name} removido.`)
    await load()
  } catch (e) {
    error.value = e.message
  }
}

function state(item) {
  if (!item.percent) return 'normal'
  if (item.percent >= 100) return 'danger'
  if (item.percent >= 80) return 'warning'
  return 'normal'
}

onMounted(() => {
  load()
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
    <header class="page-header">
      <div>
        <h1>Orçamentos</h1>
        <p>Defina limites mensais para seus gastos.</p>
      </div>
      <label class="sr-only" for="budgets-period">Período</label>
      <DateInput id="budgets-period" v-model="period" type="month" :max="currentMonth()" class="month" @change="load" />
    </header>

    <p v-if="error" class="message" role="alert">{{ error }}</p>

    <section class="card add-category">
      <h2>Nova categoria</h2>
      <form @submit.prevent="createCategory">
        <label class="sr-only" for="new-cat-name">Nome da categoria</label>
        <input id="new-cat-name" v-model="newCategory.name" class="input" maxlength="50" required placeholder="Ex.: Assinaturas" />
        <label class="sr-only" for="new-cat-color">Cor da categoria</label>
        <input id="new-cat-color" v-model="newCategory.color" class="color" required type="color" />
        <button class="button">Adicionar categoria</button>
      </form>
    </section>

    <div v-if="loading" class="empty" role="status" aria-live="polite">Carregando orçamentos…</div>

    <section v-else class="budget-grid">
      <article v-for="item in items" :key="item.id" class="card" @contextmenu.prevent="openContextMenu($event, item)">
        <div class="title">
          <span :style="{ background: item.color }" class="dot" aria-hidden="true" />
          <h2>{{ item.name }}</h2>
        </div>
        <template v-if="item.budget_limit">
          <p class="spent">{{ brl(item.spent) }} <span>de {{ brl(item.budget_limit) }}</span></p>
          <div class="track" :aria-label="`${item.name}: ${item.percent}% utilizado`">
            <i :class="state(item)" :style="{ width: `${Math.min(item.percent, 100)}%` }" />
          </div>
          <p :class="['status', state(item)]">
            {{ item.percent >= 100 ? 'Limite ultrapassado' : item.percent >= 80 ? 'Atenção: perto do limite' : `${item.percent}% usado` }}
          </p>
        </template>
        <p v-else class="no-limit">Sem limite definido.</p>
        <form class="budget-form" @submit.prevent="save(item)">
          <label class="sr-only" :for="`limit-${item.id}`">Limite mensal de {{ item.name }}</label>
          <input :id="`limit-${item.id}`" v-model="values[item.id]" class="input" min="0.01" step="0.01" placeholder="Limite mensal" type="number" />
          <button class="button button--ghost">Salvar</button>
        </form>
      </article>
    </section>

    <div v-if="contextMenu" class="context-menu" :style="{ left: `${contextMenu.x}px`, top: `${contextMenu.y}px` }" role="menu" @click.stop>
      <button type="button" role="menuitem" @click="editBudget">Editar</button>
      <button type="button" class="danger" role="menuitem" @click="deleteBudget">Excluir</button>
    </div>
  </div>
</template>

<style scoped>
.month { width: 145px; }
.add-category { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; gap: 16px; flex-wrap: wrap; }
.add-category h2 { font-size: 16px; margin: 0; letter-spacing: -0.02em; }
.add-category form { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.color { width: 42px; height: 40px; padding: 3px; border: 1px solid var(--color-border); border-radius: 7px; background: var(--color-bg); cursor: pointer; }
.budget-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
.title { display: flex; align-items: center; gap: 8px; }
.title h2 { font-size: 16px; margin: 0; }
.dot { width: 10px; height: 10px; border-radius: 50%; }
.spent { font-family: var(--font-mono); font-size: 19px; font-weight: var(--font-weight-bold); letter-spacing: -0.06em; margin: 20px 0 8px; }
.spent span, .no-limit { font-size: 13px; font-weight: var(--font-weight-regular); color: var(--color-text-secondary); }
.track { height: 7px; border-radius: 8px; background: var(--color-surface-raised); overflow: hidden; }
.track i { display: block; height: 100%; background: var(--color-accent); transition: width 0.3s ease; }
.track i.warning { background: var(--color-warning); }
.track i.danger { background: var(--color-danger); }
.status { font-size: 12px; color: var(--color-success); margin: 8px 0 18px; }
.status.warning { color: var(--color-warning); }
.status.danger { color: var(--color-danger); }
.no-limit { margin: 20px 0; }
.budget-form { display: flex; gap: 8px; }
.budget-form input { min-width: 0; flex: 1; }
.budget-form .button { padding: 8px 10px; }
.context-menu { position: fixed; z-index: 10; display: grid; width: 160px; padding: 4px; border: 1px solid var(--color-border-strong); border-radius: 7px; background: var(--color-surface-raised); box-shadow: 0 10px 30px rgba(0, 0, 0, 0.28); }
.context-menu button { border: 0; border-radius: 4px; padding: 8px 10px; color: var(--color-text-primary); text-align: left; background: transparent; cursor: pointer; font-size: 13px; }
.context-menu button:hover { background: var(--color-surface); }
.context-menu .danger { color: var(--color-danger); }
</style>
