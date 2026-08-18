<template>
  <div>
    <div class="page-header">
      <div>
        <div class="page-title">风格模版</div>
        <div class="page-subtitle">管理博主风格，用于文案生成时的风格模仿</div>
      </div>
      <n-space>
        <n-button secondary @click="showCombinedModal = true">
          <template #icon><n-icon><GitMergeOutline /></n-icon></template>
          联合风格分析
        </n-button>
        <n-button type="primary" @click="showModal = true">
          <template #icon><n-icon><AddOutline /></n-icon></template>
          手动创建模版
        </n-button>
      </n-space>
    </div>

    <n-alert type="info" :bordered="false" style="margin-bottom: 20px; border-radius: 10px;">
      提示：在「博主资料库」页面抓取博主内容后，点击「提取风格」可自动生成风格模版。
    </n-alert>

    <!-- 内容类型筛选 -->
    <n-space style="margin-bottom: 16px;">
      <n-tag
        v-for="ct in contentTypeFilters"
        :key="ct.value"
        :bordered="false"
        :type="activeFilter === ct.value ? 'primary' : 'default'"
        :style="activeFilter === ct.value ? '' : 'cursor:pointer;opacity:0.6'"
        style="cursor:pointer;"
        @click="activeFilter = activeFilter === ct.value ? null : ct.value"
      >
        {{ ct.label }}
      </n-tag>
    </n-space>

    <n-spin :show="loading">
      <div v-if="templates.length === 0 && !loading" class="empty-state-big">
        <n-icon size="48" color="rgba(255,255,255,0.15)"><ColorPaletteOutline /></n-icon>
        <p>还没有风格模版</p>
        <p style="font-size:12px;">去博主页面抓取内容后点击「提取风格」</p>
      </div>

      <n-grid v-else cols="1 s:2 m:3" responsive="screen" :x-gap="16" :y-gap="16">
        <n-gi v-for="t in filteredTemplates" :key="t.id">
            <div class="style-card">
            <div class="style-header">
              <div class="style-name">{{ t.name }}</div>
              <n-space :size="4">
                <n-tag v-if="t.content_type" size="small" :bordered="false" :color="contentTypeColor(t.content_type)">{{ t.content_type }}</n-tag>
                <n-tag size="small" :bordered="false" :type="platformType(t.platform)">{{ t.platform }}</n-tag>
              </n-space>
            </div>
            <!-- 博主来源（突出显示） -->
            <div v-if="t.creator_name" class="style-creator-badge">
              <n-icon size="12" style="vertical-align:middle;margin-right:3px;"><PersonOutline /></n-icon>
              来自博主：<strong>{{ t.creator_name }}</strong>
            </div>
            <div v-if="t.tone_description" class="style-tone">{{ t.tone_description }}</div>

            <div v-if="t.hook_patterns?.length" style="margin-top: 12px;">
              <div class="style-section-label">开头钩子</div>
              <div v-for="(h, i) in t.hook_patterns.slice(0, 2)" :key="i" class="style-hook">
                「{{ h }}」
              </div>
            </div>

            <div v-if="t.cta_patterns?.length" style="margin-top: 10px;">
              <div class="style-section-label">结尾 CTA</div>
              <div class="style-hook cta">{{ t.cta_patterns[0] }}</div>
            </div>

            <div style="margin-top:14px;text-align:right;">
              <n-popconfirm @positive-click="deleteTemplate(t.id)">
                <template #trigger>
                  <n-button size="tiny" quaternary type="error">
                    <template #icon><n-icon><TrashOutline /></n-icon></template>
                    删除
                  </n-button>
                </template>
                确定删除模板「{{ t.name }}」？
              </n-popconfirm>
            </div>
          </div>
        </n-gi>
      </n-grid>
    </n-spin>

    <!-- Manual create modal -->
    <n-modal v-model:show="showModal" preset="card" title="创建风格模版" style="width: 560px;">
      <n-form :model="form" label-placement="top" :show-feedback="false">
        <n-grid :cols="2" :x-gap="16">
          <n-gi>
            <n-form-item label="模版名称">
              <n-input v-model:value="form.name" placeholder="例如：美妆干货博主风格" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="平台">
              <n-select v-model:value="form.platform" :options="platformOpts" />
            </n-form-item>
          </n-gi>
        </n-grid>
        <n-form-item label="内容类型">
          <n-select v-model:value="form.content_type" :options="contentTypeOpts" placeholder="选择内容类型（可选）" clearable />
        </n-form-item>
        <n-form-item label="语气风格描述">
          <n-input v-model:value="form.tone_description" placeholder="例如：口语化，亲切，带有紧迫感" />
        </n-form-item>
        <n-form-item label="内容结构">
          <n-input v-model:value="form.structure_pattern" type="textarea" :autosize="{ minRows: 2 }" placeholder="例如：提出问题 → 分析误区 → 给出解决方案 → 产品推荐" />
        </n-form-item>
        <n-form-item label="开头钩子示例（每行一个）">
          <n-input v-model:value="hooksText" type="textarea" :autosize="{ minRows: 3 }" placeholder="你知道为什么你越洗脸越油吗？&#10;今天必须说一个很多人都不知道的护肤误区" />
        </n-form-item>
        <n-form-item label="结尾 CTA 示例（每行一个）">
          <n-input v-model:value="ctasText" type="textarea" :autosize="{ minRows: 2 }" placeholder="关注我，每天分享干货&#10;点赞收藏，下次找得到" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showModal = false">取消</n-button>
          <n-button type="primary" :loading="creating" @click="create">创建</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- Combined style analysis modal -->
    <n-modal v-model:show="showCombinedModal" preset="card" title="多博主联合风格分析" style="width: 560px;">
      <n-alert type="info" :bordered="false" style="margin-bottom: 16px; border-radius: 8px;">
        选择多个博主，AI 将分析他们的共同风格特征，生成融合风格模板。建议先在「博主资料库」完成内容抓取。
      </n-alert>
      <n-form label-placement="top" :show-feedback="false">
        <n-form-item label="选择博主（可多选）">
          <n-select
            v-model:value="combinedForm.creator_ids"
            multiple
            :options="creatorOptions"
            placeholder="请选择2个或以上博主"
          />
        </n-form-item>
        <n-grid :cols="2" :x-gap="16">
          <n-gi>
            <n-form-item label="融合模板名称">
              <n-input v-model:value="combinedForm.template_name" placeholder="例如：美妆行业融合风格" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="平台">
              <n-select v-model:value="combinedForm.platform" :options="platformOpts" />
            </n-form-item>
          </n-gi>
        </n-grid>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showCombinedModal = false">取消</n-button>
          <n-button
            type="primary"
            :loading="analyzing"
            :disabled="combinedForm.creator_ids.length < 1 || !combinedForm.template_name"
            @click="analyzeCombined"
          >
            <template #icon><n-icon><SparklesOutline /></n-icon></template>
            开始分析
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import { AddOutline, ColorPaletteOutline, GitMergeOutline, SparklesOutline, PersonOutline, TrashOutline } from '@vicons/ionicons5'
import { styleApi, creatorsApi } from '../api'

const message = useMessage()
const templates = ref([])
const loading = ref(false)
const showModal = ref(false)
const showCombinedModal = ref(false)
const creating = ref(false)
const analyzing = ref(false)
const hooksText = ref('')
const ctasText = ref('')
const creators = ref([])

const combinedForm = ref({
  creator_ids: [],
  template_name: '',
  platform: 'douyin',
})

const creatorOptions = computed(() =>
  creators.value.map(c => ({ label: `${c.nickname} (${c.platform}) · ${formatNum(c.follower_count)}粉`, value: c.id }))
)

const form = ref({
  name: '', platform: 'douyin',
  tone_description: '', structure_pattern: '',
  hook_patterns: [], cta_patterns: [], example_scripts: [],
  content_type: null,
})

const contentTypeOpts = [
  { label: '产品种草', value: '产品种草' },
  { label: '知识分享', value: '知识分享' },
  { label: '观点输出', value: '观点输出' },
  { label: '故事叙述', value: '故事叙述' },
  { label: '认知觉醒', value: '认知觉醒' },
]

const contentTypeFilterItems = [
  { label: '全部', value: null },
  { label: '产品种草', value: '产品种草' },
  { label: '知识分享', value: '知识分享' },
  { label: '观点输出', value: '观点输出' },
  { label: '故事叙述', value: '故事叙述' },
  { label: '认知觉醒', value: '认知觉醒' },
]

const activeFilter = ref(null)

const contentTypeFilters = contentTypeFilterItems

const filteredTemplates = computed(() =>
  activeFilter.value ? templates.value.filter(t => t.content_type === activeFilter.value) : templates.value
)

const contentTypeColorMap = {
  '产品种草': { color: '#fff', borderColor: '#f78166', textColor: '#f78166' },
  '知识分享': { color: '#fff', borderColor: '#4ea8de', textColor: '#4ea8de' },
  '观点输出': { color: '#fff', borderColor: '#7c6af7', textColor: '#7c6af7' },
  '故事叙述': { color: '#fff', borderColor: '#e3b341', textColor: '#e3b341' },
  '认知觉醒': { color: '#fff', borderColor: '#56d364', textColor: '#56d364' },
}

function contentTypeColor(ct) {
  return contentTypeColorMap[ct] || { color: '#fff', borderColor: '#94a3b8', textColor: '#94a3b8' }
}

const platformOpts = [
  { label: '抖音', value: 'douyin' },
  { label: '小红书', value: 'xiaohongshu' },
  { label: '视频号', value: 'weixin' },
]

async function load() {
  loading.value = true
  try {
    const [t, c] = await Promise.all([styleApi.list(), creatorsApi.list()])
    templates.value = t.data
    creators.value = c.data
  } finally { loading.value = false }
}

async function create() {
  if (!form.value.name) { message.warning('请填写模版名称'); return }
  creating.value = true
  try {
    const payload = {
      ...form.value,
      hook_patterns: hooksText.value.split('\n').map(s => s.trim()).filter(Boolean),
      cta_patterns: ctasText.value.split('\n').map(s => s.trim()).filter(Boolean),
    }
    await styleApi.create(payload)
    message.success('风格模版已创建')
    showModal.value = false
    await load()
  } catch { message.error('创建失败') }
  finally { creating.value = false }
}

function platformType(p) {
  return { douyin: 'error', xiaohongshu: 'success', weixin: 'warning' }[p] || 'default'
}

function formatNum(n) {
  if (!n) return '0'
  if (n >= 10000) return (n / 10000).toFixed(1) + 'w'
  return n.toString()
}

async function deleteTemplate(id) {
  try {
    await styleApi.delete(id)
    message.success('已删除')
    await load()
  } catch { message.error('删除失败') }
}

async function analyzeCombined() {
  if (!combinedForm.value.template_name) { message.warning('请填写模板名称'); return }
  if (combinedForm.value.creator_ids.length < 1) { message.warning('请至少选择一个博主'); return }
  analyzing.value = true
  try {
    const { data } = await styleApi.analyzeCombined({
      creator_ids: combinedForm.value.creator_ids,
      template_name: combinedForm.value.template_name,
      platform: combinedForm.value.platform,
    })
    message.success(`融合风格模板「${data.name}」已生成（来自 ${data.source_creators?.join('、')}）`)
    showCombinedModal.value = false
    combinedForm.value = { creator_ids: [], template_name: '', platform: 'douyin' }
    await load()
  } catch (e) {
    message.error(e.response?.data?.detail || '分析失败，请确保已抓取博主内容')
  } finally {
    analyzing.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.style-card {
  background: var(--c-bg-elevated, #fff);
  border: 1px solid var(--c-border, rgba(0,0,0,.06));
  border-radius: var(--radius-lg, 12px);
  padding: 18px;
  transition: border-color var(--duration-fast, .2s), box-shadow var(--duration-fast, .2s);
  box-shadow: var(--shadow-sm, 0 1px 2px rgba(0,0,0,.04));
}
.style-card:hover { border-color: var(--c-primary-light, rgba(99,102,241,.3)); box-shadow: var(--shadow-md, 0 4px 16px rgba(99,102,241,.1)); }
.style-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
.style-name { font-size: 15px; font-weight: 600; color: var(--c-text-1, #0f172a); }
.style-creator { font-size: 12px; color: var(--c-text-4, #94a3b8); margin-bottom: 8px; }
.style-creator-badge {
  display: inline-flex; align-items: center;
  font-size: 12px; color: var(--c-primary, #6366f1);
  background: rgba(99,102,241,.08);
  border-radius: 20px; padding: 2px 10px;
  margin-bottom: 8px;
}
.style-tone { font-size: 13px; color: #64748b; line-height: 1.5; }
.style-section-label { font-size: 11px; color: var(--c-text-4, #94a3b8); margin-bottom: 5px; letter-spacing: 0.5px; }
.style-hook { font-size: 12px; color: var(--c-primary, #6366f1); margin-bottom: 4px; line-height: 1.5; }
.style-hook.cta { color: #10b981; }
.empty-state-big { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 80px 0; color: #cbd5e1; }
</style>
