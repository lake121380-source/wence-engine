<template>
  <n-config-provider :theme-overrides="themeOverrides" :locale="zhCN" :date-locale="dateZhCN">
    <n-message-provider>
      <n-dialog-provider>
      <router-view v-if="isPublicRoute" />

      <div v-else class="layout">
        <!-- 即梦风格左侧导航 -->
        <aside class="sidebar">
          <div class="sidebar-logo" @click="router.push('/app')">
            <svg width="28" height="28" viewBox="0 0 32 32" fill="none">
              <defs>
                <linearGradient id="sg" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0%" stop-color="#22d3ee"/>
                  <stop offset="100%" stop-color="#0891b2"/>
                </linearGradient>
              </defs>
              <path d="M16 3 L18.5 12 L28 12 L20.5 17.5 L23 27 L16 21.5 L9 27 L11.5 17.5 L4 12 L13.5 12 Z" fill="url(#sg)"/>
            </svg>
          </div>

          <nav class="sidebar-nav">
            <a
              v-for="item in menuOptions"
              :key="item.key"
              class="nav-item"
              :class="{ active: activeKey === item.key }"
              @click.prevent="router.push(item.key)"
              href="#"
            >
              <span class="nav-icon"><n-icon size="18"><component :is="item.icon" /></n-icon></span>
              <span class="nav-label">{{ item.label }}</span>
            </a>
          </nav>

          <div class="sidebar-bottom">
            <a
              class="nav-item"
              :class="{ active: activeKey === '/pricing' }"
              @click.prevent="router.push('/pricing')"
              href="#"
            >
              <span class="nav-icon"><n-icon size="18"><CardOutline /></n-icon></span>
              <span class="nav-label">订阅</span>
            </a>
            <a
              class="nav-item"
              :class="{ active: activeKey === '/settings' }"
              @click.prevent="router.push('/settings')"
              href="#"
            >
              <span class="nav-icon"><n-icon size="18"><SettingsOutline /></n-icon></span>
              <span class="nav-label">设置</span>
            </a>
            <div v-if="authStore.user" class="sidebar-user" @click="handleLogout" title="退出登录">
              <n-avatar :src="authStore.user.avatar || defaultAvatar" round :size="30" />
            </div>
          </div>
        </aside>

        <!-- 主内容区 -->
        <main class="main-content">
          <router-view v-slot="{ Component }">
            <keep-alive :max="10">
              <component :is="Component" />
            </keep-alive>
          </router-view>
        </main>
      </div>

      <!-- 订阅过期提示弹窗 -->
      <n-modal
        v-model:show="subscriptionStore.showExpiredModal"
        preset="card"
        style="width: 440px; border-radius: 16px;"
        :bordered="false"
        :mask-closable="true"
        :closable="true"
        @close="subscriptionStore.dismiss()"
      >
        <template #header>
          <div style="display:flex;align-items:center;gap:10px;">
            <n-icon size="22" style="color:#f59e0b"><WarningOutline /></n-icon>
            <span style="font-weight:700;font-size:16px;">订阅已到期</span>
          </div>
        </template>

        <div style="line-height:1.7;color:#444;">
          <p style="margin:0 0 12px;">您的订阅已到期，以下功能暂时无法使用：</p>
          <ul style="margin:0 0 16px;padding-left:20px;color:#666;">
            <li>AI 文案生成</li>
            <li>博主抓取 & 风格分析</li>
            <li>选题搜索 & 推荐</li>
            <li>文档上传 & 知识库检索</li>
            <li>内容生成历史</li>
          </ul>
          <p style="margin:0;color:#888;font-size:13px;">续费后即可恢复所有功能，历史数据不会丢失。</p>
        </div>

        <template #footer>
          <div style="display:flex;justify-content:flex-end;gap:10px;">
            <n-button @click="subscriptionStore.dismiss()">稍后再说</n-button>
            <n-button type="primary" @click="goToPricing">立即续费</n-button>
          </div>
        </template>
      </n-modal>

      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { zhCN, dateZhCN, NIcon } from 'naive-ui'
import {
  PeopleOutline, DocumentTextOutline,
  ColorPaletteOutline, SparklesOutline, TimeOutline,
  TrendingUpOutline, BulbOutline, CalendarOutline,
  LogOutOutline, CardOutline, SettingsOutline, WarningOutline,
} from '@vicons/ionicons5'
import { useAuthStore } from './stores/auth.js'
import { useSubscriptionStore } from './stores/subscription.js'
import { authApi } from './api/index.js'

const defaultAvatar = `data:image/svg+xml;base64,${btoa('<svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 30 30"><rect width="30" height="30" rx="15" fill="#0891b2"/><text x="15" y="20" text-anchor="middle" font-family="sans-serif" font-size="14" font-weight="bold" fill="white">U</text></svg>')}`

const router = useRouter()
const route = useRoute()
const isPublicRoute = computed(() => !!route.meta.public)
const authStore = useAuthStore()
const subscriptionStore = useSubscriptionStore()

onMounted(async () => {
  if (!authStore.isAuthenticated) return
  try {
    const { data } = await authApi.me()
    authStore.setUser(data)
  } catch {}
})

function handleLogout() {
  authStore.logout()
  // 全页刷新以销毁 keep-alive 缓存的所有组件状态
  window.location.href = '/login'
}

function goToPricing() {
  subscriptionStore.dismiss()
  router.push('/pricing')
}

const themeOverrides = {
  common: {
    primaryColor: '#0891b2',
    primaryColorHover: '#0e7490',
    primaryColorPressed: '#155e75',
    primaryColorSuppl: '#0891b2',
    infoColor: '#0891b2',
    successColor: '#22c55e',
    warningColor: '#f59e0b',
    errorColor: '#ef4444',
    borderRadius: '10px',
    fontFamily: "'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Segoe UI', Roboto, sans-serif",
    bodyColor: '#f0f9ff',
  },
  Button: { borderRadiusMedium: '10px', borderRadiusSmall: '8px' },
  Card: { borderRadius: '14px', color: '#ffffff', borderColor: '#e0f2fe' },
  Input: {
    borderRadius: '10px',
    color: '#f8fcff',
    colorFocus: '#ffffff',
    borderColor: '#e0f2fe',
    borderHover: '#7dd3fc',
    borderFocus: '#0891b2',
    boxShadowFocus: '0 0 0 2px rgba(8,145,178,0.12)',
    textColor: '#0f172a',
    placeholderColor: '#94a3b8',
    caretColor: '#0891b2',
  },
  InternalSelection: {
    borderRadius: '10px',
    color: '#f8fcff',
    colorActive: '#ffffff',
    borderColor: '#e0f2fe',
    borderHover: '#7dd3fc',
    borderFocus: '#0891b2',
    boxShadowFocus: '0 0 0 2px rgba(8,145,178,0.12)',
    textColor: '#0f172a',
    placeholderColor: '#94a3b8',
  },
  InternalSelectMenu: {
    borderRadius: '10px',
    optionTextColor: '#0f172a',
    optionCheckColor: '#0891b2',
  },
  Tag: { borderRadius: '8px' },
}

const activeKey = computed(() => route.path)

const menuOptions = [
  { label: '创作', key: '/app',        icon: SparklesOutline },
  { label: '选题', key: '/topics',     icon: TrendingUpOutline },
  { label: '博主', key: '/creators',   icon: PeopleOutline },
  { label: '资料', key: '/documents',  icon: DocumentTextOutline },
  { label: '风格', key: '/styles',     icon: ColorPaletteOutline },
  { label: '观点', key: '/viewpoints', icon: BulbOutline },
  { label: '日历', key: '/calendar',  icon: CalendarOutline },
  { label: '历史', key: '/history',    icon: TimeOutline },
]
</script>

<style>
/* ── CSS Variables ── */
:root {
  /* Brand: fresh teal-cyan system */
  --c-primary: #0891b2;                        /* cyan-600 */
  --c-primary-light: rgba(8,145,178,0.08);
  --c-primary-hover: #0e7490;                  /* cyan-700 */
  --c-accent: #22d3ee;                          /* cyan-400 */
  --c-accent-soft: #cffafe;                     /* cyan-100 */
  /* Text */
  --c-text-1: #0f172a;                          /* slate-900 */
  --c-text-2: #475569;                          /* slate-500 */
  --c-text-3: #94a3b8;                          /* slate-400 */
  --c-text-4: #cbd5e1;                          /* slate-300 */
  /* Surfaces */
  --c-border: #e0f2fe;                          /* sky-100 */
  --c-border-strong: #bae6fd;                   /* sky-200 */
  --c-bg-page: #f0f9ff;                         /* sky-50: fresh light tint */
  --c-bg-card: #ffffff;
  --c-bg-elevated: #ffffff;
  --c-bg-white: #ffffff;
  --c-bg-subtle: #f8fafc;                       /* slate-50 */
  /* Radius */
  --radius-sm: 8px;
  --radius-md: 10px;
  --radius-lg: 14px;
  --radius-xl: 18px;
  --radius-full: 9999px;
  /* Shadows — tinted with brand */
  --shadow-sm: 0 1px 3px rgba(8,145,178,0.06);
  --shadow-md: 0 4px 16px rgba(8,145,178,0.08);
  --shadow-lg: 0 8px 28px rgba(8,145,178,0.11);
  --shadow-card: 0 1px 4px rgba(8,145,178,0.07), 0 0 0 1px rgba(8,145,178,0.04);
  --ease: cubic-bezier(0.4,0,0.2,1);
}

*,*::before,*::after { box-sizing:border-box; margin:0; padding:0; }
html, body, #app { height:100%; overflow:hidden; }
body {
  font-family: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Segoe UI', Roboto, sans-serif;
  font-size: 14px;
  color: var(--c-text-1);
  background: var(--c-bg-page);
  -webkit-font-smoothing: antialiased;
}

/* ── Layout ── */
.layout {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

/* ── Sidebar ── */
.sidebar {
  width: 68px;
  background: #fff;
  border-right: 1px solid var(--c-border);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 14px 0;
  flex-shrink: 0;
  height: 100%;
  overflow: hidden;
  user-select: none;
}

.sidebar-logo {
  width: 32px;
  height: 32px;
  margin-bottom: 18px;
  cursor: pointer;
  transition: transform 0.2s var(--ease);
}
.sidebar-logo:hover { transform: scale(1.08); }
.sidebar-logo svg { width: 100%; height: 100%; }

.sidebar-nav {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0;
  width: 100%;
}

.nav-item {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  padding: 10px 0;
  cursor: pointer;
  font-size: 11px;
  color: var(--c-text-3);
  gap: 4px;
  transition: color 0.18s var(--ease);
  text-decoration: none;
  border-left: 2px solid transparent;
}
.nav-item:hover {
  color: var(--c-primary);
  background: var(--c-primary-light);
}
.nav-item.active {
  color: var(--c-primary);
  background: var(--c-primary-light);
  border-left-color: var(--c-primary);
}

.nav-icon {
  font-size: 18px;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-label {
  font-size: 11px;
  line-height: 1;
  white-space: nowrap;
}

.sidebar-bottom {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0;
  width: 100%;
}

.sidebar-user {
  margin-top: 8px;
  cursor: pointer;
  transition: opacity 0.2s;
}
.sidebar-user:hover { opacity: 0.7; }

/* ── Main Content ── */
.main-content {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  overflow-x: hidden;
  background: var(--c-bg-page);
  padding: 20px 28px;
}

/* ── Reusable page classes ── */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}
.page-title {
  font-size: 22px;
  font-weight: 600;
  color: var(--c-text-1);
}
.page-subtitle {
  font-size: 13px;
  color: var(--c-text-3);
  margin-top: 4px;
}

.card {
  background: var(--c-bg-card);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-card);
  transition: box-shadow 0.2s var(--ease), border-color 0.2s;
}
.card:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--c-border-strong);
}

.search-card {
  background: var(--c-bg-card);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-lg);
  padding: 20px 24px;
  margin-bottom: 20px;
  box-shadow: var(--shadow-card);
}

.empty-state-big {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 80px 0;
  color: var(--c-text-4);
}

/* ── Scrollbar ── */
.main-content::-webkit-scrollbar { width: 6px; }
.main-content::-webkit-scrollbar-track { background: transparent; }
.main-content::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.12); border-radius: 3px; }
.main-content::-webkit-scrollbar-thumb:hover { background: rgba(0,0,0,0.2); }

/* ── Mobile ── */
@media (max-width: 768px) {
  .layout {
    display: block;
  }
  .sidebar {
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    width: 100%;
    height: 60px;
    border-right: 0;
    border-top: 1px solid var(--c-border);
    flex-direction: row;
    align-items: stretch;
    padding: 0;
    z-index: 120;
    background: rgba(255,255,255,0.98);
    backdrop-filter: blur(8px);
  }
  .sidebar-logo,
  .sidebar-bottom {
    display: none;
  }
  .sidebar-nav {
    width: 100%;
    flex-direction: row;
    align-items: stretch;
    justify-content: space-between;
    overflow-x: auto;
    gap: 0;
  }
  .nav-item {
    min-width: 52px;
    padding: 6px 0;
    border-left: 0;
    border-top: 2px solid transparent;
    flex: 1;
  }
  .nav-item.active {
    border-left-color: transparent;
    border-top-color: var(--c-primary);
  }
  .nav-label {
    display: none;
  }
  .main-content {
    padding: 14px;
    padding-bottom: 78px;
  }
  .page-title {
    font-size: 18px;
  }
}
</style>
