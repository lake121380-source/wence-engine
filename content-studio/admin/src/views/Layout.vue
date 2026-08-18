<template>
  <n-layout has-sider style="height: 100vh">
    <!-- 侧边栏 -->
    <n-layout-sider
      bordered
      :width="220"
      :collapsed-width="64"
      collapse-mode="width"
      :native-scrollbar="false"
      style="background: #16213e"
    >
      <div class="logo">
        <span class="logo-text">CS 管理后台</span>
      </div>
      <n-menu
        :value="activeKey"
        :options="menuOptions"
        :collapsed="false"
        @update:value="handleMenuSelect"
      />
      <div class="sider-footer">
        <n-button text size="small" @click="handleLogout" style="color: rgba(255,255,255,0.4)">
          退出登录
        </n-button>
      </div>
    </n-layout-sider>

    <!-- 主内容区 -->
    <n-layout>
      <n-layout-header bordered style="height: 56px; display: flex; align-items: center; padding: 0 24px; background: #1a1a2e">
        <n-breadcrumb>
          <n-breadcrumb-item>管理后台</n-breadcrumb-item>
          <n-breadcrumb-item>{{ currentTitle }}</n-breadcrumb-item>
        </n-breadcrumb>
        <div style="flex: 1" />
        <span style="color: rgba(255,255,255,0.5); font-size: 13px">{{ adminNickname }}</span>
      </n-layout-header>
      <n-layout-content
        content-style="padding: 24px;"
        :native-scrollbar="false"
        style="background: #1a1a2e; height: calc(100vh - 56px)"
      >
        <router-view />
      </n-layout-content>
    </n-layout>
  </n-layout>
</template>

<script setup>
import { computed, h } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { NIcon } from 'naive-ui'
import {
  GridOutline,
  BusinessOutline,
  PeopleOutline,
  CardOutline,
  DocumentTextOutline,
  SettingsOutline,
} from '@vicons/ionicons5'

const router = useRouter()
const route = useRoute()

const adminUser = JSON.parse(localStorage.getItem('admin_user') || '{}')
const adminNickname = computed(() => adminUser.nickname || adminUser.username || '管理员')

const activeKey = computed(() => {
  const path = route.path
  if (path.startsWith('/tenants')) return 'tenants'
  if (path.startsWith('/users')) return 'users'
  if (path.startsWith('/orders')) return 'orders'
  if (path.startsWith('/content')) return 'content'
  if (path.startsWith('/settings')) return 'settings'
  return 'dashboard'
})

const currentTitle = computed(() => {
  const map = { dashboard: '数据概览', tenants: '租户管理', users: '用户管理', orders: '订单记录', content: '内容管理', settings: '系统设置' }
  return map[activeKey.value] || '数据概览'
})

function renderIcon(icon) {
  return () => h(NIcon, null, { default: () => h(icon) })
}

const menuOptions = [
  { label: '数据概览', key: 'dashboard', icon: renderIcon(GridOutline) },
  { label: '租户管理', key: 'tenants', icon: renderIcon(BusinessOutline) },
  { label: '用户管理', key: 'users', icon: renderIcon(PeopleOutline) },
  { label: '订单记录', key: 'orders', icon: renderIcon(CardOutline) },
  { label: '内容管理', key: 'content', icon: renderIcon(DocumentTextOutline) },
  { label: '系统设置', key: 'settings', icon: renderIcon(SettingsOutline) },
]

function handleMenuSelect(key) {
  router.push(`/${key}`)
}

function handleLogout() {
  localStorage.removeItem('admin_token')
  localStorage.removeItem('admin_user')
  router.replace('/login')
}
</script>

<style scoped>
.logo {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.logo-text {
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 1px;
}
.sider-footer {
  position: absolute;
  bottom: 16px;
  left: 0;
  right: 0;
  text-align: center;
}
</style>
