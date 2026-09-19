<script setup>
import { edition, navigationItems } from '@/modules/registry'
</script>

<template>
  <aside class="sidebar">
    <div class="brand"><b>C</b><span>cypher</span></div>
    <nav aria-label="Navegação principal">
      <RouterLink v-for="link in navigationItems" :key="link.path" :to="link.path"><i aria-hidden="true" />{{ link.label }}</RouterLink>
    </nav>
    <small><b>{{ edition.name }}</b>Seus dados ficam neste computador.</small>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 224px;
  min-width: 224px;
  min-height: 100vh;
  padding: 28px 14px 20px;
  display: flex;
  flex-direction: column;
  background: var(--color-surface-raised);
  border-right: 1px solid var(--color-border);
}
.brand {
  display: flex;
  gap: 9px;
  align-items: center;
  padding: 4px 10px 40px;
  color: var(--color-text-primary);
  font-family: var(--font-display);
  font-size: 21px;
  letter-spacing: 0.04em;
}
.brand b {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border: 1px solid var(--color-border-strong);
  border-radius: 50%;
  background: var(--color-surface);
}
nav {
  display: grid;
  gap: 4px;
}
nav a {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--color-text-secondary);
  text-decoration: none;
  padding: 11px 12px;
  border-radius: 7px;
  font-family: var(--font-display);
  font-size: 13px;
  letter-spacing: 0.01em;
  border: 1px solid transparent;
}
nav i {
  width: 6px;
  height: 6px;
  border: 1px solid currentColor;
  border-radius: 50%;
}
nav a:hover,
nav a.router-link-active {
  color: var(--color-text-primary);
  background: var(--color-accent-bg);
  border-color: transparent;
  box-shadow: inset 3px 0 var(--color-accent);
}
nav a.router-link-active i {
  background: var(--color-accent);
}
small {
  margin-top: auto;
  padding: 10px;
  color: var(--color-text-muted);
  line-height: 1.4;
  font-size: 11px;
  border-top: 1px solid var(--color-border);
}
small b {
  display: block;
  margin-bottom: 6px;
  color: var(--color-text-secondary);
  font-family: var(--font-display);
  font-size: 10px;
  font-weight: 500;
}
</style>
