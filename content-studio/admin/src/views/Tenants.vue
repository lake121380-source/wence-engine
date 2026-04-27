<template>
  <div>
    <!-- 搜索栏 -->
    <n-space align="center" style="margin-bottom: 16px">
      <n-input v-model:value="keyword" placeholder="搜索租户名称" clearable style="width: 240px"
        @keyup.enter="fetchList" />
      <n-button type="primary" @click="fetchList">搜索</n-button>
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

    <!-- 编辑租户弹窗 -->
    <n-modal v-model:show="showEditModal" preset="dialog" title="编辑租户" :positive-text="null" style="width: 400px">
      <n-form label-placement="left" label-width="80">
        <n-form-item label="租户名称">
          <n-input v-model:value="editForm.name" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showEditModal = false">取消</n-button>
        <n-button type="primary" :loading="editLoading" @click="doEdit">保存</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, h, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { NTag, NButton, NAvatar, NSpace, NPopconfirm, useMessage } from 'naive-ui'
import { tenantApi } from '../api'

const router = useRouter()
const message = useMessage()
const loading = ref(false)
const keyword = ref('')
const list = ref([])

const pagination = reactive({
  page: 1,
  pageSize: 20,
  itemCount: 0,
  showSizePicker: false,
})

// 编辑
const showEditModal = ref(false)
const editLoading = ref(false)
const editTenantId = ref(null)
const editForm = ref({ name: '' })

const columns = [
  { title: 'ID', key: 'id', width: 60 },
  {
    title: '租户名称',
    key: 'name',
    render: (row) => h('span', { style: 'font-weight: 500' }, row.name),
  },
  {
    title: '管理员',
    key: 'admin_nickname',
    render: (row) => h(NSpace, { align: 'center', size: 8 }, () => [
      row.admin_avatar ? h(NAvatar, { src: row.admin_avatar, size: 24, round: true }) : null,
      row.admin_nickname || '-',
    ]),
  },
  { title: '成员数', key: 'member_count', width: 80 },
  {
    title: '订阅状态',
    key: 'subscription',
    render: (row) => {
      const sub = row.subscription
      if (!sub || sub.plan === 'none') return h(NTag, { size: 'small', type: 'default' }, () => '无')
      const isActive = sub.is_active
      return h(NSpace, { align: 'center', size: 4 }, () => [
        h(NTag, { size: 'small', type: isActive ? 'success' : 'error' }, () =>
          sub.plan === 'trial' ? '试用' : '月付'
        ),
        sub.expire_at ? h('span', { style: 'font-size: 12px; color: rgba(255,255,255,0.4)' },
          sub.expire_at.slice(0, 10)
        ) : null,
      ])
    },
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 120,
    render: (row) => row.created_at ? row.created_at.slice(0, 10) : '-',
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    render: (row) => h(NSpace, { size: 8 }, () => [
      h(NButton, {
        size: 'small', text: true, type: 'primary',
        onClick: () => router.push(`/tenants/${row.id}`),
      }, () => '详情'),
      h(NButton, {
        size: 'small', text: true,
        onClick: () => openEdit(row),
      }, () => '编辑'),
      h(NPopconfirm, { onPositiveClick: () => doDelete(row.id) }, {
        trigger: () => h(NButton, { size: 'small', type: 'error', text: true }, () => '删除'),
        default: () => `确认删除「${row.name}」及其所有数据？此操作不可恢复！`,
      }),
    ]),
  },
]

function openEdit(row) {
  editTenantId.value = row.id
  editForm.value = { name: row.name }
  showEditModal.value = true
}

async function doEdit() {
  editLoading.value = true
  try {
    const res = await tenantApi.edit(editTenantId.value, editForm.value)
    message.success(res.data.message)
    showEditModal.value = false
    fetchList()
  } catch (e) {
    message.error(e.response?.data?.detail || '更新失败')
  } finally {
    editLoading.value = false
  }
}

async function doDelete(id) {
  try {
    const res = await tenantApi.delete(id)
    message.success(res.data.message)
    fetchList()
  } catch (e) {
    message.error(e.response?.data?.detail || '删除失败')
  }
}

async function fetchList() {
  loading.value = true
  try {
    const res = await tenantApi.list({
      keyword: keyword.value || undefined,
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

onMounted(fetchList)
</script>
