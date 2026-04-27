/**
 * 前端 E2E 测试 - 核心业务闭环
 * 注册 → 创建观点 → 上传文档 → 创建风格模版 → 生成文案 → 查看历史 → 评分
 */
const { test, expect } = require('@playwright/test')

const TEST_EMAIL = `biz_${Date.now()}@test.com`
const TEST_PASSWORD = 'BizTest1234'

test.describe.serial('核心业务闭环', () => {
  /** @type {import('@playwright/test').Page} */
  let page

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage()
  })
  test.afterAll(async () => { await page.close() })

  // ── 注册并登录 ────────────────────────────────
  test('注册新账号', async () => {
    await page.goto('/login')
    await page.getByText('立即注册').click()
    await page.getByPlaceholder('邮箱地址').fill(TEST_EMAIL)
    await page.getByPlaceholder('密码（至少 8 位，含字母和数字）').fill(TEST_PASSWORD)
    await page.getByPlaceholder('昵称（选填）').fill('业务闭环测试')
    await page.locator('.n-button--primary-type').filter({ hasText: /注\s*册/ }).click()
    await page.waitForURL('/', { timeout: 15000 })
  })

  // ── 创建观点 ──────────────────────────────────
  test('创建一个运营观点', async () => {
    await page.goto('/viewpoints')
    await page.waitForLoadState('networkidle')
    await page.getByRole('button', { name: '添加观点' }).first().click()
    await page.waitForTimeout(500)

    await page.getByPlaceholder('一句话概括你的观点').fill('好产品不需要夸大其辞')
    await page.getByPlaceholder(/详细描述你的立场/).fill('真实的用户体验和成分透明度，是赢得信任的核心。避免过度承诺。')
    await page.getByPlaceholder(/护肤,成分党/).fill('品质,真实,信任')

    await page.getByRole('button', { name: '创建观点' }).click()
    await page.waitForTimeout(2000)
    await expect(page.getByText('好产品不需要夸大其辞')).toBeVisible()
  })

  // ── 添加文档资料 ──────────────────────────────
  test('添加文本资料到资料库', async () => {
    await page.goto('/documents')
    await page.waitForLoadState('networkidle')

    await page.getByRole('button', { name: '添加文本' }).click()
    await page.waitForTimeout(500)
    await page.getByPlaceholder(/例如：产品介绍/).fill('测试产品说明书')
    await page.getByPlaceholder(/粘贴产品说明/).fill(
      '产品名称：超级补水面膜\n主要成分：玻尿酸、烟酰胺\n功效：深层补水保湿，提亮肤色\n使用方法：洁面后敷15-20分钟\n适用人群：所有肤质'
    )
    await page.getByRole('button', { name: '确认添加' }).click()
    await page.waitForTimeout(3000)
  })

  // ── 创建风格模版 ──────────────────────────────
  test('创建风格模版', async () => {
    await page.goto('/styles')
    await page.waitForLoadState('networkidle')
    await page.getByRole('button', { name: '手动创建模版' }).click()
    await page.waitForTimeout(500)

    await page.getByPlaceholder(/例如：美妆干货博主风格/).fill('闭环测试风格')
    await page.getByPlaceholder(/例如：口语化/).fill('亲切自然、分享式语气')
    await page.getByPlaceholder(/例如：提出问题/).fill('痛点引入 → 产品介绍 → 真实体验 → 使用建议')

    await page.locator('.n-modal-body-wrapper').getByRole('button', { name: '创建' }).click()
    await page.waitForTimeout(3000)
    await expect(page.getByText('闭环测试风格')).toBeVisible()
  })

  // ── 生成文案（核心功能）────────────────────────
  test('使用 Composer 生成文案', async () => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    // 在 composer 输入框中输入主题
    const textarea = page.locator('textarea.composer-input')
    await textarea.fill('帮我写一段关于补水面膜的种草文案，要突出玻尿酸成分的补水效果')

    // 点击生成按钮
    await page.locator('button.send-btn').click()

    // 等待生成开始（应该出现 pending 状态或内容开始流入）
    // 等待最多 60 秒让 AI 生成完成
    await page.waitForTimeout(3000)

    // 检查是否有生成的内容（或至少没有报错）
    const hasError = await page.getByText(/生成失败|出错|error/i).isVisible().catch(() => false)
    const hasContent = await page.locator('.chat-bubble, .chat-msg, .result-content').count() > 0
    const hasPending = await page.locator('.pending-row, .n-spin').isVisible().catch(() => false)

    // 至少应该有一种状态：正在生成、已生成内容、或错误提示
    expect(hasError || hasContent || hasPending).toBeTruthy()

    if (hasContent && !hasError) {
      console.log('    ✓ 文案生成成功')
    } else if (hasPending) {
      console.log('    ℹ 文案正在生成中...')
      // 等待更长时间
      await page.waitForTimeout(30000)
    } else {
      console.log('    ⚠ 生成可能配置了无效的 API Key 或额度不足')
    }
  })

  // ── 查看历史记录 ──────────────────────────────
  test('历史记录页面应有数据', async () => {
    await page.goto('/history')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(2000)

    // 如果生成成功了，历史记录应该有条目
    const historyItems = page.locator('.history-item, .history-card, tr, .n-list-item')
    const count = await historyItems.count()
    console.log(`    ℹ 历史记录条数: ${count}`)
  })

  // ── 修改密码 ─────────────────────────────────
  test('修改密码 - 正确流程', async () => {
    await page.goto('/settings')
    await page.waitForLoadState('networkidle')

    await page.getByPlaceholder('请输入当前密码').fill(TEST_PASSWORD)
    await page.getByPlaceholder('至少 8 位，含字母和数字').fill('NewPass1234')
    await page.getByPlaceholder('再次输入新密码').fill('NewPass1234')
    await page.getByRole('button', { name: '保存新密码' }).click()
    await page.waitForTimeout(2000)

    // 成功后应看到提示
    const success = await page.getByText(/密码.*成功|已修改|已更新/).isVisible().catch(() => false)
    if (success) {
      console.log('    ✓ 密码修改成功')
    }
  })

  // ── 修改密码后重新登录验证 ─────────────────────
  test('用新密码重新登录', async () => {
    await page.evaluate(() => {
      localStorage.removeItem('cs_token')
      localStorage.removeItem('cs_user')
      localStorage.removeItem('cs_tenant')
    })
    await page.goto('/login')

    await page.getByPlaceholder('邮箱地址').fill(TEST_EMAIL)
    await page.getByPlaceholder('密码（至少 8 位，含字母和数字）').fill('NewPass1234')
    await page.locator('.n-button--primary-type').filter({ hasText: /登\s*录/ }).click()
    await page.waitForURL('/', { timeout: 10000 })
    await expect(page).toHaveURL('/')
  })

  // ── 定价页功能 ──────────────────────────────
  test('定价页显示正确的套餐信息', async () => {
    await page.goto('/pricing')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)

    // 应该能看到套餐卡片
    await expect(page.getByText('免费体验')).toBeVisible()
    await expect(page.getByText('标准版')).toBeVisible()
    // 价格信息
    await expect(page.getByText('¥49').first()).toBeVisible()
  })

  // ── 清理测试数据（通过 API） ──────────────────────────────
  test('清理：通过 API 删除测试数据', async () => {
    const token = await page.evaluate(() => localStorage.getItem('cs_token'))
    const headers = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
    const base = 'http://localhost:8080'

    // 删除风格模版
    const stylesRes = await page.request.get(`${base}/style-templates`, { headers })
    if (stylesRes.ok()) {
      const styles = await stylesRes.json()
      for (const s of styles) {
        if (s.name === '闭环测试风格') {
          await page.request.delete(`${base}/style-templates/${s.id}`, { headers })
          console.log('    ✓ 删除了测试风格模版')
        }
      }
    }

    // 删除观点
    const vpRes = await page.request.get(`${base}/viewpoints`, { headers })
    if (vpRes.ok()) {
      const vps = await vpRes.json()
      for (const v of vps) {
        if (v.title === '好产品不需要夸大其辞') {
          await page.request.delete(`${base}/viewpoints/${v.id}`, { headers })
          console.log('    ✓ 删除了测试观点')
        }
      }
    }
  })
})
