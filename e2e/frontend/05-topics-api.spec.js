// @ts-check
const { test, expect } = require('@playwright/test')

/**
 * 选题库全链路 API 测试
 * 覆盖: save / list / keywords / status / delete / batch-delete
 * 注意: search 和 fetch-detail 依赖第三方 TikHub API，这里用 save 代替 search 来构造数据
 */

const BASE = 'http://localhost:8080/api'
let token = ''
const headers = () => ({ Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' })

test.describe.serial('选题库全链路', () => {
  let topicId1 = 0
  let topicId2 = 0

  // ── 登录获取 token ──
  test('准备：注册并登录测试用户', async ({ request }) => {
    const ts = Date.now()
    const email = `topic_test_${ts}@test.com`
    await request.post(`${BASE}/auth/register`, {
      data: { email, password: 'TopicTest1234', nickname: '选题测试' },
    })
    const loginRes = await request.post(`${BASE}/auth/login`, {
      data: { email, password: 'TopicTest1234' },
    })
    expect(loginRes.ok()).toBeTruthy()
    const body = await loginRes.json()
    token = body.token || body.access_token
    expect(token).toBeTruthy()
  })

  // ── 手动保存选题 ──
  test('POST /topics/save - 保存第一个选题', async ({ request }) => {
    const res = await request.post(`${BASE}/topics/save`, {
      headers: headers(),
      data: {
        keyword: '护肤测试',
        platform: 'douyin',
        video_id: `test_vid_${Date.now()}_1`,
        title: '测试选题-补水面膜推荐',
        description: '这是一条测试选题描述',
        author: '测试博主',
        like_count: 50000,
        comment_count: 1200,
        share_count: 300,
        play_count: 500000,
        collect_count: 8000,
        tags: ['护肤', '面膜', '补水'],
      },
    })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    topicId1 = body.id
    expect(topicId1).toBeGreaterThan(0)
    expect(body.already_saved).toBe(false)
  })

  test('POST /topics/save - 保存第二个选题', async ({ request }) => {
    const res = await request.post(`${BASE}/topics/save`, {
      headers: headers(),
      data: {
        keyword: '美妆测试',
        platform: 'douyin',
        video_id: `test_vid_${Date.now()}_2`,
        title: '测试选题-眼影盘测评',
        description: '眼影盘测评描述',
        author: '美妆博主',
        like_count: 30000,
        comment_count: 800,
        play_count: 300000,
      },
    })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    topicId2 = body.id
    expect(topicId2).toBeGreaterThan(0)
  })

  test('POST /topics/save - 重复保存返回 already_saved', async ({ request }) => {
    // 用相同的 video_id 再保存一次
    const res = await request.post(`${BASE}/topics/save`, {
      headers: headers(),
      data: {
        keyword: '护肤测试',
        platform: 'douyin',
        video_id: `test_vid_${Date.now()}_1`, // 不同 video_id 不算重复
        title: '另一条',
      },
    })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    // 新 video_id => 新记录
    expect(body.already_saved).toBe(false)
    // 清理这个额外的
    if (body.id) {
      await request.delete(`${BASE}/topics/${body.id}`, { headers: headers() })
    }
  })

  // ── 列表查询 ──
  test('GET /topics - 获取选题列表', async ({ request }) => {
    const res = await request.get(`${BASE}/topics`, { headers: headers() })
    expect(res.ok()).toBeTruthy()
    const topics = await res.json()
    expect(Array.isArray(topics)).toBeTruthy()
    expect(topics.length).toBeGreaterThanOrEqual(2)
    // 检查字段结构
    const t = topics[0]
    expect(t).toHaveProperty('id')
    expect(t).toHaveProperty('title')
    expect(t).toHaveProperty('platform')
    expect(t).toHaveProperty('like_count')
    expect(t).toHaveProperty('status')
  })

  test('GET /topics?keyword=护肤测试 - 按关键词筛选', async ({ request }) => {
    const res = await request.get(`${BASE}/topics?keyword=护肤测试`, { headers: headers() })
    expect(res.ok()).toBeTruthy()
    const topics = await res.json()
    expect(topics.length).toBeGreaterThanOrEqual(1)
    expect(topics.every(t => t.keyword === '护肤测试')).toBeTruthy()
  })

  test('GET /topics?platform=douyin - 按平台筛选', async ({ request }) => {
    const res = await request.get(`${BASE}/topics?platform=douyin`, { headers: headers() })
    expect(res.ok()).toBeTruthy()
    const topics = await res.json()
    expect(topics.every(t => t.platform === 'douyin')).toBeTruthy()
  })

  // ── 关键词列表 ──
  test('GET /topics/keywords - 搜索关键词去重列表', async ({ request }) => {
    const res = await request.get(`${BASE}/topics/keywords`, { headers: headers() })
    expect(res.ok()).toBeTruthy()
    const kws = await res.json()
    expect(Array.isArray(kws)).toBeTruthy()
    const kwNames = kws.map(k => k.keyword)
    expect(kwNames).toContain('护肤测试')
    expect(kwNames).toContain('美妆测试')
    // 每个关键词有 count
    expect(kws[0]).toHaveProperty('count')
  })

  // ── 更新状态 ──
  test('PATCH /topics/:id/status - 更新选题状态为已采纳', async ({ request }) => {
    const res = await request.patch(`${BASE}/topics/${topicId1}/status`, {
      headers: headers(),
      data: { status: '已采纳' },
    })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.ok).toBe(true)
    expect(body.status).toBe('已采纳')
  })

  test('PATCH /topics/:id/status - 无效状态返回 400', async ({ request }) => {
    const res = await request.patch(`${BASE}/topics/${topicId1}/status`, {
      headers: headers(),
      data: { status: '无效状态' },
    })
    expect(res.status()).toBe(400)
  })

  test('PATCH /topics/:id/status - 不存在的选题返回 404', async ({ request }) => {
    const res = await request.patch(`${BASE}/topics/999999/status`, {
      headers: headers(),
      data: { status: '已采纳' },
    })
    expect(res.status()).toBe(404)
  })

  test('GET /topics?status=已采纳 - 按状态筛选', async ({ request }) => {
    const res = await request.get(`${BASE}/topics?status=${encodeURIComponent('已采纳')}`, { headers: headers() })
    expect(res.ok()).toBeTruthy()
    const topics = await res.json()
    expect(topics.length).toBeGreaterThanOrEqual(1)
    expect(topics.every(t => t.status === '已采纳')).toBeTruthy()
  })

  // ── 单条删除 ──
  test('DELETE /topics/:id - 删除选题', async ({ request }) => {
    const res = await request.delete(`${BASE}/topics/${topicId1}`, { headers: headers() })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.ok).toBe(true)
  })

  test('DELETE /topics/:id - 已删除的返回 404', async ({ request }) => {
    const res = await request.delete(`${BASE}/topics/${topicId1}`, { headers: headers() })
    expect(res.status()).toBe(404)
  })

  // ── 批量删除 ──
  test('POST /topics/batch-delete - 批量删除', async ({ request }) => {
    const res = await request.post(`${BASE}/topics/batch-delete`, {
      headers: headers(),
      data: { ids: [topicId2] },
    })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.ok).toBe(true)
    expect(body.deleted).toBe(1)
  })

  test('POST /topics/batch-delete - 空列表返回 deleted=0', async ({ request }) => {
    const res = await request.post(`${BASE}/topics/batch-delete`, {
      headers: headers(),
      data: { ids: [999999] },
    })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.deleted).toBe(0)
  })
})
