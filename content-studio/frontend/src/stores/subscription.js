import { defineStore } from 'pinia'
import { ref } from 'vue'

/**
 * 订阅过期提示 Store
 * 当 API 返回 402 时，显示弹窗而非直接跳转，让用户知道哪些功能受限。
 */
export const useSubscriptionStore = defineStore('subscription', () => {
  // 是否显示过期弹窗
  const showExpiredModal = ref(false)
  // 触发原因（用户做了什么操作被拦截了）
  const triggerAction = ref('')

  function triggerExpired(action = '') {
    triggerAction.value = action
    showExpiredModal.value = true
  }

  function dismiss() {
    showExpiredModal.value = false
    triggerAction.value = ''
  }

  return { showExpiredModal, triggerAction, triggerExpired, dismiss }
})
