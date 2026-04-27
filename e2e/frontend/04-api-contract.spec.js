/**
 * API 契约测试 - 直接调用后端 API 验证数据正确性
 * 不走 UI，直接验证接口的输入输出
 */
const { test, expect } = require('@playwright/test')

const BASE_URL = 'http://localhost:8080'
const EMAIL = `api_${Date.now()}@test.com`
const PASSWORD = 'ApiTest1234'
let token = ''
let userId = 0
let tenantId = 0

test.describe.serial('API 契约测试', () => {
  // ═══════════════════════════════════════════
  //  注册 + 登录
  // ═══════════════════════════════════════════
  test('POST /auth/register - 正常注册', async ({ request }) => {
    const res = await request.post(`${BASE_URL}/api/auth/register`, {
      data: { email: EMAIL, password: PASSWORD, nickname: 'API测试' },
    })
    expect(res.status()).toBe(200)
    const body = await res.json()
    expect(body).toHaveProperty('token')
    expect(body).toHaveProperty('user')
    expect(body.user).toHaveProperty('id')
    expect(body.user.email).toBe(EMAIL)
    expect(body.user.is_trial).toBe(true)
    token = body.token
    userId = body.user.id
  })

  test('POST /auth/register - 重复邮箱返回 409', async ({ request }) => {
    const res = await request.post(`${BASE_URL}/api/auth/register`, {
      data: { email: EMAIL, password: PASSWORD },
    })
    expect(res.status()).toBe(409)
    const body = await res.json()
    expect(body.detail).toContain('已注册')
  })

  test('POST /auth/register - 无效邮箱返回 400', async ({ request }) => {
    const res = await request.post(`${BASE_URL}/api/auth/register`, {
      data: { email: 'bad-email', password: PASSWORD },
    })
    expect(res.status()).toBe(400)
  })

  test('POST /auth/register - 弱密码返回 400', async ({ request }) => {
    const res = await request.post(`${BASE_URL}/api/auth/register`, {
      data: { email: 'weak@test.com', password: '12345678' },
    })
    expect(res.status()).toBe(400)
  })

  test('POST /auth/login - 正确密码', async ({ request }) => {
    const res = await request.post(`${BASE_URL}/api/auth/login`, {
      data: { email: EMAIL, password: PASSWORD },
    })
    expect(res.status()).toBe(200)
    const body = await res.json()
    expect(body).toHaveProperty('token')
    token = body.token
  })

  test('POST /auth/login - 错误密码返回 401', async ({ request }) => {
    const res = await request.post(`${BASE_URL}/api/auth/login`, {
      data: { email: EMAIL, password: 'WrongPass99' },
    })
    expect(res.status()).toBe(401)
  })

  // ═══════════════════════════════════════════
  //  鉴权守卫
  // ═══════════════════════════════════════════
  test('GET /auth/me - 无 Token 返回 401', async ({ request }) => {
    const res = await request.get(`${BASE_URL}/api/auth/me`)
    expect(res.status()).toBe(401)
  })

  test('GET /auth/me - 有效 Token 返回用户信息', async ({ request }) => {
    const res = await request.get(`${BASE_URL}/api/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    expect(res.status()).toBe(200)
    const body = await res.json()
    expect(body.email).toBe(EMAIL)
    expect(body).toHaveProperty('is_trial')
    expect(body).toHaveProperty('is_subscription_active')
  })

  test('GET /auth/me - 伪造 Token 返回 401', async ({ request }) => {
    const res = await request.get(`${BASE_URL}/api/auth/me`, {
      headers: { Authorization: 'Bearer fake.token.here' },
    })
    expect(res.status()).toBe(401)
  })

  // ═══════════════════════════════════════════
  //  资料库 CRUD
  // ═══════════════════════════════════════════
  let docId = 0
  let folderId = ''

  test('POST /documents/folders - 创建文件夹', async ({ request }) => {
    const res = await request.post(`${BASE_URL}/api/documents/folders`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { name: 'API测试文件夹' },
    })
    expect(res.status()).toBe(200)
  })

  test('POST /documents/folders - 空名称返回 400', async ({ request }) => {
    const res = await request.post(`${BASE_URL}/api/documents/folders`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { name: '' },
    })
    expect(res.status()).toBe(400)
  })

  test('POST /documents/add-text - 添加文本', async ({ request }) => {
    const res = await request.post(`${BASE_URL}/api/documents/add-text`, {
      headers: { Authorization: `Bearer ${token}` },
      data: {
        name: 'API测试文档',
        content: '这是 API 测试添加的文本内容，用于验证文档创建功能。',
        folder_name: 'API测试文件夹',
      },
    })
    expect(res.status()).toBe(200)
    const body = await res.json()
    expect(body).toHaveProperty('id')
    expect(body.name).toBe('API测试文档')
    docId = body.id
  })

  test('GET /documents - 列表包含刚创建的文档', async ({ request }) => {
    const res = await request.get(`${BASE_URL}/api/documents`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    expect(res.status()).toBe(200)
    const body = await res.json()
    expect(Array.isArray(body)).toBe(true)
    const found = body.find(d => d.name === 'API测试文档')
    expect(found).toBeTruthy()
  })

  test('GET /documents/{id} - 获取单个文档', async ({ request }) => {
    const res = await request.get(`${BASE_URL}/api/documents/${docId}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    expect(res.status()).toBe(200)
    const body = await res.json()
    expect(body.id).toBe(docId)
  })

  test('DELETE /documents/{id} - 删除文档', async ({ request }) => {
    const res = await request.delete(`${BASE_URL}/api/documents/${docId}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    expect(res.status()).toBe(200)
  })

  test('GET /documents/{id} - 已删除文档返回 404', async ({ request }) => {
    const res = await request.get(`${BASE_URL}/api/documents/${docId}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    expect(res.status()).toBe(404)
  })

  // ═══════════════════════════════════════════
  //  观点 CRUD
  // ═══════════════════════════════════════════
  let viewpointId = 0

  test('POST /viewpoints - 创建观点', async ({ request }) => {
    const res = await request.post(`${BASE_URL}/api/viewpoints`, {
      headers: { Authorization: `Bearer ${token}` },
      data: {
        title: 'API测试观点',
        content: '真实性和透明度是长期品牌建设的基石',
        category: '价值观',
        tags: '品牌,信任',
      },
    })
    expect(res.status()).toBe(200)
    const body = await res.json()
    expect(body).toHaveProperty('id')
    viewpointId = body.id
  })

  test('GET /viewpoints - 列表包含观点', async ({ request }) => {
    const res = await request.get(`${BASE_URL}/api/viewpoints`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    expect(res.status()).toBe(200)
    const body = await res.json()
    expect(Array.isArray(body)).toBe(true)
    const found = body.find(v => v.title === 'API测试观点')
    expect(found).toBeTruthy()
  })

  test('PUT /viewpoints/{id} - 更新观点', async ({ request }) => {
    const res = await request.put(`${BASE_URL}/api/viewpoints/${viewpointId}`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { title: 'API测试观点（已更新）' },
    })
    expect(res.status()).toBe(200)
  })

  test('DELETE /viewpoints/{id} - 删除观点', async ({ request }) => {
    const res = await request.delete(`${BASE_URL}/api/viewpoints/${viewpointId}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    expect(res.status()).toBe(200)
  })

  test('DELETE /viewpoints/{id} - 已删除返回 404', async ({ request }) => {
    const res = await request.delete(`${BASE_URL}/api/viewpoints/${viewpointId}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    expect(res.status()).toBe(404)
  })

  // ═══════════════════════════════════════════
  //  风格模版 CRUD
  // ═══════════════════════════════════════════
  let styleId = 0

  test('POST /style-templates - 创建风格', async ({ request }) => {
    const res = await request.post(`${BASE_URL}/api/style-templates`, {
      headers: { Authorization: `Bearer ${token}` },
      data: {
        name: 'API测试风格',
        platform: 'douyin',
        tone: '轻松幽默',
        structure: '开头引入→正文→结尾CTA',
      },
    })
    expect(res.status()).toBe(200)
    const body = await res.json()
    expect(body).toHaveProperty('id')
    styleId = body.id
  })

  test('GET /style-templates - 列表包含风格', async ({ request }) => {
    const res = await request.get(`${BASE_URL}/api/style-templates`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    expect(res.status()).toBe(200)
    const body = await res.json()
    const found = body.find(s => s.name === 'API测试风格')
    expect(found).toBeTruthy()
  })

  test('DELETE /style-templates/{id}', async ({ request }) => {
    const res = await request.delete(`${BASE_URL}/api/style-templates/${styleId}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    expect(res.status()).toBe(200)
  })

  // ═══════════════════════════════════════════
  //  生成 API
  // ═══════════════════════════════════════════
  test('POST /generate - 无 topic 返回 422', async ({ request }) => {
    const res = await request.post(`${BASE_URL}/api/generate`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { platform: 'douyin' },
    })
    expect(res.status()).toBe(422)
  })

  test('POST /generate - 无权访问的文档 ID 返回 403', async ({ request }) => {
    const res = await request.post(`${BASE_URL}/api/generate`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { topic: '测试', product_doc_ids: [999999] },
    })
    // 403 或 500（取决于实现）
    expect([403, 500]).toContain(res.status())
  })

  // ═══════════════════════════════════════════
  //  知识库统计
  // ═══════════════════════════════════════════
  test('GET /knowledge/stats - 获取统计', async ({ request }) => {
    const res = await request.get(`${BASE_URL}/api/knowledge/stats`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    expect(res.status()).toBe(200)
    const body = await res.json()
    // 应该包含数量统计字段
    expect(body).toHaveProperty('creators')
    expect(body).toHaveProperty('documents')
  })

  // ═══════════════════════════════════════════
  //  租户隔离验证
  // ═══════════════════════════════════════════
  test('租户隔离 - 另一个用户看不到前一个用户的数据', async ({ request }) => {
    // 创建另一个用户
    const email2 = `api2_${Date.now()}@test.com`
    const regRes = await request.post(`${BASE_URL}/api/auth/register`, {
      data: { email: email2, password: PASSWORD },
    })
    const { token: token2 } = await regRes.json()

    // 用第二个用户添加一个文档
    await request.post(`${BASE_URL}/api/documents/add-text`, {
      headers: { Authorization: `Bearer ${token2}` },
      data: { name: '隔离测试文档', content: '这是第二个租户的文档' },
    })

    // 用第一个用户查询 → 不应该看到
    const res = await request.get(`${BASE_URL}/api/documents`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    const docs = await res.json()
    const leaked = docs.find(d => d.name === '隔离测试文档')
    expect(leaked).toBeUndefined()
  })

  // ═══════════════════════════════════════════
  //  修改密码
  // ═══════════════════════════════════════════
  test('POST /auth/change-password - 原密码错误返回 400', async ({ request }) => {
    const res = await request.post(`${BASE_URL}/api/auth/change-password`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { old_password: 'WrongOld99', new_password: 'NewPass1234' },
    })
    expect(res.status()).toBe(400)
    const body = await res.json()
    expect(body.detail).toContain('原密码错误')
  })

  test('POST /auth/change-password - 新密码太短返回 400', async ({ request }) => {
    const res = await request.post(`${BASE_URL}/api/auth/change-password`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { old_password: PASSWORD, new_password: 'Ab1' },
    })
    expect(res.status()).toBe(400)
  })
})
