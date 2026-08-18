<template>
  <div>
    <n-spin :show="loading">
      <!-- 概览卡片 -->
      <n-grid :cols="4" :x-gap="16" :y-gap="16">
        <n-gi>
          <n-card class="stat-card">
            <n-statistic label="总用户数" :value="data.overview?.total_users || 0">
              <template #suffix>
                <n-tag v-if="data.overview?.today_new_users" type="success" size="small" round>
                  今日 +{{ data.overview.today_new_users }}
                </n-tag>
              </template>
            </n-statistic>
          </n-card>
        </n-gi>
        <n-gi>
          <n-card class="stat-card">
            <n-statistic label="付费用户" :value="data.overview?.paid_users || 0">
              <template #suffix>
                <n-text depth="3" style="font-size: 13px">
                  / 活跃 {{ data.overview?.active_subscriptions || 0 }}
                </n-text>
              </template>
            </n-statistic>
          </n-card>
        </n-gi>
        <n-gi>
          <n-card class="stat-card">
            <n-statistic label="本月收入" :value="'¥' + (data.overview?.month_revenue || 0)">
              <template #suffix>
                <n-text depth="3" style="font-size: 13px">
                  累计 ¥{{ data.overview?.total_revenue || 0 }}
                </n-text>
              </template>
            </n-statistic>
          </n-card>
        </n-gi>
        <n-gi>
          <n-card class="stat-card">
            <n-statistic label="租户数" :value="data.overview?.total_tenants || 0">
              <template #suffix>
                <n-text depth="3" style="font-size: 13px">
                  试用 {{ data.overview?.trial_users || 0 }}
                </n-text>
              </template>
            </n-statistic>
          </n-card>
        </n-gi>
      </n-grid>

      <!-- 内容统计 -->
      <n-grid :cols="3" :x-gap="16" :y-gap="16" style="margin-top: 16px">
        <n-gi>
          <n-card size="small">
            <n-statistic label="博主数" :value="data.content?.total_creators || 0" />
          </n-card>
        </n-gi>
        <n-gi>
          <n-card size="small">
            <n-statistic label="选题数" :value="data.content?.total_topics || 0" />
          </n-card>
        </n-gi>
        <n-gi>
          <n-card size="small">
            <n-statistic label="生成次数" :value="data.content?.total_generations || 0" />
          </n-card>
        </n-gi>
      </n-grid>

      <!-- 趋势图 -->
      <n-grid :cols="2" :x-gap="16" style="margin-top: 16px">
        <n-gi>
          <n-card title="近7日注册趋势" size="small">
            <div class="chart-bars">
              <div v-for="item in data.register_trend || []" :key="item.date" class="bar-item">
                <div class="bar-value">{{ item.count }}</div>
                <div class="bar" :style="{ height: barHeight(item.count, maxRegister) }"></div>
                <div class="bar-label">{{ item.date }}</div>
              </div>
            </div>
          </n-card>
        </n-gi>
        <n-gi>
          <n-card title="近7日收入趋势" size="small">
            <div class="chart-bars">
              <div v-for="item in data.revenue_trend || []" :key="item.date" class="bar-item">
                <div class="bar-value">{{ item.amount > 0 ? '¥' + item.amount : '0' }}</div>
                <div class="bar revenue" :style="{ height: barHeight(item.amount, maxRevenue) }"></div>
                <div class="bar-label">{{ item.date }}</div>
              </div>
            </div>
          </n-card>
        </n-gi>
      </n-grid>
    </n-spin>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { dashboardApi } from '../api'

const loading = ref(false)
const data = ref({})

const maxRegister = computed(() => {
  const vals = (data.value.register_trend || []).map(i => i.count)
  return Math.max(...vals, 1)
})

const maxRevenue = computed(() => {
  const vals = (data.value.revenue_trend || []).map(i => i.amount)
  return Math.max(...vals, 1)
})

function barHeight(val, max) {
  if (!val || !max) return '2px'
  return Math.max(val / max * 120, 2) + 'px'
}

async function fetchData() {
  loading.value = true
  try {
    const res = await dashboardApi.get()
    data.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
</script>

<style scoped>
.stat-card {
  text-align: center;
}
.chart-bars {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 160px;
  padding-top: 20px;
}
.bar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
}
.bar-value {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 4px;
}
.bar {
  width: 28px;
  background: linear-gradient(180deg, #63e2b7, #18a058);
  border-radius: 4px 4px 0 0;
  min-height: 2px;
  transition: height 0.3s;
}
.bar.revenue {
  background: linear-gradient(180deg, #70c0e8, #2080f0);
}
.bar-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
  margin-top: 6px;
}
</style>
