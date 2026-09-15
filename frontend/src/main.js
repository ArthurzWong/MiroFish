import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import i18n from './i18n'

// Self-hosted typefaces (no runtime Google Fonts request for Latin text)
import '@fontsource-variable/bricolage-grotesque'
import '@fontsource-variable/outfit'
import '@fontsource-variable/jetbrains-mono'

// Deep Ocean design system
import './styles/theme.css'

const app = createApp(App)

app.use(router)
app.use(i18n)

app.mount('#app')
