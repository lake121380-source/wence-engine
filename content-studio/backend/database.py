from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings
import json
from datetime import datetime, date


def _json_serializer(obj):
    """自定义 JSON 序列化器，处理 datetime 等非标准类型"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


_extra_kwargs = {}
if "sqlite" in settings.database_url:
    _extra_kwargs["connect_args"] = {"check_same_thread": False}
    _extra_kwargs["json_serializer"] = lambda obj: json.dumps(obj, default=_json_serializer, ensure_ascii=False)
elif "mysql" in settings.database_url:
    _extra_kwargs["pool_recycle"] = 3600
    _extra_kwargs["pool_pre_ping"] = True

engine = create_engine(settings.database_url, **_extra_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def _ensure_users_session_version_column():
    """轻量兼容迁移：确保 users.session_version 存在且可用。"""
    if not settings.database_url.startswith("sqlite"):
        return

    with engine.begin() as conn:
        columns = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(users)").fetchall()]
        if "session_version" not in columns:
            conn.exec_driver_sql(
                "ALTER TABLE users ADD COLUMN session_version INTEGER NOT NULL DEFAULT 1"
            )
        conn.exec_driver_sql(
            "UPDATE users SET session_version = 1 WHERE session_version IS NULL OR session_version < 1"
        )

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from models import Creator, CreatorVideo, Document, StyleTemplate, Generation  # noqa
    from models import CreatorIntelCard, OperatorViewpoint, VideoAnalysis  # noqa
    from models import Topic  # noqa
    from models import Tenant, User, Subscription, PaymentOrder, WechatScene  # noqa
    from models import DocumentFolder  # noqa
    Base.metadata.create_all(bind=engine)
    _ensure_users_session_version_column()
