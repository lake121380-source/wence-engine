<template>
  <div>
    <n-page-header @back="$router.back()" :title="tenant?.name || '租户详情'" subtitle="">
      <template #extra>
        <n-tag :type="tenant?.created_at ? 'info' : 'default'" size="small">
          创建于 {{ tenant?.created_at?.slice(0, 10) || '-' }}
        </n-tag>
      </template>
    </n-page-header>

    <n-spin :show="loading" style="margin-top: 16px">
      <!-- 统计 -->
      <n-grid :cols="3" :x-gap="16" style="margin-bottom: 16px">
        <n-gi>
          <n-card size="small"><n-statistic label="博主数" :value="tenant?.stats?.creators || 0" /></n-card>
        </n-gi>
        <n-gi>
          <n-card size="small"><n-statistic label="选题数" :value="tenant?.stats?.topics || 0" /></n-card>
        </n-gi>
        <n-gi>
          <n-card size="small"><n-statistic label="生成次数" :value="tenant?.stats?.generations || 0" /></n-card>
        </n-gi>
      </n-grid>

      <!-- 成员列表 -->
      <n-card title="成员列表" size="small">
        <n-data-table
          :columns="memberColumns"
          :data="tenant?.members || []"
          :row-key="row => row.id"
          :pagination="false"
        />
      </n-card>
    </n-spin>
  </div>
</template>

<script setup>
import { ref, h, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { NTag, NAvatar, NSpace } from 'naive-ui'
import { tenantApi } from '../api'

const route = useRoute()
const loading = ref(false)
const tenant = ref(null)

const memberColumns = [
  { title: 'ID', key: 'id', width: 60 },
  {
    title: '用户',
    key: 'nickname',
    render: (row) => h(NSpace, { align: 'center', size: 8 }, () => [
      row.avatar ? h(NAvatar, { src: row.avatar, size: 28, round: true }) : null,
      row.nickname || '未设置',
    ]),
  },
  {
    title: '角色',
    key: 'role',
    width: 80,
    render: (row) => h(NTag, { size: 'small', type: row.role === 'admin' ? 'warning' : 'default' },
      () => row.role === 'admin' ? '管理员' : '成员'),
  },
  {
    title: '状态',
    key: 'is_active',
    width: 80,
    render: (row) => h(NTag, { size: 'small', type: row.is_active ? 'success' : 'error' },
      () => row.is_active ? '正常' : '已封禁'),
  },
  {
    title: '订阅',
    key: 'subscription',
    render: (row) => {
      const sub = row.subscription
      if (!sub || sub.plan === 'none') return '-'
      return h(NSpace, { align: 'center', size: 4 }, () => [
        h(NTag, { size: 'small', type: sub.is_active ? 'success' : 'error' },
          () => sub.plan === 'trial' ? '试用' : '月付'),
        sub.expire_at ? h('span', { style: 'font-size: 12px; color: rgba(255,255,255,0.4)' },
          sub.expire_at.slice(0, 10)) : null,
      ])
    },
  },
  {
    title: '最后登录',
    key: 'last_login_at',
    width: 120,
    render: (row) => row.last_login_at ? row.last_login_at.slice(0, 10) : '-',
  },
]

async function fetchDetail() {
  loading.value = true
  try {
    const res = await tenantApi.detail(route.params.id)
    tenant.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(fetchDetail)
</script>
