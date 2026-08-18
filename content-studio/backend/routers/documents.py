import os
import uuid
from typing import Optional

import aiofiles
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import CreatorVideo, Document, DocumentFolder, Topic, User, VideoAnalysis
from routers.deps import require_active_subscription
from services.knowledge import knowledge_service

router = APIRouter()

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/documents")
def list_documents(
    folder: Optional[str] = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    q = db.query(Document).filter(Document.tenant_id == current_user.tenant_id)
    if folder is not None:
        if folder == "__none__":
            q = q.filter((Document.folder_name == None) | (Document.folder_name == ""))
        else:
            q = q.filter(Document.folder_name == folder)
    docs = q.order_by(Document.created_at.desc()).offset(offset).limit(limit).all()
    return [
        {
            "id": d.id,
            "name": d.name,
            "file_type": d.file_type,
            "chunk_count": d.chunk_count,
            "indexed": d.indexed,
            "tags": d.tags,
            "folder_name": d.folder_name,
            "source_type": d.source_type,
            "source_ref": d.source_ref,
            "content_preview": (d.content or "")[:300] if d.content else None,
            "created_at": d.created_at,
        }
        for d in docs
    ]


@router.get("/documents/folders")
def list_document_folders(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    from sqlalchemy import distinct

    doc_rows = (
        db.query(distinct(Document.folder_name))
        .filter(
            Document.tenant_id == current_user.tenant_id,
            Document.folder_name != None,
            Document.folder_name != "",
        )
        .all()
    )
    doc_folders = {row[0] for row in doc_rows if row[0]}

    explicit_rows = (
        db.query(DocumentFolder.name)
        .filter(DocumentFolder.tenant_id == current_user.tenant_id)
        .all()
    )
    explicit_folders = {row[0] for row in explicit_rows if row[0]}

    return sorted(doc_folders | explicit_folders)


class CreateFolderRequest(BaseModel):
    name: str


@router.post("/documents/folders")
def create_document_folder(
    body: CreateFolderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="文件夹名不能为空")

    existing = (
        db.query(DocumentFolder)
        .filter(
            DocumentFolder.tenant_id == current_user.tenant_id,
            DocumentFolder.name == name,
        )
        .first()
    )
    if not existing:
        folder = DocumentFolder(tenant_id=current_user.tenant_id, name=name)
        db.add(folder)
        db.commit()
    return {"name": name}


@router.delete("/documents/folders/{folder_name}")
def delete_document_folder(
    folder_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    db.query(DocumentFolder).filter(
        DocumentFolder.tenant_id == current_user.tenant_id,
        DocumentFolder.name == folder_name,
    ).delete()
    db.commit()
    return {"ok": True}


@router.get("/documents/{doc_id}")
def get_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    doc = (
        db.query(Document)
        .filter(Document.id == doc_id, Document.tenant_id == current_user.tenant_id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    return {
        "id": doc.id,
        "name": doc.name,
        "file_type": doc.file_type,
        "chunk_count": doc.chunk_count,
        "indexed": doc.indexed,
        "tags": doc.tags,
        "folder_name": doc.folder_name,
        "source_type": doc.source_type,
        "source_ref": doc.source_ref,
        "content": doc.content or "",
        "created_at": doc.created_at,
    }


@router.get("/documents/{doc_id}/analysis")
def get_document_analysis(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    doc = (
        db.query(Document)
        .filter(Document.id == doc_id, Document.tenant_id == current_user.tenant_id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    if doc.source_type not in ("creator_video", "topic"):
        raise HTTPException(status_code=404, detail="该文档没有关联的爆款分析")

    if not doc.source_ref:
        raise HTTPException(status_code=404, detail="文档缺少来源引用")

    video_row = None
    analysis_row = None

    if doc.source_type == "creator_video":
        video_row = db.query(CreatorVideo).filter(CreatorVideo.video_id == doc.source_ref).first()
        if video_row:
            analysis_row = (
                db.query(VideoAnalysis)
                .filter(
                    VideoAnalysis.video_id == video_row.id,
                    VideoAnalysis.tenant_id == current_user.tenant_id,
                )
                .first()
            )
    elif doc.source_type == "topic":
        topic_row = (
            db.query(Topic)
            .filter(
                Topic.video_id == doc.source_ref,
                Topic.tenant_id == current_user.tenant_id,
            )
            .first()
        )
        if topic_row:
            video_row = topic_row
            analysis_row = (
                db.query(VideoAnalysis)
                .filter(
                    VideoAnalysis.topic_id == topic_row.id,
                    VideoAnalysis.tenant_id == current_user.tenant_id,
                )
                .first()
            )

    video_info = None
    if video_row:
        video_info = {
            "title": getattr(video_row, "title", None),
            "script": getattr(video_row, "script", None),
            "description": getattr(video_row, "description", None),
            "video_url": getattr(video_row, "video_url", None),
            "like_count": getattr(video_row, "like_count", None),
            "comment_count": getattr(video_row, "comment_count", None),
            "collect_count": getattr(video_row, "collect_count", None),
            "play_count": getattr(video_row, "play_count", None),
            "like_play_ratio": getattr(video_row, "like_play_ratio", None),
            "comment_play_ratio": getattr(video_row, "comment_play_ratio", None),
            "collect_play_ratio": getattr(video_row, "collect_play_ratio", None),
        }

    if not analysis_row:
        return {"video": video_info, "analysis": None}

    return {
        "video": video_info,
        "analysis": {
            "like_play_ratio": analysis_row.like_play_ratio,
            "comment_play_ratio": analysis_row.comment_play_ratio,
            "collect_play_ratio": analysis_row.collect_play_ratio,
            "like_play_level": getattr(analysis_row, "like_play_level", None),
            "comment_play_level": getattr(analysis_row, "comment_play_level", None),
            "collect_play_level": getattr(analysis_row, "collect_play_level", None),
            "resonance_analysis": analysis_row.resonance_analysis,
            "discussion_analysis": analysis_row.discussion_analysis,
            "value_analysis": analysis_row.value_analysis,
            "why_viral_summary": analysis_row.why_viral_summary,
        },
    }


@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    tags: str = Form(""),
    folder_name: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    ext = file.filename.split(".")[-1].lower()
    if ext not in ("pdf", "docx", "doc", "txt"):
        raise HTTPException(status_code=400, detail="仅支持 PDF / Word / TXT 格式")

    safe_filename = f"{uuid.uuid4().hex}.{ext}"
    save_path = os.path.join(UPLOAD_DIR, safe_filename)
    async with aiofiles.open(save_path, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)

    doc = Document(
        name=file.filename,
        file_type=ext,
        file_path=save_path,
        tags=[tag.strip() for tag in tags.split(",") if tag.strip()],
        folder_name=folder_name.strip() if folder_name else None,
        source_type="upload",
        tenant_id=current_user.tenant_id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    chunks = await knowledge_service.process_document(db, doc.id)
    return {"id": doc.id, "name": doc.name, "chunks": chunks}


@router.delete("/documents/{doc_id}")
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.tenant_id == current_user.tenant_id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.file_path and os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    db.delete(doc)
    db.commit()
    return {"message": "deleted"}


@router.patch("/documents/{doc_id}/folder")
def move_document_folder(
    doc_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.tenant_id == current_user.tenant_id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.folder_name = body.get("folder_name") or None
    db.commit()
    return {"ok": True}


class AddTextDocRequest(BaseModel):
    name: str
    content: str
    folder_name: Optional[str] = None
    tags: list[str] = []
    source_type: Optional[str] = None
    source_ref: Optional[str] = None


@router.post("/documents/add-text")
async def add_text_document(
    req: AddTextDocRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_subscription),
):
    if req.source_ref:
        existing = db.query(Document).filter(
            Document.tenant_id == current_user.tenant_id,
            Document.source_type == req.source_type,
            Document.source_ref == req.source_ref,
        ).first()
        if existing:
            return {
                "id": existing.id,
                "name": existing.name,
                "chunks": existing.chunk_count or 0,
                "duplicate": True,
            }

    doc = Document(
        name=req.name,
        file_type="text",
        content=req.content,
        tags=req.tags,
        folder_name=req.folder_name or None,
        source_type=req.source_type,
        source_ref=req.source_ref,
        tenant_id=current_user.tenant_id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    chunks = await knowledge_service.process_text(db, doc.id, req.content)
    return {"id": doc.id, "name": doc.name, "chunks": chunks}
