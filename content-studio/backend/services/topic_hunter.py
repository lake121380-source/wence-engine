"""
选题猎手服务
- 根据关键词跨平台搜索爆款视频（含作者信息、互动比、视频链接）
- 获取视频详情：视频文案(desc)、评论区热评
- 按互动数据排序
- 博主关键词批量发现
"""
import asyncio, time
from typing import Optional
from sqlalchemy.orm import Session
from services.tikhub import tikhub
from models import Creator


def _extract_subtitle_text(items: list) -> str:
    """从抖音字幕/自动字幕数据中提取内联纯文本（按时间顺序拼接）"""
    texts = []
    for item in items:
        if isinstance(item, dict):
            text = item.get("text") or item.get("content") or item.get("label") or ""
            if text:
                texts.append(str(text).strip())
    return " ".join(filter(None, texts))


def _fetch_srt_url(subtitle_infos: list) -> str:
    """
    从 subtitle_infos 中找到 SRT/VTT 字幕文件 URL 并下载解析为纯文本。
    抖音 API 返回的 subtitle_infos 通常是 {Url/url, LangCode/language_code, Format/format}
    形式的字幕文件链接，需要下载后解析。
    """
    import re
    import httpx

    srt_url = None
    for item in subtitle_infos:
        if not isinstance(item, dict):
            continue
        url = item.get("Url") or item.get("url") or ""
        if not url:
            continue
        lang = (item.get("LangCode") or item.get("LanguageCode") or
                item.get("language_code") or item.get("language") or "").lower()
        # 优先中文字幕
        if "zh" in lang or "cn" in lang:
            srt_url = url
            break
        if not srt_url:
            srt_url = url

    if not srt_url:
        return ""

    try:
        resp = httpx.get(
            srt_url,
            timeout=20,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1)"},
        )
        resp.raise_for_status()
        lines = []
        for line in resp.text.splitlines():
            line = line.strip()
            if not line:
                continue
            if re.match(r'^\d+$', line):          # SRT 序号行
                continue
            if re.match(r'[\d:,]+ --> [\d:,]+', line):  # SRT 时间轴行
                continue
            if re.match(r'WEBVTT', line, re.IGNORECASE):  # VTT 文件头
                continue
            lines.append(line)
        text = " ".join(lines)
        print(f"[TopicHunter] SRT 下载解析完成，共 {len(text)} 字")
        return text
    except Exception as e:
        print(f"[TopicHunter] SRT 下载失败: {e}")
        return ""


class TopicHunterService:

    # ─── 爆款视频搜索 ────────────────────────────────────────
    async def search_viral_videos(
        self,
        keyword: str,
        platforms: list[str] = None,
        limit: int = 30,
        sort: str = "likes",   # likes / new / comment_ratio / collect_ratio
        min_likes: int = 0,
        days: int = 0,         # 0=不限, 3/7/30 天内
        pages: int = 1,        # 搜索翻页数
    ) -> list[dict]:
        """
        跨平台搜索爆款视频
        返回按指定方式排序的统一格式视频列表
        """
        if platforms is None:
            platforms = ["douyin"]

        # 各平台并发，但每个平台内部顺序翻页（避免并发轰炸 TikHub 导致超时/限速）
        tasks = []
        if "douyin" in platforms:
            tasks.append(self._search_douyin(keyword, sort, limit, days=days))
        if "xiaohongshu" in platforms:
            xhs_sort = "likes" if sort in ("likes", "comment_ratio", "collect_ratio") else "new"
            tasks.append(self._search_xhs(keyword, xhs_sort, limit))
        if "weixin" in platforms:
            tasks.append(self._search_weixin(keyword, limit))

        results_per_platform = await asyncio.gather(*tasks, return_exceptions=True)

        all_videos: list[dict] = []
        errors: list[str] = []
        seen_ids = set()
        for result in results_per_platform:
            if isinstance(result, Exception):
                errors.append(f"{type(result).__name__}: {result}")
                continue
            for v in result:
                vid = f"{v.get('platform')}-{v.get('video_id')}"
                if vid in seen_ids:
                    continue
                seen_ids.add(vid)
                v["keyword"] = keyword
                all_videos.append(v)

        # 时间过滤
        if days > 0:
            cutoff = time.time() - days * 86400
            all_videos = [v for v in all_videos if (v.get("create_time") or 0) >= cutoff]

        # 最低点赞过滤
        if min_likes > 0:
            all_videos = [v for v in all_videos if (v.get("like_count") or 0) >= min_likes]

        # 排序
        sort_keys = {
            "likes": lambda x: x.get("like_count", 0),
            "new": lambda x: x.get("create_time", 0),
            "comment_ratio": lambda x: x.get("comment_play_ratio", 0),
            "collect_ratio": lambda x: x.get("collect_play_ratio", 0),
            "like_ratio": lambda x: x.get("like_play_ratio", 0),
        }
        key_fn = sort_keys.get(sort, sort_keys["likes"])
        all_videos.sort(key=key_fn, reverse=True)
        return all_videos[:limit], errors

    async def _search_douyin(self, keyword: str, sort: str, limit: int, days: int = 0) -> list[dict]:
        """
        使用 general_search_v1 接口，支持 offset 翻页。
        按用户选择的排序方式搜索，多页翻页直到凑够 limit 条。
        days: 时间过滤，传给 API 的 publish_time（0=不限,1=一天,7=一周）
        """
        sort_type_map = {"likes": 1, "new": 2}
        sort_type = sort_type_map.get(sort, 1)
        max_pages = max(2, (limit // 15) + 1)  # 每页约 17 条有效视频

        # API 支持的 publish_time: 0=不限, 1=一天内, 7=一周内, 182=半年内
        # 前端传 3/7/30，映射到 API 最近的较大范围，后端再精确过滤
        api_publish_time = 0
        if days > 0:
            if days <= 1:
                api_publish_time = 1
            elif days <= 7:
                api_publish_time = 7
            else:
                api_publish_time = 182

        seen_ids: set = set()
        result: list[dict] = []

        for page in range(max_pages):
            if len(result) >= limit:
                break
            try:
                raw = await tikhub.douyin_general_search(
                    keyword, sort_type=sort_type, offset=page * 20,
                    publish_time=api_publish_time
                )
                data = raw.get("data", {})
                items = data.get("data", []) if isinstance(data, dict) else data if isinstance(data, list) else []
                print(f"[TopicHunter] douyin general page={page+1} items={len(items)}")
                for item in items:
                    ai = item.get("aweme_info")
                    if not ai:
                        continue
                    p = tikhub.parse_douyin_video(ai)
                    vid = p.get("video_id", "")
                    if vid and vid not in seen_ids:
                        seen_ids.add(vid)
                        result.append(p)
                has_more = data.get("has_more", 0) if isinstance(data, dict) else 0
                if not has_more:
                    break
                if page < max_pages - 1 and len(result) < limit:
                    await asyncio.sleep(0.3)
            except Exception as e:
                print(f"[TopicHunter] douyin general page={page+1} error: {type(e).__name__}: {e}")
                break

        print(f"[TopicHunter] douyin total unique={len(result)}")
        return result[:limit]

    async def _search_xhs(self, keyword: str, sort: str, limit: int) -> list[dict]:
        try:
            raw = await tikhub.xhs_search_notes(keyword, sort=sort)
            data = raw.get("data", {})
            # web v1: data.data.items[{model_type, note}]
            inner = data.get("data", {}) if isinstance(data.get("data"), dict) else {}
            notes_raw = inner.get("items") or data.get("items") or data.get("notes") or []
            result = []
            for n in notes_raw:
                parsed = tikhub.parse_xhs_search_note(n)
                if parsed.get("video_id"):
                    result.append(parsed)
            return result[:limit]
        except Exception as e:
            print(f"[TopicHunter] xhs search error: {type(e).__name__}: {e}")
            return []

    async def _search_weixin(self, keyword: str, limit: int) -> list[dict]:
        """视频号关键词搜索（暂用用户搜索接口取视频列表）"""
        try:
            from services.tikhub import tikhub as th
            raw = await th.wechat_channels_search_users(keyword, page=0)
            data = raw.get("data", {})
            items = data.get("items", [])
            result = []
            for item in items:
                jump_info = item.get("jumpInfo", {})
                username = jump_info.get("userName", "")
                if not username:
                    continue
                import re as _re
                _strip = lambda s: _re.sub(r'<[^>]+>', '', s or '')
                result.append({
                    "platform": "weixin",
                    "video_id": username,
                    "title": _strip(item.get("title", "")),
                    "description": _strip(item.get("desc", "")),
                    "cover_url": item.get("thumbUrl", ""),
                    "like_count": 0,
                    "comment_count": 0,
                    "play_count": 0,
                })
            return result[:limit]
        except Exception as e:
            print(f"[TopicHunter] weixin search error: {type(e).__name__}: {e}")
            return []

    # ─── 获取单视频详情 + 评论 ────────────────────────────────
    async def fetch_video_detail(self, platform: str, video_id: str, comment_count: int = 20) -> dict:
        """
        获取单个视频的详细信息 + 热门评论
        返回: { script, top_comments: [{nickname, content, likes}], ... }

        对于抖音视频：
          1. 优先使用 API 返回的自动字幕字段（subtitle_infos / video.auto_captions）
          2. 若无内置字幕，调用硅基流动 SenseVoice 对视频音频做 ASR
          3. 两者均失败则 script 返回空字符串
        """
        detail_data = {}
        comments_data = []

        if platform == "douyin":
            # 获取视频详情
            try:
                raw = await tikhub.douyin_get_video_detail(video_id)
                data = raw.get("data", {})
                v = data.get("aweme_detail") or data

                # 提取视频播放地址（用于音频下载）
                video_obj = v.get("video") or {}
                play_addr = video_obj.get("play_addr") or {}
                url_list = play_addr.get("url_list") or []
                play_url = url_list[0] if url_list else ""

                # 1. 优先使用 API 内置自动字幕
                transcript = ""
                subtitle_infos = v.get("subtitle_infos") or []
                auto_captions = video_obj.get("auto_captions") or []

                if subtitle_infos:
                    transcript = _extract_subtitle_text(subtitle_infos)
                    if not transcript:  # 内联文本为空，尝试下载 SRT 文件 URL
                        transcript = _fetch_srt_url(subtitle_infos)
                    if transcript:
                        print(f"[TopicHunter] 使用 subtitle_infos 字幕，共 {len(transcript)} 字")
                if not transcript and auto_captions:  # subtitle_infos 失败则继续尝试 auto_captions
                    transcript = _extract_subtitle_text(auto_captions)
                    if not transcript:
                        transcript = _fetch_srt_url(auto_captions)
                    if transcript:
                        print(f"[TopicHunter] 使用 auto_captions 字幕，共 {len(transcript)} 字")

                # 2. 若无内置字幕，调用 SenseVoice 语音转录
                if not transcript and play_url:
                    from services.transcribe import transcribe_service
                    transcript = await transcribe_service.transcribe_from_url(play_url, video_id)

                detail_data = {
                    "script": transcript,
                    "caption": v.get("desc", ""),   # 博主手动输入的文案描述
                    "share_url": (v.get("share_info") or {}).get("share_url", ""),
                }
            except Exception as e:
                print(f"[TopicHunter] douyin detail error: {e}")

            # 获取评论
            try:
                raw = await tikhub.douyin_get_video_comments(video_id, count=comment_count)
                data = raw.get("data", {})
                raw_comments = data.get("comments") or []
                for c in raw_comments:
                    parsed = tikhub.parse_douyin_comment(c)
                    comments_data.append({
                        "nickname": parsed.get("user_nickname", ""),
                        "content": parsed.get("content", ""),
                        "likes": parsed.get("digg_count", 0),
                        "replies": parsed.get("reply_count", 0),
                    })
                # 按点赞降序
                comments_data.sort(key=lambda x: x["likes"], reverse=True)
            except Exception as e:
                print(f"[TopicHunter] douyin comments error: {e}")

        elif platform == "xiaohongshu":
            try:
                raw = await tikhub.xhs_get_note_comments(video_id)
                data = raw.get("data", {})
                raw_comments = data.get("comments") or []
                for c in raw_comments:
                    parsed = tikhub.parse_xhs_comment(c)
                    comments_data.append({
                        "nickname": parsed.get("user_nickname", ""),
                        "content": parsed.get("content", ""),
                        "likes": parsed.get("like_count", 0),
                        "replies": parsed.get("sub_comment_count", 0),
                    })
                comments_data.sort(key=lambda x: x["likes"], reverse=True)
            except Exception as e:
                print(f"[TopicHunter] xhs comments error: {e}")

        return {
            "script": detail_data.get("script", ""),
            "caption": detail_data.get("caption", ""),
            "share_url": detail_data.get("share_url", ""),
            "top_comments": comments_data[:comment_count],
        }

    # ─── 博主关键词发现 ──────────────────────────────────────
    async def discover_creators_by_keyword(
        self, db: Session, keyword: str, limit: int = 30
    ) -> list[dict]:
        try:
            raw = await tikhub.douyin_search_users(keyword)
            users_raw = raw.get("data", {}).get("user_list", [])
        except Exception as e:
            raise RuntimeError(f"搜索博主失败: {e}")

        results = []
        for item in users_raw[:limit]:
            user_info = item.get("user_info", item)
            sec_uid = user_info.get("sec_uid", "")
            existing = db.query(Creator).filter(
                Creator.platform == "douyin",
                Creator.platform_id == sec_uid,
            ).first() if sec_uid else None

            results.append({
                "platform": "douyin",
                "platform_id": sec_uid,
                "unique_id": user_info.get("unique_id", ""),
                "nickname": user_info.get("nickname", ""),
                "avatar_url": user_info.get("avatar_thumb", {}).get("url_list", [""])[0],
                "follower_count": user_info.get("follower_count", 0),
                "bio": user_info.get("signature", ""),
                "already_added": existing is not None,
                "creator_id": existing.id if existing else None,
            })

        results.sort(key=lambda x: x.get("follower_count", 0), reverse=True)
        return results


topic_hunter = TopicHunterService()
