"""GitHub UI analytics backed only by persisted generation records."""
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models import Generation, Tenant
from routers.admin import get_current_admin

router = APIRouter()
PLATFORMS = {"douyin": "抖音", "xiaohongshu": "小红书", "weixin": "视频号", "channels": "视频号"}


@router.get("/admin/generations/analytics")
def generation_analytics(
    time_range: Literal["24h", "7d", "30d"] = "7d",
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    now = datetime.utcnow()
    since = now - timedelta(days={"24h": 1, "7d": 7, "30d": 30}[time_range])
    rows = db.query(
        Generation.tenant_id, Tenant.name.label("tenant_name"), Generation.platform,
        Generation.rating, Generation.created_at,
        func.length(func.coalesce(Generation.output_full, "")).label("words"),
    ).outerjoin(Tenant, Tenant.id == Generation.tenant_id).filter(
        Generation.created_at >= since, Generation.created_at <= now,
    ).all()
    total = len(rows)
    rated = [r.rating for r in rows if r.rating is not None]
    platforms = defaultdict(list)
    tenants = defaultdict(list)
    for row in rows:
        platforms[row.platform or "unknown"].append(row)
        tenants[(row.tenant_id, row.tenant_name or "未分配租户")].append(row)

    def avg_rating(items):
        values = [r.rating for r in items if r.rating is not None]
        return round(sum(values) / len(values), 2) if values else None

    days = []
    counts = Counter(r.created_at.date() for r in rows)
    for offset in range((now.date() - since.date()).days + 1):
        day = since.date() + timedelta(days=offset)
        days.append({"date": day.isoformat(), "count": counts[day]})

    return {
        "source": "database", "time_range": time_range,
        "since": since.isoformat() + "Z", "until": now.isoformat() + "Z",
        "summary": {
            "total_generations": total,
            "today_generations": counts[now.date()],
            "avg_word_count": round(sum(r.words for r in rows) / total) if total else 0,
            "avg_rating": round(sum(rated) / len(rated), 2) if rated else None,
            "rated_count": len(rated), "active_tenants": len(tenants),
        },
        "engine_health": {
            "model_name": settings.deepseek_model if settings.use_deepseek else "Claude",
            "engine_status_text": "真实后端已连接", "sdk_driver": "FastAPI / Python",
        },
        "platforms": [{
            "platform": key, "name": PLATFORMS.get(key, key), "count": len(items),
            "percentage": round(len(items) * 100 / total, 1),
            "avg_words": round(sum(r.words for r in items) / len(items)),
            "avg_rating": avg_rating(items),
        } for key, items in sorted(platforms.items(), key=lambda pair: -len(pair[1]))],
        "trend_days": days,
        "tenant_ranking": [{
            "tenant_id": key[0], "tenant_name": key[1], "count": len(items),
            "avg_rating": avg_rating(items),
        } for key, items in sorted(tenants.items(), key=lambda pair: -len(pair[1]))[:10]],
        "unavailable_metrics": ["latency", "tokens", "cache_hit_rate", "adoption", "success_rate"],
    }
