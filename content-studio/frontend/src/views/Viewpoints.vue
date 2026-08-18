<template>
  <div>
    <div class="page-description">
      <p class="page-subtitle">沉淀你的独立立场与行业观点，在生成文案时自动融入个人视角</p>
    </div>

    <!-- 工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <n-select
          v-model:value="filterCategory"
          :options="categoryOptions"
          clearable
          placeholder="按分类筛选"
          style="width: 160px"
          @update:value="loadViewpoints"
        />
        <n-switch v-model:value="activeOnly" @update:value="loadViewpoints">
          <template #checked>仅显示启用</template>
          <template #unchecked>全部</template>
        </n-switch>
      </div>
      <n-button type="primary" @click="openCreate">
        <template #icon><n-icon><AddOutline /></n-icon></template>
        添加观点
      </n-button>
    </div>

    <!-- 观点列表 -->
    <div v-if="loading" class="center-loader">
      <n-spin size="large" />
    </div>

    <div v-else-if="viewpoints.length === 0" class="empty-state">
      <n-empty description="还没有观点，添加你的第一个独立立场吧！">
        <template #extra>
          <n-button type="primary" @click="openCreate">添加观点</n-button>
        </template>
      </n-empty>
    </div>

    <div v-else class="viewpoints-grid">
      <div
        v-for="vp in viewpoints"
        :key="vp.id"
        class="viewpoint-card"
        :class="{ inactive: !vp.is_active }"
      >
        <div class="card-header">
          <div class="card-meta">
            <n-tag :type="categoryTagType(vp.category)" size="small">{{ vp.category }}</n-tag>
            <span v-if="!vp.is_active" class="disabled-badge">已禁用</span>
          </div>
          <n-dropdown
            :options="cardActions(vp)"
            @select="(key) => handleAction(key, vp)"
          >
            <n-button size="tiny" quaternary circle>
              <template #icon><n-icon><EllipsisHorizontalOutline /></n-icon></template>
            </n-button>
          </n-dropdown>
        </div>

        <h3 class="card-title">{{ vp.title }}</h3>
        <p class="card-content">{{ vp.content }}</p>

        <div v-if="vp.tags" class="card-tags">
          <n-tag
            v-for="tag in parseTags(vp.tags)"
            :key="tag"
            size="tiny"
            :bordered="false"
            style="background: #f1f5f9; color: #64748b; margin-right: 4px;"
          >{{ tag }}</n-tag>
        </div>
      </div>
    </div>

    <!-- 创建/编辑弹窗 -->
    <n-modal v-model:show="showModal" preset="card" :title="editingId ? '编辑观点' : '添加观点'" style="width: 560px">
      <n-form :model="form" label-placement="top" :show-feedback="false" size="large">
        <n-form-item label="观点标题" required>
          <n-input v-model:value="form.title" placeholder="一句话概括你的观点" />
        </n-form-item>
        <n-form-item label="分类">
          <n-select v-model:value="form.category" :options="categoryOptions.filter(o => o.value)" />
        </n-form-item>
        <n-form-item label="观点详情" required>
          <n-input
            v-model:value="form.content"
            type="textarea"
            :autosize="{ minRows: 4, maxRows: 8 }"
            placeholder="详细描述你的立场、观点或差异化角度..."
          />
        </n-form-item>
        <n-form-item label="标签（逗号分隔）">
          <n-input v-model:value="form.tags" placeholder="护肤,成分党,油皮..." />
        </n-form-item>
      </n-form>
      <template #footer>
        <div style="display: flex; justify-content: flex-end; gap: 12px;">
          <n-button @click="showModal = false">取消</n-button>
          <n-button type="primary" :loading="saving" @click="save">
            {{ editingId ? '保存修改' : '创建观点' }}
          </n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import { AddOutline, EllipsisHorizontalOutline } from '@vicons/ionicons5'
import { viewpointsApi } from '../api/index.js'

const message = useMessage()

const viewpoints = ref([])
const loading = ref(false)
const filterCategory = ref(null)
const activeOnly = ref(false)

const showModal = ref(false)
const saving = ref(false)
const editingId = ref(null)
const form = ref({ title: '', category: '行业立场', content: '', tags: '' })

const categoryOptions = [
  { label: '全部分类', value: null },
  { label: '行业立场', value: '行业立场' },
  { label: '价值观', value: '价值观' },
  { label: '差异化角度', value: '差异化角度' },
  { label: '用户洞察', value: '用户洞察' },
  { label: '产品主张', value: '产品主张' },
]

const categoryTagType = (cat) => {
  const map = {
    '行业立场': 'info',
    '价值观': 'success',
    '差异化角度': 'warning',
    '用户洞察': 'primary',
    '产品主张': 'error',
  }
  return map[cat] || 'default'
}

const parseTags = (tags) => tags ? tags.split(',').map(t => t.trim()).filter(Boolean) : []

const cardActions = (vp) => [
  { label: '编辑', key: 'edit' },
  { label: vp.is_active ? '禁用' : '启用', key: 'toggle' },
  { label: '删除', key: 'delete', props: { style: 'color: #ef4444' } },
]

async function loadViewpoints() {
  loading.value = true
  try {
    const res = await viewpointsApi.list({
      category: filterCategory.value,
      active_only: activeOnly.value,
    })
    viewpoints.value = res.data
  } catch {
    message.error('加载观点失败')
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  form.value = { title: '', category: '行业立场', content: '', tags: '' }
  showModal.value = true
}

function openEdit(vp) {
  editingId.value = vp.id
  form.value = { title: vp.title, category: vp.category, content: vp.content, tags: vp.tags || '' }
  showModal.value = true
}

async function save() {
  if (!form.value.title.trim() || !form.value.content.trim()) {
    message.warning('标题和内容不能为空')
    return
  }
  saving.value = true
  try {
    if (editingId.value) {
      await viewpointsApi.update(editingId.value, form.value)
      message.success('观点已更新')
    } else {
      await viewpointsApi.create(form.value)
      message.success('观点已创建并入向量库')
    }
    showModal.value = false
    loadViewpoints()
  } catch (e) {
    message.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function handleAction(key, vp) {
  if (key === 'edit') {
    openEdit(vp)
  } else if (key === 'toggle') {
    try {
      await viewpointsApi.update(vp.id, { is_active: !vp.is_active })
      message.success(vp.is_active ? '已禁用' : '已启用')
      loadViewpoints()
    } catch {
      message.error('操作失败')
    }
  } else if (key === 'delete') {
    try {
      await viewpointsApi.delete(vp.id)
      message.success('已删除')
      loadViewpoints()
    } catch {
      message.error('删除失败')
    }
  }
}

onMounted(loadViewpoints)
</script>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  gap: 12px;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.viewpoints-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.viewpoint-card {
  background: var(--c-bg-elevated, rgba(255,255,255,.92));
  backdrop-filter: blur(10px);
  border-radius: var(--radius-lg, 12px);
  padding: 18px;
  border: 1px solid var(--c-border, rgba(0,0,0,.06));
  transition: box-shadow var(--duration-fast, .2s), transform var(--duration-fast, .2s);
}

.viewpoint-card:hover {
  box-shadow: 0 4px 20px rgba(99, 102, 241, 0.12);
  transform: translateY(-2px);
}

.viewpoint-card.inactive {
  opacity: 0.5;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.disabled-badge {
  font-size: 11px;
  color: var(--c-text-4, #94a3b8);
  background: #f1f5f9;
  padding: 2px 6px;
  border-radius: 4px;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--c-text-1, #0f172a);
  margin: 0 0 8px;
  line-height: 1.4;
}

.card-content {
  font-size: 13px;
  color: #475569;
  line-height: 1.6;
  margin: 0 0 12px;
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-tags {
  margin-top: 8px;
}

.center-loader {
  display: flex;
  justify-content: center;
  padding: 60px;
}
</style>
