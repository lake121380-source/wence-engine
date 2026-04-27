// @ts-check
const { test, expect } = require('@playwright/test')

/**
 * 租户管理全链路 API 测试
 * 覆盖: tenant/info, tenant/members, tenant/invite, 角色变更, 成员移除
 */

const BASE = 'http://localhost:8080/api'
let adminToken = ''  // 租户 admin 用户
let memberToken = '' // 租户 member 用户
let adminUserId = 0
let memberUserId = 0
const adminEmail = `tenant_admin_${Date.now()}@test.com`
const memberEmail = `tenant_member_${Date.now()}@test.com`

const h = (tk) => ({ Authorization: `Bearer ${tk}`, 'Content-Type': 'application/json' })

test.describe.serial('租户管理全链路', () => {

  // ── 准备：注册 admin 用户 ──
  test('注册 admin 用户', async ({ request }) => {
    const res = await request.post(`${BASE}/auth/register`, {
      data: { email: adminEmail, password: 'Admin1234', nickname: '租户管理员' },
    })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    adminToken = body.token || body.access_token
    expect(adminToken).toBeTruthy()
    // 获取用户 ID
    const me = await request.get(`${BASE}/auth/me`, { headers: h(adminToken) })
    const meBody = await me.json()
    adminUserId = meBody.id
  })

  // ── 企业信息 ──
  test('GET /tenant/info - 获取企业信息', async ({ request }) => {
    const res = await request.get(`${BASE}/tenant/info`, { headers: h(adminToken) })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body).toHaveProperty('id')
    expect(body).toHaveProperty('name')
    expect(body).toHaveProperty('member_count')
    expect(body.member_count).toBeGreaterThanOrEqual(1)
  })

  test('PUT /tenant/info - 更新企业名称', async ({ request }) => {
    const res = await request.put(`${BASE}/tenant/info`, {
      headers: h(adminToken),
      data: { name: '测试企业-改名后' },
    })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.ok).toBe(true)
    expect(body.name).toBe('测试企业-改名后')
  })

  test('GET /tenant/info - 验证名称已更新', async ({ request }) => {
    const res = await request.get(`${BASE}/tenant/info`, { headers: h(adminToken) })
    const body = await res.json()
    expect(body.name).toBe('测试企业-改名后')
  })

  // ── 成员管理 ──
  test('GET /tenant/members - 初始只有自己', async ({ request }) => {
    const res = await request.get(`${BASE}/tenant/members`, { headers: h(adminToken) })
    expect(res.ok()).toBeTruthy()
    const members = await res.json()
    expect(Array.isArray(members)).toBeTruthy()
    expect(members.length).toBe(1)
    expect(members[0].role).toBe('admin')
  })

  test('POST /tenant/members/create - 创建成员', async ({ request }) => {
    const res = await request.post(`${BASE}/tenant/members/create`, {
      headers: h(adminToken),
      data: { email: memberEmail, password: 'Member1234', nickname: '普通成员', role: 'member' },
    })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.ok).toBe(true)
    memberUserId = body.user?.id
    expect(memberUserId).toBeTruthy()
  })

  test('POST /tenant/members/create - 重复邮箱返回 400', async ({ request }) => {
    const res = await request.post(`${BASE}/tenant/members/create`, {
      headers: h(adminToken),
      data: { email: memberEmail, password: 'Member1234', role: 'member' },
    })
    expect(res.status()).toBe(400)
  })

  test('POST /tenant/members/create - 邮箱格式不正确返回 400', async ({ request }) => {
    const res = await request.post(`${BASE}/tenant/members/create`, {
      headers: h(adminToken),
      data: { email: 'bad-email', password: 'Member1234', role: 'member' },
    })
    expect(res.status()).toBe(400)
  })

  test('POST /tenant/members/create - 密码太短返回 400', async ({ request }) => {
    const res = await request.post(`${BASE}/tenant/members/create`, {
      headers: h(adminToken),
      data: { email: `short_pw_${Date.now()}@test.com`, password: '123', role: 'member' },
    })
    expect(res.status()).toBe(400)
  })

  test('POST /tenant/members/create - 无效角色返回 400', async ({ request }) => {
    const res = await request.post(`${BASE}/tenant/members/create`, {
      headers: h(adminToken),
      data: { email: `role_${Date.now()}@test.com`, password: 'Pass1234', role: 'superadmin' },
    })
    expect(res.status()).toBe(400)
  })

  test('成员可以登录', async ({ request }) => {
    const res = await request.post(`${BASE}/auth/login`, {
      data: { email: memberEmail, password: 'Member1234' },
    })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    memberToken = body.token || body.access_token
    expect(memberToken).toBeTruthy()
  })

  test('GET /tenant/members - 现在有 2 个成员', async ({ request }) => {
    const res = await request.get(`${BASE}/tenant/members`, { headers: h(adminToken) })
    const members = await res.json()
    expect(members.length).toBe(2)
  })

  // ── 角色变更 ──
  test('PUT /tenant/members/:id/role - 提升成员为 admin', async ({ request }) => {
    const res = await request.put(`${BASE}/tenant/members/${memberUserId}/role`, {
      headers: h(adminToken),
      data: { role: 'admin' },
    })
    expect(res.ok()).toBeTruthy()
  })

  test('PUT /tenant/members/:id/role - 不能修改自己的角色', async ({ request }) => {
    const res = await request.put(`${BASE}/tenant/members/${adminUserId}/role`, {
      headers: h(adminToken),
      data: { role: 'member' },
    })
    expect(res.status()).toBe(400)
  })

  test('PUT /tenant/members/:id/role - 无效角色返回 400', async ({ request }) => {
    const res = await request.put(`${BASE}/tenant/members/${memberUserId}/role`, {
      headers: h(adminToken),
      data: { role: 'invalid' },
    })
    expect(res.status()).toBe(400)
  })

  test('PUT /tenant/members/:id/role - 改回 member', async ({ request }) => {
    const res = await request.put(`${BASE}/tenant/members/${memberUserId}/role`, {
      headers: h(adminToken),
      data: { role: 'member' },
    })
    expect(res.ok()).toBeTruthy()
  })

  // ── 权限控制：member 不能执行管理操作 ──
  test('member 不能创建成员', async ({ request }) => {
    const res = await request.post(`${BASE}/tenant/members/create`, {
      headers: h(memberToken),
      data: { email: `x_${Date.now()}@test.com`, password: 'Pass1234', role: 'member' },
    })
    expect(res.status()).toBe(403)
  })

  test('member 不能修改角色', async ({ request }) => {
    const res = await request.put(`${BASE}/tenant/members/${adminUserId}/role`, {
      headers: h(memberToken),
      data: { role: 'member' },
    })
    expect(res.status()).toBe(403)
  })

  test('member 不能更新企业信息', async ({ request }) => {
    const res = await request.put(`${BASE}/tenant/info`, {
      headers: h(memberToken),
      data: { name: '恶意改名' },
    })
    expect(res.status()).toBe(403)
  })

  // ── 邀请链接 ──
  test('POST /tenant/invite/create - 生成邀请链接', async ({ request }) => {
    const res = await request.post(`${BASE}/tenant/invite/create`, {
      headers: h(adminToken),
    })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.invite_token).toBeTruthy()
    expect(body.invite_token.length).toBeGreaterThan(10)
  })

  test('member 不能生成邀请链接', async ({ request }) => {
    const res = await request.post(`${BASE}/tenant/invite/create`, {
      headers: h(memberToken),
    })
    expect(res.status()).toBe(403)
  })

  test('POST /tenant/invite/accept - 无效 token 返回 404', async ({ request }) => {
    const res = await request.post(`${BASE}/tenant/invite/accept?invite_token=fake_token_xxx`, {
      headers: h(memberToken),
    })
    expect(res.status()).toBe(404)
  })

  // ── 移除成员 ──
  test('DELETE /tenant/members/:id - 不能移除自己', async ({ request }) => {
    const res = await request.delete(`${BASE}/tenant/members/${adminUserId}`, {
      headers: h(adminToken),
    })
    expect(res.status()).toBe(400)
  })

  test('member 不能移除别人', async ({ request }) => {
    const res = await request.delete(`${BASE}/tenant/members/${adminUserId}`, {
      headers: h(memberToken),
    })
    expect(res.status()).toBe(403)
  })

  test('DELETE /tenant/members/:id - admin 移除成员', async ({ request }) => {
    const res = await request.delete(`${BASE}/tenant/members/${memberUserId}`, {
      headers: h(adminToken),
    })
    expect(res.ok()).toBeTruthy()
  })

  test('GET /tenant/members - 移除后只剩 1 人', async ({ request }) => {
    const res = await request.get(`${BASE}/tenant/members`, { headers: h(adminToken) })
    const members = await res.json()
    expect(members.length).toBe(1)
  })
})
