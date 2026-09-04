<template>
  <div class="generate-page rb-theme" :class="{ 'is-chat': !isWelcome, 'is-welcome': isWelcome }">
    <div class="rb-canvas" aria-hidden="true">
      <span class="rb-blob rb-blob-a"></span>
      <span class="rb-blob rb-blob-b"></span>
      <span class="rb-blob rb-blob-c"></span>
      <span class="rb-grid"></span>
    </div>

    <!-- ═══ WELCOME MODE: 首页 ═══ -->
    <template v-if="isWelcome">
      <div class="welcome-shell">
        <div class="welcome-head rb-entrance" style="--rb-delay: 30ms">
          <div class="hero-title">
            <span>有素材，就能创作</span>
            <span class="hero-accent rb-shiny">自由组合，一键成稿</span>
          </div>
          <div class="hero-sub">输入需求或用 @ 引用风格、文档、观点，一键生成多平台文案</div>
        </div>

        <div class="" style="--rb-delay: 70ms">
          <div class="search-wrap">
            <div class="search-container">
              <div class="search-top">
                <textarea
                  ref="composerRef"
                  v-model="promptText"
                  class="search-input"
                  rows="3"
                  placeholder="例如：模仿 @风格:李老师风格，结合 @文档:产品资料，写一版抖音口播文案"
                  @input="handleComposerInput"
                  @click="updateMentionState"
                  @keyup="updateMentionState"
                  @blur="handleComposerBlur"
                  @keydown.enter.exact.prevent="sendPrompt"
                />
                <button class="search-submit rb-submit" :class="{ active: promptText.trim() || materialBlocks.length }" @click="sendPrompt">
                  <n-icon size="16"><SparklesOutline /></n-icon>
                </button>

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

              <div class="search-actions">
                <n-space size="small">
                  <n-button size="tiny" quaternary @click="openAtPicker">
                    <template #icon><n-icon size="14"><AddOutline /></n-icon></template>
                    添加素材
                  </n-button>
                  <n-button size="tiny" quaternary @click="openConfig = true">
                    <template #icon><n-icon size="13"><OptionsOutline /></n-icon></template>
                    更多配置
                  </n-button>
                  <n-button size="tiny" :type="showBrief ? 'primary' : 'default'" quaternary @click="showBrief = !showBrief">
                    <template #icon><n-icon size="13"><BulbOutline /></n-icon></template>
                    创作Brief{{ hasBrief ? ' ✦' : '' }}
                  </n-button>
                </n-space>
                <n-button size="tiny" text @click="showPresetPanel = !showPresetPanel">
                  {{ showPresetPanel ? '收起模式' : '展开模式' }}
                </n-button>
              </div>

              <div v-if="materialBlocks.length" class="search-refs">
                <n-tag
                  v-for="block in materialBlocks"
                  :key="block.key"
                  size="small"
                  :bordered="false"
                  type="info"
                  closable
                  @close="removeReference(block)"
                >
                  @{{ block.label }}
                </n-tag>
              </div>

              <div v-show="showBrief" class="brief-panel">
                <div class="brief-row">
                  <label class="brief-label">目标人群</label>
                  <input v-model="brief.audience" class="brief-input" placeholder="例：25-35岁职场妈妈，关注效率和自我提升" />
                </div>
                <div class="brief-row">
                  <label class="brief-label">核心卖点</label>
                  <textarea v-model="brief.selling_points" class="brief-input brief-textarea" placeholder="例：打破传统课程模式，碎片化时间就能学，已有3000+用户2周见效" rows="2" />
                </div>
                <div class="brief-row">
                  <label class="brief-label">真实数据/案例</label>
                  <input v-model="brief.data_examples" class="brief-input" placeholder="例：用户小林，35岁，用了21天从0粉到8000粉" />
                </div>
                <div class="brief-row">
                  <label class="brief-label">回避内容</label>
                  <input v-model="brief.avoid" class="brief-input" placeholder="例：不提竞品，不说价格，不用感叹号" />
                </div>
                <div v-if="quickViewpointChips.length" class="brief-row">
                  <label class="brief-label">快捷观点</label>
                  <div class="brief-chip-list">
                    <button
                      v-for="vp in quickViewpointChips"
                      :key="vp.id"
                      class="brief-chip"
                      :class="{ active: isQuickViewpointSelected(vp.id) }"
                      @click="toggleQuickViewpoint(vp.id)"
                    >
                      {{ vp.title }}
                    </button>
                  </div>
                  <div class="brief-hint">勾选后自动加入素材引用，无需手动 @ 输入</div>
                </div>
              </div>

              <div v-show="showPresetPanel" class="search-bottom">
                <div class="mode-chip" :class="{ active: activePresetId === 'custom' }" @click="activePresetId = 'custom'">
                  <span class="chip-icon">✦</span> 自由创作
                </div>
                <div
                  v-for="p in presets"
                  :key="p.id"
                  class="mode-chip"
                  :class="{ active: activePresetId === p.id }"
                  @click="applyPreset(p)"
                >
                  {{ p.name }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="tools-row">
          <router-link to="/topics" class="tool-card rb-glow-card rb-entrance" style="--rb-delay: 120ms">
            <div class="tool-thumb icon-topics">
              <n-icon size="18"><FlameOutline /></n-icon>
            </div>
            <div class="tool-info">
              <div class="tool-name">选题发现</div>
              <div class="tool-desc">实时搜索热门爆款视频</div>
            </div>
          </router-link>
          <router-link to="/creators" class="tool-card rb-glow-card rb-entrance" style="--rb-delay: 170ms">
            <div class="tool-thumb icon-creators">
              <n-icon size="18"><PeopleOutline /></n-icon>
            </div>
            <div class="tool-info">
              <div class="tool-name">博主库</div>
              <div class="tool-desc">风格参考</div>
            </div>
          </router-link>
          <router-link to="/documents" class="tool-card rb-glow-card rb-entrance" style="--rb-delay: 220ms">
            <div class="tool-thumb icon-docs">
              <n-icon size="18"><DocumentTextOutline /></n-icon>
            </div>
            <div class="tool-info">
              <div class="tool-name">资料库</div>
              <div class="tool-desc">知识管理</div>
            </div>
          </router-link>
          <router-link to="/styles" class="tool-card rb-glow-card rb-entrance" style="--rb-delay: 270ms">
            <div class="tool-thumb icon-styles">
              <n-icon size="18"><ColorPaletteOutline /></n-icon>
            </div>
            <div class="tool-info">
              <div class="tool-name">风格模板</div>
              <div class="tool-desc">一键套用</div>
            </div>
          </router-link>
          <router-link to="/viewpoints" class="tool-card rb-glow-card rb-entrance" style="--rb-delay: 320ms">
            <div class="tool-thumb icon-views">
              <n-icon size="18"><BulbOutline /></n-icon>
            </div>
            <div class="tool-info">
              <div class="tool-name">观点库</div>
              <div class="tool-desc">运营观点</div>
            </div>
          </router-link>
        </div>

        <div class="discover rb-entrance" style="--rb-delay: 360ms">
          <div class="discover-head">
            <div class="discover-title"><span class="rb-live-dot"></span>推荐选题</div>
            <div class="discover-head-actions">
              <span class="discover-updated">{{ quickTopicsUpdatedText }}</span>
              <n-button size="tiny" text :loading="quickTopicsLoading" @click="fetchQuickTopics()">刷新</n-button>
            </div>
          </div>

          <div v-if="quickTopicsLoading" class="discover-empty">正在更新推荐选题...</div>
          <div v-else-if="quickTopics.length" class="discover-grid">
            <div
              v-for="(t, idx) in quickTopics"
              :key="t.id"
              class="discover-item rb-entrance"
              :style="{ '--rb-delay': `${120 + idx * 55}ms` }"
              @click="useQuickTopic(t)"
            >
              <div class="discover-item-title">{{ t.title }}</div>
              <div class="discover-item-meta">{{ platformLabel(t.platform) }}</div>
            </div>
          </div>
          <div v-else class="discover-empty-state">
            <span class="discover-empty-icon">📋</span>
            <span>暂无推荐选题，可前往<router-link to="/topics" class="discover-link">选题页</router-link>搜索保存后显示</span>
          </div>
        </div>
      </div>
    </template>

    <!-- ═══ CHAT MODE: 对话界面 ═══ -->
    <template v-else>
      <div class="chat-header rb-glass">
        <n-space align="center" size="small">
          <n-tag v-if="activePreset" type="info" :bordered="false" size="small">{{ activePreset.name }}</n-tag>
          <n-tag :bordered="false" size="small">{{ platformLabel(config.platform) }}</n-tag>
        </n-space>
        <n-space align="center" size="small">
          <n-button size="small" secondary @click="openConfig = true">
            <template #icon><n-icon size="14"><OptionsOutline /></n-icon></template>
            配置
          </n-button>
          <n-button size="small" quaternary @click="resetSession">新会话</n-button>
        </n-space>
      </div>

      <section class="gen-shell rb-panel">
        <div ref="chatListRef" class="chat-list" :class="{ centered: shouldCenterConversation }">
          <div
            v-for="msg in messages"
            :key="msg.id"
            :id="`msg-${msg.id}`"
            class="chat-msg"
            :class="msg.role === 'user' ? 'is-user' : 'is-assistant'"
          >
            <div class="chat-avatar">{{ msg.role === 'user' ? '你' : 'AI' }}</div>

            <div class="chat-bubble rb-glass" :class="{ 'result-compact': msg.type === 'result' && !isResultExpanded(msg.id), 'is-result': msg.type === 'result' }">
              <template v-if="msg.type === 'result'">
                <div class="result-head">
                  <div class="result-title-wrap">
                    <div class="result-title">已生成一版文案</div>
                    <div class="result-sub">可直接复制使用，也可以再生成不同版本</div>
                  </div>
                  <n-space size="small" class="result-actions">
                    <n-button v-if="bodyIsLong(msg.data)" size="tiny" quaternary @click="toggleResultExpand(msg.id)">
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
                    <n-button size="tiny" quaternary :disabled="generating" @click="regenerateWithTwist(msg.payload)">
                      <template #icon><n-icon><RefreshOutline /></n-icon></template>
                      换个写法
                    </n-button>
                  </n-space>
                </div>

                <div class="result-block">
                  <div class="result-value body" :class="{ compact: !isResultExpanded(msg.id) }">
                    <div v-for="(line, idx) in (isResultExpanded(msg.id) ? splitFullText(msg.data) : previewFullText(msg.data))" :key="idx">{{ line }}</div>
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
                  <span>正在生成...</span>
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
                  <n-tag v-for="r in msg.refs" :key="r.key" size="small" :bordered="false" type="info">@{{ compactRefLabel(r) }}</n-tag>
                </div>
              </template>
            </div>
          </div>
        </div>

        <div class="composer-wrap rb-glass">
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
              placeholder="继续输入需求，或 @ 引用素材..."
              @input="handleComposerInput"
              @click="updateMentionState"
              @keyup="updateMentionState"
              @blur="handleComposerBlur"
              @keydown.enter.exact.prevent="sendPrompt"
            />
            <n-button class="send-btn" type="primary" :loading="generating" @click="sendPrompt">
              <template #icon><n-icon><SparklesOutline /></n-icon></template>
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
            <n-space size="small">
              <n-button size="tiny" quaternary @click="openAtPicker">@ 引用素材</n-button>
              <n-button size="tiny" quaternary @click="clearReferences">清空素材</n-button>
            </n-space>
            <div class="composer-hint">Enter 发送</div>
          </div>
        </div>
      </section>
    </template>

    <!-- ═══ 配置 Drawer（两种模式共享） ═══ -->
    <n-drawer v-model:show="openConfig" :width="configDrawerWidth" placement="right">
      <n-drawer-content title="模板与配置" closable>
        <template #header-extra>
          <n-button size="tiny" quaternary @click="configDrawerExpanded = !configDrawerExpanded">
            {{ configDrawerExpanded ? '收起' : '展开' }}
          </n-button>
        </template>

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
          <n-form-item label="目标字数（可选）">
            <n-input-number
              v-model:value="config.target_word_count"
              :min="100"
              :max="2000"
              :step="50"
              placeholder="不填则按平台默认"
              style="width: 100%;"
            />
          </n-form-item>
          <n-form-item label="风格模板（单选）">
            <n-select v-model:value="config.style_template_id" :options="styleOptions" clearable placeholder="不限" />
          </n-form-item>
          <n-form-item label="文档资料（多选）">
            <n-select v-model:value="config.product_doc_ids" multiple :options="docOptions" clearable placeholder="不限" />
          </n-form-item>
          <n-form-item label="运营观点（多选）">
            <n-select v-model:value="config.viewpoint_ids" multiple :options="viewpointOptions" clearable placeholder="不限" />
          </n-form-item>
          <n-form-item label="爆款分析（多选）">
            <n-select v-model:value="config.viral_analysis_ids" multiple :options="viralAnalysisOptions" clearable placeholder="不限" />
          </n-form-item>
        </n-form>
      </n-drawer-content>
    </n-drawer>

    <n-modal
      v-model:show="showOnboarding"
      preset="card"
      style="width: 640px; border-radius: 14px;"
      :mask-closable="false"
    >
      <template #header>
        <div class="onboarding-header">新手引导</div>
      </template>

      <div class="onboarding-intro">
        先完成这 4 步，你就可以稳定产出可发布文案。
      </div>

      <div class="onboarding-list">
        <div class="onboarding-item" :class="{ done: isOnboardingDone('creators') }">
          <div class="onboarding-step">1</div>
          <div class="onboarding-main">
            <div class="onboarding-title">添加博主</div>
            <div class="onboarding-desc">至少添加 1 位博主，用于风格提取与参考。</div>
          </div>
          <n-button size="tiny" quaternary @click="jumpOnboarding('/creators')">
            {{ isOnboardingDone('creators') ? '已完成' : '去完成' }}
          </n-button>
        </div>

        <div class="onboarding-item" :class="{ done: isOnboardingDone('documents') }">
          <div class="onboarding-step">2</div>
          <div class="onboarding-main">
            <div class="onboarding-title">上传资料</div>
            <div class="onboarding-desc">上传产品文档，生成时可直接引用知识内容。</div>
          </div>
          <n-button size="tiny" quaternary @click="jumpOnboarding('/documents')">
            {{ isOnboardingDone('documents') ? '已完成' : '去完成' }}
          </n-button>
        </div>

        <div class="onboarding-item" :class="{ done: isOnboardingDone('topics') }">
          <div class="onboarding-step">3</div>
          <div class="onboarding-main">
            <div class="onboarding-title">保存选题</div>
            <div class="onboarding-desc">从爆款中保存至少 1 条选题，快速积累灵感池。</div>
          </div>
          <n-button size="tiny" quaternary @click="jumpOnboarding('/topics')">
            {{ isOnboardingDone('topics') ? '已完成' : '去完成' }}
          </n-button>
        </div>

        <div class="onboarding-item" :class="{ done: isOnboardingDone('generations') }">
          <div class="onboarding-step">4</div>
          <div class="onboarding-main">
            <div class="onboarding-title">开始生成</div>
            <div class="onboarding-desc">完成首次生成后，你就有可复用的历史上下文。</div>
          </div>
          <n-button size="tiny" quaternary @click="jumpOnboarding('/')">
            {{ isOnboardingDone('generations') ? '已完成' : '去完成' }}
          </n-button>
        </div>
      </div>

      <template #footer>
        <n-space justify="end">
          <n-button @click="hideOnboarding(false)">稍后再看</n-button>
          <n-button type="primary" @click="hideOnboarding(true)">我知道了</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useMessage } from 'naive-ui'
import {
  AddOutline,
  BulbOutline,
  CopyOutline,
  ColorPaletteOutline,
  DocumentTextOutline,
  FlameOutline,
  OptionsOutline,
  PeopleOutline,
  RefreshOutline,
  ReorderThreeOutline,
  SparklesOutline,
} from '@vicons/ionicons5'
import {
  analyzerApi,
  documentsApi,
  generateApi,
  statsApi,
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
const configDrawerExpanded = ref(false)
const showPresetPanel = ref(true)
const showBrief = ref(false)
const brief = reactive({
  audience: '',        // 目标人群
  selling_points: '', // 核心卖点 / 差异化
  data_examples: '',  // 真实数据 / 案例
  avoid: '',          // 回避内容
})
const promptText = ref('')
const quickTopics = ref([])
const quickTopicsLoading = ref(false)
const quickTopicsUpdatedAt = ref(0)
const showOnboarding = ref(false)
const onboardingStats = reactive({
  creators: 0,
  documents: 0,
  topics: 0,
  generations: 0,
})
const chatListRef = ref(null)
const composerRef = ref(null)

const QUICK_TOPICS_POLL_MS = 30000
let quickTopicsTimer = null

const configDrawerWidth = computed(() => (configDrawerExpanded.value ? 680 : 440))

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
  target_word_count: null,
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
const docs = ref([])
const viewpoints = ref([])
const viralAnalyses = ref([])

const styleOptions = computed(() =>
  styles.value.map((s) => ({
    label: s.content_type ? `[${s.content_type}] ${s.name}` : s.name,
    value: s.id,
  }))
)
const docOptions = computed(() => docs.value.map((d) => ({ label: d.name, value: d.id })))
const viewpointOptions = computed(() => viewpoints.value.map((v) => ({ label: v.title, value: v.id })))
const quickViewpointChips = computed(() => viewpoints.value.slice(0, 12))
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
    text: '你可以这样输入：@风格:某某风格，结合 @文档:产品资料，生成一版可直接拍摄的文案。',
  },
])

const isWelcome = computed(() => !messages.value.some((m) => m.role === 'user'))
const shouldCenterConversation = computed(() => !isWelcome.value && messages.value.length <= 3)
const quickTopicsUpdatedText = computed(() => {
  if (!quickTopicsUpdatedAt.value) return '未更新'
  return `更新于 ${new Date(quickTopicsUpdatedAt.value).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  })}`
})

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

function isOnboardingDone(key) {
  return (onboardingStats[key] || 0) > 0
}

function hideOnboarding(permanent = false) {
  showOnboarding.value = false
  if (permanent) {
    localStorage.setItem('cs_onboarding_done', '1')
    return
  }
  sessionStorage.setItem('cs_onboarding_hidden', '1')
}

function jumpOnboarding(path) {
  showOnboarding.value = false
  sessionStorage.setItem('cs_onboarding_hidden', '1')
  router.push(path)
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
    style: '风格模板',
    creator: '博主',
    doc: '文档',
    viewpoint: '观点',
    analysis: '爆款分析',
  }[type] || '素材'
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
      label: `视频分析:${title}`,
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

function isQuickViewpointSelected(id) {
  return config.viewpoint_ids.includes(id)
}

function toggleQuickViewpoint(id) {
  if (config.viewpoint_ids.includes(id)) {
    config.viewpoint_ids = config.viewpoint_ids.filter((x) => x !== id)
  } else {
    config.viewpoint_ids = [...config.viewpoint_ids, id]
  }
  syncBlocksFromConfig()
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

// 解析输入框中当前存在的compact token，反向同步config
function parseTokensInText(text) {
  // 匹配 @视#数字  @文档:xxx  @观点:xxx  @风格:xxx
  const tokens = []
  const re = /@(视#(\d+)|文档:([^\s@]+)|观点:([^\s@]+)|风格:([^\s@]+))/g
  let m
  while ((m = re.exec(text)) !== null) {
    if (m[2]) tokens.push({ type: 'analysis', hint: parseInt(m[2]) }) // 直接 id
    else if (m[3]) tokens.push({ type: 'doc', hint: m[3] })
    else if (m[4]) tokens.push({ type: 'viewpoint', hint: m[4] })
    else if (m[5]) tokens.push({ type: 'style', hint: m[5] })
  }
  return tokens
}

function syncRefsFromText() {
  const tokens = parseTokensInText(promptText.value)

  // 对于 analysis：直接匹配id
  const analysisIds = tokens.filter(t => t.type === 'analysis').map(t => t.hint)
  config.viral_analysis_ids = config.viral_analysis_ids.filter(id => analysisIds.includes(id))

  // 对于其他类型：用 hint（名称片段）到mentionPool 里找匹配
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
  // label 形如 "文档:产品资料" / "视:某标?? / "风格:xxx"
  // analysis 直接用短 ID 形式避免超长标题进输入框
  if (item.type === 'analysis') return `@视#${item.id}`
  // 其他类型取label 冒号后的名称，最多10 字
  const name = (item.label || '').replace(/^[^:]+:/, '').slice(0, 10)
  const prefix = { doc: '文档', viewpoint: '观点', style: '风格' }[item.type] || '素材'
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

const hasBrief = computed(() =>
  !!(brief.audience || brief.selling_points || brief.data_examples || brief.avoid)
)

function buildTopic() {
  const baseText = promptText.value.trim()
  const refsText = materialBlocks.value.map((r) => `@${r.label}`).join(' ')
  const base = baseText || refsText
  if (!base) return ''

  let topic = base

  if (activePreset.value?.instruction) {
    topic += `\n\n【模板要求】${activePreset.value.instruction}`
  }

  // 注入创作 Brief（只注入有填写的字段）
  const briefLines = []
  if (brief.audience) briefLines.push(`目标人群：${brief.audience}`)
  if (brief.selling_points) briefLines.push(`核心卖点：${brief.selling_points}`)
  if (brief.data_examples) briefLines.push(`真实数据/案例（请直接用到文案中）：${brief.data_examples}`)
  if (brief.avoid) briefLines.push(`回避内容（严格遵守）：${brief.avoid}`)
  if (briefLines.length) {
    topic += `\n\n【创作Brief — 比模板要求优先级更高，必须严格遵守】\n${briefLines.join('\n')}`
  }

  return topic
}

function normalizedTargetWordCount() {
  const value = Number(config.target_word_count)
  if (!Number.isFinite(value)) return null
  const rounded = Math.round(value)
  if (rounded < 100 || rounded > 2000) return null
  return rounded
}

function makePayload() {
  const styleBlock = materialBlocks.value.find((x) => x.type === 'style')

  // 构建对话历史（最多3 轮）
  const history = []
  const pastMsgs = messages.value.filter((m) => m.type === 'text' || m.type === 'result')
  const recent = pastMsgs.slice(-6)
  for (const m of recent) {
    if (m.role === 'user' && m.text) {
      history.push({ role: 'user', content: m.text })
    } else if (m.role === 'assistant' && m.type === 'result' && m.data) {
      // 把上一次生成结果作为assistant 回复
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
    target_word_count: normalizedTargetWordCount(),
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

function makeTwistPayload(payload) {
  const angles = [
    '故事开场，再过渡到方法拆解',
    '反常识开场，再给出可执行步骤',
    '先抛痛点，再给出对比转折',
    '问题清单开场，再给解决方案',
  ]
  const angle = angles[Math.floor(Math.random() * angles.length)]
  return {
    ...payload,
    topic: `${payload.topic}\n\n【改写要求】保持核心信息不变，换一种表达方式和叙事节奏，避免复用上一版句式。请优先采用：${angle}。`,
  }
}

async function runGenerate(payload, payloadForReuse = payload) {
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

    // 替换 streaming 消息为result 消息
    const idx = messages.value.findIndex((m) => m.id === streamMsgId)
    if (idx >= 0 && finalResult) {
      const newId = makeId()
      messages.value[idx] = {
        id: newId,
        role: 'assistant',
        type: 'result',
        payload: { ...payloadForReuse },
        data: { ...finalResult },
      }
      resultExpanded[newId] = false
      scrollToMessage(newId)
    }

    await fetchQuickTopics({ silent: true })
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
  await runGenerate({ ...payload }, { ...payload })
}

async function regenerateWithTwist(payload) {
  if (!payload || generating.value) return
  messages.value.push({
    id: makeId(),
    role: 'user',
    type: 'text',
    text: '换个写法（保留核心信息，改变表达节奏）',
  })
  await runGenerate(makeTwistPayload({ ...payload }), { ...payload })
}



async function copyResult(msg) {
  const data = msg?.data
  if (!data) return
  const text = buildFullText(data)
  try {
    if (navigator.clipboard?.writeText && window.isSecureContext) {
      await navigator.clipboard.writeText(text)
    } else {
      const textarea = document.createElement('textarea')
      textarea.value = text
      textarea.setAttribute('readonly', '')
      textarea.style.position = 'fixed'
      textarea.style.opacity = '0'
      textarea.style.left = '-9999px'
      document.body.appendChild(textarea)
      textarea.select()
      const copied = document.execCommand('copy')
      document.body.removeChild(textarea)
      if (!copied) throw new Error('copy-failed')
    }
    message.success('已复制到剪贴板')
  } catch {
    message.error('复制失败，请检查浏览器权限')
  }
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
  if (ref.type === 'analysis') return `视#${ref.id}`
  const label = ref.label || ''
  if (label.length <= 18) return label
  return `${label.slice(0, 18)}...`
}

async function resetSession() {
  messages.value = [
    {
      id: makeId(),
      role: 'assistant',
      type: 'text',
      text: '新会话已开启。继续用 @ 素材块自由组合吧。',
    },
  ]
  promptText.value = ''
  mentionState.visible = false

  // 进入欢迎态时主动刷新一次推荐选题，避免依赖 watch 时机导致列表为空。
  startQuickTopicsPolling()
  await fetchQuickTopics({ silent: true })

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

async function fetchQuickTopics(options = {}) {
  const { silent = false } = options
  if (quickTopicsLoading.value) return
  if (!silent) quickTopicsLoading.value = true

  try {
    // 多拉 30 条，随机打乱后取前 8，保证每次刷新内容不同
    const { data: pendingTopics } = await topicsApi.list({ status: '待评审', limit: 30 })
    let pool = pendingTopics || []

    // 兜底：如果待评审为空，则回退到全量选题，避免首页完全无推荐。
    if (!pool.length) {
      const { data: fallbackTopics } = await topicsApi.list({ limit: 30 })
      pool = fallbackTopics || []
    }

    if (pool.length > 0) {
      // Fisher-Yates shuffle
      for (let i = pool.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [pool[i], pool[j]] = [pool[j], pool[i]]
      }
      quickTopics.value = pool.slice(0, 8)
    } else {
      quickTopics.value = []
    }
    quickTopicsUpdatedAt.value = Date.now()
  } catch {
    if (!silent) message.warning('推荐选题更新失败，请稍后重试')
  } finally {
    quickTopicsLoading.value = false
  }
}

function stopQuickTopicsPolling() {
  if (quickTopicsTimer) {
    clearInterval(quickTopicsTimer)
    quickTopicsTimer = null
  }
}

function startQuickTopicsPolling() {
  stopQuickTopicsPolling()
  fetchQuickTopics({ silent: true })
  // 不再自动轮询，用户手动点「刷新」按钮更新选题，避免频繁消耗 API
}

function normalizeIdList(value) {
  const raw = Array.isArray(value) ? value : (value ? [value] : [])
  return raw
    .map((id) => Number(id))
    .filter((id) => Number.isFinite(id) && id > 0)
}

async function loadOptions() {
  try {
    const [s, d, vp] = await Promise.all([
      styleApi.list(),
      documentsApi.list(),
      viewpointsApi.list({ active_only: true }),
    ])
    styles.value = s.data || []
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

  await fetchQuickTopics({ silent: true })

  if (generateStore.prefillTopic) {
    const prefill = generateStore.prefillTopic
    promptText.value = prefill.title || prefill.prompt || ''
    if (prefill.platform && ['douyin', 'xiaohongshu', 'weixin'].includes(prefill.platform)) {
      config.platform = prefill.platform
    }
    const docIds = normalizeIdList(prefill.product_doc_ids || prefill.product_doc_id)
    const analysisIds = normalizeIdList(prefill.viral_analysis_ids || prefill.viral_analysis_id)
    const viewpointIds = normalizeIdList(prefill.viewpoint_ids || prefill.viewpoint_id)
    if (docIds.length) config.product_doc_ids = docIds
    if (analysisIds.length) config.viral_analysis_ids = analysisIds
    if (viewpointIds.length) config.viewpoint_ids = viewpointIds
    syncBlocksFromConfig()
    generateStore.clearPrefillTopic()
    if (prefill.autoGenerate) {
      nextTick(() => sendPrompt())
    } else if (prefill.focusComposer !== false) {
      nextTick(() => composerRef.value?.focus())
    }
  }

  syncBlocksFromConfig()
}

async function maybeShowOnboarding() {
  if (localStorage.getItem('cs_onboarding_done') === '1') return
  if (sessionStorage.getItem('cs_onboarding_hidden') === '1') return

  try {
    const { data } = await statsApi.get()
    onboardingStats.creators = data?.creators || 0
    onboardingStats.documents = data?.documents || 0
    onboardingStats.topics = data?.topics || 0
    onboardingStats.generations = data?.generations || 0

    if (
      onboardingStats.creators > 0
      && onboardingStats.documents > 0
      && onboardingStats.topics > 0
      && onboardingStats.generations > 0
    ) {
      localStorage.setItem('cs_onboarding_done', '1')
      return
    }

    showOnboarding.value = true
  } catch {
    // 忽略引导统计异常，不影响主流程
  }
}

watch(() => config.style_template_id, syncBlocksFromConfig)
watch(() => config.product_doc_ids.slice(), syncBlocksFromConfig)
watch(() => config.viewpoint_ids.slice(), syncBlocksFromConfig)
watch(() => config.viral_analysis_ids.slice(), syncBlocksFromConfig)
watch(mentionPool, syncBlocksFromConfig)
watch(isWelcome, (value) => {
  if (value) startQuickTopicsPolling()
  else stopQuickTopicsPolling()
}, { immediate: true })

onMounted(async () => {
  await loadOptions()
  await maybeShowOnboarding()
  nextTick(() => {
    const el = chatListRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
})

onBeforeUnmount(() => {
  stopQuickTopicsPolling()
})
</script>

<style scoped>
.generate-page {
  min-height: calc(100vh - 44px);
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.generate-page.is-welcome {
  justify-content: flex-start;
  padding: 10px 0 18px;
}

.generate-page.is-chat {
  min-height: calc(100vh - 44px);
  max-height: calc(100vh - 44px);
  overflow: hidden;
}

/* Welcome Mode */
.hero {
  padding: 26px 0 10px;
  border-radius: 18px;
  background: linear-gradient(180deg, #e9fbfd 0%, #f5f5f7 100%);
  border: 1px solid rgba(11, 188, 212, 0.18);
  text-align: center;
}

.hero-title {
  font-size: 34px;
  line-height: 1.15;
  font-weight: 700;
  color: #1a1a1a;
}

.hero-accent {
  color: #0891b2;
}

.hero-sub {
  margin-top: 10px;
  color: #6b7280;
  font-size: 14px;
}

.search-wrap {
  margin-top: 20px;
  padding: 0 24px;
}

.search-container {
  max-width: 980px;
  margin: 0 auto;
  border-radius: 18px;
  background: #fff;
  border: 1px solid #e8e8e8;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
  overflow: visible;
}

.search-top {
  position: relative;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) 40px;
  gap: 8px;
  align-items: center;
  padding: 12px 16px 10px;
}

.search-add-btn {
  width: auto;
  height: 36px;
  min-height: unset;
  padding: 0 12px;
  border-radius: 8px;
  border: 1px solid #d6e4ea;
  background: #f7fbfc;
  color: #2f6f78;
  display: inline-flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  gap: 7px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.search-add-btn:hover {
  border-color: #0071e3;
  background: #e8f1fd;
  color: #0071e3;
}

.search-add-btn:active {
  transform: translateY(1px);
}

.search-add-btn span {
  line-height: 1;
  font-size: 12px;
  letter-spacing: 0.02em;
  white-space: nowrap;
  margin-left: 5px;
}

.search-input {
  width: 100%;
  height: 36px;
  min-height: unset;
  max-height: 120px;
  border: 1px solid #e2ebef;
  border-radius: 8px;
  outline: none;
  resize: none;
  overflow: hidden;
  font-size: 14px;
  line-height: 1.5;
  color: #1f2937;
  background: #fbfdfe;
  padding: 8px 12px;
  box-sizing: border-box;
  font-family: inherit;
  transition: border-color 0.2s, box-shadow 0.2s, background-color 0.2s;
}

.search-input::placeholder {
  color: #b7b7b7;
}

.search-input:focus {
  border-color: #89d8e3;
  box-shadow: 0 0 0 3px rgba(11, 188, 212, 0.12);
  background: #fff;
}

.search-submit {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  border: 0;
  background: #d0d5db;
  color: #fff;
  display: grid;
  place-items: center;
  cursor: pointer;
  align-self: end;
  transition: all 0.2s;
}

.search-submit.active,
.search-submit:hover {
  background: #0bbcd4;
}

.search-refs {
  padding: 0 16px 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.search-bottom {
  border-top: 1px solid #f0f0f0;
  padding: 10px 14px 14px;
  display: flex;
  align-items: center;
  gap: 8px;
  overflow-x: auto;
}

.mode-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 9999px;
  border: 1px solid #e4e4e4;
  background: #fff;
  color: #555;
  font-size: 12px;
  line-height: 1;
  white-space: nowrap;
  cursor: pointer;
  transition: all 0.2s;
}

.mode-chip:hover {
  color: #0bbcd4;
  border-color: #0bbcd4;
}

.mode-chip.active {
  color: #0bbcd4;
  border-color: #0bbcd4;
  background: rgba(11, 188, 212, 0.08);
}

.chip-icon {
  font-size: 12px;
}

.tools-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr 1fr;
  gap: 12px;
}

.tool-card {
  border: 1px solid #e2e8f0;
  background: #fff;
  border-radius: 14px;
  padding: 13px 14px;
  color: inherit;
  text-decoration: none;
  transition: border-color 0.2s, box-shadow 0.2s, transform 0.2s;
}

.tool-card:hover {
  border-color: #cbd5e1;
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
  transform: translateY(-2px);
}

.tool-card.wide {
  display: flex;
  align-items: center;
  gap: 12px;
}

.tool-card.small {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
}

.tool-thumb {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  border: 1px solid transparent;
}

.icon-topics {
  background: #fff4ed;
  border-color: #fed7aa;
  color: #ea580c;
}

.icon-creators {
  background: #eff6ff;
  border-color: #bfdbfe;
  color: #2563eb;
}

.icon-docs {
  background: #f8fafc;
  border-color: #cbd5e1;
  color: #334155;
}

.icon-styles {
  background: #f5f3ff;
  border-color: #ddd6fe;
  color: #7c3aed;
}

.icon-views {
  background: #fefce8;
  border-color: #fde68a;
  color: #ca8a04;
}

.tool-info {
  min-width: 0;
}

.tool-name {
  font-size: 13px;
  color: #0f172a;
  font-weight: 700;
}

.tool-desc {
  margin-top: 3px;
  font-size: 12px;
  color: #64748b;
}

.tools-row .rb-glow-card::before,
.tools-row .rb-glow-card::after {
  display: none;
}

.discover {
  border-radius: 14px;
  border: 1px solid #e8e8e8;
  background: #fff;
  padding: 14px;
}

.discover-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 700;
  color: #1f2937;
}

.rb-live-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #22c55e;
  box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.45);
  animation: rbPulseDot 1.8s ease-out infinite;
}

.discover-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.discover-head-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.discover-updated {
  font-size: 12px;
  color: #9ca3af;
}

.discover-empty {
  border: 1px dashed #e5e7eb;
  border-radius: 10px;
  padding: 18px;
  color: #9ca3af;
  font-size: 13px;
  text-align: center;
}

.discover-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.discover-item {
  border: 1px solid #ececec;
  border-radius: 10px;
  padding: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.discover-item:hover {
  border-color: #0bbcd4;
  background: rgba(11, 188, 212, 0.04);
}

.discover-item-title {
  font-size: 12px;
  line-height: 1.5;
  color: #374151;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.discover-item-meta {
  margin-top: 6px;
  font-size: 11px;
  color: #9ca3af;
}

/* Chat Mode */
.chat-header {
  border-radius: 12px;
  border: 1px solid #e8e8e8;
  background: #fff;
  padding: 10px 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.gen-shell {
  flex: 1;
  min-height: 0;
  border-radius: 14px;
  border: 1px solid #e8e8e8;
  background: #fff;
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

.chat-list.centered {
  justify-content: center;
}

.chat-msg {
  display: grid;
  grid-template-columns: 40px minmax(0, 1fr);
  gap: 10px;
  animation: msgIn 0.22s ease;
}

.chat-msg.is-user {
  grid-template-columns: minmax(0, 1fr) 40px;
}

.chat-msg.is-user .chat-avatar {
  grid-column: 2;
  background: #0bbcd4;
  color: #fff;
}

.chat-msg.is-user .chat-bubble {
  grid-column: 1;
  justify-self: end;
  background: rgba(11, 188, 212, 0.08);
  border-color: rgba(11, 188, 212, 0.2);
}

.chat-avatar {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: #f3f4f6;
  color: #555;
  display: grid;
  place-items: center;
  font-size: 11px;
  font-weight: 700;
}

.chat-bubble {
  max-width: min(960px, 100%);
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  background: #f8f8fa;
  padding: 10px 12px;
}

.chat-bubble.is-result {
  border: 1px solid rgba(14, 165, 233, 0.28);
  background:
    linear-gradient(165deg, rgba(255, 255, 255, 0.95), rgba(241, 249, 255, 0.92));
  box-shadow:
    0 10px 24px rgba(14, 165, 233, 0.12),
    0 1px 0 rgba(255, 255, 255, 0.72) inset;
}

.chat-bubble.result-compact .result-block {
  margin-top: 8px;
  padding-top: 8px;
}

.chat-text {
  color: #4b5563;
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
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 8px;
}

.result-title-wrap {
  min-width: 0;
}

.result-title {
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
}

.result-sub {
  margin-top: 3px;
  font-size: 12px;
  color: #64748b;
}

.result-actions :deep(.n-button) {
  border-radius: 9999px;
}

.result-block {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed rgba(0, 0, 0, 0.06);
}

.result-label {
  font-size: 11px;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.result-value {
  margin-top: 6px;
  color: #334155;
  line-height: 1.72;
  font-size: 14px;
}

.result-value.body {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.result-value.body.compact {
  max-height: 112px;
  overflow: hidden;
}

.pending-row {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #6b7280;
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
  color: #1f2937;
}

/* Shared Composer */
.composer-wrap {
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  background: #fff;
  padding: 10px 14px;
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
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 10px;
  background: #f8f8fa;
  padding: 8px;
  cursor: grab;
}

.material-card.dragging {
  opacity: 0.6;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

.material-handle {
  color: #9ca3af;
  display: grid;
  place-items: center;
}

.material-thumb,
.mention-thumb {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  overflow: hidden;
  background: rgba(11, 188, 212, 0.1);
  border: 1px solid rgba(11, 188, 212, 0.15);
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
  color: #0bbcd4;
  font-size: 14px;
  font-weight: 700;
}

.material-main,
.mention-main {
  min-width: 0;
}

.material-title,
.mention-title {
  font-size: 13px;
  color: #111827;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.material-source,
.mention-source {
  margin-top: 2px;
  font-size: 12px;
  color: #9ca3af;
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
  min-height: 48px;
  max-height: 140px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  background: #f8f8fa;
  border-radius: 12px;
  padding: 10px 12px;
  font-size: 14px;
  color: #111827;
  line-height: 1.7;
  resize: vertical;
  outline: none;
  transition: border-color 150ms, box-shadow 150ms;
}

.composer-input:focus {
  border-color: #0bbcd4;
  box-shadow: 0 0 0 3px rgba(11, 188, 212, 0.15);
}

.send-btn {
  align-self: flex-end;
  height: 36px;
}

.mention-panel {
  position: absolute;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 12px;
  background: #f8f8fa;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  max-height: 290px;
  overflow: auto;
  z-index: 60;
}

.search-top .mention-panel {
  left: 42px;
  right: 44px;
  top: calc(100% + 8px);
}

.composer-main .mention-panel {
  left: 0;
  right: 72px;
  bottom: calc(100% + 8px);
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
  background: rgba(0, 113, 227, 0.08);
}

.mention-empty {
  padding: 12px;
  color: #9ca3af;
  font-size: 13px;
}

.composer-foot {
  margin-top: 4px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.composer-hint {
  font-size: 12px;
  color: #9ca3af;
}

/* Drawer */
.preset-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.drawer-subtitle {
  font-size: 13px;
  color: #6b7280;
  font-weight: 600;
}

.preset-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}

.preset-card {
  border: 1px solid rgba(0, 0, 0, 0.06);
  background: #f8f8fa;
  border-radius: 10px;
  padding: 10px;
  text-align: left;
  cursor: pointer;
  color: inherit;
  transition: all 150ms;
}

.preset-card:hover,
.preset-card.active {
  border-color: #0071e3;
}

.preset-card.active {
  background: rgba(0, 113, 227, 0.08);
}

.preset-name {
  font-size: 14px;
  color: #111827;
  font-weight: 700;
}

.preset-desc {
  margin-top: 4px;
  font-size: 12px;
  color: #6b7280;
}

.preset-platform {
  margin-top: 6px;
  font-size: 12px;
  color: #0071e3;
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

/* ReactBits-style visual overrides */
.rb-theme {
  position: relative;
  isolation: isolate;
  font-family: 'Manrope', 'Noto Sans SC', 'PingFang SC', 'Segoe UI', sans-serif;
}

.rb-theme > *:not(.rb-canvas) {
  position: relative;
  z-index: 2;
}

.rb-canvas {
  position: absolute;
  inset: -28px -16px -16px;
  overflow: hidden;
  pointer-events: none;
  z-index: 0;
  border-radius: 24px;
}

.rb-blob {
  position: absolute;
  border-radius: 9999px;
  filter: blur(52px);
  opacity: 0.42;
  animation: rbFloat 14s ease-in-out infinite;
}

.rb-blob-a {
  width: 320px;
  height: 320px;
  left: -120px;
  top: -70px;
  background: radial-gradient(circle at 30% 30%, #14b8ff, #0bbcd4 65%, transparent 80%);
}

.rb-blob-b {
  width: 380px;
  height: 380px;
  right: -140px;
  top: 120px;
  background: radial-gradient(circle at 50% 40%, #a78bfa, #7c3aed 62%, transparent 82%);
  animation-delay: -5s;
}

.rb-blob-c {
  width: 300px;
  height: 300px;
  left: 32%;
  bottom: -120px;
  background: radial-gradient(circle at 50% 50%, #60a5fa, #818cf8 58%, transparent 84%);
  animation-delay: -8s;
}

.rb-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.45) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.45) 1px, transparent 1px);
  background-size: 34px 34px;
  opacity: 0.22;
  mask-image: radial-gradient(ellipse at center, rgba(0, 0, 0, 0.9), transparent 75%);
}

.rb-glass {
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.88), rgba(255, 255, 255, 0.72)) !important;
  border: 1px solid rgba(255, 255, 255, 0.75) !important;
  box-shadow: 0 16px 34px rgba(15, 23, 42, 0.08), 0 2px 8px rgba(15, 23, 42, 0.06);
  backdrop-filter: blur(12px);
}

.rb-panel {
  box-shadow: 0 18px 36px rgba(15, 23, 42, 0.12), 0 1px 1px rgba(255, 255, 255, 0.55) inset;
}

.hero {
  padding: 34px 0 16px;
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.85);
  background:
    linear-gradient(170deg, rgba(255, 255, 255, 0.88), rgba(255, 255, 255, 0.63)),
    radial-gradient(circle at 80% 10%, rgba(124, 58, 237, 0.2), transparent 40%),
    radial-gradient(circle at 18% 8%, rgba(11, 188, 212, 0.2), transparent 42%);
}

.hero-title {
  font-size: clamp(28px, 3.8vw, 42px);
  font-weight: 800;
  letter-spacing: -0.02em;
  color: #0f172a;
}

.hero-accent {
  background: linear-gradient(90deg, #06b6d4 0%, #3b82f6 48%, #8b5cf6 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  position: relative;
}

.rb-shiny {
  background-size: 200% 100%;
  animation: rbShiny 5.4s ease-in-out infinite;
}

.hero-sub {
  margin-top: 12px;
  font-size: 14px;
  color: #475569;
}

.search-container {
  position: relative;
  border-radius: 22px;
  border: 1px solid rgba(255, 255, 255, 0.78);
  box-shadow: 0 18px 38px rgba(2, 132, 199, 0.12), 0 0 0 1px rgba(255, 255, 255, 0.65) inset;
}

.search-container::after {
  content: '';
  position: absolute;
  inset: -1px;
  border-radius: inherit;
  pointer-events: none;
  background: linear-gradient(120deg, rgba(6, 182, 212, 0), rgba(6, 182, 212, 0.38), rgba(139, 92, 246, 0), rgba(6, 182, 212, 0));
  transform: translateX(-65%);
  opacity: 0;
  animation: rbSweep 7.6s linear infinite;
}

.search-top {
  padding: 16px 18px 12px;
}

.search-input {
  height: 36px;
  min-height: unset;
  font-size: 14px;
  line-height: 1.5;
  resize: none;
  overflow: hidden;
}

.search-submit {
  box-shadow: 0 8px 20px rgba(11, 188, 212, 0.3);
}

.rb-submit {
  transition: transform 180ms ease, box-shadow 180ms ease, background-color 180ms ease;
}

.search-submit.active,
.search-submit:hover {
  transform: translateY(-1px) scale(1.03);
}

.rb-submit:active {
  transform: translateY(0) scale(0.98);
}

.mode-chip {
  border-color: rgba(148, 163, 184, 0.35);
  color: #475569;
  background: rgba(255, 255, 255, 0.75);
}

.mode-chip.active {
  box-shadow: 0 6px 14px rgba(6, 182, 212, 0.18);
}

.rb-glow-card {
  position: relative;
  overflow: hidden;
}

.rb-glow-card::before {
  content: '';
  position: absolute;
  inset: -1px;
  border-radius: inherit;
  padding: 1px;
  background: linear-gradient(130deg, rgba(6, 182, 212, 0.65), rgba(139, 92, 246, 0.6), rgba(56, 189, 248, 0.65));
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  opacity: 0;
  transition: opacity 0.26s ease;
  pointer-events: none;
}

.rb-glow-card:hover::before {
  opacity: 1;
}

.rb-glow-card::after {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 18% 8%, rgba(56, 189, 248, 0.16), transparent 45%);
  opacity: 0;
  transition: opacity 220ms ease;
  pointer-events: none;
}

.rb-glow-card:hover::after {
  opacity: 1;
}

.rb-entrance {
  opacity: 0;
  transform: translateY(12px) scale(0.985);
  animation: rbRise 520ms cubic-bezier(0.22, 0.98, 0.32, 1) forwards;
  animation-delay: var(--rb-delay, 0ms);
}

.tool-card {
  border-color: #e2e8f0;
  background: #fff;
}

.tool-thumb {
  box-shadow: 0 2px 6px rgba(15, 23, 42, 0.06);
}

.discover {
  border-color: rgba(148, 163, 184, 0.22);
}

.discover-item {
  border-color: rgba(148, 163, 184, 0.3);
  background: linear-gradient(150deg, rgba(255, 255, 255, 0.7), rgba(241, 245, 249, 0.7));
}

.discover-item-title {
  color: #1e293b;
  font-weight: 600;
}

.chat-header {
  border-radius: 14px;
}

.chat-header,
.gen-shell,
.composer-wrap {
  transition: box-shadow 220ms ease, border-color 220ms ease;
}

.chat-bubble {
  border-color: rgba(148, 163, 184, 0.24) !important;
}

.composer-wrap {
  border-top-color: rgba(148, 163, 184, 0.25);
}

.composer-input {
  border-color: rgba(148, 163, 184, 0.3);
  background: rgba(248, 250, 252, 0.78);
}

.composer-input:focus,
.search-input:focus {
  box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.15);
}

.mention-panel {
  border-color: rgba(148, 163, 184, 0.25);
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.96), rgba(248, 250, 252, 0.96));
  box-shadow: 0 16px 28px rgba(15, 23, 42, 0.16);
}

.search-top .mention-panel {
  top: calc(100% + 10px);
  bottom: auto;
}

.generate-page.is-chat .rb-canvas {
  opacity: 0.72;
}

@keyframes rbFloat {
  0%,
  100% {
    transform: translate3d(0, 0, 0) scale(1);
  }
  50% {
    transform: translate3d(0, -14px, 0) scale(1.06);
  }
}

@keyframes rbRise {
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes rbSweep {
  0% {
    transform: translateX(-70%);
    opacity: 0;
  }
  10% {
    opacity: 1;
  }
  45% {
    transform: translateX(70%);
    opacity: 0;
  }
  100% {
    transform: translateX(70%);
    opacity: 0;
  }
}

@keyframes rbShiny {
  0%,
  100% {
    background-position: 0% 0;
  }
  50% {
    background-position: 100% 0;
  }
}

@keyframes rbPulseDot {
  0% {
    box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.4);
  }
  75% {
    box-shadow: 0 0 0 10px rgba(34, 197, 94, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(34, 197, 94, 0);
  }
}

/* DreamOS reference style overrides */
.generate-page {
  background: linear-gradient(180deg, #f7fafc 0%, #f2f5f9 58%, #eff3f7 100%);
  border-radius: 22px;
  padding: 0 16px 18px;
}

.generate-page.is-welcome {
  justify-content: flex-start;
  padding: 14px 16px 20px;
}

.welcome-shell {
  width: min(1540px, 100%);
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.welcome-head {
  text-align: center;
  padding: 12px 0 10px;
}

.hero {
  padding: 14px 10px 14px;
  margin-top: 2px;
  border-radius: 26px;
  border: 0;
  background: transparent;
  box-shadow: none;
}

.hero-title {
  font-size: clamp(30px, 4vw, 48px);
  letter-spacing: -0.03em;
}

.hero-sub {
  margin-top: 8px;
  font-size: 14px;
  color: #64748b;
}

.search-wrap {
  margin-top: 18px;
  padding: 0 18px;
}

.search-container {
  max-width: 920px;
  border-radius: 20px;
  border: 1px solid rgba(226, 232, 240, 0.9);
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
}

.search-top {
  padding: 14px;
  grid-template-columns: minmax(0, 1fr) 44px;
  align-items: center;
}

.search-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px 8px;
  border-top: 1px solid #eef3f8;
}

.search-add-btn {
  height: 40px;
  border-radius: 12px;
  border-color: #dbe7f2;
  background: #f8fbff;
}

.search-input {
  min-height: 96px;
  max-height: 180px;
  border-radius: 10px;
  border-color: #dbe5ef;
  background: #f9fbfd;
  resize: vertical;
}

.search-submit {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: #cfd8e3;
  box-shadow: none;
}

.search-submit.active,
.search-submit:hover {
  background: #15b5e8;
  box-shadow: 0 8px 18px rgba(21, 181, 232, 0.3);
}

.search-bottom {
  padding: 10px 12px 12px;
  gap: 7px;
  border-top: 1px solid #eef3f8;
}

.brief-panel {
  padding: 12px 14px 14px;
  border-top: 1px solid #eef3f8;
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: #fafcff;
}

.brief-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.brief-label {
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}

.brief-input {
  width: 100%;
  padding: 7px 10px;
  border: 1px solid #dbe7f2;
  border-radius: 8px;
  font-size: 13px;
  color: #1e293b;
  background: #fff;
  outline: none;
  box-sizing: border-box;
  font-family: inherit;
  transition: border-color 0.15s;
}

.brief-input:focus {
  border-color: #7dd3fc;
  box-shadow: 0 0 0 3px rgba(125, 211, 252, 0.15);
}

.brief-textarea {
  resize: vertical;
  min-height: 52px;
}

.mode-chip {
  background: #f8fafc;
  border-color: #dde6f0;
  color: #475569;
}

.mode-chip.active {
  border-color: rgba(14, 165, 233, 0.5);
  color: #0284c7;
  background: #eef7ff;
  box-shadow: none;
}

.tools-row {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
}

.tool-card {
  border-radius: 14px;
  border: 1px solid rgba(222, 230, 239, 0.95);
  background: rgba(255, 255, 255, 0.93);
  min-height: 92px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.tool-card:hover {
  border-color: rgba(148, 163, 184, 0.55);
  box-shadow: 0 10px 18px rgba(15, 23, 42, 0.08);
  transform: translateY(-2px);
}

.tool-thumb {
  width: 36px;
  height: 36px;
}

.tool-name {
  font-size: 14px;
}

.tool-desc {
  font-size: 12px;
}

.discover {
  border-radius: 14px;
  border: 1px solid rgba(222, 230, 239, 0.95);
  background: rgba(255, 255, 255, 0.92);
  padding: 12px;
}

.discover-empty {
  background: #f8fafc;
  border: 1px dashed #d5dee9;
  color: #94a3b8;
  padding: 16px;
}

.discover-item {
  border-color: rgba(222, 230, 239, 0.95);
  background: #fff;
}

.discover-item:hover {
  border-color: rgba(14, 165, 233, 0.55);
  background: #f0f9ff;
}

.discover-hint {
  margin-top: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 12px;
  color: #94a3b8;
}

@media (max-width: 1200px) {
  .tools-row {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .tool-card.wide {
    grid-column: span 3;
  }

  .discover-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 960px) {
  .generate-page {
    min-height: auto;
    gap: 12px;
  }

  .generate-page.is-welcome {
    justify-content: flex-start;
    padding: 4px 10px 14px;
  }

  .welcome-shell {
    width: 100%;
    margin: 0;
  }

  .welcome-head {
    padding: 8px 0 6px;
  }

  .hero {
    padding: 12px 0 8px;
  }

  .hero-title {
    font-size: 24px;
  }

  .hero-sub {
    padding: 0 10px;
    font-size: 13px;
  }

  .search-wrap {
    padding: 0 10px;
  }

  .search-top {
    grid-template-columns: minmax(0, 1fr) 36px;
    gap: 8px;
    padding: 10px;
  }

  .search-actions {
    padding: 6px 10px 8px;
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }

  .search-input {
    min-height: 62px;
  }

  .rb-live-dot {
    width: 7px;
    height: 7px;
  }

  .search-bottom {
    padding: 8px 10px 10px;
  }

  .tools-row {
    grid-template-columns: 1fr;
  }

  .tool-card.wide {
    grid-column: auto;
  }

  .discover-grid {
    grid-template-columns: 1fr;
  }

  .generate-page.is-chat {
    min-height: calc(100vh - 96px);
    max-height: calc(100vh - 96px);
  }

  .chat-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .chat-list {
    padding: 10px;
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

  .search-top .mention-panel,
  .composer-main .mention-panel {
    left: 0;
    right: 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .rb-blob,
  .rb-shiny,
  .rb-live-dot,
  .rb-entrance,
  .search-container::after {
    animation: none !important;
    transition: none !important;
  }

  .rb-entrance {
    opacity: 1;
    transform: none;
  }
}

/* ═══════════════════════════════════════════════
   FRESH & CLEAN THEME — overrides all above
   Palette: sky-50 bg / cyan-600 brand / flat style
   ═══════════════════════════════════════════════ */

/* Remove all decorative bl blob orbs */
.rb-canvas { display: none !important; }

/* Page container — transparent to let App.vue bg show */
.generate-page {
  background: transparent !important;
  border-radius: 0 !important;
}
.generate-page.is-welcome {
  padding: 16px 0 24px !important;
}

/* Hero — clean flat text, no background decoration */
.hero {
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
  padding: 10px 0 14px !important;
  backdrop-filter: none !important;
}
.hero-title {
  font-size: clamp(26px, 3.6vw, 40px);
  font-weight: 800;
  letter-spacing: -0.025em;
  color: #0f172a;
  line-height: 1.18;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
/* Solid accent color — no gradient, no animation */
.hero-accent {
  background: none !important;
  -webkit-background-clip: unset !important;
  background-clip: unset !important;
  color: #0891b2 !important;
  animation: none !important;
}
.hero-sub {
  color: #64748b;
  font-size: 14px;
  margin-top: 10px;
}

/* Search container — clean elevated card */
.search-container {
  border-radius: 18px !important;
  border: 1px solid #e0f2fe !important;
  background: #ffffff !important;
  box-shadow: 0 4px 20px rgba(8,145,178,0.09), 0 1px 4px rgba(8,145,178,0.05) !important;
  backdrop-filter: none !important;
}
.search-container::after { display: none !important; }
.search-input {
  background: #f8fcff !important;
  border-color: #dbeafe !important;
  color: #0f172a !important;
}
.search-input:focus {
  border-color: #7dd3fc !important;
  box-shadow: 0 0 0 3px rgba(8,145,178,0.1) !important;
  background: #fff !important;
}
.search-input::placeholder { color: #94a3b8 !important; }
.search-submit {
  background: #cbd5e1 !important;
  box-shadow: none !important;
}
.search-submit.active,
.search-submit:hover {
  background: #0891b2 !important;
  box-shadow: 0 4px 12px rgba(8,145,178,0.28) !important;
  transform: translateY(-1px) scale(1.02) !important;
}

/* Mode chips */
.mode-chip {
  background: #ffffff !important;
  border-color: #e0f2fe !important;
  color: #64748b !important;
}
.mode-chip:hover {
  color: #0891b2 !important;
  border-color: #7dd3fc !important;
  background: #f0f9ff !important;
}
.mode-chip.active {
  color: #0891b2 !important;
  border-color: #7dd3fc !important;
  background: #e0f2fe !important;
  box-shadow: none !important;
}

/* Tool cards — flat style with hover lift */
.tool-card {
  border: 1px solid #e0f2fe !important;
  background: #ffffff !important;
  box-shadow: 0 1px 3px rgba(8,145,178,0.05) !important;
  min-height: 80px !important;
  gap: 12px !important;
}
.tool-card:hover {
  border-color: #7dd3fc !important;
  box-shadow: 0 6px 18px rgba(8,145,178,0.1) !important;
  transform: translateY(-2px) !important;
}
/* Disable glow border pseudo-elements */
.rb-glow-card::before, .rb-glow-card::after { display: none !important; }
.tool-thumb {
  box-shadow: none !important;
}

/* Discover / topics section */
.discover {
  border: 1px solid #e0f2fe !important;
  background: #ffffff !important;
  box-shadow: 0 1px 4px rgba(8,145,178,0.05) !important;
  padding: 12px !important;
  border-radius: 14px !important;
}
.discover-item {
  border: 1px solid #e0f2fe !important;
  background: #fafeff !important;
  transition: all 0.18s ease !important;
}
.discover-item:hover {
  border-color: #7dd3fc !important;
  background: #f0f9ff !important;
  transform: translateY(-1px) !important;
}
.discover-item-title { color: #1e293b !important; font-weight: 600 !important; }
.discover-empty {
  background: #f8fafc !important;
  border: 1px dashed #bae6fd !important;
  color: #94a3b8 !important;
}
.discover-empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 18px;
  background: #f8fafc;
  border: 1px dashed #bae6fd;
  border-radius: 10px;
  font-size: 13px;
  color: #94a3b8;
}
.discover-empty-icon { font-size: 16px; line-height: 1; }
.discover-link {
  color: #0891b2;
  text-decoration: none;
  font-weight: 600;
}
.discover-link:hover { text-decoration: underline; }

/* Glass effect — replace with flat cards */
.rb-glass {
  background: #ffffff !important;
  border: 1px solid #e0f2fe !important;
  box-shadow: 0 2px 8px rgba(8,145,178,0.06) !important;
  backdrop-filter: none !important;
}
.rb-panel {
  box-shadow: 0 2px 12px rgba(8,145,178,0.07), 0 1px 3px rgba(8,145,178,0.04) !important;
}

/* Chat mode */
.chat-header {
  background: #ffffff !important;
  border: 1px solid #e0f2fe !important;
  box-shadow: 0 1px 4px rgba(8,145,178,0.05) !important;
}
.chat-bubble {
  background: #f8fafc !important;
  border: 1px solid #e8f4fb !important;
}
.chat-bubble.is-result {
  background: linear-gradient(160deg, #f0f9ff, #ffffff) !important;
  border: 1px solid #bae6fd !important;
  box-shadow: 0 4px 14px rgba(8,145,178,0.08) !important;
}
.chat-msg.is-user .chat-bubble {
  background: #e0f2fe !important;
  border-color: #bae6fd !important;
}
.chat-msg.is-user .chat-avatar {
  background: #0891b2 !important;
}
.chat-avatar {
  background: #f0f9ff !important;
  color: #0891b2 !important;
  border: 1px solid #e0f2fe !important;
}
.composer-wrap {
  background: #ffffff !important;
  border-top: 1px solid #e0f2fe !important;
}
.composer-input {
  background: #f8fafc !important;
  border-color: #dbeafe !important;
}
.composer-input:focus {
  border-color: #7dd3fc !important;
  box-shadow: 0 0 0 3px rgba(8,145,178,0.1) !important;
  background: #fff !important;
}
.gen-shell {
  border: 1px solid #e0f2fe !important;
  background: #ffffff !important;
}
.material-card {
  background: #f8fafc !important;
  border: 1px solid #e0f2fe !important;
}
.mention-panel {
  background: #ffffff !important;
  border: 1px solid #e0f2fe !important;
  box-shadow: 0 8px 24px rgba(8,145,178,0.12) !important;
  backdrop-filter: none !important;
}

/* Brief panel */
.brief-panel {
  background: #f8fcff !important;
  border-top: 1px solid #e0f2fe !important;
}
.brief-input {
  border-color: #dbeafe !important;
  background: #fff !important;
}
.brief-input:focus {
  border-color: #7dd3fc !important;
  box-shadow: 0 0 0 3px rgba(8,145,178,0.1) !important;
}
.brief-chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.brief-chip {
  border: 1px solid #dbeafe;
  background: #ffffff;
  color: #475569;
  border-radius: 999px;
  font-size: 12px;
  line-height: 1;
  padding: 7px 11px;
  cursor: pointer;
  transition: all 0.16s ease;
}
.brief-chip:hover {
  border-color: #7dd3fc;
  background: #f0f9ff;
}
.brief-chip.active {
  border-color: #0891b2;
  color: #0e7490;
  background: #ecfeff;
}
.brief-hint {
  margin-top: 2px;
  color: #94a3b8;
  font-size: 12px;
}

.onboarding-header {
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
}
.onboarding-intro {
  font-size: 13px;
  color: #475569;
  margin-bottom: 12px;
}
.onboarding-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.onboarding-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  border: 1px solid #e0f2fe;
  border-radius: 10px;
  background: #ffffff;
  padding: 10px 12px;
}
.onboarding-item.done {
  background: #f0fdf4;
  border-color: #bbf7d0;
}
.onboarding-step {
  width: 22px;
  height: 22px;
  border-radius: 999px;
  background: #0891b2;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.onboarding-item.done .onboarding-step {
  background: #16a34a;
}
.onboarding-main {
  flex: 1;
  min-width: 0;
}
.onboarding-title {
  font-size: 13px;
  font-weight: 600;
  color: #0f172a;
}
.onboarding-desc {
  margin-top: 3px;
  font-size: 12px;
  line-height: 1.55;
  color: #64748b;
}

@media (max-width: 768px) {
  .generate-page {
    gap: 12px;
  }
  .search-wrap {
    padding: 0 8px !important;
  }
  .search-actions {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  .tools-row {
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  }
  .tool-card {
    min-height: 72px !important;
  }
  .discover-grid {
    grid-template-columns: 1fr !important;
  }
  .chat-msg {
    grid-template-columns: minmax(0, 1fr) !important;
  }
  .chat-avatar {
    display: none !important;
  }
  .result-head {
    flex-direction: column;
    align-items: flex-start;
  }
  .result-actions {
    width: 100%;
    justify-content: flex-start;
    flex-wrap: wrap;
  }
  .composer-wrap {
    padding: 10px !important;
  }
  .material-card {
    grid-template-columns: auto minmax(0, 1fr) auto !important;
  }
  .onboarding-item {
    flex-wrap: wrap;
  }
}

/* Search actions bottom bar */
.search-actions { border-top: 1px solid #e0f2fe !important; }
.search-bottom { border-top: 1px solid #e0f2fe !important; }
</style>
