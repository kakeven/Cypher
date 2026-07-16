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
        <p class="card-title">Saldo</p>
        <p class="valor">
            <span class="valor-gasto">R${{ gasto }}</span>
            <span class="valor-total"> / R${{ total }}</span>
        </p>
        <barra_porcentagem :progresso="progresso"/>
    </div>
</template>

<style scoped>
    .valor {
        margin: 0 0 var(--space-md);
    }

    .valor-gasto {
        font-size: var(--font-size-xl);
        font-weight: var(--font-weight-bold);
        color: var(--color-text-primary);
    }

    .valor-total {
        font-size: var(--font-size-base);
        color: var(--color-text-muted);
    }
</style>