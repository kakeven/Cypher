<script setup>
    import CardSaldo from '@/components/CardSaldo.vue';
    import CardGastosRecentes from '@/components/CardGastosRecentes.vue';
    import CardOrcamento from '@/components/CardOrcamento.vue';
    import CardOportunidades from '@/components/CardOportunidades.vue';
    const gasto = 2500
    const total = 3000
    const progresso = (gasto/total) *100
</script>

<template>
    <div class="dashboard">
        <CardSaldo :gasto="gasto" :total="total" :progresso="progresso"/>
        <CardOportunidades/>
        <CardGastosRecentes/>
        <CardOrcamento/>
    </div>
    
    

</template>

<style>

    /* Importa os tokens globais uma única vez (ideal: mover para main.js) */
    
 
    body {
        background: var(--color-bg);
        font-family: var(--font-family);
    }
 
    .dashboard{
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: var(--space-lg);
        padding: var(--space-xl);
        max-width: 960px;
        margin: 0 auto;
    }
 
    /* Base compartilhada por todos os cards */
    .card {
        background: var(--color-surface);
        border: 1px solid var(--color-border);
        border-radius: var(--radius-lg);
        padding: var(--space-lg);
        box-shadow: var(--shadow-card);
        color: var(--color-text-primary);
        transition: transform 0.15s ease, border-color 0.15s ease;
    }
 
    .card:hover {
        transform: translateY(-2px);
        border-color: var(--color-accent);
    }
 
    .card-title {
        font-size: var(--font-size-sm);
        font-weight: var(--font-weight-medium);
        color: var(--color-text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: var(--space-md);
    }
</style>

