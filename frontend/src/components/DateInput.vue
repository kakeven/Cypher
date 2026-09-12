<script setup>
defineProps({
  modelValue: { type: String, default: '' },
  type: { type: String, default: 'date' },
  id: { type: String, default: undefined },
  required: { type: Boolean, default: false },
  min: { type: String, default: undefined },
  max: { type: String, default: undefined },
  ariaLabel: { type: String, default: undefined },
})
defineEmits(['update:modelValue', 'change'])
</script>

<template>
  <span class="date-input">
    <input
      :id="id"
      :value="modelValue"
      :type="type"
      :required="required"
      :min="min"
      :max="max"
      :aria-label="ariaLabel"
      class="input date-input__field"
      @input="$emit('update:modelValue', $event.target.value)"
      @change="$emit('change', $event)"
    />
    <svg
      class="date-input__icon"
      xmlns="http://www.w3.org/2000/svg"
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
      aria-hidden="true"
    >
      <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
      <line x1="16" y1="2" x2="16" y2="6" />
      <line x1="8" y1="2" x2="8" y2="6" />
      <line x1="3" y1="10" x2="21" y2="10" />
    </svg>
  </span>
</template>

<style scoped>
.date-input {
  position: relative;
  display: inline-flex;
  align-items: center;
  width: 100%;
}
.date-input__field {
  width: 100%;
  padding-right: 38px;
}
.date-input__icon {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-text-secondary);
  pointer-events: none;
}
.date-input__field::-webkit-calendar-picker-indicator {
  position: absolute;
  right: 0;
  top: 0;
  width: 38px;
  height: 100%;
  margin: 0;
  padding: 0;
  cursor: pointer;
  opacity: 0;
}
.date-input__field::-webkit-calendar-picker-indicator:hover {
  opacity: 0;
}
</style>
