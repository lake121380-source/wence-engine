from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import StyleTemplate, User
from routers.deps import require_active_subscription
from services.knowledge import knowledge_service

router = APIRouter()


@router.get("/style-templates")
def list_style_templates(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    templates = (
        db.query(StyleTemplate)
        .filter(StyleTemplate.tenant_id == current_user.tenant_id)
        .order_by(StyleTemplate.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": t.id,
            "name": t.name,
            "platform": t.platform,
            "creator_id": t.creator_id,
            "creator_name": t.creator.nickname if t.creator else None,
            "tone_description": t.tone_description,
            "hook_patterns": t.hook_patterns,
            "cta_patterns": t.cta_patterns,
            "avg_duration": t.avg_duration,
            "content_type": t.content_type,
        }
        for t in templates
    ]


class CreateStyleRequest(BaseModel):
    name: str
    platform: str = "douyin"
    tone_description: str = ""
    structure_pattern: str = ""
    hook_patterns: list[str] = []
    cta_patterns: list[str] = []
    example_scripts: list[str] = []
    content_type: Optional[str] = None


@router.post("/style-templates")
async def create_style_template(
    req: CreateStyleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    tmpl = StyleTemplate(**req.model_dump(), tenant_id=current_user.tenant_id)
    db.add(tmpl)
    db.commit()
    db.refresh(tmpl)
    await knowledge_service.index_style_template(db, tmpl.id)
    return {"id": tmpl.id, "name": tmpl.name}


@router.delete("/style-templates/{template_id}")
def delete_style_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    tmpl = db.query(StyleTemplate).filter(
        StyleTemplate.id == template_id,
        StyleTemplate.tenant_id == current_user.tenant_id,
    ).first()
    if not tmpl:
        raise HTTPException(status_code=404, detail="模板不存在")
    db.delete(tmpl)
    db.commit()
    return {"ok": True}
