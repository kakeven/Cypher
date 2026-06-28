import { createRouter, createWebHistory } from 'vue-router'
import tele_principal from '@/views/tele_principal.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'dashboard', component: tele_principal }
  ],
})

export default router
