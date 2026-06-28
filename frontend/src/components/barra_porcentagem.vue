<script setup>
    import { ref} from 'vue';
    defineProps({
        progresso: Number
    })
</script>

<template>
    <div class="barra-container">
        <div class="barra-fill" :style="{width: progresso + '%'}"></div>

    </div>

</template>

<style scoped>
.barra-container {
  width: 100%;
  height: 12px;
  background: #e0e0e0;
  border-radius: 6px;
  overflow: hidden;
}
.barra-fill {
  height: 100%;
  background: #42b883;
  transition: width 0.3s ease;
}
</style>