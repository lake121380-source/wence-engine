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

          <div
            class="chat-bubble"
            :class="{
              'is-result-slate': msg.type === 'result',
              'result-collapsed': msg.type === 'result' && !isResultExpanded(msg.id)
            }"
          >
            <template v-if="msg.type === 'result'">
              <!-- 🎬 导演台账顶栏：极富影视张力的标头与视图切换 -->
              <div class="slate-clapper-header">
                <div class="slate-title-group">
                  <div class="slate-index-badge">
                    <span class="slate-clapper-stripe"></span>
                    <span class="slate-badge-text">SLATE 工业分镜台账</span>
                  </div>
                  <h3 class="slate-main-title" :title="msg.data.title || '短视频口播脚本'">
                    {{ msg.data.title || '短视频口播脚本' }}
                  </h3>
                </div>

                <div class="slate-actions">
                  <!-- 视图模式切换 -->
                  <div class="slate-mode-tabs">
                    <button
                      class="slate-tab-btn"
                      :class="{ active: getResultViewMode(msg.id) === 'slate' }"
                      @click="setResultViewMode(msg.id, 'slate')"
                      title="工业级影视分镜台账"
                    >
                      <n-icon size="14"><FilmOutline /></n-icon>
                      <span>导演分镜</span>
                    </button>
                    <button
                      class="slate-tab-btn"
                      :class="{ active: getResultViewMode(msg.id) === 'script' }"
                      @click="setResultViewMode(msg.id, 'script')"
                      title="提词器专用连续口播文案"
                    >
                      <n-icon size="14"><DocumentTextOutline /></n-icon>
                      <span>口播通读</span>
                    </button>
                  </div>

                  <n-button
                    size="small"
                    quaternary
                    @click="toggleResultExpand(msg.id)"
                    class="slate-collapse-btn"
                  >
                    {{ isResultExpanded(msg.id) ? '收起' : '展开' }}
                  </n-button>
                </div>
              </div>

              <!-- 导演台账核心技术指标看板（字数、时长、分镜数、完播率预测） -->
              <div class="slate-meta-ribbon">
                <div class="slate-metric-item">
                  <span class="slate-metric-label">平台适配</span>
                  <span class="slate-metric-val platform-tag">{{ getPlatformLabel(msg.data.platform || config.platform) }}</span>
                </div>
                <div class="slate-metric-divider"></div>
                <div class="slate-metric-item">
                  <span class="slate-metric-label">预估时长</span>
                  <span class="slate-metric-val duration">{{ getScriptStats(msg.data).duration }}</span>
                </div>
                <div class="slate-metric-divider"></div>
                <div class="slate-metric-item">
                  <span class="slate-metric-label">台词字数</span>
                  <span class="slate-metric-val words">{{ getScriptStats(msg.data).words }} 字</span>
                </div>
                <div class="slate-metric-divider"></div>
                <div class="slate-metric-item">
                  <span class="slate-metric-label">工业分镜</span>
                  <span class="slate-metric-val scenes">{{ getDirectorScenes(msg.data).length }} 幕</span>
                </div>
                <div class="slate-metric-divider"></div>
                <div class="slate-metric-item">
                  <span class="slate-metric-label">黄金前3秒完播</span>
                  <span class="slate-metric-val score">
                    <n-icon size="12" style="margin-right:2px;"><FlashOutline /></n-icon>
                    {{ getScriptStats(msg.data).retentionScore }}
                  </span>
                </div>
              </div>

              <!-- 展开详情区域 -->
              <div v-show="isResultExpanded(msg.id)" class="slate-body-container">
                <!-- 模式 1：🎬 导演分镜台账 (Director's Slate) -->
                <div v-if="getResultViewMode(msg.id) === 'slate'" class="slate-scenes-grid">
                  <div
                    v-for="(scene, sIdx) in getDirectorScenes(msg.data)"
                    :key="sIdx"
                    class="scene-card"
                    :class="scene.bg"
                  >
                    <!-- 镜头卡头：幕号 + 时码 + 景别机位 + 快捷复制 -->
                    <div class="scene-card-header">
                      <div class="scene-ident">
                        <span class="scene-code">{{ scene.code }}</span>
                        <span class="scene-timecode">{{ scene.timecode }}</span>
                        <span class="scene-stage-badge">{{ scene.stage }}</span>
                      </div>
                      <div class="scene-shot-info">
                        <span class="scene-shot-pill">{{ scene.shot }}</span>
                        <button
                          class="scene-copy-btn"
                          title="复制该镜台词"
                          @click="copySceneAudio(scene.audio)"
                        >
                          <n-icon size="13"><CopyOutline /></n-icon>
                          <span>复制单镜</span>
                        </button>
                      </div>
                    </div>

                    <!-- 镜头双栏/主次排版：口播台词 & 导演视听指导 -->
                    <div class="scene-content-wrap">
                      <div class="scene-audio-block">
                        <div class="scene-audio-label">
                          <span class="audio-dot"></span>
                          同期口播台词
                        </div>
                        <div class="scene-audio-text">{{ scene.audio }}</div>
                      </div>

                      <div class="scene-visual-directive">
                        <div class="visual-directive-title">
                          <n-icon size="13"><FilmOutline /></n-icon>
                          <span>运镜与视觉花字指导</span>
                        </div>
                        <div class="visual-directive-text">{{ scene.visual }}</div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- 模式 2：📜 纯享口播剧本 (Teleprompter Script) -->
                <div v-else class="slate-script-view">
                  <div class="teleprompter-board">
                    <div v-if="msg.data.hook" class="teleprompter-section hook-highlight">
                      <div class="tele-tag">前 3 秒黄金开场钩子</div>
                      <div class="tele-text bold-hook">{{ msg.data.hook }}</div>
                    </div>
                    <div v-if="msg.data.body" class="teleprompter-section body-flow">
                      <div class="tele-tag">核心论述与价值解法</div>
                      <div class="tele-text">{{ msg.data.body }}</div>
                    </div>
                    <div v-if="msg.data.cta" class="teleprompter-section cta-highlight">
                      <div class="tele-tag">尾声行动号召与闭环</div>
                      <div class="tele-text">{{ msg.data.cta }}</div>
                    </div>
                  </div>
                </div>

                <!-- 标签列表 -->
                <div v-if="msg.data.tags?.length" class="slate-tags-row">
                  <span class="slate-tags-label">推荐话题：</span>
                  <div class="slate-tags-list">
                    <span v-for="t in msg.data.tags" :key="t" class="slate-tag-chip">#{{ t }}</span>
                  </div>
                </div>

                <!-- 底部操作底栏 -->
                <div class="slate-footer-bar">
                  <div class="slate-footer-tip">
                    <span>💡 提示：支持一键复制到提词器，或直接导出完整导演分镜表。</span>
                  </div>
                  <div class="slate-footer-buttons">
                    <n-button size="small" secondary @click="copyFullSpokenText(msg.data)">
                      <template #icon><n-icon><DocumentTextOutline /></n-icon></template>
                      复制提词器口播稿
                    </n-button>
                    <n-button size="small" type="primary" secondary @click="copyFullDirectorSlate(msg.data)">
                      <template #icon><n-icon><CopyOutline /></n-icon></template>
                      复制工业分镜全表
                    </n-button>
                    <n-button
                      size="small"
                      quaternary
                      :disabled="generating"
                      @click="regenerate(msg.payload)"
                    >
                      <template #icon><n-icon><RefreshOutline /></n-icon></template>
                      按此配置再生成一版
                    </n-button>
                  </div>
                </div>
              </div>

              <!-- 折叠状态下的精简预览摘要 -->
              <div v-show="!isResultExpanded(msg.id)" class="slate-collapsed-preview" @click="toggleResultExpand(msg.id)">
                <div class="preview-hook">“{{ msg.data.hook || msg.data.title || '点击展开查看完整分镜台账...' }}”</div>
                <div class="preview-expand-tip">点击展开完整导演分镜台账 (共 {{ getDirectorScenes(msg.data).length }} 幕) ▾</div>
              </div>
            </template>

            <template v-else-if="msg.type === 'pending'">
              <div class="pending-row">
                <n-spin size="small" />
                <span>正在构思分镜与剧本骨架...</span>
              </div>
            </template>

            <template v-else-if="msg.type === 'streaming'">
              <div class="streaming-slate-box">
                <div class="streaming-indicator-bar">
                  <span class="streaming-pulse-dot"></span>
                  <span class="streaming-label">正在实时推演生成脚本台词...</span>
                </div>
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
  DocumentTextOutline,
  FilmOutline,
  FlashOutline,
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
  Array.isArray(styles.value)
    ? styles.value.map((s) => ({
        label: s.content_type ? `[${s.content_type}] ${s.name}` : s.name,
        value: s.id,
      }))
    : []
)
const creatorOptions = computed(() =>
  Array.isArray(creators.value)
    ? creators.value.map((c) => ({ label: `${c.nickname} (${c.platform})`, value: c.id }))
    : []
)
const docOptions = computed(() =>
  Array.isArray(docs.value) ? docs.value.map((d) => ({ label: d.name, value: d.id })) : []
)
const viewpointOptions = computed(() =>
  Array.isArray(viewpoints.value) ? viewpoints.value.map((v) => ({ label: v.title, value: v.id })) : []
)
const viralAnalysisOptions = computed(() =>
  Array.isArray(viralAnalyses.value)
    ? viralAnalyses.value.map((a) => ({
        label: a.title || `视频分析 #${a.id}`,
        value: a.id,
      }))
    : []
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

  if (Array.isArray(styles.value)) {
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
  }

  if (Array.isArray(creators.value)) {
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
  }

  if (Array.isArray(docs.value)) {
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
  }

  if (Array.isArray(viewpoints.value)) {
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
  }

  if (Array.isArray(viralAnalyses.value)) {
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
  }

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

const resultViewModes = reactive({})

function getResultViewMode(id) {
  return resultViewModes[id] || 'slate'
}

function setResultViewMode(id, mode) {
  resultViewModes[id] = mode
}

function getPlatformLabel(val) {
  const map = {
    douyin: '抖音短平快',
    xiaohongshu: '小红书种草口播',
    weixin: '视频号深度分享',
  }
  return map[val] || '短视频全域通用'
}

function getDirectorScenes(data) {
  if (!data) return []
  const scenes = []

  // Scene 1: Golden Hook (前3秒黄金强悬念)
  const hookText = (data.hook || '').trim() || (data.title || '').trim() || '（黄金前3秒悬念破局）'
  scenes.push({
    num: '01',
    code: 'SCENE 01',
    timecode: '00:00 - 00:03',
    stage: '黄金前3秒 · 冲突破局',
    shot: '特写 / 快速入画推镜',
    shotTag: 'CLOSE-UP',
    audio: hookText,
    visual: '强反差高亮花字直击认知痛点，直视镜头抓取用户留存，配合环境背景重音转折。',
    bg: 'hook-scene',
  })

  // Scene 2..N: Body Beats
  const bodyText = (data.body || '').trim()
  if (bodyText) {
    const rawParagraphs = bodyText
      .split(/\n\s*\n|\n/)
      .map((p) => p.trim())
      .filter(Boolean)

    if (rawParagraphs.length <= 1) {
      const sentences = bodyText.split(/(?<=[。！？!?])\s*/).filter(Boolean)
      if (sentences.length >= 2) {
        const mid = Math.ceil(sentences.length / 2)
        rawParagraphs.length = 0
        rawParagraphs.push(sentences.slice(0, mid).join(''), sentences.slice(mid).join(''))
      }
    }

    const shotArchetypes = [
      {
        shot: '中景 / 第一人称生活化',
        tag: 'MEDIUM',
        stage: '痛点剖析 · 情绪共鸣',
        visual: '真实生活/工作场景带入，具象化拆解用户现实痛点，建立深度认同感。',
      },
      {
        shot: '近景特写 / 证据链展示',
        tag: 'DETAIL',
        stage: '独家解法 · 核心反转',
        visual: '核心数据、真实案例或实操画面高亮展示，屏幕侧边弹出思维要点指示牌。',
      },
      {
        shot: '手持微动 / 节奏切镜',
        tag: 'ACTION',
        stage: '避坑指南 · 认知升维',
        visual: '快切多机位画面强化对比，突出不可替代的核心方法论与避坑秘诀。',
      },
    ]

    rawParagraphs.forEach((para, idx) => {
      const preset = shotArchetypes[idx % shotArchetypes.length]
      const sceneNum = String(scenes.length + 1).padStart(2, '0')
      const startSec = (idx + 1) * 8
      const endSec = startSec + 9
      scenes.push({
        num: sceneNum,
        code: `SCENE ${sceneNum}`,
        timecode: `00:${String(startSec).padStart(2, '0')} - 00:${String(endSec).padStart(2, '0')}`,
        stage: preset.stage,
        shot: preset.shot,
        shotTag: preset.tag,
        audio: para,
        visual: preset.visual,
        bg: 'body-scene',
      })
    })
  }

  // Final Scene: CTA (闭环转化)
  const ctaText =
    (data.cta || '').trim() ||
    '觉得这期内容有用别忘了点赞收藏，在评论区留下你的看法，关注我持续带你拆解行业干货。'
  const sceneNum = String(scenes.length + 1).padStart(2, '0')
  scenes.push({
    num: sceneNum,
    code: `SCENE ${sceneNum}`,
    timecode: '尾声 · 转化闭环',
    stage: '价值闭环 · 行动召唤',
    shot: '定格中景 / 眼神坚定',
    shotTag: 'ACTION CALL',
    audio: ctaText,
    visual: '眼神笃定真诚，屏幕下沿弹出互动引导浮层或主页资料指引，BGM渐弱收尾。',
    bg: 'cta-scene',
  })

  return scenes
}

function getScriptStats(data) {
  if (!data) return { words: 0, duration: '00:00', retentionScore: '95%' }
  const fullText = [data.title, data.hook, data.body, data.cta].filter(Boolean).join('')
  const words = fullText.replace(/\s+/g, '').length
  const totalSeconds = Math.max(15, Math.round(words / 4.2))
  const mins = Math.floor(totalSeconds / 60)
  const secs = totalSeconds % 60
  const duration = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
  const retentionScore = words > 120 ? '97% 完播预测' : '94% 完播预测'
  return { words, duration, retentionScore }
}

function copySceneAudio(audio) {
  if (!audio) return
  navigator.clipboard.writeText(audio)
  message.success('已复制单镜台词')
}

function copyFullSpokenText(data) {
  if (!data) return
  const parts = []
  if (data.hook) parts.push(`【黄金开篇】\n${data.hook}`)
  if (data.body) parts.push(`【正文分述】\n${data.body}`)
  if (data.cta) parts.push(`【行动转化】\n${data.cta}`)
  navigator.clipboard.writeText(parts.join('\n\n'))
  message.success('已复制提词器纯口播稿')
}

function copyFullDirectorSlate(data) {
  if (!data) return
  const scenes = getDirectorScenes(data)
  const lines = [
    `🎬 《${data.title || '短视频口播脚本'}》工业导演分镜台账`,
    `适配平台：${getPlatformLabel(data.platform || config.platform)} | 预估时长：${getScriptStats(data).duration} | 镜头数：${scenes.length} 幕`,
    '──────────────────────────────',
  ]
  scenes.forEach((s) => {
    lines.push(`【${s.code} · ${s.stage}】(${s.timecode})`)
    lines.push(`▶ 机位运镜：${s.shot}`)
    lines.push(`▶ 同期台词：${s.audio}`)
    lines.push(`▶ 视听指导：${s.visual}`)
    lines.push('')
  })
  if (data.tags?.length) {
    lines.push(`推荐标签：${data.tags.map((t) => '#' + t).join(' ')}`)
  }
  navigator.clipboard.writeText(lines.join('\n'))
  message.success('已复制完整工业分镜台账')
}

function isResultExpanded(id) {
  return resultExpanded[id] !== false
}

function toggleResultExpand(id) {
  resultExpanded[id] = !isResultExpanded(id)
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

    const { consumeGenerationStream } = await import('../api/sse.js')
    const finalResult = await consumeGenerationStream(response, text => {
      const message = messages.value.find(m => m.id === streamMsgId)
      if (message) message.text += text
      scrollToBottom()
    })

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
      resultExpanded[newId] = true
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
    styles.value = Array.isArray(s?.data) ? s.data : []
    creators.value = Array.isArray(c?.data) ? c.data : []
    docs.value = Array.isArray(d?.data) ? d.data : []
    viewpoints.value = Array.isArray(vp?.data) ? vp.data : []
  } catch {
    message.warning('部分配置数据加载失败，可刷新重试')
    styles.value = []
    creators.value = []
    docs.value = []
    viewpoints.value = []
  }

  try {
    const res = await analyzerApi.listAnalyses()
    viralAnalyses.value = Array.isArray(res?.data) ? res.data : []
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
  min-height: calc(100vh - 120px);
}

.gen-shell {
  padding: 0;
  height: calc(100vh - 200px);
  min-height: 520px;
  overflow: hidden;
  display: grid;
  grid-template-rows: 1fr auto;
}

.chat-list {
  padding: 16px 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.chat-msg {
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr);
  gap: 12px;
  align-items: flex-start;
  animation: msgIn var(--duration-normal, 200ms) var(--ease-default, ease);
}

.chat-msg.is-user {
  grid-template-columns: minmax(0, 1fr) 38px;
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
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: #0f766e;
  color: #fff;
  display: grid;
  place-items: center;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}

.chat-bubble {
  max-width: min(920px, 92%);
  border-radius: var(--radius-lg, 12px);
  border: 1px solid var(--c-border, rgba(0, 0, 0, 0.08));
  background: var(--c-bg-elevated, #fff);
  padding: 14px 16px;
  box-shadow: var(--shadow-sm, 0 1px 2px rgba(0, 0, 0, 0.05));
  transition: all var(--duration-fast, 160ms) ease;
}

.chat-bubble.is-result-slate {
  max-width: 100%;
  width: 100%;
  padding: 0;
  border-radius: var(--radius-xl, 16px);
  border: 1px solid var(--c-border);
  box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.04), 0 2px 6px -1px rgba(0, 0, 0, 0.02);
  overflow: hidden;
  background: #ffffff;
}

.chat-bubble.result-collapsed {
  cursor: pointer;
}

/* 🎬 导演台账 Clapperboard 标头 */
.slate-clapper-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: linear-gradient(180deg, #fafbfd 0%, #f4f6f9 100%);
  border-bottom: 1px solid var(--c-border);
  gap: 16px;
}

.slate-title-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.slate-index-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.slate-clapper-stripe {
  width: 14px;
  height: 12px;
  border-radius: 2px;
  background: repeating-linear-gradient(45deg, #1e293b, #1e293b 3px, #e2e8f0 3px, #e2e8f0 6px);
}

.slate-badge-text {
  font-size: 11px;
  font-weight: 750;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--c-primary, #1d4ed8);
}

.slate-main-title {
  font-size: 18px;
  font-weight: 750;
  color: var(--c-text-1, #111827);
  letter-spacing: -0.02em;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.slate-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.slate-mode-tabs {
  display: inline-flex;
  background: rgba(17, 24, 39, 0.06);
  padding: 3px;
  border-radius: 8px;
  gap: 2px;
}

.slate-tab-btn {
  border: none;
  background: transparent;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  color: var(--c-text-3, #6b7280);
  transition: all 160ms var(--ease-default);
}

.slate-tab-btn:hover {
  color: var(--c-text-1, #111827);
}

.slate-tab-btn.active {
  background: #ffffff;
  color: var(--c-primary, #1d4ed8);
  font-weight: 600;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

/* 导演技术参数看带 */
.slate-meta-ribbon {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  padding: 10px 20px;
  background: #ffffff;
  border-bottom: 1px dashed var(--c-border);
  font-size: 12px;
}

.slate-metric-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.slate-metric-label {
  color: var(--c-text-4, #9ca3af);
  font-size: 11px;
}

.slate-metric-val {
  font-weight: 600;
  color: var(--c-text-2, #374151);
  font-variant-numeric: tabular-nums;
}

.slate-metric-val.platform-tag {
  color: var(--c-primary, #1d4ed8);
  background: var(--c-primary-bg, rgba(29, 78, 216, 0.06));
  padding: 1px 8px;
  border-radius: 4px;
  font-size: 11.5px;
}

.slate-metric-val.score {
  display: inline-flex;
  align-items: center;
  color: #c2410c;
  background: #fff7ed;
  padding: 1px 7px;
  border-radius: 4px;
}

.slate-metric-divider {
  width: 1px;
  height: 12px;
  background: var(--c-border);
}

/* 展开区域 */
.slate-body-container {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.slate-scenes-grid {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.scene-card {
  border: 1px solid var(--c-border);
  border-radius: 12px;
  background: #ffffff;
  padding: 16px;
  transition: border-color 180ms ease, box-shadow 180ms ease;
}

.scene-card:hover {
  border-color: rgba(29, 78, 216, 0.25);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.03);
}

.scene-card.hook-scene {
  border-left: 3px solid #1d4ed8;
  background: linear-gradient(180deg, #f8faff 0%, #ffffff 100%);
}

.scene-card.cta-scene {
  border-left: 3px solid #15803d;
  background: linear-gradient(180deg, #f8fdfa 0%, #ffffff 100%);
}

.scene-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(17, 24, 39, 0.05);
}

.scene-ident {
  display: flex;
  align-items: center;
  gap: 8px;
  font-variant-numeric: tabular-nums;
}

.scene-code {
  font-weight: 800;
  font-size: 12px;
  color: var(--c-text-1, #111827);
  letter-spacing: 0.04em;
}

.scene-timecode {
  font-size: 11px;
  color: var(--c-text-3, #6b7280);
  background: #f1f5f9;
  padding: 2px 6px;
  border-radius: 4px;
}

.scene-stage-badge {
  font-size: 11.5px;
  font-weight: 600;
  color: var(--c-text-2, #374151);
}

.scene-shot-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.scene-shot-pill {
  font-size: 11px;
  color: var(--c-primary, #1d4ed8);
  background: var(--c-primary-bg, rgba(29, 78, 216, 0.06));
  padding: 2px 8px;
  border-radius: 999px;
  font-weight: 600;
}

.scene-copy-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--c-text-4, #9ca3af);
  font-size: 11px;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
  transition: all 150ms ease;
}

.scene-copy-btn:hover {
  color: var(--c-primary, #1d4ed8);
  background: var(--c-primary-bg, rgba(29, 78, 216, 0.06));
}

.scene-content-wrap {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 16px;
  align-items: stretch;
}

@media (max-width: 820px) {
  .scene-content-wrap {
    grid-template-columns: 1fr;
  }
}

.scene-audio-block {
  background: #f8fafc;
  border: 1px solid rgba(17, 24, 39, 0.05);
  border-radius: 8px;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
}

.scene-audio-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 600;
  color: var(--c-text-3, #6b7280);
  margin-bottom: 6px;
  text-transform: uppercase;
}

.audio-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--c-primary, #1d4ed8);
}

.scene-audio-text {
  font-size: 14px;
  line-height: 1.7;
  color: var(--c-text-1, #111827);
  font-weight: 500;
  white-space: pre-wrap;
}

.scene-visual-directive {
  background: #fefce8;
  border: 1px dashed rgba(202, 138, 4, 0.3);
  border-radius: 8px;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
}

.visual-directive-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 600;
  color: #854d0e;
  margin-bottom: 6px;
}

.visual-directive-text {
  font-size: 12.5px;
  line-height: 1.6;
  color: #713f12;
}

/* 纯享口播剧本（提词器版式） */
.slate-script-view {
  display: flex;
  flex-direction: column;
}

.teleprompter-board {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.teleprompter-section {
  padding: 16px 18px;
  border-radius: 10px;
  border: 1px solid var(--c-border);
  background: #ffffff;
}

.teleprompter-section.hook-highlight {
  border-color: rgba(29, 78, 216, 0.25);
  background: #f8faff;
}

.teleprompter-section.cta-highlight {
  border-color: rgba(21, 128, 61, 0.25);
  background: #f8fdfa;
}

.tele-tag {
  font-size: 11px;
  font-weight: 750;
  color: var(--c-text-3, #6b7280);
  margin-bottom: 8px;
  text-transform: uppercase;
}

.tele-text {
  font-size: 15px;
  line-height: 1.8;
  color: var(--c-text-1, #111827);
  white-space: pre-wrap;
}

.tele-text.bold-hook {
  font-weight: 700;
  color: var(--c-primary, #1d4ed8);
  font-size: 16px;
}

/* 标签栏与底栏 */
.slate-tags-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
}

.slate-tags-label {
  font-size: 12px;
  color: var(--c-text-3, #6b7280);
}

.slate-tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.slate-tag-chip {
  font-size: 12px;
  color: var(--c-primary, #1d4ed8);
  background: var(--c-primary-bg, rgba(29, 78, 216, 0.06));
  padding: 2px 8px;
  border-radius: 999px;
  font-weight: 500;
}

.slate-footer-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  padding-top: 14px;
  border-top: 1px solid var(--c-border);
}

.slate-footer-tip {
  font-size: 12px;
  color: var(--c-text-4, #9ca3af);
}

.slate-footer-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

/* 折叠摘要预览 */
.slate-collapsed-preview {
  padding: 14px 20px;
  background: #fafafa;
  border-top: 1px solid var(--c-border);
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.slate-collapsed-preview:hover {
  background: #f4f5f7;
}

.preview-hook {
  font-size: 13.5px;
  font-weight: 600;
  color: var(--c-text-2, #374151);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.preview-expand-tip {
  font-size: 12px;
  color: var(--c-primary, #1d4ed8);
  flex-shrink: 0;
  font-weight: 500;
}

/* 流式生成美学 */
.streaming-slate-box {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px 18px;
}

.streaming-indicator-bar {
  display: flex;
  align-items: center;
  gap: 8px;
}

.streaming-pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--c-primary, #1d4ed8);
  box-shadow: 0 0 0 0 rgba(29, 78, 216, 0.4);
  animation: pulseGlow 1.8s infinite;
}

@keyframes pulseGlow {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(29, 78, 216, 0.5); }
  70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(29, 78, 216, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(29, 78, 216, 0); }
}

.streaming-label {
  font-size: 12.5px;
  font-weight: 600;
  color: var(--c-primary, #1d4ed8);
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
  gap: 12px;
  align-items: flex-end;
}

.composer-input {
  width: 100%;
  min-height: 72px;
  max-height: 160px;
  border: 1px solid var(--c-border, rgba(0, 0, 0, 0.08));
  background: var(--c-bg-soft, #f8fafc);
  border-radius: var(--radius-lg, 12px);
  padding: 10px 14px;
  font-size: 14px;
  color: var(--c-text-1, #0f172a);
  line-height: 1.6;
  resize: vertical;
  outline: none;
  transition: border-color var(--duration-fast, 150ms), box-shadow var(--duration-fast, 150ms), background-color var(--duration-fast, 150ms);
}

.composer-input:focus {
  background: #ffffff;
  border-color: var(--c-primary, #2563EB);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.14);
}

.send-btn {
  align-self: flex-end;
  height: 42px;
  padding: 0 18px;
  flex-shrink: 0;
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
