"""
FastAPI 通用依赖：JWT 认证守卫 + 订阅有效期检查
"""
from datetime import datetime
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from services.auth import decode_jwt_token


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
