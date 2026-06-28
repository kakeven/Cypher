<script setup>
    const oportunidades = [{nome:"transporte",queda_porcentagem:10,valor_atual:10},{nome:"transporte",queda_porcentagem:10,valor_atual:10},{nome:"transporte",queda_porcentagem:10,valor_atual:10}]
</script>

<template>
    <div class="oportunidades">
        <div v-for="oportunidade in oportunidades" :key="oportunidade.nome">
            {{ oportunidade.nome }}: {{ oportunidade.valor_atual }} - {{ oportunidade.queda_porcentagem }}%

        </div>
    </div>
</template>