// @ts-check
const { test, expect } = require('@playwright/test')

/**
 * 补充 API 测试：文档遗漏接口 + 生成评分 + Token 刷新 + 图片代理 + 单设备登录
 */

const BASE = 'http://localhost:8080/api'
let token = ''
let userId = 0
const testEmail = `misc_test_${Date.now()}@test.com`
const headers = () => ({ Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' })

test.describe.serial('补充接口测试', () => {

  test('准备：注册并登录', async ({ request }) => {
    const reg = await request.post(`${BASE}/auth/register`, {
      data: { email: testEmail, password: 'MiscTest1234', nickname: '补充测试' },
    })
    expect(reg.ok()).toBeTruthy()
    const body = await reg.json()
    token = body.token || body.access_token
    const me = await request.get(`${BASE}/auth/me`, { headers: headers() })
    userId = (await me.json()).id
  })

  // ═══════════════════════════════════════
  //  文档补充接口
  // ═══════════════════════════════════════

  test('GET /documents/folders - 获取文件夹列表', async ({ request }) => {
    const res = await request.get(`${BASE}/documents/folders`, { headers: headers() })
    expect(res.ok()).toBeTruthy()
    const folders = await res.json()
    expect(Array.isArray(folders)).toBeTruthy()
  })

  let testFolderName = '自动化测试文件夹'
  test('POST /documents/folders - 创建文件夹', async ({ request }) => {
    const res = await request.post(`${BASE}/documents/folders`, {
      headers: headers(),
      data: { name: testFolderName },
    })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.name).toBe(testFolderName)
  })

  test('GET /documents/folders - 列表包含新文件夹', async ({ request }) => {
    const res = await request.get(`${BASE}/documents/folders`, { headers: headers() })
    const folders = await res.json()
    expect(folders).toContain(testFolderName)
  })

  let docId = 0
  test('POST /documents/add-text - 添加文本到文件夹', async ({ request }) => {
    const res = await request.post(`${BASE}/documents/add-text`, {
      headers: headers(),
      data: {
        name: '文件夹内文档',
        content: '这个文档放在测试文件夹中',
        folder_name: testFolderName,
        tags: ['测试'],
      },
    })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    docId = body.id
    expect(docId).toBeGreaterThan(0)
  })

  test('PATCH /documents/:id/folder - 移动文档到其他文件夹', async ({ request }) => {
    const res = await request.patch(`${BASE}/documents/${docId}/folder`, {
      headers: headers(),
      data: { folder_name: '新位置' },
    })
    expect(res.ok()).toBeTruthy()
  })

  test('GET /documents/:id - 验证文件夹已变更', async ({ request }) => {
    const res = await request.get(`${BASE}/documents/${docId}`, { headers: headers() })
    const body = await res.json()
    expect(body.folder_name).toBe('新位置')
  })

  test('PATCH /documents/:id/folder - 移到根目录 (null)', async ({ request }) => {
    const res = await request.patch(`${BASE}/documents/${docId}/folder`, {
      headers: headers(),
      data: { folder_name: null },
    })
    expect(res.ok()).toBeTruthy()
  })

  test('DELETE /documents/folders/:name - 删除文件夹', async ({ request }) => {
    const res = await request.delete(`${BASE}/documents/folders/${encodeURIComponent(testFolderName)}`, {
      headers: headers(),
    })
    expect(res.ok()).toBeTruthy()
  })

  test('POST /documents/upload - 不支持的格式返回 400', async ({ request }) => {
    // 构造一个假的 .exe 文件上传
    const res = await request.post(`${BASE}/documents/upload`, {
      headers: { Authorization: `Bearer ${token}` },
      multipart: {
        file: { name: 'malware.exe', mimeType: 'application/octet-stream', buffer: Buffer.from('fake content') },
      },
    })
    expect(res.status()).toBe(400)
    const body = await res.json()
    expect(body.detail).toContain('仅支持')
  })

  test('POST /documents/upload - 上传 TXT 文件成功', async ({ request }) => {
    const res = await request.post(`${BASE}/documents/upload`, {
      headers: { Authorization: `Bearer ${token}` },
      multipart: {
        file: { name: 'test-doc.txt', mimeType: 'text/plain', buffer: Buffer.from('这是自动化测试上传的文本文件内容\n包含多行\n用于验证上传功能') },
        tags: '上传测试,自动化',
        folder_name: '',
      },
    })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.id).toBeGreaterThan(0)
    expect(body.name).toBe('test-doc.txt')
    // 清理
    await request.delete(`${BASE}/documents/${body.id}`, { headers: headers() })
  })

  // 清理测试文档
  test('清理文档', async ({ request }) => {
    if (docId) {
      await request.delete(`${BASE}/documents/${docId}`, { headers: headers() })
    }
  })

  // ═══════════════════════════════════════
  //  Token 刷新
  // ═══════════════════════════════════════

  test('POST /auth/refresh - 刷新 Token', async ({ request }) => {
    const res = await request.post(`${BASE}/auth/refresh`, { headers: headers() })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.token).toBeTruthy()
    // 新 token 应该也能使用
    const newToken = body.token
    const me = await request.get(`${BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${newToken}` },
    })
    expect(me.ok()).toBeTruthy()
    token = newToken // 更新为新 token
  })

  test('POST /auth/refresh - 无效 token 返回 401', async ({ request }) => {
    const res = await request.post(`${BASE}/auth/refresh`, {
      headers: { Authorization: 'Bearer fake_invalid_token' },
    })
    expect(res.status()).toBe(401)
  })

  // ═══════════════════════════════════════
  //  单设备登录验证
  // ═══════════════════════════════════════

  test('单设备登录 - 新登录后旧 token 失效', async ({ request }) => {
    const oldToken = token
    // 重新登录获取新 token
    const loginRes = await request.post(`${BASE}/auth/login`, {
      data: { email: testEmail, password: 'MiscTest1234' },
    })
    expect(loginRes.ok()).toBeTruthy()
    const body = await loginRes.json()
    const newToken = body.token || body.access_token
    expect(newToken).toBeTruthy()

    // 新 token 应该能用
    const newMe = await request.get(`${BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${newToken}` },
    })
    expect(newMe.ok()).toBeTruthy()

    // 旧 token 应该失效（session_version 递增了）
    const oldMe = await request.get(`${BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${oldToken}` },
    })
    expect(oldMe.status()).toBe(401)

    token = newToken
  })

  // ═══════════════════════════════════════
  //  图片代理
  // ═══════════════════════════════════════

  test('GET /image-proxy - 非白名单域名返回 403', async ({ request }) => {
    const res = await request.get(`${BASE}/image-proxy?url=${encodeURIComponent('https://evil.com/hack.jpg')}`)
    expect(res.status()).toBe(403)
    const body = await res.json()
    expect(body.detail).toContain('白名单')
  })

  test('GET /image-proxy - 白名单域名但不存在的图片返回 502', async ({ request }) => {
    const res = await request.get(`${BASE}/image-proxy?url=${encodeURIComponent('https://p3-sign.douyinpic.com/nonexistent.jpg')}`)
    // 可能是 502（上游非200）或 504（超时）
    expect([502, 504]).toContain(res.status())
  })

  // ═══════════════════════════════════════
  //  生成评分
  // ═══════════════════════════════════════

  test('PATCH /generations/:id/rate - 不存在的记录返回 404', async ({ request }) => {
    const res = await request.patch(`${BASE}/generations/999999/rate?rating=5`, {
      headers: headers(),
    })
    expect(res.status()).toBe(404)
  })
})
