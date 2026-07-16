<script setup>
    const orcamentos = [{nome:"transporte",total:100,gasto:50},{nome:"saude",total:100,gasto:50},{nome:"transporte",total:100,gasto:50}]
</script>

<template>
    <div class="card">
        <p class="card-title">Orçamentos</p>
        <div class="lista">
            <div class="item" v-for="(orcamento, i) in orcamentos" :key="i">
                <div class="item-topo">
                    <span class="item-nome">{{ orcamento.nome }}</span>
                    <span class="item-valores">R${{ orcamento.gasto }} / R${{ orcamento.total }}</span>
                </div>
                <div class="barra-fundo">
                    <div
                        class="barra-preenchida"
                        :style="{ width: (orcamento.gasto / orcamento.total * 100) + '%' }"
                    ></div>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
    .lista {
        display: flex;
        flex-direction: column;
        gap: var(--space-md);
    }

    .item-topo {
        display: flex;
        justify-content: space-between;
        margin-bottom: var(--space-xs);
        font-size: var(--font-size-base);
    }

    .item-nome {
        color: var(--color-text-primary);
        text-transform: capitalize;
    }

    .item-valores {
        color: var(--color-text-secondary);
        font-size: var(--font-size-sm);
    }

    .barra-fundo {
        width: 100%;
        height: 8px;
        border-radius: 999px;
        background: var(--color-border);
        overflow: hidden;
    }

    .barra-preenchida {
        height: 100%;
        border-radius: 999px;
        background: var(--color-accent);
    }
</style>