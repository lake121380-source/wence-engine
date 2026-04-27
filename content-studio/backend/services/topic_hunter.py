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

    def _match_keyword(self, video: dict, keyword: str) -> bool:
        """关键词匹配：用于热榜模式的二次筛选。"""
        kw = (keyword or "").strip().lower()
        if not kw:
            return True
        haystacks = [
            str(video.get("title") or "").lower(),
            str(video.get("description") or "").lower(),
            str(video.get("author") or "").lower(),
            " ".join(video.get("tags") or []).lower(),
        ]
        return any(kw in h for h in haystacks)

    async def search_viral_videos(
        self,
        keyword: str,
        platforms: list[str] = None,
        limit: int = 30,
        sort: str = "likes",   # likes / new / comment_ratio / collect_ratio
        min_likes: int = 0,
        days: int = 0,         # 0=不限, 3/7/30 天内
        pages: int = 1,        # 搜索翻页数
        video_type: str = "", # low_score_viral / high_completion / high_likes / high_follower_growth
    ) -> tuple[list[dict], list[str]]:
        """
        跨平台搜索爆款视频
        返回按指定方式排序的统一格式视频列表
        """
        if platforms is None:
            platforms = ["douyin"]

        # 各平台并发，但每个平台内部顺序翻页（避免并发轰炸 TikHub 导致超时/限速）
        tasks = []
        if "douyin" in platforms:
            tasks.append(self._search_douyin(keyword, sort, limit, days=days, video_type=video_type, pages=pages))
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

    async def _search_douyin(self, keyword: str, sort: str, limit: int, days: int = 0, video_type: str = "", pages: int = 1) -> list[dict]:
        """
        抖音搜索入口：
        - 有 video_type → 直接调对应 Billboard 接口（keyword 做二次过滤）
        - 无 video_type → 调关键词搜索接口
        """
        if video_type:
            return await self._search_douyin_billboard(
                keyword=keyword,
                video_type=video_type,
                limit=limit,
                pages=pages,
            )

        sort_type_map = {"likes": 1, "new": 2}
        sort_type = sort_type_map.get(sort, 1)
        max_pages = max(max(1, pages), (limit // 15) + 1)  # 每页约 17 条有效视频

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

    async def _search_douyin_billboard(self, keyword: str, video_type: str, limit: int, pages: int = 1) -> list[dict]:
        """抖音热点榜检索：优先使用 Douyin-Billboard-API。"""
        endpoint_map = {
            "low_score_viral": tikhub.douyin_billboard_fetch_hot_total_low_fan_list,
            "high_completion": tikhub.douyin_billboard_fetch_hot_total_high_play_list,
            "high_likes": tikhub.douyin_billboard_fetch_hot_total_high_like_list,
            "high_follower_growth": tikhub.douyin_billboard_fetch_hot_total_high_fan_list,
        }
        fetcher = endpoint_map.get(video_type, tikhub.douyin_billboard_fetch_hot_total_video_list)

        result: list[dict] = []
        seen_ids: set = set()
        page = 1
        page_size = min(20, max(10, limit))
        # 前端未传 pages 时默认=1；这里按 limit 自动放大翻页，确保能拿到几十条。
        auto_pages = max(1, (limit // 15) + 2)
        max_pages = max(max(1, pages), auto_pages)

        while len(result) < limit and page <= max_pages:
            try:
                raw = await fetcher(page=page, page_size=page_size)
            except Exception as exc:
                print(f"[TopicHunter] douyin billboard page={page} error: {type(exc).__name__}: {exc}")
                break

            data = raw.get("data", {}) if isinstance(raw, dict) else {}
            items = []
            page_meta = {}
            if isinstance(data, dict):
                # 新版返回通常是 data.data.objs
                nested = data.get("data")
                if isinstance(nested, dict):
                    page_meta = nested.get("page") or {}
                    objs = nested.get("objs")
                    if isinstance(objs, list):
                        items = objs
                elif isinstance(nested, list):
                    items = nested
                for key in ("list", "data", "items", "aweme_list", "video_list"):
                    val = data.get(key)
                    if isinstance(val, list):
                        items = val
                        break
            elif isinstance(data, list):
                items = data

            if not items:
                break

            for item in items:
                if not isinstance(item, dict):
                    continue
                if item.get("item_id"):
                    video_id = item.get("item_id", "")
                    like_count = int(item.get("like_cnt") or 0)
                    play_count = int(item.get("play_cnt") or 0)
                    collect_count = int(item.get("collect_cnt") or 0)
                    comment_count = int(item.get("comment_cnt") or 0)
                    if item.get("like_rate") is not None:
                        try:
                            like_play_ratio = float(item.get("like_rate") or 0)
                        except (TypeError, ValueError):
                            like_play_ratio = round((like_count / play_count), 6) if play_count > 0 else None
                    else:
                        like_play_ratio = round((like_count / play_count), 6) if play_count > 0 else None

                    parsed = {
                        "platform": "douyin",
                        "video_id": video_id,
                        "title": item.get("item_title", ""),
                        "description": item.get("item_title", ""),
                        "cover_url": item.get("item_cover_url", ""),
                        "video_url": f"https://www.douyin.com/video/{video_id}" if video_id else "",
                        "like_count": like_count,
                        "comment_count": comment_count,
                        "share_count": int(item.get("share_cnt") or 0),
                        "play_count": play_count,
                        "collect_count": collect_count,
                        "duration": int(item.get("item_duration") or 0),
                        "author": item.get("nick_name", ""),
                        "author_id": item.get("author_id", ""),
                        "author_unique_id": item.get("author_unique_id", ""),
                        "author_avatar": item.get("avatar_url", ""),
                        "author_follower_count": int(item.get("fans_cnt") or 0),
                        "author_bio": "",
                        "author_url": item.get("author_url", ""),
                        "create_time": int(item.get("publish_time") or 0),
                        "like_play_ratio": like_play_ratio,
                        "comment_play_ratio": round((comment_count / play_count), 6) if play_count > 0 else 0,
                        "collect_play_ratio": round((collect_count / play_count), 6) if play_count > 0 else 0,
                        "tags": [],
                    }
                else:
                    aweme = item.get("aweme_info") or item.get("aweme") or item.get("item") or item
                    if not isinstance(aweme, dict):
                        continue
                    parsed = tikhub.parse_douyin_video(aweme)

                vid = parsed.get("video_id")
                if not vid or vid in seen_ids:
                    continue
                if not self._match_keyword(parsed, keyword):
                    continue
                seen_ids.add(vid)
                result.append(parsed)
                if len(result) >= limit:
                    break

            page += 1
            # 不再用 len(items) < page_size 判定是否结束（该接口常见固定 19 条/页）
            if isinstance(page_meta, dict):
                total = int(page_meta.get("total") or 0)
                current = int(page_meta.get("page") or (page - 1))
                if total > 0 and current * page_size >= total:
                    break
            elif not items:
                break

        print(f"[TopicHunter] douyin billboard total unique={len(result)} type={video_type or 'default'} keyword={keyword}")
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

    # ─── 通过链接添加单个视频 ────────────────────────────────
    async def resolve_video_url(self, url: str) -> tuple[str, str]:
        """
        根据视频链接识别平台 + 提取 video_id。
        支持：
          - 抖音短链 v.douyin.com/xxx  、iesdouyin.com/share/video/123
          - 抖音长链 www.douyin.com/video/123 、douyin.com/note/123
          - 小红书短链 xhslink.com/xxx
          - 小红书长链 www.xiaohongshu.com/explore/xxx / /discovery/item/xxx
        返回 (platform, video_id)
        """
        import re, httpx
        raw = (url or "").strip()
        if not raw:
            raise ValueError("链接为空")

        # 从中文分享文本里提取第一个 http(s) 链接
        m = re.search(r"https?://[^\s]+", raw)
        if m:
            raw = m.group(0).rstrip("，。,。 ；;")

        # 跟随短链重定向
        resolved = raw
        short_hosts = ("v.douyin.com", "xhslink.com", "v.xhs.cn")
        if any(h in raw for h in short_hosts):
            try:
                async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as c:
                    r = await c.get(raw, headers={
                        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15",
                    })
                    resolved = str(r.url)
            except Exception:
                resolved = raw

        # 抖音 aweme_id
        patterns = [
            (r"douyin\.com/video/(\d+)", "douyin"),
            (r"douyin\.com/note/(\d+)", "douyin"),
            (r"iesdouyin\.com/share/video/(\d+)", "douyin"),
            (r"douyin\.com/share/video/(\d+)", "douyin"),
            (r"modal_id=(\d+)", "douyin"),
            # 小红书 note_id（24 位十六进制）
            (r"xiaohongshu\.com/explore/([0-9a-fA-F]+)", "xiaohongshu"),
            (r"xiaohongshu\.com/discovery/item/([0-9a-fA-F]+)", "xiaohongshu"),
        ]
        for pat, plat in patterns:
            mm = re.search(pat, resolved)
            if mm:
                return plat, mm.group(1)

        raise ValueError("无法识别的视频链接，目前支持抖音 / 小红书")

    async def fetch_topic_from_url(self, url: str) -> dict:
        """
        通过视频链接获取标准化的选题字段（不入库）。
        返回字段与 parse_douyin_video / parse_xhs_note 一致，可直接用于构建 Topic。
        """
        platform, video_id = await self.resolve_video_url(url)

        if platform == "douyin":
            raw = await tikhub.douyin_get_video_detail(video_id)
            data = raw.get("data", {})
            v = data.get("aweme_detail") or data
            if not v or not (v.get("aweme_id") or v.get("desc")):
                raise ValueError("未能从抖音获取到视频详情")
            return tikhub.parse_douyin_video(v)

        if platform == "xiaohongshu":
            raw = await tikhub.xhs_get_note_detail(video_id)
            data = raw.get("data", {})
            # web_v3 返回结构差异较大，兼容几种可能的路径
            note = data.get("note") or data.get("items", [{}])[0] if isinstance(data.get("items"), list) else data
            if not note:
                raise ValueError("未能从小红书获取到笔记详情")
            # 补一下 id 字段（有些返回体用 note_id）
            if not (note.get("id") or note.get("noteId") or note.get("note_id")):
                note["noteId"] = video_id
            return tikhub.parse_xhs_note(note)

        raise ValueError(f"暂不支持的平台：{platform}")

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
