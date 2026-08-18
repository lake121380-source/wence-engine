import { createRouter, createWebHistory } from 'vue-router'
import Creators from '../views/Creators.vue'
import Documents from '../views/Documents.vue'
import StyleTemplates from '../views/StyleTemplates.vue'
import Generate from '../views/Generate.vue'
import History from '../views/History.vue'
import Topics from '../views/Topics.vue'
import Viewpoints from '../views/Viewpoints.vue'
import Login from '../views/Login.vue'
import Invite from '../views/Invite.vue'
import Pricing from '../views/Pricing.vue'
import Settings from '../views/Settings.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: Login, meta: { public: true } },
    { path: '/auth/callback', component: Login, meta: { public: true } },
    { path: '/invite', component: Invite, meta: { public: true } },
    { path: '/', component: Generate },
    { path: '/creators', component: Creators },
    { path: '/documents', component: Documents },
    { path: '/styles', component: StyleTemplates },
    { path: '/topics', component: Topics },
    { path: '/generate', redirect: '/' },
    { path: '/history', component: History },
    { path: '/viewpoints', component: Viewpoints },
    { path: '/pricing', component: Pricing },
    { path: '/settings', component: Settings },
    { path: '/:pathMatch(.*)*', component: { template: '<div style="text-align:center;padding:80px 20px;"><h1 style="font-size:48px;color:#666;">404</h1><p style="color:#999;margin:16px 0;">页面不存在</p><a href="/" style="color:#6366f1;">返回首页</a></div>' }, meta: { public: true } },
  ]
})

function isTokenExpired(token) {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.exp && payload.exp * 1000 < Date.now()
  } catch { return true }
}

// 路由守卫：未登录跳转到登录页
router.beforeEach((to) => {
  if (to.meta.public) return true
  const token = localStorage.getItem('cs_token')
  if (!token || isTokenExpired(token)) {
    localStorage.removeItem('cs_token')
    localStorage.removeItem('cs_user')
    localStorage.removeItem('cs_tenant')
    return { path: '/login' }
  }
  return true
})

export default router
