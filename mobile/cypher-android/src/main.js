import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { IonicVue } from '@ionic/vue'

import App from './App.vue'
import router from './router'
import { useDataSource } from './services/api'
import { createDataSource } from './services/mobileDataSource'
import './assets/variaveis.css'
import '@ionic/vue/css/core.css'
import '@ionic/vue/css/normalize.css'
import '@ionic/vue/css/structure.css'
import '@ionic/vue/css/typography.css'

const app = createApp(App)

app.use(createPinia())
app.use(IonicVue)
app.use(router)

createDataSource().then((source) => {
  useDataSource(source)
  app.mount('#app')
})
