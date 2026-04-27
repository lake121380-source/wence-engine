<template>
  <div>
    <n-tabs v-model:value="activeTab" type="line" style="margin-bottom: 16px">
      <n-tab-pane name="creators" tab="创作者">
        <n-space align="center" style="margin-bottom: 12px">
          <n-input v-model:value="creatorsKeyword" placeholder="搜索创作者" clearable style="width: 200px" @keyup.enter="fetchCreators" />
          <n-button type="primary" size="small" @click="fetchCreators">搜索</n-button>
        </n-space>
        <n-data-table :columns="creatorCols" :data="creators" :loading="creatorsLoading" :pagination="creatorsPag" :row-key="r => r.id" @update:page="p => { creatorsPag.page = p; fetchCreators() }" />
      </n-tab-pane>

      <n-tab-pane name="topics" tab="选题">
        <n-space align="center" style="margin-bottom: 12px">
          <n-input v-model:value="topicsKeyword" placeholder="搜索选题标题" clearable style="width: 200px" @keyup.enter="fetchTopics" />
          <n-button type="primary" size="small" @click="fetchTopics">搜索</n-button>
        </n-space>
        <n-data-table :columns="topicCols" :data="topics" :loading="topicsLoading" :pagination="topicsPag" :row-key="r => r.id" @update:page="p => { topicsPag.page = p; fetchTopics() }" />
      </n-tab-pane>

      <n-tab-pane name="generations" tab="生成内容">
        <n-space align="center" style="margin-bottom: 12px">
          <n-input v-model:value="gensKeyword" placeholder="搜索标题/内容" clearable style="width: 200px" @keyup.enter="fetchGenerations" />
          <n-button type="primary" size="small" @click="fetchGenerations">搜索</n-button>
        </n-space>
        <n-data-table :columns="genCols" :data="generations" :loading="gensLoading" :pagination="gensPag" :row-key="r => r.id" @update:page="p => { gensPag.page = p; fetchGenerations() }" />
      </n-tab-pane>
    </n-tabs>

    <!-- 内容详情弹窗 -->
    <n-modal v-model:show="showContentModal" preset="card" title="生成内容详情" style="width: 640px; max-height: 80vh;">
      <div v-if="contentDetail">
        <h3 style="margin: 0 0 12px 0">{{ contentDetail.title }}</h3>
        <n-tag size="small">{{ contentDetail.tenant_name }}</n-tag>
        <n-tag size="small" style="margin-left: 8px">{{ contentDetail.created_at?.slice(0, 10) }}</n-tag>
        <n-divider style="margin: 12px 0" />
        <div style="white-space: pre-wrap; line-height: 1.8; max-height: 50vh; overflow-y: auto;">{{ contentDetail.full_content }}</div>
      </div>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, h, onMounted, reactive } from 'vue'
import { NTag, NButton, NDivider } from 'naive-ui'
import { contentApi } from '../api'

const activeTab = ref('creators')

// ── 创作者 ──
const creatorsKeyword = ref('')
const creatorsLoading = ref(false)
const creators = ref([])
const creatorsPag = reactive({ page: 1, pageSize: 20, itemCount: 0 })

const creatorCols = [
  { title: 'ID', key: 'id', width: 60 },
  { title: '名称', key: 'name' },
  { title: '平台', key: 'platform', width: 80, render: (r) => h(NTag, { size: 'small' }, () => r.platform || '-') },
  { title: '标识', key: 'identifier', width: 140 },
  { title: '风格摘要', key: 'style_summary', ellipsis: { tooltip: true } },
  { title: '所属租户', key: 'tenant_name', width: 140 },
  { title: '创建时间', key: 'created_at', width: 110, render: (r) => r.created_at?.slice(0, 10) || '-' },
]

async function fetchCreators() {
  creatorsLoading.value = true
  try {
    const { data } = await contentApi.creators({ keyword: creatorsKeyword.value || undefined, page: creatorsPag.page, page_size: creatorsPag.pageSize })
    creators.value = data.items
    creatorsPag.itemCount = data.total
  } finally { creatorsLoading.value = false }
}

// ── 选题 ──
const topicsKeyword = ref('')
const topicsLoading = ref(false)
const topics = ref([])
const topicsPag = reactive({ page: 1, pageSize: 20, itemCount: 0 })

const topicCols = [
  { title: 'ID', key: 'id', width: 60 },
  { title: '标题', key: 'title', ellipsis: { tooltip: true } },
  { title: '平台', key: 'platform', width: 80, render: (r) => h(NTag, { size: 'small' }, () => r.platform || '-') },
  { title: '所属租户', key: 'tenant_name', width: 140 },
  { title: '创建时间', key: 'created_at', width: 110, render: (r) => r.created_at?.slice(0, 10) || '-' },
]

async function fetchTopics() {
  topicsLoading.value = true
  try {
    const { data } = await contentApi.topics({ keyword: topicsKeyword.value || undefined, page: topicsPag.page, page_size: topicsPag.pageSize })
    topics.value = data.items
    topicsPag.itemCount = data.total
  } finally { topicsLoading.value = false }
}

// ── 生成内容 ──
const gensKeyword = ref('')
const gensLoading = ref(false)
const generations = ref([])
const gensPag = reactive({ page: 1, pageSize: 20, itemCount: 0 })
const showContentModal = ref(false)
const contentDetail = ref(null)

const genCols = [
  { title: 'ID', key: 'id', width: 60 },
  { title: '标题', key: 'title', ellipsis: { tooltip: true } },
  {
    title: '内容预览', key: 'content_preview', ellipsis: { tooltip: true },
    render: (r) => h('span', {
      style: 'cursor: pointer; color: #63e2b7;',
      onClick: () => { contentDetail.value = r; showContentModal.value = true }
    }, r.content_preview || '-')
  },
  { title: '所属租户', key: 'tenant_name', width: 140 },
  { title: '创建时间', key: 'created_at', width: 110, render: (r) => r.created_at?.slice(0, 10) || '-' },
  {
    title: '操作', key: 'actions', width: 80,
    render: (r) => h(NButton, {
      size: 'small', text: true, type: 'primary',
      onClick: () => { contentDetail.value = r; showContentModal.value = true }
    }, () => '查看')
  },
]

async function fetchGenerations() {
  gensLoading.value = true
  try {
    const { data } = await contentApi.generations({ keyword: gensKeyword.value || undefined, page: gensPag.page, page_size: gensPag.pageSize })
    generations.value = data.items
    gensPag.itemCount = data.total
  } finally { gensLoading.value = false }
}

onMounted(() => {
  fetchCreators()
  fetchTopics()
  fetchGenerations()
})
</script>
