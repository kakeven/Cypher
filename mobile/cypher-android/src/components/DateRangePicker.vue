<script setup>
import { computed, ref } from 'vue'
import { formatDateBR, todayISO } from '@/utils/format'

const props = defineProps({
  start: { type: String, default: '' },
  end: { type: String, default: '' },
  max: { type: String, default: todayISO() },
  compact: { type: Boolean, default: false },
})
const emit = defineEmits(['update:start', 'update:end', 'change'])
const open = ref(false)
const month = ref(new Date())
const weekdays = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']

function localDate(value) {
  const [year, monthValue, day] = value.split('-').map(Number)
  return new Date(year, monthValue - 1, day)
}
function iso(value) {
  const year = value.getFullYear()
  const monthValue = String(value.getMonth() + 1).padStart(2, '0')
  const day = String(value.getDate()).padStart(2, '0')
  return `${year}-${monthValue}-${day}`
}
function openPicker() {
  month.value = localDate(props.end || props.start || props.max)
  open.value = true
}
const monthLabel = computed(() => month.value.toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' }))
const days = computed(() => {
  const year = month.value.getFullYear()
  const monthValue = month.value.getMonth()
  const first = new Date(year, monthValue, 1)
  const offset = (first.getDay() + 6) % 7
  const count = new Date(year, monthValue + 1, 0).getDate()
  return Array.from({ length: offset + count }, (_, index) => {
    if (index < offset) return null
    const value = new Date(year, monthValue, index - offset + 1)
    return { value: iso(value), label: value.getDate() }
  })
})
function previousMonth() { month.value = new Date(month.value.getFullYear(), month.value.getMonth() - 1, 1) }
function nextMonth() {
  const next = new Date(month.value.getFullYear(), month.value.getMonth() + 1, 1)
  if (iso(next) <= props.max.slice(0, 7) + '-01') month.value = next
}
function isInRange(value) { return props.start && props.end && value > props.start && value < props.end }
function select(value) {
  if (value > props.max) return
  if (!props.start || props.end) {
    emit('update:start', value)
    emit('update:end', '')
    return
  }
  if (value < props.start) {
    emit('update:start', value)
    emit('update:end', '')
    return
  }
  emit('update:end', value)
  emit('change')
  open.value = false
}
function clear() {
  emit('update:start', '')
  emit('update:end', '')
  emit('change')
  open.value = false
}
function finish() {
  if (props.start) emit('change')
  open.value = false
}
</script>

<template>
  <button type="button" class="range-trigger" :class="{ selected: start, compact }" :aria-label="compact ? 'Selecionar período' : undefined" :title="compact ? 'Selecionar período' : undefined" :aria-expanded="open" @click="openPicker">
    <svg class="range-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <rect x="3" y="4.5" width="18" height="16.5" rx="2" />
      <path d="M8 2.5v4M16 2.5v4M3 9h18M8 13h.01M12 13h.01M16 13h.01M8 17h.01M12 17h.01M16 17h.01" />
    </svg>
    <template v-if="!compact">
      <span v-if="start">{{ formatDateBR(start) }} <i>até</i> {{ end ? formatDateBR(end) : '…' }}</span>
      <span v-else>Selecionar período</span>
    </template>
  </button>

  <Teleport to="body">
    <div v-if="open" class="range-overlay" @mousedown.self="open = false">
      <section class="range-dialog" role="dialog" aria-modal="true" aria-label="Selecionar intervalo de datas">
        <header>
          <div><h2>Selecionar período</h2><p>{{ !start || end ? 'Escolha a data inicial.' : 'Agora escolha a data final.' }}</p></div>
          <button type="button" class="close" aria-label="Fechar calendário" @click="open = false">×</button>
        </header>
        <div class="calendar-nav"><button type="button" aria-label="Mês anterior" @click="previousMonth">‹</button><strong>{{ monthLabel }}</strong><button type="button" aria-label="Próximo mês" @click="nextMonth">›</button></div>
        <div class="weekdays"><span v-for="day in weekdays" :key="day">{{ day }}</span></div>
        <div class="days">
          <span v-for="(day, index) in days" :key="day?.value || `empty-${index}`" class="day-slot">
            <button v-if="day" type="button" :disabled="day.value > max" :class="{ start: day.value === start, end: day.value === end, between: isInRange(day.value) }" @click="select(day.value)">{{ day.label }}</button>
          </span>
        </div>
        <footer><button type="button" class="clear" :disabled="!start" @click="clear">Limpar período</button><button type="button" class="done" @click="finish">Concluído</button></footer>
      </section>
    </div>
  </Teleport>
</template>

<style scoped>
.range-trigger { display: inline-flex; align-items: center; gap: 8px; min-height: 36px; border: 1px solid var(--color-border); border-radius: 6px; padding: 7px 10px; color: var(--color-text-secondary); background: transparent; cursor: pointer; font-size: 12px; white-space: nowrap; }
.range-trigger.compact { justify-content: center; width: 36px; padding: 7px; }
.range-trigger:hover, .range-trigger.selected { color: var(--color-text-primary); border-color: var(--color-border-strong); background: var(--color-surface-raised); }
.range-trigger.selected { border-color: var(--color-accent); }
.range-icon { width: 16px; height: 16px; flex: 0 0 auto; color: var(--color-accent-bright); } .range-trigger i { color: var(--color-text-muted); font-style: normal; }
.range-overlay { position: fixed; z-index: 100; inset: 0; display: grid; place-items: center; padding: 24px; background: rgba(4, 7, 13, 0.58); }
.range-dialog { width: min(386px, 100%); border: 1px solid var(--color-border-strong); border-radius: 10px; background: var(--color-surface); box-shadow: 0 22px 60px rgba(0, 0, 0, 0.45); }
.range-dialog header { display: flex; justify-content: space-between; align-items: start; padding: 18px 18px 14px; border-bottom: 1px solid var(--color-border); } .range-dialog h2 { margin: 0; font-size: 15px; } .range-dialog p { margin: 5px 0 0; color: var(--color-text-secondary); font-size: 12px; } .close, .calendar-nav button { border: 0; color: var(--color-text-secondary); background: transparent; cursor: pointer; }
.close { width: 28px; height: 28px; border-radius: 5px; font-size: 22px; line-height: 1; } .close:hover, .calendar-nav button:hover { color: var(--color-text-primary); background: var(--color-surface-raised); }
.calendar-nav { display: grid; grid-template-columns: 32px 1fr 32px; align-items: center; padding: 16px 18px 10px; text-align: center; } .calendar-nav strong { font-size: 13px; text-transform: capitalize; } .calendar-nav button { width: 30px; height: 30px; border-radius: 5px; font-size: 23px; line-height: 1; }
.weekdays, .days { display: grid; grid-template-columns: repeat(7, 1fr); padding: 0 18px; } .weekdays { margin-bottom: 4px; } .weekdays span { color: var(--color-text-muted); text-align: center; font-size: 10px; }
.days { padding-bottom: 16px; } .day-slot { display: grid; place-items: center; height: 38px; background: transparent; } .day-slot button { width: 32px; height: 32px; border: 0; border-radius: 5px; color: var(--color-text-primary); background: transparent; cursor: pointer; font-size: 12px; } .day-slot button:hover:not(:disabled) { background: var(--color-surface-raised); }
.day-slot button:disabled { color: var(--color-text-muted); cursor: not-allowed; opacity: 0.42; } .day-slot button.between { width: 100%; border-radius: 0; color: var(--color-accent-bright); background: var(--color-accent-bg); } .day-slot button.start, .day-slot button.end { color: #fff; background: var(--color-accent); } .day-slot button.start { border-radius: 5px 0 0 5px; } .day-slot button.end { border-radius: 0 5px 5px 0; } .day-slot button.start.end { border-radius: 5px; }
.range-dialog footer { display: flex; justify-content: space-between; padding: 12px 18px; border-top: 1px solid var(--color-border); } .range-dialog footer button { border: 0; padding: 7px 9px; border-radius: 5px; cursor: pointer; font-size: 12px; } .clear { color: var(--color-text-secondary); background: transparent; } .clear:disabled { opacity: 0.45; cursor: not-allowed; } .done { color: #fff; background: var(--color-accent); }
</style>
