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
    .dashboard{
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 20px;
    }

</style>