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
          <span class="price-amount">¥{{ monthlyPriceText }}</span>
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
            @click="openPayModal"
            :loading="creating"
          >
            {{ !authStore.isSubscriptionActive ? '立即续费' : `续费 ¥${monthlyPriceText}/月` }}
          </n-button>
        </div>
      </div>
    </div>

    <!-- 支付弹窗 -->
    <n-modal
      v-model:show="showPayModal"
      preset="card"
      title="选择支付方式"
      style="width:440px;max-width:calc(100vw - 32px);border-radius:20px;"
      :mask-closable="!creating && !devPaying && !finishingPayment"
      @update:show="handlePayModalChange"
    >
      <div class="pay-modal">
        <div class="pay-amount-banner">
          <span class="pay-title">标准版 · 1个月</span>
          <span class="pay-amount-text">¥{{ monthlyPriceText }}</span>
        </div>

        <!-- Step1: 选择方式 -->
        <template v-if="payStep === 1">
          <n-alert v-if="paymentError" type="error" :bordered="false" class="payment-alert">
            {{ paymentError }}
          </n-alert>
          <div class="pay-methods">
            <div
              class="pay-method-btn"
              :class="{ selected: payMethod === 'wechat' }"
              @click="selectPayMethod('wechat')"
              @keyup.enter="selectPayMethod('wechat')"
              role="button"
              tabindex="0"
            >
              <n-icon size="28" class="pay-method-icon wechat-icon" aria-hidden="true">
                <LogoWechat />
              </n-icon>
              <span>微信支付</span>
            </div>
            <div
              class="pay-method-btn"
              :class="{ selected: payMethod === 'alipay' }"
              @click="selectPayMethod('alipay')"
              @keyup.enter="selectPayMethod('alipay')"
              role="button"
              tabindex="0"
            >
              <n-icon size="28" class="pay-method-icon alipay-icon" aria-hidden="true">
                <LogoAlipay />
              </n-icon>
              <span>支付宝</span>
            </div>
          </div>
          <div class="pay-actions" style="margin-top:20px;">
            <n-button secondary block @click="closePayModal">取消</n-button>
            <n-button type="primary" block :loading="creating" :disabled="creating" @click="createOrder">
              确认支付
            </n-button>
          </div>
        </template>

        <!-- Step2: 扫码支付（微信/支付宝统一） -->
        <template v-else-if="payStep === 2">
          <n-alert v-if="paymentError" type="error" :bordered="false" class="payment-alert">
            {{ paymentError }}
          </n-alert>

          <div v-if="qrCodeUrl && !qrImageFailed" class="qr-area">
            <img
              :src="qrCodeUrl"
              width="200"
              height="200"
              alt="扫码支付"
              class="payment-qr"
              @error="handleQrError"
            />
            <p class="qr-hint">请使用{{ payMethodLabel }}扫码完成支付</p>
            <p class="qr-hint qr-hint-muted">有效期15分钟，支付完成后自动更新订阅状态</p>
            <a
              v-if="payUrl"
              :href="payUrl"
              target="_blank"
              rel="noopener noreferrer"
              class="payment-link"
            >二维码无法识别？打开支付页面</a>
            <a
              v-if="urlScheme"
              :href="urlScheme"
              rel="noopener noreferrer"
              class="payment-link"
            >在支持的支付应用中打开</a>
            <n-button
              v-if="qrPayload"
              text
              size="small"
              @click="copyQrPayload"
            >复制二维码内容</n-button>
          </div>

          <div v-else-if="payUrl" class="redirect-area">
            <div class="redirect-icon" aria-hidden="true">↗</div>
            <p class="redirect-title">支付页面已准备</p>
            <p class="qr-hint">点击下方按钮完成{{ payMethodLabel }}，完成后请返回本页。</p>
            <n-button
              tag="a"
              type="primary"
              block
              :href="payUrl"
              target="_blank"
              rel="noopener noreferrer"
            >打开支付页面</n-button>
            <p class="qr-hint qr-hint-muted">本页会自动查询订单状态</p>
          </div>

          <div v-else-if="qrPayload" class="qr-payload-area">
            <p class="redirect-title">请在{{ payMethodLabel }}中识别二维码内容</p>
            <code class="qr-payload">{{ qrPayload }}</code>
            <n-button secondary block @click="copyQrPayload">复制二维码内容</n-button>
            <a
              v-if="urlScheme"
              :href="urlScheme"
              class="payment-link"
              rel="noopener noreferrer"
            >在支持的支付应用中打开</a>
          </div>

          <div v-else-if="urlScheme" class="scheme-area">
            <div class="redirect-icon" aria-hidden="true">↗</div>
            <p class="redirect-title">请在{{ payMethodLabel }}中打开支付</p>
            <p class="qr-hint">此支付入口是应用专用链接，请使用{{ payMethodLabel }}打开。</p>
            <n-button
              tag="a"
              type="primary"
              block
              :href="urlScheme"
              rel="noopener noreferrer"
            >在{{ payMethodLabel }}中打开</n-button>
          </div>

          <div v-else class="payment-unavailable">
            <p class="redirect-title">暂未获取到支付入口</p>
            <p class="qr-hint">订单已创建（{{ orderNo || orderId || '未知' }}），请稍后重试或联系管理员。</p>
            <n-button secondary block :loading="creating" @click="retryOrder">重新获取支付入口</n-button>
          </div>

          <div v-if="paymentStatus === 'pending'" class="polling-status" role="status">
            <span class="polling-dot" aria-hidden="true"></span>
            等待支付确认…
          </div>
          <div v-else-if="paymentStatus === 'paid'" class="polling-status success" role="status">
            支付已确认，正在刷新订阅状态…
          </div>

          <!-- 开发模式：模拟支付按钮 -->
          <div v-if="isDev" class="dev-pay-area">
            <n-divider style="margin:12px 0"><span style="font-size:12px;color:#f59e0b">开发模式</span></n-divider>
            <n-button
              type="warning"
              block
              size="small"
              :loading="devPaying"
              :disabled="devPaying || !orderId"
              @click="handleDevPay"
            >模拟支付完成（跳过真实扫码）</n-button>
          </div>
          <div class="pay-actions" style="margin-top:16px;">
            <n-button
              secondary
              block
              :disabled="creating || devPaying || finishingPayment"
              @click="backToMethods"
            >返回</n-button>
            <n-button
              secondary
              block
              :disabled="creating || devPaying || finishingPayment"
              @click="closePayModal"
            >关闭</n-button>
          </div>
        </template>
      </div>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useMessage } from 'naive-ui'
import { CheckmarkOutline, LogoWechat, LogoAlipay } from '@vicons/ionicons5'
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
const qrPayload = ref('')
const qrImageFailed = ref(false)
const payUrl = ref('')
const urlScheme = ref('')
const orderId = ref(null)
const orderNo = ref('')
const paymentStatus = ref('idle')
const paymentError = ref('')
const paymentConfig = ref({
  available: false,
  mode: 'unavailable',
  amount_fen: 4900,
  amount_yuan: '49.00',
})
const monthlyPriceText = computed(() => {
  const configured = Number(paymentConfig.value.amount_fen)
  if (Number.isFinite(configured) && configured > 0) {
    return (configured / 100).toFixed(2)
  }
  const fallback = Number(paymentConfig.value.amount_yuan)
  return Number.isFinite(fallback) && fallback > 0 ? fallback.toFixed(2) : '49.00'
})
// 后端同时校验 DEBUG + PAYMENT_DEV_MODE，且只有在两者均开启时才返回
// mode=development。本地生产构建也需要显示模拟支付按钮，因此以后端能力为准；
// 线上返回 gggua 时按钮仍然不可见，dev-pay 接口也会拒绝调用。
const isDev = computed(() => paymentConfig.value.mode === 'development')
let pollTimer = null
let pollStartedAt = 0
let pollInFlight = false
let pollInFlightGeneration = 0
let pollFailures = 0
const finishingPayment = ref(false)

// A checkout session is invalidated whenever the modal is reset, closed, or
// the user goes back to choose a method.  Async responses carry this value so
// a late response from an old order cannot overwrite the current checkout.
let paymentGeneration = 0
const idempotencyKey = ref('')

const POLL_INTERVAL_MS = 3000
const POLL_TIMEOUT_MS = 15 * 60 * 1000

onMounted(async () => {
  try {
    const { data } = await paymentApi.config()
    if (data && typeof data === 'object') {
      paymentConfig.value = { ...paymentConfig.value, ...data }
    }
  } catch {
    // The checkout endpoint remains the source of truth. Keep the safe local
    // fallback price if a public capability request is temporarily unavailable.
  }
})

function createIdempotencyKey() {
  try {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
      return crypto.randomUUID()
    }
  } catch {
    // Fall through to the compatibility form below.
  }
  return `checkout-${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`
}

const expireText = computed(() => {
  if (!authStore.user?.subscription_expire_at) return ''
  return new Date(authStore.user.subscription_expire_at).toLocaleDateString('zh-CN')
})

const payMethodLabel = computed(() => ({
  wechat: '微信支付',
  alipay: '支付宝',
}[payMethod.value] || '支付'))

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

function unwrapPaymentResponse(payload) {
  if (!payload || typeof payload !== 'object') return {}
  // 兼容 axios data、{ data: {...} } 以及供应商包装的 result。
  if (payload.data && typeof payload.data === 'object' && !Array.isArray(payload.data)) {
    return payload.data
  }
  if (payload.result && typeof payload.result === 'object' && !Array.isArray(payload.result)) {
    return payload.result
  }
  return payload
}

function asText(value) {
  return value === undefined || value === null ? '' : String(value).trim()
}

function isImageSource(value) {
  const source = asText(value)
  if (!source) return false
  if (/^data:image\//i.test(source) || /^blob:/i.test(source)) return true
  if (/^https?:\/\//i.test(source) || source.startsWith('/')) return true
  // 有些服务返回不带 data: 前缀的 base64 图片。
  return source.length > 100 && /^[A-Za-z0-9+/=\r\n]+$/.test(source)
}

function toImageSource(value) {
  const source = asText(value)
  if (!source) return ''
  if (/^data:image\//i.test(source) || /^blob:/i.test(source) || /^https?:\/\//i.test(source) || source.startsWith('/')) {
    return source
  }
  if (source.length > 100 && /^[A-Za-z0-9+/=\r\n]+$/.test(source)) {
    return `data:image/png;base64,${source.replace(/\s+/g, '')}`
  }
  return ''
}

function safePaymentLink(value, { allowAppScheme = false } = {}) {
  const link = asText(value)
  if (/^https?:\/\//i.test(link)) return link
  if (allowAppScheme && /^(?:weixin|weixin\-app|alipays):\/\//i.test(link)) return link
  return ''
}

function normalizeStatus(value) {
  const status = asText(value).toLowerCase()
  if (['paid', 'success', 'successful', 'completed', 'complete', 'trade_success'].includes(status)) return 'paid'
  if (['closed', 'cancelled', 'canceled', 'expired', 'timeout', 'failed', 'fail', 'refunded'].includes(status)) return status
  return 'pending'
}

function paymentErrorMessage(error, fallback = '支付请求失败，请稍后再试') {
  const status = error?.response?.status
  const rawDetail = error?.response?.data?.detail
  const detail = Array.isArray(rawDetail)
    ? rawDetail.map(item => item?.msg || item).join('；')
    : rawDetail && typeof rawDetail === 'object'
      ? asText(rawDetail.message || rawDetail.detail || rawDetail.code)
      : asText(rawDetail)

  if (status === 503 || /未配置|配置不完整|商户|支付服务|GGGUA|YunGouOS/i.test(detail)) {
    return '支付服务暂未配置或暂不可用，请联系管理员。'
  }
  if (status === 401) return '登录状态已失效，请重新登录。'
  if (status === 404) return '订单不存在或已被清理，请重新下单。'
  if (status === 409 && /过期|expired|closed|关闭/i.test(detail)) {
    return '订单已过期或关闭，请重新下单。'
  }
  if (status === 429) return '操作过于频繁，请稍后再试。'
  if (error?.code === 'ERR_NETWORK') return '网络连接失败，请检查网络后重试。'
  if (!error?.response && error instanceof Error && error.message) return error.message
  return detail || fallback
}

function setPaymentError(errorOrMessage, fallback) {
  const text = typeof errorOrMessage === 'string'
    ? errorOrMessage
    : paymentErrorMessage(errorOrMessage, fallback)
  paymentError.value = text
  message.error(text)
  return text
}

function isExpiredOrderError(error) {
  const detail = error?.response?.data?.detail
  const text = typeof detail === 'string'
    ? detail
    : detail && typeof detail === 'object'
      ? (detail.message || detail.code || '')
      : ''
  return error?.response?.status === 409 && /过期|expired|order_expired/i.test(String(text))
}

function selectPayMethod(method) {
  if (creating.value || devPaying.value) return
  if (!['wechat', 'alipay'].includes(method)) return
  if (payMethod.value !== method) {
    payMethod.value = method
    // The backend binds an idempotency key to the method.  Rotate it when
    // switching methods, while retries for the same method keep the key.
    idempotencyKey.value = createIdempotencyKey()
  }
  paymentError.value = ''
}

function openPayModal() {
  if (creating.value || devPaying.value) return
  resetPay()
  showPayModal.value = true
}

function handlePayModalChange(visible) {
  showPayModal.value = visible
  if (!visible) resetPay()
}

function closePayModal() {
  showPayModal.value = false
  resetPay()
}

function clearOrderState({ preserveBusy = false } = {}) {
  paymentGeneration += 1
  stopPolling()
  pollInFlight = false
  pollInFlightGeneration = 0
  qrCodeUrl.value = ''
  qrPayload.value = ''
  qrImageFailed.value = false
  payUrl.value = ''
  urlScheme.value = ''
  orderId.value = null
  orderNo.value = ''
  paymentStatus.value = 'idle'
  paymentError.value = ''
  pollFailures = 0
  if (!preserveBusy) {
    creating.value = false
    devPaying.value = false
  }
  finishingPayment.value = false
}

function resetPay() {
  clearOrderState()
  idempotencyKey.value = createIdempotencyKey()
  payMethod.value = 'wechat'
  payStep.value = 1
}

function backToMethods() {
  clearOrderState()
  idempotencyKey.value = createIdempotencyKey()
  payStep.value = 1
}

async function retryOrder() {
  if (creating.value || devPaying.value) return
  const method = payMethod.value
  // Keep the same key for a pending order so a lost response can be safely
  // recovered as the original provider order.  Once the backend has reported
  // a terminal/expired state, this is an intentional new checkout and must
  // use a fresh key.
  const terminal = ['closed', 'cancelled', 'canceled', 'expired', 'timeout', 'failed', 'fail', 'refunded']
  const rotateKey = terminal.includes(normalizeStatus(paymentStatus.value))
  clearOrderState()
  payMethod.value = method
  if (rotateKey) idempotencyKey.value = createIdempotencyKey()
  payStep.value = 1
  await createOrder()
}

function extractPaymentEntry(payload) {
  const data = unwrapPaymentResponse(payload)
  // GGGUA 的 qrcode 是二维码内容（如 weixin://…），不能直接当作
  // <img src>。后端会把它渲染成 qr_code_url data URI；优先使用这个
  // 明确的图片字段，再把 qrcode/qr_payload 保留为复制或深链回退。
  const explicitQr = data.qr_code_url ?? data.qrCodeUrl
  const qrIsUrl = data.qr_code_is_url ?? data.qrCodeIsUrl
  const rawPayload = data.qr_payload ?? data.qrPayload ?? data.qr_content ?? data.qrContent ?? data.qrcode ?? data.qr_code
  const rawPayUrl = data.pay_url ?? data.payUrl ?? data.payurl ?? data.payment_url ?? data.paymentUrl
  const rawScheme = data.url_scheme ?? data.urlScheme ?? data.urlscheme

  // `qr_code_is_url=false` describes the provider payload, not the adapter's
  // generated `qr_code_url` image.  Therefore an actual image data URI must
  // still win even when that flag is false.
  const explicitQrText = asText(explicitQr)
  let image = toImageSource(explicitQrText)
  let payloadText = asText(rawPayload)
  if (!payloadText && qrIsUrl === false && !image) payloadText = asText(explicitQr)
  // A raw qrcode value is normally a payment URI.  Only infer an image from
  // data/blob/base64 values; treating an arbitrary https:// payment URI as an
  // image would hide the usable payload after the image load fails.
  if (!image && isImageSource(payloadText) && !/^https?:\/\//i.test(payloadText)) {
    image = toImageSource(payloadText)
    payloadText = ''
  }

  // 兼容供应商把二维码地址放在 url/qrcode，把支付页放在 payurl 的响应。
  const genericUrl = asText(data.url)
  const payLink = safePaymentLink(rawPayUrl) || (genericUrl && !image ? safePaymentLink(genericUrl) : '')

  return {
    data,
    image,
    payload: payloadText,
    payUrl: payLink,
    urlScheme: safePaymentLink(rawScheme, { allowAppScheme: true }),
  }
}

async function createOrder() {
  if (!payMethod.value || creating.value) return
  creating.value = true
  paymentError.value = ''
  // Invalidate any queued timer/result from the preceding order, but keep the
  // busy flag and idempotency key for this request.
  clearOrderState({ preserveBusy: true })
  creating.value = true
  const generation = paymentGeneration
  const requestKey = idempotencyKey.value || createIdempotencyKey()
  idempotencyKey.value = requestKey
  try {
    const requestMethod = payMethod.value
    const { data: rawData } = await paymentApi.createOrder(
      { method: requestMethod, plan: 'monthly' },
      requestKey,
    )
    // The modal may have been closed or reset while the request was in
    // flight.  Ignore that response completely.
    if (generation !== paymentGeneration) return
    const entry = extractPaymentEntry(rawData)
    const data = entry.data
    orderId.value = data.order_id ?? data.orderId ?? data.id ?? data.order?.id ?? null
    orderNo.value = asText(data.order_no ?? data.orderNo ?? data.out_trade_no ?? data.outTradeNo ?? data.trade_no)
    paymentStatus.value = normalizeStatus(data.status ?? data.trade_status ?? data.tradeStatus)
    qrCodeUrl.value = entry.image
    qrPayload.value = entry.payload
    payUrl.value = entry.payUrl
    urlScheme.value = entry.urlScheme

    if (orderId.value === null || orderId.value === undefined || orderId.value === '') {
      throw new Error('支付服务未返回订单号，请稍后再试')
    }

    payStep.value = 2
    if (paymentStatus.value === 'paid') {
      await completePayment()
      return
    }

    if (!qrCodeUrl.value && !qrPayload.value && !payUrl.value && !urlScheme.value) {
      paymentError.value = '订单已创建，但支付服务未返回二维码或支付链接，请稍后重试。'
      message.warning(paymentError.value)
    }
    startPolling()
  } catch (error) {
    if (generation === paymentGeneration) {
      if (isExpiredOrderError(error)) {
        // The original reservation is intentionally not retried against
        // GGGUA.  Let the next click create a fresh checkout reservation.
        idempotencyKey.value = createIdempotencyKey()
      }
      setPaymentError(error, '创建订单失败，请稍后再试')
    }
  } finally {
    if (generation === paymentGeneration) {
      creating.value = false
    }
  }
}

async function refreshSubscription(successMessage = '支付成功！订阅已激活') {
  const { data: me } = await paymentApi.refreshMe()
  // `/auth/me` currently returns the user directly; keep compatibility with
  // deployments that wrap it as `{ user, tenant }` so the store never holds
  // the response envelope as if it were a user record.
  authStore.setUser(me?.user ?? me)
  if (me?.tenant) authStore.setTenant(me.tenant)
  message.success(successMessage)
}

async function completePayment(
  expectedGeneration = paymentGeneration,
  successMessage = '支付成功！订阅已激活',
) {
  if (expectedGeneration !== paymentGeneration || finishingPayment.value) return
  finishingPayment.value = true
  stopPolling()
  paymentStatus.value = 'paid'
  try {
    await refreshSubscription(successMessage)
    if (expectedGeneration !== paymentGeneration) return
    closePayModal()
  } catch (error) {
    if (expectedGeneration === paymentGeneration) {
      setPaymentError(error, '支付已确认，但订阅状态刷新失败，请刷新页面重试。')
    }
  } finally {
    if (expectedGeneration === paymentGeneration) {
      finishingPayment.value = false
    }
  }
}

async function handleDevPay() {
  if (!orderId.value || devPaying.value) return
  const generation = paymentGeneration
  const expectedOrderId = orderId.value
  devPaying.value = true
  paymentError.value = ''
  stopPolling()
  try {
    await paymentApi.devPay(expectedOrderId)
    if (generation !== paymentGeneration || orderId.value !== expectedOrderId) return
    // Reuse the normal completion gate. An already in-flight status poll may
    // observe the paid order at the same time; the gate prevents duplicate
    // refreshes and success messages.
    await completePayment(generation, '模拟支付成功！订阅已激活')
  } catch (error) {
    if (generation === paymentGeneration) {
      setPaymentError(error, '模拟支付失败')
      if (orderId.value === expectedOrderId && paymentStatus.value !== 'paid') {
        startPolling()
      }
    }
  } finally {
    if (generation === paymentGeneration) {
      devPaying.value = false
    }
  }
}

function stopPolling() {
  if (pollTimer !== null) {
    clearInterval(pollTimer)
    pollTimer = null
  }
  pollStartedAt = 0
}

function terminalStatusMessage(status) {
  return {
    closed: '订单已关闭，请重新下单。',
    cancelled: '订单已取消，请重新下单。',
    canceled: '订单已取消，请重新下单。',
    expired: '订单已过期，请重新下单。',
    timeout: '订单已超时，请重新下单。',
    failed: '支付失败，请重新下单。',
    fail: '支付失败，请重新下单。',
    refunded: '订单已退款，如有疑问请联系管理员。',
  }[status] || '订单未完成，请重新下单。'
}

async function pollOrder(expectedGeneration = paymentGeneration, expectedOrderId = orderId.value) {
  if (
    expectedGeneration !== paymentGeneration ||
    !expectedOrderId ||
    orderId.value !== expectedOrderId ||
    (pollInFlight && pollInFlightGeneration === expectedGeneration) ||
    finishingPayment.value
  ) return
  if (pollStartedAt && Date.now() - pollStartedAt >= POLL_TIMEOUT_MS) {
    stopPolling()
    paymentStatus.value = 'expired'
    setPaymentError('二维码已过期，请返回后重新下单。')
    return
  }

  pollInFlight = true
  pollInFlightGeneration = expectedGeneration
  try {
    const { data: rawData } = await paymentApi.checkOrder(expectedOrderId)
    if (expectedGeneration !== paymentGeneration || orderId.value !== expectedOrderId) return
    const data = unwrapPaymentResponse(rawData)
    const status = normalizeStatus(data.status ?? data.trade_status ?? data.tradeStatus)
    paymentStatus.value = status
    // A successful response means a transient network warning is no longer
    // actionable. Preserve other user-facing errors (e.g. QR image failure).
    if (paymentError.value === '暂时无法查询支付状态，正在重试…') {
      paymentError.value = ''
    }
    pollFailures = 0
    if (status === 'paid') {
      await completePayment(expectedGeneration)
    } else if (['closed', 'cancelled', 'canceled', 'expired', 'timeout', 'failed', 'fail', 'refunded'].includes(status)) {
      stopPolling()
      setPaymentError(terminalStatusMessage(status))
    }
  } catch (error) {
    if (expectedGeneration !== paymentGeneration || orderId.value !== expectedOrderId) return
    pollFailures += 1
    const status = error?.response?.status
    if (status === 401 || status === 404) {
      stopPolling()
      setPaymentError(error, '查询订单失败，请重新下单。')
    } else if (pollFailures >= 3 && !paymentError.value) {
      // 网络抖动不立即结束订单，但给用户可见反馈；后续轮询仍会继续。
      paymentError.value = '暂时无法查询支付状态，正在重试…'
    }
  } finally {
    if (pollInFlightGeneration === expectedGeneration) {
      pollInFlight = false
      pollInFlightGeneration = 0
    }
  }
}

function startPolling() {
  stopPolling()
  if (!orderId.value) return
  const generation = paymentGeneration
  const expectedOrderId = orderId.value
  paymentStatus.value = paymentStatus.value === 'paid' ? 'paid' : 'pending'
  pollStartedAt = Date.now()
  pollFailures = 0
  // 先查一次，避免用户必须等待完整的 3 秒间隔。
  void pollOrder(generation, expectedOrderId)
  pollTimer = setInterval(() => { void pollOrder(generation, expectedOrderId) }, POLL_INTERVAL_MS)
}

function handleQrError() {
  qrImageFailed.value = true
  if (!paymentError.value) {
    paymentError.value = '二维码加载失败，请使用支付链接或返回后重新下单。'
  }
}

async function copyQrPayload() {
  if (!qrPayload.value) return
  try {
    if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(qrPayload.value)
      message.success('支付链接已复制')
      return
    }
  } catch {
    // 继续显示文本，用户可以手动复制。
  }
  message.info('请长按或手动复制支付链接')
}

onUnmounted(() => {
  // Invalidate in-flight requests as the component leaves the page. Their
  // eventual responses must not mutate an unmounted/new checkout instance.
  paymentGeneration += 1
  stopPolling()
  pollInFlight = false
  pollInFlightGeneration = 0
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

.pay-method-icon {
  flex: 0 0 auto;
}

.wechat-icon { color: #07c160; }
.alipay-icon { color: #1677ff; }

.pay-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.pay-actions .n-button {
  min-width: 0;
  width: 100%;
}

.qr-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 12px 0;
}

.payment-qr {
  display: block;
  width: 200px;
  height: 200px;
  object-fit: contain;
  border-radius: 8px;
  background: #fff;
}

.payment-alert {
  margin-bottom: 2px;
}

.payment-link {
  color: var(--c-primary, #6366f1);
  font-size: 13px;
  text-decoration: none;
}

.payment-link:hover { text-decoration: underline; }

.redirect-area,
.scheme-area,
.qr-payload-area,
.payment-unavailable {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 16px 0;
  text-align: center;
}

.redirect-icon {
  display: grid;
  width: 48px;
  height: 48px;
  place-items: center;
  border-radius: 50%;
  background: #eef2ff;
  color: var(--c-primary, #6366f1);
  font-size: 28px;
  font-weight: 700;
}

.redirect-title {
  margin: 0;
  color: #334155;
  font-size: 15px;
  font-weight: 600;
}

.qr-payload {
  display: block;
  width: 100%;
  max-height: 96px;
  overflow: auto;
  padding: 10px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f8fafc;
  color: #475569;
  font-size: 11px;
  line-height: 1.5;
  overflow-wrap: anywhere;
  text-align: left;
  user-select: text;
}

.qr-hint-muted {
  margin-top: -2px;
  color: #94a3b8;
  font-size: 12px;
}

.polling-status {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  color: #64748b;
  font-size: 12px;
}

.polling-status.success { color: #059669; }

.polling-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #f59e0b;
  box-shadow: 0 0 0 4px rgba(245, 158, 11, .14);
}

.qr-hint { font-size: 13px; color: #64748b; }

.dev-pay-area { margin-top: 4px; }

@media (max-width: 768px) {
  .plans-grid {
    grid-template-columns: 1fr;
  }
}
</style>
