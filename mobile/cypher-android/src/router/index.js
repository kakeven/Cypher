import { createRouter, createWebHistory } from 'vue-router'
import { routeDefinitions } from 'virtual:cypher-edition'

const routes = [
  { path: '/', redirect: routeDefinitions[0].path },
  ...routeDefinitions,
  { path: '/:pathMatch(.*)*', redirect: routeDefinitions[0].path },
]

export default createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})
