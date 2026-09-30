import './index.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { FrappeUI, useColorScheme } from 'frappe-ui'

import App from './App.vue'
import router from './router'

useColorScheme()

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(FrappeUI)
app.mount('#app')
