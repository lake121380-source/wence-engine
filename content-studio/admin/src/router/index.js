import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { noAuth: true },
  },
  {
    path: '/',
    component: () => import('../views/Layout.vue'),
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
      { path: 'tenants', name: 'Tenants', component: () => import('../views/Tenants.vue') },
      { path: 'tenants/:id', name: 'TenantDetail', component: () => import('../views/TenantDetail.vue') },
      { path: 'users', name: 'Users', component: () => import('../views/Users.vue') },
      { path: 'orders', name: 'Orders', component: () => import('../views/Orders.vue') },
      { path: 'content', name: 'Content', component: () => import('../views/Content.vue') },
      { path: 'settings', name: 'AdminSettings', component: () => import('../views/AdminSettings.vue') },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: { template: '<div style="text-align:center;padding:80px 20px;"><h1 style="font-size:48px;color:#666;">404</h1><p style="color:#999;margin:16px 0;">页面不存在</p><a href="#/" style="color:#63e2b7;">返回首页</a></div>' },
    meta: { noAuth: true },
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

function isTokenExpired(token) {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.exp && payload.exp * 1000 < Date.now()
  } catch { return true }
}

router.beforeEach((to) => {
  if (to.meta.noAuth) return true
  const token = localStorage.getItem('admin_token')
  if (!token || isTokenExpired(token)) {
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_user')
    return { path: '/login' }
  }
  return true
})

export default router
