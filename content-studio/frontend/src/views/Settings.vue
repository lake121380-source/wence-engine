<template>
  <div>
    <div class="page-header">
      <div>
        <div class="page-title">个人设置</div>
        <div class="page-subtitle">修改密码、查看订阅状态</div>
      </div>
    </div>

    <div class="settings-layout">
      <!-- 修改密码 -->
      <div class="section-card">
        <div class="section-title">修改密码</div>
        <n-form label-placement="top" :show-feedback="false" size="large" style="max-width:400px;">
          <n-form-item label="原密码">
            <n-input
              v-model:value="pwdForm.old_password"
              type="password"
              show-password-on="click"
              placeholder="请输入当前密码"
            />
          </n-form-item>
          <n-form-item label="新密码">
            <n-input
              v-model:value="pwdForm.new_password"
              type="password"
              show-password-on="click"
              placeholder="至少 8 位，含字母和数字"
            />
          </n-form-item>
          <n-form-item label="确认新密码">
            <n-input
              v-model:value="pwdForm.confirm_password"
              type="password"
              show-password-on="click"
              placeholder="再次输入新密码"
            />
          </n-form-item>
          <n-form-item>
            <n-button type="primary" :loading="changingPwd" @click="doChangePwd">
              保存新密码
            </n-button>
          </n-form-item>
        </n-form>
      </div>

      <!-- 订阅状态 -->
      <div class="section-card">
        <div class="section-title">我的订阅</div>
        <div class="sub-row">
          <div class="sub-item">
            <div class="sub-label">当前状态</div>
            <n-tag :type="authStore.planType" :bordered="false" size="medium">
              {{ authStore.planLabel }}
            </n-tag>
          </div>
          <div class="sub-item">
            <div class="sub-label">到期时间</div>
            <div class="sub-value">{{ expireText }}</div>
          </div>
          <div class="sub-item" style="margin-top:4px;">
            <n-button type="primary" @click="$router.push('/pricing')" size="small">
              {{ authStore.isSubscriptionActive ? '续费' : '立即订阅' }}
            </n-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useMessage } from 'naive-ui'
import { useAuthStore } from '../stores/auth.js'
import { authApi } from '../api/index.js'

const message = useMessage()
const authStore = useAuthStore()

const changingPwd = ref(false)
const pwdForm = ref({ old_password: '', new_password: '', confirm_password: '' })

async function doChangePwd() {
  if (!pwdForm.value.old_password) return message.warning('请输入原密码')
  if (pwdForm.value.new_password.length < 8) return message.warning('新密码至少 8 位')
  if (pwdForm.value.new_password !== pwdForm.value.confirm_password) return message.warning('两次输入的新密码不一致')
  changingPwd.value = true
  try {
    await authApi.changePassword({
      old_password: pwdForm.value.old_password,
      new_password: pwdForm.value.new_password,
    })
    message.success('密码修改成功')
    pwdForm.value = { old_password: '', new_password: '', confirm_password: '' }
  } catch (e) {
    message.error(e.response?.data?.detail || '修改失败')
  } finally {
    changingPwd.value = false
  }
}

const expireText = computed(() => {
  if (!authStore.user?.subscription_expire_at) return '无订阅'
  const d = new Date(authStore.user.subscription_expire_at)
  const dateStr = d.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
  const timeStr = d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  if (!authStore.isSubscriptionActive) return `${dateStr} ${timeStr}（已到期）`
  const hours = authStore.hoursUntilExpiry
  const days = authStore.daysUntilExpiry
  if (days < 1) return `${dateStr} ${timeStr}（还剩 ${hours} 小时）`
  return `${dateStr} ${timeStr}（还剩 ${days} 天）`
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-xl, 24px);
}
.page-title { font-size: 22px; font-weight: 600; color: var(--c-text-1, #0f172a); }
.page-subtitle { font-size: 13px; color: var(--c-text-4, #94a3b8); margin-top: 4px; }

.settings-layout {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 560px;
}

.section-card {
  background: var(--c-bg-elevated, #fff);
  border: 1px solid var(--c-border, rgba(0,0,0,.06));
  border-radius: var(--radius-lg, 12px);
  padding: 24px;
  box-shadow: var(--shadow-sm, 0 1px 2px rgba(0,0,0,.04));
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--c-text-1, #0f172a);
  margin-bottom: 20px;
}

.sub-row { display: flex; gap: 32px; align-items: flex-start; flex-wrap: wrap; }
.sub-item { display: flex; flex-direction: column; gap: 6px; }
.sub-label { font-size: 12px; color: var(--c-text-4, #94a3b8); }
.sub-value { font-size: 14px; color: #334155; font-weight: 500; }
</style>
