<template>
  <div>
    <div class="page-header">
      <div>
        <div class="page-title">对话历史</div>
        <div class="page-subtitle">每一次文案生成的完整对话记录</div>
      </div>
    </div>

    <n-spin :show="loading">
      <div v-if="gens.length === 0 && !loading" class="empty-state-big">
        <p>暂无对话记录</p>
        <n-button type="primary" @click="$router.push('/')">去生成</n-button>
      </div>

      <div v-else class="history-list">
        <div v-for="g in gens" :key="g.id" class="conv-card" @click="toggle(g.id)">
          <div class="conv-header">
            <n-tag size="small" :type="platformType(g.platform)" :bordered="false">{{ g.platform }}</n-tag>
            <span class="conv-date">{{ formatDate(g.created_at) }}</span>
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
import { ref, reactive, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import { generateApi } from '../api'

const message = useMessage()
const gens = ref([])
const loading = ref(false)
const expanded = reactive({})

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
    const { data } = await generateApi.list(50)
    gens.value = data
  } finally {
    loading.value = false
  }
}

function copy(g) {
  const text = g.output_full || g.output_body || ''
  navigator.clipboard.writeText(text)
  message.success('已复制')
}

function platformType(p) {
  return { douyin: 'error', xiaohongshu: 'success', weixin: 'warning' }[p] || 'default'
}
function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(load)
</script>

<style scoped>
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
