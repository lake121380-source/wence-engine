import { createApp } from 'vue'
import { createPinia } from 'pinia'
import naive from 'naive-ui'
import router from './router'
import App from './App.vue'
import { setApiRouter, setSubscriptionStoreGetter } from './api/index.js'
import { useSubscriptionStore } from './stores/subscription.js'

const pinia = createPinia()
const app = createApp(App)
app.use(pinia)
app.use(router)
app.use(naive)
app.mount('#app')

// 把 router 注册到 api 拦截器，避免用 window.location.href
setApiRouter(router)
// 把 subscription store getter 注册到 api 拦截器，以便 402 时弹窗提示
setSubscriptionStoreGetter(() => useSubscriptionStore())
