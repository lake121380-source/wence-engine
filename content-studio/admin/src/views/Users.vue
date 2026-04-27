<template>
  <div>
    <!-- 搜索栏 -->
    <n-space align="center" style="margin-bottom: 16px" justify="space-between">
      <n-space align="center">
        <n-input v-model:value="keyword" placeholder="搜索用户昵称/邮箱" clearable style="width: 220px"
          @keyup.enter="fetchList" />
        <n-select v-model:value="filterActive" :options="activeOptions" placeholder="用户状态"
          clearable style="width: 120px" />
        <n-button type="primary" @click="fetchList">搜索</n-button>
      </n-space>
      <n-space>
        <n-button @click="handleExport" :loading="exportLoading">导出 CSV</n-button>
        <n-button type="info" @click="showCreateModal = true">创建用户</n-button>
      </n-space>
    </n-space>

    <!-- 表格 -->
    <n-data-table
      :columns="columns"
      :data="list"
      :loading="loading"
      :pagination="pagination"
      :row-key="row => row.id"
      @update:page="handlePageChange"
    />

    <!-- 创建用户弹窗 -->
    <n-modal v-model:show="showCreateModal" preset="dialog" title="创建用户" :positive-text="null" style="width: 440px">
      <n-form label-placement="left" label-width="70">
        <n-form-item label="邮箱">
          <n-input v-model:value="createForm.email" placeholder="user@example.com" />
        </n-form-item>
        <n-form-item label="密码">
          <n-input v-model:value="createForm.password" type="password" placeholder="至少 8 位，含字母和数字" />
        </n-form-item>
        <n-form-item label="昵称">
          <n-input v-model:value="createForm.nickname" placeholder="选填" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showCreateModal = false">取消</n-button>
        <n-button type="primary" :loading="createLoading" @click="doCreate">创建</n-button>
      </template>
    </n-modal>

    <!-- 编辑用户弹窗 -->
    <n-modal v-model:show="showEditModal" preset="dialog" title="编辑用户" :positive-text="null" style="width: 440px">
      <n-form label-placement="left" label-width="70">
        <n-form-item label="昵称">
          <n-input v-model:value="editForm.nickname" />
        </n-form-item>
        <n-form-item label="邮箱">
          <n-input v-model:value="editForm.email" />
        </n-form-item>
        <n-form-item label="状态">
          <n-switch v-model:value="editForm.is_active" />
          <span style="margin-left: 8px; font-size: 13px; color: rgba(255,255,255,0.5);">
            {{ editForm.is_active ? '正常' : '已封禁' }}
          </span>
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showEditModal = false">取消</n-button>
        <n-button type="primary" :loading="editLoading" @click="doEdit">保存</n-button>
      </template>
    </n-modal>

    <!-- 重置密码弹窗 -->
    <n-modal v-model:show="showResetPwdModal" preset="dialog" title="重置密码" :positive-text="null" style="width: 400px">
      <n-form label-placement="left" label-width="70">
        <n-form-item label="新密码">
          <n-input v-model:value="resetPwdForm.password" type="password" placeholder="至少 8 位，含字母和数字" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showResetPwdModal = false">取消</n-button>
        <n-button type="warning" :loading="resetPwdLoading" @click="doResetPwd">确认重置</n-button>
      </template>
    </n-modal>

    <!-- 延长订阅弹窗 -->
    <n-modal v-model:show="showExtendModal" preset="dialog" title="延长订阅" :positive-text="null">
      <n-form>
        <n-form-item label="延长天数">
          <n-input-number v-model:value="extendForm.days" :min="1" :max="365" />
        </n-form-item>
        <n-form-item label="套餐类型">
          <n-select v-model:value="extendForm.plan" :options="[
            { label: '月付', value: 'monthly' },
            { label: '试用', value: 'trial' },
          ]" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showExtendModal = false">取消</n-button>
        <n-button type="primary" :loading="extendLoading" @click="doExtend">确认延长</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, h, onMounted, reactive } from 'vue'
import { NTag, NButton, NAvatar, NSpace, NPopconfirm, useMessage } from 'naive-ui'
import { userApi, exportApi } from '../api'

const message = useMessage()
const loading = ref(false)
const keyword = ref('')
const filterActive = ref(null)
const list = ref([])
const exportLoading = ref(false)

const activeOptions = [
  { label: '正常', value: true },
  { label: '已封禁', value: false },
]

const pagination = reactive({
  page: 1,
  pageSize: 20,
  itemCount: 0,
})

// 创建用户
const showCreateModal = ref(false)
const createLoading = ref(false)
const createForm = ref({ email: '', password: '', nickname: '' })

// 编辑用户
const showEditModal = ref(false)
const editLoading = ref(false)
const editUserId = ref(null)
const editForm = ref({ nickname: '', email: '', is_active: true })

// 重置密码
const showResetPwdModal = ref(false)
const resetPwdLoading = ref(false)
const resetPwdUserId = ref(null)
const resetPwdForm = ref({ password: '' })

// 延长订阅
const showExtendModal = ref(false)
const extendLoading = ref(false)
const extendUserId = ref(null)
const extendForm = ref({ days: 30, plan: 'monthly' })

const columns = [
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
    title: '邮箱',
    key: 'email',
    render: (row) => row.email || '-',
  },
  {
    title: '租户',
    key: 'tenant_name',
    render: (row) => row.tenant_name || '-',
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
      if (!sub || sub.plan === 'none') return h(NTag, { size: 'small' }, () => '无订阅')
      return h(NSpace, { align: 'center', size: 4 }, () => [
        h(NTag, { size: 'small', type: sub.is_active ? 'success' : 'error' },
          () => sub.is_trial ? '试用' : '月付'),
        sub.expire_at ? h('span', { style: 'font-size: 12px; color: rgba(255,255,255,0.4)' },
          sub.expire_at.slice(0, 10)) : null,
      ])
    },
  },
  {
    title: '注册时间',
    key: 'created_at',
    width: 120,
    render: (row) => row.created_at ? row.created_at.slice(0, 10) : '-',
  },
  {
    title: '操作',
    key: 'actions',
    width: 320,
    render: (row) => {
      const btns = []
      btns.push(
        h(NButton, { size: 'small', text: true, onClick: () => openEdit(row) }, () => '编辑')
      )
      btns.push(
        h(NButton, { size: 'small', text: true, type: 'warning', onClick: () => openResetPwd(row) }, () => '重置密码')
      )
      if (row.is_active) {
        btns.push(
          h(NPopconfirm, { onPositiveClick: () => toggleBan(row) }, {
            trigger: () => h(NButton, { size: 'small', type: 'error', text: true }, () => '封禁'),
            default: () => `确认封禁 ${row.nickname || '该用户'}？`,
          })
        )
      } else {
        btns.push(
          h(NButton, { size: 'small', type: 'success', text: true, onClick: () => toggleBan(row) }, () => '解封')
        )
      }
      btns.push(
        h(NButton, { size: 'small', type: 'primary', text: true, onClick: () => openExtend(row) }, () => '延长订阅')
      )
      if (row.subscription?.is_active) {
        btns.push(
          h(NPopconfirm, { onPositiveClick: () => revokeSubscription(row) }, {
            trigger: () => h(NButton, { size: 'small', type: 'warning', text: true }, () => '撤销'),
            default: () => '确认撤销该用户的订阅？',
          })
        )
      }
      return h(NSpace, { size: 8 }, () => btns)
    },
  },
]

async function fetchList() {
  loading.value = true
  try {
    const res = await userApi.list({
      keyword: keyword.value || undefined,
      is_active: filterActive.value ?? undefined,
      page: pagination.page,
      page_size: pagination.pageSize,
    })
    list.value = res.data.items
    pagination.itemCount = res.data.total
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function handlePageChange(page) {
  pagination.page = page
  fetchList()
}

async function doCreate() {
  createLoading.value = true
  try {
    const res = await userApi.create(createForm.value)
    message.success(res.data.message)
    showCreateModal.value = false
    createForm.value = { email: '', password: '', nickname: '' }
    fetchList()
  } catch (e) {
    message.error(e.response?.data?.detail || '创建失败')
  } finally {
    createLoading.value = false
  }
}

function openEdit(row) {
  editUserId.value = row.id
  editForm.value = { nickname: row.nickname, email: row.email || '', is_active: row.is_active }
  showEditModal.value = true
}

async function doEdit() {
  editLoading.value = true
  try {
    const res = await userApi.edit(editUserId.value, editForm.value)
    message.success(res.data.message)
    showEditModal.value = false
    fetchList()
  } catch (e) {
    message.error(e.response?.data?.detail || '更新失败')
  } finally {
    editLoading.value = false
  }
}

function openResetPwd(row) {
  resetPwdUserId.value = row.id
  resetPwdForm.value = { password: '' }
  showResetPwdModal.value = true
}

async function doResetPwd() {
  resetPwdLoading.value = true
  try {
    const res = await userApi.resetPassword(resetPwdUserId.value, resetPwdForm.value)
    message.success(res.data.message)
    showResetPwdModal.value = false
  } catch (e) {
    message.error(e.response?.data?.detail || '重置失败')
  } finally {
    resetPwdLoading.value = false
  }
}

async function toggleBan(row) {
  try {
    if (row.is_active) {
      await userApi.ban(row.id)
      message.success('已封禁')
    } else {
      await userApi.unban(row.id)
      message.success('已解封')
    }
    fetchList()
  } catch (e) {
    message.error(e.response?.data?.detail || '操作失败')
  }
}

function openExtend(row) {
  extendUserId.value = row.id
  extendForm.value = { days: 30, plan: 'monthly' }
  showExtendModal.value = true
}

async function doExtend() {
  extendLoading.value = true
  try {
    const res = await userApi.extendSubscription(extendUserId.value, extendForm.value)
    message.success(res.data.message)
    showExtendModal.value = false
    fetchList()
  } catch (e) {
    message.error(e.response?.data?.detail || '操作失败')
  } finally {
    extendLoading.value = false
  }
}

async function revokeSubscription(row) {
  try {
    await userApi.revokeSubscription(row.id)
    message.success('订阅已撤销')
    fetchList()
  } catch (e) {
    message.error(e.response?.data?.detail || '操作失败')
  }
}

async function handleExport() {
  exportLoading.value = true
  try {
    const res = await exportApi.users()
    const url = URL.createObjectURL(new Blob([res.data]))
    const a = document.createElement('a')
    a.href = url
    a.download = 'users.csv'
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    message.error('导出失败')
  } finally {
    exportLoading.value = false
  }
}

onMounted(fetchList)
</script>
