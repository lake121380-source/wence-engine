/**
 * 管理端 E2E 测试 - 完整功能验证
 * 登录 → 仪表盘数据 → 用户 CRUD → 租户管理 → 订阅管理 → 系统设置
 */
const { test, expect } = require('@playwright/test')

const ADMIN_USER = 'e2eadmin2'
const ADMIN_PASS = 'Admin1234'
const BASE_URL = 'http://localhost:8080'

test.describe.serial('管理端完整功能测试', () => {
  /** @type {import('@playwright/test').Page} */
  let page
  let adminToken = ''

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage()
  })
  test.afterAll(async () => { await page.close() })

  // ═══════════════════════════════════════════
  //  1. 管理员初始化/登录
  // ═══════════════════════════════════════════
  test('1.1 管理员初始化或登录', async ({ request }) => {
    // 尝试初始化
    const initRes = await request.post(`${BASE_URL}/api/admin/init`, {
      data: { username: ADMIN_USER, password: ADMIN_PASS },
    })
    if (initRes.status() === 200) {
      const body = await initRes.json()
      adminToken = body.token
      console.log('    ✓ 首次初始化管理员成功')
    } else {
      // 已存在，尝试登录
      const loginRes = await request.post(`${BASE_URL}/api/admin/login`, {
        data: { username: ADMIN_USER, password: ADMIN_PASS },
      })
      if (loginRes.status() === 200) {
        const body = await loginRes.json()
        adminToken = body.token
      } else {
        // 尝试用之前的 e2eadmin
        const loginRes2 = await request.post(`${BASE_URL}/api/admin/login`, {
          data: { username: 'e2eadmin', password: 'Admin1234' },
        })
        expect(loginRes2.status()).toBe(200)
        const body = await loginRes2.json()
        adminToken = body.token
      }
    }
    expect(adminToken).toBeTruthy()
  })

  test('1.2 在浏览器中登录管理端', async () => {
    // 直接注入 token 避免重复登录流程
    await page.goto('/admin/#/login')
    await page.evaluate((t) => {
      localStorage.setItem('admin_token', t)
      localStorage.setItem('admin_user', JSON.stringify({ username: 'admin' }))
    }, adminToken)
    await page.goto('/admin/#/dashboard')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)
  })

  // ═══════════════════════════════════════════
  //  2. 仪表盘验证
  // ═══════════════════════════════════════════
  test('2.1 仪表盘 API 返回正确结构', async ({ request }) => {
    const res = await request.get(`${BASE_URL}/api/admin/dashboard`, {
      headers: { Authorization: `Bearer ${adminToken}` },
    })
    expect(res.status()).toBe(200)
    const body = await res.json()
    expect(body).toHaveProperty('overview')
    expect(body.overview).toHaveProperty('total_users')
    expect(body.overview).toHaveProperty('total_tenants')
    expect(body.overview).toHaveProperty('total_revenue')
    expect(body).toHaveProperty('content')
    expect(body).toHaveProperty('register_trend')
    expect(body).toHaveProperty('revenue_trend')
    expect(body.overview.total_users).toBeGreaterThanOrEqual(0)
  })

  test('2.2 仪表盘页面显示统计卡片', async () => {
    await page.goto('/admin/#/dashboard')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1500)
    // 应该能看到统计数字（Naive UI statistic 或自定义卡片）
    // 页面不应有明显错误
    const hasError = await page.getByText(/错误|失败|error/i).isVisible().catch(() => false)
    expect(hasError).toBe(false)
  })

  // ═══════════════════════════════════════════
  //  3. 用户管理
  // ═══════════════════════════════════════════
  const testUserEmail = `admintest_${Date.now()}@test.com`
  let testUserId = 0

  test('3.1 通过 API 创建用户', async ({ request }) => {
    const res = await request.post(`${BASE_URL}/api/admin/users/create`, {
      headers: { Authorization: `Bearer ${adminToken}` },
      data: { email: testUserEmail, password: 'UserPass1234', nickname: '管理端创建的用户' },
    })
    expect(res.status()).toBe(200)
    const body = await res.json()
    testUserId = body.user_id || body.id || body.user?.id
    expect(testUserId).toBeTruthy()
  })

  test('3.2 用户列表页能搜索到新用户', async () => {
    await page.goto('/admin/#/users')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)

    // 搜索
    await page.getByPlaceholder(/搜索用户/).fill(testUserEmail.split('@')[0])
    await page.getByRole('button', { name: '搜索' }).click()
    await page.waitForTimeout(1500)

    // 应该能在表格中看到用户
    await expect(page.getByText(testUserEmail)).toBeVisible({ timeout: 5000 })
  })

  test('3.3 封禁用户', async ({ request }) => {
    const res = await request.patch(`${BASE_URL}/api/admin/users/${testUserId}/ban`, {
      headers: { Authorization: `Bearer ${adminToken}` },
    })
    expect(res.status()).toBe(200)
  })

  test('3.4 被封禁用户无法登录', async ({ request }) => {
    const res = await request.post(`${BASE_URL}/api/auth/login`, {
      data: { email: testUserEmail, password: 'UserPass1234' },
    })
    expect(res.status()).toBe(403)
    const body = await res.json()
    expect(body.detail).toContain('停用')
  })

  test('3.5 解封用户', async ({ request }) => {
    const res = await request.patch(`${BASE_URL}/api/admin/users/${testUserId}/unban`, {
      headers: { Authorization: `Bearer ${adminToken}` },
    })
    expect(res.status()).toBe(200)
  })

  test('3.6 解封后用户可以登录', async ({ request }) => {
    const res = await request.post(`${BASE_URL}/api/auth/login`, {
      data: { email: testUserEmail, password: 'UserPass1234' },
    })
    expect(res.status()).toBe(200)
  })

  test('3.7 延长用户订阅', async ({ request }) => {
    const res = await request.post(`${BASE_URL}/api/admin/users/${testUserId}/subscription/extend`, {
      headers: { Authorization: `Bearer ${adminToken}` },
      data: { days: 30, plan: 'monthly' },
    })
    expect(res.status()).toBe(200)
  })

  test('3.8 撤销用户订阅', async ({ request }) => {
    const res = await request.post(`${BASE_URL}/api/admin/users/${testUserId}/subscription/revoke`, {
      headers: { Authorization: `Bearer ${adminToken}` },
    })
    expect(res.status()).toBe(200)
  })

  test('3.9 重置用户密码', async ({ request }) => {
    const res = await request.post(`${BASE_URL}/api/admin/users/${testUserId}/reset-password`, {
      headers: { Authorization: `Bearer ${adminToken}` },
      data: { password: 'NewReset1234' },
    })
    expect(res.status()).toBe(200)

    // 验证新密码可以登录
    const loginRes = await request.post(`${BASE_URL}/api/auth/login`, {
      data: { email: testUserEmail, password: 'NewReset1234' },
    })
    expect(loginRes.status()).toBe(200)
  })

  test('3.10 重置密码 - 太短返回 400', async ({ request }) => {
    const res = await request.post(`${BASE_URL}/api/admin/users/${testUserId}/reset-password`, {
      headers: { Authorization: `Bearer ${adminToken}` },
      data: { password: 'Ab1' },
    })
    expect(res.status()).toBe(400)
  })

  // ═══════════════════════════════════════════
  //  4. 租户管理
  // ═══════════════════════════════════════════
  test('4.1 租户列表 API', async ({ request }) => {
    const res = await request.get(`${BASE_URL}/api/admin/tenants`, {
      headers: { Authorization: `Bearer ${adminToken}` },
    })
    expect(res.status()).toBe(200)
    const body = await res.json()
    expect(body).toHaveProperty('items')
    expect(body).toHaveProperty('total')
    expect(body.total).toBeGreaterThanOrEqual(1)
  })

  test('4.2 租户列表页面正常显示', async () => {
    await page.goto('/admin/#/tenants')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1500)
    // 表格应该有内容
    const rows = page.locator('.n-data-table-tr, tr').filter({ hasNot: page.locator('th') })
    const count = await rows.count()
    expect(count).toBeGreaterThanOrEqual(1)
  })

  test('4.3 租户详情页', async () => {
    // 点击第一个租户的详情
    const detailBtn = page.getByRole('button', { name: '详情' }).first()
    if (await detailBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await detailBtn.click()
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(1000)
      // 应该跳转到详情页
      expect(page.url()).toContain('#/tenants/')
    }
  })

  // ═══════════════════════════════════════════
  //  5. 内容审核（只读）
  // ═══════════════════════════════════════════
  test('5.1 内容管理页面加载', async () => {
    await page.goto('/admin/#/content')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)
    expect(page.url()).toContain('#/content')
  })

  // ═══════════════════════════════════════════
  //  6. 订单管理
  // ═══════════════════════════════════════════
  test('6.1 订单列表页面', async () => {
    await page.goto('/admin/#/orders')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)
    expect(page.url()).toContain('#/orders')
  })

  // ═══════════════════════════════════════════
  //  7. 系统设置
  // ═══════════════════════════════════════════
  test('7.1 系统设置页面加载', async () => {
    await page.goto('/admin/#/settings')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)
    // 应能看到密码修改表单和管理员列表
    await expect(page.getByPlaceholder('当前密码')).toBeVisible()
  })

  test('7.2 管理员改密 - 原密码错误', async ({ request }) => {
    const res = await request.post(`${BASE_URL}/api/admin/change-password`, {
      headers: { Authorization: `Bearer ${adminToken}` },
      data: { old_password: 'WrongPass', new_password: 'NewAdmin1234' },
    })
    expect(res.status()).toBe(400)
  })

  // ═══════════════════════════════════════════
  //  8. 数据导出
  // ═══════════════════════════════════════════
  test('8.1 导出用户 CSV', async ({ request }) => {
    const res = await request.get(`${BASE_URL}/api/admin/export/users`, {
      headers: { Authorization: `Bearer ${adminToken}` },
    })
    expect(res.status()).toBe(200)
    const contentType = res.headers()['content-type']
    expect(contentType).toContain('text/csv')
  })

  test('8.2 导出订单 CSV', async ({ request }) => {
    const res = await request.get(`${BASE_URL}/api/admin/export/orders`, {
      headers: { Authorization: `Bearer ${adminToken}` },
    })
    expect(res.status()).toBe(200)
  })

  // ═══════════════════════════════════════════
  //  9. 管理员权限校验
  // ═══════════════════════════════════════════
  test('9.1 普通用户 token 不能访问管理端 API', async ({ request }) => {
    // 用普通用户 token 调管理端接口
    const regRes = await request.post(`${BASE_URL}/api/auth/register`, {
      data: { email: `nonadmin_${Date.now()}@test.com`, password: 'Test1234' },
    })
    const { token: userToken } = await regRes.json()

    const res = await request.get(`${BASE_URL}/api/admin/dashboard`, {
      headers: { Authorization: `Bearer ${userToken}` },
    })
    expect(res.status()).toBe(401)
  })

  test('9.2 无 token 访问管理端 API 返回 401', async ({ request }) => {
    const res = await request.get(`${BASE_URL}/api/admin/dashboard`)
    expect(res.status()).toBe(401)
  })

  // ═══════════════════════════════════════════
  //  10. 管理员不能删除自己
  // ═══════════════════════════════════════════
  test('10.1 获取当前管理员 ID', async ({ request }) => {
    const res = await request.get(`${BASE_URL}/api/admin/me`, {
      headers: { Authorization: `Bearer ${adminToken}` },
    })
    expect(res.status()).toBe(200)
    const body = await res.json()
    const myId = body.id

    // 尝试删除自己
    const delRes = await request.delete(`${BASE_URL}/api/admin/admins/${myId}`, {
      headers: { Authorization: `Bearer ${adminToken}` },
    })
    expect(delRes.status()).toBe(400)
  })
})
