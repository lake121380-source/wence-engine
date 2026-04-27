<template>
  <div>
    <div class="page-header">
      <div>
        <div class="page-title">对话历史</div>
        <div class="page-subtitle">每一次文案生成的完整对话记录</div>
      </div>
    </div>

    <div class="history-toolbar">
      <n-input
        v-model:value="filters.q"
        class="toolbar-search"
        clearable
        placeholder="搜索关键词或文案内容"
        @keydown.enter="load"
        @clear="load"
      />
      <n-select
        v-model:value="filters.platform"
        class="toolbar-platform"
        :options="platformOptions"
        @update:value="load"
      />
      <n-checkbox v-model:checked="filters.likedOnly" @update:checked="load">
        仅看已点赞
      </n-checkbox>
      <n-button type="primary" @click="load">筛选</n-button>
      <n-button quaternary @click="resetFilters">重置</n-button>
    </div>

    <n-spin :show="loading">
      <div v-if="gens.length === 0 && !loading" class="empty-state-big">
        <p>{{ hasFilters ? '没有匹配当前筛选条件的记录' : '暂无对话记录' }}</p>
        <n-button type="primary" @click="$router.push('/app')">去生成</n-button>
      </div>

      <div v-else class="history-list">
        <div v-for="g in gens" :key="g.id" class="conv-card" @click="toggle(g.id)">
          <div class="conv-header">
            <n-tag size="small" :type="platformType(g.platform)" :bordered="false">{{ platformText(g.platform) }}</n-tag>
            <n-tag v-if="(g.rating || 0) >= 4" size="small" type="success" :bordered="false">已点赞</n-tag>
            <span class="conv-date">{{ formatDate(g.created_at) }}</span>
            <n-button size="tiny" quaternary @click.stop="scheduleFromGeneration(g)">排期</n-button>
            <n-button size="tiny" quaternary @click.stop="copy(g)" style="margin-left:auto;">复制文案</n-button>
          </div>

          <!-- 用户消息 -->
          <div class="conv-bubble user-bubble">
            <div class="bubble-role">我</div>
            <div class="bubble-text">{{ g.topic }}</div>
          </div>

          <!-- AI 回复 -->
          <div class="conv-bubble ai-bubble">
            <div class="bubble-role">AI</div>
            <div class="bubble-text" :class="{ truncated: !expanded[g.id] }">{{ g.output_full || g.output_body }}</div>
          </div>

          <div v-if="isLong(g)" class="expand-hint">
            {{ expanded[g.id] ? '收起' : '展开全文' }}
          </div>
        </div>
      </div>
    </n-spin>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useMessage } from 'naive-ui'
import { generateApi, scheduleApi } from '../api'

const message = useMessage()
const gens = ref([])
const loading = ref(false)
const expanded = reactive({})
const filters = reactive({
  q: '',
  platform: '',
  likedOnly: false,
})

const platformOptions = [
  { label: '全部平台', value: '' },
  { label: '抖音', value: 'douyin' },
  { label: '小红书', value: 'xiaohongshu' },
  { label: '视频号', value: 'weixin' },
]

const hasFilters = computed(() => !!(filters.q.trim() || filters.platform || filters.likedOnly))

function toggle(id) {
  expanded[id] = !expanded[id]
}

function isLong(g) {
  const text = g.output_full || g.output_body || ''
  return text.length > 200 || text.split('\n').length > 6
}

async function load() {
  loading.value = true
  try {
    const params = {
      limit: 100,
      q: filters.q.trim() || undefined,
      platform: filters.platform || undefined,
      liked_only: filters.likedOnly || undefined,
    }
    const { data } = await generateApi.list(params)
    gens.value = data || []
  } catch {
    message.error('历史记录加载失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.q = ''
  filters.platform = ''
  filters.likedOnly = false
  load()
}

function copy(g) {
  const text = g.output_full || g.output_body || ''
  navigator.clipboard.writeText(text).then(() => {
    message.success('已复制')
  }).catch(() => {
    message.error('复制失败，请检查浏览器权限')
  })
}

async function scheduleFromGeneration(g) {
  const base = new Date()
  base.setDate(base.getDate() + 1)
  base.setHours(20, 0, 0, 0)

  try {
    await scheduleApi.create({
      title: (g.topic || '文案排期').slice(0, 80),
      content: g.output_full || g.output_body || '',
      platform: g.platform || 'douyin',
      scheduled_date: base.toISOString(),
      status: 'draft',
      generation_id: g.id,
    })
    message.success('已加入文案日历（明晚 20:00）')
  } catch (e) {
    message.error(e.response?.data?.detail || '加入日历失败')
  }
}

function platformType(p) {
  return { douyin: 'error', xiaohongshu: 'success', weixin: 'warning' }[p] || 'default'
}
function platformText(p) {
  return { douyin: '抖音', xiaohongshu: '小红书', weixin: '视频号' }[p] || (p || '未知平台')
}
function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(load)
</script>

<style scoped>
.history-toolbar {
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.toolbar-search {
  width: 320px;
  max-width: 100%;
}
.toolbar-platform {
  width: 136px;
}
.history-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.conv-card {
  background: var(--c-bg-elevated, #fff);
  border: 1px solid var(--c-border, rgba(0,0,0,.06));
  border-radius: var(--radius-lg, 12px);
  padding: 16px;
  cursor: pointer;
  transition: border-color .2s, box-shadow .2s;
  box-shadow: 0 1px 2px rgba(0,0,0,.04);
}
.conv-card:hover {
  border-color: rgba(99,102,241,.3);
  box-shadow: 0 4px 16px rgba(99,102,241,.08);
}
.conv-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.conv-date {
  font-size: 11px;
  color: #94a3b8;
}
.conv-bubble {
  margin-bottom: 10px;
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 13px;
  line-height: 1.7;
}
.user-bubble {
  background: rgba(99,102,241,.06);
  border: 1px solid rgba(99,102,241,.1);
}
.ai-bubble {
  background: var(--c-bg-soft, #f8fafc);
  border: 1px solid rgba(0,0,0,.04);
}
.bubble-role {
  font-size: 11px;
  font-weight: 600;
  color: #94a3b8;
  margin-bottom: 4px;
}
.bubble-text {
  color: var(--c-text-2, #374151);
  white-space: pre-wrap;
  word-break: break-word;
}
.bubble-text.truncated {
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.expand-hint {
  text-align: center;
  font-size: 12px;
  color: #6366f1;
  padding-top: 4px;
}
.empty-state-big {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 80px 0;
  color: #cbd5e1;
}
</style>
