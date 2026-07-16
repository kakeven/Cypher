<script setup>
    const gastos_recentes = [{nome:"netflix",valor:80},{nome:"Corte de cabelo",valor:30},{nome:"Corte de cabelo",valor:30},{nome:"Corte de cabelo",valor:30},{nome:"Corte de cabelo",valor:30}]
</script>

<template>
    <div class="card">
        <p class="card-title">Gastos recentes</p>
        <div class="lista">
            <div class="item" v-for="(gasto, i) in gastos_recentes" :key="i">
                <span class="item-nome">{{ gasto.nome }}</span>
                <span class="item-valor">R${{ gasto.valor }}</span>
            </div>
        </div>
    </div>
</template>

<style scoped>
    .lista {
        display: flex;
        flex-direction: column;
        gap: var(--space-sm);
    }

    .item {
        display: flex;
        justify-content: space-between;
        padding: var(--space-sm) 0;
        border-bottom: 1px solid var(--color-border);
        font-size: var(--font-size-base);
    }

    .item:last-child {
        border-bottom: none;
    }

    .item-nome {
        color: var(--color-text-secondary);
    }

    .item-valor {
        font-weight: var(--font-weight-medium);
        color: var(--color-text-primary);
    }
</style>