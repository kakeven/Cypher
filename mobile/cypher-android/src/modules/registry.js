import catalog from './catalog.json'
import { edition, enabledModuleIds } from 'virtual:cypher-edition'

const modulesById = new Map(catalog.modules.map((module) => [module.id, module]))

export { edition }

export const enabledModules = enabledModuleIds.map((id) => modulesById.get(id))

export const navigationItems = enabledModules
  .filter((module) => module.navigation && module.routes.length)
  .sort((left, right) => left.navigation.order - right.navigation.order)
  .map((module) => ({
    moduleId: module.id,
    path: module.routes[0].path,
    label: module.navigation.label,
  }))
