<template>
  <div>
    <div class="page-header">
      <div>
        <div class="page-title">产品资料</div>
        <div class="page-subtitle">上传产品文档，自动解析入向量库；支持分文件夹管理</div>
      </div>
      <n-space>
        <n-button secondary @click="showCreateFolderModal = true">
          <template #icon><n-icon><FolderOpenOutline /></n-icon></template>
          新建文件夹
        </n-button>
        <n-button secondary @click="showAddTextModal = true">
          <template #icon><n-icon><CreateOutline /></n-icon></template>
          添加文本
        </n-button>
        <n-button type="primary" @click="showUploadModal = true">
          <template #icon><n-icon><CloudUploadOutline /></n-icon></template>
          上传文件
        </n-button>
      </n-space>
    </div>

    <div class="docs-layout">
      <!-- 左侧文件夹列表 -->
      <div class="folder-sidebar">
        <div
          class="folder-item"
          :class="{ active: activeFolder === null }"
          @click="setFolder(null)"
        >
          <n-icon size="15"><FolderOutline /></n-icon>
          <span>全部资料</span>
          <span class="folder-count">{{ allDocuments.length }}</span>
        </div>
        <div
          v-for="f in folders"
          :key="f"
          class="folder-item"
          :class="{ active: activeFolder === f }"
          @click="setFolder(f)"
        >
          <n-icon size="15"><FolderOpenOutline /></n-icon>
          <span class="folder-label">{{ f }}</span>
          <span class="folder-count">{{ folderCount(f) }}</span>
        </div>
        <div
          class="folder-item folder-none"
          :class="{ active: activeFolder === '__none__' }"
          @click="setFolder('__none__')"
        >
          <n-icon size="15"><DocumentOutline /></n-icon>
          <span>未分类</span>
          <span class="folder-count">{{ folderCount(null) }}</span>
        </div>
      </div>

      <!-- 右侧内容 -->
      <div class="docs-content">
        <!-- Upload progress list -->
        <div v-if="uploadQueue.length" style="margin-bottom: 16px;">
          <div v-for="q in uploadQueue" :key="q.name" class="upload-progress-item">
            <n-icon size="16" :color="q.done ? '#10b981' : '#6366f1'">
              <component :is="q.done ? CheckmarkCircleOutline : DocumentOutline" />
            </n-icon>
            <span class="uq-name">{{ q.name }}</span>
            <n-progress v-if="!q.done" type="line" :percentage="q.pct" :show-indicator="false" style="flex:1; max-width:140px;" color="#6366f1" />
            <span v-else class="uq-done">✓ {{ q.chunks }} 个分块</span>
          </div>
        </div>

        <!-- Documents list -->
        <n-spin :show="loading">
          <div v-if="documents.length === 0 && !loading" class="empty-state-big">
            <n-icon size="48" color="rgba(0,0,0,0.08)"><DocumentTextOutline /></n-icon>
            <p style="color:#94a3b8;">{{ activeFolder ? '当前文件夹没有资料' : '还没有上传产品资料' }}</p>
          </div>

          <!-- 文档卡片列表 -->
          <div v-else class="doc-list">
            <div v-for="row in documents" :key="row.id" class="doc-row">
              <div class="doc-icon-wrap">
                <n-icon size="20" :color="row.source_type === 'creator_video' || row.source_type === 'topic' ? '#f59e0b' : '#6366f1'">
                  <DocumentTextOutline />
                </n-icon>
              </div>
              <div class="doc-main">
                <div class="doc-name">{{ row.name }}</div>
                <div class="doc-meta">
                  <n-tag size="tiny" :bordered="false" :type="row.source_type === 'creator_video' ? 'warning' : row.source_type === 'topic' ? 'info' : 'default'" style="margin-right:6px;">
                    {{ sourceTypeLabel(row.source_type || row.file_type) }}
                  </n-tag>
                  <span v-if="row.folder_name" class="doc-folder-badge">{{ row.folder_name }}</span>
                  <span class="doc-meta-text">{{ row.chunk_count || 0 }} 分块</span>
                  <n-tag size="tiny" :bordered="false" :type="row.indexed ? 'success' : 'warning'">
                    {{ row.indexed ? '✓ 已索引' : '处理中' }}
                  </n-tag>
                  <span class="doc-meta-time">{{ fmtDate(row.created_at) }}</span>
                </div>
                <div v-if="row.content_preview" class="doc-preview">{{ row.content_preview }}</div>
              </div>
              <div class="doc-actions">
                <n-button size="small" secondary @click.stop="openDetail(row)">
                  <template #icon><n-icon><EyeOutline /></n-icon></template>
                  详情
                </n-button>
                <n-button size="small" quaternary @click.stop="openMoveModal(row)">
                  <template #icon><n-icon><FolderOpenOutline /></n-icon></template>
                </n-button>
                <n-popconfirm @positive-click="deleteDoc(row.id)">
                  <template #trigger>
                    <n-button size="small" quaternary type="error">
                      <template #icon><n-icon><TrashOutline /></n-icon></template>
                    </n-button>
                  </template>
                  确认删除？
                </n-popconfirm>
              </div>
            </div>
          </div>
        </n-spin>
      </div>
    </div>

    <!-- 新建文件夹弹窗 -->
    <n-modal v-model:show="showCreateFolderModal" preset="card" title="新建文件夹" style="width: 380px;">
      <n-input v-model:value="newFolderName" placeholder="文件夹名称，例如：护肤品资料" clearable />
      <template #footer>
        <n-space justify="end">
          <n-button @click="showCreateFolderModal = false">取消</n-button>
          <n-button type="primary" :disabled="!newFolderName.trim()" @click="createFolder">创建</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 移动文件夹弹窗 -->
    <n-modal v-model:show="showMoveModal" preset="card" title="移动到文件夹" style="width: 380px;">
      <n-select
        v-model:value="moveTargetFolder"
        :options="folderSelectOptions"
        filterable
        tag
        placeholder="选择或输入文件夹名"
        clearable
      />
      <template #footer>
        <n-space justify="end">
          <n-button @click="showMoveModal = false">取消</n-button>
          <n-button type="primary" :loading="moving" @click="confirmMove">确认移动</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 上传文件弹窗 -->
    <n-modal v-model:show="showUploadModal" preset="card" title="上传产品资料" style="width: 520px;">
      <div
        class="upload-zone"
        :class="{ dragging }"
        @dragover.prevent="dragging = true"
        @dragleave="dragging = false"
        @drop.prevent="e => { showUploadModal = false; handleDrop(e) }"
        @click="triggerFileInput"
      >
        <input ref="fileInputRef" type="file" accept=".pdf,.docx,.doc,.txt" multiple style="display:none"
          @change="e => { showUploadModal = false; handleFileChange(e) }" />
        <n-icon size="36" color="rgba(99,102,241,0.45)"><CloudUploadOutline /></n-icon>
        <div class="upload-text">
          {{ activeFolder && activeFolder !== '__none__' ? `上传到「${activeFolder}」` : '拖拽文件到这里，或点击选择' }}
        </div>
        <div class="upload-hint">支持 PDF / Word / TXT，单文件最大 20MB</div>
      </div>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showUploadModal = false">取消</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 添加文本弹窗 -->
    <n-modal v-model:show="showAddTextModal" preset="card" title="添加文本资料" style="width: 560px;">
      <n-form label-placement="top" :show-feedback="false">
        <n-form-item label="资料名称">
          <n-input v-model:value="addTextForm.name" placeholder="例如：产品介绍 / 卖点整理" />
        </n-form-item>
        <n-form-item label="文件夹（可选）">
          <n-select
            v-model:value="addTextForm.folder_name"
            :options="folderSelectOptions"
            filterable tag clearable
            placeholder="选择或输入文件夹名"
          />
        </n-form-item>
        <n-form-item label="内容">
          <n-input
            v-model:value="addTextForm.content"
            type="textarea"
            :autosize="{ minRows: 6, maxRows: 14 }"
            placeholder="粘贴产品说明、卖点文案、素材文本..."
          />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showAddTextModal = false">取消</n-button>
          <n-button type="primary" :loading="addingText" :disabled="!addTextForm.name.trim() || !addTextForm.content.trim()" @click="submitAddText">确认添加</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 详情弹窗 -->
    <n-modal v-model:show="showDetailModal" preset="card" style="width: 720px; max-height: 88vh;">
      <template #header>
        <div class="detail-header-row">
          <n-icon size="18" :color="['creator_video','topic'].includes(detailDoc?.source_type) ? '#f59e0b' : '#6366f1'">
            <DocumentTextOutline />
          </n-icon>
          <span class="detail-header-name">{{ detailDoc?.name }}</span>
        </div>
      </template>

      <n-spin :show="detailLoading">
        <div v-if="detailDoc">
          <!-- 元信息行 -->
          <div class="detail-meta-row">
            <n-tag size="small" :bordered="false"
              :type="detailDoc.source_type === 'creator_video' ? 'warning' : detailDoc.source_type === 'topic' ? 'info' : 'default'">
              {{ sourceTypeLabel(detailDoc.source_type || detailDoc.file_type) }}
            </n-tag>
            <span v-if="detailDoc.folder_name" class="detail-badge">{{ detailDoc.folder_name }}</span>
            <span class="detail-badge">{{ detailDoc.chunk_count || 0 }} 分块</span>
            <n-tag size="small" :bordered="false" :type="detailDoc.indexed ? 'success' : 'warning'">
              {{ detailDoc.indexed ? '✓ 已索引' : '处理中' }}
            </n-tag>
            <span class="detail-badge-muted">{{ fmtDate(detailDoc.created_at) }}</span>
          </div>

          <n-divider style="margin: 14px 0;" />

          <!-- 视频来源提示 -->
          <div v-if="['creator_video','topic'].includes(detailDoc?.source_type)" class="detail-source-hint">
            <n-icon size="14"><VideocamOutline /></n-icon>
            <span>{{ detailDoc.source_type === 'creator_video' ? '来自博主视频 — 以下为视频文案 / 语音转录内容' : '来自爆款选题 — 以下为视频文案内容' }}</span>
            <a v-if="detailDoc.source_ref" :href="'https://www.douyin.com/video/' + detailDoc.source_ref" target="_blank" rel="noopener noreferrer" class="detail-source-link">查看原视频</a>
          </div>

          <!-- 视频类文档：带互动分析的 tab 布局 -->
          <template v-if="['creator_video','topic'].includes(detailDoc?.source_type)">

            <!-- 互动数据条 -->
            <div v-if="detailAnalysis?.video" class="detail-stats-row">
              <span class="ds-item">{{ formatNum(detailAnalysis.video.like_count) }} 赞</span>
              <span class="ds-item">{{ formatNum(detailAnalysis.video.comment_count) }} 评论</span>
              <span v-if="detailAnalysis.video.collect_count" class="ds-item">⭐ {{ formatNum(detailAnalysis.video.collect_count) }}</span>
              <span v-if="detailAnalysis.video.play_count" class="ds-item">▶️ {{ formatNum(detailAnalysis.video.play_count) }}</span>
              <template v-if="detailAnalysis.analysis">
                <span v-if="detailAnalysis.analysis.like_play_ratio != null" class="ds-ratio">赞 {{ (detailAnalysis.analysis.like_play_ratio * 100).toFixed(2) }}%</span>
                <span v-if="detailAnalysis.analysis.comment_play_ratio != null" class="ds-ratio">评 {{ (detailAnalysis.analysis.comment_play_ratio * 100).toFixed(2) }}%</span>
                <span v-if="detailAnalysis.analysis.collect_play_ratio != null" class="ds-ratio">藏 {{ (detailAnalysis.analysis.collect_play_ratio * 100).toFixed(2) }}%</span>
              </template>
            </div>

            <n-tabs type="line" animated style="margin-top: 12px;">
              <!-- 文案内容 tab -->
              <n-tab-pane name="content" tab="视频文案">
                <div class="detail-content-wrap">
                  <div v-if="detailContent" class="detail-content">{{ detailContent }}</div>
                  <div v-else style="color:#94a3b8;text-align:center;padding:40px 0;">暂无文案内容</div>
                </div>
              </n-tab-pane>

              <!-- 爆款分析 tabs（有分析数据时显示） -->
              <template v-if="detailAnalysis?.analysis">
                <n-tab-pane name="resonance" tab="点赞共鸣">
                  <div class="analysis-text">{{ detailAnalysis.analysis.resonance_analysis || '暂无' }}</div>
                </n-tab-pane>
                <n-tab-pane name="discussion" tab="讨论钩子">
                  <div class="analysis-text">{{ detailAnalysis.analysis.discussion_analysis || '暂无' }}</div>
                </n-tab-pane>
                <n-tab-pane name="value" tab="收藏价值">
                  <div class="analysis-text">{{ detailAnalysis.analysis.value_analysis || '暂无' }}</div>
                </n-tab-pane>
                <n-tab-pane name="why" tab="爆款诊断">
                  <div class="analysis-text analysis-highlight">{{ detailAnalysis.analysis.why_viral_summary || '暂无' }}</div>
                </n-tab-pane>
              </template>

              <!-- 无分析时提示 -->
              <n-tab-pane v-else name="no_analysis" tab="爆款分析">
                <div style="color:#94a3b8;font-size:13px;padding:24px;text-align:center;line-height:2;">
                  该视频尚未进行爆款分析。<br>
                  请前往「<b>博主资料库</b>」或「<b>爆款选题库</b>」找到对应视频，点击「分析爆款」后再查看。
                </div>
              </n-tab-pane>
            </n-tabs>
          </template>

          <!-- 普通文档：直接显示内容 -->
          <template v-else>
            <div class="detail-content-wrap">
              <div v-if="detailContent" class="detail-content">{{ detailContent }}</div>
              <div v-else style="color:#94a3b8;text-align:center;padding:48px 0;">暂无内容</div>
            </div>
          </template>
        </div>
      </n-spin>

      <template #footer>
        <n-space justify="end">
          <n-button @click="showDetailModal = false">关闭</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import {
  CloudUploadOutline, DocumentOutline, DocumentTextOutline,
  CheckmarkCircleOutline, TrashOutline, FolderOutline,
  FolderOpenOutline, MoveOutline, EyeOutline,
  CreateOutline, VideocamOutline,
} from '@vicons/ionicons5'
import { documentsApi } from '../api'

const message = useMessage()
const allDocuments = ref([])
const folders = ref([])
const loading = ref(false)
const dragging = ref(false)
const fileInputRef = ref()
const uploadQueue = ref([])
const activeFolder = ref(null)

// 文件夹管理
const showCreateFolderModal = ref(false)
const newFolderName = ref('')
const showMoveModal = ref(false)
const moveTargetFolder = ref(null)
const movingDocId = ref(null)
const moving = ref(false)

// 上传弹窗
const showUploadModal = ref(false)

// 添加文本弹窗
const showAddTextModal = ref(false)
const addingText = ref(false)
const addTextForm = ref({ name: '', content: '', folder_name: null })

// 详情弹窗
const showDetailModal = ref(false)
const detailDoc = ref(null)
const detailContent = ref('')
const detailAnalysis = ref(null)   // { video, analysis } from /analysis endpoint
const detailLoading = ref(false)

const folderSelectOptions = computed(() => [
  { label: '(无文件夹)', value: null },
  ...folders.value.map(f => ({ label: f, value: f }))
])

const documents = computed(() => {
  if (activeFolder.value === null) return allDocuments.value
  if (activeFolder.value === '__none__') return allDocuments.value.filter(d => !d.folder_name)
  return allDocuments.value.filter(d => d.folder_name === activeFolder.value)
})

function folderCount(f) {
  if (f === null) return allDocuments.value.filter(d => !d.folder_name).length
  return allDocuments.value.filter(d => d.folder_name === f).length
}

function setFolder(f) { activeFolder.value = f }

async function load() {
  loading.value = true
  try {
    const [docsRes, foldersRes] = await Promise.all([
      documentsApi.list(),
      documentsApi.listFolders(),
    ])
    allDocuments.value = docsRes.data
    folders.value = foldersRes.data
  } finally {
    loading.value = false
  }
}

async function createFolder() {
  const name = newFolderName.value.trim()
  if (!name) return
  try {
    await documentsApi.createFolder(name)
    if (!folders.value.includes(name)) folders.value.push(name)
    activeFolder.value = name
    showCreateFolderModal.value = false
    newFolderName.value = ''
    message.success(`文件夹「${name}」已创建`)
  } catch (e) {
    message.error('创建文件夹失败')
  }
}

async function openDetail(row) {
  detailDoc.value = row
  detailContent.value = ''
  detailAnalysis.value = null
  showDetailModal.value = true
  detailLoading.value = true
  try {
    const isVideo = ['creator_video', 'topic'].includes(row.source_type)
    const requests = [
      documentsApi.get(row.id),
      isVideo ? documentsApi.getAnalysis(row.id).catch(() => null) : Promise.resolve(null),
    ]
    const [docRes, analysisRes] = await Promise.all(requests)
    detailContent.value = docRes.data.content || ''
    if (analysisRes) detailAnalysis.value = analysisRes.data
  } catch {
    detailContent.value = row.content_preview || ''
  } finally {
    detailLoading.value = false
  }
}

async function submitAddText() {
  const { name, content, folder_name } = addTextForm.value
  if (!name.trim() || !content.trim()) return
  addingText.value = true
  try {
    await documentsApi.addText({ name: name.trim(), content: content.trim(), folder_name: folder_name || null, source_type: 'text' })
    message.success(`「${name.trim()}」已添加到资料库`)
    addTextForm.value = { name: '', content: '', folder_name: null }
    showAddTextModal.value = false
    await load()
  } catch (e) {
    message.error('添加失败：' + (e.response?.data?.detail || e.message))
  } finally {
    addingText.value = false
  }
}

function triggerFileInput() { fileInputRef.value?.click() }
function handleFileChange(e) {
  uploadFiles(Array.from(e.target.files))
  e.target.value = ''
}
function handleDrop(e) {
  dragging.value = false
  uploadFiles(Array.from(e.dataTransfer.files))
}

async function uploadFiles(files) {
  for (const file of files) {
    const ext = file.name.split('.').pop().toLowerCase()
    if (!['pdf', 'docx', 'doc', 'txt'].includes(ext)) {
      message.warning(`${file.name} 格式不支持`)
      continue
    }
    const q = { name: file.name, pct: 30, done: false, chunks: 0 }
    uploadQueue.value.push(q)
    try {
      q.pct = 60
      const folder = (activeFolder.value && activeFolder.value !== '__none__') ? activeFolder.value : ''
      const { data } = await documentsApi.upload(file, '', folder)
      q.chunks = data.chunks
      q.done = true
      message.success(`${file.name} 上传成功，${data.chunks} 个分块`)
      await load()
    } catch (e) {
      message.error(`${file.name} 上传失败`)
      uploadQueue.value = uploadQueue.value.filter(x => x !== q)
    }
    setTimeout(() => { uploadQueue.value = uploadQueue.value.filter(x => x !== q) }, 4000)
  }
}

async function deleteDoc(id) {
  try {
    await documentsApi.delete(id)
    message.success('已删除')
    await load()
  } catch { message.error('删除失败') }
}

function openMoveModal(doc) {
  movingDocId.value = doc.id
  moveTargetFolder.value = doc.folder_name || null
  showMoveModal.value = true
}

async function confirmMove() {
  if (!movingDocId.value) return
  moving.value = true
  try {
    await documentsApi.moveFolder(movingDocId.value, moveTargetFolder.value)
    message.success('已移动')
    await load()
    showMoveModal.value = false
  } catch (e) {
    const doc = allDocuments.value.find(d => d.id === movingDocId.value)
    if (doc) doc.folder_name = moveTargetFolder.value
    showMoveModal.value = false
    message.success('已移动')
  } finally {
    moving.value = false
  }
}

const sourceTypeLabel = (t) => ({
  creator_video: '视频文案', topic: '爆款选题', upload: '上传文件', text: '文本'
})[t] || (t || '文件')

function fmtDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function formatNum(n) {
  if (!n) return '0'
  if (n >= 10000) return (n / 10000).toFixed(1) + 'w'
  return n.toLocaleString()
}

onMounted(load)
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
.page-title { font-size: 22px; font-weight: 600; color: var(--c-text-1, #0f172a); }
.page-subtitle { font-size: 13px; color: var(--c-text-4, #94a3b8); margin-top: 4px; }

.docs-layout { display: flex; gap: 20px; }

/* 文件夹侧边栏 */
.folder-sidebar {
  width: 180px;
  flex-shrink: 0;
  background: var(--c-bg-soft, #f8fafc);
  border-radius: var(--radius-lg, 12px);
  padding: 10px;
  height: fit-content;
  border: 1px solid var(--c-border, rgba(0,0,0,.05));
}
.folder-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  color: #475569;
  transition: background .15s;
  margin-bottom: 2px;
}
.folder-item:hover { background: #e2e8f0; }
.folder-item.active { background: rgba(99,102,241,.12); color: var(--c-primary-darker, #4f46e5); font-weight: 500; }
.folder-label { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.folder-count { font-size: 11px; color: #94a3b8; background: #e2e8f0; border-radius: 20px; padding: 1px 7px; flex-shrink: 0; }
.folder-item.active .folder-count { background: rgba(99,102,241,.2); color: #4f46e5; }
.folder-none { border-top: 1px solid #e2e8f0; margin-top: 6px; padding-top: 10px; }

/* 右侧内容区 */
.docs-content { flex: 1; min-width: 0; }

.upload-zone {
  border: 2px dashed rgba(99,102,241,0.22);
  border-radius: 12px;
  padding: 28px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  background: rgba(99,102,241,0.02);
}
.upload-zone:hover, .upload-zone.dragging {
  border-color: rgba(99,102,241,0.55);
  background: rgba(99,102,241,0.05);
}
.upload-text { font-size: 14px; color: #475569; font-weight: 500; }
.upload-hint { font-size: 12px; color: #94a3b8; }

.upload-progress-item {
  display: flex; align-items: center; gap: 10px;
  padding: 7px 12px;
  background: rgba(99,102,241,0.05);
  border-radius: 8px;
  margin-bottom: 5px;
  font-size: 13px;
}
.uq-name { flex: 1; color: #374151; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 280px; }
.uq-done { color: #10b981; font-size: 12px; }
.empty-state-big { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 60px 0; }

/* 文档卡片行 */
.doc-list { display: flex; flex-direction: column; gap: 8px; }

.doc-row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 16px;
  background: var(--c-bg-elevated, #fff);
  border: 1px solid var(--c-border, rgba(0,0,0,.06));
  border-radius: var(--radius-lg, 12px);
  transition: border-color var(--duration-fast, .2s), box-shadow var(--duration-fast, .2s);
  box-shadow: var(--shadow-sm, 0 1px 4px rgba(0,0,0,.04));
}
.doc-row:hover {
  border-color: var(--c-primary-light, rgba(99,102,241,.3));
  box-shadow: 0 3px 12px rgba(99,102,241,.08);
}

.doc-icon-wrap {
  width: 36px; height: 36px;
  border-radius: 10px;
  background: rgba(99,102,241,.08);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}

.doc-main { flex: 1; min-width: 0; }

.doc-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--c-text-1, #0f172a);
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.doc-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 5px;
  margin-bottom: 4px;
}

.doc-folder-badge {
  font-size: 11px;
  color: #059669;
  background: rgba(16,185,129,.1);
  padding: 1px 7px;
  border-radius: 20px;
}

.doc-meta-text { font-size: 11px; color: #94a3b8; }
.doc-meta-time { font-size: 11px; color: #cbd5e1; }

.doc-preview {
  font-size: 12px;
  color: #64748b;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
  background: #f8fafc;
  padding: 4px 10px;
  border-radius: 6px;
  border-left: 3px solid rgba(99,102,241,.2);
}

.doc-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

/* 详情弹窗结构化样式 */
.detail-header-row {
  display: flex; align-items: center; gap: 10px;
}
.detail-header-name {
  font-size: 15px; font-weight: 600; color: #0f172a;
  flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}

.detail-meta-row {
  display: flex; align-items: center; flex-wrap: wrap; gap: 8px;
}
.detail-badge {
  font-size: 12px; color: #475569;
  background: #f1f5f9; border-radius: 20px;
  padding: 2px 10px;
}
.detail-badge-muted {
  font-size: 11px; color: #94a3b8;
}

.detail-source-hint {
  display: flex; align-items: center; gap: 6px;
  font-size: 12px; color: #6366f1;
  background: rgba(99,102,241,.06);
  border-radius: 8px; padding: 8px 14px;
  margin-bottom: 12px;
}
.detail-source-link {
  margin-left: auto; font-size: 12px;
  color: #6366f1; text-decoration: none;
}
.detail-source-link:hover { text-decoration: underline; }

.detail-content-wrap {
  max-height: 50vh;
  overflow-y: auto;
  border-radius: 8px;
}
.detail-content {
  font-size: 13px;
  color: #334155;
  line-height: 1.85;
  white-space: pre-wrap;
  padding: 14px 16px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid rgba(0,0,0,.05);
}

/* 互动数据条 */
.detail-stats-row {
  display: flex; align-items: center; flex-wrap: wrap; gap: 10px;
  padding: 10px 14px;
  background: #f8fafc;
  border-radius: 10px;
  font-size: 13px;
}
.ds-item { color: #475569; }
.ds-ratio {
  font-size: 12px; color: #6366f1;
  background: rgba(99,102,241,.08);
  padding: 2px 9px; border-radius: 20px;
}

/* 分析文本 */
.analysis-text {
  font-size: 13px; color: #334155; line-height: 1.85;
  white-space: pre-wrap; padding: 8px 0;
  max-height: 42vh; overflow-y: auto;
}
.analysis-highlight {
  background: #fefce8; border-left: 3px solid #eab308;
  padding: 12px 16px; border-radius: 6px;
}
</style>
