from __future__ import annotations

import logging

from sqlalchemy import create_engine, inspect as sa_inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings
import json
from datetime import datetime, date


logger = logging.getLogger("content_studio.database")


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
    """检查表是否存在，兼容 SQLite、MySQL 及测试用方言。"""
    return bool(sa_inspect(conn).has_table(table_name))


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


def _ensure_payment_order_columns():
    """补齐支付订单字段和支付幂等索引。

    ``Base.metadata.create_all`` 只会创建新表，不会给线上旧表追加字段；支付
    订单又必须保留历史记录，因此这里采用幂等 ALTER 方式，覆盖 SQLite 与
    MySQL。索引创建前会检查历史重复值，避免在已有脏数据上静默启动成不安全
    的支付状态机。
    """
    with engine.begin() as conn:
        if not _table_exists(conn, "payment_orders"):
            return
        inspector = sa_inspect(conn)
        columns = {column["name"] for column in inspector.get_columns("payment_orders")}
        dialect = conn.dialect.name
        column_defs = {
            "idempotency_key": "VARCHAR(128)",
            "expires_at": "DATETIME",
            "qr_payload": "TEXT",
            "url_scheme": "TEXT",
        }
        for name, definition in column_defs.items():
            if name not in columns:
                conn.exec_driver_sql(
                    f"ALTER TABLE payment_orders ADD COLUMN {name} {definition} NULL"
                )

        # Existing deployments can contain duplicate values from an earlier
        # implementation.  Refuse to create a false sense of safety until an
        # operator resolves them, instead of silently choosing a winner.
        duplicate_checks = (
            (
                "idempotency_key",
                "SELECT user_id, idempotency_key, COUNT(*) FROM payment_orders "
                "WHERE idempotency_key IS NOT NULL GROUP BY user_id, idempotency_key "
                "HAVING COUNT(*) > 1",
            ),
            (
                "transaction_id",
                "SELECT transaction_id, COUNT(*) FROM payment_orders "
                "WHERE transaction_id IS NOT NULL GROUP BY transaction_id "
                "HAVING COUNT(*) > 1",
            ),
        )
        for label, query in duplicate_checks:
            duplicates = conn.exec_driver_sql(query).fetchall()
            if duplicates:
                raise RuntimeError(
                    f"payment_orders 存在重复 {label}，无法安全创建支付唯一索引；"
                    "请先人工核对并清理重复订单"
                )

        existing_indexes = {
            str(index.get("name"))
            for index in inspector.get_indexes("payment_orders")
            if index.get("name")
        }
        existing_constraints = {
            str(constraint.get("name"))
            for constraint in inspector.get_unique_constraints("payment_orders")
            if constraint.get("name")
        }

        def ensure_unique_index(name: str, columns_sql: str, *, where_sql: str | None = None):
            if name in existing_indexes or name in existing_constraints:
                return
            if dialect == "sqlite":
                # Keep NULL reservations exempt while indexing the actual
                # business key.  In particular, the transaction index must
                # not accidentally reuse the idempotency predicate: orders
                # created without an Idempotency-Key still need protection
                # against a provider流水号 being attached to two orders.
                where = f" WHERE {where_sql}" if where_sql else ""
                conn.exec_driver_sql(
                    f"CREATE UNIQUE INDEX IF NOT EXISTS {name} ON payment_orders ({columns_sql}){where}"
                )
            else:
                conn.exec_driver_sql(
                    f"CREATE UNIQUE INDEX {name} ON payment_orders ({columns_sql})"
                )
            existing_indexes.add(name)

        # SQLite needs partial indexes to make the intent explicit; MySQL's
        # normal UNIQUE semantics already allow multiple NULL values.
        ensure_unique_index(
            "uq_payment_order_user_idempotency",
            "user_id, idempotency_key",
            where_sql="idempotency_key IS NOT NULL",
        )
        ensure_unique_index(
            "uq_payment_order_transaction_id",
            "transaction_id",
            where_sql="transaction_id IS NOT NULL",
        )


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
    _ensure_payment_order_columns()
