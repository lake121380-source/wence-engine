// @ts-check
const { test, expect } = require('@playwright/test')

/**
 * 管理端补充 API 测试
 * 覆盖: 管理员 CRUD, 租户编辑/删除, 内容审核列表, 创作者/选题/生成内容查看
 */

const BASE = 'http://localhost:8080'
let adminToken = ''

const h = () => ({ Authorization: `Bearer ${adminToken}`, 'Content-Type': 'application/json' })

test.describe.serial('管理端补充功能', () => {

  // ── 登录 ──
  test('管理端登录', async ({ request }) => {
    // 尝试 init
    let res = await request.post(`${BASE}/api/admin/init`, {
      data: { username: 'admin', password: 'admin123' },
    })
    // init 或 login
    res = await request.post(`${BASE}/api/admin/login`, {
      data: { username: 'admin', password: 'admin123' },
    })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    adminToken = body.token || body.access_token
    expect(adminToken).toBeTruthy()
  })

  // ═══════════════════════════════════════
  //  管理员 CRUD
  // ═══════════════════════════════════════

  let newAdminId = 0
  const newAdminUser = `testadmin_${Date.now()}`

  test('POST /admin/admins/create - 创建新管理员', async ({ request }) => {
    const res = await request.post(`${BASE}/api/admin/admins/create`, {
      headers: h(),
      data: { username: newAdminUser, password: 'Admin1234', nickname: '测试管理员' },
    })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.ok).toBe(true)
  })

  test('POST /admin/admins/create - 重复用户名返回 400', async ({ request }) => {
    const res = await request.post(`${BASE}/api/admin/admins/create`, {
      headers: h(),
      data: { username: newAdminUser, password: 'Admin1234' },
    })
    expect(res.status()).toBe(400)
  })

  test('POST /admin/admins/create - 密码太短返回 400', async ({ request }) => {
    const res = await request.post(`${BASE}/api/admin/admins/create`, {
      headers: h(),
      data: { username: `short_${Date.now()}`, password: '123' },
    })
    expect(res.status()).toBe(400)
  })

  test('GET /admin/admins - 管理员列表', async ({ request }) => {
    const res = await request.get(`${BASE}/api/admin/admins`, { headers: h() })
    expect(res.ok()).toBeTruthy()
    const admins = await res.json()
    expect(Array.isArray(admins)).toBeTruthy()
    expect(admins.length).toBeGreaterThanOrEqual(2)
    // 找到新建的管理员
    const newOne = admins.find(a => a.username === newAdminUser)
    expect(newOne).toBeTruthy()
    newAdminId = newOne.id
    expect(newOne).toHaveProperty('is_active')
    expect(newOne).toHaveProperty('nickname')
  })

  test('DELETE /admin/admins/:id - 不能删除自己', async ({ request }) => {
    // 获取当前管理员 ID
    const meRes = await request.get(`${BASE}/api/admin/me`, { headers: h() })
    const me = await meRes.json()
    const res = await request.delete(`${BASE}/api/admin/admins/${me.id}`, { headers: h() })
    expect(res.status()).toBe(400)
  })

  test('DELETE /admin/admins/:id - 删除其他管理员', async ({ request }) => {
    const res = await request.delete(`${BASE}/api/admin/admins/${newAdminId}`, { headers: h() })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.ok).toBe(true)
  })

  test('DELETE /admin/admins/:id - 不存在的返回 404', async ({ request }) => {
    const res = await request.delete(`${BASE}/api/admin/admins/999999`, { headers: h() })
    expect(res.status()).toBe(404)
  })

  // ═══════════════════════════════════════
  //  租户编辑/删除
  // ═══════════════════════════════════════

  // 先创建一个专门用于删除测试的租户（通过创建用户实现）
  let testTenantId = 0
  let testTenantUserId = 0
  const deletableEmail = `deletable_${Date.now()}@test.com`

  test('创建可删除的测试租户', async ({ request }) => {
    const res = await request.post(`${BASE}/api/admin/users/create`, {
      headers: h(),
      data: { email: deletableEmail, password: 'Delete1234', nickname: '可删除用户' },
    })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    testTenantUserId = body.user_id

    // 获取该用户的 tenant_id
    const usersRes = await request.get(`${BASE}/api/admin/users?keyword=${encodeURIComponent(deletableEmail)}`, { headers: h() })
    const usersBody = await usersRes.json()
    const users = usersBody.items || usersBody
    const user = Array.isArray(users) ? users.find(u => u.email === deletableEmail) : null
    if (user) {
      testTenantId = user.tenant_id
    }
  })

  test('PATCH /admin/tenants/:id - 编辑租户名称', async ({ request }) => {
    if (!testTenantId) return
    const res = await request.patch(`${BASE}/api/admin/tenants/${testTenantId}`, {
      headers: h(),
      data: { name: '编辑后的租户名' },
    })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.ok).toBe(true)
  })

  test('PATCH /admin/tenants/:id - 不存在的租户返回 404', async ({ request }) => {
    const res = await request.patch(`${BASE}/api/admin/tenants/999999`, {
      headers: h(),
      data: { name: '不存在' },
    })
    expect(res.status()).toBe(404)
  })

  test('DELETE /admin/tenants/:id - 删除租户及级联数据', async ({ request }) => {
    if (!testTenantId) return
    const res = await request.delete(`${BASE}/api/admin/tenants/${testTenantId}`, { headers: h() })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.ok).toBe(true)
  })

  test('删除后用户无法登录', async ({ request }) => {
    const res = await request.post(`${BASE}/api/auth/login`, {
      data: { email: deletableEmail, password: 'Delete1234' },
    })
    // 用户已被级联删除，应该返回 401
    expect(res.status()).toBe(401)
  })

  test('DELETE /admin/tenants/:id - 不存在的返回 404', async ({ request }) => {
    const res = await request.delete(`${BASE}/api/admin/tenants/999999`, { headers: h() })
    expect(res.status()).toBe(404)
  })

  // ═══════════════════════════════════════
  //  内容审核列表
  // ═══════════════════════════════════════

  test('GET /admin/creators - 创作者列表', async ({ request }) => {
    const res = await request.get(`${BASE}/api/admin/creators`, { headers: h() })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body).toHaveProperty('items')
    expect(body).toHaveProperty('total')
    expect(body).toHaveProperty('page')
    expect(Array.isArray(body.items)).toBeTruthy()
  })

  test('GET /admin/creators?keyword=xxx - 支持关键词搜索', async ({ request }) => {
    const res = await request.get(`${BASE}/api/admin/creators?keyword=nonexistent_xyz`, { headers: h() })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.total).toBe(0)
  })

  test('GET /admin/topics - 选题列表', async ({ request }) => {
    const res = await request.get(`${BASE}/api/admin/topics`, { headers: h() })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body).toHaveProperty('items')
    expect(body).toHaveProperty('total')
  })

  test('GET /admin/generations - 生成内容列表', async ({ request }) => {
    const res = await request.get(`${BASE}/api/admin/generations`, { headers: h() })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body).toHaveProperty('items')
    expect(body).toHaveProperty('total')
  })

  test('GET /admin/generations?keyword=xxx - 支持关键词搜索', async ({ request }) => {
    const res = await request.get(`${BASE}/api/admin/generations?keyword=nonexistent_xyz`, { headers: h() })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.total).toBe(0)
  })

  // ═══════════════════════════════════════
  //  管理员改密成功路径
  // ═══════════════════════════════════════

  test('POST /admin/change-password - 成功修改', async ({ request }) => {
    const res = await request.post(`${BASE}/api/admin/change-password`, {
      headers: h(),
      data: { old_password: 'admin123', new_password: 'admin456' },
    })
    expect(res.ok()).toBeTruthy()
    // 改回来
    const res2 = await request.post(`${BASE}/api/admin/change-password`, {
      headers: h(),
      data: { old_password: 'admin456', new_password: 'admin123' },
    })
    expect(res2.ok()).toBeTruthy()
  })
})
