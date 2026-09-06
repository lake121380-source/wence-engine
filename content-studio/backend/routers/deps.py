"""
FastAPI 通用依赖：JWT 认证守卫 + 订阅有效期检查
"""
from datetime import datetime
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional
import hmac

from database import get_db
from services.auth import decode_jwt_token
from config import settings


def _ensure_session_token_fresh(user, token_session_version: int):
    current_session_version = int(user.session_version or 1)
    if token_session_version != current_session_version:
        raise HTTPException(status_code=401, detail="账号已在其他设备登录，请重新登录")


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """从 Authorization: Bearer <token> 提取当前用户，验证失败抛 401"""
    from models import User

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")

    token = authorization.removeprefix("Bearer ").strip()
    token_data = decode_jwt_token(token)
    if not token_data:
        raise HTTPException(status_code=401, detail="Token 无效或已过期")
    user_id = token_data["user_id"]
    token_session_version = token_data["session_version"]

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="用户不存在")

    _ensure_session_token_fresh(user, token_session_version)

    return user


def get_current_user_optional(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """可选认证：有 token 则返回用户，没有则返回 None（公开接口用）"""
    if not authorization:
        return None
    try:
        return get_current_user(authorization, db)
    except HTTPException:
        return None


def require_active_subscription(
    current_user=Depends(get_current_user),
):
    """
    订阅有效期门禁：过期返回 402，前端收到后跳转 /pricing。
    适用于内容生成等核心付费功能。
    """
    if not current_user.is_subscription_active:
        raise HTTPException(
            status_code=402,
            detail="订阅已到期，请续费后继续使用",
        )
    return current_user


def _extract_open_api_key(authorization: Optional[str], x_api_key: Optional[str]) -> str:
    if x_api_key:
        return x_api_key.strip()
    if authorization and authorization.startswith("Bearer "):
        return authorization.removeprefix("Bearer ").strip()
    return ""


def get_open_api_user(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
):
    """开放 API 认证：使用 X-API-Key（或 Authorization: Bearer <key>）绑定到固定用户。"""
    from models import User

    if not settings.open_api_enabled:
        raise HTTPException(status_code=403, detail="Open API 未启用")

    expected = (settings.open_api_key or "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="Open API 密钥未配置")

    provided = _extract_open_api_key(authorization, x_api_key)
    if not provided or not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="Open API 密钥无效")

    if settings.open_api_user_id <= 0:
        raise HTTPException(status_code=503, detail="Open API 绑定用户未配置")

    user = db.query(User).filter(User.id == settings.open_api_user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=503, detail="Open API 绑定用户不可用")

    if settings.open_api_require_subscription and not user.is_subscription_active:
        raise HTTPException(status_code=402, detail="Open API 绑定用户订阅已到期")

    return user
