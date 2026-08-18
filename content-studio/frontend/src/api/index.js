import axios from 'axios'

// 延迟获取 router，避免循环依赖（main.js 挂载后才可用）
let _router = null
export function setApiRouter(r) { _router = r }

function safeRedirect(path) {
  if (_router) {
    _router.push(path).catch(() => {})
  } else if (typeof window !== 'undefined') {
    window.location.href = path
  }
}

const api = axios.create({ baseURL: '/api' })

// JWT 拦截器：自动注入 Authorization header
api.interceptors.request.use(config => {
  const token = localStorage.getItem('cs_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// 401 → 跳登录；402 → 跳订阅页
api.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('cs_token')
      localStorage.removeItem('cs_user')
      localStorage.removeItem('cs_tenant')
      safeRedirect('/login')
    }
    if (err.response?.status === 402) {
      const currentPath = _router?.currentRoute?.value?.path ?? window.location.pathname
      if (!currentPath.startsWith('/pricing')) {
        safeRedirect('/pricing')
      }
    }
    return Promise.reject(err)
  }
)

export const authApi = {
  // 邮箱登录/注册
  login: (data) => api.post('/auth/login', data),
  register: (data) => api.post('/auth/register', data),
  // Google / GitHub OAuth
  googleUrl: (params) => api.get('/auth/google/url', { params }),
  googleCallback: (data) => api.post('/auth/google/callback', data),
  githubUrl: (params) => api.get('/auth/github/url', { params }),
  githubCallback: (data) => api.post('/auth/github/callback', data),
  // 微信（保留兼容）
  getOAuthUrl: (params) => api.get('/auth/wechat/oauth-url', { params }),
  oauthCallback: (data) => api.post('/auth/wechat/callback', data),
  createScene: () => api.post('/auth/scene/create'),
  pollScene: (sceneId) => api.get(`/auth/scene/${sceneId}/status`),
  // 通用
  refresh: () => api.post('/auth/refresh'),
  me: () => api.get('/auth/me'),
  changePassword: (data) => api.post('/auth/change-password', data),
}

export const creatorsApi = {
  list: () => api.get('/creators'),
  add: (platform, identifier) => api.post('/creators', { platform, identifier }),
  crawl: (id, maxVideos = 30) => api.post(`/creators/${id}/crawl?max_videos=${maxVideos}`),
  analyzeStyle: (id) => api.post(`/creators/${id}/analyze-style`),
  delete: (id) => api.delete(`/creators/${id}`),
  videos: (id) => api.get(`/creators/${id}/videos`),
  discover: (params) => api.post('/creators/discover', params),
  batchAdd: (platformIds) => api.post('/creators/batch-add', platformIds),
  autoDiscoverAndCrawl: (params) => api.post('/creators/auto-discover-and-crawl', params),
  getDiscoverTask: (taskId) => api.get(`/creators/discover-task/${taskId}`),
  searchWeixin: (keyword, page = 0) => api.get('/creators/search-weixin', { params: { keyword, page } }),
}

export const documentsApi = {
  list: (folder) => api.get('/documents', { params: folder !== undefined ? { folder } : {} }),
  get: (id) => api.get(`/documents/${id}`),
  getAnalysis: (id) => api.get(`/documents/${id}/analysis`),
  listFolders: () => api.get('/documents/folders'),
  createFolder: (name) => api.post('/documents/folders', { name }),
  deleteFolder: (name) => api.delete(`/documents/folders/${encodeURIComponent(name)}`),
  upload: (file, tags = '', folderName = '') => {
    const form = new FormData()
    form.append('file', file)
    form.append('tags', tags)
    if (folderName) form.append('folder_name', folderName)
    return api.post('/documents/upload', form)
  },
  addText: (data) => api.post('/documents/add-text', data),
  moveFolder: (id, folderName) => api.patch(`/documents/${id}/folder`, { folder_name: folderName }),
  delete: (id) => api.delete(`/documents/${id}`),
}

export const styleApi = {
  list: () => api.get('/style-templates'),
  create: (data) => api.post('/style-templates', data),
  delete: (id) => api.delete(`/style-templates/${id}`),
  analyzeCombined: (data) => api.post('/style-templates/analyze-combined', data),
}

export const generateApi = {
  generate: (payload) => api.post('/generate', payload),
  generateStream: (payload) => {
    const token = localStorage.getItem('cs_token')
    const headers = { 'Content-Type': 'application/json' }
    if (token) headers['Authorization'] = `Bearer ${token}`
    return fetch('/api/generate/stream', {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    })
  },
  list: (limit = 20) => api.get(`/generations?limit=${limit}`),
  rate: (id, rating) => api.patch(`/generations/${id}/rate?rating=${rating}`),
}

export const statsApi = {
  get: () => api.get('/knowledge/stats'),
}

export const topicsApi = {
  search: (params) => api.post('/topics/search', params),
  save: (video) => api.post('/topics/save', video),
  delete: (id) => api.delete(`/topics/${id}`),
  batchDelete: (ids) => api.post('/topics/batch-delete', { ids }),
  list: (params = {}) => {
    const qs = new URLSearchParams()
    if (params.keyword) qs.append('keyword', params.keyword)
    if (params.platform) qs.append('platform', params.platform)
    if (params.status) qs.append('status', params.status)
    if (params.limit) qs.append('limit', params.limit)
    return api.get(`/topics?${qs.toString()}`)
  },
  updateStatus: (id, status) => api.patch(`/topics/${id}/status`, { status }),
  fetchDetail: (id) => api.post(`/topics/${id}/fetch-detail`),
  batchFetchDetail: (topicIds) => api.post('/topics/batch-fetch-detail', topicIds),
  discoverCreators: (params) => api.post('/creators/discover', params),
  analyzeTopic: (id) => api.post(`/topics/${id}/analyze`),
  getTopicAnalysis: (id) => api.get(`/topics/${id}/analysis`),
  batchAnalyze: (params) => api.post('/topics/batch-analyze', params),
  keywords: () => api.get('/topics/keywords'),
}

export const analyzerApi = {
  getIntelCard: (creatorId) => api.get(`/creators/${creatorId}/intel-card`),
  generateIntelCard: (creatorId) => api.post(`/creators/${creatorId}/intel-card`),
  analyzeVideo: (videoId) => api.post(`/videos/${videoId}/analyze`),
  getVideoAnalysis: (videoId) => api.get(`/videos/${videoId}/analysis`),
  batchAnalyzeCreatorVideos: (creatorId, limit = 20) =>
    api.post(`/creators/${creatorId}/videos/analyze?limit=${limit}`),
  batchAnalyzeCreatorVideosAsync: (creatorId, limit = 200) =>
    api.post(`/creators/${creatorId}/videos/analyze-async?limit=${limit}`),
  getAnalyzeTask: (taskId) => api.get(`/creators/analyze-task/${taskId}`),
  listAnalyses: () => api.get('/analyses'),
}

export const viewpointsApi = {
  list: (params = {}) => {
    const qs = new URLSearchParams()
    if (params.category) qs.append('category', params.category)
    if (params.active_only) qs.append('active_only', 'true')
    return api.get(`/viewpoints?${qs.toString()}`)
  },
  create: (data) => api.post('/viewpoints', data),
  update: (id, data) => api.put(`/viewpoints/${id}`, data),
  delete: (id) => api.delete(`/viewpoints/${id}`),
}

export const paymentApi = {
  createOrder: (data) => api.post('/payment/orders', data),
  checkOrder: (orderId) => api.get(`/payment/orders/${orderId}`),
  refreshMe: () => api.get('/auth/me'),
  devPay: (orderId) => api.post(`/payment/dev-pay/${orderId}`),
}

export const tenantApi = {
  getInfo: () => api.get('/tenant/info'),
  updateInfo: (data) => api.put('/tenant/info', data),
  listMembers: () => api.get('/tenant/members'),
  createMember: (data) => api.post('/tenant/members/create', data),
  updateRole: (userId, role) => api.put(`/tenant/members/${userId}/role`, { role }),
  removeMember: (userId) => api.delete(`/tenant/members/${userId}`),
  createInvite: () => api.post('/tenant/invite/create'),
  acceptInvite: (invite_token) => api.post('/tenant/invite/accept', null, { params: { invite_token } }),
}

export default api

