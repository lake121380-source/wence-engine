<template>
  <n-config-provider :theme-overrides="themeOverrides" :locale="zhCN" :date-locale="dateZhCN">
    <n-message-provider>
      <n-dialog-provider>
      <router-view v-if="isPublicRoute" />

      <div v-else class="app-shell">
        <!-- 侧边栏 -->
        <aside class="sidebar" :class="{ collapsed }">
          <div class="logo-area">
            <div class="logo" @click="router.push('/')">
              <div class="logo-icon-wrapper">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/></svg>
              </div>
              <span v-if="!collapsed" class="logo-text">文策引擎</span>
            </div>
          </div>

          <nav class="nav-list">
            <div
              v-for="item in menuOptions"
              :key="item.key"
              class="nav-item"
              :class="{ active: activeKey === item.key }"
              @click="router.push(item.key)"
              role="button"
              tabindex="0"
              @keyup.enter="router.push(item.key)"
            >
              <n-icon size="18" class="nav-icon">
                <component :is="item.icon" />
              </n-icon>
              <span v-if="!collapsed" class="nav-label">{{ item.label }}</span>
            </div>
          </nav>

          <!-- 底部用户信息 -->
          <div class="sidebar-user" v-if="authStore.user">
            <n-avatar
              :src="authStore.user.avatar || defaultAvatar"
              round
              :size="32"
              :style="{ flexShrink: 0 }"
            />
            <div v-if="!collapsed" class="sidebar-user-info">
              <div class="sidebar-user-name">{{ authStore.user.nickname || '用户' }}</div>
              <n-tag
                v-if="!authStore.isSubscriptionActive || authStore.isTrial"
                :type="authStore.planType"
                size="tiny"
                :bordered="false"
                style="height:18px;font-size:11px;"
              >{{ authStore.planLabel }}</n-tag>
              <n-tag
                v-else
                type="success"
                size="tiny"
                :bordered="false"
                style="height:18px;font-size:11px;"
              >会员</n-tag>
            </div>
            <n-tooltip v-if="!collapsed" trigger="hover" placement="top">
              <template #trigger>
                <button class="logout-btn" @click="handleLogout" aria-label="退出登录">
                  <n-icon size="16"><LogOutOutline /></n-icon>
                </button>
              </template>
              退出登录
            </n-tooltip>
          </div>

          <button class="collapse-btn" @click="collapsed = !collapsed" :aria-label="collapsed ? '展开侧边栏' : '收起侧边栏'">
            <n-icon size="16">
              <component :is="collapsed ? ChevronForwardOutline : ChevronBackOutline" />
            </n-icon>
          </button>
        </aside>

        <!-- 右侧主区 -->
        <div class="main-area">
          <!-- 顶部栏 -->
          <header class="topbar">
            <h1 class="page-name">{{ currentPageName }}</h1>
            <div class="topbar-right">
              <!-- 订阅到期提醒 -->
              <n-tag
                v-if="authStore.isAuthenticated && authStore.isSubscriptionActive && authStore.daysUntilExpiry <= 3"
                type="warning"
                size="small"
                :bordered="false"
                class="clickable-tag"
                @click="$router.push('/pricing')"
              >
                {{ authStore.isTrial ? '体验期' : '订阅' }}还剩 {{ authStore.daysUntilExpiry < 1 ? authStore.hoursUntilExpiry + ' 小时' : authStore.daysUntilExpiry + ' 天' }}到期
              </n-tag>
              <n-tag
                v-if="authStore.isAuthenticated && !authStore.isSubscriptionActive"
                type="error"
                size="small"
                :bordered="false"
                class="clickable-tag"
                @click="$router.push('/pricing')"
              >
                订阅已到期 · 点击续费
              </n-tag>
              <n-avatar
                :src="authStore.user?.avatar"
                round
                size="small"
              >
                <template #icon><n-icon><PersonOutline /></n-icon></template>
              </n-avatar>
            </div>
          </header>

          <!-- 内容区 -->
          <main class="content">
            <!-- 全局背景装饰 -->
            <svg class="bg-deco" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">
              <defs>
                <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">
                  <path d="M 32 0 L 0 0 0 32" fill="none" stroke="rgba(37,99,235,0.045)" stroke-width="1"/>
                </pattern>
                <radialGradient id="glow1" cx="80%" cy="10%" r="45%">
                  <stop offset="0%" stop-color="rgba(37,99,235,0.07)"/>
                  <stop offset="100%" stop-color="rgba(37,99,235,0)"/>
                </radialGradient>
                <radialGradient id="glow2" cx="10%" cy="90%" r="35%">
                  <stop offset="0%" stop-color="rgba(14,165,233,0.055)"/>
                  <stop offset="100%" stop-color="rgba(14,165,233,0)"/>
                </radialGradient>
              </defs>
              <rect width="100%" height="100%" fill="url(#grid)"/>
              <rect width="100%" height="100%" fill="url(#glow1)"/>
              <rect width="100%" height="100%" fill="url(#glow2)"/>
            </svg>
            <div class="content-inner">
              <router-view v-slot="{ Component }">
                <keep-alive :max="10">
                  <component :is="Component" />
                </keep-alive>
              </router-view>
            </div>
          </main>
        </div>
      </div>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { zhCN, dateZhCN, NIcon } from 'naive-ui'
import {
  PeopleOutline, DocumentTextOutline,
  ColorPaletteOutline, SparklesOutline, TimeOutline,
  PersonOutline, TrendingUpOutline, BulbOutline,
  ChevronBackOutline, ChevronForwardOutline, LogOutOutline,
  CardOutline, SettingsOutline,
} from '@vicons/ionicons5'
import { useAuthStore } from './stores/auth.js'
import { authApi } from './api/index.js'

// 默认头像：灼见AI logo 风格的 SVG
const defaultAvatar = `data:image/svg+xml;base64,${btoa('<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32"><rect width="32" height="32" rx="16" fill="#e31c1c"/><text x="16" y="21" text-anchor="middle" font-family="Arial,sans-serif" font-size="16" font-weight="bold" fill="white">Z</text></svg>')}`

const router = useRouter()
const route = useRoute()

const isPublicRoute = computed(() => !!route.meta.public)
const collapsed = ref(false)
const authStore = useAuthStore()

onMounted(async () => {
  if (!authStore.isAuthenticated) return
  try {
    const { data } = await authApi.me()
    authStore.setUser(data)
  } catch {
    // 401 会被拦截器处理为跳转登录，这里不再重复提示
  }
})

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

const themeOverrides = {
  common: {
    primaryColor: '#2563EB',
    primaryColorHover: '#3B82F6',
    primaryColorPressed: '#1D4ED8',
    primaryColorSuppl: '#2563EB',
    infoColor: '#0ea5e9',
    successColor: '#16a34a',
    warningColor: '#ea580c',
    errorColor: '#dc2626',
    borderRadius: '8px',
    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  },
  DataTable: {
    thColor: '#f9fafb',
    tdColor: '#ffffff',
  },
  Button: {
    borderRadiusMedium: '8px',
    borderRadiusSmall: '6px',
  },
  Card: {
    borderRadius: '12px',
  },
}

const activeKey = computed(() => route.path)

const pageNames = {
  '/': '生成文案',
  '/creators': '博主资料库',
  '/documents': '产品资料',
  '/styles': '风格模版',
  '/topics': '爆款选题库',
  '/generate': '生成文案',
  '/history': '对话历史',
  '/viewpoints': '我的观点',
  '/pricing': '套餐与订阅',
  '/settings': '企业设置',
}

const currentPageName = computed(() => pageNames[route.path] || '文策引擎')

const menuOptions = [
  { label: '生成文案',  key: '/',            icon: SparklesOutline },
  { label: '博主资料库', key: '/creators',    icon: PeopleOutline },
  { label: '产品资料',  key: '/documents',   icon: DocumentTextOutline },
  { label: '风格模版',  key: '/styles',      icon: ColorPaletteOutline },
  { label: '爆款选题库', key: '/topics',     icon: TrendingUpOutline },
  { label: '我的观点',  key: '/viewpoints',  icon: BulbOutline },
  { label: '对话历史',  key: '/history',     icon: TimeOutline },
  { label: '套餐订阅',  key: '/pricing',     icon: CardOutline },
  { label: '企业设置',  key: '/settings',    icon: SettingsOutline },
]
</script>

<style>
/* ══════════════════════════════════════════════
   Design Tokens — 全局色彩与间距系统
   ══════════════════════════════════════════════ */
:root {
  /* 主色调 — Blue 600 */
  --c-primary: #2563EB;
  --c-primary-hover: #3B82F6;
  --c-primary-pressed: #1D4ED8;
  --c-primary-bg: rgba(37, 99, 235, 0.06);
  --c-primary-bg-hover: rgba(37, 99, 235, 0.10);
  --c-primary-shadow: rgba(37, 99, 235, 0.20);

  /* 语义色 */
  --c-success: #16a34a;
  --c-warning: #ea580c;
  --c-error: #dc2626;
  --c-info: #0ea5e9;

  /* 中性色 */
  --c-text-1: #111827;
  --c-text-2: #374151;
  --c-text-3: #6b7280;
  --c-text-4: #9ca3af;
  --c-text-5: #d1d5db;
  --c-border: rgba(0, 0, 0, 0.08);
  --c-border-hover: rgba(0, 0, 0, 0.14);
  --c-bg-page: #f9fafb;
  --c-bg-elevated: #ffffff;
  --c-bg-glass: rgba(255, 255, 255, 0.92);

  /* 间距 */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 12px;
  --space-lg: 16px;
  --space-xl: 24px;
  --space-2xl: 32px;
  --space-3xl: 48px;

  /* 圆角 */
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;

  /* 阴影 */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 2px 8px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.10), 0 2px 6px rgba(0, 0, 0, 0.04);
  --shadow-primary: 0 4px 14px var(--c-primary-shadow);

  /* 过渡 */
  --ease-default: cubic-bezier(0.4, 0, 0.2, 1);
  --duration-fast: 150ms;
  --duration-normal: 200ms;
}

*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html, body, #app {
  height: 100%;
  overflow: hidden;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  color: var(--c-text-1);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background: var(--c-bg-page);
}

.app-shell {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

/* ── 侧边栏 ── */
.sidebar {
  width: 220px;
  flex-shrink: 0;
  background: #eef1f8;
  border-right: 1px solid rgba(37,99,235,0.08);
  display: flex;
  flex-direction: column;
  transition: width var(--duration-normal) var(--ease-default);
  overflow: hidden;
  z-index: 10;
}
.sidebar.collapsed { width: 64px; }

.logo-area {
  padding: var(--space-md) var(--space-md) var(--space-md);
  border-bottom: 1px solid rgba(37,99,235,0.08);
  flex-shrink: 0;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: var(--space-sm) 10px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--duration-fast) var(--ease-default);
  white-space: nowrap;
}
.logo:hover { background: rgba(255,255,255,0.6); }

.logo-icon-wrapper {
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  background: linear-gradient(135deg, var(--c-primary), #6366f1);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(37,99,235,0.35), 0 1px 3px rgba(37,99,235,0.2);
  position: relative;
  overflow: hidden;
}
.logo-icon-wrapper::after {
  content: '';
  position: absolute;
  top: -6px; left: -6px;
  width: 20px; height: 20px;
  background: rgba(255,255,255,0.2);
  border-radius: 50%;
  filter: blur(6px);
}

.logo-text {
  font-size: 14px;
  font-weight: 700;
  color: #1e2d4d;
  letter-spacing: -0.3px;
}

.nav-list {
  flex: 1;
  padding: var(--space-sm);
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow-y: auto;
  overflow-x: hidden;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px var(--space-md);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--duration-fast) var(--ease-default), color var(--duration-fast), box-shadow var(--duration-fast);
  white-space: nowrap;
  color: #4b5c7a;
  font-size: 13.5px;
  font-weight: 500;
  outline: none;
}
.nav-item:hover {
  background: rgba(255,255,255,0.7);
  color: var(--c-text-1);
  box-shadow: 0 1px 3px rgba(37,99,235,0.06);
}
.nav-item:focus-visible { box-shadow: 0 0 0 2px var(--c-primary); }
.nav-item.active {
  background: #ffffff;
  color: var(--c-primary);
  box-shadow: 0 1px 4px rgba(37,99,235,0.12), 0 1px 2px rgba(0,0,0,0.04);
  font-weight: 600;
}
.nav-icon { color: #8da0bf; flex-shrink: 0; transition: color var(--duration-fast); }
.nav-item:hover .nav-icon,
.nav-item.active .nav-icon { color: var(--c-primary); }

.sidebar-user {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: 10px var(--space-md);
  border-top: 1px solid rgba(37,99,235,0.08);
  flex-shrink: 0;
}

.sidebar-user-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.sidebar-user-name {
  font-size: 13px;
  font-weight: 600;
  color: #2d3e5a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.logout-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  border-radius: var(--radius-sm);
  cursor: pointer;
  color: var(--c-text-4);
  flex-shrink: 0;
  transition: all var(--duration-fast) var(--ease-default);
}
.logout-btn:hover { color: var(--c-error); background: rgba(239, 68, 68, 0.08); }
.logout-btn:focus-visible { box-shadow: 0 0 0 2px var(--c-error); }

.collapse-btn {
  padding: var(--space-md);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #8da0bf;
  border: none;
  background: transparent;
  border-top: 1px solid rgba(37,99,235,0.08);
  flex-shrink: 0;
  transition: color var(--duration-fast), background var(--duration-fast);
}
.collapse-btn:hover { color: var(--c-primary); background: rgba(255,255,255,0.6); }
.collapse-btn:focus-visible { box-shadow: inset 0 0 0 2px var(--c-primary); }

/* ── 右侧主区 ── */
.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
  background: var(--c-bg-page);
}

.topbar {
  height: 56px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-xl);
  background: var(--c-bg-glass);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--c-border);
  position: relative;
}
.topbar::after {
  content: '';
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(37,99,235,0.15) 30%, rgba(99,102,241,0.15) 70%, transparent);
}

.page-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--c-text-1);
  letter-spacing: -0.2px;
}

.topbar-right { display: flex; align-items: center; gap: var(--space-md); }

.clickable-tag { cursor: pointer; transition: opacity var(--duration-fast); }
.clickable-tag:hover { opacity: 0.85; }

.content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  position: relative;
}

.bg-deco {
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 100%;
  pointer-events: none;
  z-index: 0;
}

.content-inner {
  padding: var(--space-xl);
  max-width: 1440px;
  margin: 0 auto;
  position: relative;
  z-index: 1;
}

/* ── 全局通用类 ── */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-xl);
  padding-bottom: var(--space-xl);
  border-bottom: 1px solid var(--c-border);
  position: relative;
}
.page-header::before {
  content: '';
  position: absolute;
  bottom: -1px; left: 0;
  width: 64px; height: 2px;
  background: linear-gradient(90deg, var(--c-primary), rgba(37,99,235,0));
  border-radius: 2px;
}

.page-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--c-text-1);
  margin: 0;
  letter-spacing: -0.3px;
}

.page-subtitle {
  font-size: 13px;
  color: var(--c-text-4);
  margin-top: var(--space-xs);
}

.card {
  background: var(--c-bg-elevated);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-sm);
  transition: box-shadow var(--duration-normal) var(--ease-default), border-color var(--duration-normal);
}
.card:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--c-border-hover);
}

.empty-state-big {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-md);
  padding: 80px 0;
  color: var(--c-text-5);
}

::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(0, 0, 0, 0.1); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(0, 0, 0, 0.18); }

@media (max-width: 768px) {
  .page-title { font-size: 18px; }
  .content-inner { padding: var(--space-lg); }
  .sidebar { display: none; }
  .topbar { padding: 0 var(--space-lg); }
}
</style>
