import { readFileSync } from 'node:fs'
import { fileURLToPath, URL } from 'node:url'
import { resolve } from 'node:path'

import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
const virtualEditionId = 'virtual:cypher-edition'
const resolvedVirtualEditionId = `\0${virtualEditionId}`

function readJson(path) {
  return JSON.parse(readFileSync(path, 'utf-8'))
}

function resolveModules(requested, modulesById) {
  const resolved = new Set()
  const visit = (id) => {
    const module = modulesById.get(id)
    if (!module) throw new Error(`Módulo desconhecido na edição: ${id}`)
    if (resolved.has(id)) return
    module.dependencies.forEach(visit)
    resolved.add(id)
  }
  requested.forEach(visit)
  return [...resolved]
}

function editionPlugin(mode) {
  const env = loadEnv(mode, process.cwd(), '')
  const root = process.cwd()
  const catalog = readJson(resolve(root, 'src/modules/catalog.json'))
  const editionId = env.VITE_CYPHER_EDITION || 'complete'
  const edition = readJson(resolve(root, `editions/${editionId}.json`))
  const modulesById = new Map(catalog.modules.map((module) => [module.id, module]))
  const enabledModuleIds = resolveModules(edition.modules, modulesById)
  const routes = enabledModuleIds.flatMap((id) => modulesById.get(id).routes.map((route) => ({ ...route, moduleId: id })))
  const routeSource = routes.map((route) => `{ path: ${JSON.stringify(route.path)}, component: () => import('@/views/${route.view}.vue'), meta: { title: ${JSON.stringify(route.title)}, moduleId: ${JSON.stringify(route.moduleId)} } }`).join(',\n')

  return {
    name: 'cypher-edition',
    resolveId(id) {
      return id === virtualEditionId ? resolvedVirtualEditionId : null
    },
    load(id) {
      if (id !== resolvedVirtualEditionId) return null
      return `export const edition = ${JSON.stringify({ id: edition.id, name: edition.name })}; export const enabledModuleIds = ${JSON.stringify(enabledModuleIds)}; export const routeDefinitions = [${routeSource}];`
    },
  }
}

export default defineConfig(({ mode }) => ({
  plugins: [vue(), vueDevTools(), editionPlugin(mode)],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    watch: { usePolling: true, interval: 300 },
  },
}))
