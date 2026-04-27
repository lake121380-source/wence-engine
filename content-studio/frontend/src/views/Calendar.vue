<template>
  <div class="calendar-page">
    <div class="page-header">
      <div>
        <div class="page-title">文案日历</div>
        <div class="page-subtitle">从历史文案拖到日期格即可自动排期，支持月视图与周视图</div>
      </div>
      <n-space>
        <n-button size="small" quaternary @click="shiftRange(-1)">上{{ viewMode === 'week' ? '周' : '月' }}</n-button>
        <n-button size="small" quaternary @click="jumpToday">今天</n-button>
        <n-button size="small" quaternary @click="shiftRange(1)">下{{ viewMode === 'week' ? '周' : '月' }}</n-button>
        <n-radio-group v-model:value="viewMode" size="small" @update:value="loadSchedules">
          <n-radio-button value="month">月视图</n-radio-button>
          <n-radio-button value="week">周视图</n-radio-button>
        </n-radio-group>
        <n-select v-model:value="statusFilter" :options="statusOptions" style="width: 140px" @update:value="loadSchedules" />
        <n-button type="primary" @click="openCreateForSelected">新建排期</n-button>
      </n-space>
    </div>

    <div class="stats-bar card-like">
      <div class="stat-chip">
        <span>总排期</span>
        <strong>{{ scheduleStats.total }}</strong>
      </div>
      <div class="stat-chip">
        <span>草稿</span>
        <strong>{{ scheduleStats.draft }}</strong>
      </div>
      <div class="stat-chip">
        <span>已排期</span>
        <strong>{{ scheduleStats.scheduled }}</strong>
      </div>
      <div class="stat-chip">
        <span>已发布</span>
        <strong>{{ scheduleStats.published }}</strong>
      </div>
      <div class="stat-chip">
        <span>抖音</span>
        <strong>{{ scheduleStats.douyin }}</strong>
      </div>
      <div class="stat-chip">
        <span>小红书</span>
        <strong>{{ scheduleStats.xiaohongshu }}</strong>
      </div>
      <div class="stat-chip">
        <span>视频号</span>
        <strong>{{ scheduleStats.weixin }}</strong>
      </div>
    </div>

    <div class="reminder-bar card-like">
      <div class="reminder-left">
        <span class="reminder-title">提醒</span>
        <n-switch v-model:value="enableBrowserReminder" size="small" />
        <span class="reminder-text">浏览器通知</span>
        <n-select
          v-model:value="reminderLeadMinutes"
          size="small"
          :options="reminderLeadOptions"
          :disabled="!enableBrowserReminder"
          style="width: 118px"
        />
        <span class="reminder-text">提前分钟</span>
      </div>
      <div class="reminder-right">
        <span class="permission-chip" :class="browserPermissionClass">{{ browserPermissionText }}</span>
        <n-button v-if="browserPermission !== 'granted'" size="tiny" quaternary @click="requestBrowserPermission">
          开启通知权限
        </n-button>
        <n-button size="tiny" quaternary :disabled="browserPermission !== 'granted'" @click="testReminder">
          测试提醒
        </n-button>
      </div>
    </div>

    <div v-if="overdueSchedules.length || todayPendingSchedules.length" class="reminder-alerts">
      <n-alert v-if="overdueSchedules.length" type="error" :show-icon="false">
        已逾期 {{ overdueSchedules.length }} 条未发布内容，建议优先处理。
      </n-alert>
      <n-alert v-if="todayPendingSchedules.length" type="warning" :show-icon="false">
        今天还有 {{ todayPendingSchedules.length }} 条待发布内容。
      </n-alert>
    </div>

    <div class="calendar-layout">
      <div class="calendar-wrap card-like">
        <n-spin :show="loading">
          <n-calendar
            v-if="viewMode === 'month'"
            v-model:value="calendarValue"
            @update:value="handleDateSelect"
            @panel-change="handleCalendarPanelChange"
          >
            <template #default="{ year, month, date }">
              <div
                class="cell"
                :class="{ dropping: dropPreviewDayKey === buildDayKey(year, month, date) }"
                @dragover.prevent="onCellDragOver(year, month, date)"
                @dragleave="onCellDragLeave"
                @drop.prevent="onDropToDay(year, month, date)"
              >
                <div class="cell-date">{{ date }}</div>
                <div class="cell-events">
                  <div
                    v-for="item in eventsForDay(year, month, date).slice(0, 2)"
                    :key="item.id"
                    class="cell-event"
                    :class="[`st-${item.status}`, { overdue: isOverdue(item) }]"
                    @click.stop="openEdit(item)"
                  >
                    {{ item.title }}
                  </div>
                  <div v-if="eventsForDay(year, month, date).length > 2" class="cell-more">
                    +{{ eventsForDay(year, month, date).length - 2 }}
                  </div>
                </div>
              </div>
            </template>
          </n-calendar>

          <div v-else class="week-board">
            <div
              v-for="day in weekDays"
              :key="day.key"
              class="week-col"
              :class="{ dropping: dropPreviewDayKey === day.key }"
              @dragover.prevent="onCellDragOverDate(day.date)"
              @dragleave="onCellDragLeave"
              @drop.prevent="onDropToDate(day.date)"
            >
              <div class="week-col-head">
                <div class="week-col-weekday">{{ day.weekday }}</div>
                <div class="week-col-date">{{ day.mmdd }}</div>
              </div>
              <div class="week-col-body">
                <div
                  v-for="item in eventsForDate(day.date)"
                  :key="item.id"
                  class="week-event"
                  :class="[`st-${item.status}`, { overdue: isOverdue(item) }]"
                  @click.stop="openEdit(item)"
                >
                  <div class="week-event-title">{{ item.title }}</div>
                  <div class="week-event-meta">{{ fmtTime(item.scheduled_date) }} · {{ platformLabel(item.platform) }}</div>
                </div>
                <div v-if="!eventsForDate(day.date).length" class="week-empty">拖拽历史文案到此处</div>
              </div>
            </div>
          </div>
        </n-spin>
      </div>

      <div class="day-panel card-like">
        <div class="day-panel-head">
          <div class="day-title">{{ selectedDateText }}</div>
          <n-button size="tiny" secondary @click="openCreateForSelected">新增</n-button>
        </div>

        <div v-if="selectedDayItems.length === 0" class="day-empty">该日期暂无排期</div>

        <div v-else class="day-list">
          <div v-for="item in selectedDayItems" :key="item.id" class="day-item" :class="{ overdue: isOverdue(item) }">
            <div class="day-item-top">
              <div class="day-item-title">{{ item.title }}</div>
              <n-tag size="tiny" :bordered="false" :type="statusType(item.status)">
                {{ statusLabel(item.status) }}
              </n-tag>
            </div>
            <div class="day-item-meta">{{ platformLabel(item.platform) }} · {{ fmtTime(item.scheduled_date) }}</div>
            <div v-if="item.content" class="day-item-content">{{ item.content }}</div>
            <div class="day-item-actions">
              <n-button size="tiny" quaternary @click="openEdit(item)">编辑</n-button>
              <n-popconfirm @positive-click="removeSchedule(item.id)">
                <template #trigger>
                  <n-button size="tiny" quaternary type="error">删除</n-button>
                </template>
                确认删除这条排期？
              </n-popconfirm>
            </div>
          </div>
        </div>
      </div>

      <div class="history-panel card-like">
        <div class="history-panel-head">
          <div class="history-title">历史文案拖拽区</div>
          <n-button size="tiny" quaternary :loading="historyLoading" @click="loadGenerations">刷新</n-button>
        </div>
        <div class="history-hint">拖拽卡片到左侧日期格，自动生成排期（默认 20:00，状态为草稿）</div>

        <n-spin :show="historyLoading">
          <div v-if="!generationPool.length && !historyLoading" class="history-empty">暂无可拖拽历史文案</div>
          <div v-else class="history-list">
            <div
              v-for="g in generationPool"
              :key="g.id"
              class="history-card"
              draggable="true"
              @dragstart="onDragGenerationStart(g)"
              @dragend="onDragGenerationEnd"
            >
              <div class="history-card-title">{{ shortTitle(g.topic) }}</div>
              <div class="history-card-meta">{{ platformLabel(g.platform) }} · {{ fmtDateTime(g.created_at) }}</div>
              <div class="history-card-preview">{{ shortPreview(g.output_full || g.output_body) }}</div>
            </div>
          </div>
        </n-spin>
      </div>
    </div>

    <n-modal v-model:show="showModal" preset="card" :title="editingId ? '编辑排期' : '新建排期'" style="width: 560px">
      <n-form label-placement="top" :show-feedback="false">
        <n-form-item label="标题">
          <n-input v-model:value="form.title" placeholder="例如：周三晚间口播：用户痛点拆解" />
        </n-form-item>
        <n-form-item label="内容摘要">
          <n-input
            v-model:value="form.content"
            type="textarea"
            :autosize="{ minRows: 3, maxRows: 7 }"
            placeholder="记录脚本要点、发布备注、素材链接等"
          />
        </n-form-item>
        <n-grid :cols="2" :x-gap="12">
          <n-gi>
            <n-form-item label="平台">
              <n-select v-model:value="form.platform" :options="platformOptions" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="状态">
              <n-select v-model:value="form.status" :options="statusCreateOptions" />
            </n-form-item>
          </n-gi>
        </n-grid>
        <n-form-item label="发布时间">
          <n-date-picker v-model:value="formDateTs" type="datetime" clearable style="width:100%" />
        </n-form-item>
      </n-form>

      <template #footer>
        <n-space justify="end">
          <n-button @click="showModal = false">取消</n-button>
          <n-button type="primary" :loading="saving" @click="saveSchedule">保存</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useMessage } from 'naive-ui'
import { generateApi, scheduleApi } from '../api'

const message = useMessage()
const loading = ref(false)
const saving = ref(false)
const historyLoading = ref(false)

const schedules = ref([])
const generationPool = ref([])

const calendarValue = ref(new Date())
const selectedDate = ref(new Date())
const statusFilter = ref('')
const viewMode = ref('month')
const nowTick = ref(Date.now())

const dragGeneration = ref(null)
const dropPreviewDayKey = ref('')

const enableBrowserReminder = ref(localStorage.getItem('cs_calendar_reminder_enabled') !== '0')
const storedLead = Number(localStorage.getItem('cs_calendar_reminder_lead') || 30)
const reminderLeadMinutes = ref([10, 30, 60].includes(storedLead) ? storedLead : 30)
const reminderLeadOptions = [
  { label: '提前10分钟', value: 10 },
  { label: '提前30分钟', value: 30 },
  { label: '提前60分钟', value: 60 },
]
let reminderTicker = null
const notifiedReminderKeys = new Set()

const showModal = ref(false)
const editingId = ref(null)
const form = ref({
  title: '',
  content: '',
  platform: 'douyin',
  status: 'draft',
})
const formDateTs = ref(Date.now())

const platformOptions = [
  { label: '抖音', value: 'douyin' },
  { label: '小红书', value: 'xiaohongshu' },
  { label: '视频号', value: 'weixin' },
]
const statusOptions = [
  { label: '全部状态', value: '' },
  { label: '草稿', value: 'draft' },
  { label: '已排期', value: 'scheduled' },
  { label: '已发布', value: 'published' },
]
const statusCreateOptions = statusOptions.filter((x) => x.value)

const browserPermission = computed(() => {
  if (typeof window === 'undefined' || !('Notification' in window)) return 'unsupported'
  return Notification.permission
})

const browserPermissionText = computed(() => {
  if (browserPermission.value === 'granted') return '通知权限：已开启'
  if (browserPermission.value === 'denied') return '通知权限：已拒绝'
  if (browserPermission.value === 'default') return '通知权限：未授权'
  return '通知权限：不支持'
})

const browserPermissionClass = computed(() => {
  if (browserPermission.value === 'granted') return 'ok'
  if (browserPermission.value === 'denied') return 'deny'
  return 'pending'
})

function dayKeyFromDate(d) {
  const date = d instanceof Date ? d : new Date(d)
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function isOverdue(item) {
  if (!item || item.status === 'published') return false
  const ts = new Date(item.scheduled_date).getTime()
  return Number.isFinite(ts) && ts < nowTick.value
}

function isSameDay(a, b) {
  return a.getFullYear() === b.getFullYear()
    && a.getMonth() === b.getMonth()
    && a.getDate() === b.getDate()
}

function buildDayKey(year, month, date) {
  return `${year}-${String(month).padStart(2, '0')}-${String(date).padStart(2, '0')}`
}

function monthRange(base) {
  const date = new Date(base)
  const start = new Date(date.getFullYear(), date.getMonth(), 1, 0, 0, 0)
  const end = new Date(date.getFullYear(), date.getMonth() + 1, 0, 23, 59, 59)
  return { start, end }
}

function weekRange(base) {
  const date = new Date(base)
  const weekDay = (date.getDay() + 6) % 7
  const start = new Date(date)
  start.setDate(date.getDate() - weekDay)
  start.setHours(0, 0, 0, 0)
  const end = new Date(start)
  end.setDate(start.getDate() + 6)
  end.setHours(23, 59, 59, 999)
  return { start, end }
}

function activeRange() {
  return viewMode.value === 'week' ? weekRange(calendarValue.value) : monthRange(calendarValue.value)
}

async function loadSchedules() {
  loading.value = true
  try {
    const { start, end } = activeRange()
    const params = {
      start: start.toISOString(),
      end: end.toISOString(),
      status: statusFilter.value || undefined,
    }
    const { data } = await scheduleApi.list(params)
    schedules.value = data || []
  } catch {
    message.error('排期加载失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

function handleCalendarPanelChange(...args) {
  const candidate = args.find((x) => x instanceof Date || typeof x === 'number')
  if (candidate !== undefined) {
    const date = candidate instanceof Date ? new Date(candidate) : new Date(candidate)
    if (!Number.isNaN(date.getTime())) {
      calendarValue.value = date
    }
  }
  loadSchedules()
}

async function loadGenerations() {
  historyLoading.value = true
  try {
    const { data } = await generateApi.list({ limit: 80 })
    generationPool.value = data || []
  } catch {
    message.error('历史文案加载失败，请稍后重试')
  } finally {
    historyLoading.value = false
  }
}

function handleDateSelect(date) {
  calendarValue.value = date
  selectedDate.value = date
  loadSchedules()
}

function shiftRange(step) {
  const next = new Date(calendarValue.value)
  if (viewMode.value === 'week') {
    next.setDate(next.getDate() + step * 7)
  } else {
    next.setMonth(next.getMonth() + step)
  }
  calendarValue.value = next
  selectedDate.value = new Date(next)
  loadSchedules()
}

function jumpToday() {
  const now = new Date()
  calendarValue.value = now
  selectedDate.value = now
  loadSchedules()
}

const groupedByDay = computed(() => {
  const map = new Map()
  for (const item of schedules.value) {
    const key = dayKeyFromDate(item.scheduled_date)
    if (!map.has(key)) map.set(key, [])
    map.get(key).push(item)
  }
  return map
})

function eventsForDay(year, month, date) {
  return groupedByDay.value.get(buildDayKey(year, month, date)) || []
}

function eventsForDate(date) {
  return groupedByDay.value.get(dayKeyFromDate(date)) || []
}

const weekDays = computed(() => {
  const { start } = weekRange(calendarValue.value)
  const days = []
  for (let i = 0; i < 7; i++) {
    const date = new Date(start)
    date.setDate(start.getDate() + i)
    days.push({
      key: dayKeyFromDate(date),
      date,
      weekday: date.toLocaleDateString('zh-CN', { weekday: 'short' }),
      mmdd: date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' }),
    })
  }
  return days
})

const selectedDateText = computed(() => {
  return selectedDate.value.toLocaleDateString('zh-CN', { month: 'long', day: 'numeric', weekday: 'long' })
})

const selectedDayItems = computed(() => {
  const key = dayKeyFromDate(selectedDate.value)
  return (groupedByDay.value.get(key) || []).slice().sort((a, b) => {
    return new Date(a.scheduled_date) - new Date(b.scheduled_date)
  })
})

const pendingSchedules = computed(() => schedules.value.filter((x) => x.status !== 'published'))

const overdueSchedules = computed(() => pendingSchedules.value.filter((x) => isOverdue(x)))

const todayPendingSchedules = computed(() => {
  const now = new Date(nowTick.value)
  return pendingSchedules.value.filter((x) => {
    const ts = new Date(x.scheduled_date).getTime()
    if (!Number.isFinite(ts)) return false
    const date = new Date(ts)
    return isSameDay(date, now) && ts >= nowTick.value
  })
})

const scheduleStats = computed(() => {
  const list = schedules.value
  return {
    total: list.length,
    draft: list.filter((x) => x.status === 'draft').length,
    scheduled: list.filter((x) => x.status === 'scheduled').length,
    published: list.filter((x) => x.status === 'published').length,
    douyin: list.filter((x) => x.platform === 'douyin').length,
    xiaohongshu: list.filter((x) => x.platform === 'xiaohongshu').length,
    weixin: list.filter((x) => x.platform === 'weixin').length,
  }
})

function platformLabel(p) {
  return { douyin: '抖音', xiaohongshu: '小红书', weixin: '视频号' }[p] || (p || '未知平台')
}

function statusLabel(s) {
  return { draft: '草稿', scheduled: '已排期', published: '已发布' }[s] || s
}

function statusType(s) {
  return { draft: 'default', scheduled: 'warning', published: 'success' }[s] || 'default'
}

function fmtTime(value) {
  if (!value) return ''
  return new Date(value).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function fmtDateTime(value) {
  if (!value) return ''
  return new Date(value).toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function shortTitle(topic) {
  const text = String(topic || '').replace(/\s+/g, ' ').trim()
  if (!text) return '无标题历史文案'
  return text.length > 40 ? `${text.slice(0, 40)}...` : text
}

function shortPreview(content) {
  const text = String(content || '').replace(/\s+/g, ' ').trim()
  if (!text) return '无正文内容'
  return text.length > 66 ? `${text.slice(0, 66)}...` : text
}

async function requestBrowserPermission() {
  if (browserPermission.value === 'unsupported') {
    message.warning('当前浏览器不支持系统通知')
    return
  }

  try {
    const result = await Notification.requestPermission()
    if (result === 'granted') {
      message.success('通知权限已开启')
      runReminderCheck(true)
    } else {
      message.warning('通知权限未开启，浏览器提醒不可用')
    }
  } catch {
    message.error('通知权限请求失败')
  }
}

function testReminder() {
  if (browserPermission.value !== 'granted') {
    message.warning('请先开启通知权限')
    return
  }

  new Notification('Content Studio 提醒测试', {
    body: `提醒功能已开启：将提前 ${reminderLeadMinutes.value} 分钟通知你发布内容。`,
    tag: 'cs-calendar-test',
  })
  message.success('测试通知已发送')
}

function runReminderCheck(forceNow = false) {
  nowTick.value = Date.now()

  if (!enableBrowserReminder.value) return
  if (browserPermission.value !== 'granted') return

  const now = nowTick.value
  const leadMs = reminderLeadMinutes.value * 60 * 1000
  const triggerWindowMs = forceNow ? leadMs : 80 * 1000

  for (const item of pendingSchedules.value) {
    const scheduleAt = new Date(item.scheduled_date).getTime()
    if (!Number.isFinite(scheduleAt)) continue

    const triggerAt = scheduleAt - leadMs
    const key = `${item.id}-${reminderLeadMinutes.value}`
    if (notifiedReminderKeys.has(key)) continue

    if (now >= triggerAt && now <= triggerAt + triggerWindowMs && scheduleAt > now) {
      new Notification('发布提醒', {
        body: `《${shortTitle(item.title)}》将在 ${reminderLeadMinutes.value} 分钟后发布（${platformLabel(item.platform)}）`,
        tag: `cs-calendar-${item.id}`,
      })
      notifiedReminderKeys.add(key)
    }
  }
}

function startReminderTicker() {
  stopReminderTicker()
  runReminderCheck(true)
  reminderTicker = window.setInterval(() => {
    runReminderCheck(false)
  }, 60 * 1000)
}

function stopReminderTicker() {
  if (reminderTicker) {
    clearInterval(reminderTicker)
    reminderTicker = null
  }
}

function openCreateForSelected() {
  editingId.value = null
  form.value = { title: '', content: '', platform: 'douyin', status: 'draft' }
  const base = new Date(selectedDate.value)
  base.setHours(20, 0, 0, 0)
  formDateTs.value = base.getTime()
  showModal.value = true
}

function openEdit(item) {
  editingId.value = item.id
  form.value = {
    title: item.title || '',
    content: item.content || '',
    platform: item.platform || 'douyin',
    status: item.status || 'draft',
  }
  formDateTs.value = new Date(item.scheduled_date).getTime()
  showModal.value = true
}

async function saveSchedule() {
  if (!form.value.title.trim()) {
    message.warning('请先填写标题')
    return
  }
  if (!formDateTs.value) {
    message.warning('请设置发布时间')
    return
  }

  saving.value = true
  try {
    const payload = {
      title: form.value.title.trim(),
      content: form.value.content || '',
      platform: form.value.platform,
      status: form.value.status,
      scheduled_date: new Date(formDateTs.value).toISOString(),
    }

    if (editingId.value) {
      await scheduleApi.update(editingId.value, payload)
      message.success('排期已更新')
    } else {
      await scheduleApi.create(payload)
      message.success('排期已创建')
    }

    showModal.value = false
    await loadSchedules()
  } catch (e) {
    message.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function removeSchedule(id) {
  try {
    await scheduleApi.delete(id)
    message.success('已删除')
    await loadSchedules()
  } catch {
    message.error('删除失败')
  }
}

function onDragGenerationStart(item) {
  dragGeneration.value = item
}

function onDragGenerationEnd() {
  dragGeneration.value = null
  dropPreviewDayKey.value = ''
}

function onCellDragOver(year, month, date) {
  dropPreviewDayKey.value = buildDayKey(year, month, date)
}

function onCellDragOverDate(date) {
  dropPreviewDayKey.value = dayKeyFromDate(date)
}

function onCellDragLeave() {
  dropPreviewDayKey.value = ''
}

async function createScheduleFromDraggedGeneration(date) {
  const item = dragGeneration.value
  dropPreviewDayKey.value = ''
  if (!item) return

  const scheduled = new Date(date)
  scheduled.setHours(20, 0, 0, 0)

  try {
    await scheduleApi.create({
      title: shortTitle(item.topic),
      content: item.output_full || item.output_body || '',
      platform: item.platform || 'douyin',
      scheduled_date: scheduled.toISOString(),
      status: 'draft',
      generation_id: item.id,
    })
    selectedDate.value = new Date(scheduled)
    calendarValue.value = new Date(scheduled)
    message.success('拖拽成功，已创建排期')
    await loadSchedules()
  } catch (e) {
    message.error(e.response?.data?.detail || '拖拽创建失败')
  } finally {
    dragGeneration.value = null
  }
}

async function onDropToDay(year, month, date) {
  await createScheduleFromDraggedGeneration(new Date(year, month - 1, date))
}

async function onDropToDate(date) {
  await createScheduleFromDraggedGeneration(new Date(date))
}

onMounted(async () => {
  startReminderTicker()
  await Promise.all([loadSchedules(), loadGenerations()])
})

onBeforeUnmount(() => {
  stopReminderTicker()
})

watch(enableBrowserReminder, (value) => {
  localStorage.setItem('cs_calendar_reminder_enabled', value ? '1' : '0')
  if (value) runReminderCheck(true)
})

watch(reminderLeadMinutes, (value) => {
  localStorage.setItem('cs_calendar_reminder_lead', String(value))
  notifiedReminderKeys.clear()
  runReminderCheck(true)
})

watch(schedules, () => {
  runReminderCheck(false)
}, { deep: true })
</script>

<style scoped>
.card-like {
  background: #fff;
  border: 1px solid #e0f2fe;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(8,145,178,0.06);
}

.stats-bar {
  margin-bottom: 12px;
  padding: 10px;
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 8px;
}

.stat-chip {
  border: 1px solid #e0f2fe;
  border-radius: 10px;
  background: #f8fcff;
  padding: 8px 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  font-size: 12px;
  color: #64748b;
}

.stat-chip strong {
  font-size: 16px;
  line-height: 1;
  color: #0f172a;
}

.reminder-bar {
  margin-bottom: 10px;
  padding: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}

.reminder-left,
.reminder-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.reminder-title {
  font-size: 12px;
  color: #334155;
  font-weight: 700;
  margin-right: 2px;
}

.reminder-text {
  font-size: 12px;
  color: #64748b;
}

.permission-chip {
  font-size: 11px;
  line-height: 1;
  border-radius: 999px;
  padding: 5px 8px;
  border: 1px solid #e2e8f0;
  color: #64748b;
  background: #f8fafc;
}

.permission-chip.ok {
  border-color: #86efac;
  color: #166534;
  background: #dcfce7;
}

.permission-chip.deny {
  border-color: #fca5a5;
  color: #991b1b;
  background: #fee2e2;
}

.permission-chip.pending {
  border-color: #fde68a;
  color: #92400e;
  background: #fef3c7;
}

.reminder-alerts {
  margin-bottom: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.calendar-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 300px 320px;
  gap: 14px;
}

.calendar-wrap {
  padding: 10px;
}

.cell {
  min-height: 84px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  border-radius: 8px;
  padding: 2px 4px;
  transition: background-color 0.15s ease, box-shadow 0.15s ease;
}

.cell.dropping {
  background: #ecfeff;
  box-shadow: inset 0 0 0 2px #67e8f9;
}

.cell-date {
  font-size: 12px;
  color: #64748b;
}

.cell-events {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.cell-event {
  font-size: 11px;
  border-radius: 6px;
  padding: 2px 6px;
  line-height: 1.35;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: pointer;
}

.cell-event.st-draft {
  background: #f1f5f9;
  color: #475569;
}

.cell-event.st-scheduled {
  background: #fef3c7;
  color: #92400e;
}

.cell-event.st-published {
  background: #dcfce7;
  color: #166534;
}

.cell-event.overdue {
  background: #fee2e2 !important;
  color: #b91c1c !important;
}

.cell-more {
  font-size: 11px;
  color: #94a3b8;
}

.week-board {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 8px;
  min-height: 430px;
}

.week-col {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #fff;
  overflow: hidden;
  min-height: 390px;
  display: flex;
  flex-direction: column;
}

.week-col.dropping {
  border-color: #22d3ee;
  box-shadow: inset 0 0 0 2px #67e8f9;
  background: #ecfeff;
}

.week-col-head {
  padding: 8px 10px;
  border-bottom: 1px solid #e2e8f0;
}

.week-col-weekday {
  font-size: 12px;
  color: #64748b;
}

.week-col-date {
  margin-top: 2px;
  font-size: 13px;
  font-weight: 600;
  color: #0f172a;
}

.week-col-body {
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-height: 0;
  overflow-y: auto;
}

.week-event {
  border-radius: 8px;
  padding: 7px 8px;
  cursor: pointer;
}

.week-event-title {
  font-size: 12px;
  font-weight: 600;
  line-height: 1.4;
  color: #0f172a;
}

.week-event-meta {
  margin-top: 2px;
  font-size: 11px;
  color: #64748b;
}

.week-event.st-draft {
  background: #f1f5f9;
}

.week-event.st-scheduled {
  background: #fef3c7;
}

.week-event.st-published {
  background: #dcfce7;
}

.week-event.overdue {
  background: #fee2e2 !important;
  border: 1px solid #fca5a5;
}

.week-event.overdue .week-event-title,
.week-event.overdue .week-event-meta {
  color: #b91c1c;
}

.week-empty {
  margin-top: 8px;
  border: 1px dashed #cbd5e1;
  border-radius: 8px;
  background: #f8fafc;
  color: #94a3b8;
  font-size: 11px;
  text-align: center;
  padding: 12px 6px;
}

.day-panel {
  padding: 12px;
}

.day-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.day-title {
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
}

.day-empty {
  color: #94a3b8;
  font-size: 13px;
  padding: 18px 4px;
}

.day-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.day-item {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #fff;
  padding: 10px;
}

.day-item.overdue {
  border-color: #fca5a5;
  background: #fff7f7;
}

.day-item.overdue .day-item-title,
.day-item.overdue .day-item-meta {
  color: #b91c1c;
}

.day-item-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.day-item-title {
  font-size: 13px;
  font-weight: 600;
  color: #0f172a;
}

.day-item-meta {
  margin-top: 4px;
  font-size: 12px;
  color: #64748b;
}

.day-item-content {
  margin-top: 6px;
  font-size: 12px;
  line-height: 1.6;
  color: #334155;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 6px 8px;
  white-space: pre-wrap;
}

.day-item-actions {
  margin-top: 8px;
  display: flex;
  gap: 6px;
}

.history-panel {
  padding: 12px;
  display: flex;
  flex-direction: column;
  min-height: 520px;
}

.history-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.history-title {
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
}

.history-hint {
  margin-top: 6px;
  margin-bottom: 8px;
  font-size: 12px;
  color: #64748b;
  line-height: 1.5;
}

.history-empty {
  font-size: 13px;
  color: #94a3b8;
  padding: 14px 2px;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow-y: auto;
  padding-right: 2px;
}

.history-card {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #fff;
  padding: 9px 10px;
  cursor: grab;
}

.history-card:active {
  cursor: grabbing;
}

.history-card-title {
  font-size: 12px;
  font-weight: 600;
  color: #0f172a;
  line-height: 1.45;
}

.history-card-meta {
  margin-top: 4px;
  font-size: 11px;
  color: #64748b;
}

.history-card-preview {
  margin-top: 5px;
  font-size: 11px;
  color: #475569;
  line-height: 1.45;
}

@media (max-width: 1400px) {
  .stats-bar {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
  .calendar-layout {
    grid-template-columns: minmax(0, 1fr) 300px;
  }
  .history-panel {
    grid-column: 1 / -1;
    min-height: 280px;
  }
}

@media (max-width: 980px) {
  .stats-bar {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .reminder-bar {
    align-items: flex-start;
  }
  .calendar-layout {
    grid-template-columns: 1fr;
  }
  .week-board {
    min-width: 780px;
  }
  .calendar-wrap {
    overflow-x: auto;
  }
}
</style>
