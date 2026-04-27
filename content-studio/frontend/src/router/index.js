import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: () => import('../views/Landing.vue'), meta: { public: true } },
    { path: '/login', component: () => import('../views/Login.vue'), meta: { public: true } },
    { path: '/auth/callback', component: () => import('../views/Login.vue'), meta: { public: true } },
    { path: '/invite', component: () => import('../views/Invite.vue'), meta: { public: true } },
    { path: '/app', component: () => import('../views/Generate.vue') },
    { path: '/creators', component: () => import('../views/Creators.vue') },
    { path: '/documents', component: () => import('../views/Documents.vue') },
    { path: '/styles', component: () => import('../views/StyleTemplates.vue') },
    { path: '/topics', component: () => import('../views/Topics.vue') },
    { path: '/generate', redirect: '/app' },
    { path: '/history', component: () => import('../views/History.vue') },
    { path: '/calendar', component: () => import('../views/Calendar.vue') },
    { path: '/viewpoints', component: () => import('../views/Viewpoints.vue') },
    { path: '/pricing', component: () => import('../views/Pricing.vue') },
    { path: '/settings', component: () => import('../views/Settings.vue') },
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
