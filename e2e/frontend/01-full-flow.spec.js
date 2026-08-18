/**
 * 前端 E2E 测试 - 注册 + 登录 + 各主要页面功能
 */
const { test, expect } = require('@playwright/test')

// 测试用账号
const TEST_EMAIL = `e2etest_${Date.now()}@test.com`
const TEST_PASSWORD = 'Test1234'
const TEST_NICKNAME = 'E2E测试用户'

test.describe.serial('前端功能测试', () => {
  /** @type {import('@playwright/test').Page} */
  let page

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage()
  })

  test.afterAll(async () => {
    await page.close()
  })

  // ═══════════════════════════════════════════
  //  1. 注册
  // ═══════════════════════════════════════════
  test('1.1 打开登录页', async () => {
    await page.goto('/login')
    await expect(page.getByText('欢迎回来')).toBeVisible()
  })

  test('1.2 切换到注册并注册新账号', async () => {
    await page.getByText('立即注册').click()
    await expect(page.getByText('创建账号')).toBeVisible()

    await page.getByPlaceholder('邮箱地址').fill(TEST_EMAIL)
    await page.getByPlaceholder('密码（至少 8 位，含字母和数字）').fill(TEST_PASSWORD)
    await page.getByPlaceholder('昵称（选填）').fill(TEST_NICKNAME)

    await page.locator('.n-button--primary-type').filter({ hasText: /注\s*册/ }).click()

    // 注册成功后应跳转到首页（生成页）
    await page.waitForURL('/', { timeout: 15000 })
    await expect(page).toHaveURL('/')
  })

  // ═══════════════════════════════════════════
  //  2. 登出再登录
  // ═══════════════════════════════════════════
  test('2.1 清除登录状态后跳转到登录页', async () => {
    // 手动清除 token 模拟登出
    await page.evaluate(() => {
      localStorage.removeItem('cs_token')
      localStorage.removeItem('cs_user')
      localStorage.removeItem('cs_tenant')
    })
    await page.goto('/')
    await page.waitForURL('/login', { timeout: 10000 })
  })

  test('2.2 使用邮箱密码登录', async () => {
    await page.getByPlaceholder('邮箱地址').fill(TEST_EMAIL)
    await page.getByPlaceholder('密码（至少 8 位，含字母和数字）').fill(TEST_PASSWORD)
    await page.locator('.n-button--primary-type').filter({ hasText: /登\s*录/ }).click()

    await page.waitForURL('/', { timeout: 15000 })
    await expect(page).toHaveURL('/')
  })

  // ═══════════════════════════════════════════
  //  3. 生成页（首页）
  // ═══════════════════════════════════════════
  test('3.1 生成页基本元素可见', async () => {
    await page.goto('/')
    // 检查 composer 输入框
    await expect(page.locator('textarea.composer-input')).toBeVisible()
    // 检查生成按钮
    await expect(page.locator('button.send-btn')).toBeVisible()
  })

  test('3.2 生成页 - 打开配置抽屉', async () => {
    const configBtn = page.getByRole('button', { name: '配置', exact: true })
    if (await configBtn.isVisible()) {
      await configBtn.click()
      // 等待抽屉出现（Naive UI drawer）
      await page.waitForTimeout(500)
      // 应该能看到平台选择
      const drawer = page.locator('.n-drawer')
      await expect(drawer).toBeVisible()
      // 关闭抽屉
      await page.locator('.n-drawer-mask').click()
      await page.waitForTimeout(300)
    }
  })

  test('3.3 生成页 - 检查预设模板', async () => {
    // 看看预设模板卡片是否存在
    const presetCards = page.locator('.preset-card')
    const count = await presetCards.count()
    console.log(`    ℹ 发现 ${count} 个预设模板`)
  })

  // ═══════════════════════════════════════════
  //  4. 博主管理
  // ═══════════════════════════════════════════
  test('4.1 导航到博主页', async () => {
    await page.goto('/creators')
    await page.waitForLoadState('networkidle')
    await expect(page.getByRole('button', { name: '手动添加博主' })).toBeVisible()
  })

  test('4.2 打开添加博主弹窗', async () => {
    await page.getByRole('button', { name: '手动添加博主' }).click()
    await page.waitForTimeout(500)
    await expect(page.getByText('添加博主').first()).toBeVisible()
    // 关闭弹窗
    await page.getByRole('button', { name: '取消' }).click()
    await page.waitForTimeout(300)
  })

  test('4.3 打开自动发现弹窗', async () => {
    const discoverBtn = page.getByRole('button', { name: '一键发现头部博主' })
    if (await discoverBtn.isVisible()) {
      await discoverBtn.click()
      await page.waitForTimeout(500)
      await expect(page.getByPlaceholder(/例如：护肤/)).toBeVisible()
      // 关闭弹窗 - 点击遮罩或取消
      await page.keyboard.press('Escape')
      await page.waitForTimeout(300)
    }
  })

  // ═══════════════════════════════════════════
  //  5. 资料库
  // ═══════════════════════════════════════════
  test('5.1 导航到资料库', async () => {
    await page.goto('/documents')
    await page.waitForLoadState('networkidle')
    await expect(page.getByRole('button', { name: '添加文本' })).toBeVisible()
  })

  test('5.2 新建文件夹', async () => {
    await page.getByRole('button', { name: '新建文件夹' }).click()
    await page.waitForTimeout(500)
    await page.getByPlaceholder(/文件夹名称/).fill('E2E测试文件夹')
    await page.locator('.n-modal-body-wrapper').getByRole('button', { name: '创建' }).click()
    await page.waitForTimeout(1000)
    // 应该能在侧栏看到新建的文件夹
    await expect(page.getByText('E2E测试文件夹', { exact: true })).toBeVisible()
  })

  test('5.3 添加文本资料', async () => {
    await page.getByRole('button', { name: '添加文本' }).click()
    await page.waitForTimeout(500)
    await page.getByPlaceholder(/例如：产品介绍/).fill('E2E测试文档')
    // 填写内容
    await page.getByPlaceholder(/粘贴产品说明/).fill('这是一份自动化测试创建的文档内容，用于验证文档功能是否正常。')
    await page.getByRole('button', { name: '确认添加' }).click()
    await page.waitForTimeout(2000)
  })

  // ═══════════════════════════════════════════
  //  6. 风格模版
  // ═══════════════════════════════════════════
  test('6.1 导航到风格模版', async () => {
    await page.goto('/styles')
    await page.waitForLoadState('networkidle')
    await expect(page.getByRole('button', { name: '手动创建模版' })).toBeVisible()
  })

  test('6.2 创建风格模版', async () => {
    await page.getByRole('button', { name: '手动创建模版' }).click()
    await page.waitForTimeout(500)
    await page.getByPlaceholder(/例如：美妆干货博主风格/).fill('E2E测试风格')
    await page.getByPlaceholder(/例如：口语化/).fill('轻松幽默、贴近生活')
    await page.getByPlaceholder(/例如：提出问题/).fill('开场钩子 → 问题分析 → 解决方案 → 产品推荐')
    await page.locator('.n-modal-body-wrapper').getByRole('button', { name: '创建' }).click()
    await page.waitForTimeout(2000)
    // 应该能看到新创建的模版
    await expect(page.getByText('E2E测试风格')).toBeVisible()
  })

  // ═══════════════════════════════════════════
  //  7. 爆款选题
  // ═══════════════════════════════════════════
  test('7.1 导航到爆款选题', async () => {
    await page.goto('/topics')
    await page.waitForLoadState('networkidle')
    await expect(page.getByPlaceholder(/输入行业关键词/)).toBeVisible()
    await expect(page.getByRole('button', { name: '搜索爆款' })).toBeVisible()
  })

  // ═══════════════════════════════════════════
  //  8. 观点库
  // ═══════════════════════════════════════════
  test('8.1 导航到观点库', async () => {
    await page.goto('/viewpoints')
    await page.waitForLoadState('networkidle')
    // 页面正常加载
    await expect(page).toHaveURL('/viewpoints')
  })

  // ═══════════════════════════════════════════
  //  9. 历史记录
  // ═══════════════════════════════════════════
  test('9.1 导航到历史记录', async () => {
    await page.goto('/history')
    await page.waitForLoadState('networkidle')
    await expect(page).toHaveURL('/history')
  })

  // ═══════════════════════════════════════════
  //  10. 定价页
  // ═══════════════════════════════════════════
  test('10.1 导航到定价页', async () => {
    await page.goto('/pricing')
    await page.waitForLoadState('networkidle')
    await expect(page).toHaveURL('/pricing')
  })

  // ═══════════════════════════════════════════
  //  11. 设置页
  // ═══════════════════════════════════════════
  test('11.1 导航到设置页', async () => {
    await page.goto('/settings')
    await page.waitForLoadState('networkidle')
    await expect(page.getByPlaceholder('请输入当前密码')).toBeVisible()
  })

  test('11.2 修改密码表单校验', async () => {
    // 测试不匹配的密码
    await page.getByPlaceholder('请输入当前密码').fill('wrongpass')
    await page.getByPlaceholder('至少 8 位，含字母和数字').fill('NewPass123')
    await page.getByPlaceholder('再次输入新密码').fill('NewPass456') // 不匹配
    await page.getByRole('button', { name: '保存新密码' }).click()
    await page.waitForTimeout(1000)
    // 应该有错误提示（两次密码不一致）
  })

  // ═══════════════════════════════════════════
  //  12. 清理：删除测试数据
  // ═══════════════════════════════════════════
  test('12.1 删除测试风格模版', async () => {
    await page.goto('/styles')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)
    const card = page.locator('.style-card', { hasText: 'E2E测试风格' })
    if (await card.count() > 0) {
      // 点击卡片内的删除按钮（会触发 n-popconfirm）
      await card.locator('button', { hasText: '删除' }).click()
      await page.waitForTimeout(500)
      // n-popconfirm 的确认按钮渲染在 teleport 中，直接在页面级查找
      // Naive UI popconfirm positive button 有 n-button--primary-type 类
      const popconfirm = page.locator('.n-popconfirm')
      await expect(popconfirm).toBeVisible({ timeout: 3000 })
      await popconfirm.locator('button').last().click()
      await page.waitForTimeout(1000)
    }
  })
})
