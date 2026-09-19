import { reactive } from 'vue'

const state = reactive({ items: [] })
let nextId = 0

function push(message, type = 'info', timeout = 4000) {
  const id = ++nextId
  state.items.push({ id, message, type })
  if (timeout > 0) setTimeout(() => dismiss(id), timeout)
  return id
}

function dismiss(id) {
  const index = state.items.findIndex((item) => item.id === id)
  if (index >= 0) state.items.splice(index, 1)
}

export const toast = {
  info: (message) => push(message, 'info'),
  success: (message) => push(message, 'success'),
  error: (message) => push(message, 'error', 6000),
  dismiss,
}

export function useToast() {
  return toast
}

export function useToastState() {
  return state
}
