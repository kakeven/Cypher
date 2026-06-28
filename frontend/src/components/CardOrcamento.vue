<script setup>
    const orcamentos = [{nome:"transporte",total:100,gasto:50},{nome:"transporte",total:100,gasto:50},{nome:"transporte",total:100,gasto:50}]
</script>

<template>
    <div class="orcamentos">
        <div v-for="orcamento in orcamentos" :key="orcamento.nome">
            {{ orcamento.nome }} - {{ orcamento.gasto }}/{{ orcamento.total }}

        </div>
    </div>
</template>