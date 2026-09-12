<script setup>
import { useToastState, useToast } from '@/composables/useToast'

const state = useToastState()
const { dismiss } = useToast()
</script>

<template>
  <div class="toast-stack" role="region" aria-live="polite" aria-label="Notificações">
    <div
      v-for="item in state.items"
      :key="item.id"
      :class="['toast', `toast--${item.type}`]"
      role="status"
    >
      <span>{{ item.message }}</span>
      <button type="button" class="toast__close" aria-label="Fechar notificação" @click="dismiss(item.id)">×</button>
    </div>
  </div>
</template>

<style scoped>
.toast-stack {
  position: fixed;
  bottom: 24px;
  right: 24px;
  display: grid;
  gap: 10px;
  z-index: 100;
  max-width: 360px;
}
.toast {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 8px;
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-card);
  font-size: 14px;
}
.toast--success { border-color: var(--color-success); }
.toast--error { border-color: var(--color-danger); }
.toast__close {
  background: transparent;
  border: 0;
  color: var(--color-text-secondary);
  cursor: pointer;
  font-size: 18px;
  line-height: 1;
  padding: 0 4px;
}
.toast__close:hover { color: var(--color-text-primary); }
</style>
