<template>
  <div class="landing-page">
    <div class="hero-backdrop hero-backdrop-left"></div>
    <div class="hero-backdrop hero-backdrop-right"></div>

    <section class="hero-shell">
      <header class="topbar">
        <div class="brand-lockup">
          <div class="brand-icon">
            <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <polygon points="23 7 16 12 23 17 23 7" />
              <rect x="1" y="5" width="15" height="14" rx="2" ry="2" />
            </svg>
          </div>
          <div>
            <div class="brand-name">文策引擎</div>
            <div class="brand-subtitle">AI 内容创作工作台</div>
          </div>
        </div>

        <div class="topbar-actions">
          <n-button quaternary class="ghost-btn" @click="router.push('/login')">登录</n-button>
          <n-button type="primary" class="cta-btn" @click="router.push('/app')">进入工作台</n-button>
        </div>
      </header>

      <div class="hero-grid">
        <div class="hero-copy">
          <div class="eyebrow">
            <span class="eyebrow-dot"></span>
            站点在线，备案处理中
          </div>

          <h1 class="headline">
            从选题到脚本，
            <br />
            一站式完成短视频内容生产
          </h1>

          <p class="hero-text">
            围绕爆款风格学习、产品知识库检索和内容批量生成，帮助团队更快产出可直接进入拍摄流程的文案。
          </p>

          <div class="hero-actions">
            <n-button type="primary" size="large" class="primary-action" @click="router.push('/login')">
              立即登录
            </n-button>
            <n-button size="large" class="secondary-action" @click="router.push('/app')">
              直接进入
            </n-button>
          </div>

          <div class="signal-row">
            <div class="signal-card" v-for="item in stats" :key="item.label">
              <div class="signal-value">{{ item.value }}</div>
              <div class="signal-label">{{ item.label }}</div>
            </div>
          </div>
        </div>

        <div class="hero-panel">
          <div class="panel-frame">
            <div class="panel-header">
              <div>
                <div class="panel-kicker">工作流概览</div>
                <div class="panel-title">内容生产链路</div>
              </div>
              <div class="panel-status">在线</div>
            </div>

            <div class="workflow-list">
              <div class="workflow-item" v-for="item in workflows" :key="item.title">
                <div class="workflow-icon">
                  <n-icon size="18">
                    <component :is="item.icon" />
                  </n-icon>
                </div>
                <div class="workflow-copy">
                  <div class="workflow-title">{{ item.title }}</div>
                  <div class="workflow-desc">{{ item.desc }}</div>
                </div>
              </div>
            </div>

            <div class="panel-note">
              当前首页已可访问。若部分地区首次访问偶发失败，通常与外部链路策略有关，不影响站点本身已在线。
            </div>
          </div>
        </div>
      </div>

      <section class="feature-band">
        <div class="feature-card" v-for="item in features" :key="item.title">
          <div class="feature-icon">
            <n-icon size="18">
              <component :is="item.icon" />
            </n-icon>
          </div>
          <div class="feature-title">{{ item.title }}</div>
          <div class="feature-desc">{{ item.desc }}</div>
        </div>
      </section>
    </section>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import {
  SparklesOutline,
  FlameOutline,
  CubeOutline,
  CalendarOutline,
  TrendingUpOutline,
  PeopleOutline,
} from '@vicons/ionicons5'

const router = useRouter()

const stats = [
  { value: '多平台', label: '爆款选题分析' },
  { value: 'RAG', label: '产品知识植入' },
  { value: '脚本级', label: '文案成稿输出' },
]

const workflows = [
  { icon: TrendingUpOutline, title: '选题发现', desc: '从近期热点和高表现内容里快速筛出可用方向。' },
  { icon: PeopleOutline, title: '风格学习', desc: '沉淀头部博主表达方式，统一团队输出口径。' },
  { icon: CubeOutline, title: '知识库调用', desc: '把产品卖点、FAQ 和素材自动融入脚本。' },
  { icon: CalendarOutline, title: '排期落地', desc: '生成结果可继续进入排期和团队协同流程。' },
]

const features = [
  { icon: FlameOutline, title: '爆款逻辑拆解', desc: '把高转化内容的结构、开头钩子和情绪节奏沉淀成可复用模板。' },
  { icon: SparklesOutline, title: '完整文案输出', desc: '支持标题、开场、口播、镜头节奏和 CTA 的成套生成。' },
  { icon: CubeOutline, title: '产品信息对齐', desc: '围绕你的业务资料和产品知识库生成更贴近真实销售场景的脚本。' },
]
</script>

<style scoped>
.landing-page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background:
    radial-gradient(circle at top left, rgba(34, 211, 238, 0.18), transparent 26%),
    radial-gradient(circle at 85% 15%, rgba(14, 165, 233, 0.18), transparent 24%),
    linear-gradient(180deg, #f4fbff 0%, #eef7fb 48%, #f8fbfd 100%);
}

.hero-backdrop {
  position: absolute;
  border-radius: 9999px;
  filter: blur(8px);
  pointer-events: none;
}

.hero-backdrop-left {
  width: 420px;
  height: 420px;
  top: -120px;
  left: -80px;
  background: rgba(34, 211, 238, 0.16);
}

.hero-backdrop-right {
  width: 360px;
  height: 360px;
  right: -100px;
  top: 180px;
  background: rgba(8, 145, 178, 0.12);
}

.hero-shell {
  position: relative;
  z-index: 1;
  width: min(1200px, calc(100% - 32px));
  margin: 0 auto;
  padding: 24px 0 40px;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 6px 0 24px;
}

.brand-lockup {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-icon {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  background: linear-gradient(135deg, #0891b2 0%, #0f766e 100%);
  box-shadow: 0 12px 22px rgba(8, 145, 178, 0.22);
}

.brand-name {
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
}

.brand-subtitle {
  margin-top: 3px;
  font-size: 12px;
  color: #64748b;
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ghost-btn {
  color: #0f172a;
}

.cta-btn,
.primary-action {
  min-width: 126px;
}

.hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(360px, 0.95fr);
  gap: 24px;
  align-items: stretch;
}

.hero-copy,
.hero-panel {
  min-width: 0;
}

.hero-copy {
  padding: 36px 10px 12px 0;
}

.eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(125, 211, 252, 0.7);
  color: #0f766e;
  font-size: 13px;
  font-weight: 600;
}

.eyebrow-dot {
  width: 8px;
  height: 8px;
  border-radius: 9999px;
  background: #10b981;
  box-shadow: 0 0 0 6px rgba(16, 185, 129, 0.12);
}

.headline {
  margin: 24px 0 16px;
  font-size: clamp(34px, 5vw, 60px);
  line-height: 1.04;
  letter-spacing: 0;
  color: #0f172a;
}

.hero-text {
  max-width: 650px;
  margin: 0;
  font-size: 16px;
  line-height: 1.8;
  color: #475569;
}

.hero-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 28px;
}

.secondary-action {
  min-width: 118px;
  background: rgba(255, 255, 255, 0.84);
  border-color: #cbd5e1;
}

.signal-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-top: 28px;
}

.signal-card {
  min-height: 96px;
  padding: 18px 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(203, 213, 225, 0.76);
  box-shadow: 0 18px 30px rgba(148, 163, 184, 0.08);
}

.signal-value {
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
}

.signal-label {
  margin-top: 6px;
  font-size: 13px;
  line-height: 1.5;
  color: #64748b;
}

.hero-panel {
  display: flex;
  align-items: stretch;
}

.panel-frame {
  width: 100%;
  padding: 26px;
  border-radius: 26px;
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.94) 0%, rgba(14, 116, 144, 0.92) 100%);
  color: #e2f7fb;
  box-shadow: 0 30px 60px rgba(15, 23, 42, 0.2);
}

.panel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.panel-kicker {
  font-size: 12px;
  color: rgba(226, 247, 251, 0.72);
}

.panel-title {
  margin-top: 6px;
  font-size: 24px;
  font-weight: 700;
  color: #ffffff;
}

.panel-status {
  flex-shrink: 0;
  padding: 7px 12px;
  border-radius: 9999px;
  background: rgba(52, 211, 153, 0.16);
  border: 1px solid rgba(134, 239, 172, 0.35);
  color: #bbf7d0;
  font-size: 12px;
  font-weight: 700;
}

.workflow-list {
  display: grid;
  gap: 14px;
  margin-top: 24px;
}

.workflow-item {
  display: grid;
  grid-template-columns: 46px minmax(0, 1fr);
  gap: 12px;
  align-items: start;
  padding: 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(226, 247, 251, 0.08);
}

.workflow-icon {
  width: 46px;
  height: 46px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.12);
  color: #ffffff;
}

.workflow-copy {
  min-width: 0;
}

.workflow-title {
  font-size: 15px;
  font-weight: 700;
  color: #ffffff;
}

.workflow-desc {
  margin-top: 5px;
  font-size: 13px;
  line-height: 1.65;
  color: rgba(226, 247, 251, 0.78);
}

.panel-note {
  margin-top: 18px;
  padding-top: 18px;
  border-top: 1px solid rgba(226, 247, 251, 0.14);
  font-size: 13px;
  line-height: 1.75;
  color: rgba(226, 247, 251, 0.72);
}

.feature-band {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-top: 26px;
}

.feature-card {
  min-height: 176px;
  padding: 22px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.84);
  border: 1px solid rgba(203, 213, 225, 0.72);
  box-shadow: 0 16px 28px rgba(148, 163, 184, 0.08);
}

.feature-icon {
  width: 42px;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  color: #0f766e;
  background: linear-gradient(135deg, rgba(34, 211, 238, 0.2) 0%, rgba(20, 184, 166, 0.18) 100%);
}

.feature-title {
  margin-top: 16px;
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}

.feature-desc {
  margin-top: 8px;
  font-size: 14px;
  line-height: 1.75;
  color: #475569;
}

@media (max-width: 1024px) {
  .hero-grid {
    grid-template-columns: 1fr;
  }

  .hero-copy {
    padding-right: 0;
  }
}

@media (max-width: 768px) {
  .hero-shell {
    width: min(100% - 24px, 1200px);
    padding-top: 18px;
    padding-bottom: 28px;
  }

  .topbar {
    flex-direction: column;
    align-items: flex-start;
  }

  .topbar-actions {
    width: 100%;
  }

  .ghost-btn,
  .cta-btn {
    flex: 1;
  }

  .signal-row,
  .feature-band {
    grid-template-columns: 1fr;
  }

  .panel-frame {
    padding: 22px 18px;
    border-radius: 22px;
  }
}

@media (max-width: 480px) {
  .headline {
    font-size: 32px;
  }

  .hero-text {
    font-size: 15px;
  }

  .hero-actions {
    flex-direction: column;
  }

  .primary-action,
  .secondary-action {
    width: 100%;
  }
}
</style>
