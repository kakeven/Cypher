import { Capacitor } from '@capacitor/core'
import { httpApi } from '@/services/api'
import { cacheResponse, initializeMobileDatabase, readCachedResponse } from '@/services/mobileDatabase'

const readMethods = new Set([
  'categories', 'transactions', 'dashboard', 'budgets', 'goals', 'goal', 'receivables', 'receivable',
  'creditCards', 'creditCard', 'creditCardInvoice', 'recurringTransactions', 'occurrences', 'occurrenceSummary',
])

function cacheKey(method, args) {
  return `${method}:${JSON.stringify(args)}`
}

export async function createDataSource() {
  if (!Capacitor.isNativePlatform()) return httpApi
  await initializeMobileDatabase()

  return new Proxy(httpApi, {
    get(target, property) {
      const method = target[property]
      if (typeof method !== 'function') return method
      return async (...args) => {
        const key = cacheKey(property, args)
        try {
          const result = await method(...args)
          if (readMethods.has(property)) await cacheResponse(key, result)
          return result
        } catch (error) {
          if (readMethods.has(property)) {
            const cached = await readCachedResponse(key)
            if (cached !== undefined) return cached
          }
          throw error
        }
      }
    },
  })
}
