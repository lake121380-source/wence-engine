<template>
  <div class="login-page">
    <div class="login-card">
      <h1>文策引擎</h1>
      <p class="subtitle">管理后台</p>

      <!-- 初始化提示 -->
      <n-alert v-if="initMode" type="info" style="margin-bottom: 16px">
        首次部署需创建管理员。请填写服务端环境变量 ADMIN_INIT_TOKEN 的值；
        该接口仅在系统内没有任何管理员时可用。
      </n-alert>

      <n-form ref="formRef" :model="form" :rules="rules">
        <n-form-item path="username" label="用户名">
          <n-input v-model:value="form.username" placeholder="请输入用户名" @keyup.enter="handleSubmit" />
        </n-form-item>
        <n-form-item path="password" label="密码">
          <n-input v-model:value="form.password" type="password" show-password-on="click"
            placeholder="请输入密码" @keyup.enter="handleSubmit" />
        </n-form-item>
        <n-form-item v-if="initMode" label="初始化 Token">
          <n-input v-model:value="initToken" placeholder="服务端 .env 中的 ADMIN_INIT_TOKEN"
            @keyup.enter="handleSubmit" />
        </n-form-item>
        <n-button type="primary" block :loading="loading" @click="handleSubmit" style="margin-top: 8px">
          {{ initMode ? '创建并登录' : '登 录' }}
        </n-button>
      </n-form>

      <div class="init-toggle">
        <a href="#" @click.prevent="toggleInitMode">
          {{ initMode ? '返回登录' : '首次部署？初始化管理员' }}
        </a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { authApi } from '../api'

const router = useRouter()
const message = useMessage()
const loading = ref(false)
const initMode = ref(false)
const initToken = ref('')
const formRef = ref(null)

const form = ref({ username: '', password: '' })
const rules = {
  username: { required: true, message: '请输入用户名', trigger: 'blur' },
  password: { required: true, message: '请输入密码', trigger: 'blur' },
}

function toggleInitMode() {
  initMode.value = !initMode.value
  initToken.value = ''
}

onMounted(async () => {
  // 已登录则直接进入后台；未登录就留在本页。
  try {
    await authApi.me()
    router.replace('/')
  } catch (e) {
    // 未登录属正常情况
  }
})

async function handleSubmit() {
  try {
    await formRef.value?.validate()
  } catch { return }

  if (initMode.value && !initToken.value.trim()) {
    message.error('请填写初始化 Token')
    return
  }

  loading.value = true
  try {
    const res = initMode.value
      ? await authApi.init(form.value, initToken.value.trim())
      : await authApi.login(form.value)
    if (initMode.value) message.success('管理员账号创建成功')
    const data = res.data
    localStorage.setItem('admin_token', data.token)
    localStorage.setItem('admin_user', JSON.stringify(data.admin))
    router.replace('/')
  } catch (e) {
    message.error(e.response?.data?.detail || (initMode.value ? '初始化失败' : '登录失败'))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
}
.login-card {
  width: 380px;
  padding: 40px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
}
h1 {
  color: #fff;
  margin: 0 0 4px 0;
  font-size: 24px;
  text-align: center;
}
.subtitle {
  color: rgba(255, 255, 255, 0.5);
  text-align: center;
  margin: 0 0 24px 0;
  font-size: 14px;
}
.init-toggle {
  margin-top: 16px;
  text-align: center;
  font-size: 13px;
}
.init-toggle a {
  color: rgba(255, 255, 255, 0.45);
  text-decoration: none;
}
.init-toggle a:hover {
  color: rgba(255, 255, 255, 0.8);
}
</style>
