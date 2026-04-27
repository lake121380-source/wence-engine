from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import Creator, CreatorVideo, OperatorViewpoint, Topic, User, VideoAnalysis
from routers.deps import require_active_subscription
from services.knowledge import knowledge_service

router = APIRouter()


class ViewpointCreateRequest(BaseModel):
    title: str
    category: str = "行业立场"
    content: str
    tags: str = ""


class ViewpointUpdateRequest(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("/analyses")
def list_analyses(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    """List all tenant-scoped VideoAnalysis records for UI selection."""
    records = (
        db.query(VideoAnalysis)
        .filter(VideoAnalysis.tenant_id == current_user.tenant_id)
        .order_by(VideoAnalysis.created_at.desc())
        .all()
    )
    result = []
    for row in records:
        entry = {
            "id": row.id,
            "video_id": row.video_id,
            "topic_id": row.topic_id,
            "like_play_ratio": row.like_play_ratio,
            "comment_play_ratio": row.comment_play_ratio,
            "collect_play_ratio": row.collect_play_ratio,
            "why_viral_summary": row.why_viral_summary,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "cover_url": None,
            "author_avatar": None,
            "source": "爆款分析",
        }

        if row.topic_id:
            topic = db.query(Topic).filter(Topic.id == row.topic_id).first()
            entry["title"] = topic.title if topic else f"选题 #{row.topic_id}"
            if topic:
                entry["cover_url"] = topic.cover_url
                entry["author_avatar"] = topic.author_avatar
                platform_label = topic.platform or "未知平台"
                author_label = topic.author or "匿名作者"
                entry["source"] = f"{platform_label} · {author_label}"
        elif row.video_id:
            video = db.query(CreatorVideo).filter(CreatorVideo.id == row.video_id).first()
            entry["title"] = video.title if video else f"视频 #{row.video_id}"
            if video:
                entry["cover_url"] = video.cover_url
                creator = db.query(Creator).filter(Creator.id == video.creator_id).first()
                if creator:
                    entry["author_avatar"] = creator.avatar_url
                    entry["source"] = f"{video.platform or '未知平台'} · {creator.nickname or '匿名博主'}"
                else:
                    entry["source"] = f"{video.platform or '未知平台'} · 视频内容"
        else:
            entry["title"] = f"分析 #{row.id}"
        result.append(entry)
    return result


@router.get("/viewpoints")
def list_viewpoints(
    category: Optional[str] = None,
    active_only: bool = False,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    q = db.query(OperatorViewpoint).filter(OperatorViewpoint.user_id == current_user.id)
    if category:
        q = q.filter(OperatorViewpoint.category == category)
    if active_only:
        q = q.filter(OperatorViewpoint.is_active == True)
    rows = q.order_by(OperatorViewpoint.created_at.desc()).offset(offset).limit(limit).all()
    return [_vp_to_dict(row) for row in rows]


@router.post("/viewpoints")
def create_viewpoint(
    req: ViewpointCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    vp = OperatorViewpoint(**req.model_dump(), tenant_id=current_user.tenant_id, user_id=current_user.id)
    db.add(vp)
    db.commit()
    db.refresh(vp)
    knowledge_service.index_viewpoint(
        vp.id,
        vp.title,
        vp.content,
        vp.category,
        vp.tags,
        tenant_id=current_user.tenant_id,
    )
    vp.indexed = True
    db.commit()
    return _vp_to_dict(vp)


@router.put("/viewpoints/{vp_id}")
def update_viewpoint(
    vp_id: int,
    req: ViewpointUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    vp = db.query(OperatorViewpoint).filter(
        OperatorViewpoint.id == vp_id,
        OperatorViewpoint.user_id == current_user.id,
    ).first()
    if not vp:
        raise HTTPException(status_code=404, detail="观点不存在")

    for field, value in req.model_dump(exclude_none=True).items():
        setattr(vp, field, value)

    vp.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(vp)
    knowledge_service.index_viewpoint(
        vp.id,
        vp.title,
        vp.content,
        vp.category,
        vp.tags,
        tenant_id=current_user.tenant_id,
    )
    return _vp_to_dict(vp)


@router.delete("/viewpoints/{vp_id}")
def delete_viewpoint(
    vp_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    vp = db.query(OperatorViewpoint).filter(
        OperatorViewpoint.id == vp_id,
        OperatorViewpoint.user_id == current_user.id,
    ).first()
    if not vp:
        raise HTTPException(status_code=404, detail="观点不存在")

    knowledge_service.delete_viewpoint(vp_id)
    db.delete(vp)
    db.commit()
    return {"message": "deleted"}


def _vp_to_dict(vp: OperatorViewpoint) -> dict:
    return {
        "id": vp.id,
        "title": vp.title,
        "category": vp.category,
        "content": vp.content,
        "tags": vp.tags,
        "is_active": vp.is_active,
        "indexed": vp.indexed,
        "created_at": vp.created_at,
        "updated_at": vp.updated_at,
    }
