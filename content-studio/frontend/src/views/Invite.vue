<template>
  <div class="invite-page">
    <div class="invite-card">
      <div v-if="loading" style="text-align:center;padding:40px;">
        <n-spin size="large" />
        <p style="margin-top:16px;color:#94a3b8;">正在处理邀请...</p>
      </div>
      <div v-else-if="success" style="text-align:center;padding:40px;">
        <div style="font-size:48px;margin-bottom:16px;"><n-icon size="48" color="var(--c-success, #22c55e)"><CheckmarkCircleOutline /></n-icon></div>
        <h2 style="margin:0 0 8px">加入成功</h2>
        <p style="color:#94a3b8;">你已成功加入团队</p>
        <n-button type="primary" size="large" style="margin-top:24px;" @click="$router.replace('/')">
          进入工作台
        </n-button>
      </div>
      <div v-else style="text-align:center;padding:40px;">
        <div style="font-size:48px;margin-bottom:16px;"><n-icon size="48" color="var(--c-primary, #6366f1)"><MailOutline /></n-icon></div>
        <h2 style="margin:0 0 8px">你收到了一个邀请</h2>
        <p style="color:#94a3b8;">点击下方按钮接受邀请并加入团队</p>
        <p v-if="errorMsg" style="color:#f87171;margin-top:12px;">{{ errorMsg }}</p>
        <n-button
          type="primary"
          size="large"
          style="margin-top:24px;"
          :loading="accepting"
          @click="acceptInvite"
        >
          接受邀请
        </n-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { useAuthStore } from '../stores/auth.js'
import { tenantApi } from '../api/index.js'
import { CheckmarkCircleOutline, MailOutline } from '@vicons/ionicons5'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const authStore = useAuthStore()

const loading = ref(false)
const accepting = ref(false)
const success = ref(false)
const errorMsg = ref('')

async function acceptInvite() {
  const token = route.query.token
  if (!token) {
    errorMsg.value = '邀请链接无效（缺少 token）'
    return
  }
  if (!authStore.isAuthenticated) {
    message.warning('请先登录后再接受邀请')
    router.push(`/login?redirect=${encodeURIComponent(route.fullPath)}`)
    return
  }
  accepting.value = true
  errorMsg.value = ''
  try {
    await tenantApi.acceptInvite(token)
    success.value = true
    // 刷新用户信息以获取新的 tenant
    const { data: me } = await import('../api/index.js').then(m => m.authApi.me())
    authStore.setUser(me.user || me)
    if (me.tenant) authStore.setTenant(me.tenant)
  } catch (e) {
    errorMsg.value = e.response?.data?.detail || '接受邀请失败，链接可能已过期'
  } finally {
    accepting.value = false
  }
}

onMounted(() => {
  if (!route.query.token) {
    errorMsg.value = '邀请链接无效'
  }
  if (!authStore.isAuthenticated) {
    message.info('请先登录后再接受邀请')
    router.push(`/login?redirect=${encodeURIComponent(route.fullPath)}`)
  }
})
</script>

<style scoped>
.invite-page {
  min-height: 80vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
.invite-card {
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.08);
  max-width: 440px;
  width: 100%;
}
</style>
