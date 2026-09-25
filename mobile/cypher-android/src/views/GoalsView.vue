<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { api, brl } from '@/services/api'
import { useToast } from '@/composables/useToast'
import { currentMonth, formatDateBR } from '@/utils/format'
import DateInput from '@/components/DateInput.vue'

const toast = useToast()
const goals = ref([])
const error = ref('')
const selected = ref(null)
const loading = ref(false)
const editing = ref(null)
const nowMonth = currentMonth()

const form = ref({ name: '', target_amount: '', deadline: '', description: '' })
const deposit = ref({ amount: '', reference_month: nowMonth, note: '' })

async function load() {
  loading.value = true
  error.value = ''
  try {
    goals.value = await api.goals()
    if (selected.value) selected.value = await api.goal(selected.value.id)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

function payload(formData) {
  return {
    ...formData,
    target_amount: Number(formData.target_amount),
    deadline: formData.deadline || null,
    description: formData.description?.trim() || null,
  }
}

async function save() {
  try {
    if (editing.value) {
      await api.updateGoal(editing.value, payload(form.value))
      toast.success('Meta atualizada.')
    } else {
      await api.createGoal(payload(form.value))
      toast.success('Meta criada.')
    }
    reset()
    await load()
  } catch (e) {
    error.value = e.message
  }
}

async function choose(goal) {
  selected.value = { ...goal }
  try {
    selected.value = await api.goal(goal.id)
  } catch (e) {
    error.value = e.message
  }
}

function edit(goal) {
  editing.value = goal.id
  form.value = {
    name: goal.name,
    target_amount: goal.target_amount,
    deadline: goal.deadline || '',
    description: goal.description || '',
  }
}

function reset() {
  editing.value = null
  form.value = { name: '', target_amount: '', deadline: '', description: '' }
}

function closeDetails() {
  selected.value = null
}

async function addDeposit() {
  if (!selected.value) return
  try {
    await api.addDeposit(selected.value.id, {
      ...deposit.value,
      amount: Number(deposit.value.amount),
      note: deposit.value.note?.trim() || null,
    })
    deposit.value = { amount: '', reference_month: nowMonth, note: '' }
    await load()
    if (selected.value?.is_completed) toast.success('Parabéns! Meta concluída.')
  } catch (e) {
    error.value = e.message
  }
}

const contextMenu = ref(null)
function openContextMenu(event, goal) { contextMenu.value = { item: goal, x: Math.min(event.clientX, window.innerWidth - 168), y: Math.min(event.clientY, window.innerHeight - 100) } }
function closeContextMenu() { contextMenu.value = null }
function editGoal() {
  const goal = contextMenu.value?.item
  if (!goal) return
  closeContextMenu()
  edit(goal)
}
async function deleteGoal() {
  const goal = contextMenu.value?.item
  closeContextMenu()
  if (!goal || !window.confirm(`Excluir a meta “${goal.name}”? Os depósitos também serão removidos.`)) return
  try {
    await api.deleteGoal(goal.id)
    if (selected.value?.id === goal.id) selected.value = null
    toast.success('Meta excluída.')
    await load()
  } catch (e) {
    error.value = e.message
  }
}

const totalSaved = computed(() => goals.value.reduce((acc, goal) => acc + Number(goal.saved_amount || 0), 0))
const totalTarget = computed(() => goals.value.reduce((acc, goal) => acc + Number(goal.target_amount || 0), 0))
const completedCount = computed(() => goals.value.filter((goal) => goal.is_completed).length)

watch(editing, (value) => {
  if (value === null) error.value = ''
})

onMounted(() => {
  load()
  window.addEventListener('click', closeContextMenu)
  window.addEventListener('scroll', closeContextMenu, true)
  window.addEventListener('keydown', handleKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('click', closeContextMenu)
  window.removeEventListener('scroll', closeContextMenu, true)
  window.removeEventListener('keydown', handleKeydown)
})

function handleKeydown(event) {
  if (event.key === 'Escape') closeDetails()
}
</script>

<template>
  <div>
    <header class="page-header">
      <div>
        <h1>Metas</h1>
        <p>Transforme seus objetivos em progresso visível.</p>
      </div>
      <div v-if="goals.length" class="totals" aria-label="Resumo das metas">
        <span><b>{{ completedCount }}</b>/{{ goals.length }} concluídas</span>
        <span>{{ brl(totalSaved) }} de {{ brl(totalTarget) }}</span>
      </div>
    </header>

    <p v-if="error" class="message" role="alert">{{ error }}</p>

    <section class="card form">
      <h2>{{ editing ? 'Editar meta' : 'Nova meta' }}</h2>
      <form class="form-grid" @submit.prevent="save">
        <label>
          Nome
          <input v-model="form.name" required class="input" maxlength="100" />
        </label>
        <label>
          Valor alvo
          <input v-model="form.target_amount" required min="0.01" step="0.01" class="input" type="number" />
        </label>
        <label>
          Prazo (opcional)
          <DateInput v-model="form.deadline" aria-label="Prazo da meta" />
        </label>
        <label class="full">
          Descrição (opcional)
          <input v-model="form.description" maxlength="250" class="input" />
        </label>
        <div class="actions">
          <button class="button">{{ editing ? 'Salvar alterações' : 'Criar meta' }}</button>
          <button v-if="editing" type="button" class="button button--ghost" @click="reset">Cancelar</button>
        </div>
      </form>
    </section>

    <div v-if="loading" class="empty" role="status">Carregando metas…</div>

    <section v-else>
      <p v-if="!goals.length" class="empty card" role="status">Você ainda não criou uma meta.</p>
      <div v-else class="goals">
        <article
          v-for="goal in goals"
          :key="goal.id"
          class="card goal"
          :class="{ active: selected?.id === goal.id, completed: goal.is_completed }"
          @contextmenu.prevent="openContextMenu($event, goal)"
        >
          <div class="goal-title">
            <h2>{{ goal.name }}</h2>
            <span v-if="goal.is_completed">Concluída ✓</span>
          </div>
          <b>{{ brl(goal.saved_amount) }} <small>de {{ brl(goal.target_amount) }}</small></b>
          <div class="track" :aria-label="`Progresso: ${goal.progress}%`">
            <i :style="{ width: `${goal.progress}%` }" />
          </div>
          <p>
            {{ goal.progress }}% concluído
            <span v-if="goal.deadline">· até {{ formatDateBR(goal.deadline) }}</span>
          </p>
          <footer>
            <button type="button" class="link" @click="choose(goal)">Ver detalhes</button>
            <button type="button" class="link goal-actions" aria-haspopup="menu" @click.stop="openContextMenu($event, goal)">Ações</button>
          </footer>
        </article>
      </div>
    </section>

    <div v-if="contextMenu" class="context-menu" :style="{ left: `${contextMenu.x}px`, top: `${contextMenu.y}px` }" role="menu" @click.stop>
      <button type="button" role="menuitem" @click="editGoal">Editar</button>
      <button type="button" class="danger" role="menuitem" @click="deleteGoal">Excluir</button>
    </div>

    <div v-if="selected" class="modal-backdrop" @click.self="closeDetails">
      <section class="card details" role="dialog" aria-modal="true" :aria-labelledby="`goal-details-${selected.id}`">
        <header class="details-header">
          <div>
            <h2 :id="`goal-details-${selected.id}`">{{ selected.name }}</h2>
            <p>Depósitos: {{ brl(selected.saved_amount) }} de {{ brl(selected.target_amount) }}</p>
          </div>
          <button type="button" class="close-modal" @click="closeDetails">← <span>Voltar</span></button>
        </header>
        <form class="deposit" @submit.prevent="addDeposit">
          <label>
            Valor do depósito
            <input id="deposit-amount" v-model="deposit.amount" class="input" min="0.01" step="0.01" required placeholder="0,00" type="number" />
          </label>
          <label>
            Mês de referência
            <DateInput id="deposit-month" v-model="deposit.reference_month" type="month" required aria-label="Mês de referência" />
          </label>
          <label>
            Observação <span>(opcional)</span>
            <input id="deposit-note" v-model="deposit.note" class="input" maxlength="250" placeholder="Ex.: valor separado este mês" />
          </label>
          <button class="button">Adicionar depósito</button>
        </form>
        <ul v-if="selected.deposits?.length">
          <li v-for="item in selected.deposits" :key="item.id">
            <span>{{ item.reference_month }} <small v-if="item.note">· {{ item.note }}</small></span>
            <b>{{ brl(item.amount) }}</b>
          </li>
        </ul>
        <p v-else class="empty" role="status">Nenhum depósito registrado.</p>
      </section>
    </div>
  </div>
</template>

<style scoped>
.form { margin-bottom: 18px; }
.form h2, .details h2 { font-size: 16px; margin: 0 0 18px; letter-spacing: -0.02em; }
.actions { display: flex; gap: 10px; }
.totals { display: grid; gap: 4px; text-align: right; font-size: 12px; color: var(--color-text-secondary); }
.totals b { color: var(--color-text-primary); font-size: 14px; }
.goals { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }
.goal { cursor: pointer; transition: border-color 0.15s, background 0.15s; }
.goal:hover, .goal.active { border-color: var(--color-border-strong); background: var(--color-surface-raised); }
.goal.completed { border-color: var(--color-success); }
.goal-title { display: flex; justify-content: space-between; gap: 6px; }
.goal-title h2 { font-size: 16px; margin: 0; }
.goal-title span { color: var(--color-success); font-size: 12px; }
.goal > b { display: block; font-family: var(--font-mono); font-size: 18px; letter-spacing: -0.06em; margin: 18px 0 9px; }
.goal small, .goal p { font-size: 12px; color: var(--color-text-secondary); font-weight: 400; }
.track { height: 7px; border-radius: 8px; overflow: hidden; background: var(--color-surface-raised); }
.track i { display: block; height: 100%; background: var(--color-accent); transition: width 0.3s ease; }
.goal.completed .track i { background: var(--color-success); }
.goal footer { margin-top: 18px; display: flex; flex-wrap: wrap; gap: 4px; }
.link { border: 0; background: none; color: var(--color-accent); cursor: pointer; padding: 0 5px; font-size: 13px; }
.link:hover { color: var(--color-accent-bright); text-decoration: underline; text-underline-offset: 3px; }
.link--danger { color: var(--color-danger); }
.modal-backdrop { position: fixed; z-index: 30; inset: 0; display: grid; place-items: center; padding: 18px; background: rgba(6, 9, 15, .72); }
.details { width: min(760px, 100%); max-height: calc(100dvh - 36px); overflow: auto; }
.details-header { display: flex; justify-content: space-between; gap: 18px; margin-bottom: 18px; }
.details-header h2 { margin-bottom: 5px; }
.details-header p { margin: 0; color: var(--color-text-secondary); font-size: 13px; }
.close-modal { border: 0; color: var(--color-text-secondary); background: transparent; cursor: pointer; font-size: 24px; line-height: 1; }
.deposit { display: grid; grid-template-columns: 1fr 1fr 2fr auto; gap: 8px; align-items: center; }
.deposit label { display: grid; gap: 7px; color: var(--color-text-secondary); font-size: 13px; }
.deposit label span { color: var(--color-text-muted); }
.deposit .month { width: 100%; }
.details ul { list-style: none; padding: 0; margin: 18px 0 0; }
.details li { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid var(--color-border); color: var(--color-text-secondary); }
.details li small { color: var(--color-text-muted); }
.details li b { color: var(--color-success); }
.context-menu { position: fixed; z-index: 10; display: grid; width: 160px; padding: 4px; border: 1px solid var(--color-border-strong); border-radius: 7px; background: var(--color-surface-raised); box-shadow: 0 10px 30px rgba(0, 0, 0, 0.28); }
.context-menu button { border: 0; border-radius: 4px; padding: 8px 10px; color: var(--color-text-primary); text-align: left; background: transparent; cursor: pointer; font-size: 13px; }
.context-menu button:hover { background: var(--color-surface); }
.context-menu .danger { color: var(--color-danger); }
@media (max-width: 640px) {
  .totals { display: none; }
  .form { padding: 14px; }
  .goals { grid-template-columns: 1fr; gap: 10px; }
  .goal { padding: 15px; }
  .goal > b { margin: 13px 0 8px; }
  .goal footer { margin-top: 12px; }
  .goal footer .link { min-height: 44px; padding: 8px 10px; }
  .modal-backdrop { z-index: 40; display: block; padding: 0; overflow: auto; background: var(--color-bg); }
  .details { width: 100%; min-height: 100dvh; max-height: none; border: 0; border-radius: 0; padding: max(18px, env(safe-area-inset-top)) 14px calc(22px + env(safe-area-inset-bottom)); box-shadow: none; }
  .details-header { position: sticky; top: calc(-1 * max(18px, env(safe-area-inset-top))); z-index: 1; align-items: center; margin: calc(-1 * max(18px, env(safe-area-inset-top))) -14px 18px; padding: max(18px, env(safe-area-inset-top)) 14px 14px; border-bottom: 1px solid var(--color-border); background: var(--color-bg); }
  .details-header h2 { margin: 0; font-size: 18px; }
  .details-header p { display: none; }
  .close-modal { order: -1; display: flex; align-items: center; gap: 6px; min-height: 42px; padding: 0; color: var(--color-accent-bright); font-size: 14px; font-weight: 650; }
  .details .deposit { grid-template-columns: 1fr; gap: 14px; align-items: stretch; }
  .details .deposit label { gap: 7px; font-size: 13px; }
  .details .deposit .input, .details .deposit .button { width: 100%; }
  .details .deposit .button { margin-top: 2px; }
  .details .deposit :deep(.date-input) { min-width: 0; }
}
:global(.app-shell--mobile) .details .deposit { grid-template-columns: 1fr; gap: 14px; align-items: stretch; }
:global(.app-shell--mobile) .details .deposit .input, :global(.app-shell--mobile) .details .deposit .button { width: 100%; }
:global(.app-shell--mobile) .details .deposit :deep(.date-input) { min-width: 0; }
</style>
