"""
情报分析服务
- 博主情报卡（四维度AI分析）
- 爆款视频互动比分析引擎
"""
import json
import asyncio
import anthropic
from datetime import datetime
from sqlalchemy.orm import Session
from models import Creator, CreatorVideo, CreatorIntelCard, VideoAnalysis, Topic
from config import settings


# ─── 互动比评级阈值（行业经验值）────────────────────────────────
RATIO_THRESHOLDS = {
    "like_play":    {"high": 0.05, "medium": 0.02},   # 点赞/播放：>5%=高, 2-5%=中
    "comment_play": {"high": 0.01, "medium": 0.005},  # 评论/播放：>1%=高, 0.5-1%=中
    "collect_play": {"high": 0.03, "medium": 0.01},   # 收藏/播放：>3%=高, 1-3%=中
}


def _rate_ratio(value, key: str) -> str:
    """返回 high / medium / low，None 时返回 low"""
    if value is None:
        return "low"
    t = RATIO_THRESHOLDS.get(key, {})
    if value >= t.get("high", 1):
        return "high"
    if value >= t.get("medium", 0.5):
        return "medium"
    return "low"


class AnalyzerService:

    def __init__(self):
        if settings.use_deepseek:
            self.client = anthropic.Anthropic(
                api_key=settings.deepseek_api_key,
                base_url=settings.deepseek_base_url
            )
            self.model_name = settings.deepseek_model
        else:
            self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            self.model_name = "claude-sonnet-4-20250514"

    def _call_ai(self, prompt: str, max_tokens: int = 1500) -> str:
        """同步调用AI（供 run_in_executor 包装）"""
        msg = self.client.messages.create(
            model=self.model_name,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text.strip()

    async def _async_ai(self, prompt: str, max_tokens: int = 1500) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self._call_ai(prompt, max_tokens))

    # ════════════════════════════════════════════════
    #  情报卡生成
    # ════════════════════════════════════════════════

    async def generate_intel_card(self, db: Session, creator_id: int, tenant_id: int = None) -> dict:
        """生成/刷新博主情报卡（深度AI分析），按租户隔离"""
        creator = db.query(Creator).filter(Creator.id == creator_id).first()
        if not creator:
            raise ValueError("博主不存在")

        # 取点赞量前20的视频
        videos = (
            db.query(CreatorVideo)
            .filter(CreatorVideo.creator_id == creator_id)
            .order_by(CreatorVideo.like_count.desc())
            .limit(20)
            .all()
        )
        if not videos:
            raise ValueError("该博主暂无视频数据，请先爬取")

        # 区分爆款（前1/3）和普通视频（后2/3），用于对比分析
        split_idx = max(1, len(videos) // 3)
        hot_videos = videos[:split_idx]
        normal_videos = videos[split_idx:]

        def _build_video_line(v, include_script=True):
            """构造单条视频摘要，优先使用语音转录"""
            line = f"- 【{(v.like_count or 0):,}赞 | {(v.comment_count or 0):,}评 | {(v.play_count or 0):,}播】{v.title or '(无标题)'}"
            script = (v.script or "").strip()
            desc = (v.description or "").strip()
            if include_script and script:
                line += f"\n  口播内容：{script[:300]}"
            elif desc:
                line += f"\n  发布描述：{desc[:100]}"
            return line

        hot_text = "\n".join([_build_video_line(v) for v in hot_videos])
        normal_text = "\n".join([_build_video_line(v, include_script=False) for v in normal_videos])

        # 计算数据指标
        total_likes = sum(v.like_count or 0 for v in videos)
        total_plays = sum(v.play_count or 0 for v in videos)
        avg_likes = total_likes // len(videos) if videos else 0
        hot_avg_likes = sum(v.like_count or 0 for v in hot_videos) // len(hot_videos) if hot_videos else 0
        normal_avg_likes = sum(v.like_count or 0 for v in normal_videos) // len(normal_videos) if normal_videos else 0
        durations = [v.duration for v in videos if v.duration]
        avg_duration = sum(durations) // len(durations) if durations else 0

        # 提取评论区痛点
        comment_samples = []
        for v in videos[:10]:
            top_comments = v.top_comments if isinstance(v.top_comments, list) else []
            if not top_comments and v.raw_data and isinstance(v.raw_data, dict):
                top_comments = v.raw_data.get("top_comments", [])
            for c in top_comments[:3]:
                if isinstance(c, dict) and c.get("content"):
                    comment_samples.append(f"「{c['content'][:60]}」(赞{c.get('likes', c.get('digg_count', 0))})")
        comment_text = "\n".join(comment_samples[:25]) if comment_samples else "暂无评论数据"

        prompt = f"""你是一位资深的短视频运营策略顾问（10年经验），请对以下博主进行专业级情报分析。

## 博主基本信息
- 昵称：{creator.nickname}
- 平台：{creator.platform}
- 粉丝数：{(creator.follower_count or 0):,}
- 简介：{creator.bio or '无'}

## 数据概览
- 视频样本：{len(videos)} 条
- 平均点赞：{avg_likes:,}
- 爆款平均点赞：{hot_avg_likes:,}（前{len(hot_videos)}条）
- 普通平均点赞：{normal_avg_likes:,}（后{len(normal_videos)}条）
- 平均时长：{avg_duration}秒
- 总播放量：{total_plays:,}

## 爆款视频（互动率最高的 {len(hot_videos)} 条）
{hot_text}

## 普通视频（对比参考）
{normal_text}

## 评论区高赞留言（观众真实反馈）
{comment_text}

## 分析任务
请从以下维度深入分析，注意**爆款视频和普通视频的差异**，找出这个博主成功的关键因素。以JSON格式输出：

{{
  "positioning": "账号定位分析（150字以内）：目标人群画像、内容赛道、差异化切入点、核心价值主张",
  "video_style": "视频风格特征（150字以内）：表达方式（口播/剧情/混剪）、语言风格、节奏特点、视觉风格、标志性习惯",
  "common_topics": ["高频内容主题1", "主题2", "主题3", "主题4", "主题5"],
  "viral_formula": "爆款公式（100字以内）：对比爆款和普通视频，总结这个博主的爆款是怎么做出来的，什么选题+什么结构+什么表达=容易爆",
  "comment_pain_points": [
    {{"pain": "受众核心痛点1", "evidence": "评论证据", "content_opportunity": "可以做什么内容来回应这个痛点"}},
    {{"pain": "痛点2", "evidence": "证据", "content_opportunity": "内容机会"}}
  ],
  "strengths": ["核心竞争优势1", "优势2", "优势3"],
  "weaknesses": ["可改进的地方1（如果有的话）"],
  "summary": "综合情报摘要（200字以内）：这个博主为什么火、核心竞争力、最值得模仿的3个点、以及需要注意的风险"
}}"""

        raw = await self._async_ai(prompt, max_tokens=3000)
        clean = raw.replace("```json", "").replace("```", "").strip()
        try:
            data = json.loads(clean)
        except Exception:
            raise ValueError(f"情报卡AI解析失败: {clean[:200]}")

        # 写入/更新数据库（按租户隔离，同一博主不同租户各有情报卡）
        filters = [CreatorIntelCard.creator_id == creator_id, CreatorIntelCard.tenant_id == tenant_id]
        card = db.query(CreatorIntelCard).filter(*filters).first()
        if card:
            card.positioning = data.get("positioning", "")
            card.video_style = data.get("video_style", "")
            card.common_topics = data.get("common_topics", [])
            card.comment_pain_points = data.get("comment_pain_points", [])
            card.summary = data.get("summary", "")
            card.raw_analysis = clean
            card.updated_at = datetime.utcnow()
        else:
            card = CreatorIntelCard(
                creator_id=creator_id,
                tenant_id=tenant_id,
                positioning=data.get("positioning", ""),
                video_style=data.get("video_style", ""),
                common_topics=data.get("common_topics", []),
                comment_pain_points=data.get("comment_pain_points", []),
                summary=data.get("summary", ""),
                raw_analysis=clean,
            )
            db.add(card)
        db.commit()
        db.refresh(card)
        return self._card_to_dict(card)

    def get_intel_card(self, db: Session, creator_id: int, tenant_id: int = None) -> dict | None:
        filters = [CreatorIntelCard.creator_id == creator_id, CreatorIntelCard.tenant_id == tenant_id]
        card = db.query(CreatorIntelCard).filter(*filters).first()
        return self._card_to_dict(card) if card else None

    def _card_to_dict(self, card: CreatorIntelCard) -> dict:
        return {
            "id": card.id,
            "creator_id": card.creator_id,
            "positioning": card.positioning,
            "video_style": card.video_style,
            "common_topics": card.common_topics or [],
            "comment_pain_points": card.comment_pain_points or [],
            "summary": card.summary,
            "created_at": card.created_at,
            "updated_at": card.updated_at,
        }

    # ════════════════════════════════════════════════
    #  爆款视频分析
    # ════════════════════════════════════════════════

    def _compute_ratios(self, like_count: int, comment_count: int, collect_count: int, play_count: int) -> dict:
        """计算三互动比"""
        if not play_count or play_count <= 0:
            return {
                "like_play_ratio": None,
                "comment_play_ratio": None,
                "collect_play_ratio": None,
                "like_play_level": "unknown",
                "comment_play_level": "unknown",
                "collect_play_level": "unknown",
            }
        lp = like_count / play_count
        cp = comment_count / play_count
        kp = collect_count / play_count
        return {
            "like_play_ratio": round(lp, 6),
            "comment_play_ratio": round(cp, 6),
            "collect_play_ratio": round(kp, 6),
            "like_play_level": _rate_ratio(lp, "like_play"),
            "comment_play_level": _rate_ratio(cp, "comment_play"),
            "collect_play_level": _rate_ratio(kp, "collect_play"),
        }

    async def analyze_video_viral(
        self,
        db: Session,
        *,
        video_id: int = None,
        topic_id: int = None,
        tenant_id: int = None,
    ) -> dict:
        """对单条视频进行爆款三维分析，按租户隔离"""
        # 获取视频数据
        if video_id:
            v = db.query(CreatorVideo).filter(CreatorVideo.id == video_id).first()
            if not v:
                raise ValueError("视频不存在")

            # ── 抖音: 拉取真实播放量（详情接口不返回 play_count） ──
            if v.platform == "douyin" and v.video_id and not (v.play_count and v.play_count > 0):
                try:
                    from services.tikhub import tikhub
                    raw_stats = await tikhub.douyin_fetch_video_statistics([v.video_id])
                    stats_list = raw_stats.get("data", {}).get("statistics_list", [])
                    if stats_list:
                        s = stats_list[0]
                        real_play = s.get("play_count", 0)
                        if real_play and real_play > 0:
                            v.play_count = real_play
                            if s.get("digg_count"):
                                v.like_count = s["digg_count"]
                            if s.get("collect_count"):
                                v.collect_count = s["collect_count"]
                            db.commit()
                            db.refresh(v)
                            print(f"[Analyzer] 拉取到真实播放量: {real_play}")
                except Exception as _e:
                    print(f"[Analyzer] 拉取播放量失败: {_e}")

            title = v.title or ""
            description = v.description or ""
            like_count = v.like_count or 0
            comment_count = v.comment_count or 0
            collect_count = v.collect_count or 0
            play_count = v.play_count or 0

            # ── 懒加载：script 为空或过短时重新获取 ──
            existing_script = (v.script or "").strip()
            existing_script_len = len(existing_script)
            duration_s = v.duration or 60
            expected_min_chars = int(duration_s * 2)
            need_script = existing_script_len < max(200, expected_min_chars)

            if v.platform == "douyin" and v.video_id and need_script:
                try:
                    from services.topic_hunter import topic_hunter
                    detail = await topic_hunter.fetch_video_detail(
                        "douyin", v.video_id, comment_count=20
                    )
                    fetched_script = detail.get("script", "").strip()
                    fetched_comments = detail.get("top_comments", [])
                    if fetched_script and len(fetched_script) > existing_script_len:
                        v.script = fetched_script
                        print(f"[Analyzer] 抖音文案更新: {existing_script_len} → {len(fetched_script)} 字")
                    if fetched_comments:
                        v.top_comments = fetched_comments
                    db.commit()
                    db.refresh(v)
                except Exception as _e:
                    print(f"[Analyzer] 抖音懒加载失败 (video_id={v.video_id}): {_e}")

            elif v.platform == "weixin" and v.video_id and need_script:
                try:
                    from services.tikhub import tikhub as _th
                    from services.transcribe import transcribe_service
                    # 先尝试用已存的 video_url，不行再调详情接口
                    play_url = (v.video_url or "").strip()
                    if not play_url:
                        raw_detail = await _th.wechat_channels_get_video_detail(v.video_id)
                        detail_data = raw_detail.get("data", {}) or {}
                        # 详情接口的视频对象通常在 data.object
                        obj = detail_data.get("object") or detail_data
                        od = obj.get("object_desc", {})
                        media = od.get("media", [{}])
                        first_media = media[0] if media else {}
                        play_url = (
                            first_media.get("url")
                            or first_media.get("play_url")
                            or (first_media.get("url_info") or {}).get("url", "")
                            or ""
                        )
                        if play_url:
                            v.video_url = play_url  # 顺带补存
                    if play_url:
                        print(f"[Analyzer] 视频号转录 (video_id={v.video_id}) ...")
                        text = await transcribe_service.transcribe_from_url(play_url, v.video_id)
                        if text and len(text) > existing_script_len:
                            v.script = text
                            print(f"[Analyzer] 视频号转录完成: {len(text)} 字")
                    db.commit()
                    db.refresh(v)
                except Exception as _e:
                    print(f"[Analyzer] 视频号转录失败 (video_id={v.video_id}): {_e}")

            # 视频文案（优先使用语音转录，其次用 description）
            raw_script = (v.script or "").strip()
            script = raw_script if (raw_script and raw_script != title and raw_script != description) else ""
            top_comments = v.top_comments or []
        elif topic_id:
            t = db.query(Topic).filter(Topic.id == topic_id).first()
            if not t:
                raise ValueError("选题不存在")
            title = t.title or ""
            description = t.description or ""
            like_count = t.like_count or 0
            comment_count = t.comment_count or 0
            collect_count = getattr(t, 'collect_count', None) or 0
            play_count = t.play_count or 0

            # 视频原声文案（排除旧数据中和标题相同的情况）
            raw_script = (t.script or "").strip()
            script = raw_script if (raw_script and raw_script != title and raw_script != description) else ""

            # 热门评论
            top_comments = t.top_comments or []
        else:
            raise ValueError("必须提供 video_id 或 topic_id")

        # play_count=0 时，优先使用已存储的互动比字段
        if play_count == 0 and video_id:
            # 优先查 VideoAnalysis 里的有效比率，其次看 CreatorVideo 字段
            _va_filters = [VideoAnalysis.video_id == video_id]
            _va_filters.append(VideoAnalysis.tenant_id == tenant_id)
            _existing_va = db.query(VideoAnalysis).filter(*_va_filters).first()
            def _valid(x): return x is not None and 0 < x <= 1
            if _existing_va and _valid(_existing_va.like_play_ratio):
                _lp = _existing_va.like_play_ratio
                _cp = _existing_va.comment_play_ratio if _valid(_existing_va.comment_play_ratio) else 0
                _kp = _existing_va.collect_play_ratio if _valid(_existing_va.collect_play_ratio) else 0
            elif _valid(v.like_play_ratio):
                _lp = v.like_play_ratio
                _cp = v.comment_play_ratio if _valid(v.comment_play_ratio) else 0
                _kp = v.collect_play_ratio if _valid(v.collect_play_ratio) else 0
            else:
                # play_count=0 时，like_count/(like_count*20) = 1/20 = 5% 恒定，无区分度
                # like_play_ratio 置 None；comment/collect 用 like*20 估算仍有区分度
                _base = like_count * 20 if like_count > 0 else 1
                _lp = None
                _cp = round(comment_count / _base, 6)
                _kp = round(collect_count / _base, 6)
            ratios = {
                "like_play_ratio": _lp,
                "comment_play_ratio": _cp,
                "collect_play_ratio": _kp,
                "like_play_level": _rate_ratio(_lp, "like_play"),
                "comment_play_level": _rate_ratio(_cp, "comment_play"),
                "collect_play_level": _rate_ratio(_kp, "collect_play"),
            }
        elif play_count == 0 and topic_id:
            stored_lp = getattr(t, 'like_play_ratio', None)
            if stored_lp:
                ratios = {
                    "like_play_ratio": stored_lp,
                    "comment_play_ratio": getattr(t, 'comment_play_ratio', 0) or 0,
                    "collect_play_ratio": getattr(t, 'collect_play_ratio', 0) or 0,
                    "like_play_level": _rate_ratio(stored_lp, "like_play"),
                    "comment_play_level": _rate_ratio(getattr(t, 'comment_play_ratio', 0) or 0, "comment_play"),
                    "collect_play_level": _rate_ratio(getattr(t, 'collect_play_ratio', 0) or 0, "collect_play"),
                }
            else:
                # play_count 和存储比率都没有，无法计算，置为 None
                ratios = {
                    "like_play_ratio": None, "comment_play_ratio": None, "collect_play_ratio": None,
                    "like_play_level": "low", "comment_play_level": "low", "collect_play_level": "low",
                }
        else:
            ratios = self._compute_ratios(like_count, comment_count, collect_count, play_count)

        def _fmt_ratio(v, key):
            if v is None:
                return "N/A"
            return f"{v*100:.2f}%({ratios[key+'_level']})"

        # ── 构建内容区块 ──────────────────────────────────
        # 视频文案（优先使用语音转录，否则用博主描述）
        if script:
            content_section = f"\n## 视频原声文案（语音转录，真实说话内容）\n{script[:800]}"
        elif description:
            content_section = f"\n## 视频文案（创作者描述）\n{description[:300]}"
        else:
            content_section = ""

        # 热门评论
        comments_section = ""
        if top_comments:
            lines = []
            for c in top_comments[:10]:
                if isinstance(c, dict) and c.get("content"):
                    lines.append(f"  - 【{c.get('likes', 0)}赞】{c['content'][:80]}")
            if lines:
                comments_section = "\n## 热门评论区（高赞评论样本）\n" + "\n".join(lines)

        has_rich_content = bool(content_section or comments_section)

        prompt = f"""你是一位资深短视频爆款拆解专家，请深度分析这条视频为什么能爆，重点基于视频原声文案内容（博主实际说的话）进行分析。

## 基础数据
标题：{title}
数据：播放{play_count:,} / 点赞{like_count:,} / 评论{comment_count:,} / 收藏{collect_count:,}
互动比：点赞率{_fmt_ratio(ratios['like_play_ratio'], 'like_play')} | 评论率{_fmt_ratio(ratios['comment_play_ratio'], 'comment_play')} | 收藏率{_fmt_ratio(ratios['collect_play_ratio'], 'collect_play')}
{content_section}{comments_section}

## 分析任务
{"请基于视频原声文案和评论数据" if has_rich_content else "请基于标题和互动数据"}，从四个维度进行爆款深度拆解，以JSON格式输出：

{{
  "resonance_analysis": "【点赞共鸣分析】博主在视频中说了什么观点/金句/共鸣点，让观众产生强烈认同而点赞？找出最有力的表达，说明为什么触动人心。（100-150字）",
  "discussion_analysis": "【评论讨论分析】视频中哪部分内容/话题引发了观众去评论区讨论？是争议点、情感共鸣、互动留言引导，还是引起强烈情绪的内容？结合热评数据分析。（100-150字）",
  "value_analysis": "【收藏价值分析】视频提供了哪些值得收藏的具体知识、操作技巧或实用信息？哪些具体内容和知识密度让人觉得以后用得上？（100-150字）",
  "why_viral_summary": "【爆款综合诊断】\n核心话题：___\n关键观点：___\n金句/高光时刻：___（直接引用视频原话）\n共鸣点：___\n讨论钩子：___\n知识价值点：___\n最值得复制的做法：___（150字以内）"
}}"""

        raw = await self._async_ai(prompt, max_tokens=1200)
        clean = raw.replace("```json", "").replace("```", "").strip()
        try:
            ai_data = json.loads(clean)
        except Exception:
            ai_data = {
                "resonance_analysis": raw[:200],
                "discussion_analysis": "",
                "value_analysis": "",
                "why_viral_summary": raw[:300],
            }

        # 保存 / 更新分析记录（按租户隔离）
        existing = None
        if video_id:
            _f = [VideoAnalysis.video_id == video_id, VideoAnalysis.tenant_id == tenant_id]
            existing = db.query(VideoAnalysis).filter(*_f).first()
        elif topic_id:
            _f = [VideoAnalysis.topic_id == topic_id, VideoAnalysis.tenant_id == tenant_id]
            existing = db.query(VideoAnalysis).filter(*_f).first()

        raw_snapshot = {
            "title": title,
            "play_count": play_count,
            "like_count": like_count,
            "comment_count": comment_count,
            "collect_count": collect_count,
        }

        if existing:
            # 只在新计算的比率有效时才更新，避免用 None 覆盖已有的好数据
            if ratios["like_play_ratio"] is not None:
                existing.like_play_ratio = ratios["like_play_ratio"]
                existing.comment_play_ratio = ratios["comment_play_ratio"]
                existing.collect_play_ratio = ratios["collect_play_ratio"]
            existing.resonance_analysis = ai_data.get("resonance_analysis", "")
            existing.discussion_analysis = ai_data.get("discussion_analysis", "")
            existing.value_analysis = ai_data.get("value_analysis", "")
            existing.why_viral_summary = ai_data.get("why_viral_summary", "")
            existing.raw_data = raw_snapshot
            analysis = existing
        else:
            analysis = VideoAnalysis(
                video_id=video_id,
                topic_id=topic_id,
                tenant_id=tenant_id,
                like_play_ratio=ratios["like_play_ratio"],
                comment_play_ratio=ratios["comment_play_ratio"],
                collect_play_ratio=ratios["collect_play_ratio"],
                resonance_analysis=ai_data.get("resonance_analysis", ""),
                discussion_analysis=ai_data.get("discussion_analysis", ""),
                value_analysis=ai_data.get("value_analysis", ""),
                why_viral_summary=ai_data.get("why_viral_summary", ""),
                raw_data=raw_snapshot,
            )
            db.add(analysis)

        # 同步写回 CreatorVideo 的互动比字段（只写有效值）
        if video_id and ratios["like_play_ratio"] is not None:
            v.like_play_ratio = ratios["like_play_ratio"]
            v.comment_play_ratio = ratios["comment_play_ratio"]
            v.collect_play_ratio = ratios["collect_play_ratio"]

        db.commit()
        db.refresh(analysis)

        result = self._analysis_to_dict(analysis)
        # 用计算出的 ratios 补充 level 信息，比率值以 analysis 记录为准（保留有效数据）
        result["like_play_level"] = ratios.get("like_play_level", "unknown")
        result["comment_play_level"] = ratios.get("comment_play_level", "unknown")
        result["collect_play_level"] = ratios.get("collect_play_level", "unknown")
        return result

    async def batch_analyze_videos(self, db: Session, video_ids: list[int], tenant_id: int = None) -> list[dict]:
        """批量分析视频（逐条，带间隔防限流）。
        已有有效分析记录（why_viral_summary 非空）的视频直接复用，不重复调用 AI。
        """
        results = []
        for vid in video_ids:
            try:
                # 复用已有分析，节省 AI API 调用
                _f = [
                    VideoAnalysis.video_id == vid,
                    VideoAnalysis.why_viral_summary != None,
                    VideoAnalysis.why_viral_summary != "",
                    VideoAnalysis.tenant_id == tenant_id,
                ]
                existing = db.query(VideoAnalysis).filter(*_f).first()
                if existing:
                    r = self._analysis_to_dict(existing)
                    r["cached"] = True
                    results.append(r)
                    continue
                r = await self.analyze_video_viral(db, video_id=vid, tenant_id=tenant_id)
                results.append(r)
                await asyncio.sleep(0.5)
            except Exception as e:
                results.append({"video_id": vid, "error": str(e)})
        return results

    def get_video_analysis(self, db: Session, video_id: int, tenant_id: int = None) -> dict | None:
        _f = [VideoAnalysis.video_id == video_id, VideoAnalysis.tenant_id == tenant_id]
        a = db.query(VideoAnalysis).filter(*_f).first()
        if not a:
            return None
        ratios = self._compute_ratios(
            a.raw_data.get("like_count", 0) if a.raw_data else 0,
            a.raw_data.get("comment_count", 0) if a.raw_data else 0,
            a.raw_data.get("collect_count", 0) if a.raw_data else 0,
            a.raw_data.get("play_count", 1) if a.raw_data else 1,
        )
        return {**self._analysis_to_dict(a), **ratios}

    def get_topic_analysis(self, db: Session, topic_id: int, tenant_id: int = None) -> dict | None:
        _f = [VideoAnalysis.topic_id == topic_id, VideoAnalysis.tenant_id == tenant_id]
        a = db.query(VideoAnalysis).filter(*_f).first()
        if not a:
            return None
        ratios = self._compute_ratios(
            a.raw_data.get("like_count", 0) if a.raw_data else 0,
            a.raw_data.get("comment_count", 0) if a.raw_data else 0,
            a.raw_data.get("collect_count", 0) if a.raw_data else 0,
            a.raw_data.get("play_count", 1) if a.raw_data else 1,
        )
        return {**self._analysis_to_dict(a), **ratios}

    def _analysis_to_dict(self, a: VideoAnalysis) -> dict:
        return {
            "id": a.id,
            "video_id": a.video_id,
            "topic_id": a.topic_id,
            "like_play_ratio": a.like_play_ratio,
            "comment_play_ratio": a.comment_play_ratio,
            "collect_play_ratio": a.collect_play_ratio,
            "resonance_analysis": a.resonance_analysis,
            "discussion_analysis": a.discussion_analysis,
            "value_analysis": a.value_analysis,
            "why_viral_summary": a.why_viral_summary,
            "created_at": a.created_at,
        }


analyzer_service = AnalyzerService()
