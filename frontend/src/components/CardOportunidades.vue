<script setup>
    const oportunidades = [{nome:"transporte",queda_porcentagem:10,valor_atual:10},{nome:"transporte",queda_porcentagem:10,valor_atual:10},{nome:"transporte",queda_porcentagem:10,valor_atual:10}]
</script>

<template>
    <div class="card">
        <p class="card-title">Oportunidades</p>
        <div class="lista">
            <div class="item" v-for="(oportunidade, i) in oportunidades" :key="i">
                <span class="item-nome">{{ oportunidade.nome }}</span>
                <span class="item-direita">
                    <span class="item-valor">R${{ oportunidade.valor_atual }}</span>
                    <span class="item-queda">-{{ oportunidade.queda_porcentagem }}%</span>
                </span>
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
        align-items: center;
        padding: var(--space-sm) 0;
        border-bottom: 1px solid var(--color-border);
        font-size: var(--font-size-base);
    }

    .item:last-child {
        border-bottom: none;
    }

    .item-nome {
        color: var(--color-text-primary);
        text-transform: capitalize;
    }

    .item-direita {
        display: flex;
        align-items: center;
        gap: var(--space-sm);
    }

    .item-valor {
        color: var(--color-text-secondary);
    }

    .item-queda {
        font-size: var(--font-size-sm);
        font-weight: var(--font-weight-medium);
        color: var(--color-success);
        background: var(--color-success-bg);
        padding: 2px 8px;
        border-radius: 999px;
    }
</style>