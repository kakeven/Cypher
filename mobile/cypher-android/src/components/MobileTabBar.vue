<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { IonActionSheet, IonLabel, IonTabBar, IonTabButton } from '@ionic/vue'
import { navigationItems } from '@/modules/registry'

const showMore = ref(false)
const router = useRouter()
const primaryItems = computed(() => navigationItems.slice(0, 4))
const moreButtons = computed(() => [
  ...navigationItems.slice(4).map((item) => ({ text: item.label, data: { href: item.path } })),
  { text: 'Cancelar', role: 'cancel' },
])

function navigate(event) {
  const href = event.detail?.data?.href
  if (href) router.push(href)
}
</script>

<template>
  <footer class="mobile-tabs">
    <IonTabBar slot="bottom">
      <IonTabButton v-for="item in primaryItems" :key="item.path" :tab="item.moduleId" :href="item.path"><IonLabel>{{ item.label }}</IonLabel></IonTabButton>
      <IonTabButton v-if="navigationItems.length > 4" tab="more" @click="showMore = true"><IonLabel>Mais</IonLabel></IonTabButton>
    </IonTabBar>
    <IonActionSheet :is-open="showMore" header="Mais áreas" :buttons="moreButtons" @did-dismiss="showMore = false" @ion-action-sheet-did-dismiss="navigate" />
  </footer>
</template>

<style scoped>
.mobile-tabs { position: fixed; z-index: 20; right: 0; bottom: 0; left: 0; border-top: 1px solid var(--color-border); }
ion-tab-bar { --background: var(--color-surface-raised); --color: var(--color-text-muted); --color-selected: var(--color-accent-bright); height: calc(58px + env(safe-area-inset-bottom)); padding-bottom: env(safe-area-inset-bottom); }
ion-tab-button { font-family: var(--font-family); font-size: 11px; }
</style>
