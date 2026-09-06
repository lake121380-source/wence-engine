<template>
  <div class="analytics-container">
    <div class="analytics-header">
      <div><h2>生成分析与引擎指标</h2><p>从已保存的文案统计产出、平台分布与用户评分</p></div>
      <n-space>
        <n-select v-model:value="timeRange" :options="timeRangeOptions" style="width: 130px" @update:value="loadData" />
        <n-button :loading="loading" @click="loadData">刷新数据</n-button>
      </n-space>
    </div>
    <n-alert v-if="error" type="error" style="margin-bottom:16px">{{ error }}</n-alert>
    <n-spin :show="loading">
      <n-card size="small" class="engine-health-card">
        <n-space align="center" justify="space-between">
          <div><n-tag :type="data ? 'success' : 'default'">{{ data?.engine_health.engine_status_text || '等待连接' }}</n-tag>
            <span style="margin-left:12px">当前配置模型：{{ data?.engine_health.model_name || '—' }}</span></div>
          <span class="muted">延迟、Token 用量、缓存命中与采纳率：未采集</span>
        </n-space>
      </n-card>
      <div class="metrics">
        <n-card><div class="muted">区间生成次数</div><div class="metric-number">{{ summary.total_generations ?? '—' }}</div><span>其中今日 {{ summary.today_generations ?? '—' }} 篇</span></n-card>
        <n-card><div class="muted">篇均字数</div><div class="metric-number">{{ summary.avg_word_count ?? '—' }}</div><span>按保存正文字符数统计</span></n-card>
        <n-card><div class="muted">平均评分</div><div class="metric-number">{{ summary.avg_rating ?? '未评分' }}</div><span>{{ summary.rated_count ?? '—' }} 篇已评分</span></n-card>
        <n-card><div class="muted">活跃租户</div><div class="metric-number">{{ summary.active_tenants ?? '—' }}</div><span>区间内产生文案的租户数</span></n-card>
      </div>
      <div class="details">
        <n-card title="各平台产出分布">
          <n-empty v-if="!data?.platforms.length" description="暂无生成记录" />
          <div v-for="p in data?.platforms || []" :key="p.platform" class="stat-row">
            <div class="row-head"><span>{{ p.name }}</span><span>{{ p.count }} 篇 · {{ p.percentage }}%</span></div>
            <n-progress type="line" :percentage="p.percentage" :show-indicator="false" />
            <div class="muted">均字 {{ p.avg_words }} · 评分 {{ p.avg_rating ?? '未评分' }}</div>
          </div>
        </n-card>
        <n-card title="区间生成走势（UTC）">
          <div class="trend-chart">
            <div v-for="day in data?.trend_days || []" :key="day.date" class="trend-col">
              <span>{{ day.count }}</span>
              <div class="trend-track"><div class="trend-bar" :style="{ height: `${day.count / maxCount * 100}%` }"></div></div>
              <span class="muted">{{ day.date.slice(5) }}</span>
            </div>
          </div>
        </n-card>
        <n-card title="租户内容产出排行" style="grid-column:1 / -1">
          <n-empty v-if="!data?.tenant_ranking.length" description="暂无数据" />
          <div v-for="(tenant, index) in data?.tenant_ranking || []" :key="tenant.tenant_id" class="row-head stat-row">
            <span>{{ index + 1 }}. {{ tenant.tenant_name }}</span><span>{{ tenant.count }} 篇 · 评分 {{ tenant.avg_rating ?? '未评分' }}</span>
          </div>
        </n-card>
      </div>
    </n-spin>
    <n-card title="生成内容明细" style="margin-top:16px">
      <n-space style="margin-bottom:16px">
        <n-select v-model:value="platform" :options="platformOptions" style="width:140px" @update:value="search" />
        <n-input v-model:value="keyword" placeholder="搜索标题 / 选题 / 正文" clearable @keyup.enter="search" />
        <n-button @click="search">查询</n-button>
      </n-space>
      <n-data-table remote :columns="columns" :data="records" :loading="tableLoading" :pagination="pagination" :row-key="r => r.id" @update:page="changePage" />
    </n-card>
    <n-modal v-model:show="showDetail" preset="card" title="生成文案" style="width:720px;max-width:95vw">
      <h3>{{ selected?.title }}</h3>
      <div class="muted">{{ selected?.tenant_name }} · {{ platformLabel(selected?.platform) }} · 评分 {{ selected?.rating ?? '未评分' }}</div>
      <pre class="script-content">{{ selected?.full_content }}</pre>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, h, onMounted } from 'vue'
import { NButton, useMessage } from 'naive-ui'
import { contentApi } from '../api'

const message = useMessage()
const data = ref(null)
const summary = computed(() => data.value?.summary || {})
const error = ref('')
const loading = ref(false)
const tableLoading = ref(false)
const timeRange = ref('7d')
const timeRangeOptions = [{ label: '近24小时', value: '24h' }, { label: '近7天', value: '7d' }, { label: '近30天', value: '30d' }]
const maxCount = computed(() => Math.max(1, ...(data.value?.trend_days || []).map(d => d.count)))
const platform = ref('all')
const keyword = ref('')
const records = ref([])
const pagination = reactive({ page: 1, pageSize: 10, itemCount: 0 })
const platformOptions = [{ label: '全部平台', value: 'all' }, { label: '抖音', value: 'douyin' }, { label: '小红书', value: 'xiaohongshu' }, { label: '视频号', value: 'weixin' }]
const platformLabel = value => platformOptions.find(p => p.value === value)?.label || value || '通用'
const showDetail = ref(false)
const selected = ref(null)
const columns = [
  { title: '标题', key: 'title', ellipsis: { tooltip: true } },
  { title: '租户', key: 'tenant_name' },
  { title: '平台', key: 'platform', render: row => platformLabel(row.platform) },
  { title: '字数', key: 'word_count' },
  { title: '评分', key: 'rating', render: row => row.rating ?? '未评分' },
  { title: '时间（UTC）', key: 'created_at', render: row => row.created_at?.slice(0, 16).replace('T', ' ') || '—' },
  { title: '操作', key: 'actions', render: row => h(NButton, { size: 'small', onClick: () => { selected.value = row; showDetail.value = true } }, { default: () => '查看全文' }) },
]
let loadVersion = 0
async function loadData() {
  const version = ++loadVersion
  loading.value = true
  error.value = ''
  try {
    const response = await contentApi.analytics({ time_range: timeRange.value })
    if (version === loadVersion) data.value = response.data
  } catch (e) {
    if (version === loadVersion) { data.value = null; error.value = e.response?.data?.detail || '读取统计失败' }
  } finally { if (version === loadVersion) loading.value = false }
}
let tableVersion = 0
async function loadTable() {
  const version = ++tableVersion
  tableLoading.value = true
  try {
    const { data } = await contentApi.generations({ page: pagination.page, page_size: pagination.pageSize, platform: platform.value, keyword: keyword.value })
    if (version === tableVersion) { records.value = data.items; pagination.itemCount = data.total }
  } catch (e) {
    if (version === tableVersion) { records.value = []; pagination.itemCount = 0; message.error(e.response?.data?.detail || '读取生成记录失败') }
  } finally { if (version === tableVersion) tableLoading.value = false }
}
function search() { pagination.page = 1; loadTable() }
function changePage(page) { pagination.page = page; loadTable() }
onMounted(() => { loadData(); loadTable() })
</script>

<style scoped>
.analytics-container { padding: 4px; }
.analytics-header, .row-head { display:flex;align-items:center;justify-content:space-between;gap:16px; }
.analytics-header { margin-bottom:20px;flex-wrap:wrap; }
h2 { margin:0 0 6px;font-size:24px; }
p, .muted { color:#7b8495;font-size:13px; }
.metrics { display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;margin-top:16px; }
.metric-number { font-size:32px;font-weight:700;margin:12px 0; }
.details { display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin-top:16px; }
.stat-row { margin:12px 0; }
.trend-chart { display:flex;gap:10px;overflow-x:auto;min-height:190px; }
.trend-col { min-width:38px;flex:1;text-align:center;font-size:12px; }
.trend-track { height:135px;display:flex;align-items:flex-end;margin:8px 0; }
.trend-bar { background:#6366f1;border-radius:4px 4px 0 0;width:100%; }
.script-content { white-space:pre-wrap;word-break:break-word;max-height:60vh;overflow:auto;font:inherit;line-height:1.8; }
@media(max-width:900px) { .metrics { grid-template-columns:repeat(2,minmax(0,1fr)); } .details { grid-template-columns:1fr; } }
</style>
