<template>
  <div class="login-shell">
    <!-- 左侧品牌展示区 -->
    <div class="brand-panel">
      <div class="brand-content">
        <div class="brand-logo">
          <div class="brand-logo-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/></svg>
          </div>
          <span class="brand-name">文策引擎</span>
        </div>
        <h1 class="brand-headline">AI 驱动的内容<br />创作工作台</h1>
        <p class="brand-desc">基于爆款博主风格 + 产品知识库，一键生成高转化短视频文案</p>

        <div class="feature-list">
          <div class="feature-item" v-for="f in features" :key="f.text">
            <div class="feature-icon">
              <n-icon size="18" color="rgba(255,255,255,0.9)">
                <component :is="f.icon" />
              </n-icon>
            </div>
            <span>{{ f.text }}</span>
          </div>
        </div>
      </div>

      <div class="brand-bg-orb orb1"></div>
      <div class="brand-bg-orb orb2"></div>
    </div>

    <!-- 右侧登录区 -->
    <div class="login-panel">
      <div class="login-card">
        <div class="login-header">
          <div class="login-title">{{ isRegister ? '创建账号' : '欢迎回来' }}</div>
          <div class="login-sub">{{ isRegister ? '注册后即可免费体验' : '登录你的账号继续创作' }}</div>
        </div>

        <!-- OAuth 按钮 -->
        <div class="oauth-buttons">
          <button class="oauth-btn google" @click="handleGoogleLogin" :disabled="oauthLoading">
            <svg viewBox="0 0 24 24" width="18" height="18">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
            <span>使用 Google 登录</span>
          </button>
          <button class="oauth-btn github" @click="handleGithubLogin" :disabled="oauthLoading">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
              <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/>
            </svg>
            <span>使用 GitHub 登录</span>
          </button>
        </div>

        <!-- 分隔符 -->
        <div class="divider">
          <span>或使用邮箱</span>
        </div>

        <!-- 邮箱表单 -->
        <div class="email-form">
          <n-input
            v-if="isRegister"
            v-model:value="form.nickname"
            placeholder="昵称（选填）"
            size="large"
            style="margin-bottom: 12px"
          />
          <n-input
            v-model:value="form.email"
            placeholder="邮箱地址"
            size="large"
            style="margin-bottom: 12px"
            @keyup.enter="handleEmailSubmit"
          />
          <n-input
            v-model:value="form.password"
            type="password"
            show-password-on="click"
            placeholder="密码（至少 8 位，含字母和数字）"
            size="large"
            style="margin-bottom: 16px"
            @keyup.enter="handleEmailSubmit"
          />
          <n-button
            type="primary"
            block
            size="large"
            :loading="emailLoading"
            :disabled="!form.email || !form.password"
            @click="handleEmailSubmit"
          >
            {{ isRegister ? '注 册' : '登 录' }}
          </n-button>
        </div>

        <!-- 切换登录/注册 -->
        <div class="toggle-mode">
          <span v-if="!isRegister">
            还没有账号？
            <a href="#" @click.prevent="isRegister = true">立即注册</a>
          </span>
          <span v-else>
            已有账号？
            <a href="#" @click.prevent="isRegister = false">去登录</a>
          </span>
        </div>

        <!-- 新用户提示 -->
        <div class="new-user-tip">
          <n-icon size="16" color="#d97706"><GiftOutline /></n-icon>
          <span>新用户免费体验 <strong>1天</strong>，无需先付费</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useMessage } from 'naive-ui'
import { useAuthStore } from '../stores/auth.js'
import { authApi } from '../api/index.js'
import {
  FlameOutline, PersonCircleOutline,
  CubeOutline, SparklesOutline, GiftOutline
} from '@vicons/ionicons5'

const router = useRouter()
const route = useRoute()
const message = useMessage()
const authStore = useAuthStore()

const isRegister = ref(false)
const emailLoading = ref(false)
const oauthLoading = ref(false)
const form = ref({ email: '', password: '', nickname: '' })



const features = [
  { icon: FlameOutline, text: '爆款选题库 — 多平台爆款视频搜索分析' },
  { icon: PersonCircleOutline, text: '博主风格提取 — AI 学习头部博主写法' },
  { icon: CubeOutline, text: '产品知识库 — RAG 精准植入产品亮点' },
  { icon: SparklesOutline, text: '一键生成 — 标题/钩子/脚本/CTA 完整输出' },
]

// ── 邮箱登录/注册 ──
async function handleEmailSubmit() {
  const email = form.value.email.trim()
  if (!email || !email.includes('@')) {
    message.warning('请输入有效邮箱')
    return
  }
  if (form.value.password.length < 8) {
    message.warning('密码至少 8 位')
    return
  }
  if (isRegister.value && (/^\d+$/.test(form.value.password) || /^[a-zA-Z]+$/.test(form.value.password))) {
    message.warning('密码需要同时包含字母和数字')
    return
  }

  emailLoading.value = true
  try {
    let res
    if (isRegister.value) {
      res = await authApi.register({
        email,
        password: form.value.password,
        nickname: form.value.nickname,
      })
      message.success('注册成功')
    } else {
      res = await authApi.login({
        email,
        password: form.value.password,
      })
    }
    _handleLoginSuccess(res.data)
  } catch (e) {
    const detail = e.response?.data?.detail || '操作失败'
    message.error(detail)
  } finally {
    emailLoading.value = false
  }
}

// ── Google OAuth ──
async function handleGoogleLogin() {
  oauthLoading.value = true
  try {
    const redirectUri = window.location.origin + '/auth/callback?provider=google'
    const { data } = await authApi.googleUrl({ redirect_uri: redirectUri })
    window.location.href = data.url
  } catch (e) {
    message.error(e.response?.data?.detail || 'Google 登录不可用')
    oauthLoading.value = false
  }
}

// ── GitHub OAuth ──
async function handleGithubLogin() {
  oauthLoading.value = true
  try {
    const redirectUri = window.location.origin + '/auth/callback?provider=github'
    const { data } = await authApi.githubUrl({ redirect_uri: redirectUri })
    window.location.href = data.url
  } catch (e) {
    message.error(e.response?.data?.detail || 'GitHub 登录不可用')
    oauthLoading.value = false
  }
}

// ── OAuth 回调处理 ──
async function handleOAuthCallback() {
  const urlParams = new URLSearchParams(window.location.search)
  const code = urlParams.get('code')
  const provider = urlParams.get('provider')

  if (!code || !provider) return false

  emailLoading.value = true
  try {
    let res
    const redirectUri = window.location.origin + `/auth/callback?provider=${provider}`
    if (provider === 'google') {
      res = await authApi.googleCallback({ code, redirect_uri: redirectUri })
    } else if (provider === 'github') {
      res = await authApi.githubCallback({ code })
    } else {
      return false
    }
    _handleLoginSuccess(res.data)
    // 清除 URL 参数
    window.history.replaceState({}, '', '/login')
    return true
  } catch (e) {
    message.error(e.response?.data?.detail || '第三方登录失败')
    window.history.replaceState({}, '', '/login')
    emailLoading.value = false
    return true
  }
}

// ── 登录成功统一处理 ──
function _handleLoginSuccess(data) {
  authStore.setToken(data.token)
  authStore.setUser(data.user)
  authStore.setTenant(data.tenant || null)
  router.replace('/')
}

onMounted(async () => {
  if (authStore.isAuthenticated) {
    router.replace('/')
    return
  }

  // 处理 OAuth 回调（从 Google/GitHub 重定向回来）
  await handleOAuthCallback()
})
</script>

<style scoped>
.login-shell {
  display: flex;
  min-height: 100vh;
  width: 100vw;
  background: var(--c-bg-page, #f8fafc);
}

/* ── 左侧品牌区 ── */
.brand-panel {
  flex: 1;
  background: linear-gradient(145deg, #4338ca 0%, #6366f1 50%, #818cf8 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 48px;
  position: relative;
  overflow: hidden;
}
.brand-content { position: relative; z-index: 2; max-width: 440px; }
.brand-logo { display: flex; align-items: center; gap: 12px; margin-bottom: 48px; }
.brand-logo-icon {
  width: 44px; height: 44px; background: rgba(255,255,255,.15); border-radius: 12px;
  display: flex; align-items: center; justify-content: center; backdrop-filter: blur(10px);
}
.brand-name { font-size: 20px; font-weight: 700; color: #fff; letter-spacing: -0.3px; }
.brand-headline { font-size: 40px; font-weight: 800; color: #fff; line-height: 1.2; margin-bottom: 16px; letter-spacing: -0.5px; }
.brand-desc { font-size: 15px; color: rgba(255,255,255,.7); line-height: 1.7; margin-bottom: 40px; }
.feature-list { display: flex; flex-direction: column; gap: 16px; }
.feature-item { display: flex; align-items: center; gap: 12px; font-size: 14px; color: rgba(255,255,255,.88); }
.feature-icon {
  width: 36px; height: 36px; background: rgba(255,255,255,.12); border-radius: 10px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.brand-bg-orb { position: absolute; border-radius: 50%; background: rgba(255,255,255,.08); }
.orb1 { width: 500px; height: 500px; top: -180px; right: -150px; }
.orb2 { width: 300px; height: 300px; bottom: -100px; left: -100px; }

/* ── 右侧登录卡片 ── */
.login-panel {
  width: 480px; flex-shrink: 0; display: flex; align-items: center;
  justify-content: center; padding: 40px 48px; background: #fff;
}
.login-card { width: 100%; max-width: 360px; }
.login-header { text-align: center; margin-bottom: 32px; }
.login-title { font-size: 24px; font-weight: 700; color: var(--c-text-1, #0f172a); margin-bottom: 8px; letter-spacing: -0.3px; }
.login-sub { font-size: 14px; color: var(--c-text-4, #94a3b8); }

/* ── OAuth 按钮 ── */
.oauth-buttons { display: flex; flex-direction: column; gap: 10px; margin-bottom: 24px; }
.oauth-btn {
  display: flex; align-items: center; justify-content: center; gap: 10px;
  height: 44px; border-radius: 10px; border: 1px solid #e2e8f0; background: #fff;
  cursor: pointer; font-size: 14px; font-weight: 500; color: var(--c-text-2, #334155);
  transition: all 150ms cubic-bezier(0.4, 0, 0.2, 1);
  outline: none;
}
.oauth-btn:hover { border-color: #cbd5e1; background: #f8fafc; transform: translateY(-1px); box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.oauth-btn:active { transform: translateY(0); box-shadow: none; }
.oauth-btn:focus-visible { box-shadow: 0 0 0 2px var(--c-primary, #6366f1); }
.oauth-btn:disabled { opacity: .5; cursor: not-allowed; transform: none; }
.oauth-btn.google:hover { border-color: #93b4f4; background: #f5f8ff; }
.oauth-btn.github { background: #1a1a2e; color: #fff; border-color: #1a1a2e; }
.oauth-btn.github:hover { background: #2a2a3e; border-color: #2a2a3e; }
.oauth-btn.github:disabled { background: #1a1a2e; }

/* ── 分隔符 ── */
.divider {
  display: flex; align-items: center; gap: 12px; margin-bottom: 24px;
  color: var(--c-text-4, #94a3b8); font-size: 13px;
}
.divider::before, .divider::after { content: ''; flex: 1; height: 1px; background: #e2e8f0; }

/* ── 切换登录/注册 ── */
.toggle-mode { text-align: center; margin-top: 20px; font-size: 13px; color: var(--c-text-3, #64748b); }
.toggle-mode a { color: var(--c-primary, #6366f1); text-decoration: none; font-weight: 600; }
.toggle-mode a:hover { text-decoration: underline; }

/* ── 底部提示 ── */
.new-user-tip {
  margin-top: 20px; background: #fffbeb;
  border: 1px solid #fde68a; border-radius: 10px; padding: 12px 16px;
  font-size: 13px; color: #92400e; text-align: center;
  display: flex; align-items: center; justify-content: center; gap: 8px;
}

/* 响应式 */
@media (max-width: 768px) {
  .login-shell { flex-direction: column; }
  .brand-panel { padding: 40px 24px; min-height: 36vh; }
  .brand-headline { font-size: 28px; }
  .feature-list { display: none; }
  .login-panel { width: 100%; padding: 32px 24px; }
  .login-card { max-width: 100%; }
}
</style>
