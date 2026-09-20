<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { IonIcon } from '@ionic/vue'
import { analyticsOutline, calendarOutline, cardOutline, cashOutline, ellipsisHorizontalOutline, homeOutline, repeatOutline, trophyOutline, walletOutline } from 'ionicons/icons'
import { navigationItems } from '@/modules/registry'

const showMore = ref(false)
const router = useRouter()
const route = useRoute()
const primaryItems = computed(() => navigationItems.slice(0, 4))
const moreItems = computed(() => navigationItems.slice(4))

const icons = {
  dashboard: homeOutline,
  transactions: cashOutline,
  budgets: walletOutline,
  goals: trophyOutline,
  receivables: analyticsOutline,
  recurring: repeatOutline,
  cards: cardOutline,
  subscriptions: calendarOutline,
}

function go(path) {
  showMore.value = false
  router.push(path)
}
</script>

<template>
  <footer class="mobile-tabs">
    <button v-if="showMore" type="button" class="more-backdrop" aria-label="Fechar menu adicional" @click="showMore = false" />
    <div v-if="showMore" id="more-navigation" class="more-stack" aria-label="Mais áreas">
      <button v-for="item in moreItems" :key="item.path" type="button" :class="{ active: route.path === item.path }" @click="go(item.path)">
        <span>{{ item.label }}</span>
        <i><IonIcon :icon="icons[item.moduleId] || analyticsOutline" /></i>
      </button>
    </div>
    <nav class="tab-list" aria-label="Navegação principal">
      <button v-for="item in primaryItems" :key="item.path" type="button" :class="{ active: route.path === item.path }" @click="go(item.path)"><IonIcon :icon="icons[item.moduleId] || analyticsOutline" /><span>{{ item.label }}</span></button>
      <button v-if="navigationItems.length > 4" type="button" :class="{ active: showMore }" :aria-expanded="showMore" aria-controls="more-navigation" @click="showMore = !showMore"><IonIcon :icon="ellipsisHorizontalOutline" /><span>Mais</span></button>
    </nav>
  </footer>
</template>

<style scoped>
.mobile-tabs { position: fixed; z-index: 20; right: 0; bottom: 0; left: 0; border-top: 1px solid var(--color-border); }
.more-backdrop { position: fixed; z-index: 0; inset: 0; border: 0; background: rgba(2, 7, 14, .22); }
.more-stack { position: absolute; z-index: 1; right: 12px; bottom: calc(76px + env(safe-area-inset-bottom)); display: grid; gap: 10px; transform-origin: right bottom; animation: more-stack-in .24s cubic-bezier(.2, .85, .3, 1.15) both; }
.more-stack button { display: flex; align-items: center; justify-content: flex-end; gap: 10px; border: 0; color: var(--color-text-primary); background: transparent; font: inherit; cursor: pointer; animation: more-item-in .28s cubic-bezier(.2, .85, .3, 1.1) both; }
.more-stack button:nth-child(2) { animation-delay: .045s; }
.more-stack button:nth-child(3) { animation-delay: .09s; }
.more-stack button:nth-child(4) { animation-delay: .135s; }
.more-stack span { padding: 7px 10px; border-radius: 7px; background: var(--color-surface-raised); box-shadow: 0 7px 18px rgba(0, 0, 0, .26); font-size: 12px; white-space: nowrap; }
.more-stack i { display: grid; width: 44px; height: 44px; place-items: center; border: 1px solid rgba(90, 141, 255, .34); border-radius: 50%; color: var(--color-accent-bright); background: var(--color-surface-raised); box-shadow: 0 7px 18px rgba(0, 0, 0, .32); }
.more-stack ion-icon { margin: 0; font-size: 21px; }
.more-stack button.active i { border-color: var(--color-accent); color: #fff; background: var(--color-accent); }
.tab-list { position: relative; z-index: 2; display: grid; grid-template-columns: repeat(5, 1fr); height: calc(64px + env(safe-area-inset-bottom)); padding-bottom: env(safe-area-inset-bottom); background: rgba(11, 21, 34, .96); border-top: 1px solid var(--color-border); }
.tab-list button { display: grid; place-items: center; align-content: center; gap: 3px; border: 0; padding: 4px 1px; color: #90a0b8; background: transparent; font-family: var(--font-family); font-size: 9px; letter-spacing: -.01em; }
.tab-list button.active { color: #4385ff; }
ion-icon { font-size: 20px; margin-bottom: 3px; }
.tab-list button:last-child ion-icon { transition: transform .22s ease; }
.tab-list button:last-child.active ion-icon { transform: rotate(90deg); }
@keyframes more-stack-in {
  from { opacity: 0; transform: translateY(12px) scale(.92); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
@keyframes more-item-in {
  from { opacity: 0; transform: translateX(16px) scale(.82); }
  to { opacity: 1; transform: translateX(0) scale(1); }
}
@media (prefers-reduced-motion: reduce) {
  .more-stack, .more-stack button { animation: none; }
  .tab-list button:last-child ion-icon { transition: none; }
}
</style>
