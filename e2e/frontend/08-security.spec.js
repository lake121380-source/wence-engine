/**
 * 安全修复回归验证
 * pass = 漏洞已修复；fail = 漏洞仍存在，需处理
 */
const { test, expect } = require('@playwright/test')
const crypto = require('crypto')

const BASE_URL = 'http://localhost:8080'

function decodeJwtPayload(token) {
  const payloadPart = token.split('.')[1] || ''
  const normalized = payloadPart.replace(/-/g, '+').replace(/_/g, '/')
  const padded = normalized + '='.repeat((4 - (normalized.length % 4)) % 4)
  const json = Buffer.from(padded, 'base64').toString('utf8')
  return JSON.parse(json)
}

function base64url(input) {
  return Buffer.from(input).toString('base64').replace(/=/g,'').replace(/\+/g,'-').replace(/\//g,'_')
}

function signHs256(payload, secret) {
  const header = { alg: 'HS256', typ: 'JWT' }
  const enc = base64url(JSON.stringify(header)) + '.' + base64url(JSON.stringify(payload))
  const sig = crypto.createHmac('sha256', secret).update(enc).digest('base64')
    .replace(/=/g,'').replace(/\+/g,'-').replace(/\//g,'_')
  return `${enc}.${sig}`
}

test.describe.serial('安全修复回归验证', () => {
  let userToken = ''
  let userId = 0
  let sessionVersion = 1

  test('准备账号：注册普通用户', async ({ request }) => {
    const res = await request.post(`${BASE_URL}/api/auth/register`, {
      data: { email: `sec_fix_${Date.now()}@test.com`, password: 'SecFix1234', nickname: '修复验证用户' },
    })
    expect(res.status()).toBe(200)
    const body = await res.json()
    userToken = body.token
    const payload = decodeJwtPayload(userToken)
    userId = Number(payload.sub || 0)
    sessionVersion = Number(payload.sv || 1)
    expect(userId).toBeGreaterThan(0)
  })

  test('? 修复：管理员登录有限流（第6次应返回 429）', async ({ request }) => {
    const randomUser = `nonexist_${Date.now()}`
    const statuses = []
    for (let i = 0; i < 7; i++) {
      const res = await request.post(`${BASE_URL}/api/admin/login`, {
        data: { username: randomUser, password: 'WrongPass123!' },
      })
      statuses.push(res.status())
    }
    expect(statuses.some(s => s === 429)).toBeTruthy()
  })

  test('? 修复：/admin/init 无 X-Init-Token 时拒绝（401 或 503）', async ({ request }) => {
    const res = await request.post(`${BASE_URL}/api/admin/init`, {
      data: { username: `probe_${Date.now()}`, password: 'InitPass123!' },
    })
    expect([401, 503]).toContain(res.status())
  })

  test('? 修复：image-proxy file:// 被 400 拒绝', async ({ request }) => {
    const evilUrl = 'file://p3-sign.douyinpic.com/etc/passwd'
    const res = await request.get(`${BASE_URL}/api/image-proxy?url=${encodeURIComponent(evilUrl)}`)
    expect(res.status()).toBe(400)
    const body = await res.json()
    expect(body.detail).not.toMatch(/Traceback|ConnectError|gaierror/i)
  })

  test('? 修复：image-proxy 502 错误不泄露内部异常', async ({ request }) => {
    const probeUrl = 'https://p3-sign.douyinpic.com/NONEXIST_PROBE_12345'
    const res = await request.get(`${BASE_URL}/api/image-proxy?url=${encodeURIComponent(probeUrl)}`)
    if (res.status() !== 200) {
      const body = await res.json().catch(() => ({}))
      expect((body.detail || '').toLowerCase()).not.toMatch(/traceback|exception|file "\/|connecterror|gaierror/)
    }
  })

  test('? 修复：默认 JWT 密钥不可伪造 Token（期望 401）', async ({ request }) => {
    const now = Math.floor(Date.now() / 1000)
    const forged = signHs256(
      { sub: String(userId), sv: sessionVersion, iat: now, exp: now + 3600 },
      'change-me-in-production-use-long-random-string',
    )
    const res = await request.get(`${BASE_URL}/api/auth/me`, {
      headers: { Authorization: `Bearer ${forged}` },
    })
    expect(res.status()).toBe(401)
  })
})
