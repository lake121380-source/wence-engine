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


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _table_exists(conn, table_name: str) -> bool:
    """检查 SQLite 表是否存在，避免 _ensure_* 迁移在表未创建时崩溃。"""
    rows = conn.exec_driver_sql(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    ).fetchall()
    return len(rows) > 0


def _ensure_users_session_version_column():
    if not settings.database_url.startswith("sqlite"):
        return
    with engine.begin() as conn:
        if not _table_exists(conn, "users"):
            return
        columns = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(users)").fetchall()]
        if "session_version" not in columns:
            conn.exec_driver_sql("ALTER TABLE users ADD COLUMN session_version INTEGER NOT NULL DEFAULT 1")
        conn.exec_driver_sql("UPDATE users SET session_version = 1 WHERE session_version IS NULL OR session_version < 1")


def _ensure_users_email_verified_column():
    if not settings.database_url.startswith("sqlite"):
        return
    with engine.begin() as conn:
        if not _table_exists(conn, "users"):
            return
        columns = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(users)").fetchall()]
        if "email_verified" not in columns:
            conn.exec_driver_sql("ALTER TABLE users ADD COLUMN email_verified BOOLEAN NOT NULL DEFAULT 1")
        conn.exec_driver_sql("UPDATE users SET email_verified = 1 WHERE email_verified IS NULL")


def _ensure_topics_viral_reason_column():
    if not settings.database_url.startswith("sqlite"):
        return
    with engine.begin() as conn:
        if not _table_exists(conn, "topics"):
            return
        columns = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(topics)").fetchall()]
        if "viral_reason" not in columns:
            conn.exec_driver_sql("ALTER TABLE topics ADD COLUMN viral_reason TEXT")


def _ensure_documents_ai_summary_column():
    if not settings.database_url.startswith("sqlite"):
        return
    with engine.begin() as conn:
        if not _table_exists(conn, "documents"):
            return
        columns = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(documents)").fetchall()]
        if "ai_summary" not in columns:
            conn.exec_driver_sql("ALTER TABLE documents ADD COLUMN ai_summary TEXT")


def _ensure_generations_debug_columns():
    if not settings.database_url.startswith("sqlite"):
        return
    with engine.begin() as conn:
        if not _table_exists(conn, "generations"):
            return
        columns = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(generations)").fetchall()]
        alter_cols = [
            ("debug_info", "TEXT"),
            ("mode_branch", "VARCHAR(32)"),
            ("temperature_used", "FLOAT"),
            ("doc_chars_injected", "INTEGER DEFAULT 0"),
            ("viral_chars_injected", "INTEGER DEFAULT 0"),
        ]
        for col_name, col_type in alter_cols:
            if col_name not in columns:
                conn.exec_driver_sql(f"ALTER TABLE generations ADD COLUMN {col_name} {col_type}")


def _ensure_analysis_tasks_columns():
    if not settings.database_url.startswith("sqlite"):
        return
    with engine.begin() as conn:
        if not _table_exists(conn, "analysis_tasks"):
            return
        columns = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(analysis_tasks)").fetchall()]
        alter_cols = [
            ("log", "TEXT"),
            ("result", "TEXT"),
        ]
        for col_name, col_type in alter_cols:
            if col_name not in columns:
                conn.exec_driver_sql(f"ALTER TABLE analysis_tasks ADD COLUMN {col_name} {col_type}")


def init_db():
    from models import Creator, CreatorVideo, Document, StyleTemplate, Generation  # noqa
    from models import CreatorIntelCard, OperatorViewpoint, VideoAnalysis, AnalysisTask  # noqa
    from models import Topic  # noqa
    from models import Tenant, User, Subscription, PaymentOrder, WechatScene, EmailVerificationToken  # noqa
    from models import DocumentFolder  # noqa
    Base.metadata.create_all(bind=engine)
    _ensure_users_session_version_column()
    _ensure_users_email_verified_column()
    _ensure_topics_viral_reason_column()
    _ensure_documents_ai_summary_column()
    _ensure_generations_debug_columns()
    _ensure_analysis_tasks_columns()
