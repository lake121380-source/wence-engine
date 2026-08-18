import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import Topic, User, VideoAnalysis
from routers.deps import require_active_subscription
from services.topic_hunter import topic_hunter

router = APIRouter()

# 互动比阈值（与 analyzer.py 一致）
_RATIO_TH = {
    "like_play":    {"high": 0.05, "medium": 0.02},
    "comment_play": {"high": 0.01, "medium": 0.005},
    "collect_play": {"high": 0.03, "medium": 0.01},
}

def _rate_level(value, key: str) -> str:
    if value is None:
        return "low"
    t = _RATIO_TH.get(key, {})
    if value >= t.get("high", 1):
        return "high"
    if value >= t.get("medium", 0.5):
        return "medium"
    return "low"


class TopicSearchRequest(BaseModel):
    keyword: str
    platforms: list[str] = ["douyin"]
    limit: int = 30
    sort: str = "likes"
    save: bool = True
    min_likes: int = 0
    days: int = 0
    video_type: str = ""
    pages: int = 1


class TopicStatusRequest(BaseModel):
    status: str


class SaveTopicRequest(BaseModel):
    """手动保存单条搜索结果到选题库"""

    keyword: str = ""
    platform: str = "douyin"
    video_id: str
    title: str = ""
    description: str = ""
    author: str = ""
    author_id: str = ""
    cover_url: str = ""
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    play_count: int = 0
    collect_count: int = 0
    tags: list[str] = []
    author_unique_id: str = ""
    author_avatar: str = ""
    author_follower_count: int = 0
    author_bio: str = ""
    author_url: str = ""
    video_url: str = ""
    create_time: int = 0
    like_play_ratio: float = 0
    comment_play_ratio: float = 0
    collect_play_ratio: float = 0


@router.post("/topics/search")
async def search_topics(
    req: TopicSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    """关键词搜索爆款视频，可选保存到本地"""
    try:
        videos, search_errors = await topic_hunter.search_viral_videos(
            keyword=req.keyword,
            platforms=req.platforms,
            limit=req.limit,
            sort=req.sort,
            min_likes=req.min_likes,
            days=req.days,
            pages=req.pages,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    douyin_vids = [v for v in videos if v.get("platform") == "douyin" and v.get("video_id")]
    if douyin_vids:
        try:
            batch_size = 20
            for i in range(0, len(douyin_vids), batch_size):
                batch = douyin_vids[i : i + batch_size]
                ids = [v["video_id"] for v in batch]
                from services.tikhub import tikhub

                raw = await tikhub.douyin_fetch_video_statistics(ids)
                stats_list = raw.get("data", {}).get("statistics_list", [])
                stats_map = {s["aweme_id"]: s for s in stats_list if isinstance(s, dict)}
                for v in batch:
                    stats = stats_map.get(v["video_id"])
                    if stats:
                        real_play = stats.get("play_count", 0)
                        if real_play and real_play > 0:
                            v["play_count"] = real_play
                            v["like_play_ratio"] = round((v.get("like_count", 0)) / real_play, 6)
                            v["comment_play_ratio"] = round((v.get("comment_count", 0)) / real_play, 6)
                            v["collect_play_ratio"] = round((v.get("collect_count", 0)) / real_play, 6)
                        if stats.get("digg_count"):
                            v["like_count"] = stats["digg_count"]
                        if stats.get("share_count"):
                            v["share_count"] = stats["share_count"]
                        if stats.get("collect_count"):
                            v["collect_count"] = stats["collect_count"]
                await asyncio.sleep(0.3)
        except Exception as exc:
            print(f"[Topics] 批量拉取播放量失败: {exc}")

    saved_ids = []
    if req.save and videos:
        for v in videos:
            existing = db.query(Topic).filter(
                Topic.platform == v.get("platform"),
                Topic.video_id == v.get("video_id"),
                Topic.user_id == current_user.id,
            ).first()
            if existing:
                existing.like_count = v.get("like_count", existing.like_count)
                existing.comment_count = v.get("comment_count", existing.comment_count)
                existing.share_count = v.get("share_count", existing.share_count)
                existing.play_count = v.get("play_count", existing.play_count)
                existing.collect_count = v.get("collect_count", 0)
                existing.author = v.get("author", "") or existing.author
                existing.author_follower_count = v.get("author_follower_count", 0)
                existing.author_bio = v.get("author_bio", "")
                existing.author_avatar = v.get("author_avatar", "")
                existing.author_url = v.get("author_url", "")
                existing.author_unique_id = v.get("author_unique_id", "")
                existing.video_url = v.get("video_url", "")
                existing.video_create_time = v.get("create_time", 0)
                existing.like_play_ratio = v.get("like_play_ratio", 0)
                existing.comment_play_ratio = v.get("comment_play_ratio", 0)
                existing.collect_play_ratio = v.get("collect_play_ratio", 0)
                saved_ids.append(existing.id)
                v["id"] = existing.id
                continue

            topic = Topic(
                keyword=req.keyword,
                platform=v.get("platform", ""),
                video_id=v.get("video_id", ""),
                title=v.get("title", ""),
                description=v.get("description", ""),
                author=v.get("author", ""),
                author_id=v.get("author_id", ""),
                cover_url=v.get("cover_url", ""),
                like_count=v.get("like_count", 0),
                comment_count=v.get("comment_count", 0),
                share_count=v.get("share_count", 0),
                play_count=v.get("play_count", 0),
                collect_count=v.get("collect_count", 0),
                tags=v.get("tags", []),
                author_unique_id=v.get("author_unique_id", ""),
                author_avatar=v.get("author_avatar", ""),
                author_follower_count=v.get("author_follower_count", 0),
                author_bio=v.get("author_bio", ""),
                author_url=v.get("author_url", ""),
                video_url=v.get("video_url", ""),
                video_create_time=v.get("create_time", 0),
                like_play_ratio=v.get("like_play_ratio", 0),
                comment_play_ratio=v.get("comment_play_ratio", 0),
                collect_play_ratio=v.get("collect_play_ratio", 0),
                tenant_id=current_user.tenant_id,
                user_id=current_user.id,
            )
            db.add(topic)
            db.flush()
            saved_ids.append(topic.id)
            v["id"] = topic.id
        db.commit()

    # 查询已有分析记录
    all_topic_ids = [v.get("id") for v in videos if v.get("id")]
    analyses_map = {}
    if all_topic_ids:
        rows = db.query(VideoAnalysis).filter(
            VideoAnalysis.topic_id.in_(all_topic_ids),
            VideoAnalysis.tenant_id == current_user.tenant_id,
        ).all()
        for a in rows:
            analyses_map[a.topic_id] = {
                "like_play_ratio": a.like_play_ratio,
                "comment_play_ratio": a.comment_play_ratio,
                "collect_play_ratio": a.collect_play_ratio,
                "resonance_analysis": a.resonance_analysis,
                "discussion_analysis": a.discussion_analysis,
                "value_analysis": a.value_analysis,
                "why_viral_summary": a.why_viral_summary,
                "like_play_level": _rate_level(a.like_play_ratio, "like_play"),
                "comment_play_level": _rate_level(a.comment_play_ratio, "comment_play"),
                "collect_play_level": _rate_level(a.collect_play_ratio, "collect_play"),
            }
    for v in videos:
        tid = v.get("id")
        v["has_analysis"] = tid in analyses_map
        v["analysis"] = analyses_map.get(tid)

    warnings = []
    if search_errors:
        warnings.append(f"部分平台搜索失败: {'; '.join(search_errors)}")
    return {"total": len(videos), "videos": videos, "saved_ids": saved_ids, "warnings": warnings}


@router.post("/topics/save")
def save_topic(
    req: SaveTopicRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    """手动保存一条搜索结果到选题库"""
    existing = db.query(Topic).filter(
        Topic.platform == req.platform,
        Topic.video_id == req.video_id,
        Topic.user_id == current_user.id,
    ).first()
    if existing:
        return {"id": existing.id, "already_saved": True}

    topic = Topic(
        keyword=req.keyword,
        platform=req.platform,
        video_id=req.video_id,
        title=req.title,
        description=req.description,
        author=req.author,
        author_id=req.author_id,
        cover_url=req.cover_url,
        like_count=req.like_count,
        comment_count=req.comment_count,
        share_count=req.share_count,
        play_count=req.play_count,
        collect_count=req.collect_count,
        tags=req.tags,
        author_unique_id=req.author_unique_id,
        author_avatar=req.author_avatar,
        author_follower_count=req.author_follower_count,
        author_bio=req.author_bio,
        author_url=req.author_url,
        video_url=req.video_url,
        video_create_time=req.create_time,
        like_play_ratio=req.like_play_ratio,
        comment_play_ratio=req.comment_play_ratio,
        collect_play_ratio=req.collect_play_ratio,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
    )
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return {"id": topic.id, "already_saved": False}


@router.post("/topics/{topic_id}/fetch-detail")
async def fetch_topic_detail(
    topic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    """获取单个选题的视频文案 + 热门评论"""
    topic = db.query(Topic).filter(Topic.id == topic_id, Topic.user_id == current_user.id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    cached_script = (topic.script or "").strip()
    script_ok = (
        cached_script
        and cached_script != (topic.title or "").strip()
        and cached_script != (topic.description or "").strip()
    )
    if script_ok and topic.top_comments:
        return {
            "id": topic.id,
            "script": topic.script,
            "top_comments": topic.top_comments,
            "video_url": topic.video_url,
            "cached": True,
        }

    detail = await topic_hunter.fetch_video_detail(
        platform=topic.platform,
        video_id=topic.video_id,
        comment_count=30,
    )

    topic.script = detail.get("script", "")
    if detail.get("share_url"):
        topic.video_url = detail["share_url"]
    topic.top_comments = detail.get("top_comments", [])
    db.commit()

    return {
        "id": topic.id,
        "script": topic.script,
        "top_comments": topic.top_comments,
        "video_url": topic.video_url,
    }


@router.post("/topics/batch-fetch-detail")
async def batch_fetch_detail(
    topic_ids: list[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    """批量获取选题的视频文案 + 评论"""
    topics = db.query(Topic).filter(Topic.id.in_(topic_ids), Topic.user_id == current_user.id).all()
    results = []
    for topic in topics:
        try:
            detail = await topic_hunter.fetch_video_detail(
                platform=topic.platform,
                video_id=topic.video_id,
                comment_count=20,
            )
            topic.script = detail.get("script", "")
            if detail.get("share_url"):
                topic.video_url = detail["share_url"]
            topic.top_comments = detail.get("top_comments", [])
            results.append({"id": topic.id, "ok": True})
        except Exception as exc:
            results.append({"id": topic.id, "ok": False, "error": str(exc)})
        await asyncio.sleep(0.3)
    db.commit()
    return {"results": results, "total": len(results)}


@router.get("/topics/keywords")
def list_topic_keywords(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    """列出用户搜索过的关键词（去重，按最近搜索排序）"""
    from sqlalchemy import desc, func

    rows = (
        db.query(
            Topic.keyword,
            func.count(Topic.id).label("count"),
            func.max(Topic.created_at).label("last_at"),
        )
        .filter(Topic.user_id == current_user.id, Topic.keyword != None, Topic.keyword != "")
        .group_by(Topic.keyword)
        .order_by(desc("last_at"))
        .limit(50)
        .all()
    )
    return [{"keyword": r.keyword, "count": r.count, "last_at": r.last_at} for r in rows]


@router.get("/topics")
def list_topics(
    keyword: Optional[str] = None,
    platform: Optional[str] = None,
    status: Optional[str] = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    """列出已保存的选题"""
    q = db.query(Topic).filter(Topic.user_id == current_user.id)
    if keyword:
        q = q.filter(Topic.keyword == keyword)
    if platform:
        q = q.filter(Topic.platform == platform)
    if status:
        q = q.filter(Topic.status == status)
    topics = q.order_by(Topic.like_count.desc()).offset(offset).limit(limit).all()

    # 批量查询已有分析记录
    topic_ids = [t.id for t in topics]
    analyses_map = {}
    if topic_ids:
        rows = db.query(VideoAnalysis).filter(
            VideoAnalysis.topic_id.in_(topic_ids),
            VideoAnalysis.tenant_id == current_user.tenant_id,
        ).all()
        for a in rows:
            analyses_map[a.topic_id] = {
                "like_play_ratio": a.like_play_ratio,
                "comment_play_ratio": a.comment_play_ratio,
                "collect_play_ratio": a.collect_play_ratio,
                "resonance_analysis": a.resonance_analysis,
                "discussion_analysis": a.discussion_analysis,
                "value_analysis": a.value_analysis,
                "why_viral_summary": a.why_viral_summary,
                "like_play_level": _rate_level(a.like_play_ratio, "like_play"),
                "comment_play_level": _rate_level(a.comment_play_ratio, "comment_play"),
                "collect_play_level": _rate_level(a.collect_play_ratio, "collect_play"),
            }

    return [
        {
            "id": t.id,
            "keyword": t.keyword,
            "platform": t.platform,
            "video_id": t.video_id,
            "title": t.title,
            "author": t.author,
            "author_avatar": t.author_avatar,
            "author_follower_count": t.author_follower_count,
            "author_bio": t.author_bio,
            "author_url": t.author_url,
            "cover_url": t.cover_url,
            "video_url": t.video_url,
            "like_count": t.like_count,
            "comment_count": t.comment_count,
            "share_count": t.share_count,
            "play_count": t.play_count,
            "collect_count": t.collect_count,
            "like_play_ratio": t.like_play_ratio,
            "comment_play_ratio": t.comment_play_ratio,
            "collect_play_ratio": t.collect_play_ratio,
            "tags": t.tags,
            "script": t.script,
            "top_comments": t.top_comments,
            "video_create_time": t.video_create_time,
            "status": t.status,
            "created_at": t.created_at,
            "has_analysis": t.id in analyses_map,
            "analysis": analyses_map.get(t.id),
        }
        for t in topics
    ]


@router.patch("/topics/{topic_id}/status")
def update_topic_status(
    topic_id: int,
    req: TopicStatusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    topic = db.query(Topic).filter(Topic.id == topic_id, Topic.user_id == current_user.id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    valid_statuses = {"待评审", "已采纳", "已使用", "已忽略"}
    if req.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"无效状态，可选: {valid_statuses}")

    topic.status = req.status
    db.commit()
    return {"ok": True, "status": req.status}


@router.delete("/topics/{topic_id}")
def delete_topic(
    topic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    topic = db.query(Topic).filter(Topic.id == topic_id, Topic.user_id == current_user.id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    db.delete(topic)
    db.commit()
    return {"ok": True}


class BatchDeleteRequest(BaseModel):
    ids: list[int]


@router.post("/topics/batch-delete")
def batch_delete_topics(
    req: BatchDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    """批量删除已保存的选题"""
    deleted = db.query(Topic).filter(
        Topic.id.in_(req.ids),
        Topic.user_id == current_user.id,
    ).delete(synchronize_session=False)
    db.commit()
    return {"ok": True, "deleted": deleted}
