<script setup>
import { onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import AppSidebar from '@/components/AppSidebar.vue'
import AppToaster from '@/components/AppToaster.vue'

const route = useRoute()

function applyTitle() {
  const base = 'Cypher'
  document.title = route.meta?.title ? `${route.meta.title} · ${base}` : base
}

onMounted(applyTitle)
watch(() => route.meta?.title, applyTitle)
</script>

<template>
  <main class="app-shell">
    <AppSidebar />
    <section class="app-content"><RouterView v-slot="{ Component }"><component :is="Component" /></RouterView></section>
    <AppToaster />
  </main>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');
* { box-sizing: border-box; }
html, body, #app { min-width: 1024px; min-height: 100vh; margin: 0; }
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
</style>
