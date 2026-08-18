import asyncio
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import SessionLocal, get_db
from models import Creator, CreatorVideo, Document, TenantCreator, User, VideoAnalysis
from routers.deps import require_active_subscription
from services.analyzer import analyzer_service
from services.crawler import crawler_service
from services.generator import generator_service
from services.topic_hunter import topic_hunter

router = APIRouter()

_discover_tasks: dict[str, dict] = {}


class AddCreatorRequest(BaseModel):
    platform: str
    identifier: str


class AutoDiscoverRequest(BaseModel):
    keyword: str
    limit: int = 30
    platforms: list[str] = ["douyin"]


class CreatorDiscoverRequest(BaseModel):
    keyword: str
    limit: int = 30


class CombinedStyleRequest(BaseModel):
    creator_ids: list[int]
    template_name: str
    platform: str = "douyin"


@router.get("/creators")
def list_creators(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    subscribed_ids = db.query(TenantCreator.creator_id).filter(
        TenantCreator.tenant_id == current_user.tenant_id
    ).subquery()
    creators = (
        db.query(Creator)
        .filter(Creator.id.in_(subscribed_ids))
        .order_by(Creator.follower_count.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    result = []
    for creator in creators:
        style_template = next(
            (t for t in creator.style_templates if t.tenant_id == current_user.tenant_id),
            None,
        )
        result.append(
            {
                "id": creator.id,
                "platform": creator.platform,
                "nickname": creator.nickname,
                "unique_id": creator.unique_id,
                "follower_count": creator.follower_count,
                "video_count": creator.video_count,
                "avatar_url": creator.avatar_url,
                "is_active": creator.is_active,
                "last_crawled_at": creator.last_crawled_at,
                "videos_in_db": len(creator.videos),
                "tags": creator.tags,
                "has_style": style_template is not None,
                "style_updated_at": style_template.updated_at if style_template else None,
                "style_name": style_template.name if style_template else None,
            }
        )
    return result


@router.post("/creators")
async def add_creator(
    req: AddCreatorRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    if current_user.is_trial:
        existing_count = db.query(TenantCreator).filter(
            TenantCreator.tenant_id == current_user.tenant_id
        ).count()
        if existing_count >= 1:
            raise HTTPException(status_code=403, detail="试用期仅可添加 1 个博主，请升级后继续使用")

    try:
        creator = await crawler_service.add_creator(
            db,
            req.platform,
            req.identifier,
            tenant_id=current_user.tenant_id,
        )
        return {"id": creator.id, "nickname": creator.nickname, "platform": creator.platform}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/creators/{creator_id}/crawl")
async def crawl_creator(
    creator_id: int,
    max_videos: int = Query(default=30, ge=10, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    sub = db.query(TenantCreator).filter(
        TenantCreator.creator_id == creator_id,
        TenantCreator.tenant_id == current_user.tenant_id,
    ).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Creator not found")

    try:
        new_count = await crawler_service.crawl_creator_videos(db, creator_id, max_videos=max_videos)
        total = db.query(CreatorVideo).filter(CreatorVideo.creator_id == creator_id).count()
        if new_count == 0 and total > 0:
            return {
                "new_videos": 0,
                "total_videos": total,
                "message": f"数据已存在，共 {total} 条视频内容",
            }
        return {
            "new_videos": new_count,
            "total_videos": total,
            "message": f"新增 {new_count} 条视频内容",
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/creators/{creator_id}/analyze-style")
async def analyze_creator_style(
    creator_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    sub = db.query(TenantCreator).filter(
        TenantCreator.creator_id == creator_id,
        TenantCreator.tenant_id == current_user.tenant_id,
    ).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Creator not found")

    creator = db.query(Creator).filter(Creator.id == creator_id).first()
    if not creator:
        raise HTTPException(status_code=404, detail="Creator not found")

    try:
        return await generator_service.analyze_style(db, creator_id, tenant_id=current_user.tenant_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/creators/{creator_id}")
def delete_creator(
    creator_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    sub = db.query(TenantCreator).filter(
        TenantCreator.creator_id == creator_id,
        TenantCreator.tenant_id == current_user.tenant_id,
    ).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Creator not found")

    db.delete(sub)
    db.commit()
    return {"message": "deleted"}


@router.get("/creators/{creator_id}/videos")
def get_creator_videos(
    creator_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    sub = db.query(TenantCreator).filter(
        TenantCreator.creator_id == creator_id,
        TenantCreator.tenant_id == current_user.tenant_id,
    ).first()
    creator = db.query(Creator).filter(Creator.id == creator_id).first() if sub else None
    if not creator:
        raise HTTPException(status_code=404, detail="Creator not found")

    videos = (
        db.query(CreatorVideo)
        .filter(CreatorVideo.creator_id == creator_id)
        .order_by(CreatorVideo.like_count.desc())
        .limit(100)
        .all()
    )

    video_id_strs = [v.video_id for v in videos if v.video_id]
    in_docs_set = set()
    if video_id_strs:
        doc_refs = db.query(Document.source_ref).filter(
            Document.source_type == "creator_video",
            Document.source_ref.in_(video_id_strs),
            Document.tenant_id == current_user.tenant_id,
        ).all()
        in_docs_set = {row[0] for row in doc_refs}

    video_ids = [v.id for v in videos]
    analyses = {}
    if video_ids:
        rows = db.query(VideoAnalysis).filter(
            VideoAnalysis.video_id.in_(video_ids),
            VideoAnalysis.tenant_id == current_user.tenant_id,
        ).all()
        for row in rows:
            analyses[row.video_id] = row

    def _analysis_dict(row):
        if not row:
            return None
        return {
            "id": row.id,
            "like_play_ratio": row.like_play_ratio,
            "comment_play_ratio": row.comment_play_ratio,
            "collect_play_ratio": row.collect_play_ratio,
            "resonance_analysis": row.resonance_analysis,
            "discussion_analysis": row.discussion_analysis,
            "value_analysis": row.value_analysis,
            "why_viral_summary": row.why_viral_summary,
        }

    return [
        {
            "id": v.id,
            "video_id": v.video_id,
            "title": v.title,
            "description": v.description,
            "script": v.script,
            "like_count": v.like_count,
            "play_count": v.play_count,
            "comment_count": v.comment_count,
            "collect_count": v.collect_count,
            "tags": v.tags,
            "cover_url": v.cover_url,
            "video_url": v.video_url,
            "published_at": v.published_at,
            "note_type": (v.raw_data or {}).get("type", "") if v.platform == "xiaohongshu" else None,
            "like_play_ratio": v.like_play_ratio
            if (v.play_count and v.play_count > 0 and v.like_play_ratio is not None)
            else None,
            "comment_play_ratio": v.comment_play_ratio
            if (v.comment_play_ratio is not None and 0 <= v.comment_play_ratio <= 1)
            else (
                round((v.comment_count or 0) / (v.like_count * 20), 6)
                if v.like_count and not (v.play_count or 0)
                else None
            ),
            "collect_play_ratio": v.collect_play_ratio
            if (v.collect_play_ratio is not None and 0 <= v.collect_play_ratio <= 1)
            else (
                round((v.collect_count or 0) / (v.like_count * 20), 6)
                if v.like_count and not (v.play_count or 0)
                else None
            ),
            "analysis": _analysis_dict(analyses.get(v.id)),
            "in_docs": v.video_id in in_docs_set,
        }
        for v in videos
    ]


@router.get("/creators/search-weixin")
async def search_weixin_creators(
    keyword: str = Query(..., min_length=1, max_length=50),
    page: int = Query(default=0, ge=0, le=10),
    current_user: User = Depends(require_active_subscription),
):
    """视频号博主搜索（按名字关键词）"""
    try:
        from services.tikhub import tikhub as th

        raw = await th.wechat_channels_search_users(keyword, page)
        data = raw.get("data", {})
        items = data.get("items", [])
        results = []
        for item in items:
            jump_info = item.get("jumpInfo", {})
            username = jump_info.get("userName", "")
            if not username:
                continue

            import re as _re

            _strip = lambda s: _re.sub(r"<[^>]+>", "", s or "")
            title = _strip(item.get("title", ""))
            desc = _strip(item.get("desc", ""))
            avatar = item.get("thumbUrl") or item.get("headUrl") or item.get("head_url") or ""
            results.append(
                {
                    "username": username,
                    "nickname": title,
                    "description": desc,
                    "avatar_url": avatar,
                }
            )
        return {"total": len(results), "creators": results}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/creators/discover")
async def discover_creators(
    req: CreatorDiscoverRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    """按关键词搜索抖音头部博主。"""
    try:
        results = await topic_hunter.discover_creators_by_keyword(db, req.keyword, req.limit)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {"total": len(results), "creators": results}


@router.post("/creators/batch-add")
async def batch_add_creators(
    creator_ids_to_add: list[str],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    """批量添加博主（来自 discover 结果），直接用 sec_uid 注册。"""
    if current_user.is_trial:
        existing_count = db.query(TenantCreator).filter(
            TenantCreator.tenant_id == current_user.tenant_id
        ).count()
        if existing_count >= 1:
            raise HTTPException(status_code=403, detail="试用期仅可添加 1 个博主，请升级后继续使用")
        creator_ids_to_add = creator_ids_to_add[:1]

    added, failed = [], []
    from services.tikhub import tikhub as th

    for sec_uid in creator_ids_to_add:
        try:
            raw = await th._get("/api/v1/douyin/web/fetch_user_profile", {"sec_user_id": sec_uid})
            profile = th.parse_douyin_user(raw)
            existing_creator = db.query(Creator).filter(
                Creator.platform == "douyin",
                Creator.platform_id == sec_uid,
            ).first()
            already_subbed = existing_creator and db.query(TenantCreator).filter(
                TenantCreator.tenant_id == current_user.tenant_id,
                TenantCreator.creator_id == existing_creator.id,
            ).first()
            if already_subbed:
                added.append({"sec_uid": sec_uid, "nickname": existing_creator.nickname, "already": True})
                continue

            if existing_creator:
                creator = existing_creator
            else:
                creator = Creator(**profile)
                db.add(creator)
                db.commit()
                db.refresh(creator)

            db.add(TenantCreator(tenant_id=current_user.tenant_id, creator_id=creator.id))
            db.commit()
            added.append({"sec_uid": sec_uid, "nickname": creator.nickname, "id": creator.id})
        except Exception as exc:
            failed.append({"sec_uid": sec_uid, "error": str(exc)})

    return {"added": added, "failed": failed}


@router.post("/creators/auto-discover-and-crawl")
async def auto_discover_and_crawl(
    req: AutoDiscoverRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_active_subscription),
):
    """一键发现头部博主并批量入库（异步后台任务）。"""
    current_tenant_id = current_user.tenant_id
    task_id = str(uuid.uuid4())
    _discover_tasks[task_id] = {
        "status": "pending",
        "progress": 0,
        "total": 0,
        "log": [],
        "result": None,
    }

    async def run_task():
        db = SessionLocal()
        task = _discover_tasks[task_id]
        task["status"] = "running"
        try:
            async def on_progress(step, total, msg, state="processing"):
                task["progress"] = step
                task["total"] = total
                task["log"].append(msg)
                if len(task["log"]) > 100:
                    task["log"] = task["log"][-100:]

            result = await crawler_service.auto_discover_and_crawl(
                db=db,
                keyword=req.keyword,
                limit=req.limit,
                platforms=req.platforms,
                progress_callback=on_progress,
                tenant_id=current_tenant_id,
            )
            task["status"] = "done"
            task["result"] = result
            task["progress"] = task["total"]
        except Exception as exc:
            task["status"] = "error"
            task["log"].append(f"错误: {str(exc)}")
        finally:
            db.close()

    background_tasks.add_task(run_task)
    return {"task_id": task_id, "message": "任务已启动"}


@router.get("/creators/discover-task/{task_id}")
def get_discover_task(
    task_id: str,
    current_user: User = Depends(require_active_subscription),
):
    """查询自动发现任务的进度。"""
    task = _discover_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.post("/style-templates/analyze-combined")
async def analyze_combined_style(
    req: CombinedStyleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    """多博主联合风格分析，生成融合风格模板。"""
    if req.creator_ids:
        valid_count = db.query(TenantCreator).filter(
            TenantCreator.creator_id.in_(req.creator_ids),
            TenantCreator.tenant_id == current_user.tenant_id,
        ).count()
        if valid_count != len(set(req.creator_ids)):
            raise HTTPException(status_code=403, detail="部分博主不属于当前租户")

    try:
        return await generator_service.analyze_combined_style(
            db=db,
            creator_ids=req.creator_ids,
            template_name=req.template_name,
            platform=req.platform,
            tenant_id=current_user.tenant_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/creators/{creator_id}/intel-card")
async def generate_intel_card(
    creator_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    """生成/刷新博主情报卡（AI四维度分析）。"""
    sub = db.query(TenantCreator).filter(
        TenantCreator.creator_id == creator_id,
        TenantCreator.tenant_id == current_user.tenant_id,
    ).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Creator not found")

    try:
        return await analyzer_service.generate_intel_card(db, creator_id, tenant_id=current_user.tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/creators/{creator_id}/intel-card")
def get_intel_card(
    creator_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    """获取博主情报卡。"""
    sub = db.query(TenantCreator).filter(
        TenantCreator.creator_id == creator_id,
        TenantCreator.tenant_id == current_user.tenant_id,
    ).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Creator not found")

    card = analyzer_service.get_intel_card(db, creator_id, tenant_id=current_user.tenant_id)
    if not card:
        raise HTTPException(status_code=404, detail="情报卡尚未生成，请先调用生成接口")
    return card
