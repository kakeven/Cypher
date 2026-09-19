import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/services/api'

export const useSubscriptionsStore = defineStore('subscriptions', () => {
  const dashboard = ref(null)
  const clients = ref([])
  const products = ref([])
  const plans = ref([])
  const subscriptions = ref([])
  const invoices = ref([])
  const loading = ref(false)
  const error = ref('')

  async function load(period) {
    loading.value = true
    error.value = ''
    try {
      const [summary, clientItems, productItems, planItems, subscriptionItems, invoiceItems] = await Promise.all([
        api.saasDashboard(period), api.saasClients(), api.saasProducts(), api.saasPlans(), api.saasSubscriptions(), api.saasInvoices({ period }),
      ])
      dashboard.value = summary
      clients.value = clientItems
      products.value = productItems
      plans.value = planItems
      subscriptions.value = subscriptionItems
      invoices.value = invoiceItems
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  return { dashboard, clients, products, plans, subscriptions, invoices, loading, error, load }
})
