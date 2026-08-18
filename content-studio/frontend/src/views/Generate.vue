<template>
  <div class="generate-page">
    <div class="page-header">
      <div>
        <div class="page-title">生成文案</div>
        <div class="page-subtitle">
          参考内容，自由组合图、文、音、视频多元素。输入中使用 @ 引用素材，像即梦一样进行组合创作。
        </div>
      </div>
      <n-space align="center">
        <n-tag v-if="activePreset" type="info" :bordered="false" size="small">
          已启用模板：{{ activePreset.name }}
        </n-tag>
        <n-button secondary @click="openConfig = true">
          <template #icon><n-icon><OptionsOutline /></n-icon></template>
          配置
        </n-button>
        <n-button quaternary @click="openAtPicker">插入 @ 引用</n-button>
        <n-button quaternary @click="resetSession">新会话</n-button>
      </n-space>
    </div>

    <section class="card gen-shell">
      <div ref="chatListRef" class="chat-list">
        <div
          v-for="msg in messages"
          :key="msg.id"
          :id="`msg-${msg.id}`"
          class="chat-msg"
          :class="msg.role === 'user' ? 'is-user' : 'is-assistant'"
        >
          <div class="chat-avatar">{{ msg.role === 'user' ? '你' : 'AI' }}</div>

          <div class="chat-bubble" :class="{ 'result-compact': msg.type === 'result' && !isResultExpanded(msg.id) }">
            <template v-if="msg.type === 'result'">
              <div class="result-head">
                <div class="result-title">已生成一版文案</div>
                <n-space size="small">
                  <n-button
                    v-if="bodyIsLong(msg.data)"
                    size="tiny"
                    quaternary
                    @click="toggleResultExpand(msg.id)"
                  >
                    {{ isResultExpanded(msg.id) ? '收起' : '展开' }}
                  </n-button>
                  <n-button size="tiny" secondary @click="copyResult(msg)">
                    <template #icon><n-icon><CopyOutline /></n-icon></template>
                    复制
                  </n-button>
                  <n-button size="tiny" quaternary :disabled="generating" @click="regenerate(msg.payload)">
                    <template #icon><n-icon><RefreshOutline /></n-icon></template>
                    再生成
                  </n-button>
                </n-space>
              </div>

              <div class="result-block">
                <div class="result-value body" :class="{ compact: !isResultExpanded(msg.id) }">
                  <div
                    v-for="(line, idx) in (isResultExpanded(msg.id) ? splitFullText(msg.data) : previewFullText(msg.data))"
                    :key="idx"
                  >
                    {{ line }}
                  </div>
                </div>
              </div>

              <div v-if="msg.data.tags?.length && isResultExpanded(msg.id)" class="result-block">
                <div class="result-label">标签</div>
                <n-space size="small" style="margin-top:8px;">
                  <n-tag v-for="t in msg.data.tags" :key="t" :bordered="false" size="small">#{{ t }}</n-tag>
                </n-space>
              </div>


            </template>

            <template v-else-if="msg.type === 'pending'">
              <div class="pending-row">
                <n-spin size="small" />
                <span>正在生成中...</span>
              </div>
            </template>

            <template v-else-if="msg.type === 'streaming'">
              <div class="streaming-row">
                <n-spin size="small" style="flex-shrink:0;" />
                <pre class="streaming-text">{{ msg.text }}</pre>
              </div>
            </template>

            <template v-else>
              <div class="chat-text">{{ msg.text }}</div>
              <div v-if="msg.refs?.length" class="chat-refs">
                <n-tag
                  v-for="r in msg.refs"
                  :key="r.key"
                  size="small"
                  :bordered="false"
                  type="info"
                >
                  @{{ compactRefLabel(r) }}
                </n-tag>
              </div>
            </template>
          </div>
        </div>
      </div>

      <div class="composer-wrap">
        <div v-if="materialBlocks.length" class="material-board">
          <div
            v-for="(block, idx) in materialBlocks"
            :key="block.key"
            class="material-card"
            :class="{ dragging: dragState.from === idx }"
            draggable="true"
            @dragstart="onBlockDragStart(idx)"
            @dragover.prevent
            @drop.prevent="onBlockDrop(idx)"
            @dragend="onBlockDragEnd"
          >
            <div class="material-handle" title="拖拽排序">
              <n-icon size="16"><ReorderThreeOutline /></n-icon>
            </div>

            <div class="material-thumb" :class="{ placeholder: !block.thumb }">
              <img v-if="block.thumb" :src="block.thumb" :alt="block.label" loading="lazy" />
              <span v-else>{{ block.badge }}</span>
            </div>

            <div class="material-main">
              <div class="material-title">@{{ block.label }}</div>
              <div class="material-source">{{ block.source }}</div>
            </div>

            <n-button size="tiny" quaternary @click="removeReference(block)">移除</n-button>
          </div>
        </div>

        <div class="composer-main">
          <textarea
            ref="composerRef"
            v-model="promptText"
            class="composer-input"
            placeholder="例如：@博主:李老师 模仿 @视频:爆款拆解 的动作节奏，音色参考 @观点:品牌调性，生成视频号口播文案。"
            @input="handleComposerInput"
            @click="updateMentionState"
            @keyup="updateMentionState"
            @blur="handleComposerBlur"
            @keydown.enter.exact.prevent="sendPrompt"
          />

          <n-button class="send-btn" type="primary" :loading="generating" @click="sendPrompt">
            <template #icon><n-icon><SparklesOutline /></n-icon></template>
            生成
          </n-button>

          <div v-if="mentionState.visible" class="mention-panel">
            <button
              v-for="item in mentionOptions"
              :key="item.key"
              class="mention-item"
              @mousedown.prevent="insertMention(item)"
            >
              <div class="mention-thumb" :class="{ placeholder: !item.thumb }">
                <img v-if="item.thumb" :src="item.thumb" :alt="item.label" loading="lazy" />
                <span v-else>{{ item.badge }}</span>
              </div>

              <div class="mention-main">
                <div class="mention-title">@{{ item.label }}</div>
                <div class="mention-source">{{ item.source }}</div>
              </div>

              <n-tag size="tiny" :bordered="false">{{ typeLabel(item.type) }}</n-tag>
            </button>
            <div v-if="!mentionOptions.length" class="mention-empty">没有匹配到可引用素材</div>
          </div>
        </div>

        <div class="composer-foot">
          <n-space>
            <n-button size="tiny" quaternary @click="openAtPicker">@ 引用素材</n-button>
            <n-button size="tiny" quaternary @click="openConfig = true">模板与配置</n-button>
            <n-button size="tiny" quaternary @click="clearReferences">清空素材块</n-button>
          </n-space>
          <div class="composer-hint">Enter 发送，Shift + Enter 换行。素材块可拖拽调整顺序。</div>
        </div>
      </div>
    </section>

    <n-drawer v-model:show="openConfig" :width="440" placement="right">
      <n-drawer-content title="模板与配置" closable>
        <div class="preset-title-row">
          <div class="drawer-subtitle">预设模板</div>
          <n-button size="tiny" quaternary @click="activePresetId = 'custom'">使用自定义</n-button>
        </div>

        <div class="preset-grid">
          <button
            v-for="p in presets"
            :key="p.id"
            class="preset-card"
            :class="{ active: activePresetId === p.id }"
            @click="applyPreset(p)"
          >
            <div class="preset-name">{{ p.name }}</div>
            <div class="preset-desc">{{ p.desc }}</div>
            <div class="preset-platform">{{ platformLabel(p.platform) }}</div>
          </button>
        </div>

        <n-divider style="margin: 16px 0" />

        <n-form label-placement="top" :show-feedback="false" size="large">
          <n-form-item label="目标平台">
            <n-radio-group v-model:value="config.platform" button-style="solid">
              <n-radio-button v-for="p in platforms" :key="p.value" :value="p.value">{{ p.label }}</n-radio-button>
            </n-radio-group>
          </n-form-item>

          <n-form-item label="风格模板（单选）">
            <n-select v-model:value="config.style_template_id" :options="styleOptions" clearable placeholder="可不选" />
          </n-form-item>

          <n-form-item label="参考博主（多选）">
            <n-select v-model:value="config.creator_ids" multiple :options="creatorOptions" clearable placeholder="可不选" />
          </n-form-item>

          <n-form-item label="文档资料（多选）">
            <n-select v-model:value="config.product_doc_ids" multiple :options="docOptions" clearable placeholder="可不选" />
          </n-form-item>

          <n-form-item label="运营观点（多选）">
            <n-select v-model:value="config.viewpoint_ids" multiple :options="viewpointOptions" clearable placeholder="可不选" />
          </n-form-item>

          <n-form-item label="爆款分析（多选）">
            <n-select v-model:value="config.viral_analysis_ids" multiple :options="viralAnalysisOptions" clearable placeholder="可不选" />
          </n-form-item>
        </n-form>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { useMessage } from 'naive-ui'
import {
  CopyOutline,
  OptionsOutline,
  RefreshOutline,
  ReorderThreeOutline,
  SparklesOutline,
} from '@vicons/ionicons5'
import {
  analyzerApi,
  creatorsApi,
  documentsApi,
  generateApi,
  styleApi,
  topicsApi,
  viewpointsApi,
} from '../api'
import { useGenerateStore } from '../stores/generate.js'
import { useAuthStore } from '../stores/auth.js'
import { useRouter } from 'vue-router'

const message = useMessage()
const generateStore = useGenerateStore()
const authStore = useAuthStore()
const router = useRouter()

const generating = ref(false)
const openConfig = ref(false)
const promptText = ref('')
const quickTopics = ref([])
const chatListRef = ref(null)
const composerRef = ref(null)

const presets = [
  {
    id: 'weixin_oral',
    name: '视频号口播',
    platform: 'weixin',
    desc: '故事感开场 + 观点递进 + 强行动召唤',
    instruction: '面向视频号口播：句子更完整，节奏稳，开头 3 秒先抛冲突，结尾明确引导私信或关注。',
    example: '写一版视频号口播文案，语气真诚有力量，适合创始人IP输出。',
  },
  {
    id: 'douyin_fast',
    name: '抖音短平快',
    platform: 'douyin',
    desc: '高密度信息点 + 金句 + 强节奏转折',
    instruction: '面向抖音：前三秒钩子要狠，句子短，信息密度高，结尾引导点赞评论。',
    example: '写一版抖音快节奏文案，开头直接打痛点，30秒内讲清。',
  },
  {
    id: 'xhs_seed',
    name: '小红书种草',
    platform: 'xiaohongshu',
    desc: '真实体验表达 + 场景化细节 + 软性转化',
    instruction: '面向小红书：真实体验口吻，场景细节具体，强调对比和可执行建议，避免硬广。',
    example: '写一版小红书种草文案，重点突出使用前后对比和真实感受。',
  },
]

const activePresetId = ref('custom')
const activePreset = computed(() => presets.find((p) => p.id === activePresetId.value) || null)

const config = reactive({
  platform: 'douyin',
  style_template_id: null,
  creator_ids: [],
  product_doc_ids: [],
  viewpoint_ids: [],
  viral_analysis_ids: [],
})

const platforms = [
  { label: '抖音', value: 'douyin' },
  { label: '小红书', value: 'xiaohongshu' },
  { label: '视频号', value: 'weixin' },
]

const styles = ref([])
const creators = ref([])
const docs = ref([])
const viewpoints = ref([])
const viralAnalyses = ref([])

const styleOptions = computed(() =>
  styles.value.map((s) => ({
    label: s.content_type ? `[${s.content_type}] ${s.name}` : s.name,
    value: s.id,
  }))
)
const creatorOptions = computed(() => creators.value.map((c) => ({ label: `${c.nickname} (${c.platform})`, value: c.id })))
const docOptions = computed(() => docs.value.map((d) => ({ label: d.name, value: d.id })))
const viewpointOptions = computed(() => viewpoints.value.map((v) => ({ label: v.title, value: v.id })))
const viralAnalysisOptions = computed(() =>
  viralAnalyses.value.map((a) => ({
    label: a.title || `视频分析 #${a.id}`,
    value: a.id,
  }))
)

let msgSeq = 1
const makeId = () => msgSeq++

const messages = ref([
  {
    id: makeId(),
    role: 'assistant',
    type: 'text',
    text: '你可以这样输入：@博主:某某 模仿 @视频:某条爆款，结合 @文档:产品资料，生成一版可直接拍摄的文案。',
  },
])

const mentionState = reactive({
  visible: false,
  query: '',
  start: 0,
  cursor: 0,
})

const materialBlocks = ref([])
const dragState = reactive({ from: -1 })
const resultExpanded = reactive({})

function platformLabel(platform) {
  return platforms.find((x) => x.value === platform)?.label || (platform || '未知平台')
}

function formatNum(n) {
  if (!n) return '0'
  if (n >= 10000) return `${(n / 10000).toFixed(1)}w`
  return String(n)
}

function formatFollower(n) {
  if (!n) return '0 粉丝'
  if (n >= 10000) return `${(n / 10000).toFixed(1)}w 粉丝`
  return `${n} 粉丝`
}

function shortBadge(type) {
  return {
    style: '风',
    creator: '博',
    doc: '文',
    viewpoint: '观',
    analysis: '爆',
  }[type] || '素'
}

function typeLabel(type) {
  return {
    style: '风格模板',
    creator: '博主',
    doc: '文档',
    viewpoint: '观点',
    analysis: '爆款分析',
  }[type] || '素材'
}

const mentionPool = computed(() => {
  const list = []

  styles.value.forEach((s) => {
    list.push({
      key: `style-${s.id}`,
      type: 'style',
      id: s.id,
      label: `风格:${s.name}`,
      source: `${typeLabel('style')} · ${platformLabel(s.platform)}`,
      search: `${s.name} ${s.content_type || ''}`,
      thumb: '',
      badge: shortBadge('style'),
    })
  })

  creators.value.forEach((c) => {
    list.push({
      key: `creator-${c.id}`,
      type: 'creator',
      id: c.id,
      label: `博主:${c.nickname}`,
      source: `${platformLabel(c.platform)} · ${formatFollower(c.follower_count)}`,
      search: `${c.nickname} ${c.platform}`,
      thumb: c.avatar_url || '',
      badge: shortBadge('creator'),
    })
  })

  docs.value.forEach((d) => {
    const sourceType = d.source_type || '资料库'
    const fileType = (d.file_type || '文档').toUpperCase()
    list.push({
      key: `doc-${d.id}`,
      type: 'doc',
      id: d.id,
      label: `文档:${d.name}`,
      source: `${fileType} · ${sourceType}`,
      search: `${d.name} ${d.file_type || ''}`,
      thumb: '',
      badge: shortBadge('doc'),
    })
  })

  viewpoints.value.forEach((v) => {
    list.push({
      key: `viewpoint-${v.id}`,
      type: 'viewpoint',
      id: v.id,
      label: `观点:${v.title}`,
      source: `${v.category || '运营观点'} · 个人素材`,
      search: `${v.title} ${v.content || ''}`,
      thumb: '',
      badge: shortBadge('viewpoint'),
    })
  })

  viralAnalyses.value.forEach((a) => {
    const title = a.title || `视频分析 #${a.id}`
    list.push({
      key: `analysis-${a.id}`,
      type: 'analysis',
      id: a.id,
      label: `视频:${title}`,
      source: a.source || '爆款分析素材',
      search: `${title} ${a.source || ''}`,
      thumb: a.cover_url || a.author_avatar || '',
      badge: shortBadge('analysis'),
    })
  })

  return list
})

const mentionOptions = computed(() => {
  const q = mentionState.query.trim().toLowerCase()
  const pool = mentionPool.value
  if (!q) return pool.slice(0, 8)
  return pool
    .filter((x) => x.search.toLowerCase().includes(q) || x.label.toLowerCase().includes(q) || x.source.toLowerCase().includes(q))
    .slice(0, 8)
})

function findPoolItem(type, id) {
  return mentionPool.value.find((x) => x.type === type && x.id === id)
}

function toFallbackItem(type, id) {
  return {
    key: `${type}-${id}`,
    type,
    id,
    label: `${typeLabel(type)}#${id}`,
    source: '已选素材',
    thumb: '',
    badge: shortBadge(type),
  }
}

function selectedItemsFromConfig() {
  const selected = []
  if (config.style_template_id) selected.push({ type: 'style', id: config.style_template_id })
  config.creator_ids.forEach((id) => selected.push({ type: 'creator', id }))
  config.product_doc_ids.forEach((id) => selected.push({ type: 'doc', id }))
  config.viewpoint_ids.forEach((id) => selected.push({ type: 'viewpoint', id }))
  config.viral_analysis_ids.forEach((id) => selected.push({ type: 'analysis', id }))
  return selected.map((s) => findPoolItem(s.type, s.id) || toFallbackItem(s.type, s.id))
}

function syncBlocksFromConfig() {
  const selected = selectedItemsFromConfig()
  const selectedMap = new Map(selected.map((x) => [x.key, x]))
  const next = materialBlocks.value
    .filter((x) => selectedMap.has(x.key))
    .map((x) => ({ ...x, ...selectedMap.get(x.key) }))

  selected.forEach((x) => {
    if (!next.some((i) => i.key === x.key)) next.push(x)
  })

  materialBlocks.value = next
}

function attachReference(item) {
  if (item.type === 'style') {
    config.style_template_id = item.id
  } else {
    const map = {
      creator: 'creator_ids',
      doc: 'product_doc_ids',
      viewpoint: 'viewpoint_ids',
      analysis: 'viral_analysis_ids',
    }
    const field = map[item.type]
    if (field && !config[field].includes(item.id)) config[field].push(item.id)
  }
  syncBlocksFromConfig()
}

function removeReference(block) {
  if (block.type === 'style') {
    config.style_template_id = null
  } else {
    const map = {
      creator: 'creator_ids',
      doc: 'product_doc_ids',
      viewpoint: 'viewpoint_ids',
      analysis: 'viral_analysis_ids',
    }
    const field = map[block.type]
    if (field) config[field] = config[field].filter((x) => x !== block.id)
  }
  syncBlocksFromConfig()
}

function clearReferences() {
  config.style_template_id = null
  config.creator_ids = []
  config.product_doc_ids = []
  config.viewpoint_ids = []
  config.viral_analysis_ids = []
  materialBlocks.value = []
}

function onBlockDragStart(index) {
  dragState.from = index
}

function onBlockDrop(index) {
  const from = dragState.from
  if (from < 0 || from === index) return
  const arr = [...materialBlocks.value]
  const [item] = arr.splice(from, 1)
  arr.splice(index, 0, item)
  materialBlocks.value = arr
  dragState.from = -1
}

function onBlockDragEnd() {
  dragState.from = -1
}

function isResultExpanded(id) {
  return !!resultExpanded[id]
}

function toggleResultExpand(id) {
  resultExpanded[id] = !resultExpanded[id]
  scrollToMessage(id)
}

function applyPreset(preset) {
  activePresetId.value = preset.id
  config.platform = preset.platform
  if (!promptText.value.trim()) promptText.value = preset.example
  message.success(`已应用模板：${preset.name}`)
}

// 解析输入框中当前存在的 compact token，反向同步 config
function parseTokensInText(text) {
  // 匹配 @视频#数字  @博主:xxx  @文档:xxx  @观点:xxx  @风格:xxx
  const tokens = []
  const re = /@(视频#(\d+)|博主:([^\s@]+)|文档:([^\s@]+)|观点:([^\s@]+)|风格:([^\s@]+))/g
  let m
  while ((m = re.exec(text)) !== null) {
    if (m[2]) tokens.push({ type: 'analysis', hint: parseInt(m[2]) }) // 直接 id
    else if (m[3]) tokens.push({ type: 'creator', hint: m[3] })
    else if (m[4]) tokens.push({ type: 'doc', hint: m[4] })
    else if (m[5]) tokens.push({ type: 'viewpoint', hint: m[5] })
    else if (m[6]) tokens.push({ type: 'style', hint: m[6] })
  }
  return tokens
}

function syncRefsFromText() {
  const tokens = parseTokensInText(promptText.value)

  // 对于 analysis：直接匹配 id
  const analysisIds = tokens.filter(t => t.type === 'analysis').map(t => t.hint)
  config.viral_analysis_ids = config.viral_analysis_ids.filter(id => analysisIds.includes(id))

  // 对于其他类型：用 hint（名称片段）去 mentionPool 里找匹配
  function filterByHint(type, oldIds) {
    const hints = tokens.filter(t => t.type === type).map(t => t.hint.toLowerCase())
    if (hints.length === 0) return []
    return oldIds.filter(id => {
      const poolItem = mentionPool.value.find(x => x.type === type && x.id === id)
      if (!poolItem) return false
      const name = (poolItem.label || '').replace(/^[^:]+:/, '').slice(0, 10).toLowerCase()
      return hints.some(h => name.startsWith(h) || h.startsWith(name))
    })
  }

  config.creator_ids = filterByHint('creator', config.creator_ids)
  config.product_doc_ids = filterByHint('doc', config.product_doc_ids)
  config.viewpoint_ids = filterByHint('viewpoint', config.viewpoint_ids)
  if (config.style_template_id) {
    const styleHints = tokens.filter(t => t.type === 'style').map(t => t.hint.toLowerCase())
    if (styleHints.length === 0) {
      config.style_template_id = null
    } else {
      const poolItem = mentionPool.value.find(x => x.type === 'style' && x.id === config.style_template_id)
      if (poolItem) {
        const name = (poolItem.label || '').replace(/^[^:]+:/, '').slice(0, 10).toLowerCase()
        if (!styleHints.some(h => name.startsWith(h) || h.startsWith(name))) {
          config.style_template_id = null
        }
      }
    }
  }

  syncBlocksFromConfig()
}

function handleComposerInput() {
  updateMentionState()
  syncRefsFromText()
}

function handleComposerBlur() {
  window.setTimeout(() => {
    mentionState.visible = false
  }, 120)
}

function updateMentionState() {
  const el = composerRef.value
  if (!el) return
  const cursor = el.selectionStart ?? promptText.value.length
  const before = promptText.value.slice(0, cursor)
  const match = before.match(/@([^\s@]*)$/)
  if (!match) {
    mentionState.visible = false
    mentionState.query = ''
    return
  }
  mentionState.visible = true
  mentionState.query = match[1]
  mentionState.start = cursor - match[0].length
  mentionState.cursor = cursor
}

function compactMentionToken(item) {
  // label 形如 "博主:李老师" / "视频:某标题" / "风格:xxx"
  // analysis 直接用短 ID 形式避免超长标题进输入框
  if (item.type === 'analysis') return `@视频#${item.id}`
  // 其他类型取 label 冒号后的名称，最多 10 个字符
  const name = (item.label || '').replace(/^[^:]+:/, '').slice(0, 10)
  const prefix = { creator: '博主', doc: '文档', viewpoint: '观点', style: '风格' }[item.type] || '素材'
  return `@${prefix}:${name || item.id}`
}

function insertMention(item) {
  const el = composerRef.value
  if (!el) return
  const cursor = el.selectionStart ?? mentionState.cursor
  const before = promptText.value.slice(0, mentionState.start)
  const after = promptText.value.slice(cursor)
  const token = compactMentionToken(item) + ' '
  promptText.value = `${before}${token}${after}`
  attachReference(item)
  mentionState.visible = false

  nextTick(() => {
    el.focus()
    const pos = (before + token).length
    el.setSelectionRange(pos, pos)
  })
}

function openAtPicker() {
  const el = composerRef.value
  if (!el) return
  const start = el.selectionStart ?? promptText.value.length
  const end = el.selectionEnd ?? start
  const before = promptText.value.slice(0, start)
  const after = promptText.value.slice(end)
  promptText.value = `${before}@${after}`

  nextTick(() => {
    el.focus()
    const cursor = start + 1
    el.setSelectionRange(cursor, cursor)
    updateMentionState()
  })
}

function idsByType(type) {
  return materialBlocks.value.filter((x) => x.type === type).map((x) => x.id)
}

function buildTopic() {
  const baseText = promptText.value.trim()
  const refsText = materialBlocks.value.map((r) => `@${r.label}`).join(' ')
  const base = baseText || refsText
  if (!base) return ''

  if (activePreset.value?.instruction) {
    return `${base}\n\n【模板要求】${activePreset.value.instruction}`
  }
  return base
}

function makePayload() {
  const styleBlock = materialBlocks.value.find((x) => x.type === 'style')

  // 构建对话历史（最近 3 轮）
  const history = []
  const pastMsgs = messages.value.filter((m) => m.type === 'text' || m.type === 'result')
  const recent = pastMsgs.slice(-6)
  for (const m of recent) {
    if (m.role === 'user' && m.text) {
      history.push({ role: 'user', content: m.text })
    } else if (m.role === 'assistant' && m.type === 'result' && m.data) {
      // 把上一次生成结果作为 assistant 回复
      const d = m.data
      history.push({
        role: 'assistant',
        content: JSON.stringify({
          title: d.title,
          hook: d.hook,
          body: d.body,
          cta: d.cta,
          tags: d.tags,
        }),
      })
    }
  }

  return {
    topic: buildTopic(),
    platform: config.platform,
    style_template_id: styleBlock?.id || config.style_template_id,
    creator_ids: idsByType('creator'),
    product_doc_ids: idsByType('doc'),
    viewpoint_ids: idsByType('viewpoint'),
    viral_analysis_ids: idsByType('analysis'),
    history,
  }
}

async function sendPrompt() {
  if (generating.value) return

  if (!authStore.isSubscriptionActive) {
    message.warning('订阅已到期，请先续费')
    router.push('/pricing')
    return
  }

  const topic = buildTopic()
  if (!topic) {
    message.warning('请先输入需求，或至少 @ 一个参考素材')
    return
  }

  const refsSnapshot = materialBlocks.value.map((x) => ({ ...x }))
  const userMsgId = makeId()
  messages.value.push({
    id: userMsgId,
    role: 'user',
    type: 'text',
    text: promptText.value.trim() || '按当前素材块顺序生成一版文案',
    refs: refsSnapshot,
  })
  scrollToMessage(userMsgId)

  const payload = makePayload()
  promptText.value = ''
  mentionState.visible = false
  await runGenerate(payload)
}

async function runGenerate(payload) {
  generating.value = true
  const streamMsgId = makeId()
  messages.value.push({ id: streamMsgId, role: 'assistant', type: 'streaming', text: '' })
  scrollToBottom()

  try {
    const response = await generateApi.generateStream(payload)
    if (!response.ok) {
      let detail = '生成失败，请稍后重试。'
      try {
        const errBody = await response.json()
        detail = errBody.detail || detail
      } catch {}
      throw new Error(detail)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let finalResult = null

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      // 解析 SSE 事件
      const lines = buffer.split('\n')
      buffer = lines.pop() // 保留未完成的行

      for (const line of lines) {
        if (line.startsWith('event: done')) {
          // 下一行是 data
          continue
        }
        if (line.startsWith('event: error')) {
          continue
        }
        if (line.startsWith('data: ')) {
          const raw = line.slice(6)
          try {
            const parsed = JSON.parse(raw)
            if (typeof parsed === 'string') {
              // 文本 chunk
              const idx = messages.value.findIndex((m) => m.id === streamMsgId)
              if (idx >= 0) {
                messages.value[idx].text += parsed
              }
              scrollToBottom()
            } else if (parsed && typeof parsed === 'object' && parsed.id) {
              // done 事件的完整结果
              finalResult = parsed
            }
          } catch {}
        }
      }
    }

    // 替换 streaming 消息为 result 消息
    const idx = messages.value.findIndex((m) => m.id === streamMsgId)
    if (idx >= 0 && finalResult) {
      const newId = makeId()
      messages.value[idx] = {
        id: newId,
        role: 'assistant',
        type: 'result',
        payload,
        data: { ...finalResult },
      }
      resultExpanded[newId] = false
      scrollToMessage(newId)
    }

    try {
      const { data: topics } = await topicsApi.list({ status: '待评审', limit: 4 })
      quickTopics.value = topics || []
    } catch {
      quickTopics.value = []
    }
  } catch (e) {
    const idx = messages.value.findIndex((m) => m.id === streamMsgId)
    if (idx >= 0) {
      messages.value[idx] = {
        id: makeId(),
        role: 'assistant',
        type: 'text',
        text: e.message || '生成失败，请稍后重试。',
      }
    }
  } finally {
    generating.value = false
    scrollToBottom()
  }
}

async function regenerate(payload) {
  if (!payload || generating.value) return
  messages.value.push({
    id: makeId(),
    role: 'user',
    type: 'text',
    text: '再生成一版（沿用同样配置）',
  })
  await runGenerate({ ...payload })
}



function copyResult(msg) {
  const data = msg?.data
  if (!data) return
  const text = buildFullText(data)
  navigator.clipboard.writeText(text)
  message.success('已复制到剪贴板')
}

function buildFullText(data) {
  const parts = []
  if (data.title) parts.push(data.title)
  if (data.hook) parts.push(data.hook)
  if (data.body) parts.push(data.body)
  if (data.cta) parts.push(data.cta)
  return parts.join('\n\n')
}

function splitFullText(data) {
  const text = buildFullText(data)
  if (!text) return ['（空）']
  const lines = text.split('\n').map((x) => x.trim()).filter(Boolean)
  return lines.length ? lines : [text]
}

function previewFullText(data) {
  const lines = splitFullText(data)
  if (lines.length <= 6) return lines
  return lines.slice(0, 6)
}

function bodyIsLong(data) {
  const lines = splitFullText(data)
  return lines.length > 6 || buildFullText(data).length > 200
}

function compactRefLabel(ref) {
  if (ref.type === 'analysis') return `视频#${ref.id}`
  const label = ref.label || ''
  if (label.length <= 18) return label
  return `${label.slice(0, 18)}...`
}

function resetSession() {
  messages.value = [
    {
      id: makeId(),
      role: 'assistant',
      type: 'text',
      text: '新会话已开启。继续用 @ 素材块自由组合吧。',
    },
  ]
  promptText.value = ''
  quickTopics.value = []
  mentionState.visible = false
  message.success('已开启新会话')
  scrollToBottom()
}

function useQuickTopic(topic) {
  promptText.value = topic.title || ''
  if (topic.platform && ['douyin', 'xiaohongshu', 'weixin'].includes(topic.platform)) {
    config.platform = topic.platform
  }
  nextTick(() => composerRef.value?.focus())
}

function scrollToBottom() {
  nextTick(() => {
    const el = chatListRef.value
    if (!el) return
    el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
  })
}

function scrollToMessage(id) {
  nextTick(() => {
    const el = document.getElementById(`msg-${id}`)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    } else {
      scrollToBottom()
    }
  })
}

async function loadOptions() {
  try {
    const [s, c, d, vp] = await Promise.all([
      styleApi.list(),
      creatorsApi.list(),
      documentsApi.list(),
      viewpointsApi.list({ active_only: true }),
    ])
    styles.value = s.data || []
    creators.value = c.data || []
    docs.value = d.data || []
    viewpoints.value = vp.data || []
  } catch {
    message.warning('部分配置数据加载失败，可刷新重试')
  }

  try {
    const { data } = await analyzerApi.listAnalyses()
    viralAnalyses.value = data || []
  } catch {
    viralAnalyses.value = []
  }

  if (generateStore.prefillTopic) {
    const prefill = generateStore.prefillTopic
    promptText.value = prefill.title || ''
    if (prefill.platform && ['douyin', 'xiaohongshu', 'weixin'].includes(prefill.platform)) {
      config.platform = prefill.platform
    }
    generateStore.clearPrefillTopic()
  }

  syncBlocksFromConfig()
}

watch(() => config.style_template_id, syncBlocksFromConfig)
watch(() => config.creator_ids.slice(), syncBlocksFromConfig)
watch(() => config.product_doc_ids.slice(), syncBlocksFromConfig)
watch(() => config.viewpoint_ids.slice(), syncBlocksFromConfig)
watch(() => config.viral_analysis_ids.slice(), syncBlocksFromConfig)
watch(mentionPool, syncBlocksFromConfig)

onMounted(async () => {
  await loadOptions()
  nextTick(() => {
    const el = chatListRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
})
</script>

<style scoped>
.generate-page {
  min-height: calc(100vh - 140px);
}

.gen-shell {
  padding: 0;
  height: calc(100vh - 220px);
  max-height: calc(100vh - 220px);
  overflow: hidden;
  display: grid;
  grid-template-rows: 1fr auto;
}

.chat-list {
  padding: 14px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.chat-msg {
  display: grid;
  grid-template-columns: 40px minmax(0, 1fr);
  gap: 10px;
  animation: msgIn var(--duration-normal, 200ms) var(--ease-default, ease);
}

.chat-msg.is-user {
  grid-template-columns: minmax(0, 1fr) 40px;
}

.chat-msg.is-user .chat-avatar {
  grid-column: 2;
  background: var(--c-primary, #2563EB);
}

.chat-msg.is-user .chat-bubble {
  grid-column: 1;
  justify-self: end;
  background: var(--c-primary-bg, rgba(37, 99, 235, 0.06));
  border-color: rgba(37, 99, 235, 0.2);
}

.chat-avatar {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: #0f766e;
  color: #fff;
  display: grid;
  place-items: center;
  font-size: 11px;
  font-weight: 700;
}

.chat-bubble {
  max-width: min(960px, 100%);
  border-radius: var(--radius-lg, 12px);
  border: 1px solid var(--c-border, rgba(0, 0, 0, 0.08));
  background: var(--c-bg-elevated, #fff);
  padding: 10px 12px;
  box-shadow: var(--shadow-sm, 0 1px 2px rgba(0, 0, 0, 0.05));
}

.chat-bubble.result-compact .result-block {
  margin-top: 8px;
  padding-top: 8px;
}

.chat-text {
  color: var(--c-text-2, #374151);
  line-height: 1.72;
  white-space: pre-wrap;
}

.chat-refs {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.result-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}

.result-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--c-text-1, #111827);
}

.result-block {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed rgba(0, 0, 0, 0.08);
}



.result-label {
  font-size: 11px;
  color: var(--c-text-4, #9ca3af);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.result-value {
  margin-top: 6px;
  color: var(--c-text-2, #374151);
  line-height: 1.62;
  font-size: 13px;
}

.result-value.strong {
  font-size: 15px;
  font-weight: 700;
  color: var(--c-text-1, #111827);
}

.result-value.body {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.result-value.body.compact {
  max-height: 112px;
  overflow: hidden;
}

.result-value.ellipsis {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.pending-row {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--c-text-3, #6b7280);
}

.streaming-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.streaming-text {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.6;
  color: var(--c-text-1, #1f2937);
}

.quick-topics {
  margin-top: 2px;
  padding: 12px;
  border: 1px solid var(--c-border, rgba(0, 0, 0, 0.08));
  border-radius: var(--radius-lg, 12px);
  background: #fcfdff;
}

.quick-title {
  font-size: 13px;
  color: var(--c-text-3, #6b7280);
  margin-bottom: 10px;
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.quick-item {
  border: 1px solid var(--c-border, rgba(0, 0, 0, 0.08));
  background: #fff;
  border-radius: var(--radius-md, 8px);
  padding: 10px;
  cursor: pointer;
  text-align: left;
  transition: border-color var(--duration-fast, 150ms), box-shadow var(--duration-fast, 150ms), transform var(--duration-fast, 150ms);
}

.quick-item:hover {
  border-color: var(--c-primary, #2563EB);
  box-shadow: var(--shadow-sm, 0 1px 2px rgba(0, 0, 0, 0.05));
  transform: translateY(-1px);
}

.quick-item-title {
  font-size: 13px;
  color: var(--c-text-2, #374151);
  font-weight: 600;
  line-height: 1.45;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.quick-item-meta {
  margin-top: 6px;
  font-size: 12px;
  color: var(--c-text-4, #9ca3af);
}

.composer-wrap {
  border-top: 1px solid var(--c-border, rgba(0, 0, 0, 0.08));
  background: var(--c-bg-elevated, #fff);
  padding: 12px;
}

.material-board {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(270px, 1fr));
  gap: 10px;
  margin-bottom: 10px;
}

.material-card {
  display: grid;
  grid-template-columns: 24px 42px minmax(0, 1fr) auto;
  gap: 8px;
  align-items: center;
  border: 1px solid var(--c-border, rgba(0, 0, 0, 0.08));
  border-radius: var(--radius-md, 8px);
  background: #fff;
  padding: 8px;
  cursor: grab;
}

.material-card.dragging {
  opacity: 0.6;
  box-shadow: var(--shadow-md, 0 2px 8px rgba(0, 0, 0, 0.08));
}

.material-handle {
  color: var(--c-text-4, #9ca3af);
  display: grid;
  place-items: center;
}

.material-thumb,
.mention-thumb {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  overflow: hidden;
  background: #eff6ff;
  border: 1px solid rgba(37, 99, 235, 0.15);
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

.material-thumb img,
.mention-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.material-thumb.placeholder,
.mention-thumb.placeholder {
  background: rgba(37, 99, 235, 0.08);
  color: var(--c-primary, #2563EB);
  font-size: 14px;
  font-weight: 700;
}

.material-main {
  min-width: 0;
}

.material-title {
  font-size: 13px;
  color: var(--c-text-1, #111827);
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.material-source {
  margin-top: 2px;
  font-size: 12px;
  color: var(--c-text-4, #9ca3af);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.composer-main {
  position: relative;
  display: flex;
  gap: 10px;
}

.composer-input {
  width: 100%;
  min-height: 72px;
  max-height: 180px;
  border: 1px solid var(--c-border, rgba(0, 0, 0, 0.08));
  background: #fff;
  border-radius: var(--radius-lg, 12px);
  padding: 10px 12px;
  font-size: 14px;
  color: var(--c-text-2, #374151);
  line-height: 1.7;
  resize: vertical;
  outline: none;
  transition: border-color var(--duration-fast, 150ms), box-shadow var(--duration-fast, 150ms);
}

.composer-input:focus {
  border-color: var(--c-primary, #2563EB);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.14);
}

.send-btn {
  align-self: flex-end;
  height: 42px;
}

.mention-panel {
  position: absolute;
  left: 0;
  right: 72px;
  bottom: calc(100% + 8px);
  border: 1px solid var(--c-border, rgba(0, 0, 0, 0.08));
  border-radius: var(--radius-lg, 12px);
  background: #fff;
  box-shadow: var(--shadow-lg, 0 8px 24px rgba(0, 0, 0, 0.10));
  max-height: 290px;
  overflow: auto;
  z-index: 30;
}

.mention-item {
  width: 100%;
  border: 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
  background: transparent;
  text-align: left;
  padding: 10px 12px;
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  cursor: pointer;
}

.mention-item:hover {
  background: rgba(37, 99, 235, 0.04);
}

.mention-main {
  min-width: 0;
}

.mention-title {
  font-size: 13px;
  color: var(--c-text-2, #374151);
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mention-source {
  margin-top: 2px;
  font-size: 12px;
  color: var(--c-text-4, #9ca3af);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mention-empty {
  padding: 12px;
  color: var(--c-text-4, #9ca3af);
  font-size: 13px;
}

.composer-foot {
  margin-top: 6px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.composer-hint {
  font-size: 12px;
  color: var(--c-text-4, #9ca3af);
}

.preset-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.drawer-subtitle {
  font-size: 13px;
  color: var(--c-text-3, #6b7280);
  font-weight: 600;
}

.preset-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}

.preset-card {
  border: 1px solid var(--c-border, rgba(0, 0, 0, 0.08));
  background: #fff;
  border-radius: var(--radius-md, 8px);
  padding: 10px;
  text-align: left;
  cursor: pointer;
  transition: all var(--duration-fast, 150ms);
}

.preset-card:hover {
  border-color: var(--c-primary, #2563EB);
  box-shadow: var(--shadow-sm, 0 1px 2px rgba(0, 0, 0, 0.05));
}

.preset-card.active {
  border-color: var(--c-primary, #2563EB);
  background: var(--c-primary-bg, rgba(37, 99, 235, 0.06));
}

.preset-name {
  font-size: 14px;
  color: var(--c-text-1, #111827);
  font-weight: 700;
}

.preset-desc {
  margin-top: 4px;
  font-size: 12px;
  color: var(--c-text-3, #6b7280);
}

.preset-platform {
  margin-top: 6px;
  font-size: 12px;
  color: var(--c-primary, #2563EB);
  font-weight: 600;
}

@keyframes msgIn {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 960px) {
  .gen-shell {
    height: calc(100vh - 240px);
    max-height: calc(100vh - 240px);
  }

  .chat-list {
    padding: 10px;
  }

  .quick-grid {
    grid-template-columns: 1fr;
  }

  .material-board {
    grid-template-columns: 1fr;
  }

  .chat-msg {
    grid-template-columns: 34px minmax(0, 1fr);
  }

  .chat-msg.is-user {
    grid-template-columns: minmax(0, 1fr) 34px;
  }

  .chat-avatar {
    width: 30px;
    height: 30px;
    border-radius: 8px;
    font-size: 10px;
  }

  .chat-bubble {
    padding: 8px 10px;
  }

  .composer-input {
    min-height: 68px;
  }

  .composer-foot {
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }
}
</style>