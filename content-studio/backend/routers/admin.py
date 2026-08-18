"""
平台管理端 API
- 管理员认证（账号密码登录）
- 租户管理
- 用户管理（创建/编辑/重置密码）
- 订阅管理
- 订单记录
- 内容管理
- 操作日志
- 数据仪表盘
"""
import hashlib
import uuid
import csv
import io
import bcrypt
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import func, case, extract
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models import AdminUser, Tenant, User, Subscription, PaymentOrder, Creator, Topic, Generation, Document, StyleTemplate, OperatorViewpoint, DocumentFolder, TenantCreator, CreatorVideo, CreatorIntelCard, VideoAnalysis

router = APIRouter(prefix="/admin", tags=["admin"])


# ═══════════════════════════════════════════════
#  工具函数
# ═══════════════════════════════════════════════

def _hash_password(password: str) -> str:
    """使用 bcrypt 哈希密码"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def _verify_admin_password(password: str, password_hash: str) -> bool:
    """验证密码，兼容旧 SHA256 哈希"""
    if password_hash.startswith("$2b$") or password_hash.startswith("$2a$"):
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    salted = f"cs_admin_{password}_{settings.jwt_secret}"
    return hashlib.sha256(salted.encode()).hexdigest() == password_hash


def _create_admin_token(admin_id: int) -> str:
    """为管理员生成JWT，payload带 admin 标识"""
    from jose import jwt as jose_jwt
    payload = {
        "sub": str(admin_id),
        "type": "admin",
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=24),
    }
    return jose_jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _decode_admin_token(token: str) -> Optional[int]:
    from jose import jwt as jose_jwt, JWTError
    try:
        payload = jose_jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "admin":
            return None
        return int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        return None


from fastapi import Header

def get_current_admin(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """管理员认证守卫"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    token = authorization.removeprefix("Bearer ").strip()
    admin_id = _decode_admin_token(token)
    if not admin_id:
        raise HTTPException(status_code=401, detail="Token 无效或已过期")
    admin = db.query(AdminUser).filter(AdminUser.id == admin_id, AdminUser.is_active == True).first()
    if not admin:
        raise HTTPException(status_code=401, detail="管理员不存在")
    return admin


# ═══════════════════════════════════════════════
#  管理员认证
# ═══════════════════════════════════════════════

class AdminLoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def admin_login(req: AdminLoginRequest, db: Session = Depends(get_db)):
    """管理员登录"""
    admin = db.query(AdminUser).filter(AdminUser.username == req.username).first()
    if not admin or not _verify_admin_password(req.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not admin.is_active:
        raise HTTPException(status_code=403, detail="账号已停用")
    # 自动迁移旧 SHA256 哈希到 bcrypt
    if not admin.password_hash.startswith("$2b$"):
        admin.password_hash = _hash_password(req.password)
    admin.last_login_at = datetime.utcnow()
    db.commit()
    return {
        "token": _create_admin_token(admin.id),
        "admin": {
            "id": admin.id,
            "username": admin.username,
            "nickname": admin.nickname,
        },
    }


@router.get("/me")
def admin_me(admin: AdminUser = Depends(get_current_admin)):
    """获取当前管理员信息"""
    return {
        "id": admin.id,
        "username": admin.username,
        "nickname": admin.nickname,
        "last_login_at": admin.last_login_at,
    }


@router.post("/init")
def admin_init(req: AdminLoginRequest, db: Session = Depends(get_db)):
    """
    初始化第一个管理员账号（仅当不存在任何管理员时可用）。
    部署后第一次访问管理端时调用。
    """
    existing = db.query(AdminUser).first()
    if existing:
        raise HTTPException(status_code=400, detail="管理员已存在，无法重复初始化")
    admin = AdminUser(
        username=req.username,
        password_hash=_hash_password(req.password),
        nickname="超级管理员",
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return {
        "message": "管理员账号创建成功",
        "token": _create_admin_token(admin.id),
        "admin": {
            "id": admin.id,
            "username": admin.username,
            "nickname": admin.nickname,
        },
    }


# ═══════════════════════════════════════════════
#  数据仪表盘
# ═══════════════════════════════════════════════

@router.get("/dashboard")
def admin_dashboard(
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    """管理端首页数据概览"""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)

    # 基础统计
    total_tenants = db.query(func.count(Tenant.id)).scalar() or 0
    total_users = db.query(func.count(User.id)).scalar() or 0
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0
    today_new_users = db.query(func.count(User.id)).filter(
        User.created_at >= today_start
    ).scalar() or 0

    # 订阅统计
    active_subscriptions = db.query(func.count(Subscription.id)).filter(
        Subscription.expire_at > now,
        Subscription.is_active == True,
    ).scalar() or 0
    trial_users = db.query(func.count(Subscription.id)).filter(
        Subscription.plan == "trial",
        Subscription.expire_at > now,
    ).scalar() or 0
    paid_users = db.query(func.count(Subscription.id)).filter(
        Subscription.plan != "trial",
        Subscription.expire_at > now,
    ).scalar() or 0

    # 收入统计
    total_revenue_fen = db.query(func.sum(PaymentOrder.amount_fen)).filter(
        PaymentOrder.status == "paid"
    ).scalar() or 0
    month_revenue_fen = db.query(func.sum(PaymentOrder.amount_fen)).filter(
        PaymentOrder.status == "paid",
        PaymentOrder.paid_at >= thirty_days_ago,
    ).scalar() or 0

    # 内容统计
    total_creators = db.query(func.count(Creator.id)).scalar() or 0
    total_topics = db.query(func.count(Topic.id)).scalar() or 0
    total_generations = db.query(func.count(Generation.id)).scalar() or 0

    # 近7天注册趋势
    register_trend = []
    for i in range(6, -1, -1):
        day = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day + timedelta(days=1)
        count = db.query(func.count(User.id)).filter(
            User.created_at >= day,
            User.created_at < day_end,
        ).scalar() or 0
        register_trend.append({
            "date": day.strftime("%m-%d"),
            "count": count,
        })

    # 近7天收入趋势
    revenue_trend = []
    for i in range(6, -1, -1):
        day = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day + timedelta(days=1)
        amount = db.query(func.sum(PaymentOrder.amount_fen)).filter(
            PaymentOrder.status == "paid",
            PaymentOrder.paid_at >= day,
            PaymentOrder.paid_at < day_end,
        ).scalar() or 0
        revenue_trend.append({
            "date": day.strftime("%m-%d"),
            "amount": round(amount / 100, 2),
        })

    return {
        "overview": {
            "total_tenants": total_tenants,
            "total_users": total_users,
            "active_users": active_users,
            "today_new_users": today_new_users,
            "active_subscriptions": active_subscriptions,
            "trial_users": trial_users,
            "paid_users": paid_users,
            "total_revenue": round(total_revenue_fen / 100, 2),
            "month_revenue": round(month_revenue_fen / 100, 2),
        },
        "content": {
            "total_creators": total_creators,
            "total_topics": total_topics,
            "total_generations": total_generations,
        },
        "register_trend": register_trend,
        "revenue_trend": revenue_trend,
    }


# ═══════════════════════════════════════════════
#  租户管理
# ═══════════════════════════════════════════════

@router.get("/tenants")
def list_tenants(
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    """租户列表"""
    q = db.query(Tenant)
    if keyword:
        q = q.filter(Tenant.name.contains(keyword))
    total = q.count()
    tenants = q.order_by(Tenant.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for t in tenants:
        member_count = db.query(func.count(User.id)).filter(User.tenant_id == t.id).scalar() or 0
        # 找该租户的管理员
        admin_user = db.query(User).filter(User.tenant_id == t.id, User.role == "admin").first()
        # 订阅状态
        if admin_user and admin_user.subscription:
            sub = admin_user.subscription
            sub_info = {
                "plan": sub.plan,
                "expire_at": sub.expire_at.isoformat() if sub.expire_at else None,
                "is_active": sub.expire_at > datetime.utcnow() if sub.expire_at else False,
            }
        else:
            sub_info = {"plan": "none", "expire_at": None, "is_active": False}

        result.append({
            "id": t.id,
            "name": t.name,
            "member_count": member_count,
            "admin_nickname": admin_user.nickname if admin_user else "",
            "admin_avatar": admin_user.avatar if admin_user else "",
            "subscription": sub_info,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        })

    return {"items": result, "total": total, "page": page, "page_size": page_size}


@router.get("/tenants/{tenant_id}")
def get_tenant_detail(
    tenant_id: int,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    """租户详情"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")

    members = db.query(User).filter(User.tenant_id == tenant_id).all()
    creators_count = db.query(TenantCreator).filter(TenantCreator.tenant_id == tenant_id).count()
    topics_count = db.query(func.count(Topic.id)).filter(Topic.tenant_id == tenant_id).scalar() or 0
    generations_count = db.query(func.count(Generation.id)).filter(Generation.tenant_id == tenant_id).scalar() or 0

    return {
        "id": tenant.id,
        "name": tenant.name,
        "created_at": tenant.created_at.isoformat() if tenant.created_at else None,
        "members": [
            {
                "id": u.id,
                "nickname": u.nickname,
                "avatar": u.avatar,
                "role": u.role,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
                "subscription": {
                    "plan": u.subscription.plan if u.subscription else "none",
                    "expire_at": u.subscription.expire_at.isoformat() if u.subscription and u.subscription.expire_at else None,
                    "is_active": u.is_subscription_active,
                } if True else None,
            }
            for u in members
        ],
        "stats": {
            "creators": creators_count,
            "topics": topics_count,
            "generations": generations_count,
        },
    }


# ═══════════════════════════════════════════════
#  用户管理
# ═══════════════════════════════════════════════

@router.get("/users")
def list_users(
    keyword: Optional[str] = None,
    is_active: Optional[bool] = None,
    plan: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    """用户列表"""
    q = db.query(User)
    if keyword:
        q = q.filter(User.nickname.contains(keyword) | User.email.contains(keyword))
    if is_active is not None:
        q = q.filter(User.is_active == is_active)
    if plan:
        sub_ids = db.query(Subscription.user_id).filter(Subscription.plan == plan).subquery()
        q = q.filter(User.id.in_(sub_ids))
    total = q.count()
    users = q.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for u in users:
        tenant = db.query(Tenant).filter(Tenant.id == u.tenant_id).first() if u.tenant_id else None
        sub = u.subscription
        result.append({
            "id": u.id,
            "nickname": u.nickname,
            "email": u.email or "",
            "avatar": u.avatar,
            "role": u.role,
            "is_active": u.is_active,
            "tenant_id": u.tenant_id,
            "tenant_name": tenant.name if tenant else "",
            "wechat_openid": u.wechat_openid[:8] + "..." if u.wechat_openid else "",
            "subscription": {
                "plan": sub.plan if sub else "none",
                "expire_at": sub.expire_at.isoformat() if sub and sub.expire_at else None,
                "is_active": u.is_subscription_active,
                "is_trial": u.is_trial,
            },
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
        })

    return {"items": result, "total": total, "page": page, "page_size": page_size}


@router.patch("/users/{user_id}/ban")
def ban_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    """封禁用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.is_active = False
    db.commit()
    return {"ok": True, "message": "已封禁"}


@router.patch("/users/{user_id}/unban")
def unban_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    """解封用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.is_active = True
    db.commit()
    return {"ok": True, "message": "已解封"}


# ═══════════════════════════════════════════════
#  订阅管理
# ═══════════════════════════════════════════════

class SubscriptionAction(BaseModel):
    days: int = 30            # 延长/赠送天数
    plan: str = "monthly"     # 套餐类型


@router.post("/users/{user_id}/subscription/extend")
def extend_subscription(
    user_id: int,
    req: SubscriptionAction,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    """手动延长用户订阅"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    sub = user.subscription
    now = datetime.utcnow()
    if sub:
        # 从当前过期时间或现在（取较晚者）开始延长
        base = max(sub.expire_at, now) if sub.expire_at else now
        sub.expire_at = base + timedelta(days=req.days)
        sub.plan = req.plan
        sub.is_active = True
    else:
        sub = Subscription(
            user_id=user.id,
            plan=req.plan,
            expire_at=now + timedelta(days=req.days),
            is_active=True,
        )
        db.add(sub)

    db.commit()
    return {
        "ok": True,
        "message": f"已延长 {req.days} 天",
        "expire_at": sub.expire_at.isoformat(),
    }


@router.post("/users/{user_id}/subscription/revoke")
def revoke_subscription(
    user_id: int,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    """撤销用户订阅（立即过期）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    sub = user.subscription
    if not sub:
        raise HTTPException(status_code=400, detail="该用户无订阅")
    sub.expire_at = datetime.utcnow()
    sub.is_active = False
    db.commit()
    return {"ok": True, "message": "订阅已撤销"}


# ═══════════════════════════════════════════════
#  订单记录
# ═══════════════════════════════════════════════

@router.get("/orders")
def list_orders(
    status: Optional[str] = None,
    method: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    """支付订单列表"""
    q = db.query(PaymentOrder)
    if status:
        q = q.filter(PaymentOrder.status == status)
    if method:
        q = q.filter(PaymentOrder.method == method)
    if keyword:
        # 搜索订单号或流水号
        user_ids = db.query(User.id).filter(User.nickname.contains(keyword)).subquery()
        q = q.filter(
            PaymentOrder.order_no.contains(keyword) |
            PaymentOrder.transaction_id.contains(keyword) |
            PaymentOrder.user_id.in_(user_ids)
        )
    total = q.count()
    orders = q.order_by(PaymentOrder.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for o in orders:
        user = db.query(User).filter(User.id == o.user_id).first()
        result.append({
            "id": o.id,
            "order_no": o.order_no,
            "user_id": o.user_id,
            "user_nickname": user.nickname if user else "",
            "amount": round(o.amount_fen / 100, 2),
            "amount_fen": o.amount_fen,
            "method": o.method,
            "plan": o.plan,
            "status": o.status,
            "transaction_id": o.transaction_id,
            "paid_at": o.paid_at.isoformat() if o.paid_at else None,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        })

    return {"items": result, "total": total, "page": page, "page_size": page_size}


# ═══════════════════════════════════════════════
#  用户管理（创建/编辑/重置密码）
# ═══════════════════════════════════════════════

def _hash_user_password(password: str) -> str:
    """使用 bcrypt 哈希用户密码，与 auth.py 保持一致"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


class CreateUserRequest(BaseModel):
    email: str
    password: str
    nickname: str = ""


class EditUserRequest(BaseModel):
    nickname: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None


class ResetPasswordRequest(BaseModel):
    password: str


@router.post("/users/create")
def create_user(
    req: CreateUserRequest,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    """管理员创建用户"""
    if not req.email or "@" not in req.email:
        raise HTTPException(status_code=400, detail="邮箱格式不正确")
    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="密码至少 8 位")
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="该邮箱已被注册")

    display_name = req.nickname or req.email.split("@")[0]
    tenant = Tenant(name=f"{display_name}的空间")
    db.add(tenant)
    db.flush()

    user = User(
        tenant_id=tenant.id,
        email=req.email,
        password_hash=_hash_user_password(req.password),
        wechat_openid=f"no_wechat_{uuid.uuid4().hex[:12]}",
        nickname=display_name,
        role="admin",
    )
    db.add(user)
    db.flush()

    sub = Subscription(
        user_id=user.id,
        plan="trial",
        expire_at=datetime.utcnow() + timedelta(days=settings.trial_days),
        is_active=True,
    )
    db.add(sub)
    db.commit()
    db.refresh(user)
    return {"ok": True, "message": f"用户 {display_name} 创建成功", "user_id": user.id}


@router.patch("/users/{user_id}/edit")
def edit_user(
    user_id: int,
    req: EditUserRequest,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    """编辑用户资料"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if req.nickname is not None:
        user.nickname = req.nickname
    if req.email is not None:
        dup = db.query(User).filter(User.email == req.email, User.id != user_id).first()
        if dup:
            raise HTTPException(status_code=400, detail="该邮箱已被其他用户使用")
        user.email = req.email
    if req.is_active is not None:
        user.is_active = req.is_active
    db.commit()
    return {"ok": True, "message": "用户信息已更新"}


@router.post("/users/{user_id}/reset-password")
def reset_user_password(
    user_id: int,
    req: ResetPasswordRequest,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    """重置用户密码"""
    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="密码至少 8 位")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.password_hash = _hash_user_password(req.password)
    db.commit()
    return {"ok": True, "message": "密码已重置"}


# ═══════════════════════════════════════════════
#  管理员账号管理
# ═══════════════════════════════════════════════

class ChangeAdminPasswordRequest(BaseModel):
    old_password: str
    new_password: str


class CreateAdminRequest(BaseModel):
    username: str
    password: str
    nickname: str = ""


@router.post("/change-password")
def change_admin_password(
    req: ChangeAdminPasswordRequest,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    """修改当前管理员密码"""
    if not _verify_admin_password(req.old_password, admin.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    if len(req.new_password) < 8:
        raise HTTPException(status_code=400, detail="新密码至少 8 位")
    admin.password_hash = _hash_password(req.new_password)
    db.commit()
    return {"ok": True, "message": "密码已修改"}


@router.post("/admins/create")
def create_admin(
    req: CreateAdminRequest,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    """添加新管理员"""
    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="密码至少 8 位")
    existing = db.query(AdminUser).filter(AdminUser.username == req.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    new_admin = AdminUser(
        username=req.username,
        password_hash=_hash_password(req.password),
        nickname=req.nickname or req.username,
    )
    db.add(new_admin)
    db.commit()
    return {"ok": True, "message": f"管理员 {req.username} 创建成功"}


@router.get("/admins")
def list_admins(
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    """管理员列表"""
    admins = db.query(AdminUser).order_by(AdminUser.id).all()
    return [
        {
            "id": a.id,
            "username": a.username,
            "nickname": a.nickname,
            "is_active": a.is_active,
            "last_login_at": a.last_login_at.isoformat() if a.last_login_at else None,
        }
        for a in admins
    ]


@router.delete("/admins/{admin_id}")
def delete_admin(
    admin_id: int,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    """删除管理员（不能删除自己）"""
    if admin_id == admin.id:
        raise HTTPException(status_code=400, detail="不能删除当前登录的管理员")
    target = db.query(AdminUser).filter(AdminUser.id == admin_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="管理员不存在")
    db.delete(target)
    db.commit()
    return {"ok": True, "message": f"管理员 {target.username} 已删除"}


# ═══════════════════════════════════════════════
#  租户管理（编辑/删除）
# ═══════════════════════════════════════════════

class EditTenantRequest(BaseModel):
    name: str


@router.patch("/tenants/{tenant_id}")
def edit_tenant(
    tenant_id: int,
    req: EditTenantRequest,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    """编辑租户名称"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")
    tenant.name = req.name
    db.commit()
    return {"ok": True, "message": "租户名称已更新"}


@router.delete("/tenants/{tenant_id}")
def delete_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    """删除租户及其下所有数据"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")
    users = db.query(User).filter(User.tenant_id == tenant_id).all()
    for u in users:
        db.query(Subscription).filter(Subscription.user_id == u.id).delete()
        db.query(PaymentOrder).filter(PaymentOrder.user_id == u.id).delete()
    db.query(User).filter(User.tenant_id == tenant_id).delete()
    # 只删除订阅关系，不删除共享的 Creator/CreatorVideo
    db.query(TenantCreator).filter(TenantCreator.tenant_id == tenant_id).delete()
    db.query(Topic).filter(Topic.tenant_id == tenant_id).delete()
    db.query(Generation).filter(Generation.tenant_id == tenant_id).delete()
    db.query(Document).filter(Document.tenant_id == tenant_id).delete()
    db.query(StyleTemplate).filter(StyleTemplate.tenant_id == tenant_id).delete()
    db.query(OperatorViewpoint).filter(OperatorViewpoint.tenant_id == tenant_id).delete()
    db.query(CreatorIntelCard).filter(CreatorIntelCard.tenant_id == tenant_id).delete()
    db.query(VideoAnalysis).filter(VideoAnalysis.tenant_id == tenant_id).delete()
    db.query(DocumentFolder).filter(DocumentFolder.tenant_id == tenant_id).delete()
    db.delete(tenant)
    db.commit()
    return {"ok": True, "message": "租户已删除"}


# ═══════════════════════════════════════════════
#  内容审核（查看创作者/选题/生成内容）
# ═══════════════════════════════════════════════

@router.get("/creators")
def list_creators(
    keyword: Optional[str] = None,
    tenant_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    """创作者列表"""
    q = db.query(Creator)
    if keyword:
        q = q.filter(Creator.nickname.contains(keyword))
    if tenant_id:
        q = q.join(TenantCreator, TenantCreator.creator_id == Creator.id).filter(
            TenantCreator.tenant_id == tenant_id
        )
    total = q.count()
    items = q.order_by(Creator.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for c in items:
        # 找到订阅该博主的租户列表
        subs = db.query(TenantCreator).filter(TenantCreator.creator_id == c.id).all()
        tenant_ids = [s.tenant_id for s in subs]
        tenant_names = []
        for tid in tenant_ids:
            t = db.query(Tenant).filter(Tenant.id == tid).first()
            if t:
                tenant_names.append(t.name)
        result.append({
            "id": c.id,
            "name": c.nickname or "",
            "platform": c.platform,
            "identifier": c.unique_id or c.platform_id or "",
            "style_summary": (c.bio or "")[:80],
            "video_count": db.query(CreatorVideo).filter(CreatorVideo.creator_id == c.id).count(),
            "tenant_ids": tenant_ids,
            "tenant_names": tenant_names,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })
    return {"items": result, "total": total, "page": page, "page_size": page_size}


@router.get("/topics")
def list_topics(
    keyword: Optional[str] = None,
    tenant_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    """选题列表"""
    q = db.query(Topic)
    if keyword:
        q = q.filter(Topic.title.contains(keyword))
    if tenant_id:
        q = q.filter(Topic.tenant_id == tenant_id)
    total = q.count()
    items = q.order_by(Topic.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for t in items:
        tenant = db.query(Tenant).filter(Tenant.id == t.tenant_id).first()
        result.append({
            "id": t.id,
            "title": t.title,
            "platform": t.platform if hasattr(t, "platform") else "",
            "source_url": t.source_url if hasattr(t, "source_url") else "",
            "tenant_id": t.tenant_id,
            "tenant_name": tenant.name if tenant else "",
            "created_at": t.created_at.isoformat() if t.created_at else None,
        })
    return {"items": result, "total": total, "page": page, "page_size": page_size}


@router.get("/generations")
def list_generations(
    tenant_id: Optional[int] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    """生成内容列表"""
    q = db.query(Generation)
    if tenant_id:
        q = q.filter(Generation.tenant_id == tenant_id)
    if keyword:
        q = q.filter(
            Generation.topic.contains(keyword) | Generation.output_title.contains(keyword) | Generation.output_full.contains(keyword)
        )
    total = q.count()
    items = q.order_by(Generation.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for g in items:
        tenant = db.query(Tenant).filter(Tenant.id == g.tenant_id).first()
        full = g.output_full or ""
        result.append({
            "id": g.id,
            "title": g.output_title or g.topic or "",
            "content_preview": (full[:100] + "...") if len(full) > 100 else full,
            "full_content": full,
            "tenant_id": g.tenant_id,
            "tenant_name": tenant.name if tenant else "",
            "created_at": g.created_at.isoformat() if g.created_at else None,
        })
    return {"items": result, "total": total, "page": page, "page_size": page_size}


# ═══════════════════════════════════════════════
#  数据导出
# ═══════════════════════════════════════════════

@router.get("/export/users")
def export_users(
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    """导出用户列表为 CSV"""
    users = db.query(User).order_by(User.id).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "昵称", "邮箱", "角色", "状态", "租户ID", "订阅", "过期时间", "注册时间", "最后登录"])
    for u in users:
        sub = u.subscription
        writer.writerow([
            u.id, u.nickname, u.email or "", u.role,
            "正常" if u.is_active else "封禁",
            u.tenant_id or "",
            sub.plan if sub else "无",
            sub.expire_at.strftime("%Y-%m-%d") if sub and sub.expire_at else "",
            u.created_at.strftime("%Y-%m-%d %H:%M") if u.created_at else "",
            u.last_login_at.strftime("%Y-%m-%d %H:%M") if u.last_login_at else "",
        ])
    output.seek(0)
    return StreamingResponse(
        iter(["\ufeff" + output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=users.csv"},
    )


@router.get("/export/orders")
def export_orders(
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    """导出订单列表为 CSV"""
    orders = db.query(PaymentOrder).order_by(PaymentOrder.id.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["订单号", "用户ID", "金额(元)", "支付方式", "套餐", "状态", "流水号", "支付时间", "创建时间"])
    for o in orders:
        writer.writerow([
            o.order_no, o.user_id, round(o.amount_fen / 100, 2),
            o.method, o.plan, o.status,
            o.transaction_id or "",
            o.paid_at.strftime("%Y-%m-%d %H:%M") if o.paid_at else "",
            o.created_at.strftime("%Y-%m-%d %H:%M") if o.created_at else "",
        ])
    output.seek(0)
    return StreamingResponse(
        iter(["\ufeff" + output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=orders.csv"},
    )
