<template>
  <div>
    <!-- 筛选 -->
    <n-space align="center" style="margin-bottom: 16px" justify="space-between">
      <n-space align="center">
        <n-input v-model:value="keyword" placeholder="搜索订单号/用户/流水号" clearable style="width: 200px"
          @keyup.enter="fetchList" />
        <n-select v-model:value="filterStatus" :options="statusOptions" placeholder="订单状态"
          clearable style="width: 130px" />
        <n-select v-model:value="filterMethod" :options="methodOptions" placeholder="支付方式"
          clearable style="width: 130px" />
        <n-button type="primary" @click="fetchList">筛选</n-button>
      </n-space>
      <n-button @click="handleExport" :loading="exportLoading">导出 CSV</n-button>
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
  </div>
</template>

<script setup>
import { ref, h, onMounted, reactive } from 'vue'
import { NTag, useMessage } from 'naive-ui'
import { orderApi, exportApi } from '../api'

const message = useMessage()
const loading = ref(false)
const exportLoading = ref(false)
const keyword = ref('')
const filterStatus = ref(null)
const filterMethod = ref(null)
const list = ref([])

const statusOptions = [
  { label: '待支付', value: 'pending' },
  { label: '已支付', value: 'paid' },
  { label: '已关闭', value: 'closed' },
  { label: '已退款', value: 'refunded' },
]

const methodOptions = [
  { label: '微信支付', value: 'wechat' },
  { label: '支付宝', value: 'alipay' },
]

const pagination = reactive({
  page: 1,
  pageSize: 20,
  itemCount: 0,
})

const statusTypeMap = {
  pending: 'warning',
  paid: 'success',
  closed: 'default',
  refunded: 'error',
}
const statusLabelMap = {
  pending: '待支付',
  paid: '已支付',
  closed: '已关闭',
  refunded: '已退款',
}

const columns = [
  { title: '订单号', key: 'order_no', width: 180, ellipsis: { tooltip: true } },
  { title: '用户', key: 'user_nickname', width: 100 },
  {
    title: '金额',
    key: 'amount',
    width: 90,
    render: (row) => h('span', { style: 'font-weight: 600' }, `¥${row.amount}`),
  },
  {
    title: '支付方式',
    key: 'method',
    width: 90,
    render: (row) => h(NTag, { size: 'small' }, () => row.method === 'wechat' ? '微信' : '支付宝'),
  },
  {
    title: '套餐',
    key: 'plan',
    width: 70,
    render: (row) => row.plan === 'monthly' ? '月付' : row.plan,
  },
  {
    title: '状态',
    key: 'status',
    width: 80,
    render: (row) => h(NTag, {
      size: 'small',
      type: statusTypeMap[row.status] || 'default',
    }, () => statusLabelMap[row.status] || row.status),
  },
  {
    title: '流水号',
    key: 'transaction_id',
    width: 150,
    ellipsis: { tooltip: true },
    render: (row) => row.transaction_id || '-',
  },
  {
    title: '支付时间',
    key: 'paid_at',
    width: 150,
    render: (row) => row.paid_at ? row.paid_at.replace('T', ' ').slice(0, 16) : '-',
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 150,
    render: (row) => row.created_at ? row.created_at.replace('T', ' ').slice(0, 16) : '-',
  },
]

async function fetchList() {
  loading.value = true
  try {
    const res = await orderApi.list({
      keyword: keyword.value || undefined,
      status: filterStatus.value || undefined,
      method: filterMethod.value || undefined,
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

async function handleExport() {
  exportLoading.value = true
  try {
    const res = await exportApi.orders()
    const url = URL.createObjectURL(new Blob([res.data]))
    const a = document.createElement('a')
    a.href = url
    a.download = 'orders.csv'
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    message.error('导出失败')
  } finally {
    exportLoading.value = false
  }
}
</script>
