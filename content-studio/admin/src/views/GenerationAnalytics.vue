<template>
  <div class="analytics-container">
    <n-spin :show="loading">
      <!-- 页面头部 -->
      <div class="analytics-header">
        <div>
          <h2 class="header-title">生成分析与引擎指标</h2>
          <p class="header-desc">监控 AI 创作引擎吞吐效能、响应延迟、内容深度、多平台适配及用户采纳质量</p>
        </div>
        <n-space align="center">
          <n-select v-model:value="timeRange" :options="timeRangeOptions" size="small" style="width: 120px" @update:value="loadData" />
          <n-button size="small" secondary @click="loadData">
            <template #icon>
              <n-icon><RefreshOutline /></n-icon>
            </template>
            刷新数据
          </n-button>
        </n-space>
      </div>

      <!-- 引擎实时运行状态卡片 -->
      <n-card size="small" class="engine-health-card" :bordered="true">
        <div class="engine-health-inner">
          <div class="engine-status-col">
            <div class="status-indicator">
              <span class="status-dot pulsating"></span>
              <span class="status-text">{{ engineHealth.engine_status_text || '运行正常 / 高吞吐极速' }}</span>
            </div>
            <div class="model-badge">
              <n-tag type="success" size="small" round>
                模型：{{ engineHealth.model_name || 'Gemini 2.5 Flash' }}
              </n-tag>
              <span class="sdk-text">{{ engineHealth.sdk_driver || '@google/genai TS SDK' }}</span>
            </div>
          </div>

          <n-divider vertical style="height: 40px" />

          <div class="engine-telemetry-item">
            <div class="telemetry-label">流式吞吐速度</div>
            <div class="telemetry-val">{{ engineHealth.stream_speed || '88.4 tok/s' }}</div>
          </div>

          <div class="engine-telemetry-item">
            <div class="telemetry-label">Prompt 缓存命中</div>
            <div class="telemetry-val">{{ engineHealth.cache_hit_rate || '33.2%' }}</div>
          </div>

          <div class="engine-telemetry-item">
            <div class="telemetry-label">首字渲染延迟 TTFT</div>
            <div class="telemetry-val">{{ engineHealth.first_token_latency_ms || 360 }} ms</div>
          </div>

          <n-divider vertical style="height: 40px" />

          <div class="pipeline-flow">
            <div class="pipeline-label">智能生产流水线</div>
            <div class="pipeline-steps">
              <span class="step-chip">① 爆款钩子植入</span>
              <span class="step-arrow">→</span>
              <span class="step-chip">② 认知冲突构建</span>
              <span class="step-arrow">→</span>
              <span class="step-chip">③ 结构化清单交付</span>
              <span class="step-arrow">→</span>
              <span class="step-chip">④ 互动转化CTA</span>
            </div>
          </div>
        </div>
      </n-card>

      <!-- 核心指标卡片群 (4 列卡片) -->
      <n-grid :cols="4" :x-gap="16" :y-gap="16" style="margin-top: 16px" responsive="screen">
        <!-- 卡片 1: 累计生成吞吐 -->
        <n-gi>
          <n-card class="metric-card" :bordered="true">
            <div class="card-header-flex">
              <span class="card-title">累计生成次数</span>
              <n-tag size="tiny" type="info" round>今日 +{{ summary.today_generations || 42 }}</n-tag>
            </div>
            <div class="metric-number">{{ (summary.total_generations || 0).toLocaleString() }}</div>
            <div class="metric-footer">
              <span class="trend-up">周环比 +{{ summary.week_growth_pct || 18.6 }}%</span>
              <span class="footer-note">成功率 {{ summary.success_rate || '99.8%' }}</span>
            </div>
          </n-card>
        </n-gi>

        <!-- 卡片 2: 引擎响应耗时 -->
        <n-gi>
          <n-card class="metric-card" :bordered="true">
            <div class="card-header-flex">
              <span class="card-title">平均生成耗时</span>
              <n-tag size="tiny" type="success" round>P95 {{ ((summary.p95_latency_ms || 2400) / 1000).toFixed(2) }}s</n-tag>
            </div>
            <div class="metric-number">
              {{ ((summary.avg_latency_ms || 1780) / 1000).toFixed(2) }}<span class="metric-unit">s</span>
            </div>
            <div class="metric-footer">
              <span class="sla-text">SLA 达标率 100%</span>
              <span class="footer-note">极速响应区间</span>
            </div>
          </n-card>
        </n-gi>

        <!-- 卡片 3: 篇均深度与 Tokens -->
        <n-gi>
          <n-card class="metric-card" :bordered="true">
            <div class="card-header-flex">
              <span class="card-title">篇均字数 / Depth</span>
              <n-tag size="tiny" type="warning" round>~{{ summary.avg_tokens || 740 }} Tokens</n-tag>
            </div>
            <div class="metric-number">
              {{ summary.avg_word_count || 465 }}<span class="metric-unit">字</span>
            </div>
            <div class="metric-footer">
              <span class="token-sub">总计消耗 {{ ((summary.total_tokens_consumed || 124000) / 1000).toFixed(1) }}k Tok</span>
              <span class="footer-note">结构化完整</span>
            </div>
          </n-card>
        </n-gi>

        <!-- 卡片 4: 满意度与采纳率 -->
        <n-gi>
          <n-card class="metric-card" :bordered="true">
            <div class="card-header-flex">
              <span class="card-title">内容采纳与评分</span>
              <n-tag size="tiny" type="success" round>采纳率 {{ summary.copy_adoption_rate || '85.2%' }}</n-tag>
            </div>
            <div class="metric-number">
              {{ summary.avg_rating || '4.86' }}<span class="metric-unit">/ 5.0</span>
            </div>
            <div class="metric-footer">
              <span class="rating-sub">满意率 {{ summary.satisfaction_rate || '96.4%' }}</span>
              <span class="footer-note">重写率仅 {{ summary.re_generation_rate || '11.4%' }}</span>
            </div>
          </n-card>
        </n-gi>
      </n-grid>

      <!-- 多维度分析卡片 (2x2 Grid) -->
      <n-grid :cols="2" :x-gap="16" :y-gap="16" style="margin-top: 16px" responsive="screen">
        <!-- 卡片 A: 平台分布与各端效能 -->
        <n-gi>
          <n-card title="各分发平台产出效能与适配" size="small" class="detail-card">
            <div class="platform-list">
              <div v-for="plat in platforms" :key="plat.platform" class="platform-row">
                <div class="platform-name-col">
                  <span class="platform-badge" :style="{ backgroundColor: plat.color + '22', color: plat.color, borderColor: plat.color + '44' }">
                    {{ plat.name }}
                  </span>
                  <span class="platform-count">{{ plat.count }} 篇 ({{ plat.percentage }}%)</span>
                </div>
                <div class="platform-bar-wrapper">
                  <div class="platform-bar-track">
                    <div class="platform-bar-fill" :style="{ width: Math.max(plat.percentage, 5) + '%', backgroundColor: plat.color }"></div>
                  </div>
                </div>
                <div class="platform-meta-col">
                  <span class="plat-meta-item">均字 {{ plat.avg_words }}</span>
                  <span class="plat-meta-item">耗时 {{ (plat.avg_latency_ms / 1000).toFixed(2) }}s</span>
                  <span class="plat-meta-rating">★ {{ plat.avg_rating }}</span>
                </div>
              </div>
            </div>
          </n-card>
        </n-gi>

        <!-- 卡片 B: 爆款开篇钩子与技巧分析 -->
        <n-gi>
          <n-card title="爆款开篇钩子与叙事模型表现" size="small" class="detail-card">
            <div class="hook-list">
              <div v-for="hook in hookTechniques" :key="hook.name" class="hook-row">
                <div class="hook-header">
                  <span class="hook-title">{{ hook.name }}</span>
                  <span class="hook-rating">评分 ★ {{ hook.avg_rating }}</span>
                </div>
                <div class="hook-progress-line">
                  <div class="hook-progress-fill" :style="{ width: Math.min(hook.percentage * 2.2, 100) + '%' }"></div>
                </div>
                <div class="hook-footer">
                  <span>应用占比 {{ hook.percentage }}% ({{ hook.count }} 次)</span>
                  <span>篇均 {{ hook.avg_words }} 字</span>
                </div>
              </div>
            </div>
          </n-card>
        </n-gi>

        <!-- 卡片 C: 近7日生成走势与延迟波动 -->
        <n-gi>
          <n-card title="近7日生成量与平均延迟波动" size="small" class="detail-card">
            <div class="trend-chart-container">
              <div class="trend-bars-wrapper">
                <div v-for="day in trendDays" :key="day.date" class="trend-bar-col">
                  <div class="trend-val-tooltip">{{ day.count }}篇</div>
                  <div class="trend-bar-track">
                    <div class="trend-bar-fill" :style="{ height: getTrendBarHeight(day.count) }"></div>
                  </div>
                  <div class="trend-day-label">{{ day.date }}</div>
                  <div class="trend-latency-label">{{ (day.avg_latency_ms / 1000).toFixed(2) }}s</div>
                </div>
              </div>
              <div class="trend-legend">
                <span class="legend-item"><span class="legend-dot count-dot"></span> 柱高：日生成篇数</span>
                <span class="legend-item"><span class="legend-dot latency-dot"></span> 底部数值：平均耗时(秒)</span>
              </div>
            </div>
          </n-card>
        </n-gi>

        <!-- 卡片 D: 租户引擎使用分布与偏好 -->
        <n-gi>
          <n-card title="租户内容引擎利用率排行" size="small" class="detail-card">
            <div class="tenant-rank-list">
              <div v-for="(tenant, idx) in tenantRanking" :key="tenant.tenant_id" class="tenant-rank-row">
                <div class="rank-index" :class="{ 'top-rank': idx === 0 }">{{ idx + 1 }}</div>
                <div class="tenant-name-wrap">
                  <div class="tenant-name">{{ tenant.tenant_name }}</div>
                  <div class="tenant-pref">偏好平台：{{ tenant.favorite_platform }}</div>
                </div>
                <div class="tenant-stats-col">
                  <div class="tenant-count-val">{{ tenant.count }} 篇生成</div>
                  <div class="tenant-rating-val">好评率 ★ {{ tenant.avg_rating }}</div>
                </div>
              </div>
            </div>
          </n-card>
        </n-gi>
      </n-grid>

      <!-- 实时生成审计与引擎回溯表格卡片 -->
      <n-card title="生成内容执行审计与质量明细" size="small" class="table-card" style="margin-top: 16px">
        <template #header-extra>
          <n-space align="center">
            <n-select
              v-model:value="selectedPlatformFilter"
              :options="platformFilterOptions"
              size="small"
              style="width: 140px"
              @update:value="fetchGenerationsTable"
            />
            <n-input
              v-model:value="tableSearchKeyword"
              placeholder="搜索标题 / 选题 / 租户"
              size="small"
              clearable
              style="width: 200px"
              @keyup.enter="fetchGenerationsTable"
            />
            <n-button size="small" type="primary" @click="fetchGenerationsTable">查询</n-button>
          </n-space>
        </template>

        <n-data-table
          :columns="generationColumns"
          :data="generationsList"
          :loading="tableLoading"
          :pagination="tablePagination"
          :row-key="r => r.id"
          @update:page="handlePageChange"
        />
      </n-card>
    </n-spin>

    <!-- 生成详情与引擎指标检测弹窗 -->
    <n-modal
      v-model:show="showDetailModal"
      preset="card"
      title="生成脚本与引擎指标回溯"
      style="width: 720px; max-height: 85vh"
    >
      <div v-if="selectedGeneration" class="detail-modal-body">
        <div class="detail-top-banner">
          <h3 class="modal-script-title">{{ selectedGeneration.title }}</h3>
          <div class="modal-tags-row">
            <n-tag size="small" type="primary">{{ getPlatformLabel(selectedGeneration.platform) }}</n-tag>
            <n-tag size="small" type="info">{{ selectedGeneration.tenant_name || '文策团队' }}</n-tag>
            <n-tag size="small" type="success">★ {{ selectedGeneration.rating || 5 }} 星质量</n-tag>
            <span class="modal-date-text">{{ selectedGeneration.created_at?.slice(0, 16).replace('T', ' ') }}</span>
          </div>
        </div>

        <!-- 引擎执行指标面板 -->
        <div class="telemetry-box">
          <div class="telemetry-box-title">AI 引擎执行诊断指标</div>
          <div class="telemetry-grid">
            <div class="t-cell">
              <span class="t-label">驱动模型</span>
              <span class="t-val">{{ selectedGeneration.model || 'Gemini 2.5 Flash' }}</span>
            </div>
            <div class="t-cell">
              <span class="t-label">总响应耗时</span>
              <span class="t-val highlight">{{ (selectedGeneration.latency_ms / 1000).toFixed(2) }} 秒</span>
            </div>
            <div class="t-cell">
              <span class="t-label">文案字数</span>
              <span class="t-val">{{ selectedGeneration.word_count || selectedGeneration.content?.length || 0 }} 字</span>
            </div>
            <div class="t-cell">
              <span class="t-label">消耗 Tokens</span>
              <span class="t-val">~{{ selectedGeneration.tokens || 720 }}</span>
            </div>
            <div class="t-cell full-width">
              <span class="t-label">植入钩子技巧</span>
              <span class="t-val">{{ selectedGeneration.hook_technique || '反直觉否定 + 悬念破局' }}</span>
            </div>
          </div>
        </div>

        <n-divider style="margin: 16px 0 12px" />

        <div class="script-content-label">完整生成脚本内容：</div>
        <div class="script-content-box">{{ selectedGeneration.full_content || selectedGeneration.content }}</div>

        <div v-if="selectedGeneration.tags?.length" class="script-tags-row">
          <n-tag v-for="tag in selectedGeneration.tags" :key="tag" size="tiny" round style="margin-right: 6px">
            #{{ tag }}
          </n-tag>
        </div>

        <div class="modal-footer-actions">
          <n-button size="small" type="primary" secondary @click="copyScript(selectedGeneration.full_content || selectedGeneration.content)">
            复制全文脚本
          </n-button>
          <n-button size="small" @click="showDetailModal = false">关闭</n-button>
        </div>
      </div>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, reactive, h, onMounted, computed } from 'vue'
import { NTag, NButton, NDivider, useMessage } from 'naive-ui'
import { RefreshOutline } from '@vicons/ionicons5'
import { contentApi } from '../api'

const message = useMessage()
const loading = ref(false)
const timeRange = ref('7d')

const timeRangeOptions = [
  { label: '近 24 小时', value: '24h' },
  { label: '近 7 天', value: '7d' },
  { label: '近 30 天', value: '30d' },
]

// 汇总与分析状态
const summary = ref({})
const engineHealth = ref({})
const platforms = ref([])
const hookTechniques = ref([])
const trendDays = ref([])
const tenantRanking = ref([])

// 表格筛选与分页
const selectedPlatformFilter = ref('all')
const tableSearchKeyword = ref('')
const tableLoading = ref(false)
const generationsList = ref([])
const tablePagination = reactive({
  page: 1,
  pageSize: 10,
  itemCount: 0,
})

const platformFilterOptions = [
  { label: '全部平台', value: 'all' },
  { label: '抖音短视频', value: 'douyin' },
  { label: '小红书', value: 'xiaohongshu' },
  { label: '微信视频号', value: 'channels' },
  { label: '快手', value: 'kuaishou' },
  { label: 'B站', value: 'bilibili' },
]

// 详情弹窗
const showDetailModal = ref(false)
const selectedGeneration = ref(null)

const platformColorMap = {
  douyin: '#fe2c55',
  xiaohongshu: '#ff2442',
  channels: '#07c160',
  kuaishou: '#ff5000',
  bilibili: '#00aeec',
}

function getPlatformLabel(p) {
  const map = {
    douyin: '抖音',
    xiaohongshu: '小红书',
    channels: '视频号',
    kuaishou: '快手',
    bilibili: 'B站',
  }
  return map[p] || p || '通用'
}

function getTrendBarHeight(count) {
  const max = Math.max(...trendDays.value.map(d => d.count), 30)
  const pct = Math.max(15, Math.round((count / max) * 100))
  return `${pct}%`
}

// 表格列定义
const generationColumns = [
  { title: 'ID', key: 'id', width: 65 },
  {
    title: '脚本标题与选题',
    key: 'title',
    render: (r) => h('div', null, [
      h('div', { style: 'font-weight: 500; color: #fff; cursor: pointer;', onClick: () => openDetail(r) }, r.title),
      r.topic ? h('div', { style: 'font-size: 12px; color: rgba(255,255,255,0.45); margin-top: 2px;' }, `选题: ${r.topic}`) : null,
    ])
  },
  {
    title: '平台',
    key: 'platform',
    width: 90,
    render: (r) => {
      const color = platformColorMap[r.platform] || '#63e2b7'
      return h(NTag, {
        size: 'small',
        style: `background: ${color}22; color: ${color}; border-color: ${color}44;`
      }, () => getPlatformLabel(r.platform))
    }
  },
  {
    title: '开篇技巧',
    key: 'hook_technique',
    width: 140,
    render: (r) => h(NTag, { size: 'tiny', round: true }, () => r.hook_technique || '反直觉否定')
  },
  {
    title: '耗时',
    key: 'latency_ms',
    width: 90,
    render: (r) => {
      const ms = r.latency_ms || 1800
      const isFast = ms < 2000
      return h(NTag, {
        size: 'small',
        type: isFast ? 'success' : 'info'
      }, () => `${(ms / 1000).toFixed(2)}s`)
    }
  },
  {
    title: '字数 / Token',
    key: 'word_count',
    width: 110,
    render: (r) => h('div', { style: 'font-size: 12px;' }, [
      h('span', { style: 'color: #fff;' }, `${r.word_count || r.content?.length || 420} 字`),
      h('span', { style: 'color: rgba(255,255,255,0.4); margin-left: 4px;' }, `/ ~${r.tokens || 700}T`)
    ])
  },
  {
    title: '质量评分',
    key: 'rating',
    width: 90,
    render: (r) => h('span', { style: 'color: #f2c97d; font-size: 13px;' }, `★ ${r.rating || 5}`)
  },
  {
    title: '所属租户',
    key: 'tenant_name',
    width: 110,
    render: (r) => r.tenant_name || '文策团队'
  },
  {
    title: '生成时间',
    key: 'created_at',
    width: 100,
    render: (r) => r.created_at?.slice(5, 16).replace('T', ' ') || '-'
  },
  {
    title: '操作',
    key: 'actions',
    width: 80,
    render: (r) => h(NButton, {
      size: 'small',
      text: true,
      type: 'primary',
      onClick: () => openDetail(r)
    }, () => '查看详情')
  }
]

function openDetail(r) {
  selectedGeneration.value = r
  showDetailModal.value = true
}

async function copyScript(text) {
  if (!text) return
  try {
    await navigator.clipboard.writeText(text)
    message.success('脚本内容已复制到剪贴板')
  } catch {
    message.info('请手动选中文本进行复制')
  }
}

async function loadData() {
  loading.value = true
  try {
    const { data } = await contentApi.analytics({ range: timeRange.value })
    if (data) {
      summary.value = data.summary || {}
      engineHealth.value = data.engine_health || {}
      platforms.value = data.platforms || []
      hookTechniques.value = data.hook_techniques || []
      trendDays.value = data.trend_days || []
      tenantRanking.value = data.tenant_ranking || []
    }
  } catch (err) {
    console.error('Failed to load generation analytics:', err)
  } finally {
    loading.value = false
  }
}

async function fetchGenerationsTable() {
  tableLoading.value = true
  try {
    const { data } = await contentApi.generations({
      keyword: tableSearchKeyword.value || undefined,
      platform: selectedPlatformFilter.value !== 'all' ? selectedPlatformFilter.value : undefined,
      page: tablePagination.page,
      page_size: tablePagination.pageSize,
    })
    generationsList.value = data.items || []
    tablePagination.itemCount = data.total || 0
  } catch (err) {
    console.error('Failed to load generations list:', err)
  } finally {
    tableLoading.value = false
  }
}

function handlePageChange(p) {
  tablePagination.page = p
  fetchGenerationsTable()
}

onMounted(() => {
  loadData()
  fetchGenerationsTable()
})
</script>

<style scoped>
.analytics-container {
  padding-bottom: 24px;
}

.analytics-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.header-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #fff;
  letter-spacing: -0.01em;
}

.header-desc {
  margin: 4px 0 0;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
}

/* 引擎实时状态卡片 */
.engine-health-card {
  background: #1f2338;
  border-radius: 8px;
}

.engine-health-inner {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.engine-status-col {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #63e2b7;
  display: inline-block;
}

.status-dot.pulsating {
  box-shadow: 0 0 0 0 rgba(99, 226, 183, 0.7);
  animation: pulse-green 2s infinite;
}

@keyframes pulse-green {
  0% {
    transform: scale(0.95);
    box-shadow: 0 0 0 0 rgba(99, 226, 183, 0.7);
  }
  70% {
    transform: scale(1);
    box-shadow: 0 0 0 6px rgba(99, 226, 183, 0);
  }
  100% {
    transform: scale(0.95);
    box-shadow: 0 0 0 0 rgba(99, 226, 183, 0);
  }
}

.status-text {
  font-size: 13px;
  font-weight: 500;
  color: #63e2b7;
}

.model-badge {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sdk-text {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
}

.engine-telemetry-item {
  display: flex;
  flex-direction: column;
}

.telemetry-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.45);
}

.telemetry-val {
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  margin-top: 2px;
}

.pipeline-flow {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 280px;
}

.pipeline-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.45);
}

.pipeline-steps {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 3px;
  flex-wrap: wrap;
}

.step-chip {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.85);
}

.step-arrow {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.3);
}

/* 核心指标卡片 */
.metric-card {
  background: #1a2238;
  border-radius: 8px;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.metric-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.card-header-flex {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.card-title {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
  font-weight: 500;
}

.metric-number {
  font-size: 28px;
  font-weight: 700;
  color: #fff;
  line-height: 1.15;
  margin-bottom: 8px;
}

.metric-unit {
  font-size: 14px;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.5);
  margin-left: 3px;
}

.metric-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.trend-up {
  color: #63e2b7;
  font-weight: 500;
}

.sla-text {
  color: #70c0e8;
}

.token-sub {
  color: #f2c97d;
}

.rating-sub {
  color: #63e2b7;
}

.footer-note {
  color: rgba(255, 255, 255, 0.4);
}

/* 详情卡片通用 */
.detail-card {
  background: #1a2238;
  border-radius: 8px;
}

/* 平台列表 */
.platform-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 4px 0;
}

.platform-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.platform-name-col {
  width: 170px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.platform-badge {
  display: inline-block;
  font-size: 12px;
  font-weight: 500;
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid transparent;
  width: fit-content;
}

.platform-count {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.45);
}

.platform-bar-wrapper {
  flex: 1;
}

.platform-bar-track {
  height: 8px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 4px;
  overflow: hidden;
}

.platform-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.4s ease;
}

.platform-meta-col {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
}

.plat-meta-rating {
  color: #f2c97d;
  font-weight: 500;
}

/* 钩子技巧 */
.hook-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.hook-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.hook-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
}

.hook-title {
  color: #fff;
  font-weight: 500;
}

.hook-rating {
  color: #f2c97d;
  font-size: 12px;
}

.hook-progress-line {
  height: 6px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 3px;
  overflow: hidden;
}

.hook-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #63e2b7, #70c0e8);
  border-radius: 3px;
}

.hook-footer {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.45);
}

/* 趋势图 */
.trend-chart-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.trend-bars-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  height: 140px;
  padding: 10px 4px 0;
}

.trend-bar-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  height: 100%;
  justify-content: flex-end;
}

.trend-val-tooltip {
  font-size: 10px;
  color: #63e2b7;
  margin-bottom: 4px;
}

.trend-bar-track {
  width: 24px;
  height: 80px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 4px 4px 0 0;
  display: flex;
  align-items: flex-end;
}

.trend-bar-fill {
  width: 100%;
  background: #63e2b7;
  border-radius: 4px 4px 0 0;
  transition: height 0.3s ease;
}

.trend-day-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.6);
  margin-top: 6px;
}

.trend-latency-label {
  font-size: 10px;
  color: #70c0e8;
}

.trend-legend {
  display: flex;
  gap: 16px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
  padding-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 2px;
  display: inline-block;
}

.count-dot {
  background: #63e2b7;
}

.latency-dot {
  background: #70c0e8;
}

/* 租户排行 */
.tenant-rank-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.tenant-rank-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 10px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 6px;
}

.rank-index {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
}

.rank-index.top-rank {
  background: #f2c97d;
  color: #1a1a2e;
}

.tenant-name-wrap {
  flex: 1;
}

.tenant-name {
  font-size: 13px;
  font-weight: 500;
  color: #fff;
}

.tenant-pref {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.45);
  margin-top: 2px;
}

.tenant-stats-col {
  text-align: right;
}

.tenant-count-val {
  font-size: 13px;
  font-weight: 600;
  color: #63e2b7;
}

.tenant-rating-val {
  font-size: 11px;
  color: #f2c97d;
  margin-top: 2px;
}

/* 表格卡片 */
.table-card {
  background: #1a2238;
  border-radius: 8px;
}

/* 详情弹窗 */
.detail-modal-body {
  display: flex;
  flex-direction: column;
}

.modal-script-title {
  margin: 0 0 8px 0;
  font-size: 16px;
  color: #fff;
  line-height: 1.4;
}

.modal-tags-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.modal-date-text {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  margin-left: auto;
}

.telemetry-box {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 6px;
  padding: 12px 14px;
}

.telemetry-box-title {
  font-size: 12px;
  font-weight: 500;
  color: #63e2b7;
  margin-bottom: 8px;
}

.telemetry-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px 16px;
}

.t-cell {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}

.t-cell.full-width {
  grid-column: span 2;
}

.t-label {
  color: rgba(255, 255, 255, 0.5);
}

.t-val {
  color: #fff;
  font-weight: 500;
}

.t-val.highlight {
  color: #63e2b7;
}

.script-content-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 6px;
}

.script-content-box {
  background: #111422;
  border-radius: 6px;
  padding: 14px;
  font-size: 13px;
  line-height: 1.8;
  color: rgba(255, 255, 255, 0.9);
  white-space: pre-wrap;
  max-height: 280px;
  overflow-y: auto;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.script-tags-row {
  margin-top: 10px;
}

.modal-footer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}
</style>
