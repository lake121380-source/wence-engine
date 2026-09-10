import { createRouter, createWebHistory } from 'vue-router'

// 按路由懒加载：首屏只下载当前页面，避免把 12 个视图全塞进一个 bundle。
const Home = () => import('../views/Home.vue')
const Creators = () => import('../views/Creators.vue')
const Documents = () => import('../views/Documents.vue')
const StyleTemplates = () => import('../views/StyleTemplates.vue')
const Generate = () => import('../views/Generate.vue')
const History = () => import('../views/History.vue')
const Topics = () => import('../views/Topics.vue')
const Viewpoints = () => import('../views/Viewpoints.vue')
const Login = () => import('../views/Login.vue')
const Invite = () => import('../views/Invite.vue')
const Pricing = () => import('../views/Pricing.vue')
const Settings = () => import('../views/Settings.vue')

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Home, meta: { public: true } },
    { path: '/login', component: Login, meta: { public: true } },
    { path: '/auth/callback', component: Login, meta: { public: true } },
    { path: '/invite', component: Invite, meta: { public: true } },
    { path: '/generate', component: Generate },
    { path: '/workspace', redirect: '/generate' },
    { path: '/creators', component: Creators },
    { path: '/documents', component: Documents },
    { path: '/styles', component: StyleTemplates },
    { path: '/topics', component: Topics },
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
