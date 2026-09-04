<template>
  <div class="settings-page">
    <!-- 页面头部 -->
    <div class="settings-header">
      <div class="header-left">
        <h1 class="page-title">个人与工作台设置</h1>
        <p class="page-subtitle">管理您的创作者名片、AI 创作引擎偏好、账号安全及订阅权益</p>
      </div>
      <div class="header-right">
        <n-button secondary size="small" @click="$router.push('/generate')">
          <template #icon>
            <n-icon><SparklesOutline /></n-icon>
          </template>
          进入创作工作台
        </n-button>
      </div>
    </div>

    <!-- 用户身份快速概览卡片 (Profile Hero Strip) -->
    <div class="profile-hero-card">
      <div class="profile-hero-left">
        <div class="avatar-container">
          <n-avatar
            :src="currentAvatarUrl"
            :size="68"
            round
            class="hero-avatar"
          />
          <button class="avatar-edit-badge" @click="activeTab = 'profile'" title="更换头像">
            <n-icon size="14"><CameraOutline /></n-icon>
          </button>
        </div>
        <div class="profile-hero-meta">
          <div class="hero-name-row">
            <span class="hero-user-name">{{ userProfile.nickname || authStore.user?.nickname || '创作者' }}</span>
            <n-tag
              :type="authStore.planType"
              :bordered="false"
              size="small"
              class="hero-plan-tag"
            >
              {{ authStore.planLabel }}
            </n-tag>
            <span class="user-role-badge">独立创作者</span>
          </div>
          <div class="hero-account-email">
            <n-icon size="14" class="email-icon"><MailOutline /></n-icon>
            <span>{{ authStore.user?.email || 'user@wence.ai' }}</span>
            <span class="meta-dot">·</span>
            <span class="meta-sub-info">
              <span v-if="authStore.isSubscriptionActive">
                {{ authStore.isTrial ? '体验权益还剩' : '会员有效期还剩' }}
                <strong class="highlight-days">{{ authStore.daysUntilExpiry < 1 ? authStore.hoursUntilExpiry + ' 小时' : authStore.daysUntilExpiry + ' 天' }}</strong>
              </span>
              <span v-else class="expired-text">已到期，建议及时续订</span>
            </span>
          </div>
        </div>
      </div>

      <div class="profile-hero-actions">
        <n-button type="primary" size="medium" @click="$router.push('/pricing')">
          <template #icon><n-icon><CardOutline /></n-icon></template>
          {{ authStore.isSubscriptionActive ? '续费与升级' : '开通会员' }}
        </n-button>
      </div>
    </div>

    <!-- 主体多标签页设置容器 -->
    <div class="settings-content-shell">
      <n-tabs v-model:value="activeTab" type="line" animated class="settings-tabs">
        
        <!-- 标签 1: 个人资料与创作者名片 -->
        <n-tab-pane name="profile" tab="创作者名片">
          <div class="tab-card-body">
            <div class="pane-section">
              <div class="section-heading">
                <div class="section-title">基本信息与形象</div>
                <div class="section-desc">定制您的创作者形象，在文案导出与团队协作中展示</div>
              </div>

              <!-- 头像挑选器 -->
              <div class="avatar-picker-row">
                <div class="picker-label">快速选择形象头像：</div>
                <div class="preset-avatars-list">
                  <div
                    v-for="(av, idx) in presetAvatars"
                    :key="idx"
                    class="avatar-option-item"
                    :class="{ selected: selectedAvatarIdx === idx }"
                    @click="choosePresetAvatar(idx)"
                  >
                    <n-avatar :src="av.url" round :size="46" />
                    <div v-if="selectedAvatarIdx === idx" class="avatar-check-badge">
                      <n-icon size="12"><CheckmarkOutline /></n-icon>
                    </div>
                  </div>
                </div>
              </div>

              <n-form label-placement="top" size="medium" class="profile-form">
                <div class="form-grid-2">
                  <n-form-item label="创作者昵称 / 品牌名">
                    <n-input
                      v-model:value="userProfile.nickname"
                      placeholder="例如：科技王老师、美妆策研室"
                      maxlength="30"
                      show-count
                    />
                  </n-form-item>
                  <n-form-item label="注册绑定邮箱">
                    <n-input
                      :value="authStore.user?.email"
                      disabled
                      placeholder="绑定邮箱"
                    >
                      <template #suffix>
                        <n-tag type="success" size="tiny" :bordered="false">已安全验证</n-tag>
                      </template>
                    </n-input>
                  </n-form-item>
                </div>

                <n-form-item label="主攻垂直内容赛道 (可多选，辅助 AI 定向选题)">
                  <div class="tracks-selector">
                    <div
                      v-for="track in contentTracks"
                      :key="track.id"
                      class="track-chip"
                      :class="{ active: userProfile.selectedTracks.includes(track.id) }"
                      @click="toggleTrack(track.id)"
                    >
                      <span class="track-icon">{{ track.icon }}</span>
                      <span class="track-name">{{ track.name }}</span>
                    </div>
                  </div>
                </n-form-item>

                <n-form-item label="个人创作宣言 / 口播人设口吻 (Prompt 上下文注入)">
                  <n-input
                    v-model:value="userProfile.bio"
                    type="textarea"
                    :rows="3"
                    placeholder="例如：专注 3C 数码硬核拆解，口吻幽默风趣、语速紧凑，拒绝官话套话，喜欢用日常案例拆解复杂参数..."
                    maxlength="200"
                    show-count
                  />
                </n-form-item>

                <div class="form-action-row">
                  <n-button type="primary" :loading="savingProfile" @click="saveProfile">
                    保存创作者名片
                  </n-button>
                  <n-button quaternary @click="resetProfile">重置更改</n-button>
                </div>
              </n-form>
            </div>
          </div>
        </n-tab-pane>

        <!-- 标签 2: AI 创作引擎偏好设置 -->
        <n-tab-pane name="preferences" tab="创作习惯偏好">
          <div class="tab-card-body">
            <div class="pane-section">
              <div class="section-heading">
                <div class="section-title">默认创作输出规范</div>
                <div class="section-desc">配置进入「生成文案」工作台时的默认首选预设，大幅减少重复配置时间</div>
              </div>

              <div class="pref-options-container">
                <!-- 预设平台 -->
                <div class="pref-card">
                  <div class="pref-card-header">
                    <div class="pref-title">默认发布主平台</div>
                    <div class="pref-sub">针对不同平台算法自动预置结构调性</div>
                  </div>
                  <div class="platform-cards-row">
                    <div
                      v-for="p in platforms"
                      :key="p.id"
                      class="platform-select-card"
                      :class="{ selected: userPref.defaultPlatform === p.id }"
                      @click="userPref.defaultPlatform = p.id"
                    >
                      <span class="plat-badge" :style="{ background: p.bg, color: p.color }">{{ p.name }}</span>
                      <span class="plat-desc">{{ p.desc }}</span>
                    </div>
                  </div>
                </div>

                <!-- 预设文案篇幅与语速节奏 -->
                <div class="pref-card">
                  <div class="pref-card-header">
                    <div class="pref-title">默认脚本时长与字数篇幅</div>
                    <div class="pref-sub">决定 AI 展开故事与观点时的结构紧凑程度</div>
                  </div>
                  <div class="length-options-row">
                    <div
                      v-for="l in lengthOptions"
                      :key="l.id"
                      class="length-select-card"
                      :class="{ selected: userPref.defaultLength === l.id }"
                      @click="userPref.defaultLength = l.id"
                    >
                      <div class="len-title">{{ l.title }}</div>
                      <div class="len-range">{{ l.words }}</div>
                      <div class="len-time">{{ l.time }}</div>
                    </div>
                  </div>
                </div>

                <!-- 视听分镜详略度 -->
                <div class="pref-card">
                  <div class="pref-card-header">
                    <div class="pref-title">分镜镜头指引默认详细度</div>
                    <div class="pref-sub">实拍创作者推荐选择完整机位规范</div>
                  </div>
                  <n-radio-group v-model:value="userPref.defaultStoryboardLevel">
                    <n-space vertical :size="12">
                      <n-radio value="full">
                        <strong>专业实拍五维分镜表</strong>（包含景别、运镜轨迹、同期声台词、画面花字与 BGM 重音点）
                      </n-radio>
                      <n-radio value="compact">
                        <strong>紧凑口播提词版</strong>（仅标注关键转场、手势动作与重点强调词，适合速拍）
                      </n-radio>
                      <n-radio value="script_only">
                        <strong>纯台词脚本模式</strong>（仅生成口播文案与自然换行断句）
                      </n-radio>
                    </n-space>
                  </n-radio-group>
                </div>

                <!-- 默认语气基调 -->
                <div class="pref-card">
                  <div class="pref-card-header">
                    <div class="pref-title">默认口吻调性倾向</div>
                    <div class="pref-sub">为文案赋予更有辨识度的真人人设网感</div>
                  </div>
                  <div class="tone-chips-grid">
                    <div
                      v-for="tone in toneOptions"
                      :key="tone.id"
                      class="tone-chip"
                      :class="{ active: userPref.defaultTone === tone.id }"
                      @click="userPref.defaultTone = tone.id"
                    >
                      <span class="tone-name">{{ tone.name }}</span>
                      <span class="tone-desc">{{ tone.desc }}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div class="form-action-row" style="margin-top:24px;">
                <n-button type="primary" @click="savePreferences">
                  保存创作习惯预设
                </n-button>
                <n-button quaternary @click="resetPreferences">恢复默认设置</n-button>
              </div>
            </div>
          </div>
        </n-tab-pane>

        <!-- 标签 3: 账户安全与密码管理 -->
        <n-tab-pane name="security" tab="账户与密码安全">
          <div class="tab-card-body">
            <div class="pane-section">
              <div class="section-heading">
                <div class="section-title">修改登录密码</div>
                <div class="section-desc">定期更新密码有助于保护您的知识库资产与创作者数据</div>
              </div>

              <n-form label-placement="top" size="medium" style="max-width: 440px;">
                <n-form-item label="当前原密码">
                  <n-input
                    v-model:value="pwdForm.old_password"
                    type="password"
                    show-password-on="click"
                    placeholder="请输入当前正在使用的密码"
                  />
                </n-form-item>
                
                <n-form-item label="设置新密码">
                  <n-input
                    v-model:value="pwdForm.new_password"
                    type="password"
                    show-password-on="click"
                    placeholder="至少 8 位，建议包含英文字母与数字"
                  />
                </n-form-item>

                <!-- 密码强度条 -->
                <div v-if="pwdForm.new_password" class="password-strength-bar">
                  <div class="strength-labels">
                    <span>密码安全强度：</span>
                    <span :class="passwordStrength.colorClass">{{ passwordStrength.text }}</span>
                  </div>
                  <div class="strength-track">
                    <div class="strength-fill" :style="{ width: passwordStrength.percent + '%', background: passwordStrength.color }"></div>
                  </div>
                </div>

                <n-form-item label="确认新密码">
                  <n-input
                    v-model:value="pwdForm.confirm_password"
                    type="password"
                    show-password-on="click"
                    placeholder="再次输入新密码以确认"
                  />
                </n-form-item>

                <n-button type="primary" :loading="changingPwd" @click="doChangePwd" style="margin-top: 8px;">
                  更新登录密码
                </n-button>
              </n-form>
            </div>

            <!-- 安全环境卡片 -->
            <div class="pane-section" style="margin-top:36px; border-top: 1px solid rgba(15, 23, 42, 0.06); padding-top: 24px;">
              <div class="section-heading">
                <div class="section-title">安全合规与会话</div>
                <div class="section-desc">当前设备的登录安全凭证与加密通道状态</div>
              </div>

              <div class="security-items-list">
                <div class="sec-item">
                  <div class="sec-item-icon safe">
                    <n-icon size="18"><ShieldCheckmarkOutline /></n-icon>
                  </div>
                  <div class="sec-item-content">
                    <div class="sec-item-title">JWT 隔离安全认证</div>
                    <div class="sec-item-sub">当前会话受企业级 Token 加密保护，支持多端登录防挤下</div>
                  </div>
                  <n-tag type="success" size="small" :bordered="false">安全中</n-tag>
                </div>

                <div class="sec-item">
                  <div class="sec-item-icon info">
                    <n-icon size="18"><KeyOutline /></n-icon>
                  </div>
                  <div class="sec-item-content">
                    <div class="sec-item-title">知识库数据企业专有加密</div>
                    <div class="sec-item-sub">您上传的产品文档与博主视频文本仅限当前租户隔离查询，绝不用作外部公共训练</div>
                  </div>
                  <n-tag type="info" size="small" :bordered="false">租户隔离</n-tag>
                </div>
              </div>
            </div>
          </div>
        </n-tab-pane>

        <!-- 标签 4: 订阅权益与用量分析 -->
        <n-tab-pane name="subscription" tab="订阅与算力权益">
          <div class="tab-card-body">
            <div class="pane-section">
              <div class="section-heading">
                <div class="section-title">当前订阅方案</div>
                <div class="section-desc">查看您的会员有效期限、专属特权与算力额度</div>
              </div>

              <div class="sub-plan-dashboard">
                <div class="plan-hero-card" :class="{ 'is-active': authStore.isSubscriptionActive }">
                  <div class="plan-card-top">
                    <div>
                      <div class="plan-badge-pill">{{ authStore.planLabel }}</div>
                      <div class="plan-big-title">文策引擎 · 专业创作者方案</div>
                    </div>
                    <n-button type="primary" @click="$router.push('/pricing')">
                      {{ authStore.isSubscriptionActive ? '立即续订' : '开通订阅' }}
                    </n-button>
                  </div>

                  <div class="plan-stats-row">
                    <div class="pstat-item">
                      <div class="pstat-num">{{ authStore.isSubscriptionActive ? (authStore.daysUntilExpiry < 1 ? authStore.hoursUntilExpiry + '小时' : authStore.daysUntilExpiry + '天') : '0天' }}</div>
                      <div class="pstat-lbl">剩余有效时长</div>
                    </div>
                    <div class="pstat-item">
                      <div class="pstat-num">无限次</div>
                      <div class="pstat-lbl">爆款选题生成额度</div>
                    </div>
                    <div class="pstat-item">
                      <div class="pstat-num">双核旗舰</div>
                      <div class="pstat-lbl">深度模型混合调度</div>
                    </div>
                  </div>
                </div>

                <!-- 专属特权检查清单 -->
                <div class="privileges-box">
                  <div class="priv-title">当前账户尊享特权：</div>
                  <div class="priv-grid">
                    <div class="priv-item" v-for="(p, i) in privilegeList" :key="i">
                      <n-icon color="#2563eb" size="16"><CheckmarkCircleOutline /></n-icon>
                      <span>{{ p }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </n-tab-pane>

        <!-- 标签 5: 快捷键速查与高效操作 -->
        <n-tab-pane name="shortcuts" tab="快捷操作速查">
          <div class="tab-card-body">
            <div class="pane-section">
              <div class="section-heading">
                <div class="section-title">键盘快捷键 (Keyboard Shortcuts)</div>
                <div class="section-desc">熟练使用快捷键可将日常脚本创作与素材调取效率提升 3 倍</div>
              </div>

              <div class="shortcuts-table">
                <div class="shortcut-row" v-for="(sc, i) in shortcutsList" :key="i">
                  <div class="sc-desc">{{ sc.desc }}</div>
                  <div class="sc-keys">
                    <kbd v-for="(k, j) in sc.keys" :key="j">{{ k }}</kbd>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </n-tab-pane>

      </n-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import {
  SparklesOutline, CameraOutline, MailOutline, CardOutline,
  CheckmarkOutline, CheckmarkCircleOutline, ShieldCheckmarkOutline, KeyOutline
} from '@vicons/ionicons5'
import { useAuthStore } from '../stores/auth.js'
import { authApi } from '../api/index.js'

const message = useMessage()
const authStore = useAuthStore()

const activeTab = ref('profile')
const savingProfile = ref(false)
const changingPwd = ref(false)

// 预设头像集
const presetAvatars = [
  { url: `data:image/svg+xml;charset=utf-8,${encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64"><rect width="64" height="64" rx="32" fill="#2563EB"/><text x="32" y="40" text-anchor="middle" font-family="system-ui" font-size="28" font-weight="bold" fill="white">文</text></svg>')}` },
  { url: `data:image/svg+xml;charset=utf-8,${encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64"><rect width="64" height="64" rx="32" fill="#7C3AED"/><text x="32" y="40" text-anchor="middle" font-family="system-ui" font-size="28" font-weight="bold" fill="white">策</text></svg>')}` },
  { url: `data:image/svg+xml;charset=utf-8,${encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64"><rect width="64" height="64" rx="32" fill="#059669"/><text x="32" y="40" text-anchor="middle" font-family="system-ui" font-size="28" font-weight="bold" fill="white">创</text></svg>')}` },
  { url: `data:image/svg+xml;charset=utf-8,${encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64"><rect width="64" height="64" rx="32" fill="#EA580C"/><text x="32" y="40" text-anchor="middle" font-family="system-ui" font-size="28" font-weight="bold" fill="white">星</text></svg>')}` },
  { url: `data:image/svg+xml;charset=utf-8,${encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64"><rect width="64" height="64" rx="32" fill="#0284C7"/><text x="32" y="40" text-anchor="middle" font-family="system-ui" font-size="28" font-weight="bold" fill="white">智</text></svg>')}` }
]

const selectedAvatarIdx = ref(0)
const currentAvatarUrl = computed(() => {
  return presetAvatars[selectedAvatarIdx.value]?.url || authStore.user?.avatar || presetAvatars[0].url
})

function choosePresetAvatar(idx) {
  selectedAvatarIdx.value = idx
}

// 创作者赛道标签
const contentTracks = [
  { id: 'tech', name: '3C 数码与前沿科技', icon: '💻' },
  { id: 'business', name: '商业思维与职场成长', icon: '📈' },
  { id: 'beauty', name: '美妆护肤与个护穿搭', icon: '✨' },
  { id: 'food', name: '美食探店与快手料理', icon: '🍳' },
  { id: 'knowledge', name: '人文科普与深度书评', icon: '📚' },
  { id: 'car', name: '汽车测评与自驾出行', icon: '🚗' },
  { id: 'mother', name: '母婴育儿与家庭生活', icon: '🍼' },
  { id: 'local', name: '同城探店与文旅休闲', icon: '📍' },
]

// 创作者名片状态
const userProfile = reactive({
  nickname: '',
  bio: '',
  selectedTracks: ['tech', 'business'],
})

function toggleTrack(id) {
  const index = userProfile.selectedTracks.indexOf(id)
  if (index > -1) {
    userProfile.selectedTracks.splice(index, 1)
  } else {
    userProfile.selectedTracks.push(id)
  }
}

// 创作偏好选项
const platforms = [
  { id: 'douyin', name: '抖音', color: '#111827', bg: '#f1f5f9', desc: '强黄金3秒钩子，视听节奏快' },
  { id: 'xiaohongshu', name: '小红书', color: '#dc2626', bg: '#fef2f2', desc: '首图吸睛吸金，真实种草体验感' },
  { id: 'weixin_video', name: '微信视频号', color: '#059669', bg: '#ecfdf5', desc: '社交裂变共鸣，注重信任与价值观' },
  { id: 'kuaishou', name: '快手', color: '#ea580c', bg: '#fff7ed', desc: '接地气烟火气，真实接地的人情味' },
]

const lengthOptions = [
  { id: 'short', title: '短口播速拍', words: '150 - 300 字', time: '约 30~50 秒' },
  { id: 'standard', title: '标准爆款篇幅', words: '400 - 650 字', time: '约 1~2 分钟' },
  { id: 'deep', title: '深度科普长文', words: '800 - 1200 字', time: '约 3~5 分钟' },
]

const toneOptions = [
  { id: 'authentic', name: '真人高情商网感', desc: '像真实闺蜜/哥们面对面聊天，无任何 AI 机械感' },
  { id: 'professional', name: '犀利行家视角', desc: '数据透彻、行业黑话精准、降维打击' },
  { id: 'storytelling', name: '叙事悬念流', desc: '以人物或突发意外开场，反转递进' },
  { id: 'enthusiastic', name: '热情种草带货', desc: '利益点密集、痛点直击，促成即时行动' },
]

// 偏好状态 (持久化到本地)
const userPref = reactive({
  defaultPlatform: 'douyin',
  defaultLength: 'standard',
  defaultStoryboardLevel: 'full',
  defaultTone: 'authentic',
})

// 修改密码状态
const pwdForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

// 密码强度计算
const passwordStrength = computed(() => {
  const p = pwdForm.new_password
  if (!p) return { percent: 0, text: '无', color: '#cbd5e1', colorClass: '' }
  let score = 0
  if (p.length >= 8) score += 30
  if (/[a-zA-Z]/.test(p)) score += 25
  if (/[0-9]/.test(p)) score += 25
  if (/[^a-zA-Z0-9]/.test(p)) score += 20

  if (score < 50) return { percent: 35, text: '较弱', color: '#ef4444', colorClass: 'text-error' }
  if (score < 80) return { percent: 70, text: '良好', color: '#f59e0b', colorClass: 'text-warning' }
  return { percent: 100, text: '强密码', color: '#10b981', colorClass: 'text-success' }
})

// 权益特权清单
const privilegeList = [
  '五维全景影视级分镜表输出 (景别 / 运镜 / 同期声 / 花字 / BGM)',
  '企业自研私有知识库 RAG 语义索引与防幻觉对齐',
  '短视频平台爆款对标博主风格模版克隆',
  '支持导出 Markdown、PDF、Word 及分镜提示词',
  '多维度实时公域热点选题推荐引擎'
]

// 快捷键列表
const shortcutsList = [
  { desc: '快速呼出全局命令面板与页面穿梭', keys: ['⌘', 'K'] },
  { desc: '在文案输入框中快速引用素材与知识库', keys: ['@'] },
  { desc: '提交并开始生成短视频脚本', keys: ['⌘ / Ctrl', 'Enter'] },
  { desc: '清空当前生成对话并开启新会话', keys: ['Alt', 'N'] },
  { desc: '一键复制当前生成的脚本全文', keys: ['⌘ / Ctrl', 'C'] },
]

onMounted(() => {
  // 恢复个人资料
  if (authStore.user) {
    userProfile.nickname = authStore.user.nickname || ''
  }
  // 恢复本地存储的偏好
  try {
    const saved = localStorage.getItem('cs_user_pref')
    if (saved) {
      Object.assign(userPref, JSON.parse(saved))
    }
    const savedProfile = localStorage.getItem('cs_user_profile_meta')
    if (savedProfile) {
      const parsed = JSON.parse(savedProfile)
      if (parsed.bio) userProfile.bio = parsed.bio
      if (parsed.selectedTracks) userProfile.selectedTracks = parsed.selectedTracks
      if (parsed.avatarIdx !== undefined) selectedAvatarIdx.value = parsed.avatarIdx
    }
  } catch {}
})

function saveProfile() {
  savingProfile.value = true
  setTimeout(() => {
    savingProfile.value = false
    try {
      localStorage.setItem('cs_user_profile_meta', JSON.stringify({
        bio: userProfile.bio,
        selectedTracks: userProfile.selectedTracks,
        avatarIdx: selectedAvatarIdx.value
      }))
      if (authStore.user) {
        authStore.user.nickname = userProfile.nickname
        authStore.user.avatar = currentAvatarUrl.value
        authStore.setUser({ ...authStore.user })
      }
      message.success('创作者名片已成功更新')
    } catch {
      message.error('保存失败，请稍后重试')
    }
  }, 400)
}

function resetProfile() {
  if (authStore.user) {
    userProfile.nickname = authStore.user.nickname || ''
  }
  userProfile.bio = ''
  userProfile.selectedTracks = ['tech', 'business']
  message.info('已重置为初始状态')
}

function savePreferences() {
  localStorage.setItem('cs_user_pref', JSON.stringify(userPref))
  message.success('创作习惯偏好已生效，进入文案生成时将自动套用')
}

function resetPreferences() {
  userPref.defaultPlatform = 'douyin'
  userPref.defaultLength = 'standard'
  userPref.defaultStoryboardLevel = 'full'
  userPref.defaultTone = 'authentic'
  localStorage.removeItem('cs_user_pref')
  message.info('已恢复为出厂推荐偏好')
}

async function doChangePwd() {
  if (!pwdForm.old_password) return message.warning('请输入当前密码')
  if (pwdForm.new_password.length < 8) return message.warning('新密码长度不能少于 8 位')
  if (pwdForm.new_password !== pwdForm.confirm_password) return message.warning('两次输入的新密码不一致')

  changingPwd.value = true
  try {
    await authApi.changePassword({
      old_password: pwdForm.old_password,
      new_password: pwdForm.new_password,
    })
    message.success('登录密码已修改成功，请牢记新密码')
    pwdForm.old_password = ''
    pwdForm.new_password = ''
    pwdForm.confirm_password = ''
  } catch (e) {
    message.error(e.response?.data?.detail || '修改失败，请确认原密码是否正确')
  } finally {
    changingPwd.value = false
  }
}
</script>

<style scoped>
.settings-page {
  max-width: 1080px;
  margin: 0 auto;
  padding-bottom: 48px;
}

/* 页面头部 */
.settings-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
}

.page-title {
  font-size: 22px;
  font-weight: 750;
  color: #0f172a;
  letter-spacing: -0.02em;
  margin: 0 0 6px;
}

.page-subtitle {
  font-size: 13.5px;
  color: #64748b;
  margin: 0;
}

/* 用户英雄概览卡片 (Profile Hero Strip) */
.profile-hero-card {
  background: #ffffff;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 16px;
  padding: 24px 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
  margin-bottom: 28px;
}

.profile-hero-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.avatar-container {
  position: relative;
  flex-shrink: 0;
}

.hero-avatar {
  border: 2px solid #ffffff;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
}

.avatar-edit-badge {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #2563eb;
  color: #ffffff;
  border: 2px solid #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.15s ease;
}

.avatar-edit-badge:hover {
  transform: scale(1.1);
}

.profile-hero-meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.hero-name-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.hero-user-name {
  font-size: 18px;
  font-weight: 750;
  color: #0f172a;
}

.user-role-badge {
  font-size: 12px;
  color: #64748b;
  background: #f1f5f9;
  padding: 2px 8px;
  border-radius: 6px;
}

.hero-account-email {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #64748b;
}

.email-icon {
  color: #94a3b8;
}

.meta-dot {
  color: #cbd5e1;
}

.highlight-days {
  color: #2563eb;
  font-weight: 700;
}

.expired-text {
  color: #dc2626;
  font-weight: 600;
}

/* 标签页主体容器 */
.settings-content-shell {
  background: #ffffff;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
  overflow: hidden;
}

.settings-tabs :deep(.n-tabs-nav) {
  padding: 8px 24px 0;
  background: #f8fafc;
  border-bottom: 1px solid rgba(15, 23, 42, 0.06);
}

.tab-card-body {
  padding: 28px 32px;
}

.section-heading {
  margin-bottom: 24px;
}

.section-title {
  font-size: 16px;
  font-weight: 750;
  color: #0f172a;
  margin-bottom: 4px;
}

.section-desc {
  font-size: 13px;
  color: #64748b;
}

/* 头像挑选器 */
.avatar-picker-row {
  margin-bottom: 24px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid rgba(15, 23, 42, 0.06);
}

.picker-label {
  font-size: 13px;
  font-weight: 600;
  color: #334155;
  margin-bottom: 12px;
}

.preset-avatars-list {
  display: flex;
  align-items: center;
  gap: 16px;
}

.avatar-option-item {
  position: relative;
  cursor: pointer;
  border-radius: 50%;
  padding: 2px;
  border: 2px solid transparent;
  transition: all 0.2s ease;
}

.avatar-option-item:hover {
  transform: translateY(-2px);
}

.avatar-option-item.selected {
  border-color: #2563eb;
}

.avatar-check-badge {
  position: absolute;
  top: -2px;
  right: -2px;
  background: #2563eb;
  color: #ffffff;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid #ffffff;
}

/* 表单布局 */
.form-grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.tracks-selector {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  width: 100%;
}

.track-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  background: #f8fafc;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 8px;
  font-size: 13px;
  color: #475569;
  cursor: pointer;
  user-select: none;
  transition: all 0.2s ease;
}

.track-chip:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
}

.track-chip.active {
  background: #eff6ff;
  border-color: #93c5fd;
  color: #1d4ed8;
  font-weight: 600;
}

.form-action-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 20px;
}

/* 偏好设置卡片 */
.pref-options-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.pref-card {
  background: #f8fafc;
  border: 1px solid rgba(15, 23, 42, 0.06);
  border-radius: 12px;
  padding: 18px 20px;
}

.pref-card-header {
  margin-bottom: 14px;
}

.pref-title {
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
}

.pref-sub {
  font-size: 12.5px;
  color: #64748b;
  margin-top: 2px;
}

.platform-cards-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.platform-select-card {
  background: #ffffff;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 10px;
  padding: 12px 14px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.platform-select-card:hover {
  border-color: #94a3b8;
}

.platform-select-card.selected {
  border-color: #2563eb;
  background: #f0f7ff;
  box-shadow: 0 0 0 1px #2563eb;
}

.plat-badge {
  font-size: 12px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
  width: fit-content;
}

.plat-desc {
  font-size: 12px;
  color: #64748b;
  line-height: 1.4;
}

.length-options-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.length-select-card {
  background: #ffffff;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 10px;
  padding: 14px 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: center;
}

.length-select-card:hover {
  border-color: #94a3b8;
}

.length-select-card.selected {
  border-color: #2563eb;
  background: #f0f7ff;
  box-shadow: 0 0 0 1px #2563eb;
}

.len-title {
  font-size: 13.5px;
  font-weight: 700;
  color: #0f172a;
}

.len-range {
  font-size: 12.5px;
  color: #2563eb;
  font-weight: 600;
  margin: 4px 0 2px;
}

.len-time {
  font-size: 11.5px;
  color: #94a3b8;
}

.tone-chips-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.tone-chip {
  background: #ffffff;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 10px;
  padding: 12px 14px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tone-chip:hover {
  border-color: #94a3b8;
}

.tone-chip.active {
  border-color: #2563eb;
  background: #f0f7ff;
  box-shadow: 0 0 0 1px #2563eb;
}

.tone-name {
  font-size: 13.5px;
  font-weight: 700;
  color: #0f172a;
}

.tone-desc {
  font-size: 12px;
  color: #64748b;
  line-height: 1.45;
}

/* 密码强度条 */
.password-strength-bar {
  margin-bottom: 16px;
}

.strength-labels {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  color: #64748b;
  margin-bottom: 4px;
}

.text-error { color: #ef4444; font-weight: 600; }
.text-warning { color: #f59e0b; font-weight: 600; }
.text-success { color: #10b981; font-weight: 600; }

.strength-track {
  height: 5px;
  background: #f1f5f9;
  border-radius: 9999px;
  overflow: hidden;
}

.strength-fill {
  height: 100%;
  transition: all 0.3s ease;
}

/* 安全列表 */
.security-items-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.sec-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 18px;
  background: #f8fafc;
  border: 1px solid rgba(15, 23, 42, 0.06);
  border-radius: 12px;
}

.sec-item-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.sec-item-icon.safe {
  background: #ecfdf5;
  color: #059669;
}

.sec-item-icon.info {
  background: #eff6ff;
  color: #2563eb;
}

.sec-item-content {
  flex: 1;
}

.sec-item-title {
  font-size: 13.5px;
  font-weight: 700;
  color: #0f172a;
}

.sec-item-sub {
  font-size: 12px;
  color: #64748b;
}

/* 订阅仪表板 */
.sub-plan-dashboard {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.plan-hero-card {
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  border-radius: 16px;
  padding: 28px 32px;
  color: #ffffff;
}

.plan-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 24px;
}

.plan-badge-pill {
  display: inline-block;
  font-size: 12px;
  font-weight: 700;
  background: rgba(37, 99, 235, 0.4);
  color: #60a5fa;
  padding: 3px 10px;
  border-radius: 9999px;
  margin-bottom: 8px;
  border: 1px solid rgba(96, 165, 250, 0.3);
}

.plan-big-title {
  font-size: 20px;
  font-weight: 750;
  letter-spacing: -0.01em;
}

.plan-stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.12);
}

.pstat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.pstat-num {
  font-size: 22px;
  font-weight: 800;
  color: #38bdf8;
}

.pstat-lbl {
  font-size: 12px;
  color: #94a3b8;
}

.privileges-box {
  background: #f8fafc;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 14px;
  padding: 20px 24px;
}

.priv-title {
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 14px;
}

.priv-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.priv-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #334155;
}

/* 快捷键表格 */
.shortcuts-table {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.shortcut-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 18px;
  background: #f8fafc;
  border-radius: 10px;
  border: 1px solid rgba(15, 23, 42, 0.06);
}

.sc-desc {
  font-size: 13.5px;
  color: #334155;
  font-weight: 500;
}

.sc-keys {
  display: flex;
  align-items: center;
  gap: 6px;
}

kbd {
  display: inline-block;
  padding: 3px 8px;
  font-size: 12px;
  font-family: inherit;
  font-weight: 600;
  color: #1e293b;
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-bottom-width: 2px;
  border-radius: 6px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

@media (max-width: 768px) {
  .profile-hero-card {
    flex-direction: column;
    align-items: flex-start;
  }
  .form-grid-2 {
    grid-template-columns: 1fr;
  }
  .platform-cards-row {
    grid-template-columns: 1fr 1fr;
  }
  .length-options-row {
    grid-template-columns: 1fr;
  }
  .tone-chips-grid {
    grid-template-columns: 1fr;
  }
  .plan-stats-row {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  .priv-grid {
    grid-template-columns: 1fr;
  }
  .tab-card-body {
    padding: 20px 16px;
  }
}
</style>
