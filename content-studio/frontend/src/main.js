import { createApp } from 'vue'
import { createPinia } from 'pinia'
import naive from 'naive-ui'
import router from './router'
import App from './App.vue'
import { setApiRouter } from './api/index.js'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(naive)
app.mount('#app')

// 把 router 注册到 api 拦截器，避免用 window.location.href
setApiRouter(router)
