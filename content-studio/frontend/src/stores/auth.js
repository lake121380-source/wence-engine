import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('cs_token') || '')
  const user = ref(JSON.parse(localStorage.getItem('cs_user') || 'null'))
  const tenant = ref(JSON.parse(localStorage.getItem('cs_tenant') || 'null'))

  const isAuthenticated = computed(() => !!token.value)

  const subscriptionEndAt = computed(() => {
    if (user.value?.subscription_expire_at) {
      const d = new Date(user.value.subscription_expire_at)
      if (!Number.isNaN(d.getTime())) return d
    }
    if (tenant.value?.subscription_end_at) return new Date(tenant.value.subscription_end_at)
    if (user.value?.trial_expires_at) return new Date(user.value.trial_expires_at)
    return null
  })

  const isSubscriptionActive = computed(() => {
    if (typeof user.value?.is_subscription_active === 'boolean') {
      return user.value.is_subscription_active
    }
    if (!subscriptionEndAt.value) return false
    return subscriptionEndAt.value > new Date()
  })

  const daysUntilExpiry = computed(() => {
    if (!subscriptionEndAt.value) return 0
    const diff = subscriptionEndAt.value - new Date()
    if (diff <= 0) return 0
    return Math.floor(diff / (1000 * 60 * 60 * 24))
  })

  const hoursUntilExpiry = computed(() => {
    if (!subscriptionEndAt.value) return 0
    const diff = subscriptionEndAt.value - new Date()
    if (diff <= 0) return 0
    return Math.ceil(diff / (1000 * 60 * 60))
  })

  const isTrial = computed(() => {
    if (typeof user.value?.is_trial === 'boolean') {
      return user.value.is_trial
    }
    return !!user.value?.trial_expires_at && !tenant.value?.subscription_end_at
  })

  const planLabel = computed(() => {
    if (!isSubscriptionActive.value) return '用户'
    if (isTrial.value) return '体验会员'
    return '会员'
  })

  const planType = computed(() => {
    if (!isSubscriptionActive.value) return 'error'
    if (isTrial.value) return 'warning'
    return 'success'
  })

  function setToken(t) {
    token.value = t
    if (t) localStorage.setItem('cs_token', t)
    else localStorage.removeItem('cs_token')
  }

  function setUser(u) {
    user.value = u
    if (u) localStorage.setItem('cs_user', JSON.stringify(u))
    else localStorage.removeItem('cs_user')
  }

  function setTenant(t) {
    tenant.value = t
    if (t) localStorage.setItem('cs_tenant', JSON.stringify(t))
    else localStorage.removeItem('cs_tenant')
  }

  function logout() {
    setToken('')
    setUser(null)
    setTenant(null)
  }

  return {
    token, user, tenant,
    isAuthenticated, isSubscriptionActive, daysUntilExpiry, hoursUntilExpiry, isTrial, planLabel, planType, subscriptionEndAt,
    setToken, setUser, setTenant, logout,
  }
})
