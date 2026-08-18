<template>
  <div>
    <!-- 页头 -->
    <div class="page-header">
      <div>
        <div class="page-title">爆款选题库</div>
        <div class="page-subtitle">关键词搜索爆款短视频，采用后一键发起文案生成</div>
      </div>
      <n-button secondary @click="openSavedDrawer">
        <template #icon><n-icon><BookmarksOutline /></n-icon></template>
        已保存选题
        <n-badge v-if="savedTopics.length" :value="savedTopics.length" :max="99" style="margin-left:6px;" />
      </n-button>
    </div>

    <!-- 搜索区 -->
    <div class="search-card">
      <n-form inline :label-width="0" style="gap:12px;flex-wrap:wrap;">
        <n-form-item style="flex:1;min-width:200px;">
          <n-input
            v-model:value="keyword"
            placeholder="输入行业关键词，如：美妆、减脂、护肤"
            size="large"
            clearable
            @keydown.enter="search"
          >
            <template #prefix><n-icon><SearchOutline /></n-icon></template>
          </n-input>
        </n-form-item>

        <n-form-item label="平台" label-style="color:rgba(255,255,255,.6)">
          <n-checkbox-group v-model:value="platforms" style="display:flex;gap:8px;">
            <n-checkbox value="douyin">抖音</n-checkbox>
            <n-checkbox value="xiaohongshu">小红书</n-checkbox>
            <n-checkbox value="weixin">视频号</n-checkbox>
          </n-checkbox-group>
        </n-form-item>

        <n-form-item label="排序" label-style="color:rgba(255,255,255,.6)">
          <n-select v-model:value="sort" :options="sortOptions" style="width:120px;" />
        </n-form-item>

        <n-form-item label="视频类型" label-style="color:rgba(255,255,255,.6)">
          <n-select v-model:value="videoType" :options="videoTypeOptions" style="width:160px;" />
        </n-form-item>

        <n-form-item label="发布时间" label-style="color:rgba(255,255,255,.6)">
          <n-select v-model:value="publishTime" :options="publishTimeOptions" style="width:120px;" />
        </n-form-item>

        <n-form-item label="数量" label-style="color:rgba(255,255,255,.6)">
          <n-select v-model:value="limit" :options="limitOptions" style="width:90px;" />
        </n-form-item>

        <n-form-item>
          <n-button type="primary" size="large" :loading="searching" @click="search">
            <template #icon><n-icon><SearchOutline /></n-icon></template>
            搜索爆款
          </n-button>
        </n-form-item>
      </n-form>
    </div>

    <!-- 操作栏 -->
    <div v-if="results.length" class="action-bar">
      <n-space>
        <n-button secondary @click="toggleAll">
          {{ allSelected ? '取消全选' : '全选' }}
        </n-button>
        <n-button
          type="primary"
          :disabled="!selectedVideos.length"
          @click="batchSaveToLibrary"
        >
          <template #icon><n-icon><BookmarkOutline /></n-icon></template>
          批量保存选题 ({{ selectedVideos.length }})
        </n-button>
        <n-button
          :disabled="!selectedIds.length"
          @click="useAsTopics"
        >
          <template #icon><n-icon><SparklesOutline /></n-icon></template>
          用于生成文案 ({{ selectedIds.length }})
        </n-button>
        <n-button
          :disabled="!selectedIds.length"
          @click="batchAnalyzeSelected"
        >
          <template #icon><n-icon><AnalyticsOutline /></n-icon></template>
          批量分析 ({{ selectedIds.length }})
        </n-button>
        <n-button
          :disabled="!selectedIds.length"
          :loading="batchFetchingDetails"
          @click="batchFetchSelectedDetails"
        >
          获取视频文案 ({{ selectedIds.length }})
        </n-button>
        <n-button
          :disabled="!selectedIds.length"
          @click="openAddToDocsModal"
        >
          <template #icon><n-icon><FolderOpenOutline /></n-icon></template>
          加入资料库 ({{ selectedIds.length }})
        </n-button>
      </n-space>
      <n-text depth="3" style="font-size:13px;">共 {{ results.length }} 条结果</n-text>
    </div>

    <!-- 结果网格 -->
    <n-spin :show="searching">
      <div v-if="!results.length && !searching" class="empty-state-big">
        <div class="empty-guide">
          <div class="empty-icon"><n-icon size="48" color="var(--c-text-4, #94a3b8)"><SearchOutline /></n-icon></div>
          <div class="empty-title">搜索行业关键词，发现爆款选题</div>
          <div class="empty-desc">在上方输入关键词（如「美妆」「减脂」「育儿」），点击「搜索爆款」即可</div>
        </div>

        <!-- 最近搜过 -->
        <div v-if="historyKeywords.length" class="recent-searches">
          <div class="recent-title">最近搜过<span class="recent-hint">（点击直接查看结果）</span></div>
          <div class="recent-list">
            <div
              v-for="h in historyKeywords"
              :key="h.keyword"
              class="recent-item"
              @click="loadHistory(h.keyword)"
            >
              <span class="recent-keyword">{{ h.keyword }}</span>
              <span class="recent-meta">{{ h.count }} 条结果</span>
            </div>
          </div>
        </div>
      </div>

      <n-grid v-else cols="1 s:2 m:3" responsive="screen" :x-gap="14" :y-gap="14">
        <n-gi v-for="v in results" :key="`${v.platform}-${v.video_id}`">
          <div
            class="video-card"
            :class="{ selected: isSelected(v) }"
            @click="toggleSelect(v)"
          >
            <!-- 选择框 -->
            <div class="select-badge">
              <n-checkbox
                :checked="isSelected(v)"
                @click.stop
                @update:checked="toggleSelect(v)"
              />
            </div>

            <!-- 封面 -->
            <div class="video-cover">
              <img
                v-if="v.cover_url"
                :src="v.cover_url"
                alt="cover"
                referrerpolicy="no-referrer"
                style="width:100%;height:100%;object-fit:cover;"
                @error="e => handleImgError(e, v)"
              />
              <div v-else class="cover-placeholder">
                <n-icon size="32" color="rgba(255,255,255,.2)"><VideocamOutline /></n-icon>
              </div>
              <div class="platform-tag">{{ platformZh(v.platform) }}</div>
              <div v-if="v._hasAnalysis || v._analysis" class="analyzed-badge">已分析</div>
            </div>

            <!-- 内容 -->
            <div class="video-body">
              <div class="video-title">{{ v.title || '(无标题)' }}</div>
              <div class="video-author">@{{ v.author || '未知作者' }}</div>

              <div class="video-stats">
                <span class="stat">
                  <n-icon size="13"><HeartOutline /></n-icon>
                  {{ formatNum(v.like_count) }}
                </span>
                <span class="stat">
                  <n-icon size="13"><ChatbubbleOutline /></n-icon>
                  {{ formatNum(v.comment_count) }}
                </span>
                <span v-if="v.collect_count" class="stat">
                  <n-icon size="13"><BookmarkOutline /></n-icon>
                  {{ formatNum(v.collect_count) }}
                </span>
                <span v-if="v.play_count" class="stat">
                  <n-icon size="13"><PlayOutline /></n-icon>
                  {{ formatNum(v.play_count) }}
                </span>
                <span v-if="v.like_play_ratio && v.play_count" class="stat ratio-tag">
                  赞{{ (v.like_play_ratio * 100).toFixed(1) }}%
                </span>
              </div>

              <div v-if="v.tags?.length" class="video-tags">
                <n-tag
                  v-for="tag in (v.tags || []).slice(0,3)"
                  :key="tag"
                  size="tiny"
                  :bordered="false"
                  style="margin-right:4px;background:rgba(99,102,241,.15);color:#818cf8;"
                >
                  #{{ tag }}
                </n-tag>
              </div>

              <!-- 爆款比率徽章 -->
              <div v-if="v._analysis" class="ratio-badges">
                <n-tag size="tiny" :type="ratioLevel(v._analysis.like_play_level).type" style="margin-right:4px;">
                  赞{{ ratioLevel(v._analysis.like_play_level).text }}
                </n-tag>
                <n-tag size="tiny" :type="ratioLevel(v._analysis.comment_play_level).type" style="margin-right:4px;">
                  评{{ ratioLevel(v._analysis.comment_play_level).text }}
                </n-tag>
                <n-tag size="tiny" :type="ratioLevel(v._analysis.collect_play_level).type">
                  藏{{ ratioLevel(v._analysis.collect_play_level).text }}
                </n-tag>
              </div>

              <!-- 操作按钮 -->
              <div class="card-actions">
                <n-button
                  size="tiny"
                  :type="v._saved ? 'default' : 'primary'"
                  :ghost="!v._saved"
                  :disabled="v._saved"
                  @click.stop="saveToLibrary(v)"
                >
                  <template #icon><n-icon><BookmarkOutline /></n-icon></template>
                  {{ v._saved ? '已保存' : '保存选题' }}
                </n-button>
                <a
                  v-if="v.video_url"
                  :href="v.video_url"
                  target="_blank"
                  rel="noopener noreferrer"
                  @click.stop
                  style="text-decoration:none;"
                >
                  <n-button size="tiny" secondary>
                    <template #icon><n-icon><OpenOutline /></n-icon></template>
                    原视频
                  </n-button>
                </a>
                <n-button
                  size="tiny"
                  secondary
                  :loading="fetchingDetailIds.has(v.id || `${v.platform}-${v.video_id}`)"
                  @click.stop="fetchTopicDetail(v)"
                >
                  {{ hasFetchedScript(v) ? '重新获取文案' : '获取原视频文案' }}
                </n-button>
                <n-button
                  v-if="v._analysis"
                  size="tiny"
                  secondary
                  @click.stop="viewAnalysis(v)"
                >查看分析</n-button>
                <n-button
                  size="tiny"
                  secondary
                  :loading="analyzingIds.has(v.id)"
                  @click.stop="analyzeVideo(v)"
                >
                  <template #icon><n-icon><AnalyticsOutline /></n-icon></template>
                  {{ v._analysis ? '重新分析' : '分析爆款' }}
                </n-button>
              </div>
            </div>
          </div>
        </n-gi>
      </n-grid>
    </n-spin>

    <!-- 已保存选题 抽屉 -->
    <n-drawer v-model:show="showSavedDrawer" :width="840" placement="right">
      <n-drawer-content :title="`已保存选题（${savedTopics.length}）`" closable>
        <template #header-extra>
          <n-button v-if="!batchMode" text type="warning" size="small" @click="batchMode = true; savedSelectedIds = []" style="margin-right:8px;">
            批量删除
          </n-button>
          <template v-if="batchMode">
            <n-button text size="small" @click="toggleSelectAll" style="margin-right:8px;">
              {{ savedSelectedIds.length === filteredSaved.length ? '取消全选' : '全选' }}
            </n-button>
            <n-button type="error" size="small" :disabled="savedSelectedIds.length === 0" :loading="deletingBatch" @click="handleBatchDelete" style="margin-right:8px;">
              删除选中({{ savedSelectedIds.length }})
            </n-button>
            <n-button text size="small" @click="batchMode = false; savedSelectedIds = []" style="margin-right:8px;">
              取消
            </n-button>
          </template>
          <n-select
            v-model:value="savedFilter"
            :options="[
              { label: '全部', value: '' },
              { label: '待评审', value: '待评审' },
              { label: '已采纳', value: '已采纳' },
              { label: '已使用', value: '已使用' },
              { label: '已忽略', value: '已忽略' },
            ]"
            style="width:100px;"
            size="small"
          />
        </template>

        <n-spin :show="loadingSaved">
          <div v-if="filteredSaved.length === 0" style="text-align:center;padding:60px 0;color:#94a3b8;">
            还没有保存的选题，搜索爆款后点击「保存选题」加入。
          </div>

          <n-grid :cols="2" :x-gap="12" :y-gap="12">
            <n-gi v-for="t in filteredSaved" :key="t.id">
              <div class="st-card" :class="{ 'st-card-selected': batchMode && savedSelectedIds.includes(t.id) }" @click="batchMode && toggleSavedSelect(t.id)">
                <!-- 批量选择复选框 -->
                <n-checkbox v-if="batchMode" :checked="savedSelectedIds.includes(t.id)" class="st-checkbox" @click.stop @update:checked="toggleSavedSelect(t.id)" />
                <!-- 封面 -->
                <div class="st-cover">
                  <img v-if="t.cover_url" :src="t.cover_url" alt="cover" referrerpolicy="no-referrer" style="width:100%;height:100%;object-fit:cover;" @error="e => handleImgError(e, t)" />
                  <div v-else class="st-cover-ph"><n-icon size="24" color="rgba(255,255,255,.2)"><VideocamOutline /></n-icon></div>
                  <div class="st-platform">{{ platformZh(t.platform) }}</div>
                  <div v-if="t.has_analysis || t._analysis" class="analyzed-badge">已分析</div>
                  <n-tag class="st-status-tag" size="tiny" :bordered="false"
                    :type="{ '已采纳':'success', '已使用':'info', '已忽略':'default', '待评审':'warning' }[t.status] || 'default'">
                    {{ t.status }}
                  </n-tag>
                </div>

                <!-- 内容 -->
                <div class="st-body">
                  <div class="st-title">{{ t.title || '(无标题)' }}</div>
                  <div class="st-author">@{{ t.author || '未知作者' }}</div>

                  <div class="st-stats">
                    <span class="st-stat"><n-icon size="12"><HeartOutline /></n-icon>{{ formatNum(t.like_count) }}</span>
                    <span class="st-stat"><n-icon size="12"><ChatbubbleOutline /></n-icon>{{ formatNum(t.comment_count) }}</span>
                    <span v-if="t.collect_count" class="st-stat"><n-icon size="12"><BookmarkOutline /></n-icon>{{ formatNum(t.collect_count) }}</span>
                    <span v-if="t.play_count" class="st-stat"><n-icon size="12"><PlayOutline /></n-icon>{{ formatNum(t.play_count) }}</span>
                    <span v-if="t.like_play_ratio" class="st-stat st-ratio">赞{{ (t.like_play_ratio * 100).toFixed(1) }}%</span>
                  </div>

                  <div v-if="t.keyword" style="margin-bottom:6px;">
                    <n-tag size="tiny" :bordered="false" style="background:rgba(99,102,241,.1);color:#818cf8;">#{{ t.keyword }}</n-tag>
                  </div>

                  <!-- 操作按钮 -->
                  <div class="st-actions">
                    <n-button size="tiny" type="primary" ghost @click="useSavedTopic(t)">用于生成</n-button>
                    <a v-if="t.video_url" :href="t.video_url" target="_blank" rel="noopener noreferrer" @click.stop style="text-decoration:none;">
                      <n-button size="tiny" secondary>
                        <template #icon><n-icon><OpenOutline /></n-icon></template>
                        原视频
                      </n-button>
                    </a>
                    <n-button
                      size="tiny"
                      secondary
                      :loading="fetchingDetailIds.has(t.id || `${t.platform}-${t.video_id}`)"
                      @click="fetchTopicDetail(t)"
                    >
                      {{ hasFetchedScript(t) ? '重新获取文案' : '获取原视频文案' }}
                    </n-button>
                    <n-button size="tiny" secondary :loading="savedAnalyzingIds.has(t.id)" @click="analyzeSavedVideo(t)">
                      <template #icon><n-icon><AnalyticsOutline /></n-icon></template>
                      {{ t._analysis ? '重新分析' : '分析' }}
                    </n-button>
                    <n-button v-if="t._analysis" size="tiny" secondary @click="viewSavedAnalysis(t)">查看分析</n-button>
                    <n-dropdown
                      :options="[
                        { label: '已采纳', key: '已采纳' },
                        { label: '已忽略', key: '已忽略' },
                        { label: '待评审', key: '待评审' },
                      ]"
                      @select="(k) => updateSavedStatus(t, k)"
                    >
                      <n-button size="tiny" quaternary>状态…</n-button>
                    </n-dropdown>
                    <n-popconfirm @positive-click="deleteSavedTopic(t)">
                      <template #trigger>
                        <n-button size="tiny" quaternary type="error">
                          <template #icon><n-icon><TrashOutline /></n-icon></template>
                        </n-button>
                      </template>
                      确定删除这条选题？
                    </n-popconfirm>
                  </div>
                </div>
              </div>
            </n-gi>
          </n-grid>
        </n-spin>
      </n-drawer-content>
    </n-drawer>

    <!-- 加入资料库弹窗 -->
    <n-modal v-model:show="showAddToDocsModal" preset="card" title="加入资料库" style="width: 420px;">
      <n-form label-placement="top" :show-feedback="false">
        <n-form-item label="文件夹（可选）">
          <n-select
            v-model:value="addToDocsFolder"
            :options="docsFolderOptions"
            filterable
            tag
            placeholder="选择或输入文件夹名，如：爆款文案"
            clearable
          />
        </n-form-item>
        <n-alert type="info" :bordered="false" style="border-radius:8px;font-size:13px;">
          将选中的 {{ selectedIds.length }} 条视频文案（已抓取文案的部分）添加到产品资料库，可在文案生成时引用。
        </n-alert>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showAddToDocsModal = false">取消</n-button>
          <n-button type="primary" :loading="addingToDocs" @click="confirmAddToDocs">确认添加</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 爆款分析详情弹窗 -->
    <n-modal v-model:show="showAnalysisModal" preset="card" style="width: 680px;">
      <template #header>爆款分析 — {{ currentAnalysisTitle }}</template>
      <div v-if="currentAnalysis" class="analysis-modal">
        <!-- 3比率 -->
        <div class="ratio-row">
          <div class="ratio-item">
            <div class="ratio-label">点赞率</div>
            <div class="ratio-value">{{ currentAnalysis.like_play_ratio != null ? (currentAnalysis.like_play_ratio * 100).toFixed(2) + '%' : 'N/A' }}</div>
            <n-tag size="small" :type="ratioLevel(currentAnalysis.like_play_level).type">
              {{ ratioLevel(currentAnalysis.like_play_level).text }}
            </n-tag>
          </div>
          <div class="ratio-item">
            <div class="ratio-label">评论率</div>
            <div class="ratio-value">{{ currentAnalysis.comment_play_ratio != null ? (currentAnalysis.comment_play_ratio * 100).toFixed(2) + '%' : 'N/A' }}</div>
            <n-tag size="small" :type="ratioLevel(currentAnalysis.comment_play_level).type">
              {{ ratioLevel(currentAnalysis.comment_play_level).text }}
            </n-tag>
          </div>
          <div class="ratio-item">
            <div class="ratio-label">收藏率</div>
            <div class="ratio-value">{{ currentAnalysis.collect_play_ratio != null ? (currentAnalysis.collect_play_ratio * 100).toFixed(2) + '%' : 'N/A' }}</div>
            <n-tag size="small" :type="ratioLevel(currentAnalysis.collect_play_level).type">
              {{ ratioLevel(currentAnalysis.collect_play_level).text }}
            </n-tag>
          </div>
        </div>

        <n-divider style="margin: 16px 0;" />

        <!-- AI 分析 -->
        <n-tabs type="line" animated>
          <n-tab-pane name="resonance" tab="点赞共鸣">
            <div class="analysis-label">博主说了什么让观众点赞？找到了哪些观点/金句/共鸣点</div>
            <div class="analysis-text">{{ currentAnalysis.resonance_analysis || '暂无分析' }}</div>
          </n-tab-pane>
          <n-tab-pane name="discussion" tab="讨论钩子">
            <div class="analysis-label">视频中哪部分内容引发了观众去评论区讨论？</div>
            <div class="analysis-text">{{ currentAnalysis.discussion_analysis || '暂无分析' }}</div>
          </n-tab-pane>
          <n-tab-pane name="value" tab="收藏价值">
            <div class="analysis-label">视频提供了什么值得收藏的知识密度/实用内容？</div>
            <div class="analysis-text">{{ currentAnalysis.value_analysis || '暂无分析' }}</div>
          </n-tab-pane>
          <n-tab-pane name="why" tab="爆款诊断">
            <div class="analysis-label">话题 · 观点 · 金句 · 共鸣 · 讨论钩子 · 知识价值 · 最值得复制的做法</div>
            <div class="analysis-text analysis-highlight">{{ currentAnalysis.why_viral_summary || '暂无分析' }}</div>
          </n-tab-pane>
        </n-tabs>
      </div>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import {
  SearchOutline, SparklesOutline,
  VideocamOutline, HeartOutline, ChatbubbleOutline,
  PlayOutline, AnalyticsOutline, OpenOutline, FolderOpenOutline,
  BookmarkOutline, BookmarksOutline, TrashOutline,
} from '@vicons/ionicons5'
import { topicsApi, analyzerApi, documentsApi } from '../api/index.js'
import { useGenerateStore } from '../stores/generate.js'

const router = useRouter()
const message = useMessage()
const generateStore = useGenerateStore()

// ── 搜索状态（从 sessionStorage 恢复搜索条件） ────────
const _cachedCond = JSON.parse(sessionStorage.getItem('cs_topics_cond') || 'null')
const keyword = ref(_cachedCond?.keyword || '')
const platforms = ref(_cachedCond?.platforms || ['douyin', 'xiaohongshu'])
const sort = ref(_cachedCond?.sort || 'likes')
const videoType = ref(_cachedCond?.videoType || '')
const publishTime = ref(_cachedCond?.publishTime || 0)
const limit = ref(_cachedCond?.limit || 30)
const searching = ref(false)
const results = ref([])
const selected = ref(new Set())

// 缓存搜索条件（不存结果，结果从数据库加载）
function _saveSearchCond() {
  sessionStorage.setItem('cs_topics_cond', JSON.stringify({
    keyword: keyword.value,
    platforms: platforms.value,
    sort: sort.value,
    videoType: videoType.value,
    publishTime: publishTime.value,
    limit: limit.value,
  }))
}

// ── 搜索历史关键词 ──────────────────────────
const historyKeywords = ref([])

async function loadHistoryKeywords() {
  try {
    const { data } = await topicsApi.keywords()
    historyKeywords.value = data
  } catch { /* ignore */ }
}

async function loadHistory(kw) {
  keyword.value = kw
  _saveSearchCond()
  searching.value = true
  selected.value.clear()
  try {
    const { data } = await topicsApi.list({ keyword: kw, limit: 200 })
    results.value = data.map(t => ({ ...t, _saved: true, _hasAnalysis: !!t.has_analysis, _analysis: t.analysis || null }))
  } catch {
    message.error('加载失败')
  } finally {
    searching.value = false
  }
}

// ── 爆款分析状态 ─────────────────────────────
const analyzingIds = ref(new Set())
const fetchingDetailIds = ref(new Set())
const batchFetchingDetails = ref(false)
const showAnalysisModal = ref(false)
const currentAnalysis = ref(null)
const currentAnalysisTitle = ref('')

const sortOptions = [
  { label: '最多点赞', value: 'likes' },
  { label: '最新发布', value: 'new' },
]
const videoTypeOptions = [
  { label: '不限', value: '' },
  { label: '低分爆款(待开发)', value: 'low_score_viral', disabled: true },
  { label: '高完播率(待开发)', value: 'high_completion', disabled: true },
  { label: '高涨粉(待开发)', value: 'high_follower_growth', disabled: true },
  { label: '高点赞(待开发)', value: 'high_likes', disabled: true },
]
const publishTimeOptions = [
  { label: '不限', value: 0 },
  { label: '近三天', value: 3 },
  { label: '近七天', value: 7 },
  { label: '近一个月', value: 30 },
]
const limitOptions = [
  { label: '20条', value: 20 },
  { label: '30条', value: 30 },
  { label: '50条', value: 50 },
]

// ── 选中逻辑 ────────────────────────────────
const selectedIds = computed(() => {
  return results.value
    .filter(v => selected.value.has(`${v.platform}-${v.video_id}`))
    .map(v => v.id)
    .filter(Boolean)
})
const allSelected = computed(() =>
  results.value.length > 0 && results.value.every(v => isSelected(v))
)

function isSelected(v) {
  return selected.value.has(`${v.platform}-${v.video_id}`)
}
function toggleSelect(v) {
  const key = `${v.platform}-${v.video_id}`
  if (selected.value.has(key)) selected.value.delete(key)
  else selected.value.add(key)
}
function toggleAll() {
  if (allSelected.value) selected.value.clear()
  else results.value.forEach(v => selected.value.add(`${v.platform}-${v.video_id}`))
}

// ── 搜索 ────────────────────────────────────
async function search() {
  if (!keyword.value.trim()) return message.warning('请输入关键词')
  if (!platforms.value.length) return message.warning('请选择至少一个平台')
  searching.value = true
  selected.value.clear()
  try {
    const { data } = await topicsApi.search({
      keyword: keyword.value.trim(),
      platforms: platforms.value,
      limit: limit.value,
      sort: sort.value,
      video_type: videoType.value || undefined,
      days: publishTime.value || undefined,
      save: true,
    })
    results.value = (data.videos || []).map(v => ({
      ...v,
      _saved: !!v.id,
      _hasAnalysis: !!v.has_analysis,
      _analysis: v.analysis || null,
    }))
    if (data.warnings?.length) {
      data.warnings.forEach(w => message.warning(w, { duration: 5000 }))
    }
    if (!results.value.length) message.info('未找到相关内容，请换个关键词试试')
    else message.success(`找到 ${results.value.length} 条爆款内容`)
    _saveSearchCond()
    loadHistoryKeywords()  // 刷新搜索历史
  } catch (e) {
    message.error(e.response?.data?.detail || '搜索失败')
  } finally {
    searching.value = false
  }
}

// ── 保存选题 ─────────────────────────────────
async function saveToLibrary(v, options = {}) {
  const { silent = false } = options
  try {
    const { data } = await topicsApi.save({
      keyword: keyword.value.trim(),
      platform: v.platform,
      video_id: v.video_id,
      title: v.title,
      description: v.description,
      author: v.author,
      author_id: v.author_id,
      cover_url: v.cover_url,
      like_count: v.like_count,
      comment_count: v.comment_count,
      share_count: v.share_count,
      play_count: v.play_count,
      collect_count: v.collect_count,
      tags: v.tags,
      author_unique_id: v.author_unique_id,
      author_avatar: v.author_avatar,
      author_follower_count: v.author_follower_count,
      author_bio: v.author_bio,
      author_url: v.author_url,
      video_url: v.video_url,
      create_time: v.create_time,
      like_play_ratio: v.like_play_ratio,
      comment_play_ratio: v.comment_play_ratio,
      collect_play_ratio: v.collect_play_ratio,
    })
    v.id = data.id
    v._saved = true
    if (!silent) {
      message.success(data.already_saved ? '该选题已存在选题库中' : '已保存到选题库')
    }
    return true
  } catch {
    if (!silent) {
      message.error('保存失败')
    }
    return false
  }
}

function hasFetchedScript(item) {
  const script = (item?.script || '').trim()
  return !!script && script !== (item?.title || '').trim() && script !== (item?.description || '').trim()
}

async function ensureTopicSaved(item) {
  if (item.id) return item.id
  const ok = await saveToLibrary(item, { silent: true })
  if (!ok) return null
  return item.id
}

async function fetchTopicDetail(item, options = {}) {
  const { silent = false } = options
  const loadingKey = item.id || `${item.platform}-${item.video_id}`
  fetchingDetailIds.value.add(loadingKey)
  try {
    const topicId = await ensureTopicSaved(item)
    if (!topicId) {
      if (!silent) {
        message.error('请先保存选题后再获取文案')
      }
      return false
    }
    const { data } = await topicsApi.fetchDetail(topicId)
    item.script = data.script || ''
    item.top_comments = data.top_comments || []
    if (data.video_url) item.video_url = data.video_url
    if (!silent) {
      message.success(data.cached ? '已读取已保存的视频文案' : '已获取原视频文案')
    }
    return true
  } catch (e) {
    if (!silent) {
      message.error(e.response?.data?.detail || '获取视频文案失败')
    }
    return false
  } finally {
    fetchingDetailIds.value.delete(loadingKey)
    if (item.id) fetchingDetailIds.value.delete(item.id)
  }
}

const selectedVideos = computed(() =>
  results.value.filter(v => isSelected(v) && !v._saved)
)

async function batchSaveToLibrary() {
  const items = selectedVideos.value
  if (!items.length) return message.info('所选视频均已保存')
  let ok = 0
  for (const v of items) {
    try {
      await saveToLibrary(v)
      ok++
    } catch { /* ignore */ }
  }
  message.success(`已保存 ${ok} 条选题`)
  // 刷新已保存列表
  try {
    const { data } = await topicsApi.list({ limit: 200 })
    savedTopics.value = data
  } catch { /* ignore */ }
}

// ── 用于生成文案 ─────────────────────────────
function useAsTopics() {
  const selectedVideos = results.value.filter(v => isSelected(v))
  if (!selectedVideos.length) return
  const first = selectedVideos[0]
  const topicText = selectedVideos.length === 1
    ? first.title
    : selectedVideos.map(v => v.title).join('\n')
  generateStore.setPrefillTopic({
    title: topicText,
    description: first.description || '',
    keyword: first.keyword || keyword.value,
    platform: first.platform || 'douyin',
  })
  router.push('/generate')
}

// ── 已保存选题（抽屉） ──────────────────────
const showSavedDrawer = ref(false)
const loadingSaved = ref(false)
const savedFilter = ref('')
const savedTopics = ref([])
const batchMode = ref(false)
const savedSelectedIds = ref([])
const deletingBatch = ref(false)

function toggleSavedSelect(id) {
  const idx = savedSelectedIds.value.indexOf(id)
  if (idx === -1) savedSelectedIds.value.push(id)
  else savedSelectedIds.value.splice(idx, 1)
}
function toggleSelectAll() {
  if (savedSelectedIds.value.length === filteredSaved.value.length) {
    savedSelectedIds.value = []
  } else {
    savedSelectedIds.value = filteredSaved.value.map(t => t.id)
  }
}
async function handleBatchDelete() {
  deletingBatch.value = true
  try {
    await topicsApi.batchDelete(savedSelectedIds.value)
    window.$message?.success(`已删除 ${savedSelectedIds.value.length} 条选题`)
    savedTopics.value = savedTopics.value.filter(t => !savedSelectedIds.value.includes(t.id))
    // 同步搜索结果中的 _saved 状态
    const deletedSet = new Set(savedSelectedIds.value)
    results.value = results.value.map(v => deletedSet.has(v.id) ? { ...v, _saved: false } : v)
    savedSelectedIds.value = []
    batchMode.value = false
  } catch (e) {
    window.$message?.error('批量删除失败')
  } finally {
    deletingBatch.value = false
  }
}

const filteredSaved = computed(() =>
  savedFilter.value
    ? savedTopics.value.filter(t => t.status === savedFilter.value)
    : savedTopics.value
)

async function openSavedDrawer() {
  showSavedDrawer.value = true
  loadingSaved.value = true
  try {
    const { data } = await topicsApi.list({ limit: 200 })
    savedTopics.value = data.map(t => ({ ...t, _analysis: t.analysis || null }))
  } catch { /* ignore */ } finally {
    loadingSaved.value = false
  }
}

async function updateSavedStatus(t, status) {
  try {
    await topicsApi.updateStatus(t.id, status)
    t.status = status
  } catch { message.error('更新状态失败') }
}

const savedAnalyzingIds = ref(new Set())

async function deleteSavedTopic(t) {
  try {
    await topicsApi.delete(t.id)
    savedTopics.value = savedTopics.value.filter(s => s.id !== t.id)
    message.success('已删除')
  } catch { message.error('删除失败') }
}

async function analyzeSavedVideo(t) {
  savedAnalyzingIds.value.add(t.id)
  try {
    const { data } = await topicsApi.analyzeTopic(t.id)
    t._analysis = data
    currentAnalysis.value = data
    currentAnalysisTitle.value = t.title || '(无标题)'
    showAnalysisModal.value = true
  } catch (e) {
    message.error(e.response?.data?.detail || '分析失败')
  } finally {
    savedAnalyzingIds.value.delete(t.id)
  }
}

function viewSavedAnalysis(t) {
  currentAnalysis.value = t._analysis
  currentAnalysisTitle.value = t.title || '(无标题)'
  showAnalysisModal.value = true
}

function useSavedTopic(t) {
  generateStore.setPrefillTopic({
    title: t.title,
    description: t.description || '',
    keyword: t.keyword || '',
    platform: t.platform || 'douyin',
  })
  showSavedDrawer.value = false
  router.push('/generate')
}

// ── 工具函数 ──────────────────────────────────
function platformZh(p) {
  return { douyin: '抖音', xiaohongshu: '小红书', weixin: '视频号' }[p] || p
}
function formatNum(n) {
  if (!n) return '0'
  if (n >= 10000) return (n / 10000).toFixed(1) + 'w'
  return n.toLocaleString()
}

// ── 图片加载失败时走后端代理 ──────────────────
function handleImgError(e, item) {
  const img = e.target
  const originalUrl = item.cover_url
  // 已经是代理 URL，直接隐藏
  if (!originalUrl || img.dataset.proxied) {
    img.style.display = 'none'
    return
  }
  // 通过后端代理重试
  img.dataset.proxied = '1'
  img.src = `/api/image-proxy?url=${encodeURIComponent(originalUrl)}`
}

// ── 爆款分析函数 ─────────────────────────────
async function analyzeVideo(v) {
  if (!v.id) return message.warning('该视频尚未保存，请先搜索保存后再分析')
  analyzingIds.value.add(v.id)
  // 首次分析会自动获取语音文案，给出提示
  if (!v.script || v.script === v.title) {
    message.info('正在获取视频语音内容，首次分析约需 30-60 秒，请稍候...', { duration: 8000 })
  }
  try {
    const { data } = await topicsApi.analyzeTopic(v.id)
    // 把分析结果附加到结果列表对应项
    const idx = results.value.findIndex(r => r.id === v.id)
    if (idx !== -1) results.value[idx] = { ...results.value[idx], _analysis: data, _hasAnalysis: true }
    currentAnalysis.value = data
    currentAnalysisTitle.value = v.title || '(无标题)'
    showAnalysisModal.value = true
  } catch (e) {
    message.error(e.response?.data?.detail || '分析失败')
  } finally {
    analyzingIds.value.delete(v.id)
  }
}

function viewAnalysis(v) {
  currentAnalysis.value = v._analysis
  currentAnalysisTitle.value = v.title || '(无标题)'
  showAnalysisModal.value = true
}

function ratioLevel(level) {
  if (level === 'high') return { text: '高', type: 'success' }
  if (level === 'medium') return { text: '中', type: 'warning' }
  return { text: '低', type: 'default' }
}

async function batchAnalyzeSelected() {
  if (!selectedIds.value.length) return
  const ids = selectedIds.value
  message.info(`开始批量分析 ${ids.length} 条内容...`)
  try {
    await topicsApi.batchAnalyze({ topic_ids: ids })
    message.success('批量分析完成')
  } catch (e) {
    message.error(e.response?.data?.detail || '批量分析失败')
  }
}

async function batchFetchSelectedDetails() {
  const items = results.value.filter(v => isSelected(v))
  if (!items.length) return
  batchFetchingDetails.value = true
  let ok = 0
  let fail = 0
  for (const item of items) {
    const fetched = await fetchTopicDetail(item, { silent: true })
    if (fetched) ok++
    else fail++
  }
  batchFetchingDetails.value = false
  if (ok) message.success(`已获取 ${ok} 条视频文案`)
  if (fail) message.warning(`${fail} 条获取失败`)
}

// ── 加入资料库 ───────────────────────────────
const showAddToDocsModal = ref(false)
const addToDocsFolder = ref(null)
const addingToDocs = ref(false)
const docsFolderOptions = ref([])

async function openAddToDocsModal() {
  if (!selectedIds.value.length) return
  try {
    const { data } = await documentsApi.listFolders()
    docsFolderOptions.value = data.map(f => ({ label: f, value: f }))
  } catch {}
  showAddToDocsModal.value = true
}

async function confirmAddToDocs() {
  const selectedItems = results.value.filter(v => isSelected(v))
  if (!selectedItems.length) return
  addingToDocs.value = true
  let ok = 0, skip = 0
  for (const v of selectedItems) {
    const content = v.script || v.description || ''
    if (!content.trim()) { skip++; continue }
    try {
      await documentsApi.addText({
        name: `[爆款] ${(v.title || v.author || '').slice(0, 40) || '视频文案'}`,
        content,
        folder_name: addToDocsFolder.value || null,
        source_type: 'topic',
        source_ref: v.video_id,
      })
      ok++
    } catch { skip++ }
  }
  addingToDocs.value = false
  showAddToDocsModal.value = false
  if (ok) message.success(`已添加 ${ok} 条文案到资料库`)
  if (skip) message.warning(`${skip} 条无文案内容，已跳过（可先抓取文案再添加）`)
}

async function loadSavedTopics() {
  try {
    const { data } = await topicsApi.list({ limit: 200 })
    savedTopics.value = data
  } catch { /* ignore */ }
}

// 页面加载时：恢复上次搜索条件，从数据库拉取对应结果
async function loadSearchResults() {
  if (!keyword.value) return  // 没搜索过，保持空状态
  try {
    const { data } = await topicsApi.list({ keyword: keyword.value, limit: 200 })
    if (data.length) {
      results.value = data.map(t => ({ ...t, _saved: true, _hasAnalysis: !!t.has_analysis, _analysis: t.analysis || null }))
    }
  } catch { /* ignore */ }
}

onMounted(() => {
  loadSearchResults()
  loadSavedTopics()
  loadHistoryKeywords()
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: var(--space-xl, 24px); }
.page-title  { font-size: 22px; font-weight: 600; color: var(--c-text-1, #0f172a); }
.page-subtitle { font-size: 13px; color: var(--c-text-4, #94a3b8); margin-top: 4px; }

.search-card {
  background: var(--c-bg-elevated, #fff);
  border: 1px solid var(--c-border, rgba(0,0,0,.06));
  border-radius: var(--radius-lg, 12px);
  padding: 16px var(--space-xl, 24px);
  margin-bottom: 16px;
  box-shadow: var(--shadow-sm, 0 1px 2px rgba(0,0,0,.04));
}

.action-bar {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 16px;
}

.section-title {
  font-size: 15px; font-weight: 600; color: #0f172a;
  margin-bottom: 16px;
}

/* 视频卡片 */
.video-card {
  background: var(--c-bg-elevated, #fff);
  border: 1px solid var(--c-border, rgba(0,0,0,.06));
  border-radius: var(--radius-lg, 12px);
  overflow: hidden;
  cursor: pointer;
  transition: border-color var(--duration-fast, .2s) var(--ease-default, ease), transform .15s, box-shadow var(--duration-fast, .2s);
  position: relative;
  box-shadow: var(--shadow-sm, 0 1px 2px rgba(0,0,0,.04));
}
.video-card:hover { border-color: var(--c-primary-light, rgba(99,102,241,.4)); transform: translateY(-2px); box-shadow: var(--shadow-md, 0 4px 16px rgba(99,102,241,.1)); }
.video-card.selected { border-color: var(--c-primary, #6366f1); background: rgba(99,102,241,.04); }

.select-badge { position: absolute; top: 10px; left: 10px; z-index: 2; }

.video-cover {
  width: 100%; height: 160px;
  background: #f1f5f9;
  position: relative; overflow: hidden;
  display: flex; align-items: center; justify-content: center;
}
.cover-placeholder { display: flex; align-items: center; justify-content: center; width: 100%; height: 100%; }

.platform-tag {
  position: absolute; bottom: 8px; right: 8px;
  background: rgba(0,0,0,.55); color: #fff;
  font-size: 11px; padding: 2px 7px; border-radius: 20px;
}
.analyzed-badge {
  position: absolute; top: 8px; right: 8px;
  background: rgba(34,197,94,.88); color: #fff;
  font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 20px;
  backdrop-filter: blur(4px);
}

.video-body { padding: 12px; }
.video-title {
  font-size: 13px; font-weight: 500; color: var(--c-text-1, #0f172a);
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  overflow: hidden; line-height: 1.4; margin-bottom: 6px;
}
.video-author { font-size: 12px; color: var(--c-text-4, #94a3b8); margin-bottom: 8px; }

.video-stats { display: flex; gap: 12px; margin-bottom: 8px; }
.stat { display: flex; align-items: center; gap: 3px; font-size: 12px; color: var(--c-text-4, #94a3b8); font-variant-numeric: tabular-nums; }
.ratio-tag { background: rgba(99,102,241,.1); color: var(--c-primary, #6366f1); border-radius: 4px; padding: 0 4px; font-size: 11px; }

.video-tags { display: flex; flex-wrap: wrap; gap: 4px; }
.ratio-badges { display: flex; margin-top: 8px; }
.card-actions { display: flex; gap: 6px; margin-top: 8px; flex-wrap: wrap; }

/* ── 爆款分析弹窗 ── */
.analysis-modal { padding-bottom: 4px; }
.ratio-row { display: flex; gap: 16px; justify-content: space-between; }
.ratio-item { flex: 1; text-align: center; background: #f8fafc; border-radius: 10px; padding: 14px 8px; }
.ratio-label { font-size: 12px; color: #94a3b8; margin-bottom: 6px; }
.ratio-value { font-size: 22px; font-weight: 700; color: #0f172a; margin-bottom: 8px; }
.analysis-label { font-size: 12px; color: #94a3b8; margin: 6px 0 10px; }
.analysis-text { font-size: 14px; color: #334155; line-height: 1.8; padding: 8px 0; white-space: pre-wrap; }
.analysis-highlight { background: #fefce8; border-left: 3px solid #eab308; padding: 12px 16px; border-radius: 6px; }

/* ── 已保存选题卡片 ── */
.st-card {
  background: #fff;
  border: 1px solid rgba(0,0,0,.06);
  border-radius: 10px;
  overflow: hidden;
  transition: border-color .2s, box-shadow .15s;
}
.st-card:hover { border-color: rgba(99,102,241,.35); box-shadow: 0 3px 12px rgba(99,102,241,.1); }
.st-card-selected { border-color: rgba(239,68,68,.5); box-shadow: 0 0 0 2px rgba(239,68,68,.15); }
.st-checkbox { position: absolute; top: 8px; left: 8px; z-index: 2; }
.st-card { position: relative; }
.st-cover { width: 100%; height: 130px; background: #f1f5f9; position: relative; overflow: hidden; display: flex; align-items: center; justify-content: center; }
.st-cover-ph { display: flex; align-items: center; justify-content: center; width: 100%; height: 100%; }
.st-platform { position: absolute; bottom: 6px; right: 6px; background: rgba(0,0,0,.55); color: #fff; font-size: 11px; padding: 2px 7px; border-radius: 20px; }
.st-status-tag { position: absolute; top: 6px; left: 6px; }
.st-body { padding: 10px; }
.st-title {
  font-size: 13px; font-weight: 500; color: #0f172a;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  overflow: hidden; line-height: 1.4; margin-bottom: 4px;
}
.st-author { font-size: 12px; color: #94a3b8; margin-bottom: 6px; }
.st-stats { display: flex; gap: 10px; margin-bottom: 6px; flex-wrap: wrap; }
.st-stat { display: flex; align-items: center; gap: 3px; font-size: 12px; color: #94a3b8; }
.st-ratio { background: rgba(99,102,241,.1); color: #6366f1; border-radius: 4px; padding: 0 4px; font-size: 11px; }
.st-actions { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 6px; }

/* 博主发现 */
.discover-section { margin-top: 32px; }
.creator-discover-card {
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 10px;
  padding: 10px 12px;
  display: flex; align-items: center; gap: 10px;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.04);
}
.creator-discover-card.added { opacity: .5; }
.pull-progress { display: flex; align-items: center; padding: 12px 0; border-top: 1px solid #e8eef4; margin-top: 12px; }

/* ── 空状态引导 + 最近搜过 ── */
.empty-state-big {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 48px 0 32px;
}
.empty-guide {
  text-align: center;
  margin-bottom: 32px;
}
.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
}
.empty-title {
  font-size: 17px;
  font-weight: 600;
  color: #334155;
  margin-bottom: 6px;
}
.empty-desc {
  font-size: 13px;
  color: #94a3b8;
}
.recent-searches {
  width: 100%;
  max-width: 560px;
}
.recent-title {
  font-size: 14px;
  font-weight: 500;
  color: #64748b;
  margin-bottom: 12px;
}
.recent-hint {
  font-weight: 400;
  font-size: 12px;
  color: #cbd5e1;
  margin-left: 4px;
}
.recent-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.recent-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 18px;
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 10px;
  cursor: pointer;
  transition: all .2s;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.03);
  min-width: 140px;
}
.recent-item:hover {
  border-color: var(--c-primary, #6366f1);
  background: rgba(99, 102, 241, 0.04);
  box-shadow: 0 2px 10px rgba(99, 102, 241, 0.12);
  transform: translateY(-1px);
}
.recent-keyword {
  font-size: 15px;
  font-weight: 500;
  color: var(--c-text-1, #1e293b);
}
.recent-meta {
  font-size: 12px;
  color: #94a3b8;
  white-space: nowrap;
}
</style>
