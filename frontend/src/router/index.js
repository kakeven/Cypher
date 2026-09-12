import { createRouter, createWebHistory } from 'vue-router'

const DashboardView = () => import('@/views/DashboardView.vue')
const TransactionsView = () => import('@/views/TransactionsView.vue')
const BudgetsView = () => import('@/views/BudgetsView.vue')
const GoalsView = () => import('@/views/GoalsView.vue')
const ReceivablesView = () => import('@/views/ReceivablesView.vue')

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', component: DashboardView, meta: { title: 'Visão geral' } },
  { path: '/transacoes', component: TransactionsView, meta: { title: 'Transações' } },
  { path: '/orcamentos', component: BudgetsView, meta: { title: 'Orçamentos' } },
  { path: '/metas', component: GoalsView, meta: { title: 'Metas' } },
  { path: '/recebimentos', component: ReceivablesView, meta: { title: 'Recebimentos' } },
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
]

export default createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})
