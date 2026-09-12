<script setup>
import { computed, ref, watch } from 'vue'
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

const pendingDelete = ref(null)
function askRemove(goal) { pendingDelete.value = goal.id }
function cancelRemove() { pendingDelete.value = null }
async function confirmRemove(goal) {
  try {
    await api.deleteGoal(goal.id)
    if (selected.value?.id === goal.id) selected.value = null
    pendingDelete.value = null
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
            <button type="button" class="link" @click="choose(goal)">Ver depósitos</button>
            <button type="button" class="link" @click="edit(goal)">Editar</button>
            <template v-if="pendingDelete === goal.id">
              <button type="button" class="link link--danger" @click="confirmRemove(goal)">Confirmar</button>
              <button type="button" class="link" @click="cancelRemove">Cancelar</button>
            </template>
            <button v-else type="button" class="link link--danger" @click="askRemove(goal)">Excluir</button>
          </footer>
        </article>
      </div>
    </section>

    <section v-if="selected" class="card details" aria-live="polite">
      <h2>{{ selected.name }} — depósitos</h2>
      <form class="deposit" @submit.prevent="addDeposit">
        <label class="sr-only" for="deposit-amount">Valor do depósito</label>
        <input id="deposit-amount" v-model="deposit.amount" class="input" min="0.01" step="0.01" required placeholder="Valor" type="number" />
        <label class="sr-only" for="deposit-month">Mês de referência</label>
        <DateInput id="deposit-month" v-model="deposit.reference_month" type="month" required aria-label="Mês de referência" />
        <label class="sr-only" for="deposit-note">Observação</label>
        <input id="deposit-note" v-model="deposit.note" class="input" maxlength="250" placeholder="Observação (opcional)" />
        <button class="button">Adicionar</button>
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
.details { margin-top: 18px; }
.deposit { display: grid; grid-template-columns: 1fr 1fr 2fr auto; gap: 8px; align-items: center; }
.deposit .month { width: 100%; }
.details ul { list-style: none; padding: 0; margin: 18px 0 0; }
.details li { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid var(--color-border); color: var(--color-text-secondary); }
.details li small { color: var(--color-text-muted); }
.details li b { color: var(--color-success); }
</style>
