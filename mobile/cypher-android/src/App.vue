<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Capacitor } from '@capacitor/core'
import { IonApp } from '@ionic/vue'
import AppSidebar from '@/components/AppSidebar.vue'
import AppToaster from '@/components/AppToaster.vue'
import AppLock from '@/components/AppLock.vue'
import MobileTabBar from '@/components/MobileTabBar.vue'

const route = useRoute()
const isNative = Capacitor.isNativePlatform()
const viewportWidth = ref(window.innerWidth)
const isMobile = computed(() => isNative || viewportWidth.value <= 640)
const isUnlocked = ref(!isNative)

function applyTitle() {
  const base = 'Cypher'
  document.title = route.meta?.title ? `${route.meta.title} · ${base}` : base
}

function syncViewport() { viewportWidth.value = window.innerWidth }

onMounted(() => {
  applyTitle()
  window.addEventListener('resize', syncViewport)
})
onBeforeUnmount(() => window.removeEventListener('resize', syncViewport))
watch(() => route.meta?.title, applyTitle)
</script>

<template>
  <IonApp>
    <AppLock v-if="isNative && !isUnlocked" @unlocked="isUnlocked = true" />
    <main v-else class="app-shell" :class="{ 'app-shell--mobile': isMobile }">
      <AppSidebar v-if="!isMobile" />
      <section class="app-content"><RouterView v-slot="{ Component }"><component :is="Component" /></RouterView></section>
      <MobileTabBar v-if="isMobile" />
      <AppToaster />
    </main>
  </IonApp>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');
* { box-sizing: border-box; }
html, body, #app { min-height: 100vh; margin: 0; }
body { background: var(--color-bg); color: var(--color-text-primary); font-family: var(--font-family); }
button, input, select, textarea { font: inherit; }
button:focus-visible, a:focus-visible, input:focus-visible, select:focus-visible { outline: 2px solid var(--color-accent-bright); outline-offset: 3px; }
.app-shell { display: flex; min-height: 100vh; }
.app-content { flex: 1; min-width: 0; padding: 26px clamp(28px, 4vw, 56px) 36px; }
.page-header { display: flex; justify-content: space-between; align-items: start; margin-bottom: 22px; }
.page-header h1 { margin: 0; font-family: var(--font-display); font-size: 26px; font-weight: 400; letter-spacing: -0.02em; }
.page-header p { color: var(--color-text-secondary); margin: 6px 0 0; }
.button { border: 1px solid var(--color-accent); border-radius: 6px; padding: 10px 14px; cursor: pointer; background: var(--color-accent); color: #fff; font-weight: 650; box-shadow: none; }
.button:hover { background: var(--color-accent-bright); border-color: var(--color-accent-bright); }
.button:disabled { opacity: 0.6; cursor: not-allowed; }
.button--ghost { background: transparent; color: var(--color-text-secondary); border-color: var(--color-border); box-shadow: none; }
.button--ghost:hover { color: var(--color-accent-bright); border-color: var(--color-border-strong); background: var(--color-accent-bg); }
.button--danger { color: var(--color-danger); }
.card { background: var(--color-surface); border: 1px solid var(--color-border); border-radius: 9px; padding: 20px; box-shadow: var(--shadow-card); }
.form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.form-grid label { display: grid; gap: 7px; color: var(--color-text-secondary); font-size: 13px; }
.form-grid .full { grid-column: 1 / -1; }
.input { border: 1px solid var(--color-border); border-radius: 6px; padding: 10px 11px; color: var(--color-text-primary); background: var(--color-bg); }
.input:hover { border-color: var(--color-border-strong); }
.input:focus { outline: 0; border-color: var(--color-accent); box-shadow: 0 0 0 3px var(--color-accent-bg); }
.message { padding: 12px 14px; border: 1px solid rgba(255, 119, 112, 0.35); border-radius: 8px; background: var(--color-danger-bg); color: #ffaaa5; margin-bottom: 16px; }
.empty { color: var(--color-text-secondary); padding: 32px; text-align: center; }
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0,0,0,0); white-space: nowrap; border: 0; }
@media (max-width: 1120px) { .app-content { padding: 24px 28px; } }
.app-shell--mobile { display: block; height: 100dvh; min-height: 0; overflow-x: hidden; overflow-y: auto; padding-bottom: calc(70px + env(safe-area-inset-bottom)); background: var(--color-bg); touch-action: pan-y; -webkit-overflow-scrolling: touch; }
.app-shell--mobile .app-content { min-height: 100%; padding: max(18px, env(safe-area-inset-top)) 14px calc(98px + env(safe-area-inset-bottom)); }
.app-shell--mobile .page-header { gap: 10px; flex-wrap: wrap; margin-bottom: 18px; }
.app-shell--mobile .page-header h1 { font-family: var(--font-family); font-size: 21px; font-weight: 700; letter-spacing: -0.045em; }
.app-shell--mobile .page-header p { margin-top: 3px; font-size: 12px; }
.app-shell--mobile .form-grid { grid-template-columns: 1fr; }
.app-shell--mobile .card { padding: 14px; border-radius: 12px; box-shadow: 0 10px 24px rgba(0, 0, 0, .16); }
.app-shell--mobile .button { min-height: 42px; border-radius: 10px; }
.app-shell--mobile .input { min-height: 42px; border-radius: 10px; background: rgba(7, 15, 25, .52); }
.app-shell--mobile .dashboard-summary,
.app-shell--mobile .dashboard-bottom,
.app-shell--mobile .category-visualization,
.app-shell--mobile .receivable-workspace,
.app-shell--mobile .two-columns { grid-template-columns: 1fr; }
.app-shell--mobile .quick-stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.app-shell--mobile .goals,
.app-shell--mobile .receivables,
.app-shell--mobile .receivable-list,
.app-shell--mobile .recurring-grid,
.app-shell--mobile .metric-grid { grid-template-columns: 1fr; }
.app-shell--mobile .payment-form,
.app-shell--mobile .deposit { grid-template-columns: 1fr; align-items: stretch; }
.app-shell--mobile .import-controls,
.app-shell--mobile .agenda-header,
.app-shell--mobile .filters,
.app-shell--mobile .summary { flex-wrap: wrap; }
.app-shell--mobile .file { min-width: 0; width: 100%; }
.app-shell--mobile .table-card,
.app-shell--mobile .invoice-detail { overflow-x: auto; }
.app-shell--mobile .drawer { width: 100vw; max-width: 100vw; }
</style>
