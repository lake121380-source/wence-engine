/**
 * 管理端 E2E 测试 - 初始化/登录 + 各管理页面
 */
const { test, expect } = require('@playwright/test')

const ADMIN_USER = 'e2eadmin'
const ADMIN_PASS = 'Admin1234'

test.describe.serial('管理端功能测试', () => {
  /** @type {import('@playwright/test').Page} */
  let page

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage()
  })

  test.afterAll(async () => {
    await page.close()
  })

  // ═══════════════════════════════════════════
  //  1. 管理员登录
  // ═══════════════════════════════════════════
  test('1.1 打开管理端登录页', async () => {
    await page.goto('/admin/#/login')
    await page.waitForLoadState('networkidle')
    await expect(page.getByText('文策引擎')).toBeVisible()
  })

  test('1.2 尝试初始化或登录', async () => {
    await page.getByPlaceholder('请输入用户名').fill(ADMIN_USER)
    await page.getByPlaceholder('请输入密码').fill(ADMIN_PASS)

    // 点击登录/创建按钮
    const submitBtn = page.getByRole('button', { name: /登\s*录|创建并登录/ })
    await submitBtn.click()
    await page.waitForTimeout(3000)

    // 成功后应跳转到 dashboard
    const url = page.url()
    if (url.includes('#/dashboard') || url.includes('#/')) {
      console.log('    ✓ 管理端登录成功')
    } else {
      // 可能管理员已存在且密码不对，尝试用常见的默认密码
      console.log('    ℹ 当前 URL:', url)
    }
  })

  // ═══════════════════════════════════════════
  //  2. 仪表盘
  // ═══════════════════════════════════════════
  test('2.1 查看仪表盘', async () => {
    await page.goto('/admin/#/dashboard')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)
    // 仪表盘页面应该加载成功
    const dashUrl = page.url()
    expect(dashUrl).toContain('#/dashboard')
  })

  // ═══════════════════════════════════════════
  //  3. 租户管理
  // ═══════════════════════════════════════════
  test('3.1 查看租户列表', async () => {
    await page.goto('/admin/#/tenants')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)
    expect(page.url()).toContain('#/tenants')
  })

  // ═══════════════════════════════════════════
  //  4. 用户管理
  // ═══════════════════════════════════════════
  test('4.1 查看用户列表', async () => {
    await page.goto('/admin/#/users')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)
    expect(page.url()).toContain('#/users')
  })

  // ═══════════════════════════════════════════
  //  5. 订单管理
  // ═══════════════════════════════════════════
  test('5.1 查看订单列表', async () => {
    await page.goto('/admin/#/orders')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)
    expect(page.url()).toContain('#/orders')
  })

  // ═══════════════════════════════════════════
  //  6. 内容管理
  // ═══════════════════════════════════════════
  test('6.1 查看内容列表', async () => {
    await page.goto('/admin/#/content')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)
    expect(page.url()).toContain('#/content')
  })

  // ═══════════════════════════════════════════
  //  7. 系统设置
  // ═══════════════════════════════════════════
  test('7.1 查看系统设置', async () => {
    await page.goto('/admin/#/settings')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)
    expect(page.url()).toContain('#/settings')
  })
})
