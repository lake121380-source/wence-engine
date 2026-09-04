<template>
  <div class="login-shell">
    <!-- 左侧品牌区 -->
    <div class="brand-panel">
      <div class="brand-content">
        <div class="brand-logo">
          <div class="brand-logo-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/>
            </svg>
          </div>
          <span class="brand-name">文策引擎</span>
        </div>
        <h1 class="brand-headline">AI 驱动的内容<br />创作工作台</h1>
        <p class="brand-desc">基于爆款博主风格 + 产品知识库，<br />一键生成高转化短视频文案</p>
        <div class="feature-list">
          <div class="feature-item" v-for="f in features" :key="f.text">
            <div class="feature-icon">
              <n-icon size="16" color="rgba(255,255,255,0.9)"><component :is="f.icon" /></n-icon>
            </div>
            <span>{{ f.text }}</span>
          </div>
        </div>
        <div class="brand-badge">
          <n-icon size="14" color="#fbbf24"><GiftOutline /></n-icon>
          <span>新用户免费体验 <strong>1 天</strong></span>
        </div>
      </div>
      <div class="brand-bg-orb orb1"></div>
      <div class="brand-bg-orb orb2"></div>
      <div class="brand-bg-orb orb3"></div>
    </div>

    <!-- 右侧登录区 -->
    <div class="login-panel">
      <div class="login-card">
        <!-- 标题 -->
        <div class="login-header">
          <div class="login-logo-sm">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6366f1" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/>
            </svg>
          </div>
          <h2 class="login-title">{{ isRegister ? '创建账号' : '欢迎回来' }}</h2>
          <p class="login-sub">{{ isRegister ? '注册即可开始免费体验' : '登录你的账号继续创作' }}</p>
          <div v-if="authStore.isAuthenticated && !isRegister" class="switch-account-banner">
            当前已登录为 <strong>{{ authStore.user?.nickname || authStore.user?.email }}</strong>，
            <a href="#" @click.prevent="handleLogoutAndSwitch">切换账号</a>
          </div>
        </div>

        <!-- 登录方式 Tab -->
        <div v-if="!isRegister" class="login-tabs">
          <button class="tab-btn" :class="{ active: loginTab === 'email' }" @click="loginTab = 'email'">邮箱登录</button>
          <button v-if="wechatLoginEnabled" class="tab-btn" :class="{ active: loginTab === 'wechat' }" @click="switchToWechatTab">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" style="flex-shrink:0">
              <path d="M8.691 2C4.485 2 1 5.485 1 9.691c0 2.315 1.033 4.394 2.672 5.816L2.74 18l3.03-1.535A8.576 8.576 0 008.69 17c.305 0 .607-.017.901-.05-.188-.605-.29-1.244-.29-1.907 0-3.87 3.154-7.01 7.047-7.01.217 0 .433.01.646.03C16.14 4.73 12.69 2 8.692 2zm-2.2 4.2a1.1 1.1 0 110 2.2 1.1 1.1 0 010-2.2zm4.4 0a1.1 1.1 0 110 2.2 1.1 1.1 0 010-2.2zM16.348 9.8c-3.313 0-6 2.566-6 5.724 0 3.158 2.687 5.724 6 5.724.977 0 1.9-.233 2.696-.64l2.29 1.17-.8-2.588C21.405 18.09 22.348 17.01 22.348 15.524c0-3.158-2.687-5.724-6-5.724zm-1.8 3.2a.9.9 0 110 1.8.9.9 0 010-1.8zm3.6 0a.9.9 0 110 1.8.9.9 0 010-1.8z"/>
            </svg>
            微信授权
          </button>
        </div>

        <!-- 邮箱表单 -->
        <div v-if="loginTab === 'email' || isRegister" class="form-body">
          <div v-if="isRegister" class="field-wrap">
            <label class="field-label">昵称（选填）</label>
            <n-input v-model:value="form.nickname" placeholder="你的昵称" size="large" round />
          </div>
          <div class="field-wrap">
            <label class="field-label">邮箱地址</label>
            <n-input v-model:value="form.email" placeholder="your@email.com" size="large" round @keyup.enter="!isRegister && handleEmailSubmit()" />
          </div>
          <div class="field-wrap">
            <label class="field-label">密码</label>
            <n-input v-model:value="form.password" type="password" show-password-on="click" :placeholder="isRegister ? '至少 8 位，含字母和数字' : '请输入密码'" size="large" round @keyup.enter="!isRegister && handleEmailSubmit()" />
          </div>
          <div v-if="isRegister" class="field-wrap">
            <label class="field-label">邮箱验证码</label>
            <div class="code-row">
              <n-input v-model:value="form.verifyCode" placeholder="6 位验证码" size="large" maxlength="6" round style="flex:1" @keyup.enter="handleEmailSubmit" />
              <n-button size="large" round :disabled="codeSending || codeCountdown > 0 || !form.email" :loading="codeSending" style="min-width:108px;white-space:nowrap" @click="sendVerifyCode">
                {{ codeCountdown > 0 ? `${codeCountdown}s 重发` : '发送验证码' }}
              </n-button>
            </div>
          </div>
          <n-button type="primary" block size="large" round :loading="emailLoading" :disabled="isRegister ? (!form.email || !form.password || !form.verifyCode) : (!form.email || !form.password)" style="margin-top:4px" @click="handleEmailSubmit">
            {{ isRegister ? '注 册' : '登 录' }}
          </n-button>
          <div class="toggle-row">
            <span v-if="!isRegister">还没有账号？<a href="#" @click.prevent="switchToRegister">立即注册</a></span>
            <span v-else>已有账号？<a href="#" @click.prevent="switchToLogin">去登录</a></span>
          </div>
        </div>

        <!-- 微信授权 Tab -->
        <div v-else-if="wechatLoginEnabled && loginTab === 'wechat'" class="wechat-body">
          <div v-if="oauthLoading" class="qr-state">
            <n-spin size="large" />
            <span>正在处理微信授权…</span>
          </div>
          <template v-else>
            <div class="qr-frame oauth-frame">
              <div class="oauth-icon-wrap">
                <svg viewBox="0 0 24 24" width="42" height="42" fill="#07c160">
                  <path d="M8.691 2C4.485 2 1 5.485 1 9.691c0 2.315 1.033 4.394 2.672 5.816L2.74 18l3.03-1.535A8.576 8.576 0 008.69 17c.305 0 .607-.017.901-.05-.188-.605-.29-1.244-.29-1.907 0-3.87 3.154-7.01 7.047-7.01.217 0 .433.01.646.03C16.14 4.73 12.69 2 8.692 2zm-2.2 4.2a1.1 1.1 0 110 2.2 1.1 1.1 0 010-2.2zm4.4 0a1.1 1.1 0 110 2.2 1.1 1.1 0 010-2.2zM16.348 9.8c-3.313 0-6 2.566-6 5.724 0 3.158 2.687 5.724 6 5.724.977 0 1.9-.233 2.696-.64l2.29 1.17-.8-2.588C21.405 18.09 22.348 17.01 22.348 15.524c0-3.158-2.687-5.724-6-5.724zm-1.8 3.2a.9.9 0 110 1.8.9.9 0 010-1.8zm3.6 0a.9.9 0 110 1.8.9.9 0 010-1.8z"/>
                </svg>
              </div>
            </div>
            <p class="qr-tip">点击下方按钮，跳转微信授权登录</p>
            <n-button type="primary" size="large" round :loading="oauthLoading" @click="startWechatOAuth">微信授权登录</n-button>
            <p class="qr-expire">授权完成后将自动返回并登录</p>
          </template>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useMessage } from 'naive-ui'
import { useAuthStore } from '../stores/auth.js'
import { authApi } from '../api/index.js'
import { FlameOutline, PersonCircleOutline, CubeOutline, SparklesOutline, GiftOutline } from '@vicons/ionicons5'

const router = useRouter()
const route = useRoute()
const message = useMessage()
const authStore = useAuthStore()
const wechatLoginEnabled = true

const loginTab = ref('email')
const isRegister = ref(false)
const emailLoading = ref(false)
const codeSending = ref(false)
const codeCountdown = ref(0)
let countdownTimer = null

const form = ref({ email: '', password: '', nickname: '', verifyCode: '' })
const oauthLoading = ref(false)

const features = [
  { icon: FlameOutline,        text: '爆款选题库 — 多平台爆款视频分析' },
  { icon: PersonCircleOutline, text: '博主风格提取 — AI 学习头部博主写法' },
  { icon: CubeOutline,         text: '产品知识库 — RAG 精准植入产品亮点' },
  { icon: SparklesOutline,     text: '一键生成 — 标题/钩子/脚本/CTA 完整输出' },
]

async function sendVerifyCode() {
  const email = form.value.email.trim()
  if (!email || !email.includes('@')) { message.warning('请先填写有效的邮箱地址'); return }
  codeSending.value = true
  try {
    const { data } = await authApi.sendRegisterCode({ email, nickname: form.value.nickname })
    message.success('验证码已发送，请查收邮件（10分钟内有效）')
    if (data?.dev_code) { form.value.verifyCode = String(data.dev_code); message.info(`调试验证码：${data.dev_code}`) }
    codeCountdown.value = 60
    countdownTimer = setInterval(() => { codeCountdown.value--; if (codeCountdown.value <= 0) { clearInterval(countdownTimer); countdownTimer = null } }, 1000)
  } catch (e) {
    message.error(e.response?.data?.detail || '验证码发送失败')
  } finally { codeSending.value = false }
}

async function handleEmailSubmit() {
  const email = form.value.email.trim()
  if (!email || !email.includes('@')) { message.warning('请输入有效邮箱'); return }
  if (form.value.password.length < 8) { message.warning('密码至少 8 位'); return }
  if (isRegister.value && (/^\d+$/.test(form.value.password) || /^[a-zA-Z]+$/.test(form.value.password))) { message.warning('密码需要同时包含字母和数字'); return }
  if (isRegister.value && !form.value.verifyCode) { message.warning('请先获取并填写邮箱验证码'); return }
  emailLoading.value = true
  try {
    let res
    if (isRegister.value) {
      res = await authApi.register({ email, password: form.value.password, nickname: form.value.nickname, verify_code: form.value.verifyCode })
    } else {
      res = await authApi.login({ email, password: form.value.password })
    }
    _handleLoginSuccess(res.data)
  } catch (e) {
    message.error(e.response?.data?.detail || '操作失败')
  } finally { emailLoading.value = false }
}

function switchToWechatTab() {
  if (!wechatLoginEnabled) return
  loginTab.value = 'wechat'
}

async function startWechatOAuth() {
  oauthLoading.value = true
  try {
    const redirectUri = `${window.location.origin}/auth/callback?provider=wechat`
    const { data } = await authApi.getOAuthUrl({ redirect_uri: redirectUri })
    if (!data?.url) throw new Error('未获取到微信授权地址')
    window.location.href = data.url
  } catch (e) {
    oauthLoading.value = false
    message.error(e.response?.data?.detail || e.message || '获取微信授权地址失败')
  }
}

async function handleWechatOAuthCallback() {
  if (route.path !== '/auth/callback') return
  const provider = String(route.query.provider || '')
  if (provider === 'wechat' && !wechatLoginEnabled) {
    message.info('微信登录暂未开放，请使用邮箱登录')
    router.replace('/login')
    return
  }
  if (provider !== 'wechat') {
    router.replace('/login')
    return
  }

  const code = String(route.query.code || '')
  const err = String(route.query.error || '')
  const errMsg = String(route.query.errmsg || route.query.error_description || '')

  if (err) {
    message.error(errMsg || `微信授权失败: ${err}`)
    router.replace('/login')
    return
  }
  if (!code) {
    message.warning('微信授权缺少 code 参数，请重试')
    router.replace('/login')
    return
  }

  loginTab.value = 'wechat'
  oauthLoading.value = true
  try {
    const res = await authApi.oauthCallback({ code })
    _handleLoginSuccess(res.data)
  } catch (e) {
    message.error(e.response?.data?.detail || '微信授权登录失败')
    router.replace('/login')
  } finally {
    oauthLoading.value = false
  }
}

function _handleLoginSuccess(data) {
  authStore.setToken(data.token)
  authStore.setUser(data.user)
  authStore.setTenant(data.tenant || null)
  // 全页刷新以销毁 keep-alive 缓存的旧账号数据，防止数据泄露
  window.location.href = '/app'
}

function switchToRegister() {
  isRegister.value = true; loginTab.value = 'email'
  form.value.verifyCode = ''; codeCountdown.value = 0
  if (countdownTimer) { clearInterval(countdownTimer); countdownTimer = null }
}

function switchToLogin() {
  isRegister.value = false; form.value.verifyCode = ''; codeCountdown.value = 0
  if (countdownTimer) { clearInterval(countdownTimer); countdownTimer = null }
}

function handleLogoutAndSwitch() {
  authStore.logout()
  window.location.reload()
}

onMounted(async () => {
  if (authStore.isAuthenticated) {
    // 已登录用户访问登录页：显示切换账号提示，不自动跳转
    return
  }
  await handleWechatOAuthCallback()
})
onBeforeUnmount(() => { if (countdownTimer) clearInterval(countdownTimer) })
</script>

<style scoped>
.login-shell { display: flex; min-height: 100vh; width: 100vw; background: #f0f9ff; }

/* 左侧品牌 */
.brand-panel {
  flex: 1;
  background: linear-gradient(150deg, #0c4a6e 0%, #0891b2 55%, #22d3ee 100%);
  display: flex; align-items: center; justify-content: center;
  padding: 60px 56px; position: relative; overflow: hidden;
}
.brand-content { position: relative; z-index: 2; max-width: 420px; }
.brand-logo { display: flex; align-items: center; gap: 10px; margin-bottom: 52px; }
.brand-logo-icon {
  width: 40px; height: 40px; background: rgba(255,255,255,.18); border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  backdrop-filter: blur(8px); border: 1px solid rgba(255,255,255,.2);
}
.brand-name { font-size: 18px; font-weight: 700; color: #fff; letter-spacing: 0.2px; }
.brand-headline { font-size: 38px; font-weight: 800; color: #fff; line-height: 1.22; margin-bottom: 16px; letter-spacing: -0.5px; }
.brand-desc { font-size: 14px; color: rgba(255,255,255,.65); line-height: 1.8; margin-bottom: 40px; }
.feature-list { display: flex; flex-direction: column; gap: 14px; margin-bottom: 40px; }
.feature-item { display: flex; align-items: center; gap: 12px; font-size: 13px; color: rgba(255,255,255,.85); }
.feature-icon { width: 30px; height: 30px; background: rgba(255,255,255,.1); border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; border: 1px solid rgba(255,255,255,.1); }
.brand-badge { display: inline-flex; align-items: center; gap: 6px; background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.2); border-radius: 20px; padding: 6px 14px; font-size: 12px; color: rgba(255,255,255,.9); backdrop-filter: blur(4px); }
.brand-badge strong { color: #fbbf24; }
.brand-bg-orb { position: absolute; border-radius: 50%; }
.orb1 { width: 480px; height: 480px; top: -160px; right: -140px; background: rgba(255,255,255,.05); }
.orb2 { width: 260px; height: 260px; bottom: -80px; left: -80px; background: rgba(255,255,255,.05); }
.orb3 { width: 140px; height: 140px; top: 40%; left: 20%; background: rgba(255,255,255,.04); }

/* 右侧面板 */
.login-panel { width: 500px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; padding: 40px 48px; background: #f0f9ff; }
.login-card { width: 100%; max-width: 380px; background: #fff; border-radius: 20px; padding: 36px 36px 32px; box-shadow: 0 4px 6px -1px rgba(0,0,0,.04), 0 16px 36px -8px rgba(8,145,178,.1); border: 1px solid #e0f2fe; }

/* 头部 */
.login-header { text-align: center; margin-bottom: 28px; }
.login-logo-sm { width: 40px; height: 40px; background: #e0f2fe; border-radius: 10px; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 14px; }
.login-title { font-size: 22px; font-weight: 700; color: #0f172a; margin: 0 0 6px; letter-spacing: -0.3px; }
.login-sub { font-size: 13px; color: #94a3b8; margin: 0; }

/* Tab */
.login-tabs { display: flex; background: #f0f9ff; border-radius: 10px; padding: 3px; margin-bottom: 24px; gap: 3px; }
.tab-btn { flex: 1; height: 36px; border: none; background: transparent; border-radius: 8px; font-size: 13px; font-weight: 500; color: #64748b; cursor: pointer; transition: all 180ms ease; display: flex; align-items: center; justify-content: center; gap: 5px; outline: none; }
.tab-btn.active { background: #fff; color: #0891b2; box-shadow: 0 1px 4px rgba(0,0,0,.06); font-weight: 600; }
.tab-btn:not(.active):hover { color: #334155; }

/* 表单 */
.form-body { display: flex; flex-direction: column; }
.field-wrap { margin-bottom: 14px; }
.field-label { display: block; font-size: 12px; font-weight: 600; color: #475569; margin-bottom: 6px; letter-spacing: 0.2px; }
.code-row { display: flex; gap: 8px; align-items: stretch; }
.toggle-row { text-align: center; margin-top: 18px; font-size: 13px; color: #64748b; }
.toggle-row a { color: #0891b2; font-weight: 600; text-decoration: none; margin-left: 4px; }
.toggle-row a:hover { text-decoration: underline; }

.switch-account-banner {
  margin-top: 12px;
  padding: 8px 12px;
  background: #fef3c7;
  border: 1px solid #fcd34d;
  border-radius: 8px;
  font-size: 12px;
  color: #92400e;
  text-align: center;
  line-height: 1.6;
}
.switch-account-banner a {
  color: #0891b2;
  font-weight: 600;
  text-decoration: none;
}
.switch-account-banner a:hover {
  text-decoration: underline;
}

/* 微信二维码 */
.wechat-body { display: flex; flex-direction: column; align-items: center; padding: 8px 0; min-height: 280px; justify-content: center; gap: 12px; }
.qr-frame { width: 196px; height: 196px; padding: 8px; background: #fff; border: 2px solid #e2e8f0; border-radius: 16px; box-shadow: 0 4px 16px rgba(0,0,0,.06); }
.qr-img { width: 100%; height: 100%; display: block; border-radius: 8px; }
.oauth-frame { display: flex; align-items: center; justify-content: center; background: linear-gradient(180deg, #f8fffb 0%, #f0fdf4 100%); }
.oauth-icon-wrap { width: 88px; height: 88px; border-radius: 50%; background: #e8fff0; border: 1px solid #bbf7d0; display: flex; align-items: center; justify-content: center; }
.qr-tip { font-size: 13px; color: #475569; text-align: center; margin: 4px 0 0; line-height: 1.6; }
.qr-expire { font-size: 11px; color: #94a3b8; margin: 0; }
.qr-state { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px; padding: 20px 0; font-size: 14px; color: #475569; width: 100%; }

@media (max-width: 860px) {
  .brand-panel { display: none; }
  .login-panel { width: 100%; padding: 24px 20px; }
  .login-card { max-width: 100%; padding: 28px 24px 24px; }
}
</style>
