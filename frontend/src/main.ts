import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'   // ← Added for state management

// Import global styles
import './style.css'

const app = createApp(App)

const pinia = createPinia()

app.use(router)
app.use(pinia)        // ← This is required for Pinia store to work

app.mount('#app')