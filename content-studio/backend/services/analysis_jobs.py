import asyncio
import threading
import uuid
from datetime import datetime, timedelta

from database import SessionLocal
from models import AnalysisTask, VideoAnalysis
from services.analyzer import analyzer_service


JOB_CONCURRENCY = 2
STALE_TASK_TIMEOUT = timedelta(minutes=30)


def _expire_stale_tasks(db, *, creator_id: int | None = None, tenant_id: int | None = None) -> None:
    cutoff = datetime.utcnow() - STALE_TASK_TIMEOUT
    query = db.query(AnalysisTask).filter(
        AnalysisTask.status.in_(("queued", "pending", "running")),
        AnalysisTask.updated_at < cutoff,
    )
    if creator_id is not None:
        query = query.filter(AnalysisTask.creator_id == creator_id)
    if tenant_id is not None:
        query = query.filter(AnalysisTask.tenant_id == tenant_id)

    stale_tasks = query.all()
    if not stale_tasks:
        return

    for task in stale_tasks:
        task.status = "error"
        task.error = "任务超时或服务重启中断，请重新发起"
        task.updated_at = datetime.utcnow()
    db.commit()


def _task_to_dict(task: AnalysisTask) -> dict:
    log = task.log or []
    return {
        "task_id": task.task_id,
        "status": task.status,
        "progress": task.done,
        "done": task.done,
        "total": task.total,
        "success": task.success,
        "failed": task.failed,
        "error": task.error,
        "log": log[-100:],
        "result": task.result,
        "creator_id": task.creator_id,
        "task_type": task.task_type,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
    }


def get_task(task_id: str, tenant_id: int) -> dict | None:
    db = SessionLocal()
    try:
        _expire_stale_tasks(db, tenant_id=tenant_id)
        task = (
            db.query(AnalysisTask)
            .filter(
                AnalysisTask.task_id == task_id,
                AnalysisTask.tenant_id == tenant_id,
            )
            .first()
        )
        return _task_to_dict(task) if task else None
    finally:
        db.close()


def get_running_task_for_creator(creator_id: int, tenant_id: int) -> dict | None:
    db = SessionLocal()
    try:
        _expire_stale_tasks(db, creator_id=creator_id, tenant_id=tenant_id)
        task = (
            db.query(AnalysisTask)
            .filter(
                AnalysisTask.creator_id == creator_id,
                AnalysisTask.tenant_id == tenant_id,
                AnalysisTask.task_type == "creator_video_batch",
                AnalysisTask.status.in_(("queued", "running")),
            )
            .order_by(AnalysisTask.created_at.desc())
            .first()
        )
        return _task_to_dict(task) if task else None
    finally:
        db.close()


def get_running_discover_task(tenant_id: int) -> dict | None:
    db = SessionLocal()
    try:
        _expire_stale_tasks(db, tenant_id=tenant_id)
        task = (
            db.query(AnalysisTask)
            .filter(
                AnalysisTask.tenant_id == tenant_id,
                AnalysisTask.task_type == "auto_discover_and_crawl",
                AnalysisTask.status.in_(("pending", "running")),
            )
            .order_by(AnalysisTask.created_at.desc())
            .first()
        )
        return _task_to_dict(task) if task else None
    finally:
        db.close()


def create_creator_batch_task(*, creator_id: int, tenant_id: int, total: int) -> dict:
    db = SessionLocal()
    try:
        task = AnalysisTask(
            task_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            creator_id=creator_id,
            task_type="creator_video_batch",
            status="queued",
            total=total,
            done=0,
            success=0,
            failed=0,
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return _task_to_dict(task)
    finally:
        db.close()


def create_discover_task(*, tenant_id: int, keyword: str, limit: int, platforms: list[str]) -> dict:
    db = SessionLocal()
    try:
        task = AnalysisTask(
            task_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            creator_id=None,
            task_type="auto_discover_and_crawl",
            status="pending",
            total=0,
            done=0,
            success=0,
            failed=0,
            log=[f"任务已创建：{keyword}，平台 {', '.join(platforms)}，上限 {limit}"],
            result=None,
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return _task_to_dict(task)
    finally:
        db.close()


def start_creator_batch_task(*, task_id: str, video_ids: list[int], tenant_id: int) -> None:
    thread = threading.Thread(
        target=_run_creator_batch_task_thread,
        args=(task_id, video_ids, tenant_id),
        daemon=True,
        name=f"analysis-task-{task_id[:8]}",
    )
    thread.start()


def start_discover_task(
    *,
    task_id: str,
    tenant_id: int,
    keyword: str,
    limit: int,
    platforms: list[str],
) -> None:
    thread = threading.Thread(
        target=_run_discover_task_thread,
        args=(task_id, tenant_id, keyword, limit, platforms),
        daemon=True,
        name=f"discover-task-{task_id[:8]}",
    )
    thread.start()


def _run_creator_batch_task_thread(task_id: str, video_ids: list[int], tenant_id: int) -> None:
    asyncio.run(_run_creator_batch_task(task_id=task_id, video_ids=video_ids, tenant_id=tenant_id))


def _run_discover_task_thread(
    task_id: str,
    tenant_id: int,
    keyword: str,
    limit: int,
    platforms: list[str],
) -> None:
    asyncio.run(
        _run_discover_task(
            task_id=task_id,
            tenant_id=tenant_id,
            keyword=keyword,
            limit=limit,
            platforms=platforms,
        )
    )


def _set_task_status(task_id: str, *, status: str, error: str | None = None) -> None:
    db = SessionLocal()
    try:
        task = db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()
        if not task:
            return
        task.status = status
        task.error = error
        task.updated_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()


def _append_task_log(task_id: str, message: str) -> None:
    db = SessionLocal()
    try:
        task = db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()
        if not task:
            return
        log = list(task.log or [])
        log.append(message)
        task.log = log[-100:]
        task.updated_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()


def _update_discover_progress(
    task_id: str,
    *,
    progress: int,
    total: int,
    message: str | None = None,
) -> None:
    db = SessionLocal()
    try:
        task = db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()
        if not task:
            return
        task.done = progress
        task.total = total
        if message:
            log = list(task.log or [])
            log.append(message)
            task.log = log[-100:]
        task.updated_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()


def _finish_discover_task(task_id: str, *, result: dict) -> None:
    db = SessionLocal()
    try:
        task = db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()
        if not task:
            return
        task.status = "done"
        task.result = result
        task.done = task.total
        task.success = int(result.get("added") or 0)
        task.failed = int(result.get("failed") or 0)
        log = list(task.log or [])
        log.append("完成")
        task.log = log[-100:]
        task.updated_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()


def _increment_task_progress(task_id: str, *, success: bool = False, failed: bool = False) -> None:
    db = SessionLocal()
    try:
        task = db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()
        if not task:
            return
        task.done += 1
        if success:
            task.success += 1
        if failed:
            task.failed += 1
        task.updated_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()


async def _run_creator_batch_task(*, task_id: str, video_ids: list[int], tenant_id: int) -> None:
    _set_task_status(task_id, status="running", error=None)

    prefetch_db = SessionLocal()
    try:
        cached_rows = (
            prefetch_db.query(VideoAnalysis.video_id)
            .filter(
                VideoAnalysis.video_id.in_(video_ids),
                VideoAnalysis.tenant_id == tenant_id,
                VideoAnalysis.why_viral_summary.isnot(None),
                VideoAnalysis.why_viral_summary != "",
            )
            .all()
        )
        cached_ids = {row.video_id for row in cached_rows}
    finally:
        prefetch_db.close()

    async def analyze_one(video_id: int) -> None:
        if video_id in cached_ids:
            _increment_task_progress(task_id, success=True)
            return

        item_db = SessionLocal()
        try:
            await analyzer_service.analyze_video_viral(
                item_db,
                video_id=video_id,
                tenant_id=tenant_id,
                enrich_missing_fields=False,
            )
            _increment_task_progress(task_id, success=True)
        except Exception:
            _increment_task_progress(task_id, failed=True)
        finally:
            item_db.close()

    try:
        for idx in range(0, len(video_ids), JOB_CONCURRENCY):
            chunk = video_ids[idx: idx + JOB_CONCURRENCY]
            await asyncio.gather(*(analyze_one(video_id) for video_id in chunk))
        _set_task_status(task_id, status="done")
    except Exception as exc:
        _set_task_status(task_id, status="error", error=str(exc))


async def _run_discover_task(
    *,
    task_id: str,
    tenant_id: int,
    keyword: str,
    limit: int,
    platforms: list[str],
) -> None:
    _set_task_status(task_id, status="running", error=None)

    db = SessionLocal()
    try:
        from services.crawler import crawler_service

        async def on_progress(step, total, msg, state="processing"):
            _update_discover_progress(
                task_id,
                progress=step,
                total=total,
                message=msg,
            )

        result = await crawler_service.auto_discover_and_crawl(
            db=db,
            keyword=keyword,
            limit=limit,
            platforms=platforms,
            progress_callback=on_progress,
            tenant_id=tenant_id,
        )
        _finish_discover_task(task_id, result=result)
    except Exception as exc:
        _append_task_log(task_id, f"错误: {exc}")
        _set_task_status(task_id, status="error", error=str(exc))
    finally:
        db.close()
