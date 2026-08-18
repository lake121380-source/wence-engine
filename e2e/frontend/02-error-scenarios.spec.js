/**
 * 前端 E2E 测试 - 错误场景 + 边界条件 + 输入校验
 */
const { test, expect } = require('@playwright/test')

test.describe('错误场景和边界条件', () => {
  /** @type {import('@playwright/test').Page} */
  let page

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage()
  })
  test.afterAll(async () => { await page.close() })

  // ═══════════════════════════════════════════
  //  注册校验
  // ═══════════════════════════════════════════
  test('注册 - 邮箱格式不正确', async () => {
    await page.goto('/login')
    await page.getByText('立即注册').click()
    await page.getByPlaceholder('邮箱地址').fill('invalid-email')
    await page.getByPlaceholder('密码（至少 8 位，含字母和数字）').fill('Test1234')
    await page.locator('.n-button--primary-type').filter({ hasText: /注\s*册/ }).click()
    // 前端校验：message.warning('请输入有效邮箱')
    await expect(page.getByText('请输入有效邮箱')).toBeVisible({ timeout: 5000 })
  })

  test('注册 - 密码少于8位', async () => {
    await page.goto('/login')
    await page.getByText('立即注册').click()
    await page.getByPlaceholder('邮箱地址').fill('short@test.com')
    await page.getByPlaceholder('密码（至少 8 位，含字母和数字）').fill('Ab1')
    await page.locator('.n-button--primary-type').filter({ hasText: /注\s*册/ }).click()
    await expect(page.getByText('密码至少 8 位')).toBeVisible({ timeout: 5000 })
  })

  test('注册 - 纯数字密码', async () => {
    await page.goto('/login')
    await page.getByText('立即注册').click()
    await page.getByPlaceholder('邮箱地址').fill('purenum@test.com')
    await page.getByPlaceholder('密码（至少 8 位，含字母和数字）').fill('12345678')
    await page.locator('.n-button--primary-type').filter({ hasText: /注\s*册/ }).click()
    await expect(page.getByText('密码需要同时包含字母和数字')).toBeVisible({ timeout: 5000 })
  })

  test('注册 - 纯字母密码', async () => {
    await page.goto('/login')
    await page.getByText('立即注册').click()
    await page.getByPlaceholder('邮箱地址').fill('purealpha@test.com')
    await page.getByPlaceholder('密码（至少 8 位，含字母和数字）').fill('abcdefgh')
    await page.locator('.n-button--primary-type').filter({ hasText: /注\s*册/ }).click()
    await expect(page.getByText('密码需要同时包含字母和数字')).toBeVisible({ timeout: 5000 })
  })

  // ═══════════════════════════════════════════
  //  登录校验
  // ═══════════════════════════════════════════
  test('登录 - 不存在的账号', async () => {
    await page.goto('/login')
    await page.getByPlaceholder('邮箱地址').fill('nonexist@test.com')
    await page.getByPlaceholder('密码（至少 8 位，含字母和数字）').fill('Test1234')
    await page.locator('.n-button--primary-type').filter({ hasText: /登\s*录/ }).click()
    await expect(page.getByText('邮箱或密码错误')).toBeVisible({ timeout: 5000 })
  })

  test('登录 - 密码错误', async () => {
    // 先注册一个用户
    const email = `errlogin_${Date.now()}@test.com`
    await page.goto('/login')
    await page.getByText('立即注册').click()
    await page.getByPlaceholder('邮箱地址').fill(email)
    await page.getByPlaceholder('密码（至少 8 位，含字母和数字）').fill('Correct1234')
    await page.locator('.n-button--primary-type').filter({ hasText: /注\s*册/ }).click()
    await page.waitForURL('/', { timeout: 10000 })

    // 登出
    await page.evaluate(() => {
      localStorage.removeItem('cs_token')
      localStorage.removeItem('cs_user')
      localStorage.removeItem('cs_tenant')
    })
    await page.goto('/login')

    // 用错误密码登录
    await page.getByPlaceholder('邮箱地址').fill(email)
    await page.getByPlaceholder('密码（至少 8 位，含字母和数字）').fill('Wrong9999')
    await page.locator('.n-button--primary-type').filter({ hasText: /登\s*录/ }).click()
    await expect(page.getByText('邮箱或密码错误')).toBeVisible({ timeout: 5000 })
  })

  // ═══════════════════════════════════════════
  //  重复注册
  // ═══════════════════════════════════════════
  test('注册 - 邮箱已存在', async () => {
    const email = `dup_${Date.now()}@test.com`
    // 第一次注册
    await page.goto('/login')
    await page.getByText('立即注册').click()
    await page.getByPlaceholder('邮箱地址').fill(email)
    await page.getByPlaceholder('密码（至少 8 位，含字母和数字）').fill('Test1234')
    await page.locator('.n-button--primary-type').filter({ hasText: /注\s*册/ }).click()
    await page.waitForURL('/', { timeout: 10000 })

    // 登出
    await page.evaluate(() => {
      localStorage.removeItem('cs_token')
      localStorage.removeItem('cs_user')
      localStorage.removeItem('cs_tenant')
    })

    // 第二次用同样邮箱注册
    await page.goto('/login')
    await page.getByText('立即注册').click()
    await page.getByPlaceholder('邮箱地址').fill(email)
    await page.getByPlaceholder('密码（至少 8 位，含字母和数字）').fill('Test1234')
    await page.locator('.n-button--primary-type').filter({ hasText: /注\s*册/ }).click()
    await expect(page.getByText('该邮箱已注册')).toBeVisible({ timeout: 5000 })
  })

  // ═══════════════════════════════════════════
  //  未登录/Token过期 访问保护页面
  // ═══════════════════════════════════════════
  test('未登录访问受保护页面 → 跳转登录页', async () => {
    await page.evaluate(() => {
      localStorage.removeItem('cs_token')
      localStorage.removeItem('cs_user')
      localStorage.removeItem('cs_tenant')
    })

    const protectedRoutes = ['/', '/creators', '/documents', '/styles', '/topics', '/viewpoints', '/history', '/settings']
    for (const route of protectedRoutes) {
      await page.goto(route)
      await page.waitForURL('/login', { timeout: 5000 })
      expect(page.url()).toContain('/login')
    }
  })

  test('伪造的过期 Token → 跳转登录页', async () => {
    // 设置一个过期的伪 JWT
    const expiredToken = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIiwiZXhwIjoxMDAwMDAwMDAwfQ.fake'
    await page.evaluate((t) => {
      localStorage.setItem('cs_token', t)
      localStorage.setItem('cs_user', '{}')
      localStorage.setItem('cs_tenant', '{}')
    }, expiredToken)
    await page.goto('/')
    await page.waitForURL('/login', { timeout: 5000 })
  })
})
