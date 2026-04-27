<template>
  <div class="pricing-page">
    <!-- 当前订阅状态 -->
    <div v-if="authStore.isAuthenticated" class="current-status card">
      <div class="status-info">
        <span class="status-label">当前状态</span>
        <n-tag :type="authStore.planType" :bordered="false" size="medium">
          {{ authStore.planLabel }}
        </n-tag>
        <span v-if="authStore.isSubscriptionActive" class="status-expire">
          {{ authStore.isTrial ? '体验' : '订阅' }}到期时间：{{ expireText }}
          （剩余 {{ authStore.daysUntilExpiry }} 天）
        </span>
        <span v-else class="status-expire expired">订阅已到期，续费后继续使用</span>
      </div>
    </div>

    <!-- 套餐卡片 -->
    <div class="plans-grid">
      <!-- 免费体验 -->
      <div class="plan-card free-card" :class="{ active: authStore.isTrial && authStore.isSubscriptionActive }">
        <div class="plan-badge" v-if="authStore.isTrial && authStore.isSubscriptionActive">当前</div>
        <div class="plan-name">免费体验</div>
        <div class="plan-price">
          <span class="price-amount">¥0</span>
          <span class="price-period">/ 1天</span>
        </div>
        <div class="plan-desc">新用户自动开通，体验全部功能</div>
        <div class="plan-features">
          <div class="feature-item" v-for="f in freeFeatures" :key="f">
            <n-icon color="#10b981"><CheckmarkOutline /></n-icon>
            <span>{{ f }}</span>
          </div>
        </div>
        <n-button size="large" block :disabled="true" style="margin-top:24px">
          {{ authStore.isTrial ? '体验中' : '新用户专享' }}
        </n-button>
      </div>

      <!-- 标准版 ¥49/月（推荐） -->
      <div class="plan-card pro-card" :class="{ active: !authStore.isTrial && authStore.isSubscriptionActive }">
        <div class="plan-badge recommended">推荐</div>
        <div class="plan-name">标准版</div>
        <div class="plan-price">
          <span class="price-amount">¥49</span>
          <span class="price-period">/ 月</span>
        </div>
        <div class="plan-desc">无限制使用全部功能，专业内容创作者首选</div>
        <div class="plan-features">
          <div class="feature-item" v-for="f in proFeatures" :key="f">
            <n-icon color="#6366f1"><CheckmarkOutline /></n-icon>
            <span>{{ f }}</span>
          </div>
        </div>
        <div style="margin-top:24px;">
          <n-button
            type="primary"
            size="large"
            block
            @click="showPayModal = true"
            :loading="creating"
          >
            {{ !authStore.isSubscriptionActive ? '立即续费' : '续费 ¥49/月' }}
          </n-button>
        </div>
      </div>
    </div>

    <!-- 支付弹窗 -->
    <n-modal
      v-model:show="showPayModal"
      preset="card"
      title="选择支付方式"
      style="width:440px;border-radius:20px;"
      :mask-closable="!creating"
    >
      <div class="pay-modal">
        <div class="pay-amount-banner">
          <span class="pay-title">标准版 · 1个月</span>
          <span class="pay-amount-text">¥49.00</span>
        </div>

        <!-- Step1: 选择方式 -->
        <template v-if="payStep === 1">
          <div class="pay-methods">
            <div
              class="pay-method-btn"
              :class="{ selected: payMethod === 'wechat' }"
              @click="payMethod = 'wechat'"
            >
              <img src="https://img.icons8.com/color/48/wechat.png" alt="微信" width="28" />
              <span>微信支付</span>
            </div>
            <div
              class="pay-method-btn"
              :class="{ selected: payMethod === 'alipay' }"
              @click="payMethod = 'alipay'"
            >
              <img src="https://img.icons8.com/color/48/alipay.png" alt="支付宝" width="28" />
              <span>支付宝</span>
            </div>
          </div>
          <div style="display:flex;gap:12px;margin-top:20px;">
            <n-button secondary block @click="showPayModal = false">取消</n-button>
            <n-button type="primary" block :loading="creating" @click="createOrder">
              确认支付
            </n-button>
          </div>
        </template>

        <!-- Step2: 扫码支付（微信/支付宝统一） -->
        <template v-else-if="payStep === 2">
          <div class="qr-area">
            <img :src="qrCodeUrl" width="200" height="200" alt="扫码支付" style="border-radius:8px;" />
            <p class="qr-hint">请使用{{ payMethod === 'wechat' ? '微信' : '支付宝' }}扫码完成支付</p>
            <p class="qr-hint" style="color:#94a3b8;font-size:12px;">有效期15分钟，支付完成后自动跳转</p>
          </div>
          <!-- 开发模式：模拟支付按钮 -->
          <div v-if="isDev" class="dev-pay-area">
            <n-divider style="margin:12px 0"><span style="font-size:12px;color:#f59e0b">开发模式</span></n-divider>
            <n-button
              type="warning"
              block
              size="small"
              :loading="devPaying"
              @click="handleDevPay"
            >模拟支付完成（跳过真实扫码）</n-button>
          </div>
          <div style="display:flex;gap:12px;margin-top:16px;">
            <n-button secondary block @click="resetPay(); payStep = 1">返回</n-button>
            <n-button secondary block @click="showPayModal = false; resetPay()">关闭</n-button>
          </div>
        </template>
      </div>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useMessage } from 'naive-ui'
import { CheckmarkOutline } from '@vicons/ionicons5'
import { useAuthStore } from '../stores/auth.js'
import { paymentApi } from '../api'

const message = useMessage()
const authStore = useAuthStore()

const showPayModal = ref(false)
const payMethod = ref('wechat')
const payStep = ref(1)   // 1=选方式, 2=扫码/跳转
const creating = ref(false)
const devPaying = ref(false)
const qrCodeUrl = ref('')
const orderId = ref(null)
const isDev = import.meta.env.DEV
let pollTimer = null

const expireText = computed(() => {
  if (!authStore.user?.subscription_expire_at) return ''
  return new Date(authStore.user.subscription_expire_at).toLocaleDateString('zh-CN')
})

const freeFeatures = [
  '不限次文案生成（1天内）',
  '爆款选题库浏览',
  '博主风格分析',
  '多平台适配',
]

const proFeatures = [
  '无限次文案生成',
  '无限博主资料入库',
  '无限产品资料上传',
  '知识库 RAG 增强生成',
  '爆款视频分析注入',
  '历史记录永久保存',
  '优先响应速度',
]

async function createOrder() {
  if (!payMethod.value) return
  creating.value = true
  try {
    const { data } = await paymentApi.createOrder({ method: payMethod.value, plan: 'monthly' })
    orderId.value = data.order_id
    if (data.qr_code_url) {
      qrCodeUrl.value = data.qr_code_url
      payStep.value = 2
      startPolling()
    } else {
      message.error('未获取到支付二维码，请稍后再试')
    }
  } catch (e) {
    message.error(e.response?.data?.detail || '创建订单失败，请稍后再试')
  } finally {
    creating.value = false
  }
}

async function handleDevPay() {
  if (!orderId.value) return
  devPaying.value = true
  try {
    await paymentApi.devPay(orderId.value)
    clearInterval(pollTimer)
    const { data: me } = await paymentApi.refreshMe()
    authStore.setUser(me)
    message.success('模拟支付成功！订阅已激活')
    showPayModal.value = false
    resetPay()
  } catch (e) {
    message.error(e.response?.data?.detail || '模拟支付失败')
  } finally {
    devPaying.value = false
  }
}

function startPolling() {
  pollTimer = setInterval(async () => {
    if (!orderId.value) return
    try {
      const { data } = await paymentApi.checkOrder(orderId.value)
      if (data.status === 'paid') {
        clearInterval(pollTimer)
        // 刷新用户信息
        const { data: me } = await paymentApi.refreshMe()
        authStore.setUser(me)
        message.success('支付成功！订阅已激活')
        showPayModal.value = false
        resetPay()
      }
    } catch {}
  }, 3000)
}

function resetPay() {
  qrCodeUrl.value = ''
  orderId.value = null
  payMethod.value = 'wechat'
  payStep.value = 1
  if (pollTimer) clearInterval(pollTimer)
}

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<style scoped>
.pricing-page {
  max-width: 860px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.current-status {
  display: flex;
  align-items: center;
  padding: 18px 24px;
}

.status-info {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}

.status-label {
  font-size: 14px;
  color: #64748b;
}

.status-expire {
  font-size: 13px;
  color: #64748b;
}
.status-expire.expired { color: #ef4444; }

.plans-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.plan-card {
  position: relative;
  background: var(--c-bg-elevated, #fff);
  border-radius: 20px;
  padding: 32px 28px;
  border: 2px solid #e2e8f0;
  transition: all .25s;
}

.plan-card.pro-card {
  border-color: var(--c-primary, #6366f1);
  box-shadow: 0 8px 40px rgba(99,102,241,.14);
}

.plan-badge {
  position: absolute;
  top: 16px;
  right: 16px;
  background: #e2e8f0;
  color: #64748b;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 20px;
}

.plan-badge.recommended {
  background: linear-gradient(135deg, var(--c-primary, #6366f1), #a78bfa);
  color: #fff;
}

.plan-name {
  font-size: 22px;
  font-weight: 700;
  color: var(--c-text-1, #0f172a);
  margin-bottom: 12px;
}

.plan-price {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 10px;
}

.price-amount {
  font-size: 42px;
  font-weight: 800;
  color: var(--c-primary, #6366f1);
  line-height: 1;
  font-variant-numeric: tabular-nums;
}

.free-card .price-amount { color: #10b981; }

.price-period {
  font-size: 15px;
  color: var(--c-text-4, #94a3b8);
}

.plan-desc {
  font-size: 13.5px;
  color: #64748b;
  margin-bottom: 24px;
  line-height: 1.5;
}

.plan-features {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13.5px;
  color: #475569;
}

/* 支付弹窗 */
.pay-modal {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.pay-amount-banner {
  background: linear-gradient(135deg, #f0f4ff, #ede9fe);
  border-radius: 12px;
  padding: 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pay-title { font-size: 14px; color: #475569; font-weight: 500; }
.pay-amount-text { font-size: 26px; font-weight: 800; color: var(--c-primary, #6366f1); font-variant-numeric: tabular-nums; }

.pay-methods {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.pay-method-btn {
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  padding: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  color: #475569;
  transition: all .2s;
}

.pay-method-btn:hover { border-color: var(--c-primary, #6366f1); }
.pay-method-btn.selected { border-color: var(--c-primary, #6366f1); background: #f0f4ff; color: var(--c-primary, #6366f1); }

.qr-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 12px 0;
}

.qr-hint { font-size: 13px; color: #64748b; }

.dev-pay-area { margin-top: 4px; }
</style>
