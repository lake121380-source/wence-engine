<template>
  <div class="login-page">
    <div class="login-card">
      <h1>文策引擎</h1>
      <p class="subtitle">管理后台</p>

      <!-- 初始化提示 -->
      <n-alert v-if="needInit" type="info" style="margin-bottom: 16px">
        首次使用，请创建管理员账号
      </n-alert>

      <n-form ref="formRef" :model="form" :rules="rules">
        <n-form-item path="username" label="用户名">
          <n-input v-model:value="form.username" placeholder="请输入用户名" @keyup.enter="handleSubmit" />
        </n-form-item>
        <n-form-item path="password" label="密码">
          <n-input v-model:value="form.password" type="password" show-password-on="click"
            placeholder="请输入密码" @keyup.enter="handleSubmit" />
        </n-form-item>
        <n-button type="primary" block :loading="loading" @click="handleSubmit" style="margin-top: 8px">
          {{ needInit ? '创建并登录' : '登 录' }}
        </n-button>
      </n-form>
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
const needInit = ref(false)
const formRef = ref(null)

const form = ref({ username: '', password: '' })
const rules = {
  username: { required: true, message: '请输入用户名', trigger: 'blur' },
  password: { required: true, message: '请输入密码', trigger: 'blur' },
}

onMounted(async () => {
  // 检查是否需要初始化（尝试 /me，如果返回 401 且无管理员则需初始化）
  try {
    await authApi.me()
    // 已登录，直接跳转
    router.replace('/')
  } catch (e) {
    // 未登录，检查是否需要初始化
  }
})

async function handleSubmit() {
  try {
    await formRef.value?.validate()
  } catch { return }

  loading.value = true
  try {
    let res
    if (needInit.value) {
      res = await authApi.init(form.value)
      message.success('管理员账号创建成功')
    } else {
      try {
        res = await authApi.login(form.value)
      } catch (e) {
        // 如果返回 401 且 detail 包含"不存在"，可能需要初始化
        if (e.response?.status === 401 && !needInit.value) {
          // 尝试初始化
          try {
            res = await authApi.init(form.value)
            message.success('管理员账号创建成功')
          } catch (e2) {
            if (e2.response?.data?.detail?.includes('已存在')) {
              message.error('用户名或密码错误')
            } else {
              message.error(e2.response?.data?.detail || '登录失败')
            }
            return
          }
        } else {
          message.error(e.response?.data?.detail || '登录失败')
          return
        }
      }
    }
    const data = res.data
    localStorage.setItem('admin_token', data.token)
    localStorage.setItem('admin_user', JSON.stringify(data.admin))
    router.replace('/')
  } catch (e) {
    message.error(e.response?.data?.detail || '操作失败')
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
</style>
