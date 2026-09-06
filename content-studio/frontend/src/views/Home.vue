<template>
  <div class="home-wrapper" id="home-top">
    <!-- 顶部常驻导航栏 -->
    <header class="site-header" :class="{ 'scrolled': isScrolled }">
      <!-- 滚动进度条 (CSS-based smooth scroll indicator) -->
      <div class="scroll-progress-bar" :style="{ width: `${scrollProgress}%` }"></div>

      <div class="header-inner">
        <!-- 品牌标识 -->
        <div class="brand-group" @click="scrollToTop" role="button" tabindex="0" title="回到顶部">
          <div class="brand-logo-badge">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <polygon points="23 7 16 12 23 17 23 7" />
              <rect x="1" y="5" width="15" height="14" rx="2" ry="2" />
            </svg>
          </div>
          <div class="brand-text">
            <span class="brand-title">文策引擎</span>
            <span class="brand-subtitle">AI短视频生产力中台</span>
          </div>
        </div>

        <!-- 锚点导航 (平滑滚动跳转) -->
        <nav class="header-nav">
          <a href="#workspace-demo" class="nav-item" @click.prevent="scrollToSection('workspace-demo')">工作台演练</a>
          <a href="#core-capabilities" class="nav-item" @click.prevent="scrollToSection('core-capabilities')">核心能力</a>
          <a href="#matrix-modules" class="nav-item" @click.prevent="scrollToSection('matrix-modules')">功能矩阵</a>
          <a href="#social-proof" class="nav-item" @click.prevent="scrollToSection('social-proof')">创作者口碑</a>
          <a href="#faq" class="nav-item" @click.prevent="scrollToSection('faq')">常见问题</a>
        </nav>

        <!-- 头部操作区 -->
        <div class="header-actions">
          <template v-if="authStore.isAuthenticated">
            <div class="user-pill" @click="navigateTo('/generate')" title="进入个人工作台">
              <n-avatar round size="small" :src="authStore.user?.avatar || defaultAvatar" />
              <span class="user-nickname">{{ authStore.user?.nickname || '创作者' }}</span>
              <span class="plan-badge">{{ authStore.planLabel }}</span>
            </div>
            <n-button type="primary" class="primary-action-btn pulse-on-hover" @click="navigateTo('/generate')">
              进入工作台
              <template #icon>
                <n-icon><ArrowForwardOutline /></n-icon>
              </template>
            </n-button>
            <n-button quaternary size="small" @click="handleLogout">
              退出
            </n-button>
          </template>

          <template v-else>
            <n-button quaternary class="login-link-btn" @click="navigateTo('/login')">
              账号登录
            </n-button>
            <n-button type="primary" secondary class="demo-login-btn" @click="handleDemoLogin" :loading="demoLoading">
              免登录极速体验
            </n-button>
            <n-button type="primary" class="primary-action-btn pulse-on-hover" @click="navigateTo('/generate')">
              进入工作台
              <template #icon>
                <n-icon><ArrowForwardOutline /></n-icon>
              </template>
            </n-button>
          </template>
        </div>
      </div>
    </header>

    <!-- 主视觉 Hero 区域 (高冲击力、鲜明价值主张与现代版式设计) -->
    <section class="hero-container">
      <!-- 动态环境柔光与精细微网格背景 -->
      <div class="hero-grid-pattern"></div>
      <div class="hero-ambient-glow"></div>

      <div class="hero-inner">
        <!-- 顶部眉毛标签 / 类别标识 -->
        <div class="hero-chip animate-fade-down" @click="scrollToSection('workspace-demo')">
          <span class="chip-status-dot"></span>
          <span class="chip-label">文策引擎 2.0 · AI 短视频内容生产力中台</span>
          <span class="chip-divider"></span>
          <span class="chip-action">深度解构博主骨架 →</span>
        </div>

        <!-- 现代版式核心主标题 (Display Typography Hierarchy) -->
        <h1 class="hero-heading animate-fade-up-1">
          解构头部博主表达骨架<br />
          <span class="hero-heading-gradient">重塑短视频完播率与转化生产力</span>
        </h1>

        <!-- 价值主张说明段落 (Clear, Direct Value Proposition) -->
        <p class="hero-description animate-fade-up-2">
          摆脱通用大模型的泛化套话与书面腔。文策引擎将<strong>百万爆款选题雷达</strong>、<strong>标杆博主语感模型</strong>与<strong>企业专属产品知识库</strong>深度交融，通过独创即梦式 @素材 自由串联，秒级交付带黄金3秒钩子与机位拍摄分镜的高转化脚本。
        </p>

        <!-- 行动号召 CTA 核心操作区 (High-Impact Action Triggers) -->
        <div class="hero-cta-group animate-fade-up-3">
          <div class="hero-button-row">
            <n-button type="primary" size="large" class="hero-primary-action btn-hover-lift" @click="navigateTo('/generate')">
              <template #icon>
                <n-icon><SparklesOutline /></n-icon>
              </template>
              免费开启高完播创作
              <template #arrow>
                <n-icon class="btn-arrow-right"><ArrowForwardOutline /></n-icon>
              </template>
            </n-button>

            <n-button size="large" class="hero-demo-action btn-hover-lift" @click="handleDemoLogin" :loading="demoLoading">
              <template #icon>
                <n-icon><PlayOutline /></n-icon>
              </template>
              免登录体验演示空间
            </n-button>

            <n-button size="large" quaternary class="hero-scroll-action" @click="scrollToSection('workspace-demo')">
              查看在线工作台演练 ↓
            </n-button>
          </div>

          <!-- 信任背书与免责承诺小字 -->
          <div class="hero-reassurance-row">
            <span class="reassurance-item"><span class="check-icon">✓</span> 零配置极速开箱即用</span>
            <span class="reassurance-dot">·</span>
            <span class="reassurance-item"><span class="check-icon">✓</span> 即梦式 @素材 自由组装</span>
            <span class="reassurance-dot">·</span>
            <span class="reassurance-item"><span class="check-icon">✓</span> 覆盖抖音/小红书/视频号生态</span>
          </div>
        </div>

        <!-- 现代版式设计：核心价值对比与指标看板 (Typographic Contrast Proof) -->
        <div class="hero-typography-showcase animate-fade-up-4">
          <!-- 对比卡片：传统大模型 vs 文策引擎 -->
          <div class="typography-comparison-card">
            <div class="comparison-side side-generic">
              <div class="side-header">
                <span class="side-tag tag-bad">传统通用大模型</span>
                <span class="side-metric bad">平均完播率 ~12%</span>
              </div>
              <p class="sample-quote generic">
                “大家好，今天我们来为大家介绍一款高品质降噪耳机。这款耳机采用了非常优秀的技术和高端材料制造，外观时尚轻便，非常适合日常通勤和办公使用，建议大家购买...”
              </p>
              <div class="side-verdict bad">
                <span>× 句式平铺直叙，浓厚书面腔</span>
                <span>× 前3秒无情绪抓手直接划走</span>
              </div>
            </div>

            <div class="comparison-divider-line">
              <div class="vs-circle">VS</div>
            </div>

            <div class="comparison-side side-wence">
              <div class="side-header">
                <span class="side-tag tag-good">文策引擎 · 博主解构+知识库</span>
                <span class="side-metric good">完播预测 95.8% · 爆款潜力</span>
              </div>
              <p class="sample-quote wence">
                <span class="shot-inline-note">【画面：博主拿两副耳机重重摔在桌面上】</span><br />
                “千万别再盲目买降噪耳机了！如果预算在一千以内，听我一句劝，先停下付款动作花60秒看完！90%的人只盯45dB深度，戴半小时耳朵胀痛得想吐...”
              </p>
              <div class="side-verdict good">
                <span>✓ 黄金3秒反常识冲突立论</span>
                <span>✓ 口语化情绪饱满，带镜头执行表</span>
              </div>
            </div>
          </div>

          <!-- 4 维关键价值指标 (Typography-Focused Value Metrics) -->
          <div class="hero-metrics-strip">
            <div class="metric-pillar">
              <span class="metric-stat-num">89.4<span class="metric-unit">%</span></span>
              <span class="metric-stat-label">黄金前3秒停留率提升</span>
              <span class="metric-stat-sub">突破算法推荐冷启动门槛</span>
            </div>
            <div class="metric-pillar-divider"></div>
            <div class="metric-pillar">
              <span class="metric-stat-num">10<span class="metric-unit">倍+</span></span>
              <span class="metric-stat-label">脚本与分镜交付提效</span>
              <span class="metric-stat-sub">从选题到拍摄成稿仅需秒级</span>
            </div>
            <div class="metric-pillar-divider"></div>
            <div class="metric-pillar">
              <span class="metric-stat-num">100<span class="metric-unit">%</span></span>
              <span class="metric-stat-label">企业知识库卖点对齐</span>
              <span class="metric-stat-sub">杜绝大模型臆造与事实错误</span>
            </div>
            <div class="metric-pillar-divider"></div>
            <div class="metric-pillar">
              <span class="metric-stat-num">0<span class="metric-unit">门槛</span></span>
              <span class="metric-stat-label">即梦式 @素材 自由组装</span>
              <span class="metric-stat-sub">像搭积木一样串联博主与观点</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 在线工作台实时演练 (Interactive Content Studio Canvas) -->
    <section id="workspace-demo" class="studio-demo-section">
      <div class="content-container">
        <div class="section-lead scroll-reveal">
          <div class="section-badge">INTERACTIVE WORKBENCH</div>
          <h2 class="section-title">创作工作台在线演练</h2>
          <p class="section-subtitle">切换不同赛道与对标博主，体验 @引用 组装机制与实时推演生成全流程</p>
        </div>

        <!-- 赛道场景切换 Tabs -->
        <div class="scenario-tabs scroll-reveal reveal-delay-1">
          <button
            v-for="s in scenarios"
            :key="s.id"
            class="scenario-tab-btn"
            :class="{ active: currentScenario.id === s.id }"
            @click="switchScenario(s)"
          >
            <span class="tab-icon">{{ s.icon }}</span>
            <span class="tab-label">{{ s.label }}</span>
          </button>
        </div>

        <!-- 演练工作台卡片画布 (支持平滑进入动效) -->
        <div class="workbench-canvas scroll-reveal reveal-scale reveal-delay-2">
          <!-- 左侧配置区 -->
          <div class="canvas-controls">
            <div class="control-header">
              <span class="control-header-title">创作参数配置</span>
              <span class="control-header-badge">即梦式 @引用 架构</span>
            </div>

            <!-- 选题配置 -->
            <div class="control-group">
              <label class="control-label">短视频核心选题</label>
              <div class="topic-presets">
                <button
                  v-for="t in currentScenario.topics"
                  :key="t"
                  class="preset-topic-pill"
                  :class="{ active: selectedTopic === t }"
                  @click="selectTopic(t)"
                >
                  <span class="topic-indicator"></span>
                  <span class="topic-text">{{ t }}</span>
                </button>
              </div>
            </div>

            <!-- 发布平台 -->
            <div class="control-group">
              <label class="control-label">发布目标平台</label>
              <div class="platform-selector">
                <button
                  v-for="p in platformOptions"
                  :key="p.id"
                  class="platform-card-btn"
                  :class="{ active: selectedPlatform === p.id }"
                  @click="selectedPlatform = p.id"
                >
                  <span class="platform-name">{{ p.name }}</span>
                  <span class="platform-style-tag">{{ p.styleTag }}</span>
                </button>
              </div>
            </div>

            <!-- 对标博主风格 -->
            <div class="control-group">
              <label class="control-label">对标博主风格模版</label>
              <div class="creator-selector">
                <button
                  v-for="c in currentScenario.creators"
                  :key="c.name"
                  class="creator-card-btn"
                  :class="{ active: selectedCreator.name === c.name }"
                  @click="selectCreator(c)"
                >
                  <div class="creator-card-top">
                    <span class="creator-name">{{ c.name }}</span>
                    <span class="creator-tag">{{ c.tag }}</span>
                  </div>
                  <span class="creator-desc">{{ c.desc }}</span>
                </button>
              </div>
            </div>

            <!-- 即梦式 @引用 实时预览 -->
            <div class="control-group">
              <label class="control-label">即梦式 @素材 组装栏</label>
              <div class="mention-bar-preview">
                <span class="mention-token token-creator">@博主:{{ selectedCreator.name }}</span>
                <span class="mention-token token-doc">@知识库:{{ currentScenario.docName }}</span>
                <span class="mention-token token-viewpoint">@观点:{{ currentScenario.viewpointTag }}</span>
              </div>
            </div>

            <!-- 触发生成按钮 -->
            <div class="control-action">
              <n-button
                type="primary"
                block
                size="large"
                class="generate-action-btn"
                :loading="isGenerating"
                @click="runSimulation"
              >
                <template #icon>
                  <n-icon><SparklesOutline /></n-icon>
                </template>
                {{ isGenerating ? 'AI 正在极速推演分镜...' : '立即运行 AI 生成脚本' }}
              </n-button>
            </div>
          </div>

          <!-- 右侧内容生成主画布 -->
          <div class="canvas-editor">
            <!-- 头部信息状态栏 -->
            <div class="editor-topbar">
              <div class="topbar-meta">
                <span class="meta-status-dot" :class="{ 'pulsing': isGenerating }"></span>
                <span class="meta-title">{{ isGenerating ? simulationStageText : '结构化短视频脚本文档' }}</span>
                <span class="meta-score-pill">完播潜力预测 95.4 分</span>
              </div>

              <div class="editor-actions">
                <n-button size="small" secondary @click="copyScriptContent" class="copy-btn">
                  <template #icon>
                    <n-icon v-if="copied" color="#10b981"><CheckmarkOutline /></n-icon>
                    <n-icon v-else><CopyOutline /></n-icon>
                  </template>
                  {{ copied ? '已复制 ✓' : '复制全文' }}
                </n-button>
                <n-button size="small" type="primary" @click="navigateTo('/generate')">
                  进入完整工作台
                </n-button>
              </div>
            </div>

            <!-- 生成过程中的动态光波扫描条 -->
            <div v-if="isGenerating" class="generating-beam-wrapper">
              <div class="generating-beam"></div>
              <div class="generating-status-box">
                <div class="generating-spinner"></div>
                <span>{{ simulationStageText }}</span>
              </div>
            </div>

            <!-- 脚本正文内容展示区 (带有平滑淡入动效) -->
            <div class="script-document" :key="scriptKey" :class="{ 'blur-during-gen': isGenerating }">
              <!-- 标题行 -->
              <div class="script-title-row animate-card-1">
                <span class="platform-badge-tag">{{ selectedPlatformName }}</span>
                <h3 class="script-headline">{{ currentScript.title }}</h3>
              </div>

              <!-- 模块 1: 黄金3秒钩子 -->
              <div class="script-block hook-block animate-card-2">
                <div class="block-header">
                  <span class="block-label">01 黄金前3秒吸睛钩子 (Hook)</span>
                  <span class="block-hint">前视听觉冲击 · 完播率核心</span>
                </div>
                <div class="block-body">
                  <p class="visual-note">【画面分镜】{{ currentScript.hookVisual }}</p>
                  <p class="spoken-text">【口播台词】“{{ currentScript.hookSpoken }}”</p>
                </div>
              </div>

              <!-- 模块 2: 认知冲突与痛点唤醒 -->
              <div class="script-block conflict-block animate-card-3">
                <div class="block-header">
                  <span class="block-label">02 痛点唤醒与反常识立论 (Conflict)</span>
                  <span class="block-hint">制造认知落差 · 引发受众停留</span>
                </div>
                <div class="block-body">
                  <p class="spoken-text">{{ currentScript.conflictText }}</p>
                </div>
              </div>

              <!-- 模块 3: 核心干货与产品卖点 -->
              <div class="script-block solution-block animate-card-4">
                <div class="block-header">
                  <span class="block-label">03 核心干货与知识库卖点 (Solution)</span>
                  <span class="block-hint">对齐企业知识库 · 科学逻辑赋能</span>
                </div>
                <div class="block-body">
                  <p class="spoken-text">{{ currentScript.solutionText }}</p>
                </div>
              </div>

              <!-- 模块 4: 行动号召与互动指令 -->
              <div class="script-block cta-block animate-card-5">
                <div class="block-header">
                  <span class="block-label">04 强互动与行动号召 (CTA)</span>
                  <span class="block-hint">撬动转评赞 · 算法推荐加权</span>
                </div>
                <div class="block-body">
                  <p class="spoken-text">{{ currentScript.ctaText }}</p>
                </div>
              </div>

              <!-- 模块 5: 运镜与分镜执行表 -->
              <div class="script-block storyboard-block animate-card-6">
                <div class="block-header">
                  <span class="block-label">05 镜头拍摄分镜指南 (Storyboard)</span>
                  <span class="block-hint">直接交付拍摄与剪辑团队</span>
                </div>
                <div class="storyboard-grid">
                  <div class="shot-card" v-for="(shot, idx) in currentScript.shots" :key="idx">
                    <span class="shot-idx">镜头 {{ idx + 1 }}</span>
                    <span class="shot-type">{{ shot.type }}</span>
                    <span class="shot-desc">{{ shot.desc }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 底部脚本参数 -->
            <div class="editor-footer-metrics">
              <div class="metric-item">
                <span class="metric-label">建议拍摄时长</span>
                <span class="metric-val">45s ~ 60s</span>
              </div>
              <div class="metric-item">
                <span class="metric-label">节奏把控</span>
                <span class="metric-val">每秒 4.2 字</span>
              </div>
              <div class="metric-item">
                <span class="metric-label">风格匹配度</span>
                <span class="metric-val highlight">98.2%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 核心能力矩阵 (Bento Architecture with Scroll Reveal) -->
    <section id="core-capabilities" class="capabilities-section">
      <div class="content-container">
        <div class="section-lead scroll-reveal">
          <div class="section-badge">CORE CAPABILITIES</div>
          <h2 class="section-title">专为短视频生态打造的四大核心架构</h2>
          <p class="section-subtitle">区别于泛化通用大模型的空洞套话，以真实平台算法推荐与完播机制驱动生产</p>
        </div>

        <div class="capabilities-grid">
          <!-- 能力 1: 选题雷达 -->
          <div class="capability-card card-interactive scroll-reveal reveal-delay-1" @click="navigateTo('/topics')">
            <div class="card-accent-line"></div>
            <div class="card-tag">VIRAL RADAR</div>
            <h3 class="card-heading">爆款选题雷达</h3>
            <p class="card-body-text">
              聚合抖音、小红书高赞爆款样本，实时追踪飙升讨论，多维评估点赞率与分享率，助你一键锁死流量池入口。
            </p>
            <div class="card-preview-box bento-preview">
              <div class="bento-widget-header">
                <div class="widget-live-indicator">
                  <span class="live-radar-dot"></span>
                  <span class="live-radar-text">实时流量池热度监测</span>
                </div>
                <span class="widget-score-badge">98.4 爆款指数</span>
              </div>
              <div class="mini-topic-item">
                <span class="topic-tag douyin">抖音 · 320W+ 播放</span>
                <span class="topic-txt">短视频黄金前3秒抓人设计公式</span>
              </div>
              <div class="mini-topic-item">
                <span class="topic-tag xhs">小红书 · 18W+ 赞藏</span>
                <span class="topic-txt">普通人低成本做个人 IP 的商业闭环</span>
              </div>
            </div>
            <div class="card-footer-action">
              <span>探索爆款选题库</span>
              <n-icon class="action-arrow"><ArrowForwardOutline /></n-icon>
            </div>
          </div>

          <!-- 能力 2: 博主解构 -->
          <div class="capability-card card-interactive scroll-reveal reveal-delay-2" @click="navigateTo('/creators')">
            <div class="card-accent-line"></div>
            <div class="card-tag">CREATOR PROFILING</div>
            <h3 class="card-heading">头部博主风格解构</h3>
            <p class="card-body-text">
              对标达人口播结构深度解构，精准复刻反常识切入、痛点故事叙述与情绪递进语调，让文案真正“说人话、有情绪”。
            </p>
            <div class="card-preview-box bento-preview">
              <div class="bento-widget-header">
                <div class="widget-live-indicator">
                  <div class="audio-equalizer">
                    <span class="eq-bar"></span>
                    <span class="eq-bar"></span>
                    <span class="eq-bar"></span>
                    <span class="eq-bar"></span>
                    <span class="eq-bar"></span>
                  </div>
                  <span class="live-radar-text">声纹语感与情绪节奏建模 · 4.2字/秒</span>
                </div>
                <span class="widget-tag-pill">深度解构</span>
              </div>
              <div class="creator-chip-row">
                <span class="chip-item">刀姐doris · 犀利反常识切入</span>
                <span class="chip-item">商业小金刚 · 痛点故事反转</span>
                <span class="chip-item">科技美学 · 参数认知降维</span>
              </div>
            </div>
            <div class="card-footer-action">
              <span>浏览博主资料库</span>
              <n-icon class="action-arrow"><ArrowForwardOutline /></n-icon>
            </div>
          </div>

          <!-- 能力 3: 产品知识库 -->
          <div class="capability-card card-interactive scroll-reveal reveal-delay-3" @click="navigateTo('/documents')">
            <div class="card-accent-line"></div>
            <div class="card-tag">KNOWLEDGE RAG</div>
            <h3 class="card-heading">企业产品知识库</h3>
            <p class="card-body-text">
              支持上传白皮书、产品手册与功能清单，自动提炼结构化卖点与权威佐证，坚决杜绝大模型胡言乱语与事实错误。
            </p>
            <div class="card-preview-box bento-preview">
              <div class="bento-widget-header">
                <div class="widget-live-indicator">
                  <span class="rag-shield-icon">🛡️</span>
                  <span class="live-radar-text">向量知识切片对齐 · 零幻觉阻断</span>
                </div>
                <span class="widget-verified-badge">100% 事实对齐</span>
              </div>
              <div class="doc-badge-row">
                <span class="doc-badge"><span class="doc-type-icon">PDF</span> 产品功能架构与白皮书</span>
                <span class="doc-badge"><span class="doc-type-icon">DOCX</span> 核心技术卖点与合规问答</span>
              </div>
            </div>
            <div class="card-footer-action">
              <span>管理产品知识库</span>
              <n-icon class="action-arrow"><ArrowForwardOutline /></n-icon>
            </div>
          </div>

          <!-- 能力 4: 即梦式 @ 引用 -->
          <div class="capability-card card-interactive scroll-reveal reveal-delay-4" @click="navigateTo('/generate')">
            <div class="card-accent-line"></div>
            <div class="card-tag">SMART MENTION WORKFLOW</div>
            <h3 class="card-heading">即梦式 @引用 工作台</h3>
            <p class="card-body-text">
              键入「@」即可快速将目标博主风格、个人独立观点与专属知识库任意组装，毫秒级输出带拍摄分镜的完整成稿。
            </p>
            <div class="card-preview-box bento-preview">
              <div class="bento-widget-header">
                <div class="widget-live-indicator">
                  <span class="workflow-symbol">⚡️</span>
                  <span class="live-radar-text">即梦式多维原子素材动态联结</span>
                </div>
                <span class="widget-speed-pill">毫秒级装配</span>
              </div>
              <div class="mention-interactive-chain">
                <span class="chain-node node-creator">@博主:刀姐</span>
                <span class="chain-connector">+</span>
                <span class="chain-node node-doc">@知识库:降噪卖点</span>
                <span class="chain-connector">+</span>
                <span class="chain-node node-viewpoint">@观点:反套路</span>
                <span class="chain-arrow">→</span>
                <span class="chain-result">黄金分镜成稿</span>
              </div>
            </div>
            <div class="card-footer-action">
              <span>进入创作工作台</span>
              <n-icon class="action-arrow"><ArrowForwardOutline /></n-icon>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 功能矩阵与快捷通道 (Matrix Modules with Scroll Reveal) -->
    <section id="matrix-modules" class="matrix-section">
      <div class="content-container">
        <div class="section-lead scroll-reveal">
          <div class="section-badge">CONTENT MATRIX</div>
          <h2 class="section-title">全套专业级内容资产中台</h2>
          <p class="section-subtitle">为创作者与运营团队提供从灵感捕捉到批量输出的完整数字资产中枢</p>
        </div>

        <div class="matrix-grid">
          <div class="matrix-item card-hover-lift scroll-reveal reveal-delay-1" @click="navigateTo('/generate')">
            <div class="matrix-icon"><n-icon size="20"><SparklesOutline /></n-icon></div>
            <div class="matrix-info">
              <h4>智能创作工作台</h4>
              <p>即梦式 @素材 自由串联，分段生成高完播脚本与拍摄分镜</p>
            </div>
            <span class="matrix-arrow">进入 →</span>
          </div>

          <div class="matrix-item card-hover-lift scroll-reveal reveal-delay-2" @click="navigateTo('/topics')">
            <div class="matrix-icon"><n-icon size="20"><TrendingUpOutline /></n-icon></div>
            <div class="matrix-info">
              <h4>爆款选题库</h4>
              <p>全网爆款视频样本雷达，按行业与点赞率灵活筛选与借势</p>
            </div>
            <span class="matrix-arrow">进入 →</span>
          </div>

          <div class="matrix-item card-hover-lift scroll-reveal reveal-delay-3" @click="navigateTo('/creators')">
            <div class="matrix-icon"><n-icon size="20"><PeopleOutline /></n-icon></div>
            <div class="matrix-info">
              <h4>博主资料库</h4>
              <p>行业标杆达人画像沉淀，解构钩子骨架与句式节奏</p>
            </div>
            <span class="matrix-arrow">进入 →</span>
          </div>

          <div class="matrix-item card-hover-lift scroll-reveal reveal-delay-4" @click="navigateTo('/documents')">
            <div class="matrix-icon"><n-icon size="20"><DocumentTextOutline /></n-icon></div>
            <div class="matrix-info">
              <h4>产品知识库</h4>
              <p>企业宣传资料与核心卖点语义索引，为生成文案精准赋能</p>
            </div>
            <span class="matrix-arrow">进入 →</span>
          </div>

          <div class="matrix-item card-hover-lift scroll-reveal reveal-delay-5" @click="navigateTo('/styles')">
            <div class="matrix-icon"><n-icon size="20"><ColorPaletteOutline /></n-icon></div>
            <div class="matrix-info">
              <h4>风格模版库</h4>
              <p>反转痛点流、干货清单流、闺蜜私信风等多种行业验证结构</p>
            </div>
            <span class="matrix-arrow">进入 →</span>
          </div>

          <div class="matrix-item card-hover-lift scroll-reveal reveal-delay-6" @click="navigateTo('/viewpoints')">
            <div class="matrix-icon"><n-icon size="20"><BulbOutline /></n-icon></div>
            <div class="matrix-info">
              <h4>我的观点库</h4>
              <p>沉淀创始人独特的商业认知与金句判断，注入真正的人格灵魂</p>
            </div>
            <span class="matrix-arrow">进入 →</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 真实创作者与品牌口碑 (Sleek Horizontal Scrolling Carousel) -->
    <section id="social-proof" class="social-proof-section">
      <div class="content-container">
        <!-- 头部导引与交互控制 -->
        <div class="social-proof-header scroll-reveal">
          <div class="section-lead-inline">
            <div class="section-badge">SOCIAL PROOF &amp; CASE STUDIES</div>
            <h2 class="section-title">来自一线短视频创作者与品牌的实测口碑</h2>
            <p class="section-subtitle">
              告别泛化大模型的空洞废话，看美妆、3C数码、商业知识IP与MCN团队如何通过文策引擎实现完播率与生产力的量级跃升
            </p>
          </div>

          <!-- 顶部轮播导航控制栏 -->
          <div class="carousel-control-cluster">
            <!-- 自动播放状态指示与切换 -->
            <button
              class="carousel-action-btn autoplay-toggle"
              :class="{ active: isAutoplayPlaying }"
              @click="toggleAutoplay"
              :title="isAutoplayPlaying ? '点击暂停自动轮播' : '点击开启自动轮播'"
            >
              <span class="pulse-play-dot" :class="{ paused: !isAutoplayPlaying }"></span>
              <span class="btn-text">{{ isAutoplayPlaying ? '自动轮播中' : '已暂停' }}</span>
            </button>

            <!-- 左右箭头按钮 -->
            <div class="carousel-nav-arrows">
              <button
                class="carousel-nav-btn prev-btn"
                :disabled="!canScrollPrev"
                @click="scrollTestimonials('prev')"
                aria-label="查看上一条实测评价"
                title="上一条实测评价"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="15 18 9 12 15 6"></polyline>
                </svg>
              </button>
              <button
                class="carousel-nav-btn next-btn"
                :disabled="!canScrollNext"
                @click="scrollTestimonials('next')"
                aria-label="查看下一条实测评价"
                title="下一条实测评价"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="9 18 15 12 9 6"></polyline>
                </svg>
              </button>
            </div>
          </div>
        </div>

        <!-- 分类筛选标签栏 -->
        <div class="proof-category-filter scroll-reveal reveal-delay-1">
          <button
            v-for="cat in testimonialCategories"
            :key="cat.id"
            class="category-filter-chip"
            :class="{ active: selectedTestimonialCategory === cat.id }"
            @click="filterTestimonials(cat.id)"
          >
            <span class="chip-label">{{ cat.label }}</span>
            <span class="chip-count" v-if="cat.id === 'all'">{{ testimonials.length }}</span>
            <span class="chip-count" v-else>{{ testimonials.filter(t => t.category === cat.id).length }}</span>
          </button>
        </div>

        <!-- 水平流畅滚动轮播卡片视口 (Horizontal Carousel Viewport & Track) -->
        <div class="carousel-viewport-wrapper scroll-reveal reveal-scale reveal-delay-2">
          <!-- 左右渐隐过渡阴影遮罩 -->
          <div class="carousel-edge-fade edge-left" :class="{ visible: canScrollPrev }"></div>
          <div class="carousel-edge-fade edge-right" :class="{ visible: canScrollNext }"></div>

          <div
            ref="testimonialTrackRef"
            class="testimonials-carousel-track"
            @mouseenter="pauseAutoplay"
            @mouseleave="resumeAutoplay"
            @touchstart.passive="pauseAutoplay"
            @touchend.passive="resumeAutoplay"
          >
            <div
              v-for="(item, idx) in filteredTestimonials"
              :key="item.id"
              class="testimonial-card card-interactive"
              :class="{ 'card-active-spotlight': activeTestimonialIndex === idx }"
            >
              <!-- 顶部卡片元信息与核心指标徽章 -->
              <div class="testimonial-card-header">
                <div class="category-and-stars">
                  <span class="card-domain-badge">{{ item.categoryName }}</span>
                  <div class="star-rating-row" :aria-label="`评分 ${item.rating} 星`">
                    <span v-for="star in 5" :key="star" class="star-icon">★</span>
                    <span class="star-score-num">5.0</span>
                  </div>
                </div>
                <div class="impact-metric-pill" :class="item.metricType">
                  <span class="metric-trend-icon">⚡</span>
                  <span class="metric-text">{{ item.metric }}</span>
                </div>
              </div>

              <!-- 核心评价大标题 -->
              <h4 class="testimonial-headline">{{ item.title }}</h4>

              <!-- 真实体验引言内容 -->
              <div class="testimonial-quote-box">
                <span class="quote-mark open">“</span>
                <p class="testimonial-quote-text">{{ item.content }}</p>
                <span class="quote-mark close">”</span>
              </div>

              <!-- 重点标签 -->
              <div class="testimonial-tags-row">
                <span v-for="tag in item.tags" :key="tag" class="workflow-tag">#{{ tag }}</span>
              </div>

              <!-- 底部作者与企业/认证信息 -->
              <div class="testimonial-author-row">
                <div class="author-avatar-wrap" :style="{ background: item.avatarBg }">
                  <span class="author-avatar-initial">{{ item.avatarText }}</span>
                  <span class="verified-avatar-badge" title="实名认证创作者">✓</span>
                </div>
                <div class="author-details">
                  <div class="author-name-line">
                    <span class="author-name">{{ item.author }}</span>
                    <span class="author-verified-tag">已认证</span>
                  </div>
                  <div class="author-subtext">
                    <span class="author-role">{{ item.role }}</span>
                    <span class="author-dot">·</span>
                    <span class="author-company">{{ item.company }}</span>
                  </div>
                </div>
                <div class="author-platform-chip">
                  <span class="platform-icon-dot"></span>
                  <span class="platform-text">{{ item.platform }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 底部轮播指示器与快速跳转 -->
        <div class="carousel-indicators-bar scroll-reveal reveal-delay-3">
          <div class="indicators-track">
            <button
              v-for="(_, idx) in filteredTestimonials"
              :key="idx"
              class="indicator-pill"
              :class="{ active: activeTestimonialIndex === idx }"
              @click="scrollTestimonialToIndex(idx)"
              :aria-label="`切换至第 ${idx + 1} 个实测案例`"
            ></button>
          </div>
          <div class="carousel-counter">
            <span class="counter-current">{{ String(activeTestimonialIndex + 1).padStart(2, '0') }}</span>
            <span class="counter-divider">/</span>
            <span class="counter-total">{{ String(filteredTestimonials.length).padStart(2, '0') }}</span>
          </div>
        </div>

        <!-- 底部信任背书指标带 (Trust Metrics Strip) -->
        <div class="social-proof-trust-strip scroll-reveal reveal-delay-4">
          <div class="trust-stat-item">
            <span class="trust-stat-num">500<span class="trust-plus">+</span></span>
            <span class="trust-stat-label">入驻先锋创作者与机构</span>
            <span class="trust-stat-desc">覆盖抖音、小红书及视频号一线团队</span>
          </div>
          <div class="trust-strip-divider"></div>
          <div class="trust-stat-item">
            <span class="trust-stat-num">120,000<span class="trust-plus">+</span></span>
            <span class="trust-stat-label">口播脚本与机位分镜生成</span>
            <span class="trust-stat-desc">标准化输出直接交付摄制与剪辑团队</span>
          </div>
          <div class="trust-strip-divider"></div>
          <div class="trust-stat-item">
            <span class="trust-stat-num">42.8<span class="trust-plus">%</span></span>
            <span class="trust-stat-label">首屏前3秒停留率提升</span>
            <span class="trust-stat-desc">反常识黄金钩子攻破算法冷启动池</span>
          </div>
          <div class="trust-strip-divider"></div>
          <div class="trust-stat-item">
            <span class="trust-stat-num">99.4<span class="trust-plus">%</span></span>
            <span class="trust-stat-label">企业知识库卖点对齐率</span>
            <span class="trust-stat-desc">杜绝大模型幻觉，一次性过审合规</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 常见问题与快速上手 FAQ (可交互手风琴展开动效、分类筛选与即时搜索) -->
    <section id="faq" class="faq-section">
      <div class="content-container">
        <!-- 区域标题与副标导引 -->
        <div class="section-lead scroll-reveal">
          <div class="section-badge">FREQUENTLY ASKED QUESTIONS</div>
          <h2 class="section-title">常见问题解答与快速上手指南</h2>
          <p class="section-subtitle">
            深入了解文策引擎在短视频完播率上的底层能力架构，以及企业和个人创作者 5 分钟极速接入配置全流程
          </p>
        </div>

        <!-- 搜索与分类筛选控制中枢 -->
        <div class="faq-control-panel scroll-reveal reveal-delay-1">
          <!-- 实时关键词搜索框 -->
          <div class="faq-search-box">
            <svg class="faq-search-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            </svg>
            <input
              v-model="faqSearchQuery"
              type="text"
              class="faq-search-input"
              placeholder="搜索问题：例如“分镜机位”、“API配置”、“零幻觉”、“知识库”、“5分钟上手”..."
              aria-label="搜索常见问题"
            />
            <button
              v-if="faqSearchQuery"
              class="faq-clear-search-btn"
              @click="faqSearchQuery = ''"
              title="清空搜索"
              aria-label="清空搜索关键词"
            >
              ✕
            </button>
          </div>

          <!-- 分类筛选药丸栏 -->
          <div class="faq-category-nav">
            <button
              v-for="cat in faqCategories"
              :key="cat.id"
              class="faq-cat-pill"
              :class="{ active: selectedFaqCategory === cat.id }"
              @click="selectedFaqCategory = cat.id"
            >
              <span class="cat-label">{{ cat.label }}</span>
              <span class="cat-badge-count">
                {{ cat.id === 'all' ? faqList.length : faqList.filter(f => f.category === cat.id).length }}
              </span>
            </button>
          </div>
        </div>

        <!-- 列表状态与展开/折叠控制栏 -->
        <div class="faq-action-row scroll-reveal reveal-delay-2">
          <div class="faq-results-summary">
            <span class="results-badge">
              共 <strong>{{ filteredFaqList.length }}</strong> 项相关解答
            </span>
            <span v-if="faqSearchQuery" class="faq-filter-indicator">
              已筛选含 “{{ faqSearchQuery }}” 的条目
              <button class="indicator-clear-btn" @click="faqSearchQuery = ''">清除过滤</button>
            </span>
          </div>

          <div class="faq-accordion-actions">
            <button
              class="faq-toggle-all-btn"
              @click="isAllExpanded ? collapseAllFaqs() : expandAllFaqs()"
              :title="isAllExpanded ? '收起所有问题' : '展开所有问题'"
            >
              <span class="toggle-icon">{{ isAllExpanded ? '−' : '+' }}</span>
              <span class="toggle-label">{{ isAllExpanded ? '全部收起' : '全部展开' }}</span>
            </button>
          </div>
        </div>

        <!-- 手风琴问答主体列表 (Accordion Deck) -->
        <div class="faq-accordion scroll-reveal reveal-delay-2">
          <!-- 搜索无结果时的友好空状态 -->
          <div v-if="filteredFaqList.length === 0" class="faq-empty-state">
            <div class="empty-icon-circle">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="11" cy="11" r="8"></circle>
                <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
              </svg>
            </div>
            <h4 class="empty-title">未找到与 “{{ faqSearchQuery }}” 相关的解答</h4>
            <p class="empty-desc">您可以尝试更换搜索词，或切换分类筛选查看全部 10 项核心问题与接入流程指南。</p>
            <button class="faq-reset-btn" @click="resetFaqFilters">
              重置筛选与关键词
            </button>
          </div>

          <!-- 问答手风琴卡片 -->
          <div
            v-for="(item, idx) in filteredFaqList"
            :key="item.id"
            class="faq-card-interactive"
            :class="{ active: isFaqExpanded(item.id) }"
          >
            <!-- 卡片头部可点击区域 -->
            <div
              class="faq-header-row"
              @click="toggleFaq(item.id)"
              role="button"
              tabindex="0"
              :aria-expanded="isFaqExpanded(item.id)"
              @keydown.enter.prevent="toggleFaq(item.id)"
              @keydown.space.prevent="toggleFaq(item.id)"
            >
              <div class="faq-title-cluster">
                <div class="faq-meta-tags">
                  <span class="faq-category-tag" :class="item.category">{{ item.categoryLabel }}</span>
                  <span class="faq-topic-tag">{{ item.tag }}</span>
                </div>
                <h3 class="faq-question-title">{{ item.q }}</h3>
              </div>
              <div class="faq-chevron-badge" :class="{ rotated: isFaqExpanded(item.id) }">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="6 9 12 15 18 9"></polyline>
                </svg>
              </div>
            </div>

            <!-- 折叠答案主体 -->
            <div class="faq-answer-collapse" v-show="isFaqExpanded(item.id)">
              <div class="faq-answer-inner">
                <!-- 主要论述段落 -->
                <p class="faq-answer-main">{{ item.a }}</p>

                <!-- 接入流程类的步骤指引图谱 (Steps Matrix) -->
                <div v-if="item.steps && item.steps.length" class="faq-steps-grid">
                  <div
                    v-for="(step, sIdx) in item.steps"
                    :key="sIdx"
                    class="faq-step-card"
                  >
                    <div class="faq-step-num-pill">{{ step.step }}</div>
                    <div class="faq-step-body">
                      <div class="faq-step-title">{{ step.title }}</div>
                      <div class="faq-step-desc">{{ step.desc }}</div>
                    </div>
                  </div>
                </div>

                <!-- 核心实操要点提示框 (Highlights Box) -->
                <div v-if="item.highlights && item.highlights.length" class="faq-highlight-box">
                  <div class="faq-highlight-title">
                    <span class="highlight-sparkle">✦</span> 核心要点解析
                  </div>
                  <ul class="faq-highlight-list">
                    <li v-for="(h, hIdx) in item.highlights" :key="hIdx">
                      <span class="highlight-bullet">•</span>
                      <span class="highlight-item-text">{{ h }}</span>
                    </li>
                  </ul>
                </div>

                <!-- 底部快捷动作跳转按钮 (若有) -->
                <div v-if="item.action" class="faq-action-footer">
                  <button
                    class="faq-jump-btn"
                    @click.stop="handleFaqAction(item.action)"
                  >
                    <span>{{ item.action.text }}</span>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                      <line x1="5" y1="12" x2="19" y2="12"></line>
                      <polyline points="12 5 19 12 12 19"></polyline>
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 仍有技术或业务疑问？咨询支持引导条 -->
        <div class="faq-support-strip scroll-reveal reveal-delay-3">
          <div class="faq-support-content">
            <div class="support-icon-wrap">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
              </svg>
            </div>
            <div class="support-text">
              <div class="support-title">还有关于企业私有化部署、模型微调或特定行业知识库的疑问？</div>
              <div class="support-subtitle">我们的内容架构专家与工程支持团队提供 1 对 1 咨询与现场演示</div>
            </div>
          </div>
          <div class="faq-support-actions">
            <button class="support-btn primary" @click="handleContactConsultant">
              预约专家咨询
            </button>
            <button class="support-btn secondary" @click="scrollToSection('workspace-demo')">
              前往工作台演练
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- 底部行动号召 Banner (滚动渐现微缩放动效) -->
    <section class="bottom-cta-section">
      <div class="content-container">
        <div class="bottom-cta-box scroll-reveal reveal-scale">
          <div class="cta-glow-element"></div>
          <h2 class="bottom-cta-title">准备好升级你的短视频爆款生产力了吗？</h2>
          <p class="bottom-cta-desc">
            无需复杂的 Prompt 调优，随时进入工作台体验 @引用 智能重组创作流程。
          </p>
          <div class="bottom-cta-buttons">
            <n-button type="primary" size="large" class="cta-primary btn-hover-lift" @click="navigateTo('/generate')">
              立即开始创作
            </n-button>
            <n-button size="large" class="cta-secondary btn-hover-lift" @click="handleDemoLogin" :loading="demoLoading">
              演示账号一键体验
            </n-button>
          </div>
        </div>
      </div>
    </section>

    <!-- 底部导航与版权 -->
    <footer class="site-footer">
      <div class="content-container">
        <div class="footer-top">
          <div class="footer-brand">
            <div class="brand-group">
              <div class="brand-logo-badge small">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                  <polygon points="23 7 16 12 23 17 23 7" />
                  <rect x="1" y="5" width="15" height="14" rx="2" ry="2" />
                </svg>
              </div>
              <span class="brand-title">文策引擎</span>
            </div>
            <p class="footer-bio">
              基于头部博主表达风格与企业产品知识库的短视频内容分析与脚本生产力中台。
            </p>
          </div>

          <div class="footer-column">
            <div class="col-heading">核心工作台</div>
            <a @click="navigateTo('/generate')">生成文案工作台</a>
            <a @click="navigateTo('/topics')">爆款选题库</a>
            <a @click="navigateTo('/creators')">博主资料库</a>
            <a @click="navigateTo('/documents')">产品知识库</a>
          </div>

          <div class="footer-column">
            <div class="col-heading">内容中台</div>
            <a @click="navigateTo('/styles')">风格模版库</a>
            <a @click="navigateTo('/viewpoints')">我的观点库</a>
            <a @click="scrollToSection('social-proof')">创作者口碑与案例</a>
            <a @click="navigateTo('/history')">对话与生成历史</a>
            <a @click="navigateTo('/pricing')">套餐与订阅</a>
          </div>

          <div class="footer-column">
            <div class="col-heading">企业与管理</div>
            <a @click="navigateTo('/settings')">企业空间设置</a>
            <a @click="navigateTo('/login')">用户登录 / 注册</a>
          </div>
        </div>

        <div class="footer-bottom">
          <span>© 2025-2026 文策引擎 (Wence Engine). 版权所有.</span>
          <span>短视频完播率与商业转化生产力系统</span>
        </div>
      </div>
    </footer>

    <!-- 浮动回到顶部按钮 (超过阈值显示) -->
    <transition name="fade-scale">
      <button v-show="showBackToTop" class="back-to-top-btn" @click="scrollToTop" title="返回顶部">
        <n-icon size="18"><ArrowUpOutline /></n-icon>
      </button>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import {
  SparklesOutline, TrendingUpOutline, PeopleOutline,
  DocumentTextOutline, ColorPaletteOutline, BulbOutline,
  PlayOutline, ArrowForwardOutline, CopyOutline, CheckmarkOutline,
  ChevronDownOutline, ArrowUpOutline
} from '@vicons/ionicons5'
import { useAuthStore } from '../stores/auth.js'
import { authApi } from '../api/index.js'

const router = useRouter()
const message = useMessage()
const authStore = useAuthStore()

const demoLoading = ref(false)
const copied = ref(false)
const expandedFaqIds = ref([1, 5])
const selectedFaqCategory = ref('all')
const faqSearchQuery = ref('')
const isScrolled = ref(false)
const showBackToTop = ref(false)
const scrollProgress = ref(0)
const scriptKey = ref(0)

let scrollObserver = null

const defaultAvatar = `data:image/svg+xml;charset=utf-8,${encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32"><rect width="32" height="32" rx="16" fill="#2563EB"/><text x="16" y="21" text-anchor="middle" font-family="Arial,sans-serif" font-size="16" font-weight="bold" fill="white">文</text></svg>')}`

// 业务赛道场景预设
const scenarios = [
  {
    id: 'tech',
    label: '数码科技',
    icon: '💻',
    docName: '2025智能降噪耳机测评白皮书',
    viewpointTag: '痛点唤醒优先于参数堆叠',
    topics: [
      '月薪3千到3万｜我只换了一个工作习惯',
      'AI时代普通人最容易忽视的超级红利',
      '别再盲目买降噪耳机了！看准这3点少花冤枉钱'
    ],
    creators: [
      { name: '极客老张', tag: '痛点反转', desc: '先拆解行业参数谎言，给出避坑指南' },
      { name: '科技美学', tag: '干货清单', desc: '场景化参数降维，小白秒懂' },
      { name: '商业小金刚', tag: '认知颠覆', desc: '从生产力底层逻辑切入' }
    ],
    scripts: {
      title: '【高完播口播】别再盲目买耳机了！看完这3点省下大几千',
      hookVisual: '博主将两副不同价位耳机重重摔在桌面上，特写镜头聚焦质感差异。',
      hookSpoken: '千万别再盲目买降噪耳机了！如果你的预算在千元以内，听我一句劝，先停下手里的付款动作，花60秒把这篇视频看完。',
      conflictText: '90%的人买耳机只盯所谓的“45dB深度降噪”，结果戴了半小时耳朵胀痛得想吐。真正的使用痛点根本不是降噪数字有多大，而是耳道声压平衡和人声透传的算法优化！',
      solutionText: '根据我们实验室近百副耳机的实测数据，真正决定佩戴舒适度的是三个硬指标：第一，双腔体泄压泄气孔设计；第二，智能动态环境音感知；第三，抗风噪微孔阵列。这几个卖点在最新发布的降噪方案里已经完全做到了千元体验百元普及。',
      ctaText: '下回买数码产品千万别再交智商税了。觉得这条内容有用的，建议先点赞收藏起来，买之前拿出来对一遍清单！',
      shots: [
        { type: '特写镜头', desc: '博主直视镜头，表情严肃提出避坑质问' },
        { type: '中景切换', desc: '拿出演示样机展示耳腔泄压孔细节' },
        { type: '图表弹窗', desc: '屏幕侧边弹出三项选购核心排查清单' },
        { type: '定格收尾', desc: '博主微笑竖起大拇指，引导点赞收藏' }
      ]
    }
  },
  {
    id: 'beauty',
    label: '美妆护肤',
    icon: '🌸',
    docName: '敏感肌屏障修护核心成分手册',
    viewpointTag: '精简护肤比盲目叠加更有效',
    topics: [
      '换季脸颊泛红刺痛？别再疯狂敷面膜了',
      '成分党避坑：这3种网红成分千万别混用',
      '早C晚A翻车自救指南：3步重建健康屏障'
    ],
    creators: [
      { name: '刀姐doris', tag: '闺蜜直言', desc: '第一人称真实共情，破除虚假神话' },
      { name: '护肤老法师', tag: '成分硬核', desc: '拿放大镜看成分表，指出底层机理' },
      { name: '美妆小确幸', tag: '温柔支招', desc: '轻柔治愈风，适合种草转化' }
    ],
    scripts: {
      title: '【真实种草】换季泛红刺痛？别再乱敷面膜了！',
      hookVisual: '博主素颜近距离展示脸颊微红泛敏状态，语气急切。',
      hookSpoken: '脸颊一到换季就刺痛起皮的姐妹，求求你们快停下手里的片状面膜！越敷角质层越烂！',
      conflictText: '很多人一看到脸干泛红，下意识就天天敷面膜，结果角质层过度水合直接烂脸。屏障受损要的是细胞间脂质补充，不是疯狂补水！',
      solutionText: '按我们研发手册的标准，修护只需要精简三步：第一，停用所有酸类；第二，用神经酰胺结合角鲨烷做仿生皮脂膜锁水；第三，物理防晒优先。我们实测了这套修护配方，48小时经皮失水率直接下降60%。',
      ctaText: '转发给你身边正在烂脸的闺蜜，按这个精简思路调理，3天就能把脸救回来。',
      shots: [
        { type: '超微距特写', desc: '展示皮肤泛红细节，激发强烈共鸣' },
        { type: '中景手持', desc: '指出护肤品配方表核心神经酰胺成分' },
        { type: '前后对比', desc: '半屏展示调理前后的水润度检测数据' },
        { type: '互动手势', desc: '手势指向下方评论区，号召打卡记录' }
      ]
    }
  },
  {
    id: 'business',
    label: '知识商业',
    icon: '📈',
    docName: '2025新个体商业化变现指引',
    viewpointTag: '做有复利的数字资产',
    topics: [
      '普通人做自媒体，为什么99%死在选题上',
      '靠信息差赚钱的时代结束了，未来只拼这一件事',
      '一个人就是一家公司：超级个体的商业闭环'
    ],
    creators: [
      { name: '商业小金刚', tag: '犀利认知', desc: '痛点反转，用数据与商业本质说话' },
      { name: '认知灯塔', tag: '金句频出', desc: '底层逻辑升维，直击痛点' },
      { name: '实战教练', tag: '保姆拆解', desc: '步骤化清晰拆解，看完能落地' }
    ],
    scripts: {
      title: '【认知口播】为什么90%做短视频的人，根本赚不到钱？',
      hookVisual: '博主坐在极简办公桌前，推眼镜直视镜头，语气沉稳有力。',
      hookSpoken: '如果你做短视频3个月还没拿到正反馈，请停下手中毫无意义的日更，听我说完这3条底层商业真相。',
      conflictText: '很多人以为做短视频是拼文笔、拼剪辑，根本不是！短视频本质是一场精准的用户注意力与交付信任的置换。你没有清晰的后端产品交付，播放量再高也只是一堆无法变现的虚荣指标。',
      solutionText: '跑通商业闭环的核心只有三件事：第一，用垂直且痛感强烈的选题过滤泛流量；第二，在文案中用标杆博主的表达框架输出高信息密度干货；第三，建立专属的产品知识库，让每一篇输出都为品牌沉淀复利资产。',
      ctaText: '把精力花在刀刃上，做有复利的事。如果你想拿到我们梳理的爆款选题清单，扣个1我发你。',
      shots: [
        { type: '中景定焦', desc: '博主沉稳开口，眼神聚焦有穿透力' },
        { type: '白板书写', desc: '在白板画出注意力-信任-变现三角漏斗' },
        { type: '金句特写', desc: '屏幕底部弹出重点标语强调复利价值' },
        { type: '行动号召', desc: '语气坚定提出引导指令' }
      ]
    }
  },
  {
    id: 'life',
    label: '职场成长',
    icon: '🌿',
    docName: '高效高潜职场人工作法手册',
    viewpointTag: '结果导向与向上管理',
    topics: [
      '职场老好人如何学会体面拒绝',
      '月薪5千到2万，向上管理只做这3件事',
      '戒掉学生思维：汇报工作千万别这么说'
    ],
    creators: [
      { name: '职场导师', tag: '情商反转', desc: '还原办公室真实对话，给出高情商解法' },
      { name: '刀姐doris', tag: '干练利落', desc: '直奔主题，破除内耗情绪' },
      { name: '思维破局者', tag: '逻辑严密', desc: '结构化分析权力与汇报关系' }
    ],
    scripts: {
      title: '【职场支招】戒掉学生思维！向上汇报千万别说这3句话',
      hookVisual: '博主拿着笔记本电脑快步走进会议室，开门见山。',
      hookSpoken: '工作能力很强却总得不到提拔？很可能是你的汇报方式在老板眼里显得极度不专业！',
      conflictText: '很多新人遇到问题就跑去问老板“这事该怎么办”，这是最典型的学生思维！老板付薪水是让你来提供解决方案做选择题的，不是来当你的解题老师。',
      solutionText: '高手向上管理永远只遵循三段论：第一，先讲结论与目前现状；第二，给出2到3个经过成本核算的备选方案及利弊；第三，给出你自己的倾向性建议并申请决策支持。这种汇报效率最高。',
      ctaText: '明天上班汇报前先把这套逻辑套一遍，你的职业口碑会瞬间翻倍。先收藏备用！',
      shots: [
        { type: '情景还原', desc: '模拟低情商与高情商汇报现场对比' },
        { type: '正面中景', desc: '博主条理清晰拆解三段论核心模型' },
        { type: '卡片提示', desc: '屏幕弹出汇报公式模板并逐条打钩' },
        { type: '结语特写', desc: '博主合上笔记本，露出自信微笑' }
      ]
    }
  }
]

// 响应式状态
const currentScenario = ref(scenarios[0])
const selectedTopic = ref(scenarios[0].topics[0])
const selectedCreator = ref(scenarios[0].creators[0])
const selectedPlatform = ref('douyin')
const isGenerating = ref(false)
const simulationStageText = ref('AI 正在准备推演...')

const platformOptions = [
  { id: 'douyin', name: '抖音', styleTag: '3秒黄金钩子 · 快节奏口播' },
  { id: 'xiaohongshu', name: '小红书', styleTag: '第一人称闺蜜体 · 真实种草' },
  { id: 'weixin', name: '视频号', styleTag: '深度认知反转 · 社交共鸣' }
]

const selectedPlatformName = computed(() => {
  const p = platformOptions.find(item => item.id === selectedPlatform.value)
  return p ? p.name : '全网发布'
})

const currentScript = computed(() => currentScenario.value.scripts)

function switchScenario(s) {
  currentScenario.value = s
  selectedTopic.value = s.topics[0]
  selectedCreator.value = s.creators[0]
  scriptKey.value++
}

function selectTopic(t) {
  selectedTopic.value = t
  scriptKey.value++
}

function selectCreator(c) {
  selectedCreator.value = c
  scriptKey.value++
}

// 平滑滚动定位方法
function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function scrollToSection(sectionId) {
  const target = document.getElementById(sectionId)
  if (target) {
    target.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

// 统一导航跳转
function navigateTo(path) {
  if (path === '/generate' || path.startsWith('/topics') || path.startsWith('/creators') || path.startsWith('/documents')) {
    if (authStore.isAuthenticated) {
      router.push(path)
    } else {
      handleDemoLogin(path)
    }
  } else {
    router.push(path)
  }
}

// 免登录一键极速体验演示账号
async function handleDemoLogin(targetPath = '/generate') {
  demoLoading.value = true
  try {
    const res = await authApi.login({
      email: 'demo@wenceai.xyz',
      password: 'password123',
    })
    authStore.setToken(res.data.token)
    authStore.setUser(res.data.user)
    authStore.setTenant(res.data.tenant)
    message.success('已载入演示空间，进入创作工作台！')
    router.push(typeof targetPath === 'string' ? targetPath : '/generate')
  } catch (err) {
    message.info('正在前往登录页面...')
    router.push('/login')
  } finally {
    demoLoading.value = false
  }
}

function handleLogout() {
  authStore.logout()
  message.success('已退出登录')
}

// 真实的多阶段模拟生成动效
function runSimulation() {
  if (isGenerating.value) return
  isGenerating.value = true
  simulationStageText.value = `正在解析 ${selectedCreator.value.name} 的表达结构与钩子公式...`

  setTimeout(() => {
    simulationStageText.value = `正在检索《${currentScenario.value.docName}》核心卖点与论据...`
  }, 400)

  setTimeout(() => {
    simulationStageText.value = '正在组装结构化口播脚本与机位分镜...'
  }, 800)

  setTimeout(() => {
    isGenerating.value = false
    scriptKey.value++
    message.success('短视频脚本已基于选中风格与知识库生成就绪！')
  }, 1200)
}

function copyScriptContent() {
  const s = currentScript.value
  const full = `${s.title}\n\n【黄金3秒前戏】\n画面：${s.hookVisual}\n台词：${s.hookSpoken}\n\n【痛点立论】\n${s.conflictText}\n\n【核心干货】\n${s.solutionText}\n\n【行动号召】\n${s.ctaText}`
  navigator.clipboard?.writeText(full)
  copied.value = true
  message.success('脚本内容已成功复制到剪贴板')
  setTimeout(() => {
    copied.value = false
  }, 2000)
}

function isFaqExpanded(id) {
  return expandedFaqIds.value.includes(id)
}

function toggleFaq(id) {
  const index = expandedFaqIds.value.indexOf(id)
  if (index > -1) {
    expandedFaqIds.value.splice(index, 1)
  } else {
    expandedFaqIds.value.push(id)
  }
}

const isAllExpanded = computed(() => {
  if (filteredFaqList.value.length === 0) return false
  return filteredFaqList.value.every(item => expandedFaqIds.value.includes(item.id))
})

function expandAllFaqs() {
  const allIds = filteredFaqList.value.map(item => item.id)
  expandedFaqIds.value = Array.from(new Set([...expandedFaqIds.value, ...allIds]))
}

function collapseAllFaqs() {
  const currentIds = new Set(filteredFaqList.value.map(item => item.id))
  expandedFaqIds.value = expandedFaqIds.value.filter(id => !currentIds.has(id))
}

function resetFaqFilters() {
  selectedFaqCategory.value = 'all'
  faqSearchQuery.value = ''
  expandedFaqIds.value = [1, 5]
}

function handleFaqAction(action) {
  if (!action) return
  if (action.type === 'scroll') {
    scrollToSection(action.target)
  } else if (action.type === 'route') {
    navigateTo(action.path)
  }
}

function handleContactConsultant() {
  message.success('已为您连接专属内容顾问，欢迎直接体验免登录演示账号或联系商务团队！')
  setTimeout(() => {
    scrollToSection('workspace-demo')
  }, 400)
}

// 滚动监听与进度条计算
const handleScroll = () => {
  const scrollTop = window.scrollY || document.documentElement.scrollTop
  const docHeight = document.documentElement.scrollHeight - window.innerHeight
  scrollProgress.value = docHeight > 0 ? Math.min(100, Math.max(0, (scrollTop / docHeight) * 100)) : 0
  isScrolled.value = scrollTop > 20
  showBackToTop.value = scrollTop > 350
}

// 初始化 IntersectionObserver 实现滚动触发式入场动画
function initScrollObserver() {
  if (typeof IntersectionObserver === 'undefined') {
    // 降级兜底：直接显示所有元素
    document.querySelectorAll('.scroll-reveal').forEach(el => el.classList.add('is-revealed'))
    return
  }

  scrollObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-revealed')
        // 一旦入场展示即取消观察，保障动画只流畅触发一次
        scrollObserver?.unobserve(entry.target)
      }
    })
  }, {
    root: null,
    rootMargin: '0px 0px -40px 0px',
    threshold: 0.12
  })

  document.querySelectorAll('.scroll-reveal').forEach(el => {
    scrollObserver.observe(el)
  })
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll, { passive: true })
  handleScroll()
  if (testimonialTrackRef.value) {
    testimonialTrackRef.value.addEventListener('scroll', handleTestimonialsScroll, { passive: true })
    updateCarouselScrollState()
  }
  startAutoplay()
  setTimeout(() => {
    initScrollObserver()
  }, 100)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
  pauseAutoplay()
  if (testimonialTrackRef.value) {
    testimonialTrackRef.value.removeEventListener('scroll', handleTestimonialsScroll)
  }
  if (scrollObserver) {
    scrollObserver.disconnect()
    scrollObserver = null
  }
})

// 创作者口碑与社交证明 (Social Proof & Testimonials)
const testimonialTrackRef = ref(null)
const activeTestimonialIndex = ref(0)
const selectedTestimonialCategory = ref('all')
const canScrollPrev = ref(false)
const canScrollNext = ref(true)
const isAutoplayPlaying = ref(true)
let autoplayInterval = null

const testimonialCategories = [
  { id: 'all', label: '全部实测' },
  { id: 'tech', label: '3C数码硬件' },
  { id: 'beauty', label: '美妆个护' },
  { id: 'business', label: '商业知识IP' },
  { id: 'mcn', label: 'MCN多账号' },
  { id: 'global', label: '品牌出海' }
]

const testimonials = [
  {
    id: 1,
    category: 'tech',
    categoryName: '3C数码硬件',
    rating: 5,
    metric: '完播率 +46%',
    metricType: 'highlight-blue',
    title: '彻底告别通用大模型的空洞废话，黄金3秒留存率直接翻倍',
    content: '以前用通用对话模型写耳机脚本，吐出来的全是“首先、其次、总之”这种八股文，发出去播放量卡死在500。用文策引擎 @极客老张 风格 + @产品手册 后，第一句台词就甩出反常识痛点，上周我们耳机的带货视频前3秒留存率从28%直接飙到54%！',
    author: '张逸凡',
    role: '主创编导',
    company: '极客视界 (数码科技矩阵)',
    avatarText: '张',
    avatarBg: 'linear-gradient(135deg, #2563eb, #38bdf8)',
    platform: '抖音 150w+ 粉丝',
    tags: ['黄金3秒钩子', '痛点反转', '带货转化'],
    verified: true
  },
  {
    id: 2,
    category: 'beauty',
    categoryName: '美妆个护',
    rating: 5,
    metric: '单条点赞 12w+',
    metricType: 'highlight-pink',
    title: '闺蜜体第一人称真实种草，毫无生硬广告推销痕迹',
    content: '美妆短视频最忌讳假大空的广告腔。文策引擎不仅能解构刀姐这种头部博主的共情语速，还能把我们内部几十页复杂的修护成分手册转化为通俗易懂的“人话”。生成的台词像闺蜜夜聊一样自然，上月爆了一条点赞12万的换季自救指南。',
    author: '周若宁',
    role: '内容主理人',
    company: '悦己新消费内容矩阵',
    avatarText: '周',
    avatarBg: 'linear-gradient(135deg, #db2777, #f472b6)',
    platform: '小红书 V8 创作者',
    tags: ['闺蜜私信风', '知识库对齐', '自然种草'],
    verified: true
  },
  {
    id: 3,
    category: 'business',
    categoryName: '商业知识IP',
    rating: 5,
    metric: '单月增粉 25w+',
    metricType: 'highlight-amber',
    title: '将个人碎片化灵感，秒级重构为高完播与高互动口播',
    content: '作为知识类IP，最痛苦的是平时有很多好点子，但写成脚本总觉得节奏拖沓。通过文策引擎的「我的观点库」，我把零散的随手笔记投进去，再 @商业小金刚 的认知反转框架，一键就生成了带情绪递进的45秒口播，单月新增关注超25万。',
    author: '陈立言',
    role: '商业IP主理人',
    company: '立言商业观察',
    avatarText: '陈',
    avatarBg: 'linear-gradient(135deg, #d97706, #fbbf24)',
    platform: '视频号 头部知识榜',
    tags: ['认知颠覆', '观点库沉淀', '高完播口播'],
    verified: true
  },
  {
    id: 4,
    category: 'mcn',
    categoryName: 'MCN机构',
    rating: 5,
    metric: '交付提速 3.5x',
    metricType: 'highlight-purple',
    title: '自带运镜分镜执行表，摄影和剪辑拿来就能踩点实拍',
    content: '我们机构旗下有18个不同赛道的账号。以往编导把文案写完，还要花大半天给摄制组标注机位、画外音和贴片提示。文策引擎直接连同5个分镜的景别、运镜和动作指令一并打包输出，团队从选题到成片直接省去2天扯皮时间。',
    author: '林思雅',
    role: 'MCN内容总监',
    company: '星芒互娱传媒',
    avatarText: '林',
    avatarBg: 'linear-gradient(135deg, #7c3aed, #a78bfa)',
    platform: '全网多平台矩阵',
    tags: ['机位分镜表', '多账号协作', '提效300%'],
    verified: true
  },
  {
    id: 5,
    category: 'tech',
    categoryName: '3C数码硬件',
    rating: 5,
    metric: '核心参数 0 差错',
    metricType: 'highlight-emerald',
    title: '企业知识库向量对齐，法务与合规部一次性过审',
    content: '智能硬件类目最怕博主在短视频里把芯片算力、续航时长或者合规卖点讲错导致违规风险。文策引擎的产品知识库向量匹配非常精确，AI在生成脚本时不仅不臆造，还严格遵循我们上传的合规红线，法务和品牌部现在都是一次性过审。',
    author: '何文杰',
    role: '品牌市场负责人',
    company: '未来引力智造',
    avatarText: '何',
    avatarBg: 'linear-gradient(135deg, #059669, #34d399)',
    platform: '企业认证品牌方',
    tags: ['知识库切片', '零幻觉', '合规过审'],
    verified: true
  },
  {
    id: 6,
    category: 'global',
    categoryName: '品牌出海',
    rating: 5,
    metric: '赞藏比 16.4%',
    metricType: 'highlight-indigo',
    title: '标准化爆款骨架，新人编导两周内就能独立交出爆款',
    content: '之前团队招新手编导，培训两三个月写出来的东西还是缺乏节奏感。现在给新人配置文策引擎，按照“3秒黄金钩子 + 痛点认知冲突 + 知识库卖点 + 行动号召”的标准化生产流水线走，入职第二周的实习生就写出了赞藏比16.4%的爆款脚本。',
    author: 'Sophie Zhao',
    role: '出海内容负责人',
    company: 'Aurora Global Media',
    avatarText: 'S',
    avatarBg: 'linear-gradient(135deg, #4f46e5, #818cf8)',
    platform: 'TikTok & 视频号生态',
    tags: ['标准化生产', '团队赋能', '高赞藏比'],
    verified: true
  }
]

const filteredTestimonials = computed(() => {
  if (selectedTestimonialCategory.value === 'all') return testimonials
  return testimonials.filter(t => t.category === selectedTestimonialCategory.value)
})

function updateCarouselScrollState() {
  const track = testimonialTrackRef.value
  if (!track) return
  const scrollLeft = track.scrollLeft
  const maxScroll = track.scrollWidth - track.clientWidth
  canScrollPrev.value = scrollLeft > 10
  canScrollNext.value = scrollLeft < maxScroll - 10

  const card = track.querySelector('.testimonial-card')
  if (card) {
    const cardWidth = card.offsetWidth + 24
    const currentIndex = Math.round(scrollLeft / cardWidth)
    activeTestimonialIndex.value = Math.min(Math.max(0, currentIndex), filteredTestimonials.value.length - 1)
  }
}

function handleTestimonialsScroll() {
  updateCarouselScrollState()
}

function scrollTestimonials(direction) {
  const track = testimonialTrackRef.value
  if (!track) return
  const card = track.querySelector('.testimonial-card')
  const scrollAmount = card ? card.offsetWidth + 24 : 380
  track.scrollBy({
    left: direction === 'next' ? scrollAmount : -scrollAmount,
    behavior: 'smooth'
  })
}

function scrollTestimonialToIndex(idx) {
  const track = testimonialTrackRef.value
  if (!track) return
  const cards = track.querySelectorAll('.testimonial-card')
  if (cards[idx]) {
    cards[idx].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' })
    activeTestimonialIndex.value = idx
  }
}

function filterTestimonials(catId) {
  selectedTestimonialCategory.value = catId
  activeTestimonialIndex.value = 0
  const track = testimonialTrackRef.value
  if (track) {
    track.scrollTo({ left: 0, behavior: 'smooth' })
  }
}

function startAutoplay() {
  if (autoplayInterval) clearInterval(autoplayInterval)
  autoplayInterval = setInterval(() => {
    if (!isAutoplayPlaying.value) return
    const track = testimonialTrackRef.value
    if (!track) return
    const maxScroll = track.scrollWidth - track.clientWidth
    if (track.scrollLeft >= maxScroll - 20) {
      track.scrollTo({ left: 0, behavior: 'smooth' })
    } else {
      scrollTestimonials('next')
    }
  }, 4500)
}

function pauseAutoplay() {
  if (autoplayInterval) {
    clearInterval(autoplayInterval)
    autoplayInterval = null
  }
}

function resumeAutoplay() {
  if (isAutoplayPlaying.value) {
    startAutoplay()
  }
}

function toggleAutoplay() {
  isAutoplayPlaying.value = !isAutoplayPlaying.value
  if (isAutoplayPlaying.value) {
    startAutoplay()
    message.info('已开启自动平滑轮播')
  } else {
    pauseAutoplay()
    message.info('已暂停自动轮播')
  }
}

const faqCategories = [
  { id: 'all', label: '全部常见问题' },
  { id: 'capabilities', label: '引擎核心能力 (Capabilities)' },
  { id: 'setup', label: '接入与配置流程 (Setup Process)' },
  { id: 'enterprise', label: '团队协同与合规 (Enterprise)' }
]

const faqList = [
  {
    id: 1,
    category: 'capabilities',
    categoryLabel: '核心能力',
    tag: '#完播率重构',
    q: '文策引擎与通用对话大模型（如 ChatGPT / Claude）在短视频创作上有何本质差异？',
    a: '通用大语言模型本质擅长书面化、论述型写作，生成的文本往往逻辑冗长、充满“首先、其次、综上所述”等机械式AI套话，若直接用于短视频口播，极易因缺乏视听节奏导致用户在前3秒划走。文策引擎专门针对短视频公域算法底层逻辑进行工程化重构，核心差异在于：',
    highlights: [
      '黄金3秒反常识钩子：在前3秒精准抛出高反差认知冲突或视听钩子，专攻突破公域500播放量冷启动池。',
      '真人口播语速与呼吸停顿解构：拆解头部博主的实际发音节奏与情绪起伏，生成符合自然口播习惯的高转化台词。',
      '@产品手册 知识库向量对齐：通过 RAG 语义切片技术锁定产品卖点与合规红线，坚决杜绝大模型臆造参数。',
      '声画一体机位分镜输出：不仅输出口播台词，还直接生成景别、运镜、花字贴片与动作指令，无缝对接现场拍摄。'
    ],
    action: { text: '体验工作台机位分镜演练', target: 'workspace-demo', type: 'scroll' }
  },
  {
    id: 2,
    category: 'capabilities',
    categoryLabel: '核心能力',
    tag: '#去AI塑料感',
    q: '如何确保生成的短视频脚本具有真实网感，杜绝千篇一律的AI空洞套话？',
    a: '文策引擎内置了「视听语言动力学」与「达人语音流分析器」，通过底层三层语义过滤器解决传统大模型的“塑料感”与推销腔调：',
    highlights: [
      '动态句式变频技术：打破平铺直叙的长句均一节奏，高频交替使用短促设问、口语化感叹词与断句，还原真实人类口头表达习惯。',
      '情绪波形起伏调度：按照“痛点戳刺 → 认知反转 → 深度解惑 → 情绪共鸣”建立心理预期管理，避免说教式科普。',
      '高权重去八股词库：强制过滤“不可否认、众所周知、显而易见、总而言之”等 500+ 类AI生成高频废话，确保字字紧扣完播率。'
    ]
  },
  {
    id: 3,
    category: 'capabilities',
    categoryLabel: '核心能力',
    tag: '#标准化分镜',
    q: '生成的分镜脚本包含哪些具体拍摄与剪辑执行指导？摄制组能直接拿去实拍吗？',
    a: '完全可以直接交付摄制与剪辑团队。文策引擎输出标准化的视听分镜矩阵（机位景别表），涵盖拍摄现场与后期机房所需的完整技术参数：',
    highlights: [
      '景别与机位定义：精确标注特写镜头（如产品核心细节、质地微距）、中景手持、第一人称主观视角或定格收尾。',
      '运镜动势指令：包含推镜头增强压迫感、平移展示产品阵列、快速摇镜头转场以及手势互动导引。',
      '同期声台词与口播语速：精确到秒级的口播台词节奏建议与重点重音字标注，方便主持人跟读提词器。',
      '后期花字贴片与BGM提示：明确屏幕弹窗浮层卡片、强调字幕特效与背景音乐重音踩点时机，极大缩减编导沟通成本。'
    ]
  },
  {
    id: 4,
    category: 'capabilities',
    categoryLabel: '核心能力',
    tag: '#多平台算法',
    q: '针对抖音、小红书、微信视频号与快手，文策引擎如何做针对性算法适配？',
    a: '不同内容分发平台的推荐分发机制与用户心理账户截然不同，文策引擎针对各平台算法核心推荐指标构建了针对性生成流水线：',
    highlights: [
      '抖音：侧重“高前戏抓眼球、快节奏信息密集、引导完播与评论区争论点”，追求黄金3秒留存率与复播完播率。',
      '小红书：采用第一人称“真实闺蜜/哥们体”，侧重生活化痛点自救与清单式笔记排版，以高赞藏比与种草信任为核心导向。',
      '微信视频号：深度契合30岁+高线成熟受众，强化“认知升级、商业洞察、底层逻辑”，主打熟人社交圈高赞高转。',
      '快手：突出“真诚老铁人设、生活烟火气与直白高性价比促单”，建立长效人设信赖。'
    ]
  },
  {
    id: 5,
    category: 'setup',
    categoryLabel: '配置流程',
    tag: '#5分钟快速上手',
    q: '新团队或个人创作者如何从零开始，在 5 分钟内完成系统初始化并生成第一条分镜脚本？',
    a: '无需任何复杂的 Prompt 提示词工程学习，仅需极简 4 步即可走通属于您团队的短视频高效工业化生产闭环：',
    steps: [
      { step: '01', title: '进入空间与初始化', desc: '点击顶部「立即开始创作」或「演示账号体验」，一键进入专属内容工作室中台环境。' },
      { step: '02', title: '建立专属产品知识库', desc: '在「产品知识库」上传 1 份产品手册、卖点清单或说明文档（支持 PDF/DOCX/TXT 格式直接拖拽上传）。' },
      { step: '03', title: '调取 @风格 与 @知识库', desc: '在工作台输入框输入 @ 符号，即可一键调出内置头部博主模版（如极客老张、刀姐）并关联产品知识。' },
      { step: '04', title: '一键生成与视听分镜导出', desc: '输入一句话选题意图，AI 即可结合知识库与达人骨架生成包含景别与口播的高转化分镜，可直接复制或导出。' }
    ],
    action: { text: '立即进入工作台实操体验', path: '/generate', type: 'route' }
  },
  {
    id: 6,
    category: 'setup',
    categoryLabel: '配置流程',
    tag: '#自定义API接入',
    q: '企业如何接入与配置自己的大模型 API Key（OpenAI / DeepSeek / Claude / Qwen 等）？',
    a: '文策引擎既提供即开即用的内置算力，也全面支持企业接入自备的模型 API Key，实现算力自主与成本极致可控：',
    steps: [
      { step: '01', title: '进入模型服务提供商设置', desc: '登录后进入系统控制台「设置」中心，切换至「模型服务提供商 (Model Providers)」配置卡片。' },
      { step: '02', title: '选择厂商并录入密钥', desc: '支持选择 DeepSeek (V3/R1)、OpenAI (GPT-4o)、Anthropic Claude、阿里通义千问等，填入您的 API Key。' },
      { step: '03', title: '自定义代理网关与超参 (可选)', desc: '支持配置企业私有代理 Base URL、模型 Temperature（创造性指数）及最大生成 Tokens 上限。' },
      { step: '04', title: '连通性测试并即刻生效', desc: '点击「测试连通」一键验证网络握手与调用配额，确认正常后点击保存，所有创作任务立即生效。' }
    ],
    highlights: [
      '端到端安全隔离：企业自备 API Key 仅在用户安全受控环境中存储，生成请求由企业账户直连大模型服务商，内部知识库与提示词绝不参与公开模型训练。'
    ]
  },
  {
    id: 7,
    category: 'setup',
    categoryLabel: '配置流程',
    tag: '#知识库切片规范',
    q: '企业产品手册、质检报告或飞书/语雀文档如何上传切片？如何确保检索零幻觉？',
    a: '针对商业短视频对产品卖点绝对准确的高要求，文策引擎研发了专用于短视频场景的 RAG 向量知识库切片与检索系统：',
    steps: [
      { step: '01', title: '多格式资料一键导入', desc: '支持直接拖拽上传 PDF 说明书、Word 宣传文档、TXT 卖点表或飞书文档文本，支持按产品型号分类管理。' },
      { step: '02', title: '智能语义分块与实体抽取', desc: '自研 Chunking 算法按功能模块、核心卖点、客群痛点与技术参数精准分块，自动剔除文档前言与版权噪音。' },
      { step: '03', title: '语义向量索引与严格对齐', desc: '在创作生成时，系统通过语义高维距离实时检索最相关的切片，生成时对关键参数进行强制真实性核验。' }
    ],
    highlights: [
      '严格事实性边界（Factuality Guarantee）：若知识库中未记载某项参数指标，引擎将严格遵循既有事实或明确声明未知，坚决杜绝虚假宣传合规风险。'
    ],
    action: { text: '查看产品知识库功能', path: '/documents', type: 'route' }
  },
  {
    id: 8,
    category: 'setup',
    categoryLabel: '配置流程',
    tag: '#风格模版克隆',
    q: '如何录入并沉淀属于我们自己 IP 达人的专属表达风格与口吻模版？',
    a: '如果您有旗下出镜主播、创始人 IP 或希望复刻某位对标大咖的表达语调，只需极简 4 步即可将其沉淀为团队标准资产：',
    steps: [
      { step: '01', title: '打开风格模版库', desc: '在导航栏进入「风格模版库」，点击右上角「新建达人风格」按钮。' },
      { step: '02', title: '录入真实爆款样本文案', desc: '粘贴 3~5 篇该达人近期完播率最高、点赞过万的短视频文案或实拍录音逐字稿（样本越真实效果越精准）。' },
      { step: '03', title: 'AI 自动解析风格画像', desc: '系统自动提炼该达人的标志性口癖、开场反常识钩子类型、叙事语速节奏与金句公式，形成结构化风格模型。' },
      { step: '04', title: '全团队 @引用 调用', desc: '命名保存后，该达人风格即加入团队专属模版库，任何成员在写脚本时输入 @博主名 即可一键调用。' }
    ],
    action: { text: '前往风格模版库', path: '/styles', type: 'route' }
  },
  {
    id: 9,
    category: 'enterprise',
    categoryLabel: '团队协同',
    tag: '#MCN与团队矩阵',
    q: 'MCN 机构或品牌多矩阵团队如何进行多账号协同管理与权限隔离？',
    a: '文策引擎专为多业务线矩阵而生，支持灵活的企业多租户协作架构：',
    highlights: [
      '细粒度角色权限管理：支持超级管理员、主创编导、摄制摄影师、剪辑后期及品牌合规审核员等不同角色分配，职责清晰。',
      '账号资产独立与共享：不同赛道或子品牌账号可拥有独立的选题池与历史记录，同时能够共享公司级核心品牌产品知识库。',
      '避免人才流失与断层：将头部达人或优秀编导的创作经验结构化沉淀在系统中，新员工入职 2 天内即可上手产出符合品牌调性的标准化爆款脚本。'
    ]
  },
  {
    id: 10,
    category: 'enterprise',
    categoryLabel: '团队协同',
    tag: '#100%商用版权',
    q: '生成的短视频文案与机位分镜脚本版权归谁所有？是否支持商业投流？',
    a: '您拥有 100% 完全独立的商业版权，可无限制投入全网商业流转：',
    highlights: [
      '资产版权 100% 归属客户：用户通过文策引擎生成的全部文案、分镜执行表、标题与衍生内容，其版权与知识产权独家归属于创作者及所属企业。',
      '商业用途无限制：可自由用于抖音/快手信息流广告投放、千川投流、线下发布会大屏口播、电商直播带货脚本及企业宣传片拍摄。',
      '多种专业格式直接导出：支持一键复制纯文本、导出 Markdown、Word (.docx) 以及剪映脚本标准格式，方便与拍摄剪辑组高效对接。'
    ]
  }
]

const filteredFaqList = computed(() => {
  let list = faqList
  if (selectedFaqCategory.value !== 'all') {
    list = list.filter(item => item.category === selectedFaqCategory.value)
  }
  const q = faqSearchQuery.value.trim().toLowerCase()
  if (q) {
    list = list.filter(item => {
      const matchQ = item.q.toLowerCase().includes(q)
      const matchA = item.a.toLowerCase().includes(q)
      const matchTag = item.tag ? item.tag.toLowerCase().includes(q) : false
      const matchSteps = item.steps ? item.steps.some(s => s.title.toLowerCase().includes(q) || s.desc.toLowerCase().includes(q)) : false
      const matchHighlights = item.highlights ? item.highlights.some(h => h.toLowerCase().includes(q)) : false
      return matchQ || matchA || matchTag || matchSteps || matchHighlights
    })
  }
  return list
})
</script>

<style scoped>
/* 页面整体容器与原生平滑滚动 */
.home-wrapper {
  width: 100%;
  min-height: 100vh;
  background-color: #f8fafc;
  color: #0f172a;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  overflow-x: hidden;
  position: relative;
  scroll-behavior: smooth;
}

/* 锚点滚动距离顶部留白 (避免被吸顶导航栏遮挡) */
#workspace-demo,
#core-capabilities,
#matrix-modules,
#faq,
#home-top,
.studio-demo-section,
.capabilities-section,
.matrix-section,
.faq-section {
  scroll-margin-top: 76px;
}

.content-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
}

/* 顶部导航栏与滚动微型进度条 */
.site-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid #e2e8f0;
  transition: all 0.3s ease;
}

.site-header.scrolled {
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
}

.scroll-progress-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 2.5px;
  background: linear-gradient(90deg, #2563eb, #6366f1, #38bdf8);
  transition: width 0.1s cubic-bezier(0.16, 1, 0.3, 1);
  z-index: 10;
}

.header-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 14px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.brand-group {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  user-select: none;
  transition: transform 0.2s ease;
}

.brand-group:hover {
  transform: translateY(-1px);
}

.brand-logo-badge {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, #2563eb, #3b82f6);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.28);
  transition: all 0.3s ease;
}

.brand-group:hover .brand-logo-badge {
  box-shadow: 0 6px 16px rgba(37, 99, 235, 0.38);
}

.brand-logo-badge.small {
  width: 28px;
  height: 28px;
  border-radius: 7px;
}

.brand-text {
  display: flex;
  flex-direction: column;
}

.brand-title {
  font-size: 18px;
  font-weight: 800;
  color: #0f172a;
  line-height: 1.2;
  letter-spacing: -0.02em;
}

.brand-subtitle {
  font-size: 11px;
  color: #64748b;
  margin-top: 2px;
}

.header-nav {
  display: flex;
  align-items: center;
  gap: 28px;
}

.nav-item {
  font-size: 14px;
  font-weight: 500;
  color: #475569;
  text-decoration: none;
  transition: color 0.2s ease;
  cursor: pointer;
  position: relative;
}

.nav-item::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 0;
  width: 0;
  height: 2px;
  background: #2563eb;
  transition: width 0.25s ease;
}

.nav-item:hover {
  color: #2563eb;
}

.nav-item:hover::after {
  width: 100%;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.user-pill:hover {
  background: #e2e8f0;
  transform: translateY(-1px);
}

.user-nickname {
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
}

.plan-badge {
  font-size: 11px;
  color: #2563eb;
  background: #eff6ff;
  padding: 1px 6px;
  border-radius: 4px;
  font-weight: 600;
}

.primary-action-btn {
  font-weight: 600;
  border-radius: 8px;
  transition: all 0.25s ease;
}

.demo-login-btn {
  font-weight: 500;
  border-radius: 8px;
  transition: all 0.25s ease;
}

/* ══════════════════════════════════════════════
   滚动触发入场动画 (Scroll-Triggered Entrance Animations)
   ══════════════════════════════════════════════ */
.scroll-reveal {
  opacity: 0;
  transform: translateY(30px);
  transition: opacity 0.75s cubic-bezier(0.16, 1, 0.3, 1), transform 0.75s cubic-bezier(0.16, 1, 0.3, 1);
  will-change: opacity, transform;
}

.scroll-reveal.reveal-scale {
  transform: scale(0.96) translateY(24px);
  transition: opacity 0.85s cubic-bezier(0.16, 1, 0.3, 1), transform 0.85s cubic-bezier(0.16, 1, 0.3, 1);
}

.scroll-reveal.is-revealed {
  opacity: 1;
  transform: translateY(0) scale(1);
}

/* 阶梯递进延时设置 */
.reveal-delay-1 { transition-delay: 0.05s; }
.reveal-delay-2 { transition-delay: 0.14s; }
.reveal-delay-3 { transition-delay: 0.23s; }
.reveal-delay-4 { transition-delay: 0.32s; }
.reveal-delay-5 { transition-delay: 0.41s; }
.reveal-delay-6 { transition-delay: 0.50s; }

/* 主视觉 Hero 区域 (现代版式设计与高冲击力视觉) */
.hero-container {
  position: relative;
  padding: 92px 24px 84px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  border-bottom: 1px solid #e2e8f0;
  overflow: hidden;
}

/* 微网格与柔和光晕背景 */
.hero-grid-pattern {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(#e2e8f0 1px, transparent 1px);
  background-size: 28px 28px;
  opacity: 0.65;
  pointer-events: none;
}

.hero-ambient-glow {
  position: absolute;
  top: -120px;
  left: 50%;
  transform: translateX(-50%);
  width: 900px;
  height: 500px;
  background: radial-gradient(circle, rgba(37, 99, 235, 0.09) 0%, rgba(99, 102, 241, 0.04) 50%, transparent 70%);
  pointer-events: none;
  animation: auraBreath 8s ease-in-out infinite alternate;
}

@keyframes auraBreath {
  0% {
    transform: translateX(-50%) scale(0.95);
    opacity: 0.7;
  }
  100% {
    transform: translateX(-50%) scale(1.1);
    opacity: 1;
  }
}

.hero-inner {
  max-width: 1040px;
  margin: 0 auto;
  text-align: center;
  position: relative;
  z-index: 1;
}

/* 首屏关键帧入场动画 */
.animate-fade-down {
  animation: fadeDown 0.7s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.animate-fade-up-1 {
  animation: fadeUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) 0.1s both;
}

.animate-fade-up-2 {
  animation: fadeUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) 0.2s both;
}

.animate-fade-up-3 {
  animation: fadeUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) 0.3s both;
}

.animate-fade-up-4 {
  animation: fadeUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) 0.4s both;
}

@keyframes fadeDown {
  from {
    opacity: 0;
    transform: translateY(-16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeUp {
  from {
    opacity: 0;
    transform: translateY(22px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 顶部眉毛胶囊标签 */
.hero-chip {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 6px 18px;
  background: #ffffff;
  border: 1px solid #dbeafe;
  border-radius: 30px;
  font-size: 13px;
  color: #1e293b;
  margin-bottom: 26px;
  box-shadow: 0 2px 10px rgba(37, 99, 235, 0.08);
  cursor: pointer;
  transition: all 0.25s ease;
}

.hero-chip:hover {
  background: #eff6ff;
  border-color: #93c5fd;
  transform: translateY(-1px);
}

.chip-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.2);
  animation: pulseDot 2s infinite;
}

@keyframes pulseDot {
  0%, 100% {
    transform: scale(1);
    box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2);
  }
  50% {
    transform: scale(1.2);
    box-shadow: 0 0 0 5px rgba(37, 99, 235, 0.35);
  }
}

.chip-label {
  font-weight: 600;
  color: #1e293b;
}

.chip-divider {
  width: 1px;
  height: 12px;
  background: #cbd5e1;
}

.chip-action {
  font-size: 12px;
  font-weight: 700;
  color: #2563eb;
}

/* 现代版式核心主标题 (Display Typography) */
.hero-heading {
  font-size: 50px;
  font-weight: 850;
  line-height: 1.2;
  color: #0f172a;
  letter-spacing: -0.035em;
  margin-bottom: 22px;
}

.hero-heading-gradient {
  color: #2563eb;
  display: inline-block;
}

/* 价值主张副标题说明文本 */
.hero-description {
  font-size: 17.5px;
  line-height: 1.75;
  color: #475569;
  max-width: 840px;
  margin: 0 auto 36px;
  letter-spacing: -0.01em;
}

.hero-description strong {
  color: #0f172a;
  font-weight: 700;
}

/* 行动号召 CTA 操作区 */
.hero-cta-group {
  margin-bottom: 48px;
}

.hero-button-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.btn-hover-lift {
  transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.2s ease;
}

.btn-hover-lift:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.08);
}

.btn-hover-lift:active {
  transform: translateY(0);
}

.hero-primary-action {
  font-size: 15.5px;
  font-weight: 700;
  height: 50px;
  padding: 0 30px;
  border-radius: 9px;
  background: #2563eb;
  box-shadow: 0 4px 16px rgba(37, 99, 235, 0.32);
}

.btn-arrow-right {
  margin-left: 4px;
  transition: transform 0.2s ease;
}

.hero-primary-action:hover .btn-arrow-right {
  transform: translateX(3px);
}

.hero-demo-action {
  font-size: 15px;
  font-weight: 600;
  height: 50px;
  padding: 0 24px;
  border-radius: 9px;
  background: #ffffff;
  border: 1px solid #cbd5e1;
}

.hero-scroll-action {
  font-size: 14px;
  color: #64748b;
  transition: color 0.2s ease;
}

.hero-scroll-action:hover {
  color: #2563eb;
}

/* 信任背书承诺行 */
.hero-reassurance-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  font-size: 13px;
  color: #64748b;
  flex-wrap: wrap;
}

.reassurance-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.check-icon {
  color: #10b981;
  font-weight: 800;
}

.reassurance-dot {
  color: #cbd5e1;
}

/* 现代版式设计：核心价值对比与指标看板 */
.hero-typography-showcase {
  max-width: 980px;
  margin: 0 auto;
}

/* 对比卡片 */
.typography-comparison-card {
  display: grid;
  grid-template-columns: 1fr 44px 1fr;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
  overflow: hidden;
  margin-bottom: 24px;
  text-align: left;
}

.comparison-side {
  padding: 24px 28px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.side-generic {
  background: #fafbfc;
}

.side-wence {
  background: #ffffff;
}

.side-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.side-tag {
  font-size: 12px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
}

.tag-bad {
  background: #fee2e2;
  color: #991b1b;
}

.tag-good {
  background: #dbeafe;
  color: #1e40af;
}

.side-metric {
  font-size: 11.5px;
  font-weight: 600;
}

.side-metric.bad {
  color: #ef4444;
}

.side-metric.good {
  color: #059669;
}

.sample-quote {
  font-size: 13.5px;
  line-height: 1.65;
  margin: 0;
  flex: 1;
}

.sample-quote.generic {
  color: #64748b;
  font-style: italic;
}

.sample-quote.wence {
  color: #1e293b;
  font-weight: 500;
}

.shot-inline-note {
  display: block;
  font-size: 11.5px;
  color: #2563eb;
  font-weight: 700;
  margin-bottom: 4px;
  font-style: normal;
}

.side-verdict {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  padding-top: 10px;
  border-top: 1px dashed #e2e8f0;
}

.side-verdict.bad {
  color: #dc2626;
}

.side-verdict.good {
  color: #059669;
  font-weight: 600;
}

.comparison-divider-line {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f1f5f9;
  position: relative;
}

.vs-circle {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #0f172a;
  color: #ffffff;
  font-size: 11px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 3px solid #ffffff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
}

/* 4 维关键价值指标条 */
.hero-metrics-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px 24px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.03);
}

.metric-pillar {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 3px;
}

.metric-stat-num {
  font-size: 32px;
  font-weight: 850;
  color: #0f172a;
  line-height: 1;
  letter-spacing: -0.03em;
}

.metric-unit {
  font-size: 16px;
  font-weight: 700;
  color: #2563eb;
  margin-left: 2px;
}

.metric-stat-label {
  font-size: 13px;
  font-weight: 700;
  color: #1e293b;
  margin-top: 4px;
}

.metric-stat-sub {
  font-size: 11.5px;
  color: #64748b;
}

.metric-pillar-divider {
  width: 1px;
  background: #e2e8f0;
  height: 48px;
  align-self: center;
}

/* 区域共用引导标题 */
.section-lead {
  text-align: center;
  max-width: 680px;
  margin: 0 auto 40px;
}

.section-badge {
  font-size: 12px;
  font-weight: 700;
  color: #2563eb;
  letter-spacing: 0.08em;
  margin-bottom: 8px;
}

.section-title {
  font-size: 32px;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.015em;
  margin-bottom: 12px;
}

.section-subtitle {
  font-size: 15px;
  color: #64748b;
  line-height: 1.6;
}

/* 工作台演练区 (高阶 Studio 体验) */
.studio-demo-section {
  padding: 88px 0 96px;
  background: #ffffff;
  border-bottom: 1px solid rgba(15, 23, 42, 0.08);
}

.scenario-tabs {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-bottom: 32px;
  flex-wrap: wrap;
  background: #f1f5f9;
  padding: 5px;
  border-radius: 30px;
  max-width: fit-content;
  margin-left: auto;
  margin-right: auto;
  border: 1px solid rgba(15, 23, 42, 0.06);
}

.scenario-tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 18px;
  border: none;
  border-radius: 24px;
  background: transparent;
  font-size: 13.5px;
  font-weight: 550;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.scenario-tab-btn:hover {
  color: #090d16;
}

.scenario-tab-btn.active {
  background: #ffffff;
  color: #090d16;
  font-weight: 700;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.08), 0 1px 2px rgba(0, 0, 0, 0.04);
}

/* 工作台画布 (IDE / Studio 旗舰体验) */
.workbench-canvas {
  display: grid;
  grid-template-columns: 380px 1fr;
  gap: 0;
  background: #ffffff;
  border: 1px solid rgba(15, 23, 42, 0.09);
  border-radius: 18px;
  box-shadow: 0 16px 40px -12px rgba(15, 23, 42, 0.08), 0 1px 3px rgba(0, 0, 0, 0.02);
  overflow: hidden;
}

.canvas-controls {
  background: #fafbfc;
  border-right: 1px solid rgba(15, 23, 42, 0.07);
  padding: 26px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.control-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(15, 23, 42, 0.06);
}

.control-header-title {
  font-size: 15px;
  font-weight: 750;
  color: #090d16;
  letter-spacing: -0.01em;
}

.control-header-badge {
  font-size: 11px;
  color: #2563eb;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 600;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.control-label {
  font-size: 12px;
  font-weight: 650;
  color: #475569;
}

.topic-presets {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.preset-topic-pill {
  padding: 10px 12px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 10px;
  background: #ffffff;
  font-size: 13px;
  color: #334155;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  line-height: 1.45;
  display: flex;
  align-items: flex-start;
  gap: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
}

.topic-indicator {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #cbd5e1;
  margin-top: 6px;
  flex-shrink: 0;
  transition: background 0.2s ease;
}

.preset-topic-pill:hover {
  background: #f8fafc;
  border-color: #94a3b8;
  transform: translateX(3px);
}

.preset-topic-pill.active {
  background: #eff6ff;
  border-color: #2563eb;
  color: #1d4ed8;
  font-weight: 650;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.12);
}

.preset-topic-pill.active .topic-indicator {
  background: #2563eb;
}

.platform-selector {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
}

.platform-card-btn {
  padding: 10px 6px;
  background: #ffffff;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
}

.platform-card-btn:hover {
  background: #f8fafc;
  border-color: #94a3b8;
}

.platform-card-btn.active {
  background: #eff6ff;
  border-color: #2563eb;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.12);
}

.platform-card-btn .platform-name {
  font-size: 13px;
  font-weight: 700;
  color: #090d16;
}

.platform-card-btn .platform-style-tag {
  font-size: 10px;
  color: #64748b;
  text-align: center;
  line-height: 1.2;
}

.creator-selector {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.creator-card-btn {
  padding: 10px 12px;
  background: #ffffff;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 10px;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
}

.creator-card-btn:hover {
  background: #f8fafc;
  border-color: #94a3b8;
  transform: translateX(3px);
}

.creator-card-btn.active {
  background: #eff6ff;
  border-color: #2563eb;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.12);
}

.creator-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 2px;
}

.creator-name {
  font-size: 13px;
  font-weight: 700;
  color: #090d16;
}

.creator-tag {
  font-size: 11px;
  color: #2563eb;
  font-weight: 600;
}

.creator-desc {
  font-size: 11.5px;
  color: #64748b;
  display: block;
}

.mention-bar-preview {
  display: flex;
  flex-direction: column;
  gap: 6px;
  background: #f8fafc;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 10px;
  padding: 10px;
}

.mention-token {
  font-size: 12px;
  padding: 4px 9px;
  border-radius: 6px;
  display: inline-block;
  font-family: monospace;
  font-weight: 550;
}

.token-creator {
  background: #e0e7ff;
  color: #3730a3;
  border: 1px solid #c7d2fe;
}

.token-doc {
  background: #dcfce7;
  color: #166534;
  border: 1px solid #bbf7d0;
}

.token-viewpoint {
  background: #fef3c7;
  color: #92400e;
  border: 1px solid #fde68a;
}

.generate-action-btn {
  font-weight: 700;
  border-radius: 10px;
  height: 44px;
  background: linear-gradient(180deg, #2563eb 0%, #1d4ed8 100%);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2), 0 4px 14px rgba(37, 99, 235, 0.3);
  transition: all 0.25s ease;
}

/* 画布主编辑展示区 */
.canvas-editor {
  padding: 26px;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  position: relative;
}

.editor-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 16px;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 20px;
}

.topbar-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.meta-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #10b981;
}

.meta-status-dot.pulsing {
  background: #2563eb;
  animation: pulseDot 1s infinite;
}

.meta-title {
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
}

.meta-score-pill {
  font-size: 11px;
  color: #059669;
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 600;
}

.editor-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 生成中的动态扫描波 */
.generating-beam-wrapper {
  margin-bottom: 16px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  padding: 12px 16px;
  overflow: hidden;
  position: relative;
}

.generating-beam {
  position: absolute;
  top: 0;
  left: -100%;
  width: 50%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(37, 99, 235, 0.25), transparent);
  animation: scanBeam 1.2s infinite ease-in-out;
}

@keyframes scanBeam {
  0% {
    left: -50%;
  }
  100% {
    left: 150%;
  }
}

.generating-status-box {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  font-weight: 600;
  color: #1d4ed8;
}

.generating-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid #bfdbfe;
  border-top-color: #2563eb;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.blur-during-gen {
  opacity: 0.6;
  filter: blur(1px);
  transition: all 0.3s ease;
}

/* 脚本排版与卡片动画 */
.script-document {
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
}

.animate-card-1 { animation: cardReveal 0.4s cubic-bezier(0.16, 1, 0.3, 1) 0.05s both; }
.animate-card-2 { animation: cardReveal 0.4s cubic-bezier(0.16, 1, 0.3, 1) 0.1s both; }
.animate-card-3 { animation: cardReveal 0.4s cubic-bezier(0.16, 1, 0.3, 1) 0.15s both; }
.animate-card-4 { animation: cardReveal 0.4s cubic-bezier(0.16, 1, 0.3, 1) 0.2s both; }
.animate-card-5 { animation: cardReveal 0.4s cubic-bezier(0.16, 1, 0.3, 1) 0.25s both; }
.animate-card-6 { animation: cardReveal 0.4s cubic-bezier(0.16, 1, 0.3, 1) 0.3s both; }

@keyframes cardReveal {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.script-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-bottom: 8px;
}

.platform-badge-tag {
  font-size: 11px;
  font-weight: 750;
  background: #090d16;
  color: #ffffff;
  padding: 3px 8px;
  border-radius: 5px;
  letter-spacing: 0.02em;
}

.script-headline {
  font-size: 19px;
  font-weight: 850;
  color: #090d16;
  letter-spacing: -0.02em;
  margin: 0;
}

.script-block {
  background: #ffffff;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 12px;
  padding: 16px 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
  transition: all 0.2s ease;
}

.script-block:hover {
  border-color: #cbd5e1;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.04);
}

.hook-block {
  background: #f8fbff;
  border: 1px solid #dbeafe;
}

.hook-block .block-label {
  color: #1d4ed8;
}

.conflict-block {
  background: #fffdfa;
  border: 1px solid #fef3c7;
}

.conflict-block .block-label {
  color: #b45309;
}

.solution-block {
  background: #f8fdfa;
  border: 1px solid #dcfce7;
}

.solution-block .block-label {
  color: #15803d;
}

.cta-block {
  background: #faf8ff;
  border: 1px solid #ede9fe;
}

.cta-block .block-label {
  color: #6d28d9;
}

.block-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.block-label {
  font-size: 13px;
  font-weight: 750;
  color: #090d16;
}

.block-hint {
  font-size: 11px;
  color: #64748b;
  font-weight: 500;
}

.block-body p {
  margin: 0;
  font-size: 14px;
  line-height: 1.68;
  color: #334155;
}

.visual-note {
  font-size: 12px;
  color: #475569;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(15, 23, 42, 0.06);
  padding: 6px 12px;
  border-radius: 6px;
  margin-bottom: 8px !important;
  font-weight: 500;
}

.storyboard-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-top: 10px;
}

.shot-card {
  background: #ffffff;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 10px;
  padding: 10px 14px;
  display: flex;
  flex-direction: column;
  gap: 3px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
}

.shot-idx {
  font-size: 11px;
  font-weight: 800;
  color: #2563eb;
}

.shot-type {
  font-size: 12.5px;
  font-weight: 700;
  color: #090d16;
}

.shot-desc {
  font-size: 11.5px;
  color: #64748b;
  line-height: 1.45;
}

.editor-footer-metrics {
  display: flex;
  align-items: center;
  justify-content: space-around;
  margin-top: 24px;
  padding: 14px 20px;
  border-top: 1px solid rgba(15, 23, 42, 0.06);
  background: #f8fafc;
  border-radius: 10px;
  border: 1px solid rgba(15, 23, 42, 0.05);
}

.metric-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.metric-label {
  font-size: 11px;
  color: #64748b;
  font-weight: 500;
}

.metric-val {
  font-size: 14.5px;
  font-weight: 750;
  color: #090d16;
}

.metric-val.highlight {
  color: #2563eb;
}

/* 核心能力 Bento Grid (旗舰级高阶设计) */
.capabilities-section {
  padding: 88px 0;
  background: #f8fafc;
  border-bottom: 1px solid rgba(15, 23, 42, 0.08);
}

.capabilities-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

.capability-card {
  background: #ffffff;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 16px;
  padding: 32px;
  display: flex;
  flex-direction: column;
  position: relative;
  cursor: pointer;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02), 0 8px 24px -4px rgba(15, 23, 42, 0.03);
  transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
}

.card-accent-line {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #2563eb, #6366f1, #38bdf8);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.capability-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 16px 36px -8px rgba(15, 23, 42, 0.09), 0 4px 12px -2px rgba(15, 23, 42, 0.04);
  border-color: rgba(37, 99, 235, 0.35);
}

.capability-card:hover .card-accent-line {
  opacity: 1;
}

.capability-card:hover .action-arrow {
  transform: translateX(4px);
}

.card-tag {
  font-size: 11px;
  font-weight: 700;
  color: #2563eb;
  letter-spacing: 0.08em;
  margin-bottom: 10px;
}

.card-heading {
  font-size: 21px;
  font-weight: 800;
  color: #090d16;
  letter-spacing: -0.02em;
  margin: 0 0 10px;
}

.card-body-text {
  font-size: 14.5px;
  color: #475569;
  line-height: 1.68;
  margin: 0 0 22px;
  flex: 1;
}

/* Bento 微组件预览框 (高定质感) */
.card-preview-box.bento-preview {
  background: #f8fafc;
  border: 1px solid rgba(15, 23, 42, 0.06);
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 22px;
}

.bento-widget-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 8px;
  margin-bottom: 10px;
  border-bottom: 1px solid rgba(15, 23, 42, 0.06);
}

.widget-live-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11.5px;
  font-weight: 600;
  color: #334155;
}

.live-radar-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.25);
  animation: pulseDot 2s infinite;
}

.widget-score-badge {
  font-size: 10.5px;
  font-weight: 700;
  color: #2563eb;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  padding: 2px 7px;
  border-radius: 4px;
}

.widget-tag-pill,
.widget-verified-badge,
.widget-speed-pill {
  font-size: 10.5px;
  font-weight: 700;
  color: #059669;
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  padding: 2px 7px;
  border-radius: 4px;
}

/* 动态音频声纹柱 */
.audio-equalizer {
  display: inline-flex;
  align-items: flex-end;
  gap: 2.5px;
  height: 12px;
}

.eq-bar {
  width: 2.5px;
  background: #2563eb;
  border-radius: 1.5px;
  animation: eqBounce 1.2s ease-in-out infinite alternate;
}

.eq-bar:nth-child(1) { height: 5px; animation-delay: 0.1s; }
.eq-bar:nth-child(2) { height: 12px; animation-delay: 0.3s; }
.eq-bar:nth-child(3) { height: 8px; animation-delay: 0.2s; }
.eq-bar:nth-child(4) { height: 11px; animation-delay: 0.4s; }
.eq-bar:nth-child(5) { height: 6px; animation-delay: 0.15s; }

@keyframes eqBounce {
  0% { transform: scaleY(0.35); }
  100% { transform: scaleY(1); }
}

.rag-shield-icon,
.workflow-symbol {
  font-size: 12px;
}

.mini-topic-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 7px;
  font-size: 12.5px;
}

.mini-topic-item:last-child {
  margin-bottom: 0;
}

.topic-tag {
  font-size: 10px;
  padding: 2px 7px;
  border-radius: 4px;
  font-weight: 600;
  flex-shrink: 0;
}

.topic-tag.douyin {
  background: #fee2e2;
  color: #dc2626;
  border: 1px solid #fecaca;
}

.topic-tag.xhs {
  background: #fef3c7;
  color: #b45309;
  border: 1px solid #fde68a;
}

.topic-txt {
  color: #334155;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 500;
}

.creator-chip-row {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.chip-item {
  font-size: 11.5px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  padding: 4px 9px;
  border-radius: 6px;
  color: #334155;
  font-weight: 500;
}

.doc-badge-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.doc-badge {
  font-size: 11.5px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  padding: 5px 10px;
  border-radius: 6px;
  color: #334155;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
}

.doc-type-icon {
  font-size: 10px;
  font-weight: 800;
  color: #2563eb;
  background: #eff6ff;
  padding: 1px 4px;
  border-radius: 3px;
}

/* 即梦式多维原子素材动态联结 */
.mention-interactive-chain {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.chain-node {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 5px;
}

.node-creator {
  background: #eff6ff;
  color: #1d4ed8;
  border: 1px solid #bfdbfe;
}

.node-doc {
  background: #ecfdf5;
  color: #047857;
  border: 1px solid #a7f3d0;
}

.node-viewpoint {
  background: #fffbeb;
  color: #b45309;
  border: 1px solid #fde68a;
}

.chain-connector {
  color: #94a3b8;
  font-weight: 700;
  font-size: 12px;
}

.chain-arrow {
  color: #2563eb;
  font-weight: 700;
  font-size: 12px;
}

.chain-result {
  font-size: 11px;
  font-weight: 700;
  color: #0f172a;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  padding: 3px 8px;
  border-radius: 5px;
}

.card-footer-action {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #2563eb;
}

.action-arrow {
  transition: transform 0.2s ease;
}

/* 功能矩阵 (高阶微质感) */
.matrix-section {
  padding: 88px 0;
  background: #ffffff;
  border-bottom: 1px solid rgba(15, 23, 42, 0.08);
}

.matrix-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.matrix-item {
  background: #ffffff;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 14px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02), 0 6px 16px -4px rgba(15, 23, 42, 0.03);
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.card-hover-lift:hover {
  background: #ffffff;
  border-color: rgba(37, 99, 235, 0.35);
  transform: translateY(-4px);
  box-shadow: 0 16px 32px -8px rgba(15, 23, 42, 0.08);
}

.card-hover-lift:hover .matrix-arrow {
  transform: translateX(4px);
  color: #2563eb;
}

.card-hover-lift:hover .matrix-icon {
  background: #2563eb;
  color: #ffffff;
  transform: scale(1.06);
  box-shadow: 0 4px 14px rgba(37, 99, 235, 0.3);
}

.matrix-icon {
  width: 46px;
  height: 46px;
  border-radius: 12px;
  background: #eff6ff;
  color: #2563eb;
  border: 1px solid #dbeafe;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.25s ease;
}

.matrix-info {
  flex: 1;
}

.matrix-info h4 {
  font-size: 15.5px;
  font-weight: 750;
  color: #090d16;
  margin: 0 0 4px;
  letter-spacing: -0.01em;
}

.matrix-info p {
  font-size: 12.5px;
  color: #64748b;
  margin: 0;
  line-height: 1.55;
}

.matrix-arrow {
  font-size: 13px;
  font-weight: 700;
  color: #94a3b8;
  transition: all 0.2s ease;
  white-space: nowrap;
}

/* 创作者实测与社交证明轮播 (Sleek Horizontal Scrolling Carousel) */
.social-proof-section {
  padding: 96px 0 88px;
  background: #ffffff;
  border-bottom: 1px solid rgba(15, 23, 42, 0.08);
  position: relative;
  overflow: hidden;
}

.social-proof-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 28px;
  gap: 24px;
}

.section-lead-inline {
  max-width: 680px;
}

.section-lead-inline .section-badge {
  margin-bottom: 10px;
}

.section-lead-inline .section-title {
  font-size: 32px;
  font-weight: 850;
  color: #090d16;
  margin: 0 0 10px;
  letter-spacing: -0.02em;
  line-height: 1.25;
}

.section-lead-inline .section-subtitle {
  font-size: 14.5px;
  color: #64748b;
  margin: 0;
  line-height: 1.6;
}

.carousel-control-cluster {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-shrink: 0;
}

.carousel-action-btn.autoplay-toggle {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 9999px;
  padding: 8px 16px;
  font-size: 12.5px;
  font-weight: 600;
  color: #475569;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.carousel-action-btn.autoplay-toggle:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
  color: #0f172a;
}

.pulse-play-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
  transition: all 0.2s ease;
  animation: dotPulse 2s infinite ease-in-out;
}

.pulse-play-dot.paused {
  background: #94a3b8;
  box-shadow: none;
  animation: none;
}

@keyframes dotPulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.35);
    opacity: 0.7;
  }
}

.carousel-nav-arrows {
  display: flex;
  gap: 8px;
}

.carousel-nav-btn {
  width: 42px;
  height: 42px;
  border-radius: 11px;
  background: #ffffff;
  border: 1px solid rgba(15, 23, 42, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #0f172a;
  cursor: pointer;
  transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.carousel-nav-btn:hover:not(:disabled) {
  border-color: #2563eb;
  color: #2563eb;
  background: #eff6ff;
  transform: translateY(-2px);
  box-shadow: 0 6px 16px -4px rgba(37, 99, 235, 0.25);
}

.carousel-nav-btn:active:not(:disabled) {
  transform: translateY(0);
}

.carousel-nav-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
  border-color: rgba(15, 23, 42, 0.06);
  background: #f8fafc;
  color: #94a3b8;
  box-shadow: none;
}

/* 分类筛选条 */
.proof-category-filter {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 24px;
  overflow-x: auto;
  scrollbar-width: none;
  padding: 4px 0;
}

.proof-category-filter::-webkit-scrollbar {
  display: none;
}

.category-filter-chip {
  padding: 7px 15px;
  border-radius: 9px;
  font-size: 13px;
  font-weight: 600;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  color: #475569;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  white-space: nowrap;
}

.category-filter-chip:hover {
  background: #f1f5f9;
  color: #0f172a;
  border-color: #cbd5e1;
}

.category-filter-chip.active {
  background: #090d16;
  border-color: #090d16;
  color: #ffffff;
  box-shadow: 0 4px 12px rgba(9, 13, 22, 0.15);
}

.chip-count {
  font-size: 11px;
  padding: 1px 7px;
  border-radius: 9999px;
  background: #e2e8f0;
  color: #64748b;
  font-weight: 700;
  line-height: 1.4;
}

.category-filter-chip.active .chip-count {
  background: rgba(255, 255, 255, 0.22);
  color: #ffffff;
}

/* 轮播视口与边缘渐隐 */
.carousel-viewport-wrapper {
  position: relative;
  width: 100%;
}

.carousel-edge-fade {
  position: absolute;
  top: 0;
  bottom: 16px;
  width: 50px;
  z-index: 2;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.carousel-edge-fade.edge-left {
  left: 0;
  background: linear-gradient(90deg, #ffffff 0%, rgba(255, 255, 255, 0) 100%);
}

.carousel-edge-fade.edge-right {
  right: 0;
  background: linear-gradient(270deg, #ffffff 0%, rgba(255, 255, 255, 0) 100%);
}

.carousel-edge-fade.visible {
  opacity: 1;
}

/* 轮播卡片轨道 */
.testimonials-carousel-track {
  display: flex;
  gap: 24px;
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  scroll-behavior: smooth;
  padding: 8px 4px 24px;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.testimonials-carousel-track::-webkit-scrollbar {
  display: none;
}

/* 评价卡片视觉 (高精高质感) */
.testimonial-card {
  flex: 0 0 calc(33.333% - 16px);
  min-width: 360px;
  max-width: 440px;
  scroll-snap-align: start;
  background: #ffffff;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 16px;
  padding: 26px 26px 22px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02), 0 8px 24px -4px rgba(15, 23, 42, 0.04);
  transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
  position: relative;
}

.testimonial-card:hover,
.testimonial-card.card-active-spotlight {
  border-color: rgba(37, 99, 235, 0.35);
  transform: translateY(-5px);
  box-shadow: 0 20px 42px -10px rgba(15, 23, 42, 0.09), 0 0 0 1px rgba(37, 99, 235, 0.08);
}

.testimonial-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.category-and-stars {
  display: flex;
  align-items: center;
  gap: 10px;
}

.card-domain-badge {
  font-size: 11.5px;
  font-weight: 700;
  color: #1e293b;
  background: #f1f5f9;
  padding: 3px 8px;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
}

.star-rating-row {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  color: #f59e0b;
  font-size: 13px;
  line-height: 1;
}

.star-score-num {
  font-size: 12px;
  font-weight: 800;
  color: #0f172a;
  margin-left: 4px;
}

/* 核心成果指标徽章 (高辨识度标签) */
.impact-metric-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  font-weight: 750;
  padding: 4px 10px;
  border-radius: 9999px;
  letter-spacing: -0.01em;
}

.impact-metric-pill.highlight-blue {
  background: #eff6ff;
  color: #1d4ed8;
  border: 1px solid #bfdbfe;
}

.impact-metric-pill.highlight-pink {
  background: #fdf2f8;
  color: #be185d;
  border: 1px solid #fbcfe8;
}

.impact-metric-pill.highlight-amber {
  background: #fffbeb;
  color: #b45309;
  border: 1px solid #fde68a;
}

.impact-metric-pill.highlight-purple {
  background: #faf5ff;
  color: #6d28d9;
  border: 1px solid #e9d5ff;
}

.impact-metric-pill.highlight-emerald {
  background: #ecfdf5;
  color: #047857;
  border: 1px solid #a7f3d0;
}

.impact-metric-pill.highlight-indigo {
  background: #eef2ff;
  color: #4338ca;
  border: 1px solid #c7d2fe;
}

.metric-trend-icon {
  font-size: 11px;
}

.testimonial-headline {
  font-size: 16px;
  font-weight: 750;
  color: #090d16;
  line-height: 1.45;
  margin: 0 0 14px;
  letter-spacing: -0.01em;
}

.testimonial-quote-box {
  position: relative;
  margin-bottom: 16px;
  flex: 1;
}

.testimonial-quote-text {
  font-size: 13px;
  color: #475569;
  line-height: 1.7;
  margin: 0;
  text-align: justify;
}

.quote-mark {
  font-family: Georgia, serif;
  font-size: 18px;
  color: #94a3b8;
  line-height: 1;
  font-weight: bold;
}

.quote-mark.open {
  margin-right: 2px;
}

.quote-mark.close {
  margin-left: 2px;
}

.testimonial-tags-row {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 18px;
}

.workflow-tag {
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  background: #f8fafc;
  border: 1px solid #f1f5f9;
  padding: 2px 7px;
  border-radius: 4px;
}

/* 卡片底部创作者作者信息 */
.testimonial-author-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid rgba(15, 23, 42, 0.06);
}

.author-avatar-wrap {
  position: relative;
  width: 42px;
  height: 42px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-weight: 800;
  font-size: 16px;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.verified-avatar-badge {
  position: absolute;
  bottom: -2px;
  right: -2px;
  width: 15px;
  height: 15px;
  border-radius: 50%;
  background: #2563eb;
  color: #ffffff;
  font-size: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid #ffffff;
  font-weight: bold;
}

.author-details {
  flex: 1;
  min-width: 0;
}

.author-name-line {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 2px;
}

.author-name {
  font-size: 14px;
  font-weight: 750;
  color: #0f172a;
}

.author-verified-tag {
  font-size: 10px;
  font-weight: 700;
  color: #047857;
  background: #ecfdf5;
  padding: 1px 5px;
  border-radius: 3px;
  border: 1px solid #a7f3d0;
}

.author-subtext {
  font-size: 11.5px;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.author-dot {
  margin: 0 3px;
  color: #cbd5e1;
}

.author-platform-chip {
  font-size: 11px;
  font-weight: 600;
  color: #475569;
  background: #f1f5f9;
  padding: 4px 8px;
  border-radius: 6px;
  white-space: nowrap;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  flex-shrink: 0;
}

.platform-icon-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #2563eb;
}

/* 轮播指示器导航条 */
.carousel-indicators-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 24px;
  padding: 0 4px;
}

.indicators-track {
  display: flex;
  align-items: center;
  gap: 8px;
}

.indicator-pill {
  height: 6px;
  width: 14px;
  border-radius: 9999px;
  background: #e2e8f0;
  border: none;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  padding: 0;
}

.indicator-pill.active {
  width: 36px;
  background: #2563eb;
}

.indicator-pill:hover:not(.active) {
  background: #cbd5e1;
}

.carousel-counter {
  font-size: 13px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  color: #64748b;
  font-weight: 600;
}

.counter-current {
  color: #0f172a;
  font-weight: 800;
}

.counter-divider {
  margin: 0 4px;
  color: #cbd5e1;
}

/* 底部信任背书指标带 (Trust Metrics Strip) */
.social-proof-trust-strip {
  margin-top: 52px;
  background: #f8fafc;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 16px;
  padding: 28px 36px;
  display: grid;
  grid-template-columns: 1fr auto 1fr auto 1fr auto 1fr;
  align-items: center;
  gap: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
}

.trust-stat-item {
  display: flex;
  flex-direction: column;
}

.trust-stat-num {
  font-size: 30px;
  font-weight: 850;
  color: #090d16;
  line-height: 1.1;
  letter-spacing: -0.02em;
}

.trust-plus {
  color: #2563eb;
  font-weight: 700;
  margin-left: 2px;
}

.trust-stat-label {
  font-size: 13.5px;
  font-weight: 700;
  color: #1e293b;
  margin-top: 6px;
}

.trust-stat-desc {
  font-size: 11.5px;
  color: #64748b;
  margin-top: 2px;
  line-height: 1.45;
}

.trust-strip-divider {
  width: 1px;
  height: 44px;
  background: rgba(15, 23, 42, 0.08);
}

/* 常见问题与快速上手 FAQ (高阶手风琴交互与工坊中枢设计) */
.faq-section {
  padding: 96px 0;
  background: #f8fafc;
  border-bottom: 1px solid rgba(15, 23, 42, 0.08);
}

/* 搜索与分类控制中枢 */
.faq-control-panel {
  max-width: 900px;
  margin: 0 auto 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 实时搜索框 */
.faq-search-box {
  position: relative;
  width: 100%;
  display: flex;
  align-items: center;
  background: #ffffff;
  border: 1px solid rgba(15, 23, 42, 0.12);
  border-radius: 12px;
  padding: 4px 14px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
  transition: all 0.2s ease;
}

.faq-search-box:focus-within {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12), 0 4px 12px rgba(37, 99, 235, 0.06);
}

.faq-search-icon {
  color: #94a3b8;
  margin-right: 10px;
  flex-shrink: 0;
}

.faq-search-input {
  flex: 1;
  border: none;
  background: transparent;
  padding: 10px 0;
  font-size: 14.5px;
  color: #0f172a;
  outline: none;
}

.faq-search-input::placeholder {
  color: #94a3b8;
}

.faq-clear-search-btn {
  background: #f1f5f9;
  border: none;
  color: #64748b;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;
}

.faq-clear-search-btn:hover {
  background: #e2e8f0;
  color: #0f172a;
}

/* 分类筛选药丸导航栏 */
.faq-category-nav {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.faq-cat-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 7px 16px;
  background: #ffffff;
  border: 1px solid rgba(15, 23, 42, 0.1);
  border-radius: 9999px;
  font-size: 13.5px;
  font-weight: 600;
  color: #475569;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  white-space: nowrap;
}

.faq-cat-pill:hover {
  border-color: #cbd5e1;
  color: #0f172a;
  background: #f8fafc;
}

.faq-cat-pill.active {
  background: #0f172a;
  border-color: #0f172a;
  color: #ffffff;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.15);
}

.cat-badge-count {
  font-size: 11px;
  font-weight: 700;
  padding: 1px 7px;
  border-radius: 9999px;
  background: #f1f5f9;
  color: #64748b;
}

.faq-cat-pill.active .cat-badge-count {
  background: rgba(255, 255, 255, 0.22);
  color: #ffffff;
}

/* 列表状态与展开折叠操作栏 */
.faq-action-row {
  max-width: 900px;
  margin: 0 auto 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 0 4px;
}

.faq-results-summary {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: #64748b;
}

.results-badge strong {
  color: #0f172a;
  font-weight: 700;
}

.faq-filter-indicator {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #eff6ff;
  color: #1e40af;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 12px;
}

.indicator-clear-btn {
  background: none;
  border: none;
  color: #2563eb;
  text-decoration: underline;
  cursor: pointer;
  font-size: 12px;
  padding: 0;
}

.faq-accordion-actions {
  display: flex;
  align-items: center;
}

.faq-toggle-all-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #ffffff;
  border: 1px solid rgba(15, 23, 42, 0.1);
  padding: 5px 12px;
  border-radius: 8px;
  font-size: 12.5px;
  font-weight: 600;
  color: #334155;
  cursor: pointer;
  transition: all 0.2s ease;
}

.faq-toggle-all-btn:hover {
  background: #f1f5f9;
  color: #0f172a;
  border-color: #cbd5e1;
}

.toggle-icon {
  font-size: 14px;
  font-weight: 700;
  color: #2563eb;
}

/* 手风琴问答主体列表 */
.faq-accordion {
  max-width: 900px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* 空状态 */
.faq-empty-state {
  background: #ffffff;
  border: 1px dashed rgba(15, 23, 42, 0.15);
  border-radius: 16px;
  padding: 48px 24px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.empty-icon-circle {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: #eff6ff;
  color: #2563eb;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.empty-title {
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 8px;
}

.empty-desc {
  font-size: 13.5px;
  color: #64748b;
  max-width: 440px;
  margin: 0 0 20px;
  line-height: 1.6;
}

.faq-reset-btn {
  background: #0f172a;
  color: #ffffff;
  border: none;
  padding: 8px 18px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
}

.faq-reset-btn:hover {
  background: #1e293b;
}

/* 手风琴卡片 (高质感折叠) */
.faq-card-interactive {
  background: #ffffff;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
  transition: all 0.24s cubic-bezier(0.16, 1, 0.3, 1);
  overflow: hidden;
}

.faq-card-interactive:hover {
  border-color: #cbd5e1;
  box-shadow: 0 8px 20px -4px rgba(0, 0, 0, 0.04);
}

.faq-card-interactive.active {
  border-color: rgba(37, 99, 235, 0.4);
  box-shadow: 0 12px 28px -6px rgba(37, 99, 235, 0.08);
}

/* 卡片标题头部行 */
.faq-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 22px 26px;
  cursor: pointer;
  user-select: none;
  transition: background 0.2s ease;
}

.faq-card-interactive.active .faq-header-row {
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
}

.faq-title-cluster {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}

.faq-meta-tags {
  display: flex;
  align-items: center;
  gap: 8px;
}

.faq-category-tag {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
  letter-spacing: 0.02em;
}

.faq-category-tag.capabilities {
  background: #eff6ff;
  color: #1d4ed8;
  border: 1px solid #bfdbfe;
}

.faq-category-tag.setup {
  background: #ecfdf5;
  color: #047857;
  border: 1px solid #a7f3d0;
}

.faq-category-tag.enterprise {
  background: #faf5ff;
  color: #7e22ce;
  border: 1px solid #e9d5ff;
}

.faq-topic-tag {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
}

.faq-question-title {
  font-size: 16.5px;
  font-weight: 750;
  color: #0f172a;
  letter-spacing: -0.01em;
  line-height: 1.45;
  margin: 0;
}

.faq-chevron-badge {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: #475569;
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.faq-chevron-badge.rotated {
  transform: rotate(180deg);
  background: #eff6ff;
  color: #2563eb;
}

/* 折叠答案内容区 */
.faq-answer-collapse {
  padding: 0 26px 24px;
  animation: answerFadeIn 0.28s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.faq-answer-inner {
  padding-top: 16px;
  border-top: 1px solid rgba(15, 23, 42, 0.06);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.faq-answer-main {
  font-size: 14.5px;
  color: #334155;
  line-height: 1.75;
  margin: 0;
}

/* 接入流程类 步骤指示矩阵 (Steps Matrix) */
.faq-steps-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-top: 4px;
}

.faq-step-card {
  background: #f8fafc;
  border: 1px solid rgba(15, 23, 42, 0.07);
  border-radius: 12px;
  padding: 14px 16px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  transition: all 0.2s ease;
}

.faq-step-card:hover {
  background: #ffffff;
  border-color: #cbd5e1;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
}

.faq-step-num-pill {
  font-size: 11px;
  font-weight: 800;
  color: #2563eb;
  background: #eff6ff;
  padding: 3px 7px;
  border-radius: 6px;
  border: 1px solid rgba(37, 99, 235, 0.2);
  flex-shrink: 0;
}

.faq-step-body {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.faq-step-title {
  font-size: 13.5px;
  font-weight: 700;
  color: #0f172a;
}

.faq-step-desc {
  font-size: 12.5px;
  color: #64748b;
  line-height: 1.55;
}

/* 核心要点高亮盒 (Highlights Box) */
.faq-highlight-box {
  background: #f0f9ff;
  border: 1px solid rgba(56, 189, 248, 0.3);
  border-radius: 12px;
  padding: 14px 18px;
}

.faq-highlight-title {
  font-size: 13px;
  font-weight: 750;
  color: #0369a1;
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}

.highlight-sparkle {
  color: #0284c7;
  font-size: 12px;
}

.faq-highlight-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.faq-highlight-list li {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 13px;
  color: #334155;
  line-height: 1.6;
}

.highlight-bullet {
  color: #0284c7;
  font-weight: bold;
}

.highlight-item-text {
  flex: 1;
}

/* 底部快捷动作跳转按钮 */
.faq-action-footer {
  display: flex;
  justify-content: flex-end;
  padding-top: 4px;
}

.faq-jump-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  color: #1d4ed8;
  padding: 7px 14px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.faq-jump-btn:hover {
  background: #dbeafe;
  color: #1e40af;
  transform: translateX(2px);
}

/* 底部技术支持与咨询 Banner (FAQ Support Strip) */
.faq-support-strip {
  max-width: 900px;
  margin: 48px auto 0;
  background: #ffffff;
  border: 1px solid rgba(15, 23, 42, 0.1);
  border-radius: 18px;
  padding: 24px 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  box-shadow: 0 4px 16px -2px rgba(0, 0, 0, 0.03);
}

.faq-support-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.support-icon-wrap {
  width: 46px;
  height: 46px;
  border-radius: 12px;
  background: #eff6ff;
  color: #2563eb;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.support-title {
  font-size: 15px;
  font-weight: 750;
  color: #0f172a;
  margin-bottom: 3px;
}

.support-subtitle {
  font-size: 13px;
  color: #64748b;
}

.faq-support-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.support-btn {
  padding: 9px 18px;
  border-radius: 10px;
  font-size: 13.5px;
  font-weight: 650;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.support-btn.primary {
  background: #2563eb;
  color: #ffffff;
  border: none;
}

.support-btn.primary:hover {
  background: #1d4ed8;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
}

.support-btn.secondary {
  background: #f8fafc;
  color: #334155;
  border: 1px solid rgba(15, 23, 42, 0.12);
}

.support-btn.secondary:hover {
  background: #f1f5f9;
  color: #0f172a;
}

@keyframes answerFadeIn {
  from {
    opacity: 0;
    transform: translateY(-6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 底部行动号召 (黑曜石旗舰氛围) */
.bottom-cta-section {
  padding: 85px 0;
  background: #ffffff;
}

.bottom-cta-box {
  background: radial-gradient(ellipse at 50% 0%, #1e293b 0%, #090d16 85%);
  color: #ffffff;
  border-radius: 20px;
  padding: 70px 40px;
  text-align: center;
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: 0 24px 64px -16px rgba(15, 23, 42, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.12);
}

.cta-glow-element {
  position: absolute;
  top: -60%;
  left: 50%;
  transform: translateX(-50%);
  width: 650px;
  height: 380px;
  background: radial-gradient(circle, rgba(37, 99, 235, 0.4) 0%, transparent 70%);
  pointer-events: none;
}

.bottom-cta-title {
  font-size: 34px;
  font-weight: 850;
  letter-spacing: -0.025em;
  margin: 0 0 16px;
  position: relative;
  z-index: 1;
}

.bottom-cta-desc {
  font-size: 16.5px;
  color: #94a3b8;
  max-width: 640px;
  margin: 0 auto 36px;
  line-height: 1.7;
  position: relative;
  z-index: 1;
}

.bottom-cta-buttons {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  position: relative;
  z-index: 1;
}

.cta-primary {
  font-weight: 700;
  font-size: 15px;
  border-radius: 9px;
  height: 48px;
  padding: 0 32px;
  background: linear-gradient(180deg, #3b82f6 0%, #1d4ed8 100%);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.25), 0 4px 16px rgba(37, 99, 235, 0.4);
}

.cta-secondary {
  background: rgba(255, 255, 255, 0.1);
  color: #ffffff;
  border: 1px solid rgba(255, 255, 255, 0.22);
  border-radius: 9px;
  height: 48px;
  padding: 0 28px;
  font-size: 15px;
  backdrop-filter: blur(10px);
}

.cta-secondary:hover {
  background: rgba(255, 255, 255, 0.18);
  border-color: rgba(255, 255, 255, 0.35);
}

/* 底部页脚 */
.site-footer {
  background: #ffffff;
  border-top: 1px solid #e2e8f0;
  padding: 55px 0 35px;
}

.footer-top {
  display: flex;
  justify-content: space-between;
  gap: 40px;
  padding-bottom: 35px;
  border-bottom: 1px solid #f1f5f9;
}

.footer-brand {
  max-width: 320px;
}

.footer-bio {
  font-size: 13px;
  color: #64748b;
  line-height: 1.65;
  margin-top: 12px;
}

.footer-column {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.col-heading {
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 4px;
}

.footer-column a {
  font-size: 13px;
  color: #64748b;
  text-decoration: none;
  cursor: pointer;
  transition: color 0.2s ease;
}

.footer-column a:hover {
  color: #2563eb;
}

.footer-bottom {
  padding-top: 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  color: #94a3b8;
}

/* 浮动回到顶部按钮 */
.back-to-top-btn {
  position: fixed;
  bottom: 30px;
  right: 30px;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: #2563eb;
  color: #ffffff;
  border: none;
  box-shadow: 0 4px 16px rgba(37, 99, 235, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 99;
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.back-to-top-btn:hover {
  background: #1d4ed8;
  transform: translateY(-3px) scale(1.05);
  box-shadow: 0 8px 20px rgba(37, 99, 235, 0.45);
}

.fade-scale-enter-active,
.fade-scale-leave-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.fade-scale-enter-from,
.fade-scale-leave-to {
  opacity: 0;
  transform: scale(0.7) translateY(10px);
}

/* 无障碍：系统倾向弱化动画时直接展示 */
@media (prefers-reduced-motion: reduce) {
  .scroll-reveal {
    opacity: 1 !important;
    transform: none !important;
    transition: none !important;
  }
}

/* 移动端与响应式适配 */
@media (max-width: 992px) {
  .hero-container {
    padding: 60px 16px 50px;
  }
  .hero-heading {
    font-size: 34px;
    line-height: 1.25;
  }
  .hero-description {
    font-size: 15px;
    margin-bottom: 28px;
  }
  .typography-comparison-card {
    grid-template-columns: 1fr;
  }
  .comparison-divider-line {
    padding: 8px 0;
  }
  .hero-metrics-strip {
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
    padding: 16px;
  }
  .metric-pillar-divider {
    display: none;
  }
  .workbench-canvas {
    grid-template-columns: 1fr;
  }
  .capabilities-grid {
    grid-template-columns: 1fr;
  }
  .matrix-grid {
    grid-template-columns: 1fr;
  }
  .social-proof-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 20px;
  }
  .carousel-control-cluster {
    width: 100%;
    justify-content: space-between;
  }
  .testimonial-card {
    flex: 0 0 calc(50% - 12px);
    min-width: 320px;
  }
  .social-proof-trust-strip {
    grid-template-columns: repeat(2, 1fr);
    gap: 24px;
    padding: 24px;
  }
  .trust-strip-divider {
    display: none;
  }
  .header-nav {
    display: none;
  }
  .footer-top {
    flex-direction: column;
    gap: 28px;
  }
  .footer-bottom {
    flex-direction: column;
    gap: 8px;
  }
  .faq-steps-grid {
    grid-template-columns: 1fr;
  }
  .faq-support-strip {
    flex-direction: column;
    align-items: flex-start;
    gap: 18px;
    padding: 20px;
  }
  .faq-support-actions {
    width: 100%;
    justify-content: flex-start;
  }
  .faq-action-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
}

@media (max-width: 640px) {
  .hero-heading {
    font-size: 28px;
  }
  .hero-chip {
    font-size: 11.5px;
    padding: 5px 12px;
  }
  .hero-button-row {
    flex-direction: column;
    width: 100%;
  }
  .hero-primary-action,
  .hero-demo-action {
    width: 100%;
  }
  .hero-metrics-strip {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  .testimonial-card {
    flex: 0 0 86vw;
    min-width: 285px;
    padding: 22px 18px 18px;
  }
  .social-proof-trust-strip {
    grid-template-columns: 1fr;
    gap: 20px;
    padding: 20px 18px;
  }
  .author-platform-chip {
    display: none;
  }
  .faq-header-row {
    padding: 16px 18px;
  }
  .faq-answer-collapse {
    padding: 0 18px 20px;
  }
  .faq-question-title {
    font-size: 15px;
  }
  .faq-category-nav {
    gap: 6px;
  }
  .faq-cat-pill {
    padding: 6px 12px;
    font-size: 12.5px;
  }
  .faq-support-strip {
    padding: 18px;
  }
  .faq-support-actions {
    flex-direction: column;
    width: 100%;
  }
  .support-btn {
    width: 100%;
    text-align: center;
  }
}
</style>
