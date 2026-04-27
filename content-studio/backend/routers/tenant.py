"""
租户管理路由：企业信息 + 成员管理
"""
import secrets
import uuid
import bcrypt
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from config import settings
from database import get_db
from models import User, Tenant, Subscription
from routers.deps import get_current_user

router = APIRouter(prefix="/tenant", tags=["tenant"])


# ── Pydantic ──────────────────────────────────────────────────────────────────

class TenantUpdateRequest(BaseModel):
    name: Optional[str] = None


class RoleUpdateRequest(BaseModel):
    role: str   # admin / member


class CreateMemberRequest(BaseModel):
    email: str
    password: str
    nickname: str = ""
    role: str = "member"


# ── 企业信息 ──────────────────────────────────────────────────────────────────

@router.get("/info")
def get_tenant_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前企业信息"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=404, detail="未绑定企业")
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="企业不存在")
    return {
        "id": tenant.id,
        "name": tenant.name,
        "created_at": tenant.created_at,
        "member_count": len(tenant.users),
    }


@router.put("/info")
def update_tenant_info(
    req: TenantUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新企业信息（仅 admin）"""
    _require_admin(current_user)
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="企业不存在")
    if req.name:
        tenant.name = req.name.strip()
    db.commit()
    return {"ok": True, "name": tenant.name}


# ── 成员管理 ──────────────────────────────────────────────────────────────────

@router.get("/members")
def list_members(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """列出所有成员"""
    members = (
        db.query(User)
        .filter(User.tenant_id == current_user.tenant_id, User.is_active == True)
        .order_by(User.created_at.asc())
        .all()
    )
    return [_user_to_dict(u) for u in members]


@router.put("/members/{user_id}/role")
def update_member_role(
    user_id: int,
    req: RoleUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """变更成员角色（仅 admin）"""
    _require_admin(current_user)
    if req.role not in ("admin", "member"):
        raise HTTPException(status_code=400, detail="角色只能是 admin 或 member")
    user = db.query(User).filter(
        User.id == user_id,
        User.tenant_id == current_user.tenant_id,
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="成员不存在")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能修改自己的角色")
    user.role = req.role
    db.commit()
    return {"ok": True}


@router.delete("/members/{user_id}")
def remove_member(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """移除成员（仅 admin；不能移除自己）"""
    _require_admin(current_user)
    user = db.query(User).filter(
        User.id == user_id,
        User.tenant_id == current_user.tenant_id,
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="成员不存在")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能移除自己")
    user.is_active = False
    db.commit()
    return {"ok": True}


@router.post("/members/create")
def create_member(
    req: CreateMemberRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """管理员直接创建成员（邮箱+密码）"""
    _require_admin(current_user)
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="未绑定企业")

    email = req.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="邮箱格式不正确")
    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="密码至少 8 位")
    if req.role not in ("admin", "member"):
        raise HTTPException(status_code=400, detail="角色只能是 admin 或 member")

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="该邮箱已被注册")

    password_hash = bcrypt.hashpw(req.password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")
    display_name = req.nickname.strip() or email.split("@")[0]

    user = User(
        tenant_id=current_user.tenant_id,
        email=email,
        password_hash=password_hash,
        wechat_openid=f"no_wechat_{uuid.uuid4().hex[:12]}",
        nickname=display_name,
        role=req.role,
    )
    db.add(user)
    db.flush()

    # 给新成员也创建试用订阅
    trial = Subscription(
        user_id=user.id,
        plan="trial",
        expire_at=datetime.utcnow() + timedelta(days=settings.trial_days),
    )
    db.add(trial)
    db.commit()

    return {"ok": True, "message": f"成员 {display_name} 创建成功", "user": _user_to_dict(user)}


# ── 邀请链接 ──────────────────────────────────────────────────────────────────

# 内存级邀请 token 存储（生产建议用 Redis）
_invite_tokens: dict[str, int] = {}   # token -> tenant_id


@router.post("/invite/create")
def create_invite_link(
    current_user: User = Depends(get_current_user),
):
    """生成一次性邀请 token（仅 admin）"""
    _require_admin(current_user)
    token = secrets.token_urlsafe(24)
    _invite_tokens[token] = current_user.tenant_id
    return {"invite_token": token}


@router.post("/invite/accept")
def accept_invite(
    invite_token: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """接受邀请，将当前用户加入企业"""
    tenant_id = _invite_tokens.pop(invite_token, None)
    if not tenant_id:
        raise HTTPException(status_code=404, detail="邀请链接无效或已使用")
    if current_user.tenant_id == tenant_id:
        raise HTTPException(status_code=400, detail="您已在该企业中")
    current_user.tenant_id = tenant_id
    current_user.role = "member"
    db.commit()
    return {"ok": True}


# ── 内部工具 ──────────────────────────────────────────────────────────────────

def _require_admin(user: User):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")


def _user_to_dict(u: User) -> dict:
    expire_at = None
    if u.subscription:
        expire_at = u.subscription.expire_at.isoformat()
    return {
        "id": u.id,
        "nickname": u.nickname or "",
        "avatar": u.avatar or "",
        "role": u.role,
        "is_active": u.is_active,
        "subscription_expire_at": expire_at,
        "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
        "created_at": u.created_at.isoformat() if u.created_at else None,
    }
