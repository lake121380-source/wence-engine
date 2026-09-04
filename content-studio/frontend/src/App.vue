<template>
  <n-config-provider :theme-overrides="themeOverrides" :locale="zhCN" :date-locale="dateZhCN">
    <n-message-provider>
      <n-dialog-provider>
        <div v-if="isPublicRoute" class="public-view-wrapper">
          <router-view />
        </div>

        <div v-else class="app-shell">
          <!-- 桌面端侧边栏 -->
          <aside class="sidebar" :class="{ collapsed }">
            <!-- 品牌与工作台 Logo 区域 -->
            <div class="logo-area">
              <div class="logo" @click="router.push('/')" title="点击返回官网首页">
                <div class="logo-icon-wrapper">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <polygon points="23 7 16 12 23 17 23 7"/>
                    <rect x="1" y="5" width="15" height="14" rx="2" ry="2"/>
                  </svg>
                </div>
                <div v-if="!collapsed" class="logo-brand-info">
                  <span class="logo-text">文策引擎</span>
                  <span class="workspace-pill">创作者工作空间</span>
                </div>
              </div>
            </div>

            <!-- 分组导航菜单栏 -->
            <nav class="nav-list">
              <template v-for="group in menuGroups" :key="group.title">
                <div v-if="!collapsed" class="nav-group-title">{{ group.title }}</div>
                <div v-else class="nav-group-divider"></div>

                <template v-for="item in group.items" :key="item.key">
                  <n-tooltip v-if="collapsed" placement="right" trigger="hover">
                    <template #trigger>
                      <div
                        class="nav-item"
                        :class="{ active: activeKey === item.key }"
                        @click="router.push(item.key)"
                        role="button"
                        tabindex="0"
                      >
                        <n-icon size="18" class="nav-icon">
                          <component :is="item.icon" />
                        </n-icon>
                      </div>
                    </template>
                    {{ item.label }}
                  </n-tooltip>

                  <div
                    v-else
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
                    <span class="nav-label">{{ item.label }}</span>
                    <span v-if="item.badge" class="nav-badge" :class="item.badgeClass || 'badge-default'">
                      {{ item.badge }}
                    </span>
                  </div>
                </template>
              </template>
            </nav>

            <!-- 侧边栏底部用户信息与状态卡片 -->
            <div class="sidebar-user-section" v-if="authStore.user">
              <div class="sidebar-user-inner" @click="router.push('/settings')" title="点击查看个人设置">
                <n-avatar
                  :src="authStore.user.avatar || defaultAvatar"
                  round
                  :size="34"
                  class="user-avatar-chip"
                />
                <div v-if="!collapsed" class="sidebar-user-details">
                  <div class="sidebar-user-row">
                    <span class="sidebar-user-name">{{ authStore.user.nickname || '创作者' }}</span>
                    <n-tag
                      :type="authStore.planType"
                      size="tiny"
                      :bordered="false"
                      class="plan-mini-tag"
                    >
                      {{ authStore.planLabel }}
                    </n-tag>
                  </div>
                  <div class="sidebar-user-sub">
                    <span v-if="authStore.isSubscriptionActive">
                      剩 {{ authStore.daysUntilExpiry < 1 ? authStore.hoursUntilExpiry + '小时' : authStore.daysUntilExpiry + '天' }}
                    </span>
                    <span v-else class="expired-sub">已到期</span>
                  </div>
                </div>
              </div>

              <!-- 折叠与展开触发按钮 -->
              <div class="sidebar-bottom-actions">
                <n-tooltip trigger="hover" placement="top">
                  <template #trigger>
                    <button
                      class="collapse-btn"
                      @click="collapsed = !collapsed"
                      :aria-label="collapsed ? '展开侧边栏' : '收起侧边栏'"
                    >
                      <n-icon size="16">
                        <component :is="collapsed ? ChevronForwardOutline : ChevronBackOutline" />
                      </n-icon>
                      <span v-if="!collapsed" class="collapse-btn-text">收起侧栏</span>
                    </button>
                  </template>
                  {{ collapsed ? '展开侧边栏' : '收起侧边栏' }}
                </n-tooltip>

                <n-tooltip v-if="!collapsed" trigger="hover" placement="top">
                  <template #trigger>
                    <button class="logout-icon-btn" @click="handleLogout" aria-label="退出登录">
                      <n-icon size="16"><LogOutOutline /></n-icon>
                    </button>
                  </template>
                  退出登录
                </n-tooltip>
              </div>
            </div>
          </aside>

          <!-- 右侧主区 -->
          <div class="main-area">
            <!-- 现代高阶顶部栏 (Topbar) -->
            <header class="topbar">
              <div class="topbar-left">
                <!-- 移动端汉堡菜单触发按钮 (只有在小于 768px 显示) -->
                <button
                  class="mobile-menu-trigger"
                  @click="mobileDrawerOpen = true"
                  aria-label="打开导航菜单"
                >
                  <n-icon size="20"><MenuOutline /></n-icon>
                </button>

                <!-- 层次分明的面包屑导航 -->
                <div class="breadcrumbs-area">
                  <span class="bc-root">文策工作台</span>
                  <span class="bc-sep">/</span>
                  <span class="bc-group">{{ currentPageGroup }}</span>
                  <span class="bc-sep">/</span>
                  <span class="bc-current">{{ currentPageName }}</span>
                </div>
              </div>

              <!-- 中间全局快捷搜索胶囊 -->
              <div class="topbar-center">
                <button class="command-search-bar" @click="commandPaletteVisible = true">
                  <n-icon size="15" class="search-bar-icon"><SearchOutline /></n-icon>
                  <span class="search-bar-placeholder">快速搜索功能或直达...</span>
                  <span class="search-bar-kbd">⌘K</span>
                </button>
              </div>

              <!-- 右侧快捷功能与用户卡片 -->
              <div class="topbar-right">
                <!-- 引擎算力健康度指示 -->
                <div class="engine-status-tag" title="Gemini & DeepSeek 双核调度引擎实时在线">
                  <span class="status-pulse-dot"></span>
                  <span class="status-text">旗舰双核引擎在线</span>
                </div>

                <!-- 快速新建生成按钮 -->
                <n-button
                  type="primary"
                  size="small"
                  @click="quickNewGeneration"
                  class="quick-action-btn"
                >
                  <template #icon><n-icon><AddOutline /></n-icon></template>
                  新建生成
                </n-button>

                <!-- 官网跳转按钮 -->
                <n-button
                  size="small"
                  quaternary
                  @click="router.push('/')"
                  class="back-home-btn"
                >
                  <template #icon><n-icon><HomeOutline /></n-icon></template>
                  官网
                </n-button>

                <!-- 到期紧迫提示 -->
                <n-tag
                  v-if="authStore.isAuthenticated && authStore.isSubscriptionActive && authStore.daysUntilExpiry <= 3"
                  type="warning"
                  size="small"
                  :bordered="false"
                  class="clickable-tag"
                  @click="$router.push('/pricing')"
                >
                  剩余 {{ authStore.daysUntilExpiry < 1 ? authStore.hoursUntilExpiry + '小时' : authStore.daysUntilExpiry + '天' }}
                </n-tag>

                <!-- 用户头像下拉功能菜单 (Dropdown) -->
                <n-dropdown
                  :options="userDropdownOptions"
                  @select="handleDropdownSelect"
                  trigger="click"
                  placement="bottom-end"
                >
                  <div class="topbar-avatar-badge" role="button" tabindex="0">
                    <n-avatar
                      :src="authStore.user?.avatar || defaultAvatar"
                      round
                      :size="30"
                      class="top-user-avatar"
                    />
                    <span class="top-username">{{ authStore.user?.nickname || '创作者' }}</span>
                    <n-icon size="12" class="top-chevron"><ChevronDownOutline /></n-icon>
                  </div>
                </n-dropdown>
              </div>
            </header>

            <!-- 主内容区域 -->
            <main class="content">
              <!-- 背景装饰光影微光 -->
              <svg class="bg-deco" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">
                <defs>
                  <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">
                    <path d="M 32 0 L 0 0 0 32" fill="none" stroke="rgba(37,99,235,0.03)" stroke-width="1"/>
                  </pattern>
                  <radialGradient id="glow1" cx="80%" cy="10%" r="45%">
                    <stop offset="0%" stop-color="rgba(37,99,235,0.05)"/>
                    <stop offset="100%" stop-color="rgba(37,99,235,0)"/>
                  </radialGradient>
                </defs>
                <rect width="100%" height="100%" fill="url(#grid)"/>
                <rect width="100%" height="100%" fill="url(#glow1)"/>
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

          <!-- 移动端导航抽屉 (Mobile Drawer) -->
          <n-drawer v-model:show="mobileDrawerOpen" :width="280" placement="left">
            <n-drawer-content closable title="文策引擎导航">
              <div class="mobile-drawer-body">
                <div class="mobile-user-card" @click="handleMobileNavigate('/settings')">
                  <n-avatar :src="authStore.user?.avatar || defaultAvatar" round :size="40" />
                  <div class="mobile-user-info">
                    <div class="mobile-user-name">{{ authStore.user?.nickname || '创作者' }}</div>
                    <div class="mobile-user-sub">{{ authStore.planLabel }} · 有效期内</div>
                  </div>
                </div>

                <div class="mobile-nav-groups">
                  <div v-for="group in menuGroups" :key="group.title" class="mobile-group">
                    <div class="mobile-group-title">{{ group.title }}</div>
                    <div
                      v-for="item in group.items"
                      :key="item.key"
                      class="mobile-nav-item"
                      :class="{ active: activeKey === item.key }"
                      @click="handleMobileNavigate(item.key)"
                    >
                      <n-icon size="18" class="mobile-item-icon"><component :is="item.icon" /></n-icon>
                      <span class="mobile-item-label">{{ item.label }}</span>
                      <span v-if="item.badge" class="nav-badge" :class="item.badgeClass || 'badge-default'">
                        {{ item.badge }}
                      </span>
                    </div>
                  </div>
                </div>

                <div class="mobile-drawer-footer">
                  <n-button block secondary @click="handleMobileNavigate('/')">
                    <template #icon><n-icon><HomeOutline /></n-icon></template>
                    返回官网首页
                  </n-button>
                  <n-button block type="error" ghost @click="handleLogout" style="margin-top:8px;">
                    退出登录
                  </n-button>
                </div>
              </div>
            </n-drawer-content>
          </n-drawer>

          <!-- 全局快捷命令面板 (Command Palette Modal, ⌘K 唤起) -->
          <n-modal
            v-model:show="commandPaletteVisible"
            preset="card"
            style="width: 580px; max-width: 92vw; border-radius: 16px; overflow: hidden;"
            :closable="false"
            :bordered="false"
          >
            <div class="cmd-palette-wrapper">
              <div class="cmd-search-input-box">
                <n-icon size="18" class="cmd-input-icon"><SearchOutline /></n-icon>
                <input
                  ref="cmdInputRef"
                  v-model="cmdSearchQuery"
                  type="text"
                  placeholder="搜索功能模块、操作快捷指令... (Esc 关闭)"
                  class="cmd-real-input"
                  @keydown.down.prevent="moveCmdSelection(1)"
                  @keydown.up.prevent="moveCmdSelection(-1)"
                  @keydown.enter.prevent="executeCmdSelected"
                />
                <span class="cmd-esc-tip">ESC</span>
              </div>

              <div class="cmd-results-list">
                <div
                  v-for="(item, idx) in filteredCmdItems"
                  :key="item.key"
                  class="cmd-result-item"
                  :class="{ selected: selectedCmdIdx === idx }"
                  @mouseenter="selectedCmdIdx = idx"
                  @click="jumpCmd(item)"
                >
                  <div class="cmd-item-icon-box">
                    <n-icon size="18"><component :is="item.icon" /></n-icon>
                  </div>
                  <div class="cmd-item-content">
                    <div class="cmd-item-label">{{ item.label }}</div>
                    <div class="cmd-item-desc">{{ item.desc }}</div>
                  </div>
                  <span class="cmd-item-group">{{ item.group }}</span>
                </div>

                <div v-if="filteredCmdItems.length === 0" class="cmd-empty">
                  未匹配到相关功能，请尝试搜索“生成”、“选题”、“博主”、“设置”等
                </div>
              </div>

              <div class="cmd-footer-tips">
                <span><kbd>↑</kbd> <kbd>↓</kbd> 切换导航</span>
                <span><kbd>↵</kbd> 回车跳转</span>
                <span><kbd>ESC</kbd> 关闭面板</span>
              </div>
            </div>
          </n-modal>

        </div>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, h } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { zhCN, dateZhCN, NIcon } from 'naive-ui'
import {
  PeopleOutline, DocumentTextOutline,
  ColorPaletteOutline, SparklesOutline, TimeOutline,
  PersonOutline, TrendingUpOutline, BulbOutline,
  ChevronBackOutline, ChevronForwardOutline, LogOutOutline,
  CardOutline, SettingsOutline, HomeOutline,
  MenuOutline, SearchOutline, AddOutline, ChevronDownOutline
} from '@vicons/ionicons5'
import { useAuthStore } from './stores/auth.js'
import { authApi } from './api/index.js'

const defaultAvatar = `data:image/svg+xml;charset=utf-8,${encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32"><rect width="32" height="32" rx="16" fill="#2563EB"/><text x="16" y="21" text-anchor="middle" font-family="Arial,sans-serif" font-size="16" font-weight="bold" fill="white">文</text></svg>')}`

const router = useRouter()
const route = useRoute()

const isPublicRoute = computed(() => !!route.meta.public)
const collapsed = ref(false)
const mobileDrawerOpen = ref(false)
const commandPaletteVisible = ref(false)
const cmdSearchQuery = ref('')
const selectedCmdIdx = ref(0)
const cmdInputRef = ref(null)

const authStore = useAuthStore()

onMounted(async () => {
  if (!authStore.isAuthenticated) return
  try {
    const { data } = await authApi.me()
    authStore.setUser(data)
  } catch {}
  
  window.addEventListener('keydown', handleGlobalKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalKeydown)
})

function handleGlobalKeydown(e) {
  // ⌘K 或 Ctrl+K 触发命令面板
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault()
    commandPaletteVisible.value = !commandPaletteVisible.value
    if (commandPaletteVisible.value) {
      cmdSearchQuery.value = ''
      selectedCmdIdx.value = 0
      nextTick(() => {
        cmdInputRef.value?.focus()
      })
    }
  }
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

function quickNewGeneration() {
  if (route.path === '/generate') {
    // 若已在页面，派发局部新会话事件或提示
    window.dispatchEvent(new CustomEvent('wence-new-session'))
  } else {
    router.push('/generate')
  }
}

function handleMobileNavigate(path) {
  mobileDrawerOpen.value = false
  router.push(path)
}

const themeOverrides = {
  common: {
    primaryColor: '#1d4ed8',
    primaryColorHover: '#2563eb',
    primaryColorPressed: '#1e40af',
    primaryColorSuppl: '#1d4ed8',
    infoColor: '#0284c7',
    successColor: '#15803d',
    warningColor: '#c2410c',
    errorColor: '#b91c1c',
    borderRadius: '8px',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif',
  },
  DataTable: {
    thColor: '#f8f9fa',
    tdColor: '#ffffff',
  },
  Button: {
    borderRadiusMedium: '8px',
    borderRadiusSmall: '6px',
    fontWeight: '500',
  },
  Card: {
    borderRadius: '12px',
    borderColor: 'rgba(17, 24, 39, 0.07)',
  },
}

const activeKey = computed(() => route.path)

const pageNames = {
  '/': '文策引擎首页',
  '/generate': '生成文案',
  '/creators': '博主资料库',
  '/documents': '产品知识库',
  '/styles': '风格模版库',
  '/topics': '爆款选题库',
  '/history': '对话生成历史',
  '/viewpoints': '我的观点库',
  '/pricing': '套餐与权益',
  '/settings': '个人与设置',
}

const pageGroups = {
  '/generate': '创作中枢',
  '/topics': '创作中枢',
  '/history': '创作中枢',
  '/creators': '内容资产',
  '/documents': '内容资产',
  '/styles': '内容资产',
  '/viewpoints': '内容资产',
  '/pricing': '空间与账户',
  '/settings': '空间与账户',
}

const currentPageName = computed(() => pageNames[route.path] || '工作台')
const currentPageGroup = computed(() => pageGroups[route.path] || '文策工坊')

// 分组导航结构
const menuGroups = [
  {
    title: '创作工坊',
    items: [
      { label: '生成文案', key: '/generate', icon: SparklesOutline, badge: 'AI', badgeClass: 'badge-ai' },
      { label: '爆款选题库', key: '/topics', icon: TrendingUpOutline, badge: 'HOT', badgeClass: 'badge-hot' },
      { label: '对话生成历史', key: '/history', icon: TimeOutline },
    ]
  },
  {
    title: '知识与资产',
    items: [
      { label: '博主资料库', key: '/creators', icon: PeopleOutline },
      { label: '产品知识库', key: '/documents', icon: DocumentTextOutline },
      { label: '风格模版库', key: '/styles', icon: ColorPaletteOutline },
      { label: '我的观点库', key: '/viewpoints', icon: BulbOutline },
    ]
  },
  {
    title: '空间与管理',
    items: [
      { label: '套餐与权益', key: '/pricing', icon: CardOutline },
      { label: '个人与设置', key: '/settings', icon: SettingsOutline },
    ]
  }
]

// 下拉菜单选项
const userDropdownOptions = [
  {
    label: () => h('div', { style: 'padding: 4px 0;' }, [
      h('div', { style: 'font-weight: 700; font-size: 13.5px; color: #0f172a;' }, authStore.user?.nickname || '创作者'),
      h('div', { style: 'font-size: 11.5px; color: #64748b; margin-top: 2px;' }, authStore.user?.email || 'user@wence.ai')
    ]),
    key: 'header',
    disabled: true
  },
  { type: 'divider', key: 'd1' },
  { label: '个人中心与偏好', key: '/settings', icon: () => h(NIcon, null, { default: () => h(SettingsOutline) }) },
  { label: '套餐与权益中心', key: '/pricing', icon: () => h(NIcon, null, { default: () => h(CardOutline) }) },
  { label: '返回官网首页', key: 'home', icon: () => h(NIcon, null, { default: () => h(HomeOutline) }) },
  { type: 'divider', key: 'd2' },
  { label: '退出登录', key: 'logout', icon: () => h(NIcon, { color: '#dc2626' }, { default: () => h(LogOutOutline) }) },
]

function handleDropdownSelect(key) {
  if (key === 'logout') {
    handleLogout()
  } else if (key === 'home') {
    router.push('/')
  } else {
    router.push(key)
  }
}

// 命令面板搜索项列表
const allCommandItems = [
  { key: '/generate', label: '生成文案', desc: '进入五维视听分镜生成工作台，支持 @ 引用素材', group: '创作', icon: SparklesOutline },
  { key: '/topics', label: '爆款选题库', desc: '公域高互动选题挖掘与爆款趋势', group: '创作', icon: TrendingUpOutline },
  { key: '/history', label: '对话生成历史', desc: '查看历史生成的脚本文案与对话记录', group: '创作', icon: TimeOutline },
  { key: '/creators', label: '博主资料库', desc: '管理行业对标博主与爆款视频拆解', group: '资产', icon: PeopleOutline },
  { key: '/documents', label: '产品知识库', desc: '上传说明书、白皮书，RAG 语义切片防幻觉', group: '资产', icon: DocumentTextOutline },
  { key: '/styles', label: '风格模版库', desc: '沉淀 IP 专属腔调与结构化模版', group: '资产', icon: ColorPaletteOutline },
  { key: '/viewpoints', label: '我的观点库', desc: '记录独特认知与金句表达库', group: '资产', icon: BulbOutline },
  { key: '/pricing', label: '套餐与权益', desc: '查看会员状态、无限次生成特权及充值续费', group: '账户', icon: CardOutline },
  { key: '/settings', label: '个人与设置', desc: '修改创作者名片、AI 输出习惯预设与登录密码', group: '账户', icon: SettingsOutline },
  { key: '/', label: '返回官网首页', desc: '查看产品功能介绍、演示与常见问题 FAQ', group: '导航', icon: HomeOutline },
]

const filteredCmdItems = computed(() => {
  const q = cmdSearchQuery.value.trim().toLowerCase()
  if (!q) return allCommandItems
  return allCommandItems.filter(item =>
    item.label.toLowerCase().includes(q) ||
    item.desc.toLowerCase().includes(q) ||
    item.group.toLowerCase().includes(q)
  )
})

function moveCmdSelection(step) {
  const total = filteredCmdItems.value.length
  if (total === 0) return
  selectedCmdIdx.value = (selectedCmdIdx.value + step + total) % total
}

function executeCmdSelected() {
  const item = filteredCmdItems.value[selectedCmdIdx.value]
  if (item) {
    jumpCmd(item)
  }
}

function jumpCmd(item) {
  commandPaletteVisible.value = false
  router.push(item.key)
}
</script>

<style>
/* ══════════════════════════════════════════════
   全局色彩、间距与圆角设计系统
   ══════════════════════════════════════════════ */
:root {
  --c-primary: #1d4ed8;
  --c-primary-hover: #2563eb;
  --c-primary-pressed: #1e40af;
  --c-primary-bg: rgba(29, 78, 216, 0.05);
  --c-primary-bg-hover: rgba(29, 78, 216, 0.09);
  --c-primary-shadow: rgba(29, 78, 216, 0.16);

  --c-success: #15803d;
  --c-warning: #c2410c;
  --c-error: #b91c1c;
  --c-info: #0284c7;

  --c-text-1: #111827;
  --c-text-2: #374151;
  --c-text-3: #6b7280;
  --c-text-4: #9ca3af;
  --c-text-5: #e5e7eb;

  --c-border: rgba(17, 24, 39, 0.07);
  --c-border-hover: rgba(17, 24, 39, 0.14);
  --c-bg-page: #f8f9fa;
  --c-bg-elevated: #ffffff;
  --c-bg-soft: #f3f4f6;
  --c-bg-glass: rgba(255, 255, 255, 0.88);

  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 12px;
  --space-lg: 16px;
  --space-xl: 24px;
  --space-2xl: 32px;

  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;

  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.03);
  --shadow-md: 0 4px 16px -2px rgba(0, 0, 0, 0.04), 0 2px 6px -1px rgba(0, 0, 0, 0.02);
  --shadow-lg: 0 12px 32px -4px rgba(0, 0, 0, 0.06);

  --ease-default: cubic-bezier(0.16, 1, 0.3, 1);
  --duration-fast: 160ms;
  --duration-normal: 240ms;
}

*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  color: var(--c-text-1);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
  font-variant-numeric: tabular-nums;
  background: var(--c-bg-page);
  min-height: 100vh;
  margin: 0;
  padding: 0;
  overflow-x: hidden;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.public-view-wrapper {
  width: 100%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-shell {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

/* ══════════════════════════════════════════════
   侧边栏 Sidebar (高阶分级架构)
   ══════════════════════════════════════════════ */
.sidebar {
  width: 236px;
  flex-shrink: 0;
  background: #ffffff;
  border-right: 1px solid var(--c-border);
  display: flex;
  flex-direction: column;
  transition: width var(--duration-normal) var(--ease-default);
  overflow: hidden;
  z-index: 20;
}

.sidebar.collapsed {
  width: 68px;
}

.logo-area {
  padding: 16px 14px;
  border-bottom: 1px solid var(--c-border);
  flex-shrink: 0;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 8px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--duration-fast) var(--ease-default);
}

.logo:hover {
  background: #f1f5f9;
}

.logo-icon-wrapper {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  background: linear-gradient(135deg, #1d4ed8 0%, #3b82f6 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(29, 78, 216, 0.25);
}

.logo-brand-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.logo-text {
  font-size: 15px;
  font-weight: 750;
  color: #0f172a;
  letter-spacing: -0.02em;
  white-space: nowrap;
}

.workspace-pill {
  font-size: 11px;
  color: #64748b;
  font-weight: 500;
  white-space: nowrap;
}

/* 导航分组与列表 */
.nav-list {
  flex: 1;
  padding: 12px 10px;
  display: flex;
  flex-direction: column;
  gap: 3px;
  overflow-y: auto;
  overflow-x: hidden;
}

.nav-group-title {
  font-size: 11px;
  font-weight: 700;
  color: #94a3b8;
  padding: 12px 10px 4px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.nav-group-divider {
  height: 1px;
  background: var(--c-border);
  margin: 8px 6px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8.5px 12px;
  border-radius: 9px;
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-default);
  white-space: nowrap;
  color: #475569;
  font-size: 13.5px;
  font-weight: 500;
  outline: none;
  position: relative;
}

.sidebar.collapsed .nav-item {
  padding: 10px;
  justify-content: center;
}

.nav-item:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.nav-item.active {
  background: var(--c-primary-bg, rgba(29, 78, 216, 0.05));
  color: var(--c-primary, #1d4ed8);
  font-weight: 600;
}

.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  bottom: 8px;
  width: 3px;
  background: var(--c-primary, #1d4ed8);
  border-radius: 0 3px 3px 0;
}

.sidebar.collapsed .nav-item.active::before {
  display: none;
}

.nav-icon {
  color: #64748b;
  flex-shrink: 0;
  transition: color var(--duration-fast);
}

.nav-item:hover .nav-icon,
.nav-item.active .nav-icon {
  color: #2563eb;
}

.nav-label {
  flex: 1;
}

.nav-badge {
  font-size: 10.5px;
  font-weight: 800;
  padding: 1px 6px;
  border-radius: 9999px;
  letter-spacing: 0.02em;
}

.badge-ai {
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  color: #1d4ed8;
  border: 1px solid #bfdbfe;
}

.badge-hot {
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  color: #dc2626;
  border: 1px solid #fecaca;
}

.badge-default {
  background: #f1f5f9;
  color: #64748b;
}

/* 侧边栏底部用户信息 */
.sidebar-user-section {
  padding: 12px 10px;
  border-top: 1px solid var(--c-border);
  background: #ffffff;
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex-shrink: 0;
}

.sidebar-user-inner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 8px;
  border-radius: 10px;
  cursor: pointer;
  transition: background var(--duration-fast);
}

.sidebar-user-inner:hover {
  background: #f8fafc;
}

.user-avatar-chip {
  flex-shrink: 0;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}

.sidebar-user-details {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.sidebar-user-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.sidebar-user-name {
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.plan-mini-tag {
  height: 17px;
  font-size: 10.5px;
  padding: 0 5px;
}

.sidebar-user-sub {
  font-size: 11.5px;
  color: #64748b;
}

.expired-sub {
  color: #dc2626;
}

.sidebar-bottom-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 2px 4px 0;
}

.collapse-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: transparent;
  border: none;
  color: #64748b;
  font-size: 12px;
  cursor: pointer;
  padding: 6px 8px;
  border-radius: 6px;
  transition: all var(--duration-fast);
}

.collapse-btn:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.logout-icon-btn {
  background: transparent;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  padding: 6px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--duration-fast);
}

.logout-icon-btn:hover {
  background: #fee2e2;
  color: #dc2626;
}

/* ══════════════════════════════════════════════
   顶部栏 (Topbar - 磨砂毛玻璃体验)
   ══════════════════════════════════════════════ */
.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
  background: var(--c-bg-page);
}

.topbar {
  height: 58px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: var(--c-bg-glass);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--c-border);
  z-index: 10;
  gap: 16px;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.mobile-menu-trigger {
  display: none;
  background: none;
  border: none;
  color: #334155;
  cursor: pointer;
  padding: 6px;
  border-radius: 6px;
}

.breadcrumbs-area {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13.5px;
  white-space: nowrap;
}

.bc-root {
  color: #64748b;
}

.bc-sep {
  color: #cbd5e1;
}

.bc-group {
  color: #475569;
}

.bc-current {
  color: #0f172a;
  font-weight: 700;
}

/* 中间命令搜索胶囊 */
.topbar-center {
  flex: 1;
  max-width: 380px;
  display: flex;
  justify-content: center;
}

.command-search-bar {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f1f5f9;
  border: 1px solid transparent;
  border-radius: 10px;
  padding: 6px 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
}

.command-search-bar:hover {
  background: #e2e8f0;
  border-color: #cbd5e1;
}

.search-bar-icon {
  color: #94a3b8;
}

.search-bar-placeholder {
  flex: 1;
  font-size: 12.5px;
  color: #64748b;
  text-align: left;
}

.search-bar-kbd {
  font-size: 11px;
  font-weight: 700;
  color: #475569;
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  padding: 1px 5px;
}

/* 右侧组件与用户徽标 */
.topbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.engine-status-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: #f8fafc;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 9999px;
  font-size: 11.5px;
  color: #475569;
}

.status-pulse-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
}

.topbar-avatar-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 3px 8px 3px 4px;
  border-radius: 9999px;
  border: 1px solid var(--c-border);
  background: #ffffff;
  cursor: pointer;
  transition: all 0.15s ease;
  user-select: none;
}

.topbar-avatar-badge:hover {
  border-color: #cbd5e1;
  background: #f8fafc;
}

.top-username {
  font-size: 13px;
  font-weight: 600;
  color: #0f172a;
  max-width: 90px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.top-chevron {
  color: #94a3b8;
}

/* ══════════════════════════════════════════════
   主工作区内容壳 (Content Inner)
   ══════════════════════════════════════════════ */
.content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  position: relative;
}

.bg-deco {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
}

.content-inner {
  padding: 24px;
  max-width: 1440px;
  margin: 0 auto;
  position: relative;
  z-index: 1;
}

/* ══════════════════════════════════════════════
   全局通用样式 (Cards, Headers)
   ══════════════════════════════════════════════ */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--c-border);
}

.page-title {
  font-size: 22px;
  font-weight: 750;
  color: var(--c-text-1, #111827);
  margin: 0;
  letter-spacing: -0.02em;
}

.page-subtitle {
  font-size: 13.5px;
  color: var(--c-text-3, #6b7280);
  margin-top: 4px;
}

.card {
  background: #ffffff;
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
  gap: 16px;
  padding: 80px 0;
  color: var(--c-text-4);
}

/* ══════════════════════════════════════════════
   全局命令面板 (⌘K Modal)
   ══════════════════════════════════════════════ */
.cmd-palette-wrapper {
  display: flex;
  flex-direction: column;
}

.cmd-search-input-box {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--c-border);
  background: #ffffff;
}

.cmd-input-icon {
  color: #2563eb;
  flex-shrink: 0;
}

.cmd-real-input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 15px;
  color: #0f172a;
  outline: none;
}

.cmd-esc-tip {
  font-size: 11px;
  color: #94a3b8;
  background: #f1f5f9;
  border: 1px solid #cbd5e1;
  padding: 2px 6px;
  border-radius: 4px;
}

.cmd-results-list {
  max-height: 360px;
  overflow-y: auto;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.cmd-result-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.cmd-result-item:hover,
.cmd-result-item.selected {
  background: #eff6ff;
}

.cmd-item-icon-box {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: #f1f5f9;
  color: #2563eb;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.cmd-result-item.selected .cmd-item-icon-box {
  background: #ffffff;
}

.cmd-item-content {
  flex: 1;
  min-width: 0;
}

.cmd-item-label {
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
}

.cmd-item-desc {
  font-size: 12px;
  color: #64748b;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cmd-item-group {
  font-size: 11px;
  font-weight: 600;
  color: #94a3b8;
  background: #f8fafc;
  padding: 2px 6px;
  border-radius: 4px;
}

.cmd-empty {
  padding: 32px 16px;
  text-align: center;
  font-size: 13.5px;
  color: #94a3b8;
}

.cmd-footer-tips {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 14px;
  padding: 10px 20px;
  background: #f8fafc;
  border-top: 1px solid var(--c-border);
  font-size: 12px;
  color: #64748b;
}

.cmd-footer-tips kbd {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  padding: 1px 5px;
  border-radius: 3px;
  font-weight: bold;
}

/* ══════════════════════════════════════════════
   移动端抽屉 (Mobile Drawer Navigation)
   ══════════════════════════════════════════════ */
.mobile-drawer-body {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.mobile-user-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 12px;
  cursor: pointer;
}

.mobile-user-name {
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
}

.mobile-user-sub {
  font-size: 12px;
  color: #64748b;
}

.mobile-nav-groups {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.mobile-group-title {
  font-size: 11px;
  font-weight: 700;
  color: #94a3b8;
  margin-bottom: 6px;
  padding-left: 6px;
  text-transform: uppercase;
}

.mobile-nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 12px;
  border-radius: 8px;
  font-size: 14px;
  color: #334155;
  cursor: pointer;
  transition: background 0.15s ease;
}

.mobile-nav-item:hover,
.mobile-nav-item.active {
  background: #eff6ff;
  color: #2563eb;
  font-weight: 600;
}

.mobile-item-icon {
  color: #64748b;
}

.mobile-nav-item.active .mobile-item-icon {
  color: #2563eb;
}

.mobile-item-label {
  flex: 1;
}

/* ══════════════════════════════════════════════
   响应式断点控制
   ══════════════════════════════════════════════ */
@media (max-width: 768px) {
  .sidebar {
    display: none;
  }
  .mobile-menu-trigger {
    display: inline-flex;
  }
  .topbar {
    padding: 0 14px;
  }
  .topbar-center {
    display: none;
  }
  .engine-status-tag {
    display: none;
  }
  .content-inner {
    padding: 16px 12px;
  }
  .bc-group {
    display: none;
  }
  .bc-sep:nth-child(2) {
    display: none;
  }
  .top-username {
    display: none;
  }
}
</style>
