from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import (
    Creator,
    CreatorVideo,
    Document,
    Generation,
    OperatorViewpoint,
    StyleTemplate,
    TenantCreator,
    Topic,
    User,
    VideoAnalysis,
)
from routers.deps import require_active_subscription
from services.generator import generator_service
from services.knowledge import knowledge_service

router = APIRouter()


class GenerateRequest(BaseModel):
    topic: str
    platform: str = "douyin"
    style_template_id: Optional[int] = None
    product_doc_ids: list[int] = []
    creator_ids: list[int] = []
    viewpoint_ids: list[int] = []
    viral_analysis_ids: list[int] = []
    history: list[dict] = []


@router.post("/generate")
async def generate_content(
    req: GenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    tid = current_user.tenant_id

    if req.product_doc_ids:
        valid = db.query(Document.id).filter(
            Document.id.in_(req.product_doc_ids),
            Document.tenant_id == tid,
        ).all()
        valid_ids = {r.id for r in valid}
        invalid = [i for i in req.product_doc_ids if i not in valid_ids]
        if invalid:
            raise HTTPException(status_code=403, detail=f"无权访问文档: {invalid}")

    if req.creator_ids:
        valid = db.query(TenantCreator.creator_id).filter(
            TenantCreator.creator_id.in_(req.creator_ids),
            TenantCreator.tenant_id == tid,
        ).all()
        valid_ids = {r.creator_id for r in valid}
        invalid = [i for i in req.creator_ids if i not in valid_ids]
        if invalid:
            raise HTTPException(status_code=403, detail=f"无权访问博主: {invalid}")

    if req.viewpoint_ids:
        valid = db.query(OperatorViewpoint.id).filter(
            OperatorViewpoint.id.in_(req.viewpoint_ids),
            OperatorViewpoint.user_id == current_user.id,
        ).all()
        valid_ids = {r.id for r in valid}
        invalid = [i for i in req.viewpoint_ids if i not in valid_ids]
        if invalid:
            raise HTTPException(status_code=403, detail=f"无权访问观点: {invalid}")

    if req.style_template_id:
        tmpl = db.query(StyleTemplate).filter(
            StyleTemplate.id == req.style_template_id,
            StyleTemplate.tenant_id == tid,
        ).first()
        if not tmpl:
            raise HTTPException(status_code=403, detail="无权访问该风格模板")

    if req.viral_analysis_ids:
        valid = db.query(VideoAnalysis.id).filter(
            VideoAnalysis.id.in_(req.viral_analysis_ids),
            VideoAnalysis.tenant_id == tid,
        ).all()
        valid_ids = {r.id for r in valid}
        invalid = [i for i in req.viral_analysis_ids if i not in valid_ids]
        if invalid:
            raise HTTPException(status_code=403, detail=f"无权访问爆款分析: {invalid}")

    try:
        result = await generator_service.generate(
            db=db,
            topic=req.topic,
            platform=req.platform,
            style_template_id=req.style_template_id,
            product_doc_ids=req.product_doc_ids,
            creator_ids=req.creator_ids,
            viewpoint_ids=req.viewpoint_ids if req.viewpoint_ids else None,
            viral_analysis_ids=req.viral_analysis_ids if req.viral_analysis_ids else None,
            tenant_id=current_user.tenant_id,
            history=req.history,
        )
        if isinstance(result, dict) and result.get("id"):
            gen = db.query(Generation).filter(Generation.id == result["id"]).first()
            if gen:
                gen.tenant_id = current_user.tenant_id
                gen.user_id = current_user.id
                db.commit()
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


def _validate_generate_request(req: GenerateRequest, db: Session, current_user: User):
    """校验生成请求中引用的资源权限"""
    tid = current_user.tenant_id
    if req.product_doc_ids:
        valid = db.query(Document.id).filter(
            Document.id.in_(req.product_doc_ids), Document.tenant_id == tid,
        ).all()
        invalid = [i for i in req.product_doc_ids if i not in {r.id for r in valid}]
        if invalid:
            raise HTTPException(status_code=403, detail=f"无权访问文档: {invalid}")
    if req.creator_ids:
        valid = db.query(TenantCreator.creator_id).filter(
            TenantCreator.creator_id.in_(req.creator_ids), TenantCreator.tenant_id == tid,
        ).all()
        invalid = [i for i in req.creator_ids if i not in {r.creator_id for r in valid}]
        if invalid:
            raise HTTPException(status_code=403, detail=f"无权访问博主: {invalid}")
    if req.viewpoint_ids:
        valid = db.query(OperatorViewpoint.id).filter(
            OperatorViewpoint.id.in_(req.viewpoint_ids), OperatorViewpoint.user_id == current_user.id,
        ).all()
        invalid = [i for i in req.viewpoint_ids if i not in {r.id for r in valid}]
        if invalid:
            raise HTTPException(status_code=403, detail=f"无权访问观点: {invalid}")
    if req.style_template_id:
        tmpl = db.query(StyleTemplate).filter(
            StyleTemplate.id == req.style_template_id, StyleTemplate.tenant_id == tid,
        ).first()
        if not tmpl:
            raise HTTPException(status_code=403, detail="无权访问该风格模板")
    if req.viral_analysis_ids:
        valid = db.query(VideoAnalysis.id).filter(
            VideoAnalysis.id.in_(req.viral_analysis_ids), VideoAnalysis.tenant_id == tid,
        ).all()
        invalid = [i for i in req.viral_analysis_ids if i not in {r.id for r in valid}]
        if invalid:
            raise HTTPException(status_code=403, detail=f"无权访问爆款分析: {invalid}")


@router.post("/generate/stream")
async def generate_content_stream(
    req: GenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    _validate_generate_request(req, db, current_user)

    async def event_stream():
        try:
            gen_id = None
            async for chunk in generator_service.generate_stream(
                db=db,
                topic=req.topic,
                platform=req.platform,
                style_template_id=req.style_template_id,
                product_doc_ids=req.product_doc_ids,
                creator_ids=req.creator_ids,
                viewpoint_ids=req.viewpoint_ids if req.viewpoint_ids else None,
                viral_analysis_ids=req.viral_analysis_ids if req.viral_analysis_ids else None,
                tenant_id=current_user.tenant_id,
                history=req.history,
            ):
                # 捕获 done 事件中的 gen_id 用于更新 tenant/user
                if chunk.startswith("event: done"):
                    import json as _json
                    try:
                        data_line = chunk.split("data: ", 1)[1].strip()
                        result = _json.loads(data_line)
                        gen_id = result.get("id")
                    except Exception:
                        pass
                yield chunk

            # 更新 tenant_id / user_id
            if gen_id:
                gen = db.query(Generation).filter(Generation.id == gen_id).first()
                if gen:
                    gen.tenant_id = current_user.tenant_id
                    gen.user_id = current_user.id
                    db.commit()
        except Exception as exc:
            import json as _json
            yield f"event: error\ndata: {_json.dumps(str(exc), ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/generations")
def list_generations(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    gens = (
        db.query(Generation)
        .filter(Generation.user_id == current_user.id)
        .order_by(Generation.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": g.id,
            "topic": g.topic,
            "platform": g.platform,
            "output_body": g.output_body,
            "output_full": g.output_full or g.output_body,
            "created_at": g.created_at,
        }
        for g in gens
    ]


@router.patch("/generations/{gen_id}/rate")
def rate_generation(
    gen_id: int,
    rating: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    gen = db.query(Generation).filter(
        Generation.id == gen_id,
        Generation.user_id == current_user.id,
    ).first()
    if not gen:
        raise HTTPException(status_code=404, detail="Not found")
    gen.rating = max(1, min(5, rating))
    db.commit()
    return {"ok": True}


@router.get("/knowledge/stats")
def knowledge_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    tid = current_user.tenant_id
    vector_stats = knowledge_service.get_stats()
    return {
        "creators": db.query(TenantCreator).filter(TenantCreator.tenant_id == tid).count(),
        "videos": db.query(CreatorVideo)
        .join(Creator)
        .join(TenantCreator, TenantCreator.creator_id == Creator.id)
        .filter(TenantCreator.tenant_id == tid)
        .count(),
        "documents": db.query(Document).filter(Document.tenant_id == tid).count(),
        "style_templates": db.query(StyleTemplate).filter(StyleTemplate.tenant_id == tid).count(),
        "generations": db.query(Generation).filter(Generation.tenant_id == tid).count(),
        "topics": db.query(Topic).filter(Topic.tenant_id == tid).count(),
        "viewpoints": db.query(OperatorViewpoint).filter(OperatorViewpoint.tenant_id == tid).count(),
        **vector_stats,
    }
