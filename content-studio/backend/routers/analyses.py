import asyncio

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import Creator, CreatorVideo, TenantCreator, Topic, User
from routers.deps import require_active_subscription
from services.analyzer import analyzer_service
from services.analysis_jobs import (
    create_creator_batch_task,
    get_running_task_for_creator,
    get_task,
    start_creator_batch_task,
)
from services.topic_hunter import topic_hunter

router = APIRouter()


class BatchAnalyzeRequest(BaseModel):
    video_ids: list[int] = []
    topic_ids: list[int] = []


@router.post("/videos/{video_id}/analyze")
async def analyze_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    video = db.query(CreatorVideo).filter(CreatorVideo.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    sub = db.query(TenantCreator).filter(
        TenantCreator.creator_id == video.creator_id,
        TenantCreator.tenant_id == current_user.tenant_id,
    ).first()
    if not sub:
        raise HTTPException(status_code=404, detail="视频不存在")

    try:
        return await analyzer_service.analyze_video_viral(
            db,
            video_id=video_id,
            tenant_id=current_user.tenant_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/videos/{video_id}/analysis")
def get_video_analysis(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    video = db.query(CreatorVideo).filter(CreatorVideo.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    sub = db.query(TenantCreator).filter(
        TenantCreator.creator_id == video.creator_id,
        TenantCreator.tenant_id == current_user.tenant_id,
    ).first()
    if not sub:
        raise HTTPException(status_code=404, detail="视频不存在")

    result = analyzer_service.get_video_analysis(db, video_id, tenant_id=current_user.tenant_id)
    if not result:
        raise HTTPException(status_code=404, detail="该视频尚未分析，请先调用分析接口")
    return result


@router.post("/topics/{topic_id}/analyze")
async def analyze_topic(
    topic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    topic = db.query(Topic).filter(Topic.id == topic_id, Topic.user_id == current_user.id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="选题不存在")

    raw_script = (topic.script or "").strip()
    needs_fetch = (
        not raw_script
        or raw_script == (topic.title or "").strip()
        or raw_script == (topic.description or "").strip()
    )
    if needs_fetch and topic.video_id:
        try:
            detail = await topic_hunter.fetch_video_detail(
                platform=topic.platform,
                video_id=topic.video_id,
                comment_count=20,
            )
            if detail.get("script"):
                topic.script = detail["script"]
            if detail.get("top_comments"):
                topic.top_comments = detail["top_comments"]
            if detail.get("share_url"):
                topic.video_url = detail["share_url"]
            db.commit()
        except Exception as exc:
            print(f"[Router] analyze_topic prefetch failed (topic={topic_id}): {exc}")

    try:
        result = await analyzer_service.analyze_video_viral(
            db,
            topic_id=topic_id,
            tenant_id=current_user.tenant_id,
        )
        return {
            **result,
            "script": topic.script or "",
            "description": topic.description or "",
            "title": topic.title or "",
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/topics/{topic_id}/analysis")
def get_topic_analysis(
    topic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    topic = db.query(Topic).filter(Topic.id == topic_id, Topic.user_id == current_user.id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="选题不存在")

    result = analyzer_service.get_topic_analysis(db, topic_id, tenant_id=current_user.tenant_id)
    if not result:
        raise HTTPException(status_code=404, detail="该选题尚未分析")
    return {
        **result,
        "script": topic.script or "",
        "description": topic.description or "",
        "title": topic.title or "",
    }


@router.post("/topics/batch-analyze")
async def batch_analyze_topics(
    req: BatchAnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    results = []

    if req.topic_ids:
        valid_topics = db.query(Topic.id).filter(
            Topic.id.in_(req.topic_ids),
            Topic.user_id == current_user.id,
        ).all()
        valid_tids = {t.id for t in valid_topics}
    else:
        valid_tids = set()

    for tid in req.topic_ids:
        if tid not in valid_tids:
            results.append({"topic_id": tid, "error": "选题不存在"})
            continue
        try:
            result = await analyzer_service.analyze_video_viral(
                db,
                topic_id=tid,
                tenant_id=current_user.tenant_id,
            )
            results.append(result)
            await asyncio.sleep(0.3)
        except Exception as exc:
            results.append({"topic_id": tid, "error": str(exc)})

    if req.video_ids:
        valid_videos = (
            db.query(CreatorVideo.id)
            .join(Creator, Creator.id == CreatorVideo.creator_id)
            .join(TenantCreator, TenantCreator.creator_id == Creator.id)
            .filter(
                CreatorVideo.id.in_(req.video_ids),
                TenantCreator.tenant_id == current_user.tenant_id,
            )
            .all()
        )
        valid_vids = {v.id for v in valid_videos}
    else:
        valid_vids = set()

    for vid in req.video_ids:
        if vid not in valid_vids:
            results.append({"video_id": vid, "error": "视频不存在"})
            continue
        try:
            result = await analyzer_service.analyze_video_viral(
                db,
                video_id=vid,
                tenant_id=current_user.tenant_id,
            )
            results.append(result)
            await asyncio.sleep(0.3)
        except Exception as exc:
            results.append({"video_id": vid, "error": str(exc)})

    return {"total": len(results), "results": results}


@router.post("/creators/{creator_id}/videos/analyze")
async def batch_analyze_creator_videos(
    creator_id: int,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    sub = db.query(TenantCreator).filter(
        TenantCreator.creator_id == creator_id,
        TenantCreator.tenant_id == current_user.tenant_id,
    ).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Creator not found")

    videos = (
        db.query(CreatorVideo)
        .filter(CreatorVideo.creator_id == creator_id)
        .order_by(CreatorVideo.like_count.desc())
        .limit(limit)
        .all()
    )
    if not videos:
        raise HTTPException(status_code=404, detail="该博主暂无视频")

    video_ids = [v.id for v in videos]
    results = await analyzer_service.batch_analyze_videos(
        db,
        video_ids,
        tenant_id=current_user.tenant_id,
    )
    return {"total": len(results), "results": results}


@router.post("/creators/{creator_id}/videos/analyze-async")
async def batch_analyze_creator_videos_async(
    creator_id: int,
    limit: int = 200,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    sub = db.query(TenantCreator).filter(
        TenantCreator.creator_id == creator_id,
        TenantCreator.tenant_id == current_user.tenant_id,
    ).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Creator not found")

    videos = (
        db.query(CreatorVideo)
        .filter(CreatorVideo.creator_id == creator_id)
        .order_by(CreatorVideo.like_count.desc())
        .limit(limit)
        .all()
    )
    if not videos:
        raise HTTPException(status_code=404, detail="该博主暂无视频")

    running_task = get_running_task_for_creator(
        creator_id=creator_id,
        tenant_id=current_user.tenant_id,
    )
    if running_task:
        return {
            "task_id": running_task["task_id"],
            "total": running_task["total"],
            "message": "已有进行中的批量分析任务",
        }

    video_ids = [v.id for v in videos]
    task = create_creator_batch_task(
        creator_id=creator_id,
        tenant_id=current_user.tenant_id,
        total=len(video_ids),
    )
    start_creator_batch_task(
        task_id=task["task_id"],
        video_ids=video_ids,
        tenant_id=current_user.tenant_id,
    )
    return {
        "task_id": task["task_id"],
        "total": len(video_ids),
        "message": "分析任务已在后台启动",
    }


@router.get("/creators/analyze-task/{task_id}")
def get_analyze_task(
    task_id: str,
    current_user: User = Depends(require_active_subscription),
):
    task = get_task(task_id, tenant_id=current_user.tenant_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task
