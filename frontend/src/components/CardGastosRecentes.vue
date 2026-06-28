<script setup>
    const gastos_recentes = [{nome:"netflix",valor:80},{nome:"Corte de cabelo",valor:30},{nome:"Corte de cabelo",valor:30},{nome:"Corte de cabelo",valor:30},{nome:"Corte de cabelo",valor:30}]
</script>

<template>
    <div class="gastos_recentes">
        Gastos recentes
        <div v-for="gasto in gastos_recentes" :key="gasto.nome">
            {{ gasto.nome }} - R${{ gasto.valor }}
        </div>

    </div>
</template>
