<script setup>
    import barra_porcentagem from '@/components/barra_porcentagem.vue';
    
    defineProps({
        gasto:Number,
        total: Number,
        progresso: Number
    })
     
</script>


<template>
    <div class="card">
        <p>{{ gasto }}/{{ total }}</p>
        <barra_porcentagem :progresso="progresso"/>
    </div>
</template>