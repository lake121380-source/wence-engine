from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import ContentSchedule, User
from routers.deps import require_active_subscription

router = APIRouter()
_VALID_STATUS = {"draft", "scheduled", "published"}


class ScheduleCreateRequest(BaseModel):
    title: str
    content: str = ""
    platform: str = "douyin"
    scheduled_date: datetime
    status: str = "draft"
    generation_id: Optional[int] = None


class ScheduleUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    platform: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    status: Optional[str] = None
    generation_id: Optional[int] = None


@router.get("/schedules")
def list_schedules(
    start: Optional[datetime] = Query(default=None),
    end: Optional[datetime] = Query(default=None),
    status: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    q = db.query(ContentSchedule).filter(ContentSchedule.user_id == current_user.id)
    if start:
        q = q.filter(ContentSchedule.scheduled_date >= start)
    if end:
        q = q.filter(ContentSchedule.scheduled_date <= end)
    if status:
        q = q.filter(ContentSchedule.status == status)

    rows = q.order_by(ContentSchedule.scheduled_date.asc(), ContentSchedule.created_at.desc()).all()
    return [
        {
            "id": x.id,
            "title": x.title,
            "content": x.content,
            "platform": x.platform,
            "scheduled_date": x.scheduled_date,
            "status": x.status,
            "generation_id": x.generation_id,
            "created_at": x.created_at,
        }
        for x in rows
    ]


@router.post("/schedules")
def create_schedule(
    req: ScheduleCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    if req.status not in _VALID_STATUS:
        raise HTTPException(status_code=400, detail=f"无效状态，可选: {_VALID_STATUS}")

    title = req.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="标题不能为空")

    row = ContentSchedule(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        generation_id=req.generation_id,
        title=title,
        content=req.content,
        platform=req.platform,
        scheduled_date=req.scheduled_date,
        status=req.status,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    return {
        "id": row.id,
        "title": row.title,
        "content": row.content,
        "platform": row.platform,
        "scheduled_date": row.scheduled_date,
        "status": row.status,
        "generation_id": row.generation_id,
        "created_at": row.created_at,
    }


@router.put("/schedules/{schedule_id}")
def update_schedule(
    schedule_id: int,
    req: ScheduleUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    row = db.query(ContentSchedule).filter(
        ContentSchedule.id == schedule_id,
        ContentSchedule.user_id == current_user.id,
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="排期不存在")

    if req.status is not None and req.status not in _VALID_STATUS:
        raise HTTPException(status_code=400, detail=f"无效状态，可选: {_VALID_STATUS}")

    if req.title is not None:
        title = req.title.strip()
        if not title:
            raise HTTPException(status_code=400, detail="标题不能为空")
        row.title = title
    if req.content is not None:
        row.content = req.content
    if req.platform is not None:
        row.platform = req.platform
    if req.scheduled_date is not None:
        row.scheduled_date = req.scheduled_date
    if req.status is not None:
        row.status = req.status
    if req.generation_id is not None:
        row.generation_id = req.generation_id

    db.commit()
    db.refresh(row)

    return {
        "id": row.id,
        "title": row.title,
        "content": row.content,
        "platform": row.platform,
        "scheduled_date": row.scheduled_date,
        "status": row.status,
        "generation_id": row.generation_id,
        "created_at": row.created_at,
    }


@router.delete("/schedules/{schedule_id}")
def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    row = db.query(ContentSchedule).filter(
        ContentSchedule.id == schedule_id,
        ContentSchedule.user_id == current_user.id,
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="排期不存在")

    db.delete(row)
    db.commit()
    return {"ok": True}
