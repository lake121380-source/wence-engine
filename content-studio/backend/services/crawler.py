"""
博主内容抓取服务
负责：新增博主 / 定时更新视频列表 / 触发向量索引
"""
from datetime import datetime, date
from sqlalchemy.orm import Session
from models import Creator, CreatorVideo, TenantCreator
from services.tikhub import tikhub
from services.knowledge import knowledge_service
import asyncio


def _json_safe(obj):
    """递归将 dict/list 中的 datetime/date 转为 ISO 字符串，确保 JSON 可序列化"""
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return obj


class CrawlerService:

    async def add_creator(
        self,
        db: Session,
        platform: str,
        identifier: str,
        tenant_id: int = None,
    ) -> Creator:
        """
        新增博主并建立租户订阅关系。
        Creator 记录全局共享（同一博主只存一份），
        TenantCreator 记录哪个租户订阅了该博主。
        identifier: 抖音号(unique_id) / 小红书用户ID / B站UID
        """
        profile = None
        resolved_uid = None
        if platform == "xiaohongshu":
            # 先解析 user_id，后续 _fetch_profile 不再重复解析
            resolved_uid = await self._resolve_xhs_user_id(identifier)
            profile = await self._fetch_profile(platform, identifier, resolved_user_id=resolved_uid)
        else:
            profile = await self._fetch_profile(platform, identifier)
        if not profile:
            raise ValueError(f"无法获取 {platform} 用户 {identifier} 的信息")

        # 全局共享的博主表，不区分租户
        existing = db.query(Creator).filter(
            Creator.platform == platform,
            Creator.platform_id == profile["platform_id"],
        ).first()

        if existing:
            # 更新博主基础信息
            for k, v in profile.items():
                setattr(existing, k, v)
            db.commit()
            creator = existing
        else:
            creator = Creator(**profile)
            db.add(creator)
            db.commit()
            db.refresh(creator)

        # 建立租户订阅关系（已订阅则跳过）
        if tenant_id:
            sub = db.query(TenantCreator).filter(
                TenantCreator.tenant_id == tenant_id,
                TenantCreator.creator_id == creator.id,
            ).first()
            if not sub:
                db.add(TenantCreator(tenant_id=tenant_id, creator_id=creator.id))
                db.commit()

        return creator

    async def crawl_creator_videos(self, db: Session, creator_id: int, max_videos: int = 30) -> int:
        """
        抓取博主视频并存库。
        如果数据库中已有 max_videos 条及以上视频，直接从 DB 返回，不调 API。
        返回：新增视频数
        """
        # 检查 DB 中已有多少视频
        existing_count = db.query(CreatorVideo).filter(
            CreatorVideo.creator_id == creator_id
        ).count()
        if existing_count >= max_videos:
            print(f"[Crawl] Creator {creator_id} 已有 {existing_count} 条视频（>={max_videos}），直接从 DB 获取，跳过 API")
            return 0
        creator = db.query(Creator).filter(Creator.id == creator_id).first()
        if not creator:
            raise ValueError(f"Creator {creator_id} not found")

        videos_data = await self._fetch_videos(creator.platform, creator.platform_id, max_videos)
        new_count = 0

        for vd in videos_data:
            # 检查是否已存在（同一博主内去重，共享记录）
            existing = db.query(CreatorVideo).filter(
                CreatorVideo.video_id == vd["video_id"],
                CreatorVideo.creator_id == creator.id,
            ).first()
            if existing:
                continue

            # 只传 CreatorVideo 模型有的列，过滤 tikhub 返回的多余字段
            valid_cols = {c.key for c in CreatorVideo.__table__.columns}
            video_fields = {k: v for k, v in vd.items() if k in valid_cols and k != "raw_data"}
            # raw_data 需要 JSON 可序列化，递归将 datetime 转为 ISO 字符串
            raw_data_safe = _json_safe(vd)
            video = CreatorVideo(
                creator_id=creator.id,
                raw_data=raw_data_safe,
                **video_fields
            )
            db.add(video)
            new_count += 1

        creator.last_crawled_at = datetime.utcnow()
        db.commit()

        # 抖音：批量拉取真实播放量（详情接口不返回 play_count）
        if creator.platform == "douyin":
            await self._backfill_douyin_play_counts(db, creator_id)

        # 触发向量索引
        if new_count > 0:
            await knowledge_service.index_creator_videos(db, creator_id)

        return new_count

    async def crawl_all_active_creators(self, db: Session):
        """定时任务：批量更新所有激活博主"""
        creators = db.query(Creator).filter(Creator.is_active == True).all()
        results = []
        for creator in creators:
            try:
                n = await self.crawl_creator_videos(db, creator.id)
                results.append({"creator_id": creator.id, "new_videos": n})
            except Exception as e:
                results.append({"creator_id": creator.id, "error": str(e)})
            await asyncio.sleep(1)  # 避免请求过快
        return results

    async def auto_discover_and_crawl(
        self,
        db: Session,
        keyword: str,
        limit: int = 30,
        platforms: list[str] = None,
        progress_callback=None,
        tenant_id: int = None,
    ) -> dict:
        """
        一键自动发现头部博主并添加入库
        1. 按关键词搜索博主（按粉丝数排序）
        2. 依次添加 + 抓取视频
        progress_callback: async fn(step, total, msg) 用于汇报进度
        """
        if platforms is None:
            platforms = ["douyin"]

        all_found = []
        # 各平台搜索博主
        for platform in platforms:
            try:
                if platform == "douyin":
                    raw = await tikhub.douyin_search_users(keyword, count=min(limit, 20))
                    data = raw.get("data", {})
                    # 兼容不同响应结构
                    users = data.get("user_list", data.get("data", []))
                    for u in users:
                        user_info = u.get("user_info", u)
                        uid = user_info.get("unique_id", "") or user_info.get("sec_uid", "")
                        if not uid:
                            continue
                        all_found.append({
                            "platform": "douyin",
                            "identifier": uid,
                            "nickname": user_info.get("nickname", uid),
                            "follower_count": user_info.get("mplatform_followers_count") or user_info.get("follower_count", 0),
                            "sec_uid": user_info.get("sec_uid", ""),
                        })
                    if not users:
                        print(f"[AutoDiscover] 抖音用户搜索返回空结果，可能该关键词暂不支持搜索")
                elif platform == "weixin":
                    raw = await tikhub.wechat_channels_search_users(keyword, page=0)
                    data = raw.get("data", {})
                    items = data.get("items", [])
                    for item in items:
                        jump_info = item.get("jumpInfo", {})
                        username = jump_info.get("userName", "")
                        if not username:
                            continue
                        title = item.get("title", "").replace("<em>", "").replace("</em>", "")
                        all_found.append({
                            "platform": "weixin",
                            "identifier": username,
                            "nickname": title,
                            "follower_count": 0,
                        })
                    if not items:
                        print(f"[AutoDiscover] 视频号用户搜索返回空结果")
            except Exception as e:
                print(f"[AutoDiscover] 搜索平台 {platform} 失败: {e}")

        # 按粉丝数降序，取前 limit 个
        all_found.sort(key=lambda x: x.get("follower_count", 0), reverse=True)
        all_found = all_found[:limit]

        added, failed, skipped = [], [], []
        total = len(all_found)

        for idx, u in enumerate(all_found):
            msg = f"正在处理 {u['nickname']} ({idx+1}/{total})"
            if progress_callback:
                await progress_callback(idx, total, msg, "processing")

            identifier = u.get("identifier") or u.get("sec_uid")
            if not identifier:
                failed.append({"nickname": u["nickname"], "reason": "无法获取账号ID"})
                continue

            try:
                creator = await self.add_creator(db, u["platform"], identifier, tenant_id=tenant_id)
                # 抓取视频内容
                try:
                    new_videos = await self.crawl_creator_videos(db, creator.id, max_videos=30)
                    added.append({
                        "id": creator.id,
                        "nickname": creator.nickname,
                        "follower_count": creator.follower_count,
                        "new_videos": new_videos,
                        "platform": creator.platform,
                        "already_existed": False,
                    })
                except Exception as ve:
                    added.append({
                        "id": creator.id,
                        "nickname": creator.nickname,
                        "follower_count": creator.follower_count,
                        "new_videos": 0,
                        "platform": creator.platform,
                        "crawl_error": str(ve),
                    })
            except ValueError as e:
                if "已存在" in str(e) or "already" in str(e).lower():
                    skipped.append({"nickname": u["nickname"], "reason": "已在库中"})
                else:
                    failed.append({"nickname": u["nickname"], "reason": str(e)})
            except Exception as e:
                failed.append({"nickname": u["nickname"], "reason": str(e)})

            # 防止请求过快被封
            await asyncio.sleep(0.8)

        if progress_callback:
            await progress_callback(total, total, "完成", "done")

        return {
            "total_found": total,
            "added": len(added),
            "skipped": len(skipped),
            "failed": len(failed),
            "creators": added,
            "failed_list": failed,
        }

    async def _resolve_xhs_user_id(self, identifier: str) -> str:
        """
        智能解析小红书用户标识 → 内部 user_id
        支持格式：
          1. 内部 user_id（24位hex）→ 直接返回
          2. 小红书主页链接 → 通过 API 提取
          3. 小红书号（redId）→ 通过搜索匹配
        """
        import re
        identifier = identifier.strip()

        # 1) 已经是 24 位 hex user_id
        if re.fullmatch(r'[0-9a-f]{24}', identifier):
            return identifier

        # 2) 是链接 → 提取 user_id
        if 'xiaohongshu.com' in identifier or 'xhslink.com' in identifier:
            try:
                resp = await tikhub.xhs_get_user_id_from_share_link(identifier)
                uid = resp.get("data", {}).get("user_id", "")
                if uid:
                    print(f"[Crawler] XHS share link resolved to user_id={uid}")
                    return uid
            except Exception as e:
                print(f"[Crawler] XHS share link extraction failed: {e}")

        # 3) 小红书号 → 搜索用户，匹配 redId（带重试）
        for attempt in range(3):
            try:
                resp = await tikhub.xhs_search_users(identifier, page=1)
                break
            except Exception as _e:
                if attempt < 2:
                    print(f"[Crawler] XHS search attempt {attempt+1} failed: {_e}, retrying...")
                    await asyncio.sleep(1)
                    continue
                resp = {}
        try:
            # web/search_users: data.data.users[].{id, red_id, name}
            search_data = resp.get("data", {})
            inner = search_data.get("data", {})
            users = inner.get("users") or search_data.get("users") or search_data.get("user_list") or []
            for u in users:
                user_info = u.get("user_info") or u
                red_id = user_info.get("red_id") or user_info.get("redId") or ""
                user_id = user_info.get("id") or user_info.get("user_id") or user_info.get("userId") or ""
                if red_id == identifier and user_id:
                    print(f"[Crawler] XHS redId '{identifier}' matched user_id={user_id}")
                    return user_id
            # 如果精确匹配失败，取第一个结果（用户可能搜的是昵称）
            if users:
                first = users[0].get("user_info") or users[0]
                uid = first.get("id") or first.get("user_id") or first.get("userId") or ""
                if uid:
                    print(f"[Crawler] XHS search fallback: first result user_id={uid}")
                    return uid
        except Exception as e:
            print(f"[Crawler] XHS search failed: {e}")

        # 兜底：原样返回，让 fetch_user_info 尝试
        return identifier

    async def _fetch_profile(self, platform: str, identifier: str, resolved_user_id: str = None) -> dict | None:
        try:
            if platform == "douyin":
                raw = await tikhub.douyin_get_user_by_unique_id(identifier)
                print(f"[Crawler] douyin raw status_code={raw.get('status_code')} message={raw.get('message')}")
                profile = tikhub.parse_douyin_user(raw)
                print(f"[Crawler] parsed profile: {profile}")
                if not profile.get("platform_id"):
                    print(f"[Crawler] WARNING: empty platform_id, raw data keys: {list(raw.get('data', {}).keys())}")
                    return None
                return profile
            elif platform == "xiaohongshu":
                # 如果已经解析过 user_id 就直接用，避免重复搜索
                user_id = resolved_user_id or await self._resolve_xhs_user_id(identifier)
                raw = await tikhub.xhs_get_user_info(user_id)
                return tikhub.parse_xhs_user(raw)
            elif platform == "weixin":
                raw = await tikhub.wechat_channels_get_home_page(identifier)
                return tikhub.parse_wechat_channels_user(raw, username=identifier)
        except Exception as e:
            import traceback
            print(f"[Crawler] fetch_profile error: {e}\n{traceback.format_exc()}")
            return None

    async def _fetch_videos(self, platform: str, platform_id: str, max_videos: int) -> list[dict]:
        videos = []
        try:
            if platform == "douyin":
                cursor = 0
                while len(videos) < max_videos:
                    raw = await tikhub.douyin_get_user_videos(platform_id, cursor)
                    data = raw.get("data", {})
                    items = data.get("aweme_list", [])
                    for v in items:
                        videos.append(tikhub.parse_douyin_video(v))
                    has_more = data.get("has_more", False)
                    cursor = data.get("max_cursor", 0)
                    if not has_more or not items:
                        break
                    await asyncio.sleep(0.5)

            elif platform == "xiaohongshu":
                cursor = ""
                while len(videos) < max_videos:
                    raw = await tikhub.xhs_get_user_notes(platform_id, cursor)
                    data = raw.get("data", {})
                    # app/get_user_notes: data.data.notes
                    inner = data.get("data") if isinstance(data.get("data"), dict) else {}
                    items = inner.get("notes") or data.get("notes") or data.get("list") or []
                    for n in items:
                        videos.append(tikhub.parse_xhs_note(n))
                    # cursor 在每条笔记的 cursor 字段里，取最后一条
                    has_more = inner.get("has_more", False)
                    cursor = items[-1].get("cursor", "") if items else ""
                    if not has_more or not cursor or not items:
                        break
                    await asyncio.sleep(0.5)

            elif platform == "weixin":
                last_buffer = ""
                while len(videos) < max_videos:
                    raw = await tikhub.wechat_channels_get_home_page(platform_id, last_buffer)
                    data = raw.get("data", {})
                    items = data.get("object", [])
                    for v in items:
                        videos.append(tikhub.parse_wechat_channels_video(v))
                    if not items:
                        break
                    # pagination: last_buffer from response data level
                    last_buffer = data.get("last_buffer", "")
                    if not last_buffer:
                        break
                    await asyncio.sleep(0.5)

        except Exception as e:
            import traceback
            print(f"[Crawler] fetch_videos error ({platform}/{platform_id}): {e}")
            traceback.print_exc()

        return videos[:max_videos]


    async def _backfill_douyin_play_counts(self, db: Session, creator_id: int):
        """
        用批量统计接口补齐 play_count 并重算互动比。
        对批量接口未返回的视频，逐条用详情接口重试。
        """
        videos = (
            db.query(CreatorVideo)
            .filter(CreatorVideo.creator_id == creator_id, CreatorVideo.platform == "douyin")
            .filter(CreatorVideo.video_id != None)
            .all()
        )
        if not videos:
            return

        missed_videos = []  # 批量接口未覆盖的视频

        # ── 第一轮：批量统计接口 ──
        batch_size = 20
        for i in range(0, len(videos), batch_size):
            batch = videos[i:i + batch_size]
            aweme_ids = [v.video_id for v in batch if v.video_id]
            if not aweme_ids:
                continue
            try:
                raw = await tikhub.douyin_fetch_video_statistics(aweme_ids)
                stats_list = raw.get("data", {}).get("statistics_list", [])
                stats_map = {s["aweme_id"]: s for s in stats_list if isinstance(s, dict)}

                for v in batch:
                    s = stats_map.get(v.video_id)
                    if not s:
                        missed_videos.append(v)
                        continue
                    self._apply_stats(v, s)

                db.commit()
                print(f"[Crawler] 已补齐 {len(stats_map)} 条视频播放量 (batch {i//batch_size+1})")
            except Exception as e:
                print(f"[Crawler] 批量拉取播放量失败: {e}")
                missed_videos.extend(batch)
            await asyncio.sleep(0.5)

        # ── 第二轮：逐条详情接口重试未覆盖的视频 ──
        if missed_videos:
            print(f"[Crawler] 批量接口遗漏 {len(missed_videos)} 条，逐条重试...")
            retry_ok = 0
            for v in missed_videos:
                try:
                    raw = await tikhub.douyin_get_video_detail(v.video_id)
                    aweme = raw.get("data", {}).get("aweme_detail", raw.get("data", {}))
                    stats = aweme.get("statistics", {})
                    if stats:
                        self._apply_stats(v, stats)
                        retry_ok += 1
                except Exception as e:
                    print(f"[Crawler] 单条重试 {v.video_id} 失败: {e}")
                await asyncio.sleep(0.3)
            db.commit()
            print(f"[Crawler] 逐条重试完成，成功 {retry_ok}/{len(missed_videos)}")

    @staticmethod
    def _apply_stats(v: CreatorVideo, s: dict):
        """将统计数据应用到视频记录"""
        play = s.get("play_count", 0)
        if play and play > 0:
            v.play_count = play
            v.like_play_ratio = round((v.like_count or 0) / play, 6)
            v.comment_play_ratio = round((v.comment_count or 0) / play, 6)
            v.collect_play_ratio = round((v.collect_count or 0) / play, 6)
        if s.get("digg_count"):
            v.like_count = s["digg_count"]
        if s.get("share_count"):
            v.share_count = s["share_count"]
        if s.get("collect_count"):
            v.collect_count = s["collect_count"]


crawler_service = CrawlerService()
