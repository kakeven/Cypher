<script setup>
import { onMounted, ref } from 'vue'
import { IonButton, IonCard, IonCardContent, IonInput, IonSpinner } from '@ionic/vue'
import { SecureStorage } from '@aparajita/capacitor-secure-storage'

const emit = defineEmits(['unlocked'])
const pin = ref('')
const confirmPin = ref('')
const message = ref('')
const loading = ref(true)
const hasPin = ref(false)

async function hash(value) {
  const bytes = new TextEncoder().encode(value)
  const digest = await crypto.subtle.digest('SHA-256', bytes)
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, '0')).join('')
}

async function unlockWithBiometrics() {
  try {
    const { BiometricAuth } = await import('@aparajita/capacitor-biometric-auth')
    const state = await BiometricAuth.checkBiometry()
    if (state.isAvailable) {
      await BiometricAuth.authenticate({ reason: 'Desbloqueie seus dados financeiros' })
      emit('unlocked')
      return true
    }
  } catch {
    message.value = 'Use seu PIN para abrir o Cypher.'
  }
  return false
}

async function submitPin() {
  if (!hasPin.value) {
    if (!/^\d{6}$/.test(pin.value)) return message.value = 'Crie um PIN de 6 números.'
    if (pin.value !== confirmPin.value) return message.value = 'Os PINs não coincidem.'
    await SecureStorage.setItem('cypher.mobile.pin', await hash(pin.value))
    hasPin.value = true
    emit('unlocked')
    return
  }
  if (await hash(pin.value) === await SecureStorage.getItem('cypher.mobile.pin')) return emit('unlocked')
  message.value = 'PIN incorreto. Tente novamente.'
}

onMounted(async () => {
  hasPin.value = Boolean(await SecureStorage.getItem('cypher.mobile.pin'))
  loading.value = false
  if (hasPin.value) await unlockWithBiometrics()
})
</script>

<template>
  <section class="lock-screen">
    <IonCard class="lock-card">
      <IonCardContent>
        <div class="mark">C</div>
        <h1>Cypher</h1>
        <p>{{ hasPin ? 'Confirme sua identidade para acessar os dados.' : 'Crie um PIN para proteger este aplicativo.' }}</p>
        <IonSpinner v-if="loading" name="crescent" />
        <form v-else @submit.prevent="submitPin">
          <IonInput v-model="pin" type="password" inputmode="numeric" maxlength="6" :label="hasPin ? 'PIN' : 'Novo PIN'" label-placement="stacked" fill="outline" />
          <IonInput v-if="!hasPin" v-model="confirmPin" type="password" inputmode="numeric" maxlength="6" label="Confirmar PIN" label-placement="stacked" fill="outline" />
          <p v-if="message" class="lock-message">{{ message }}</p>
          <IonButton expand="block" type="submit">{{ hasPin ? 'Desbloquear' : 'Proteger aplicativo' }}</IonButton>
        </form>
      </IonCardContent>
    </IonCard>
  </section>
</template>

<style scoped>
.lock-screen { display: grid; min-height: 100vh; place-items: center; padding: 24px; background: radial-gradient(circle at top, #162a42 0%, var(--color-bg) 48%); }
.lock-card { width: min(100%, 390px); --background: var(--color-surface-raised); --color: var(--color-text-primary); border: 1px solid var(--color-border-strong); }
.lock-card ion-card-content { display: grid; gap: 18px; padding: 28px; }
.mark { display: grid; width: 42px; height: 42px; place-items: center; border: 1px solid var(--color-accent); border-radius: 50%; color: var(--color-accent-bright); font-family: var(--font-display); }
h1, p { margin: 0; } h1 { font-family: var(--font-display); font-size: 25px; font-weight: 400; } p { color: var(--color-text-secondary); line-height: 1.5; }
form { display: grid; gap: 13px; } ion-input { --background: var(--color-bg); --color: var(--color-text-primary); --highlight-color-focused: var(--color-accent); } .lock-message { color: var(--color-danger); font-size: 13px; }
</style>
