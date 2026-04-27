import axios from 'axios'

const api = axios.create({
  baseURL: '/api/admin',
  timeout: 30000,
})

// 请求拦截器：注入 token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('admin_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：401 跳登录
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('admin_token')
      localStorage.removeItem('admin_user')
      window.location.hash = '#/login'
    }
    return Promise.reject(err)
  }
)

export const authApi = {
  login: (data) => api.post('/login', data),
  me: () => api.get('/me'),
  init: (data) => api.post('/init', data),
  changePassword: (data) => api.post('/change-password', data),
}

export const adminApi = {
  list: () => api.get('/admins'),
  create: (data) => api.post('/admins/create', data),
  delete: (id) => api.delete(`/admins/${id}`),
}

export const dashboardApi = {
  get: () => api.get('/dashboard'),
}

export const tenantApi = {
  list: (params) => api.get('/tenants', { params }),
  detail: (id) => api.get(`/tenants/${id}`),
  edit: (id, data) => api.patch(`/tenants/${id}`, data),
  delete: (id) => api.delete(`/tenants/${id}`),
}

export const userApi = {
  list: (params) => api.get('/users', { params }),
  create: (data) => api.post('/users/create', data),
  edit: (id, data) => api.patch(`/users/${id}/edit`, data),
  resetPassword: (id, data) => api.post(`/users/${id}/reset-password`, data),
  ban: (id) => api.patch(`/users/${id}/ban`),
  unban: (id) => api.patch(`/users/${id}/unban`),
  extendSubscription: (id, data) => api.post(`/users/${id}/subscription/extend`, data),
  revokeSubscription: (id) => api.post(`/users/${id}/subscription/revoke`),
}

export const orderApi = {
  list: (params) => api.get('/orders', { params }),
}

export const contentApi = {
  creators: (params) => api.get('/creators', { params }),
  topics: (params) => api.get('/topics', { params }),
  generations: (params) => api.get('/generations', { params }),
}

export const exportApi = {
  users: () => api.get('/export/users', { responseType: 'blob' }),
  orders: () => api.get('/export/orders', { responseType: 'blob' }),
}

export default api
