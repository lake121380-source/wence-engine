"""
TikHub API 封装
支持：抖音 / 小红书 / 微信视频号
"""
import httpx
from typing import Optional
from config import settings

BASE_URL = "https://api.tikhub.io"

class TikHubClient:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {settings.tikhub_api_key}",
            "Content-Type": "application/json",
        }
        self.timeout = 60.0

    async def _get(self, endpoint: str, params: dict = None) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(
                f"{BASE_URL}{endpoint}",
                headers=self.headers,
                params=params or {}
            )
            resp.raise_for_status()
            return resp.json()

    async def _post(self, endpoint: str, json_data: dict = None) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{BASE_URL}{endpoint}",
                headers=self.headers,
                json=json_data or {}
            )
            resp.raise_for_status()
            return resp.json()

    # ─── 抖音 ───────────────────────────────────────────────
    async def douyin_get_user_by_unique_id(self, unique_id: str) -> dict:
        """通过抖音号获取用户信息"""
        return await self._get(
            "/api/v1/douyin/web/handler_user_profile_v2",
            {"unique_id": unique_id}
        )

    async def douyin_get_user_videos(self, sec_user_id: str, max_cursor: int = 0) -> dict:
        """获取用户主页作品列表"""
        return await self._get(
            "/api/v1/douyin/web/fetch_user_post_videos",
            {"sec_user_id": sec_user_id, "max_cursor": max_cursor, "count": 20}
        )

    async def douyin_get_video_detail(self, aweme_id: str) -> dict:
        """获取单个视频详情（V2 Web 接口，数据更全）"""
        return await self._get(
            "/api/v1/douyin/web/fetch_one_video_v2",
            {"aweme_id": aweme_id}
        )

    async def douyin_fetch_video_statistics(self, aweme_ids: list[str]) -> dict:
        """批量获取视频统计数据（含真实播放量）"""
        return await self._get(
            "/api/v1/douyin/app/v3/fetch_multi_video_statistics",
            {"aweme_ids": ",".join(aweme_ids)}
        )

    # ─── 小红书 ─────────────────────────────────────────────
    async def xhs_get_user_info(self, user_id: str) -> dict:
        """获取小红书用户信息（web v1 接口，稳定可用）"""
        return await self._get(
            "/api/v1/xiaohongshu/web/get_user_info",
            {"user_id": user_id}
        )

    async def xhs_get_user_notes(self, user_id: str, cursor: str = "") -> dict:
        """获取小红书用户笔记列表（app 接口）"""
        params = {"user_id": user_id, "num": 30}
        if cursor:
            params["cursor"] = cursor
        return await self._get(
            "/api/v1/xiaohongshu/app/get_user_notes",
            params
        )

    async def xhs_get_note_detail(self, note_id: str) -> dict:
        """获取小红书笔记详情"""
        return await self._get(
            "/api/v1/xiaohongshu/web_v3/fetch_note_detail",
            {"note_id": note_id}
        )

    async def xhs_search_users(self, keyword: str, page: int = 1) -> dict:
        """小红书关键词搜索用户（web v1 接口，稳定可用）"""
        return await self._get(
            "/api/v1/xiaohongshu/web/search_users",
            {"keyword": keyword, "page": page}
        )

    async def xhs_get_user_id_from_share_link(self, share_link: str) -> dict:
        """从小红书分享链接提取 user_id"""
        return await self._get(
            "/api/v1/xiaohongshu/app/get_user_id_and_xsec_token",
            {"share_link": share_link}
        )

    # ─── 微信视频号 ─────────────────────────────────────────
    async def wechat_channels_get_home_page(self, username: str, last_buffer: str = "") -> dict:
        """获取微信视频号用户主页（含视频列表）"""
        payload = {"username": username}
        if last_buffer:
            payload["last_buffer"] = last_buffer
        return await self._post(
            "/api/v1/wechat_channels/fetch_home_page",
            payload
        )

    async def wechat_channels_get_video_detail(self, video_id: str) -> dict:
        """获取微信视频号视频详情"""
        return await self._get(
            "/api/v1/wechat_channels/fetch_video_detail",
            {"id": video_id}
        )

    async def wechat_channels_search_users(self, keywords: str, page: int = 0) -> dict:
        """微信视频号用户搜索"""
        return await self._get(
            "/api/v1/wechat_channels/fetch_user_search_v2",
            {"keywords": keywords, "page": page}
        )

    # ─── 关键词搜索（爆款发现）──────────────────────────────
    async def douyin_search_videos(
        self, keyword: str, sort_type: int = 1, publish_time: int = 0, cursor: int = 0, count: int = 20
    ) -> dict:
        """
        抖音关键词搜索视频 (search/v1 POST接口)
        sort_type: 0=综合排序, 1=最多点赞, 2=最新发布
        cursor: 上一次请求返回的 cursor 值，用于翻页
        """
        return await self._post(
            "/api/v1/douyin/search/fetch_video_search_v1",
            {
                "keyword": keyword,
                "count": count,
                "offset": cursor,
                "sort_type": str(sort_type),
                "publish_time": str(publish_time),
            }
        )

    async def douyin_general_search(
        self, keyword: str, sort_type: int = 0, publish_time: int = 0, offset: int = 0, count: int = 20
    ) -> dict:
        """
        抖音综合搜索 (general_search_v1 POST接口)
        支持真正翻页，每页约 19 条，包含 aweme_info
        sort_type: 0=综合, 1=最多点赞, 2=最新发布
        """
        return await self._post(
            "/api/v1/douyin/search/fetch_general_search_v1",
            {
                "keyword": keyword,
                "count": str(count),
                "offset": str(offset),
                "sort_type": str(sort_type),
                "publish_time": str(publish_time),
            }
        )

    async def douyin_search_users(self, keyword: str, count: int = 20) -> dict:
        """抖音关键词搜索博主（用于发现行业头部博主）"""
        return await self._get(
            "/api/v1/douyin/web/fetch_user_search_result",
            {"keyword": keyword, "count": count, "offset": 0}
        )

    async def xhs_search_notes(self, keyword: str, sort: str = "general", page: int = 1) -> dict:
        """
        小红书关键词搜索笔记 (web v1 接口)
        sort: general=综合, likes=最多点赞(popularity_descending), new=最新(time_descending)
        """
        sort_map = {"general": "general", "likes": "popularity_descending", "new": "time_descending"}
        return await self._get(
            "/api/v1/xiaohongshu/web/search_notes",
            {"keyword": keyword, "sort": sort_map.get(sort, sort), "page": page}
        )



    # ─── 数据解析 helpers ────────────────────────────────────
    def parse_douyin_user(self, raw: dict) -> dict:
        # handler_user_profile_v2 returns data.user_info
        data = raw.get("data", {})
        u = data.get("user_info", data.get("user", {}))
        avatar = u.get("avatar_medium", u.get("avatar_larger", {}))
        return {
            "platform": "douyin",
            "platform_id": u.get("sec_uid", ""),
            "unique_id": u.get("unique_id", ""),
            "nickname": u.get("nickname", ""),
            "avatar_url": avatar.get("url_list", [""])[0] if avatar else "",
            "follower_count": u.get("mplatform_followers_count") or u.get("follower_count", 0),
            "video_count": u.get("aweme_count", 0),
            "bio": u.get("signature", ""),
        }

    def parse_douyin_video(self, v: dict) -> dict:
        stats = v.get("statistics") or {}
        video_obj = v.get("video") or {}
        cover = video_obj.get("cover") or video_obj.get("dynamic_cover") or {}
        url_list = cover.get("url_list") or []
        duration_ms = v.get("duration") or 0
        try:
            duration_s = int(duration_ms) // 1000
        except (TypeError, ValueError):
            duration_s = 0

        # 作者信息
        author = v.get("author") or {}
        author_avatar = (author.get("avatar_medium") or author.get("avatar_larger") or {})
        author_avatar_url = (author_avatar.get("url_list") or [""])[0] if isinstance(author_avatar, dict) else ""
        sec_uid = author.get("sec_uid", "")

        # 互动数据
        like_count = stats.get("digg_count") or 0
        comment_count = stats.get("comment_count") or 0
        share_count = stats.get("share_count") or 0
        play_count = stats.get("play_count") or 0
        collect_count = stats.get("collect_count") or 0

        # 互动比率
        # like_play_ratio 只在有真实播放量时才计算，否则 like/like*20=5% 是恒等式，无区分度
        if play_count > 0:
            like_play_ratio = round(like_count / play_count, 6)
            comment_play_ratio = round(comment_count / play_count, 6)
            collect_play_ratio = round(collect_count / play_count, 6)
        elif like_count > 0:
            # 无播放量时：comment/collect 用 like*20 估算仍有区分度，like ratio 则恒定无意义
            est_base = like_count * 20
            like_play_ratio = None
            comment_play_ratio = round(comment_count / est_base, 6)
            collect_play_ratio = round(collect_count / est_base, 6)
        else:
            like_play_ratio = None
            comment_play_ratio = 0
            collect_play_ratio = 0

        return {
            "platform": "douyin",
            "video_id": v.get("aweme_id", ""),
            "title": v.get("desc", ""),
            "description": v.get("desc", ""),
            "cover_url": url_list[0] if url_list else "",
            "like_count": like_count,
            "comment_count": comment_count,
            "share_count": share_count,
            "play_count": play_count,
            "collect_count": collect_count,
            "duration": duration_s,
            "tags": [t.get("hashtag_name", "") for t in (v.get("text_extra") or []) if t.get("hashtag_name")],
            "create_time": v.get("create_time", 0),
            "published_at": _ts_to_datetime(v.get("create_time", 0)),
            # 作者
            "author": author.get("nickname", ""),
            "author_id": sec_uid,
            "author_unique_id": author.get("unique_id", ""),
            "author_avatar": author_avatar_url,
            "author_follower_count": author.get("follower_count", 0),
            "author_bio": author.get("signature", ""),
            "author_url": f"https://www.douyin.com/user/{sec_uid}" if sec_uid else "",
            # 视频链接
            "video_url": v.get("share_url", "") or (f"https://www.douyin.com/video/{v.get('aweme_id','')}" if v.get("aweme_id") else ""),
            # 互动比
            "like_play_ratio": like_play_ratio,
            "comment_play_ratio": comment_play_ratio,
            "collect_play_ratio": collect_play_ratio,
        }

    def parse_xhs_user(self, raw: dict) -> dict:
        # web/get_user_info: data.data.{nickname, red_id, userid, ...}
        # web_v3/fetch_user_info: data.basicInfo.{nickname, redId, userId, ...}
        data = raw.get("data", {})
        inner = data.get("data", {})
        u = data.get("basicInfo") or data.get("basic_info") or inner or data.get("user") or {}
        # 粉丝数：web/get_user_info 直接有 fans 字段
        fans = u.get("fans", 0)
        if not fans:
            interact = u.get("interactions") or data.get("interactions") or data.get("interaction_info") or []
            for i in interact:
                if isinstance(i, dict) and i.get("type") in ("fans", "followers"):
                    fans = _parse_count(i.get("count", 0))
                    break
        return {
            "platform": "xiaohongshu",
            "platform_id": u.get("userid") or u.get("userId") or u.get("user_id", ""),
            "unique_id": u.get("redId") or u.get("red_id", ""),
            "nickname": u.get("nickname", ""),
            "avatar_url": u.get("imageb") or u.get("image") or u.get("avatar", ""),
            "follower_count": fans,
            "bio": u.get("desc") or u.get("description", ""),
        }

    def parse_xhs_note(self, n: dict) -> dict:
        # 兼容 app/get_user_notes 和 web_v3/fetch_user_notes 两种结构
        # app格式: id, likes, comments_count, share_count, view_count, images_list
        # web_v3格式: noteId, interactInfo.{likedCount,commentCount}, cover
        interact = n.get("interactInfo") or n.get("interact_info") or {}
        images = n.get("images_list") or []
        cover = n.get("cover") or {}
        cover_url = ""
        if images:
            img = images[0] if isinstance(images[0], dict) else {}
            cover_url = img.get("url") or img.get("url_default") or img.get("info_list", [{}])[0].get("url", "")
        if not cover_url:
            cover_url = cover.get("urlDefault") or cover.get("url", "")
        note_id = n.get("id") or n.get("noteId") or n.get("note_id", "")
        note_type = n.get("type", "")  # "normal"=图文, "video"=视频
        return {
            "platform": "xiaohongshu",
            "video_id": note_id,
            "title": n.get("title") or n.get("display_title", ""),
            "description": n.get("desc") or n.get("description", ""),
            "cover_url": cover_url,
            # 构造笔记页链接，供前端"查看原笔记"跳转
            "video_url": f"https://www.xiaohongshu.com/explore/{note_id}" if note_id else "",
            "like_count": _parse_count(n.get("likes") or interact.get("likedCount") or interact.get("liked_count", 0)),
            "comment_count": _parse_count(n.get("comments_count") or interact.get("commentCount") or interact.get("comment_count", 0)),
            "share_count": _parse_count(n.get("share_count", 0)),
            "play_count": _parse_count(n.get("view_count", 0)),
            "note_type": note_type,  # 图文/视频区分
            "published_at": _ts_to_datetime(n.get("create_time") or n.get("time", 0)),
            "tags": [t.get("name", "") for t in (n.get("tagList") or n.get("tag_list") or [])],
        }

    def parse_wechat_channels_user(self, raw: dict, username: str = "") -> dict:
        """从 fetch_home_page 响应解析用户信息"""
        data = raw.get("data", {})
        objs = data.get("object", [])
        nickname = ""
        avatar_url = ""
        follower_count = 0
        bio = ""
        if objs:
            first = objs[0]
            # nickname is top-level on each video object
            nickname = first.get("nickname", "")
            # author profile is in the 'contact' sub-object
            contact = first.get("contact", {})
            avatar_url = contact.get("head_url", "") or contact.get("headUrl", "") or ""
            bio = contact.get("signature", "") or first.get("desc", "") or ""
            follower_count = contact.get("follower_count", 0) or 0
        original_count = data.get("original_info", {}).get("original_count", 0)
        return {
            "platform": "weixin",
            "platform_id": username,
            "unique_id": username,
            "nickname": nickname,
            "avatar_url": avatar_url,
            "follower_count": follower_count,
            "video_count": original_count,
            "bio": bio,
        }

    def parse_wechat_channels_video(self, v: dict) -> dict:
        """解析单个视频号视频对象"""
        od = v.get("object_desc", {})
        media = od.get("media", [{}])
        first_media = media[0] if media else {}
        cover_url = first_media.get("cover_url") or first_media.get("thumb_url", "")
        duration = first_media.get("video_play_len", 0)
        # 尝试多个常见字段名取播放直链
        video_url = (
            first_media.get("url")
            or first_media.get("play_url")
            or (first_media.get("url_info") or {}).get("url", "")
            or ""
        )
        like_count = v.get("like_count", 0)
        comment_count = v.get("comment_count", 0)
        share_count = v.get("forward_count", 0)
        fav_count = v.get("fav_count", 0)
        return {
            "platform": "weixin",
            "video_id": str(v.get("id", "")),
            "title": od.get("description", "")[:100],
            "description": od.get("description", ""),
            "cover_url": cover_url,
            "video_url": video_url,
            "like_count": like_count,
            "comment_count": comment_count,
            "share_count": share_count,
            "play_count": 0,
            "collect_count": fav_count,
            "duration": duration,
            "published_at": _ts_to_datetime(v.get("createtime", 0)),
            "tags": [],
        }

    def parse_search_video(self, platform: str, v: dict) -> dict:
        """统一解析各平台搜索结果视频"""
        if platform == "douyin":
            return self.parse_douyin_video(v)
        elif platform == "xiaohongshu":
            return self.parse_xhs_search_note(v)
        return {}

    def parse_xhs_search_note(self, n: dict) -> dict:
        """解析小红书搜索结果笔记（兼容 web v1 / web_v3 两种格式）"""
        # web v1: n = {model_type, note: {...}}  → note 里直接有字段
        # web_v3: n = {id, noteCard: {...}}      → noteCard 里有字段
        note = n.get("note") or {}
        note_card = n.get("noteCard") or n.get("note_card") or {}
        # 合并: 优先 note (web v1)
        src = note or note_card or n
        interact = src.get("interactInfo") or src.get("interact_info") or {}
        author = src.get("user") or src.get("author") or {}
        # 封面：web v1 在 images_list, web_v3 在 cover
        cover_url = ""
        images_list = src.get("images_list") or []
        if images_list and isinstance(images_list[0], dict):
            cover_url = images_list[0].get("url", "") or images_list[0].get("url_default", "")
        if not cover_url:
            cover = src.get("cover") or {}
            cover_url = cover.get("urlDefault") or cover.get("url", "")
        return {
            "platform": "xiaohongshu",
            "video_id": src.get("id") or n.get("id") or note_card.get("noteId") or note_card.get("note_id", ""),
            "title": src.get("title") or src.get("display_title", ""),
            "description": src.get("desc") or src.get("description", ""),
            "cover_url": cover_url,
            "like_count": _parse_count(src.get("liked_count") or interact.get("likedCount") or interact.get("liked_count", 0)),
            "comment_count": _parse_count(src.get("comments_count") or interact.get("commentCount") or interact.get("comment_count", 0)),
            "share_count": _parse_count(src.get("shared_count", 0)),
            "collect_count": _parse_count(src.get("collected_count", 0)),
            "play_count": 0,
            "create_time": src.get("timestamp", 0),
            "author": author.get("nickname", ""),
            "author_id": author.get("userid") or author.get("userId") or author.get("user_id", ""),
            "tags": [],
        }



    # ─── 抖音：评论 ─────────────────────────────────────────
    async def douyin_get_video_comments(
        self, aweme_id: str, cursor: int = 0, count: int = 20
    ) -> dict:
        """获取抖音视频评论列表
        
        参数:
            aweme_id: 视频id
            cursor:   翻页游标，第一页传0，后续使用响应中的cursor值
            count:    每页数量，默认20（建议保持默认，改动可能触发BUG）
        返回:
            原始响应，评论列表在 data.comments 中
        """
        return await self._get(
            "/api/v1/douyin/web/fetch_video_comments",
            {"aweme_id": aweme_id, "cursor": cursor, "count": count}
        )

    async def douyin_get_comment_replies(
        self, item_id: str, comment_id: str, cursor: int = 0, count: int = 20
    ) -> dict:
        """获取抖音视频评论的回复列表
        
        参数:
            item_id:    视频id（即aweme_id）
            comment_id: 父评论id
            cursor:     翻页游标
            count:      每页数量，默认20
        返回:
            原始响应，回复列表在 data.comments 中
        """
        return await self._get(
            "/api/v1/douyin/web/fetch_video_comment_replies",
            {"item_id": item_id, "comment_id": comment_id, "cursor": cursor, "count": count}
        )

    def parse_douyin_comment(self, raw: dict) -> dict:
        """解析抖音单条评论数据
        
        兼容 web 和 app v3 接口返回格式
        """
        user = raw.get("user") or {}
        return {
            "cid": raw.get("cid", ""),
            "user_nickname": user.get("nickname", ""),
            "user_id": user.get("uid", "") or user.get("sec_uid", ""),
            "content": raw.get("text", ""),
            "digg_count": raw.get("digg_count", 0),
            "reply_count": raw.get("reply_comment_total", 0),
            "create_time": raw.get("create_time", 0),
        }

    # ─── 抖音：话题 ─────────────────────────────────────────
    async def douyin_get_challenge_posts(
        self,
        challenge_id: str,
        sort_type: int = 0,
        cursor: int = 0,
        count: int = 20,
        cookie: Optional[str] = None,
    ) -> dict:
        """获取抖音话题下的作品列表（POST接口）
        
        参数:
            challenge_id: 话题id，可从话题详情接口或搜索接口获取
            sort_type:    0=综合排序, 1=最热排序, 2=最新排序
            cursor:       翻页游标
            count:        每页数量
            cookie:       可选，提供Cookie可获取更多数据
        返回:
            原始响应，作品列表在 data.aweme_list 中
        """
        payload: dict = {
            "challenge_id": challenge_id,
            "sort_type": sort_type,
            "cursor": cursor,
            "count": count,
        }
        if cookie:
            payload["cookie"] = cookie
        return await self._post("/api/v1/douyin/web/fetch_challenge_posts", payload)

    # ─── 抖音：直播 ─────────────────────────────────────────
    async def douyin_get_live_by_webcast_id(self, webcast_id: str) -> dict:
        """通过直播间号(webcast_id)获取抖音直播间数据
        
        webcast_id 即直播间URL中的数字，如 https://live.douyin.com/775841227732
        注意：此处参数名为 webcast_id，不是 room_id
        """
        return await self._get(
            "/api/v1/douyin/web/fetch_user_live_videos",
            {"webcast_id": webcast_id}
        )

    async def douyin_get_live_by_sec_uid(self, sec_uid: str) -> dict:
        """通过用户 sec_uid 获取该用户当前直播间数据
        
        适用场景：已知博主sec_uid，查询其是否正在直播及直播数据
        """
        return await self._get(
            "/api/v1/douyin/web/fetch_user_live_videos_by_sec_uid",
            {"sec_uid": sec_uid}
        )

    async def douyin_get_live_by_room_id(self, room_id: str) -> dict:
        """通过 room_id 获取抖音直播间数据 V2
        
        注意：room_id 每次开播都会变化，需从直播相关接口动态获取
        """
        return await self._get(
            "/api/v1/douyin/web/fetch_user_live_videos_by_room_id_v2",
            {"room_id": room_id}
        )

    # ─── 抖音：弹幕 & 相关推荐 ──────────────────────────────
    async def douyin_get_video_danmaku(
        self,
        item_id: str,
        duration: int,
        start_time: int = 0,
        end_time: Optional[int] = None,
    ) -> dict:
        """获取抖音视频弹幕数据（用于播放跳出分析）
        
        参数:
            item_id:    视频id
            duration:   视频总时长（毫秒），从视频详情接口获取
            start_time: 起始时间（毫秒），默认0
            end_time:   结束时间（毫秒），默认等于 duration - 1
        返回:
            原始响应，弹幕数据在 data.danmakus 中
            每条弹幕包含: time（出现时间ms）、content（内容）
        """
        if end_time is None:
            end_time = max(duration - 1, 0)
        return await self._get(
            "/api/v1/douyin/web/fetch_one_video_danmaku",
            {
                "item_id": item_id,
                "duration": duration,
                "start_time": start_time,
                "end_time": end_time,
            }
        )

    async def douyin_get_related_posts(
        self, aweme_id: str, count: int = 20, refresh_index: int = 1
    ) -> dict:
        """获取抖音视频的相关作品推荐（用于竞品分析）
        
        参数:
            aweme_id:      视频id
            count:         返回数量，默认20
            refresh_index: 翻页索引，从1开始每次+1
        返回:
            原始响应，相关视频列表在 data.aweme_list 中
        """
        return await self._get(
            "/api/v1/douyin/web/fetch_related_posts",
            {"aweme_id": aweme_id, "count": count, "refresh_index": refresh_index}
        )

    # ─── 抖音：增强视频详情 & 批量 ──────────────────────────
    async def douyin_get_video_detail_v2(self, aweme_id: str) -> dict:
        """获取抖音单个视频数据 V2
        
        V1接口失效时的备用方案，参数相同
        """
        return await self._get(
            "/api/v1/douyin/web/fetch_one_video_v2",
            {"aweme_id": aweme_id}
        )

    async def douyin_get_multi_video(self, aweme_ids: list) -> dict:
        """批量获取抖音视频信息（POST接口）
        
        参数:
            aweme_ids: 视频id列表，最多支持50个
        返回:
            原始响应，视频列表在 data.aweme_details 中
        注意:
            此接口按固定价格计费（0.001$ * 50 = 0.05$ / 次）
            建议一次传满50个以提高性价比
        """
        return await self._post(
            "/api/v1/douyin/web/fetch_multi_video",
            aweme_ids  # 直接传 list，接口 body 就是 list
        )

    # ─── 小红书：评论 ────────────────────────────────────────
    async def xhs_get_note_comments(
        self, note_id: str, cursor: str = ""
    ) -> dict:
        """获取小红书笔记评论列表
        
        参数:
            note_id: 笔记ID
            cursor:  翻页游标，第一次传空字符串，后续使用响应中的cursor值
        返回:
            原始响应，评论列表在 data.comments 中
        """
        return await self._get(
            "/api/v1/xiaohongshu/web_v3/fetch_note_comments",
            {"note_id": note_id, "cursor": cursor}
        )

    async def xhs_get_sub_comments(
        self,
        note_id: str,
        root_comment_id: str,
        cursor: str = "",
        num: int = 10,
    ) -> dict:
        """获取小红书评论的子评论（回复）
        
        参数:
            note_id:         笔记ID
            root_comment_id: 父评论ID
            cursor:          翻页游标
            num:             每页数量，默认10
        返回:
            原始响应，子评论列表在 data.comments 中
        """
        return await self._get(
            "/api/v1/xiaohongshu/web_v3/fetch_sub_comments",
            {
                "note_id": note_id,
                "root_comment_id": root_comment_id,
                "cursor": cursor,
                "num": num,
            }
        )

    def parse_xhs_comment(self, raw: dict) -> dict:
        """解析小红书单条评论数据
        
        兼容 web_v3 接口返回格式（camelCase / snake_case）
        """
        user = raw.get("userInfo") or raw.get("user_info") or {}
        return {
            "id": raw.get("id", ""),
            "user_nickname": user.get("nickname", ""),
            "user_id": user.get("userId") or user.get("user_id", ""),
            "content": raw.get("content", ""),
            "like_count": _parse_count(
                raw.get("likeCount") or raw.get("like_count", 0)
            ),
            "sub_comment_count": raw.get("subCommentCount") or raw.get("sub_comment_count", 0),
            "create_time": raw.get("createTime") or raw.get("create_time", 0),
        }


def _parse_count(v) -> int:
    """解析带单位的中文数字（如 '1.2万'）"""
    if isinstance(v, int):
        return v
    if isinstance(v, str):
        v = v.replace("+", "").strip()
        if "万" in v:
            return int(float(v.replace("万", "")) * 10000)
        try:
            return int(v)
        except ValueError:
            return 0
    return 0


def _ts_to_datetime(ts):
    """Unix 时间戳转 datetime，0 或无效值返回 None"""
    from datetime import datetime
    if not ts or not isinstance(ts, (int, float)) or ts < 1000000000:
        return None
    return datetime.utcfromtimestamp(ts)


tikhub = TikHubClient()
