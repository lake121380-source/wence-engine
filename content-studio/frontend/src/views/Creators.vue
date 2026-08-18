<template>
  <div>
    <div class="page-header">
      <div>
        <div class="page-title">博主资料库</div>
        <div class="page-subtitle">管理头部博主，抓取内容并提取风格</div>
      </div>
      <n-space>
        <n-button secondary @click="showAutoModal = true">
          <template #icon><n-icon><SearchOutline /></n-icon></template>
          一键发现头部博主
        </n-button>
        <n-button type="primary" @click="showAddModal = true">
          <template #icon><n-icon><AddOutline /></n-icon></template>
          手动添加博主
        </n-button>
      </n-space>
    </div>

    <!-- Platform filter tabs -->
    <n-tabs v-model:value="activePlatform" type="segment" animated style="margin-bottom: 20px;">
      <n-tab name="all">全部 ({{ creators.length }})</n-tab>
      <n-tab name="douyin">抖音</n-tab>
      <n-tab name="xiaohongshu">小红书</n-tab>
      <n-tab name="weixin">视频号</n-tab>
    </n-tabs>

    <n-spin :show="loading">
      <div v-if="filteredCreators.length === 0" class="empty-state-big">
        <n-icon size="48" color="rgba(255,255,255,0.15)"><PeopleOutline /></n-icon>
        <p>还没有添加博主</p>
        <n-button type="primary" @click="showAddModal = true">添加第一个博主</n-button>
      </div>

      <n-grid v-else cols="1 s:2 m:3" responsive="screen" :x-gap="16" :y-gap="16">
        <n-gi v-for="c in filteredCreators" :key="c.id">
          <div class="creator-card">
            <!-- SVG 背景装饰 -->
            <svg class="card-deco" aria-hidden="true" viewBox="0 0 160 100" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="140" cy="0" r="55" fill="rgba(37,99,235,0.05)"/>
              <circle cx="155" cy="20" r="30" fill="rgba(99,102,241,0.04)"/>
              <path d="M120 0 L160 0 L160 40" stroke="rgba(37,99,235,0.06)" stroke-width="1" fill="none"/>
            </svg>
            <div class="creator-header">
              <n-avatar
                :src="c.avatar_url"
                :size="44"
                round
                :img-props="{ referrerpolicy: 'no-referrer', crossorigin: 'anonymous' }"
                style="flex-shrink:0;"
              />
              <div class="creator-info">
                <div class="creator-name">{{ c.nickname }}</div>
                <div class="creator-uid">{{ displayUid(c) }}</div>
              </div>
              <n-tag size="small" :type="platformType(c.platform)" :bordered="false">{{ c.platform }}</n-tag>
            </div>

            <div class="creator-stats">
              <div class="cstat">
                <div class="cstat-val">{{ formatNum(c.follower_count) }}</div>
                <div class="cstat-label">粉丝</div>
              </div>
              <div class="cstat">
                <div class="cstat-val">{{ c.videos_in_db }}</div>
                <div class="cstat-label">已抓取</div>
              </div>
              <div class="cstat">
                <div class="cstat-val">{{ c.last_crawled_at ? '已更新' : '未抓取' }}</div>
                <div class="cstat-label">状态</div>
              </div>
            </div>

            <div class="creator-actions">
              <!-- 第一行：主操作 -->
              <div class="ca-row">
                <n-button class="ca-btn-primary" type="primary" size="small" @click.stop="viewVideos(c)">
                  <template #icon><n-icon><FilmOutline /></n-icon></template>
                  查看视频
                </n-button>
                <n-popover trigger="hover" placement="bottom">
                  <template #trigger>
                    <n-button class="ca-btn-secondary" size="small" secondary :loading="crawlingId === c.id" @click="crawl(c)">
                      <template #icon><n-icon><RefreshOutline /></n-icon></template>
                      抓取内容
                    </n-button>
                  </template>
                  <div style="display:flex;flex-direction:column;gap:6px;padding:4px;">
                    <div style="font-size:12px;color:#999;margin-bottom:2px;">抓取数量</div>
                    <n-button
                      v-for="n in [30, 50, 100, 200]" :key="n"
                      size="tiny"
                      :type="(crawlCountMap[c.id] || 30) === n ? 'primary' : 'default'"
                      @click="crawlCountMap[c.id] = n"
                    >{{ n }} 条</n-button>
                  </div>
                </n-popover>
              </div>
              <!-- 第二行：辅助操作 -->
              <div class="ca-row ca-row-secondary">
                <n-button size="small" quaternary :loading="analyzingId === c.id" @click="analyzeStyle(c)">
                  <template #icon><n-icon><ColorPaletteOutline /></n-icon></template>
                  {{ c.has_style ? '重提风格' : '提取风格' }}
                </n-button>
                <n-button size="small" quaternary @click="viewIntelCard(c)">
                  <template #icon><n-icon><DocumentOutline /></n-icon></template>
                  情报卡
                </n-button>
                <n-button size="small" quaternary style="color: var(--c-error, #ef4444); margin-left: auto;" @click="confirmDelete(c)">
                  <template #icon><n-icon><TrashOutline /></n-icon></template>
                </n-button>
              </div>
            </div>

            <div v-if="c.last_crawled_at" class="last-crawled">
              最后更新：{{ formatDate(c.last_crawled_at) }}
              <span v-if="c.has_style" class="style-badge">
                已提取风格 {{ c.style_updated_at ? formatDate(c.style_updated_at) : '' }}
              </span>
            </div>
          </div>
        </n-gi>
      </n-grid>
    </n-spin>

    <!-- Add Creator Modal -->
    <n-modal v-model:show="showAddModal" preset="card" title="添加博主" style="width: 520px;">
      <n-form ref="formRef" :model="form" :rules="rules" label-placement="top">
        <n-form-item label="平台" path="platform">
          <n-select v-model:value="form.platform" :options="platformOptions" @update:value="onPlatformChange" />
        </n-form-item>
        <!-- 视频号：搜索模式 -->
        <template v-if="form.platform === 'weixin'">
          <n-form-item label="搜索博主">
            <n-input-group>
              <n-input v-model:value="weixinSearchKeyword" placeholder="输入博主名称搜索" clearable @keyup.enter="searchWeixinCreators" />
              <n-button type="primary" :loading="weixinSearching" @click="searchWeixinCreators">
                <template #icon><n-icon><SearchOutline /></n-icon></template>
                搜索
              </n-button>
            </n-input-group>
          </n-form-item>
          <div v-if="weixinSearchResults.length > 0" class="weixin-search-results">
            <div
              v-for="item in weixinSearchResults"
              :key="item.username"
              class="weixin-result-item"
              :class="{ active: form.identifier === item.username }"
              @click="selectWeixinCreator(item)"
            >
              <div class="weixin-avatar">
                <img
                  v-if="item.avatar_url"
                  :src="item.avatar_url"
                  referrerpolicy="no-referrer"
                  crossorigin="anonymous"
                  class="weixin-avatar-img"
                  @error="e => e.target.style.display='none'"
                />
                <span v-else class="weixin-avatar-fallback">{{ (item.nickname || '?').slice(0,1) }}</span>
              </div>
              <div class="weixin-result-info">
                <div class="weixin-result-name">{{ item.nickname }}</div>
                <div v-if="item.description" class="weixin-result-desc">{{ item.description }}</div>
              </div>
              <n-icon v-if="form.identifier === item.username" size="18" color="var(--c-primary, #6366f1)">
                <CheckmarkCircleOutline />
              </n-icon>
            </div>
          </div>
          <div v-else-if="weixinSearched && !weixinSearching" style="padding:12px 0;text-align:center;color:rgba(255,255,255,0.3);font-size:13px;">
            未找到相关博主，请尝试其他关键词
          </div>
        </template>
        <!-- 其他平台：手动输入 -->
        <template v-else>
          <n-form-item :label="idLabel" path="identifier">
            <n-input v-model:value="form.identifier" :placeholder="idPlaceholder" />
          </n-form-item>
        </template>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showAddModal = false">取消</n-button>
          <n-button type="primary" :loading="adding" :disabled="form.platform === 'weixin' && !form.identifier" @click="addCreator">确认添加</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- Auto Discover Modal -->
    <n-modal v-model:show="showAutoModal" preset="card" title="一键发现头部博主" style="width: 520px;">
      <n-form label-placement="top" :show-feedback="false">
        <n-form-item label="行业关键词">
          <n-input v-model:value="autoForm.keyword" placeholder="例如：护肤、健身、美食、母婴..." clearable />
        </n-form-item>
        <n-form-item label="平台">
          <n-checkbox-group v-model:value="autoForm.platforms">
            <n-space>
              <n-checkbox value="douyin" label="抖音" />
              <n-checkbox value="xiaohongshu" label="小红书" />
              <n-checkbox value="weixin" label="视频号" />
            </n-space>
          </n-checkbox-group>
        </n-form-item>
        <n-form-item label="发现数量">
          <n-radio-group v-model:value="autoForm.limit" button-style="solid">
            <n-radio-button :value="10">10人</n-radio-button>
            <n-radio-button :value="20">20人</n-radio-button>
            <n-radio-button :value="30">30人</n-radio-button>
          </n-radio-group>
        </n-form-item>
      </n-form>

      <!-- 任务进度 -->
      <div v-if="autoTaskId" class="auto-progress">
        <n-progress
          type="line"
          :percentage="autoTask.total > 0 ? Math.round(autoTask.progress / autoTask.total * 100) : 0"
          :status="autoTask.status === 'done' ? 'success' : autoTask.status === 'error' ? 'error' : 'default'"
          :indicator-placement="'inside'"
          style="margin-bottom: 12px;"
        />
        <div class="progress-status">
          <n-tag :type="autoTask.status === 'done' ? 'success' : autoTask.status === 'error' ? 'error' : 'info'" size="small">
            {{ statusLabel(autoTask.status) }}
          </n-tag>
          <span style="margin-left: 8px; font-size: 12px; color: rgba(255,255,255,0.4);">
            {{ autoTask.progress }}/{{ autoTask.total }} 位博主
          </span>
        </div>
        <div class="progress-log">
          <div v-for="(log, i) in autoTask.log.slice(-5)" :key="i" class="log-line">{{ log }}</div>
        </div>
        <div v-if="autoTask.status === 'done' && autoTask.result" class="auto-result-summary">
          <n-statistic label="发现总数" :value="autoTask.result.total_found" />
          <n-statistic label="成功添加" :value="autoTask.result.added" />
          <n-statistic label="已在库中" :value="autoTask.result.skipped" />
          <n-statistic label="添加失败" :value="autoTask.result.failed" />
        </div>
      </div>

      <template #footer>
        <n-space justify="end">
          <n-button @click="closeAutoModal">{{ autoTask.status === 'done' ? '完成' : '取消' }}</n-button>
          <n-button
            type="primary"
            :loading="autoRunning"
            :disabled="!autoForm.keyword || autoForm.platforms.length === 0 || autoTask.status === 'running'"
            @click="startAutoDiscover"
          >
            <template #icon><n-icon><SparklesOutline /></n-icon></template>
            开始发现
          </n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- Intel Card Modal -->
    <n-modal v-model:show="showIntelCardModal" preset="card" style="width: 660px; max-height: 80vh; overflow-y: auto;">
      <template #header>
        <div style="display:flex; align-items:center; gap:10px;">
          <span>情报卡 — {{ intelCardCreator?.nickname }}</span>
        </div>
      </template>

      <div v-if="intelCard">
        <n-tabs type="line" animated>
          <n-tab-pane name="positioning" tab="账号定位">
            <div class="intel-section">{{ intelCard.positioning }}</div>
          </n-tab-pane>
          <n-tab-pane name="style" tab="视频风格">
            <div class="intel-section">{{ intelCard.video_style }}</div>
          </n-tab-pane>
          <n-tab-pane name="topics" tab="常用话题">
            <div class="intel-tags">
              <n-tag
                v-for="t in intelCard.common_topics"
                :key="t"
                type="info"
                style="margin: 4px;"
              >{{ t }}</n-tag>
            </div>
          </n-tab-pane>
          <n-tab-pane name="pain" tab="评论痛点">
            <div
              v-for="(p, i) in intelCard.comment_pain_points"
              :key="i"
              class="pain-item"
            >
              <div class="pain-title">{{ p.pain }}</div>
              <div class="pain-evidence">{{ p.evidence }}</div>
            </div>
          </n-tab-pane>
          <n-tab-pane name="summary" tab="综合摘要">
            <div class="intel-section">{{ intelCard.summary }}</div>
          </n-tab-pane>
        </n-tabs>
        <div class="intel-updated">最后更新：{{ formatDate(intelCard.updated_at) }}</div>
      </div>
      <div v-else class="empty-intel">
        <n-empty description="情报卡尚未生成" />
      </div>

      <template #footer>
        <div style="display:flex; justify-content:flex-end; gap:12px;">
          <n-button @click="showIntelCardModal = false">关闭</n-button>
          <n-button
            type="primary"
            :loading="intelCardLoading === intelCardCreator?.id"
            @click="generateIntelCard"
          >
            {{ intelCard ? '重新生成' : '生成情报卡' }}
          </n-button>
        </div>
      </template>
    </n-modal>

    <!-- 博主视频列表 Drawer -->
    <n-drawer v-model:show="showVideosDrawer" :width="860" placement="right">
      <n-drawer-content :title="`${videosCreator?.nickname} 的视频（${creatorVideos.length}条）`" closable>
        <template #header-extra>
          <n-space align="center">
            <n-button
              size="small"
              :disabled="!selectedVideoIds.size"
              @click="batchAddToDocs"
              :loading="addingToDocs"
            >
              <template #icon><n-icon><FolderOpenOutline /></n-icon></template>
              添加到资料库 ({{ selectedVideoIds.size }})
            </n-button>
            <n-button size="small" secondary @click="toggleSelectAllVideos">
              {{ selectedVideoIds.size === creatorVideos.length && creatorVideos.length > 0 ? '取消全选' : '全选' }}
            </n-button>
          </n-space>
        </template>

        <n-spin :show="loadingVideos">
          <div v-if="creatorVideos.length === 0 && !loadingVideos" class="empty-intel">
            <n-empty description="还没有抓取视频，请先点击「抓取内容」" />
          </div>

          <!-- 批量分析操作栏 -->
          <div v-if="sortedVideos.length > 0" class="batch-action-bar">
            <n-button
              type="primary"
              :loading="batchAnalyzing"
              :disabled="creatorVideos.length === 0 || batchAnalyzing"
              @click="batchAnalyzeAll"
            >
              <template #icon><n-icon><AnalyticsOutline /></n-icon></template>
              批量分析全部视频 ({{ creatorVideos.length }})
            </n-button>
            <!-- 后台任务进度条 -->
            <div v-if="batchAnalyzeTask" class="batch-task-progress">
              <n-progress
                type="line"
                :percentage="batchAnalyzeTask.total > 0 ? Math.round(batchAnalyzeTask.done / batchAnalyzeTask.total * 100) : 0"
                :status="batchAnalyzeTask.status === 'done' ? 'success' : batchAnalyzeTask.status === 'error' ? 'error' : 'default'"
                :indicator-placement="'inside'"
                style="width: 200px;"
              />
              <span class="batch-task-text">
                <template v-if="batchAnalyzeTask.status === 'running'">
                  后台分析中 {{ batchAnalyzeTask.done }}/{{ batchAnalyzeTask.total }}，可关闭此侧边栏
                </template>
                <template v-else-if="batchAnalyzeTask.status === 'done'">
                  ✓ 分析完成！成功 {{ batchAnalyzeTask.success }} / {{ batchAnalyzeTask.total }}
                </template>
                <template v-else-if="batchAnalyzeTask.status === 'error'">
                  × 分析出错
                </template>
              </span>
            </div>
          </div>

          <!-- 排序工具栏 -->
          <div v-if="sortedVideos.length > 0" class="sort-toolbar">
            <span class="sort-label">排序：</span>
            <n-radio-group v-model:value="videoSortKey" size="small">
              <n-radio-button value="like_count">点赞</n-radio-button>
              <n-radio-button value="comment_count">评论</n-radio-button>
              <n-radio-button value="collect_count">收藏</n-radio-button>
              <n-radio-button value="play_count">播放</n-radio-button>
              <n-radio-button value="like_play_ratio">点赞率</n-radio-button>
              <n-radio-button value="collect_play_ratio">收藏率</n-radio-button>
              <n-radio-button value="published_at">最新</n-radio-button>
            </n-radio-group>
          </div>

          <n-grid :cols="2" :x-gap="12" :y-gap="12">
            <n-gi v-for="v in sortedVideos" :key="v.id">
              <div
                class="cv-card"
                :class="{ selected: selectedVideoIds.has(v.id) }"
                @click="toggleSelectVideo(v)"
              >
                <!-- 选择框 -->
                <div class="cv-select">
                  <n-checkbox :checked="selectedVideoIds.has(v.id)" @click.stop @update:checked="toggleSelectVideo(v)" />
                </div>

                <!-- 封面 -->
                <div class="cv-cover">
                  <img v-if="v.cover_url" :src="v.cover_url" alt="cover" referrerpolicy="no-referrer" style="width:100%;height:100%;object-fit:cover;" @error="e=>e.target.style.display='none'" />
                  <div v-else class="cv-cover-ph">
                    <n-icon size="24" color="rgba(255,255,255,.2)">
                      <ImagesOutline v-if="videosCreator && videosCreator.platform === 'xiaohongshu'" />
                      <VideocamOutline v-else />
                    </n-icon>
                  </div>
                  <!-- 图文/视频标识 -->
                  <div v-if="v.note_type === 'normal'" class="cv-type-badge">图文</div>
                  <div v-else-if="v.note_type === 'video'" class="cv-type-badge" style="background:rgba(37,99,235,.75)">视频</div>
                </div>

                <!-- 内容 -->
                <div class="cv-body">
                  <div class="cv-title">{{ v.title || '(无标题)' }} <n-tag v-if="v._analysis" size="tiny" type="success" style="margin-left:4px;font-size:10px;">已分析</n-tag></div>
                  <div class="cv-stats">
                    <span class="cstat-s"><n-icon size="12"><HeartOutline /></n-icon>{{ formatNum(v.like_count) }}</span>
                    <span class="cstat-s"><n-icon size="12"><ChatbubbleOutline /></n-icon>{{ formatNum(v.comment_count) }}</span>
                    <span v-if="v.collect_count" class="cstat-s"><n-icon size="12"><BookmarkOutline /></n-icon>{{ formatNum(v.collect_count) }}</span>
                    <span v-if="v.play_count" class="cstat-s"><n-icon size="12"><PlayOutline /></n-icon>{{ formatNum(v.play_count) }}</span>
                    <span v-if="v.like_play_ratio != null" class="cstat-s ratio-badge">赞{{ (v.like_play_ratio*100).toFixed(1) }}%</span>
                    <span v-if="v.collect_play_ratio != null" class="cstat-s ratio-badge">藏{{ (v.collect_play_ratio*100).toFixed(1) }}%</span>
                  </div>
                  <div v-if="v.published_at" class="cv-date"><n-icon size="11"><TimeOutline /></n-icon> {{ formatDate(v.published_at) }}</div>

                  <!-- 文案预览 -->
                  <div v-if="v.description || v.script" class="cv-script">
                    {{ (v.script || v.description || '').slice(0, 80) }}{{ (v.script || v.description || '').length > 80 ? '...' : '' }}
                  </div>

                  <!-- 操作按钮 -->
                  <div class="cv-actions">
                    <n-button
                      size="tiny"
                      secondary
                      :loading="videoAnalyzingIds.has(v.id)"
                      @click.stop="analyzeCreatorVideo(v)"
                    >
                      <template #icon><n-icon><AnalyticsOutline /></n-icon></template>
                      {{ v._analysis ? '重新分析' : '分析爆款' }}
                    </n-button>
                    <n-button
                      v-if="v._analysis"
                      size="tiny"
                      secondary
                      @click.stop="viewCreatorVideoAnalysis(v)"
                    >查看分析</n-button>
                    <n-button
                      size="tiny"
                      secondary
                      :disabled="v.in_docs"
                      @click.stop="addSingleVideoToDocs(v)"
                    >
                      <template #icon><n-icon><FolderOpenOutline /></n-icon></template>
                      {{ v.in_docs ? '已在资料库' : '加入资料库' }}
                    </n-button>
                  </div>
                </div>
              </div>
            </n-gi>
          </n-grid>
        </n-spin>
      </n-drawer-content>
    </n-drawer>

    <!-- 视频爆款分析弹窗（博主视频） -->
    <n-modal v-model:show="showCVAnalysisModal" preset="card" style="width: 720px;">
      <template #header>爆款分析 — {{ currentCVTitle }}</template>
      <div v-if="currentCVAnalysis" class="analysis-modal">

        <!-- 基础数据行 -->
        <div v-if="currentCVVideo" class="cv-anal-meta">
          <span class="cam-item"><n-icon><HeartOutline /></n-icon> {{ formatNum(currentCVVideo.like_count) }} 点赞</span>
          <span class="cam-item"><n-icon><ChatbubbleOutline /></n-icon> {{ formatNum(currentCVVideo.comment_count) }} 评论</span>
          <span v-if="currentCVVideo.collect_count" class="cam-item"><n-icon><BookmarkOutline /></n-icon> {{ formatNum(currentCVVideo.collect_count) }} 收藏</span>
          <span v-if="currentCVVideo.play_count" class="cam-item"><n-icon><PlayOutline /></n-icon> {{ formatNum(currentCVVideo.play_count) }} 播放</span>
          <a v-if="currentCVVideo.video_url" :href="currentCVVideo.video_url" target="_blank" rel="noopener noreferrer" class="cam-link">
            {{ currentCVVideo.note_type !== undefined ? '查看原笔记' : '查看原视频' }}
          </a>
        </div>

        <!-- 互动比率 -->
        <div class="ratio-row">
          <div class="ratio-item">
            <div class="ratio-label">点赞率</div>
            <div class="ratio-value">{{ fmtRatio(currentCVAnalysis.like_play_ratio) }}</div>
          </div>
          <div class="ratio-item">
            <div class="ratio-label">评论率</div>
            <div class="ratio-value">{{ fmtRatio(currentCVAnalysis.comment_play_ratio) }}</div>
          </div>
          <div class="ratio-item">
            <div class="ratio-label">收藏率</div>
            <div class="ratio-value">{{ fmtRatio(currentCVAnalysis.collect_play_ratio) }}</div>
          </div>
        </div>
        
        <n-divider style="margin: 16px 0;" />
        <n-tabs type="line" animated>
          <n-tab-pane name="resonance" tab="点赞共鸣">
            <div class="analysis-text">{{ currentCVAnalysis.resonance_analysis || '暂无' }}</div>
          </n-tab-pane>
          <n-tab-pane name="discussion" tab="讨论钩子">
            <div class="analysis-text">{{ currentCVAnalysis.discussion_analysis || '暂无' }}</div>
          </n-tab-pane>
          <n-tab-pane name="value" tab="收藏价值">
            <div class="analysis-text">{{ currentCVAnalysis.value_analysis || '暂无' }}</div>
          </n-tab-pane>
          <n-tab-pane name="why" tab="爆款诊断">
            <div class="analysis-text analysis-highlight">{{ currentCVAnalysis.why_viral_summary || '暂无' }}</div>
          </n-tab-pane>
          <n-tab-pane name="script" tab="视频文案">
            <div v-if="currentCVVideo && currentCVVideo.script" class="analysis-text cv-script-full">
              <div style="font-size:12px;color:var(--c-primary, #6366f1);margin-bottom:8px;font-weight:500;">语音转录（视频中实际说的话）</div>
              {{ currentCVVideo.script }}
            </div>
            <div v-else class="analysis-text" style="color:#f59e0b;font-size:13px;margin-bottom:12px;">
              尚未获取语音转录。点击「分析爆款」后系统会自动转录视频原声。
            </div>
            <div v-if="currentCVVideo && currentCVVideo.description" style="margin-top:12px;">
              <div style="font-size:12px;color:var(--c-text-4, #94a3b8);margin-bottom:6px;font-weight:500;">博主发布描述（手动填写的文案）</div>
              <div class="analysis-text" style="color:#cbd5e1;font-size:13px;line-height:1.7;">{{ currentCVVideo.description }}</div>
            </div>
          </n-tab-pane>
        </n-tabs>
      </div>
    </n-modal>

    <!-- 添加到资料库弹窗 -->
    <n-modal v-model:show="showAddToDocsModal" preset="card" title="添加到资料库" style="width: 420px;">
      <n-form label-placement="top" :show-feedback="false">
        <n-form-item label="文件夹">
          <n-select
            v-model:value="addToDocsFolder"
            :options="folderOptions"
            filterable
            tag
            placeholder="选择或输入文件夹名（可为空）"
            clearable
          />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showAddToDocsModal = false">取消</n-button>
          <n-button type="primary" :loading="addingToDocs" @click="confirmAddToDocs">确认添加</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, h } from 'vue'
import { useMessage, NPopover, NIcon, useDialog } from 'naive-ui'
import { useRouter } from 'vue-router'
import {
  AddOutline, PeopleOutline, RefreshOutline, ColorPaletteOutline,
  TrashOutline, SearchOutline, SparklesOutline, DocumentOutline,
  FilmOutline, FolderOpenOutline, HeartOutline, ChatbubbleOutline,
  PlayOutline, AnalyticsOutline, VideocamOutline, BookmarkOutline, TimeOutline,
  ImagesOutline, CheckmarkCircleOutline,
} from '@vicons/ionicons5'
import { creatorsApi, analyzerApi, documentsApi } from '../api'
import { useAuthStore } from '../stores/auth.js'

const message = useMessage()
const dialog = useDialog()
const router = useRouter()
const authStore = useAuthStore()
const creators = ref([])
const loading = ref(false)
const activePlatform = ref('all')
const showAddModal = ref(false)
const showAutoModal = ref(false)
const adding = ref(false)
const crawlingId = ref(null)
const analyzingId = ref(null)
const crawlCountMap = ref({})  // creatorId -> crawl count
const intelCardLoading = ref(null)
const showIntelCardModal = ref(false)
const intelCard = ref(null)
const intelCardCreator = ref(null)
const formRef = ref()

// 自动发现状态
const autoForm = ref({ keyword: '', platforms: ['douyin'], limit: 30 })
const autoRunning = ref(false)
const autoTaskId = ref(null)
const autoTask = ref({ status: 'idle', progress: 0, total: 0, log: [], result: null })
let pollTimer = null

const form = ref({ platform: 'douyin', identifier: '' })
const rules = {
  platform: { required: true, message: '请选择平台' },
  identifier: { required: true, message: '请输入账号ID' },
}

// 视频号搜索状态
const weixinSearchKeyword = ref('')
const weixinSearchResults = ref([])
const weixinSearching = ref(false)
const weixinSearched = ref(false)

async function searchWeixinCreators() {
  if (!weixinSearchKeyword.value.trim()) return
  weixinSearching.value = true
  weixinSearched.value = false
  try {
    const { data } = await creatorsApi.searchWeixin(weixinSearchKeyword.value.trim())
    weixinSearchResults.value = data.creators || []
    weixinSearched.value = true
  } catch (e) {
    message.error(e.response?.data?.detail || '搜索失败')
  } finally {
    weixinSearching.value = false
  }
}

function selectWeixinCreator(item) {
  form.value.identifier = item.username
}

function onPlatformChange() {
  form.value.identifier = ''
  weixinSearchKeyword.value = ''
  weixinSearchResults.value = []
  weixinSearched.value = false
}

const platformOptions = [
  { label: '抖音', value: 'douyin' },
  { label: '小红书', value: 'xiaohongshu' },
  { label: '视频号', value: 'weixin' },
]

const idLabel = computed(() => ({
  douyin: '抖音号（unique_id）',
  xiaohongshu: '小红书号 / 主页链接',
  weixin: '视频号用户名',
}[form.value.platform]))

const idPlaceholder = computed(() => ({
  douyin: '例如：douyin_user123',
  xiaohongshu: '例如：xiaohongshu_123 或 https://www.xiaohongshu.com/user/profile/xxx',
  weixin: '例如：v2_060000...@finder',
}[form.value.platform]))

const filteredCreators = computed(() =>
  activePlatform.value === 'all'
    ? creators.value
    : creators.value.filter(c => c.platform === activePlatform.value)
)

async function load() {
  loading.value = true
  try {
    const { data } = await creatorsApi.list()
    creators.value = data
  } finally {
    loading.value = false
  }
}

async function addCreator() {
  try {
    await formRef.value?.validate()
  } catch { return }
  // 试用用户前置检查
  if (authStore.isTrial && creators.value.length >= 1) {
    dialog.warning({
      title: '试用期限制',
      content: '免费体验期仅可添加 1 个博主，升级为正式会员后可不限数量添加。',
      positiveText: '去升级',
      negativeText: '取消',
      onPositiveClick: () => router.push('/pricing'),
    })
    return
  }
  adding.value = true
  try {
    await creatorsApi.add(form.value.platform, form.value.identifier)
    message.success('博主添加成功')
    showAddModal.value = false
    form.value.identifier = ''
    await load()
  } catch (e) {
    message.error(e.response?.data?.detail || '添加失败')
  } finally {
    adding.value = false
  }
}

async function crawl(c) {
  crawlingId.value = c.id
  const count = crawlCountMap.value[c.id] || 30
  try {
    const { data } = await creatorsApi.crawl(c.id, count)
    message.success(data.message)
    await load()
  } catch (e) {
    message.error(e.response?.data?.detail || '抓取失败')
  } finally {
    crawlingId.value = null
  }
}

async function analyzeStyle(c) {
  analyzingId.value = c.id
  try {
    const { data } = await creatorsApi.analyzeStyle(c.id)
    message.success(`风格模版「${data.name}」已生成`)
    // 更新卡片上的风格状态
    c.has_style = true
    c.style_updated_at = new Date().toISOString()
    c.style_name = data.name
  } catch (e) {
    message.error(e.response?.data?.detail || '分析失败，请先抓取内容')
  } finally {
    analyzingId.value = null
  }
}

async function viewIntelCard(c) {
  intelCardCreator.value = c
  showIntelCardModal.value = true
  try {
    const { data } = await analyzerApi.getIntelCard(c.id)
    intelCard.value = data
  } catch {
    intelCard.value = null  // 尚未生成
  }
}

async function generateIntelCard() {
  if (!intelCardCreator.value) return
  intelCardLoading.value = intelCardCreator.value.id
  try {
    const { data } = await analyzerApi.generateIntelCard(intelCardCreator.value.id)
    intelCard.value = data
    message.success('情报卡已生成')
  } catch (e) {
    message.error(e.response?.data?.detail || '生成失败，请先抓取内容')
  } finally {
    intelCardLoading.value = null
  }
}

async function deleteCreator(id) {
  try {
    await creatorsApi.delete(id)
    message.success('已删除')
    await load()
  } catch {
    message.error('删除失败')
  }
}

async function startAutoDiscover() {
  if (!autoForm.value.keyword) return
  autoRunning.value = true
  autoTask.value = { status: 'pending', progress: 0, total: 0, log: [], result: null }
  try {
    const { data } = await creatorsApi.autoDiscoverAndCrawl({
      keyword: autoForm.value.keyword,
      limit: autoForm.value.limit,
      platforms: autoForm.value.platforms,
    })
    autoTaskId.value = data.task_id
    pollTimer = setInterval(pollTask, 1500)
  } catch (e) {
    message.error(e.response?.data?.detail || '启动失败')
    autoRunning.value = false
  }
}

async function pollTask() {
  if (!autoTaskId.value) return
  try {
    const { data } = await creatorsApi.getDiscoverTask(autoTaskId.value)
    autoTask.value = data
    if (data.status === 'done') {
      clearInterval(pollTimer)
      autoRunning.value = false
      message.success(`完成！成功添加 ${data.result?.added || 0} 位博主`)
      await load()
    } else if (data.status === 'error') {
      clearInterval(pollTimer)
      autoRunning.value = false
      message.error('任务执行出错，请查看日志')
    }
  } catch {}
}

function closeAutoModal() {
  if (pollTimer) clearInterval(pollTimer)
  showAutoModal.value = false
  autoTaskId.value = null
  autoTask.value = { status: 'idle', progress: 0, total: 0, log: [], result: null }
  autoForm.value = { keyword: '', platforms: ['douyin'], limit: 30 }
  autoRunning.value = false
}

function statusLabel(s) {
  return { pending: '排队中', running: '进行中', done: '已完成', error: '出错', idle: '待开始' }[s] || s
}

function platformType(p) {
  return { douyin: 'error', xiaohongshu: 'success', weixin: 'warning' }[p] || 'default'
}
function displayUid(c) {
  const uid = c.unique_id || c.username || ''
  if (!uid) return ''
  // 视频号 unique_id 形如 v2_060000...@finder，直接截短展示
  if (c.platform === 'weixin') {
    if (uid.length > 18) return uid.slice(0, 8) + '...' + uid.slice(-6)
    return uid
  }
  return '@' + uid
}
function formatNum(n) {
  if (!n) return '0'
  if (n >= 10000) return (n / 10000).toFixed(1) + 'w'
  return n.toString()
}
// 显示互动比率：null 或 >1（无播放数据）时显示"无数据"
function fmtRatio(v) {
  if (v == null) return '无数据'
  if (v > 1) return '无播放数据'  // play_count=0 时存了点赞数本身，属脏数据
  return (v * 100).toFixed(2) + '%'
}
function formatDate(d) {
  if (!d) return ''
  // 后端存 UTC，若字符串不含时区标识则补 Z 让浏览器正确转为本地时间
  const raw = String(d)
  const dt = new Date(raw.endsWith('Z') || raw.includes('+') ? raw : raw + 'Z')
  return dt.toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

// ── 博主卡片「更多」下拉菜单 ─────────
function getCreatorMenuOptions(c) {
  return [
    {
      label: c.has_style ? '重新提取风格' : '提取风格',
      key: 'style',
      icon: () => h(NIcon, null, { default: () => h(ColorPaletteOutline) }),
    },
    {
      label: '情报卡',
      key: 'intel',
      icon: () => h(NIcon, null, { default: () => h(DocumentOutline) }),
    },
    { type: 'divider' },
    {
      label: '删除博主',
      key: 'delete',
      icon: () => h(NIcon, { color: 'var(--c-error, #ef4444)' }, { default: () => h(TrashOutline) }),
      props: { style: 'color: var(--c-error, #ef4444)' },
    },
  ]
}

function handleCreatorMenu(key, c) {
  if (key === 'style') analyzeStyle(c)
  else if (key === 'intel') viewIntelCard(c)
  else if (key === 'delete') confirmDelete(c)
}

function confirmDelete(c) {
  dialog.warning({
    title: '确认删除',
    content: `确认删除「${c.nickname}」及其所有数据？`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: () => deleteCreator(c.id),
  })
}

onMounted(load)
onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
  if (batchAnalyzePollTimer) clearInterval(batchAnalyzePollTimer)
})

// ── 博主视频抽屉 ───────────────────────────────────────────
const showVideosDrawer = ref(false)
const videosCreator = ref(null)
const creatorVideos = ref([])
const loadingVideos = ref(false)
const selectedVideoIds = ref(new Set())
const videoAnalyzingIds = ref(new Set())
const videoSortKey = ref('like_count')
const showCVAnalysisModal = ref(false)
const currentCVAnalysis = ref(null)
const currentCVVideo = ref(null)   // 当前打开分析弹窗的视频对象
const currentCVTitle = ref('')
const showAddToDocsModal = ref(false)
const addToDocsFolder = ref(null)
const addingToDocs = ref(false)
const batchAnalyzing = ref(false)
const batchAnalyzeProgress = ref({ done: 0, total: 0 })
const batchAnalyzeTask = ref(null)
let batchAnalyzePollTimer = null
const folderOptions = ref([])
const pendingAddVideos = ref([])  // 待添加的视频列表

const sortedVideos = computed(() => {
  const key = videoSortKey.value
  return [...creatorVideos.value].sort((a, b) => {
    const av = a[key] ?? -Infinity
    const bv = b[key] ?? -Infinity
    if (key === 'published_at') {
      return new Date(bv) - new Date(av)
    }
    return bv - av
  })
})

async function viewVideos(c) {
  videosCreator.value = c
  showVideosDrawer.value = true
  selectedVideoIds.value = new Set()
  creatorVideos.value = []
  loadingVideos.value = true
  try {
    const { data } = await creatorsApi.videos(c.id)
    // 加载已有分析结果（持久化）
    creatorVideos.value = data.map(v => ({ ...v, _analysis: v.analysis || null }))
    // 加载文件夹列表
    const { data: folders } = await documentsApi.listFolders()
    folderOptions.value = folders.map(f => ({ label: f, value: f }))
  } catch (e) {
    message.error('加载视频失败')
  } finally {
    loadingVideos.value = false
  }
}

function toggleSelectVideo(v) {
  const s = new Set(selectedVideoIds.value)
  if (s.has(v.id)) s.delete(v.id)
  else s.add(v.id)
  selectedVideoIds.value = s
}

function toggleSelectAllVideos() {
  if (selectedVideoIds.value.size === creatorVideos.value.length && creatorVideos.value.length > 0) {
    selectedVideoIds.value = new Set()
  } else {
    selectedVideoIds.value = new Set(creatorVideos.value.map(v => v.id))
  }
}

async function batchAnalyzeAll() {
  if (!videosCreator.value) return
  batchAnalyzing.value = true
  batchAnalyzeTask.value = null
  try {
    const { data } = await analyzerApi.batchAnalyzeCreatorVideosAsync(videosCreator.value.id, creatorVideos.value.length)
    batchAnalyzeTask.value = { status: 'running', done: 0, total: data.total, success: 0, failed: 0 }
    message.success(`已在后台启动分析 ${data.total} 条视频，可以继续操作或关闭此面板`)
    // 开始轮询进度
    const taskId = data.task_id
    batchAnalyzePollTimer = setInterval(async () => {
      try {
        const { data: taskData } = await analyzerApi.getAnalyzeTask(taskId)
        batchAnalyzeTask.value = taskData
        if (taskData.status === 'done' || taskData.status === 'error') {
          clearInterval(batchAnalyzePollTimer)
          batchAnalyzePollTimer = null
          batchAnalyzing.value = false
          if (taskData.status === 'done') {
            // 刷新视频列表（补充分析结果）
            if (showVideosDrawer.value && videosCreator.value) {
              const { data: freshVideos } = await creatorsApi.videos(videosCreator.value.id)
              creatorVideos.value = freshVideos.map(fv => ({ ...fv, _analysis: fv.analysis || null }))
            }
          }
        }
      } catch {
        clearInterval(batchAnalyzePollTimer)
        batchAnalyzePollTimer = null
        batchAnalyzing.value = false
      }
    }, 3000)
  } catch (e) {
    message.error(e.response?.data?.detail || '启动批量分析失败')
    batchAnalyzing.value = false
  }
}

async function analyzeCreatorVideo(v) {
  const ids = new Set(videoAnalyzingIds.value)
  ids.add(v.id)
  videoAnalyzingIds.value = ids
  try {
    const { data } = await analyzerApi.analyzeVideo(v.id)
    // 分析后后端可能已更新 play_count，重新加载视频列表
    try {
      const { data: freshVideos } = await creatorsApi.videos(videosCreator.value.id)
      creatorVideos.value = freshVideos.map(fv => ({ ...fv, _analysis: fv.analysis || null }))
      // 从刷新后的列表找到当前视频
      const freshV = creatorVideos.value.find(fv => fv.id === v.id)
      if (freshV) {
        freshV._analysis = data
        v = freshV
      }
    } catch (_) { /* 刷新失败不影响展示分析 */ }
    data._has_play = !!(v.play_count && v.play_count > 0)
    v._analysis = data
    currentCVVideo.value = v
    currentCVAnalysis.value = data
    currentCVTitle.value = v.title || '(无标题)'
    showCVAnalysisModal.value = true
  } catch (e) {
    message.error(e.response?.data?.detail || '分析失败')
  } finally {
    const ids2 = new Set(videoAnalyzingIds.value)
    ids2.delete(v.id)
    videoAnalyzingIds.value = ids2
  }
}

function viewCreatorVideoAnalysis(v) {
  currentCVVideo.value = v
  currentCVAnalysis.value = v._analysis
  currentCVTitle.value = v.title || '(无标题)'
  showCVAnalysisModal.value = true
}

async function addSingleVideoToDocs(v) {
  pendingAddVideos.value = [v]
  showAddToDocsModal.value = true
}

function batchAddToDocs() {
  pendingAddVideos.value = creatorVideos.value.filter(v => selectedVideoIds.value.has(v.id))
  showAddToDocsModal.value = true
}

async function confirmAddToDocs() {
  if (!pendingAddVideos.value.length) return
  addingToDocs.value = true
  let ok = 0, fail = 0
  for (const v of pendingAddVideos.value) {
    const content = v.script || v.description || v.title || ''
    if (!content.trim()) { fail++; continue }
    try {
      await documentsApi.addText({
        name: `[${videosCreator.value?.nickname}] ${(v.title || '').slice(0, 40) || '视频文案'}`,
        content,
        folder_name: addToDocsFolder.value || null,
        source_type: 'creator_video',
        source_ref: v.video_id,
      })
      ok++
    } catch { fail++ }
  }
  addingToDocs.value = false
  showAddToDocsModal.value = false
  pendingAddVideos.value = []
  if (ok) {
    // 标记已加入状态
    for (const v of creatorVideos.value) {
      if (selectedVideoIds.value.has(v.id)) v.in_docs = true
    }
    message.success(`已添加 ${ok} 条视频文案到资料库`, {
      duration: 4000,
      action: h =>
        h('span', { style: 'color:#6366f1;cursor:pointer;font-size:13px;', onClick: () => router.push('/documents') }, '去查看 →')
    })
  }
  if (fail) message.warning(`${fail} 条因无文案内容跳过`)
  selectedVideoIds.value = new Set()
}
</script>

<style scoped>
/* 视频号搜索结果 */
.weixin-search-results {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid var(--c-border, rgba(255,255,255,.08));
  border-radius: 8px;
  margin-top: -8px;
}
.weixin-result-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  cursor: pointer;
  transition: background .15s;
  border-bottom: 1px solid var(--c-border, rgba(255,255,255,.04));
}
.weixin-result-item:last-child { border-bottom: none; }
.weixin-result-item:hover { background: rgba(99,102,241,.08); }
.weixin-result-item.active { background: rgba(99,102,241,.12); }
.weixin-result-info { flex: 1; min-width: 0; }
.weixin-result-name { font-size: 14px; font-weight: 500; color: var(--c-text-1, #111827); }
.weixin-result-desc { font-size: 12px; color: var(--c-text-3, #6b7280); margin-top: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.weixin-avatar {
  width: 40px; height: 40px; border-radius: 50%; overflow: hidden;
  background: rgba(99,102,241,.15); flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
}
.weixin-avatar-img { width: 100%; height: 100%; object-fit: cover; display: block; }
.weixin-avatar-fallback { font-size: 15px; font-weight: 700; color: var(--c-primary, #6366f1); }

.creator-card {
  background: var(--c-bg-elevated, #fff);
  border: 1px solid var(--c-border, rgba(0,0,0,.06));
  border-radius: var(--radius-lg, 12px);
  padding: 18px;
  transition: border-color var(--duration-fast, .2s), box-shadow var(--duration-fast, .2s), transform var(--duration-fast, .2s);
  box-shadow: var(--shadow-sm, 0 1px 2px rgba(0,0,0,.04));
  position: relative;
  overflow: hidden;
}
.creator-card:hover {
  border-color: var(--c-primary-light, rgba(37,99,235,.25));
  box-shadow: 0 4px 20px rgba(37,99,235,.1), 0 1px 4px rgba(0,0,0,.04);
  transform: translateY(-2px);
}
.card-deco {
  position: absolute; top: 0; right: 0;
  width: 130px; height: 85px;
  pointer-events: none;
  opacity: 0.7;
  transition: opacity 0.2s;
}
.creator-card:hover .card-deco { opacity: 1; }
.creator-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.creator-info { flex: 1; min-width: 0; }
.creator-name { font-size: 15px; font-weight: 600; color: var(--c-text-1, #0f172a); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.creator-uid { font-size: 12px; color: var(--c-text-4, #94a3b8); }
.creator-stats { display: flex; gap: 0; margin-bottom: 16px; background: var(--c-bg-soft, #f8fafc); border-radius: 8px; }
.cstat { flex: 1; text-align: center; padding: 10px 0; border-right: 1px solid #e8eef4; }
.cstat:last-child { border-right: none; }
.cstat-val { font-size: 15px; font-weight: 700; color: var(--c-text-1, #0f172a); font-variant-numeric: tabular-nums; }
.cstat-label { font-size: 11px; color: var(--c-text-4, #94a3b8); margin-top: 2px; }
.creator-actions { display: flex; flex-direction: column; gap: 8px; }
.ca-row { display: flex; gap: 8px; align-items: center; }
.ca-btn-primary { flex: 1; justify-content: center; }
.ca-btn-secondary { flex: 1; justify-content: center; }
.ca-row-secondary { border-top: 1px solid var(--c-border, #e8eef4); padding-top: 8px; color: var(--c-text-3, #64748b); }
.last-crawled { font-size: 11px; color: #cbd5e1; margin-top: 10px; display: flex; justify-content: space-between; align-items: center; }
.style-badge { color: var(--c-success, #22c55e); font-weight: 500; }

/* ── 情报卡 ── */
.intel-section {
  font-size: 14px;
  color: #334155;
  line-height: 1.8;
  padding: 8px 0;
  white-space: pre-wrap;
}
.intel-tags { padding: 8px 0; }
.pain-item { background: #f8fafc; border-radius: 8px; padding: 12px 14px; margin-bottom: 10px; }
.pain-title { font-size: 14px; font-weight: 600; color: var(--c-text-1, #0f172a); margin-bottom: 4px; }
.pain-evidence { font-size: 12px; color: #64748b; line-height: 1.6; }
.intel-updated { font-size: 11px; color: #94a3b8; text-align: right; margin-top: 12px; }
.empty-intel { padding: 40px 0; }
.empty-state-big { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 80px 0; color: #cbd5e1; }
.auto-progress { margin-top: 16px; padding: 16px; background: #f8fafc; border-radius: 10px; border: 1px solid #e8eef4; }
.progress-status { display: flex; align-items: center; margin-bottom: 10px; }
.progress-log { max-height: 100px; overflow-y: auto; font-size: 12px; color: #94a3b8; line-height: 1.8; }
.log-line { padding: 1px 0; }
.auto-result-summary { display: flex; gap: 16px; margin-top: 14px; padding-top: 14px; border-top: 1px solid #e8eef4; justify-content: space-around; }

/* ── 博主视频卡片 ── */
.cv-card {
  background: #fff;
  border: 1px solid rgba(0,0,0,.06);
  border-radius: 10px;
  overflow: hidden;
  cursor: pointer;
  transition: border-color .2s, box-shadow .15s;
  position: relative;
}
.cv-card:hover { border-color: rgba(99,102,241,.35); box-shadow: 0 3px 12px rgba(99,102,241,.1); }
.cv-card.selected { border-color: var(--c-primary, #6366f1); background: rgba(99,102,241,.03); }
.cv-select { position: absolute; top: 8px; left: 8px; z-index: 2; }
.cv-cover { width: 100%; height: 130px; background: #f1f5f9; position: relative; overflow: hidden; display: flex; align-items: center; justify-content: center; }
.cv-type-badge { position: absolute; top: 6px; left: 6px; font-size: 10px; line-height: 1; padding: 2px 6px; border-radius: 4px; background: rgba(0,0,0,.55); color: #fff; }
.cv-cover-ph { display: flex; align-items: center; justify-content: center; width: 100%; height: 100%; }
.cv-body { padding: 10px; }
.cv-title { font-size: 13px; font-weight: 500; color: var(--c-text-1, #0f172a); display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; line-height: 1.4; margin-bottom: 6px; }
.cv-stats { display: flex; gap: 10px; margin-bottom: 6px; }
.cstat-s { display: flex; align-items: center; gap: 3px; font-size: 12px; color: var(--c-text-4, #94a3b8); font-variant-numeric: tabular-nums; }
.ratio-badge { background: rgba(99,102,241,.1); color: var(--c-primary, #6366f1); border-radius: 4px; padding: 0 4px; font-size: 11px; }

/* 发布时间 */
.cv-date { display: flex; align-items: center; gap: 3px; font-size: 11px; color: #cbd5e1; margin-top: 4px; }

/* 批量分析操作栏 */
.batch-action-bar { display: flex; align-items: center; gap: 12px; padding: 12px 0 8px; border-bottom: 1px solid #e2e8f0; margin-bottom: 8px; flex-wrap: wrap; }
.batch-progress { font-size: 13px; color: var(--c-primary, #6366f1); animation: pulse 1.5s ease-in-out infinite; }
.batch-task-progress { display: flex; align-items: center; gap: 10px; flex: 1; min-width: 240px; }
.batch-task-text { font-size: 12px; color: rgba(255,255,255,0.55); white-space: nowrap; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

/* 排序工具栏 */
.sort-toolbar { display: flex; align-items: center; gap: 10px; padding: 10px 0 12px; flex-wrap: wrap; }
.sort-label { font-size: 12px; color: #94a3b8; white-space: nowrap; }

/* 分析弹窗基础数据行 */
.cv-anal-meta { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; background: #f8fafc; border-radius: 8px; padding: 10px 14px; margin-bottom: 14px; }
.cam-item { display: flex; align-items: center; gap: 4px; font-size: 13px; color: #475569; }
.cam-link { font-size: 13px; color: var(--c-primary, #6366f1); text-decoration: none; margin-left: auto; }
.cam-link:hover { text-decoration: underline; }

/* 原视频文案全文 */
.cv-script-full { font-size: 13px; line-height: 1.8; color: #334155; white-space: pre-wrap; max-height: 320px; overflow-y: auto; }
.cv-script { font-size: 12px; color: #64748b; line-height: 1.5; margin-bottom: 8px; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; background: #f8fafc; border-radius: 6px; padding: 6px 8px; }
.cv-actions { display: flex; gap: 6px; flex-wrap: wrap; }

/* ── 视频分析弹窗 ── */
.analysis-modal { padding-bottom: 4px; }
.ratio-row { display: flex; gap: 12px; justify-content: space-between; }
.ratio-item { flex: 1; text-align: center; background: #f8fafc; border-radius: 10px; padding: 12px 6px; }
.ratio-label { font-size: 12px; color: #94a3b8; margin-bottom: 4px; }
.ratio-value { font-size: 20px; font-weight: 700; color: var(--c-text-1, #0f172a); font-variant-numeric: tabular-nums; }
.analysis-text { font-size: 14px; color: #334155; line-height: 1.8; padding: 8px 0; white-space: pre-wrap; }
.analysis-highlight { background: #fefce8; border-left: 3px solid #eab308; padding: 12px 16px; border-radius: 6px; }
</style>
