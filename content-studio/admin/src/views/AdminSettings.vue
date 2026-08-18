<template>
  <div style="max-width: 720px">
    <!-- 修改密码 -->
    <n-card title="修改密码" style="margin-bottom: 24px">
      <n-form label-placement="left" label-width="80">
        <n-form-item label="原密码">
          <n-input v-model:value="pwdForm.old_password" type="password" placeholder="当前密码" style="max-width: 300px" />
        </n-form-item>
        <n-form-item label="新密码">
          <n-input v-model:value="pwdForm.new_password" type="password" placeholder="至少 8 位，含字母和数字" style="max-width: 300px" />
        </n-form-item>
        <n-form-item>
          <n-button type="primary" :loading="pwdLoading" @click="doChangePwd">确认修改</n-button>
        </n-form-item>
      </n-form>
    </n-card>

    <!-- 管理员列表 -->
    <n-card title="管理员列表">
      <template #header-extra>
        <n-button type="info" size="small" @click="showCreateModal = true">添加管理员</n-button>
      </template>
      <n-data-table :columns="columns" :data="admins" :loading="adminsLoading" :row-key="r => r.id" />
    </n-card>

    <!-- 添加管理员弹窗 -->
    <n-modal v-model:show="showCreateModal" preset="dialog" title="添加管理员" :positive-text="null" style="width: 420px">
      <n-form label-placement="left" label-width="70">
        <n-form-item label="用户名">
          <n-input v-model:value="createForm.username" placeholder="登录用户名" />
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
        <n-button type="primary" :loading="createLoading" @click="doCreateAdmin">创建</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, h, onMounted } from 'vue'
import { NTag, NButton, NPopconfirm, NSpace, useMessage } from 'naive-ui'
import { authApi, adminApi } from '../api'

const message = useMessage()
const currentAdminId = JSON.parse(localStorage.getItem('admin_user') || '{}').id

// ── 修改密码 ──
const pwdForm = ref({ old_password: '', new_password: '' })
const pwdLoading = ref(false)

async function doChangePwd() {
  if (pwdForm.value.new_password.length < 8) {
    message.warning('新密码至少 8 位')
    return
  }
  pwdLoading.value = true
  try {
    const res = await authApi.changePassword(pwdForm.value)
    message.success(res.data.message)
    pwdForm.value = { old_password: '', new_password: '' }
  } catch (e) {
    message.error(e.response?.data?.detail || '修改失败')
  } finally {
    pwdLoading.value = false
  }
}

// ── 管理员列表 ──
const admins = ref([])
const adminsLoading = ref(false)

const columns = [
  { title: 'ID', key: 'id', width: 60 },
  { title: '用户名', key: 'username' },
  { title: '昵称', key: 'nickname' },
  {
    title: '状态', key: 'is_active', width: 80,
    render: (r) => h(NTag, { size: 'small', type: r.is_active ? 'success' : 'error' }, () => r.is_active ? '正常' : '停用'),
  },
  {
    title: '最后登录', key: 'last_login_at', width: 140,
    render: (r) => r.last_login_at ? r.last_login_at.slice(0, 16).replace('T', ' ') : '-',
  },
  {
    title: '操作', key: 'actions', width: 100,
    render: (r) => {
      if (r.id === currentAdminId) return h(NTag, { size: 'tiny', type: 'info' }, () => '当前')
      return h(NPopconfirm, { onPositiveClick: () => doDeleteAdmin(r) }, {
        trigger: () => h(NButton, { size: 'small', type: 'error', text: true }, () => '删除'),
        default: () => `确认删除管理员 ${r.username}？`,
      })
    },
  },
]

async function fetchAdmins() {
  adminsLoading.value = true
  try {
    const { data } = await adminApi.list()
    admins.value = data
  } finally { adminsLoading.value = false }
}

// ── 添加管理员 ──
const showCreateModal = ref(false)
const createLoading = ref(false)
const createForm = ref({ username: '', password: '', nickname: '' })

async function doCreateAdmin() {
  createLoading.value = true
  try {
    const res = await adminApi.create(createForm.value)
    message.success(res.data.message)
    showCreateModal.value = false
    createForm.value = { username: '', password: '', nickname: '' }
    fetchAdmins()
  } catch (e) {
    message.error(e.response?.data?.detail || '创建失败')
  } finally {
    createLoading.value = false
  }
}

async function doDeleteAdmin(row) {
  try {
    const res = await adminApi.delete(row.id)
    message.success(res.data.message)
    fetchAdmins()
  } catch (e) {
    message.error(e.response?.data?.detail || '删除失败')
  }
}

onMounted(fetchAdmins)
</script>
