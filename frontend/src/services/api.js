const RAW_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api'
const BASE_URL = RAW_BASE.replace(/\/+$/, '').replace(/\/api$/, '') + '/api'

function extractMessage(body, status) {
  if (!body) return 'Não foi possível concluir esta ação.'
  if (typeof body.detail === 'string') {
    if (status === 404 && body.detail.toLowerCase() === 'not found') {
      return 'Recurso não encontrado. Verifique se o servidor está atualizado.'
    }
    return body.detail
  }
  if (Array.isArray(body.detail)) {
    return body.detail
      .map((entry) => entry.msg || entry.message || JSON.stringify(entry))
      .join('; ')
  }
  if (typeof body.detail === 'object' && body.detail !== null) {
    return body.detail.msg || body.detail.message || JSON.stringify(body.detail)
  }
  return 'Não foi possível concluir esta ação.'
}

async function request(path, options = {}) {
  let response
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options,
    })
  } catch {
    throw new Error('Não foi possível contatar o servidor. Verifique sua conexão.')
  }
  if (response.status === 204) return null
  const body = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(extractMessage(body, response.status))
  return body
}

export const api = {
  categories: () => request('/categories'),
  createCategory: (data) => request('/categories', { method: 'POST', body: JSON.stringify(data) }),
  updateCategory: (id, data) => request(`/categories/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  setBudget: (id, budget_limit) => request(`/categories/${id}/budget`, { method: 'PUT', body: JSON.stringify({ budget_limit }) }),
  deleteCategory: (id) => request(`/categories/${id}`, { method: 'DELETE' }),
  transactions: (params = {}) => {
    const search = new URLSearchParams(params).toString()
    return request(`/transactions${search ? `?${search}` : ''}`)
  },
  createTransaction: (data) => request('/transactions', { method: 'POST', body: JSON.stringify(data) }),
  updateTransaction: (id, data) => request(`/transactions/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteTransaction: (id) => request(`/transactions/${id}`, { method: 'DELETE' }),
  dashboard: (period) => request(`/dashboard?period=${period}`),
  budgets: (period) => request(`/budgets?period=${period}`),
  goals: () => request('/goals'),
  goal: (id) => request(`/goals/${id}`),
  createGoal: (data) => request('/goals', { method: 'POST', body: JSON.stringify(data) }),
  updateGoal: (id, data) => request(`/goals/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteGoal: (id) => request(`/goals/${id}`, { method: 'DELETE' }),
  addDeposit: (id, data) => request(`/goals/${id}/deposits`, { method: 'POST', body: JSON.stringify(data) }),
  receivables: () => request('/receivables'),
  receivable: (id) => request(`/receivables/${id}`),
  createReceivable: (data) => request('/receivables', { method: 'POST', body: JSON.stringify(data) }),
  updateReceivable: (id, data) => request(`/receivables/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteReceivable: (id) => request(`/receivables/${id}`, { method: 'DELETE' }),
  addReceivablePayment: (id, data) => request(`/receivables/${id}/payments`, { method: 'POST', body: JSON.stringify(data) }),
  recurringTransactions: () => request('/recurring-transactions'),
  createRecurringTransaction: (data) => request('/recurring-transactions', { method: 'POST', body: JSON.stringify(data) }),
  updateRecurringTransaction: (id, data) => request(`/recurring-transactions/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  pauseRecurringTransaction: (id) => request(`/recurring-transactions/${id}/pause`, { method: 'POST' }),
  resumeRecurringTransaction: (id) => request(`/recurring-transactions/${id}/resume`, { method: 'POST' }),
  generateOccurrences: (id) => request(`/recurring-transactions/${id}/generate-occurrences`, { method: 'POST' }),
  deleteRecurringTransaction: (id) => request(`/recurring-transactions/${id}`, { method: 'DELETE' }),
  occurrences: (params = {}) => request(`/occurrences${Object.keys(params).length ? `?${new URLSearchParams(params)}` : ''}`),
  occurrenceSummary: (period) => request(`/occurrences/summary?period=${period}`),
  confirmOccurrence: (id) => request(`/occurrences/${id}/confirm`, { method: 'POST' }),
  creditCards: () => request('/credit-cards'),
  createCreditCard: (data) => request('/credit-cards', { method: 'POST', body: JSON.stringify(data) }),
  creditCard: (id) => request(`/credit-cards/${id}`),
  importCreditCardCsv: (id, data) => request(`/credit-cards/${id}/import-csv`, { method: 'POST', body: JSON.stringify(data) }),
  creditCardInvoice: (id) => request(`/credit-cards/invoices/${id}`),
  deleteCreditCardInvoice: (id) => request(`/credit-cards/invoices/${id}`, { method: 'DELETE' }),
  addCreditCardInvoicePayment: (id, data) => request(`/credit-cards/invoices/${id}/payments`, { method: 'POST', body: JSON.stringify(data) }),
  setCreditCardPurchaseCategory: (id, category_id) => request(`/credit-cards/purchases/${id}/category`, { method: 'PUT', body: JSON.stringify({ category_id }) }),
  payCreditCardInvoice: (id, data) => request(`/credit-cards/invoices/${id}/pay`, { method: 'POST', body: JSON.stringify(data) }),
}

export { brl } from '@/utils/format'
