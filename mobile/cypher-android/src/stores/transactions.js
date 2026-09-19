import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/services/api'

export const useTransactionsStore = defineStore('transactions', () => {
  const items = ref([])
  const loading = ref(false)
  const error = ref('')

  async function load(filters = {}) {
    loading.value = true
    error.value = ''
    try {
      const params = Object.fromEntries(
        Object.entries(filters).filter(([, value]) => value !== '' && value !== null && value !== undefined)
      )
      items.value = await api.transactions(params)
    } catch (e) {
      error.value = e.message
      items.value = []
    } finally {
      loading.value = false
    }
  }

  async function create(payload) {
    error.value = ''
    try {
      const created = await api.createTransaction(payload)
      items.value = [created, ...items.value]
      return created
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  async function update(id, payload) {
    error.value = ''
    try {
      const updated = await api.updateTransaction(id, payload)
      const index = items.value.findIndex((item) => item.id === id)
      if (index >= 0) items.value.splice(index, 1, updated)
      return updated
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  async function remove(id) {
    error.value = ''
    try {
      await api.deleteTransaction(id)
      items.value = items.value.filter((item) => item.id !== id)
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  return { items, loading, error, load, create, update, remove }
})
