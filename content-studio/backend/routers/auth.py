"""
认证路由：邮箱注册/登录 + Google OAuth + GitHub OAuth + 微信 + JWT
"""
import uuid
import hashlib
import bcrypt
import httpx
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import User, Tenant, Subscription, WechatScene
from services.auth import (
    create_scene_qrcode, get_wx_userinfo_by_code,
    create_jwt_token, verify_wechat_signature,
)
from config import settings
from .deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

_LOGIN_WINDOW_SECONDS = 60
_LOGIN_MAX_ATTEMPTS = 5
_login_attempts: dict[str, list[float]] = {}


# ── 密码哈希 ──────────────────────────────────────────────────────────────────

def _hash_password(password: str) -> str:
    """使用 bcrypt 哈希密码"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def _verify_password(password: str, password_hash: str) -> bool:
    """验证密码，兼容旧 SHA256 哈希"""
    if password_hash.startswith("$2b$") or password_hash.startswith("$2a$"):
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    # 兼容旧 SHA256 格式
    salted = f"cs_user_{password}_{settings.jwt_secret}"
    return hashlib.sha256(salted.encode()).hexdigest() == password_hash


# ── Pydantic 模型 ──────────────────────────────────────────────────────────────

class EmailRegisterRequest(BaseModel):
    email: str
    password: str
    nickname: str = ""


class EmailLoginRequest(BaseModel):
    email: str
    password: str


class OAuthCallbackRequest(BaseModel):
    code: str


class GoogleCallbackRequest(BaseModel):
    code: str
    redirect_uri: str = ""


class GithubCallbackRequest(BaseModel):
    code: str


class UserOut(BaseModel):
    id: int
    nickname: str
    avatar: str
    role: str
    subscription_expire_at: datetime | None
    is_trial: bool
    is_subscription_active: bool

    class Config:
        from_attributes = True


# ── 工具函数 ──────────────────────────────────────────────────────────────────

def _create_new_user(db: Session, *, email: str = None, password_hash: str = None,
                     oauth_provider: str = None, oauth_id: str = None,
                     wechat_openid: str = None, nickname: str = "", avatar: str = "") -> User:
    """创建新用户 + 租户 + 试用订阅"""
    display_name = nickname or (email.split("@")[0] if email else "新用户")
    tenant = Tenant(name=f"{display_name}的空间")
    db.add(tenant)
    db.flush()

    user = User(
        tenant_id=tenant.id,
        email=email,
        password_hash=password_hash,
        oauth_provider=oauth_provider,
        oauth_id=oauth_id,
        wechat_openid=wechat_openid or f"no_wechat_{uuid.uuid4().hex[:12]}",
        nickname=display_name,
        avatar=avatar,
        role="admin",
    )
    db.add(user)
    db.flush()

    trial = Subscription(
        user_id=user.id,
        plan="trial",
        expire_at=datetime.utcnow() + timedelta(days=settings.trial_days),
    )
    db.add(trial)
    db.commit()
    db.refresh(user)
    return user


def _rotate_user_session(user: User):
    user.session_version = int(user.session_version or 0) + 1
    user.last_login_at = datetime.utcnow()


def _login_response(db: Session, user: User) -> dict:
    _rotate_user_session(user)
    db.commit()
    db.refresh(user)
    token = create_jwt_token(user.id, user.session_version)
    return {"token": token, "user": _user_to_dict(user)}


def _get_or_create_user(db: Session, openid: str, userinfo: dict) -> User:
    """根据 openid 查找或创建用户（微信登录用）"""
    user = db.query(User).filter(User.wechat_openid == openid).first()
    if not user:
        user = _create_new_user(
            db, wechat_openid=openid,
            nickname=userinfo.get("nickname", ""),
            avatar=userinfo.get("avatar", ""),
        )
    else:
        if userinfo.get("nickname"):
            user.nickname = userinfo["nickname"]
        if userinfo.get("avatar"):
            user.avatar = userinfo["avatar"]
    return user


def _user_to_dict(user: User) -> dict:
    expire_at = None
    if user.subscription:
        # 加 Z 后缀明确标注 UTC，防止浏览器误当本地时间解析
        expire_at = user.subscription.expire_at.strftime('%Y-%m-%dT%H:%M:%SZ')
    return {
        "id": user.id,
        "nickname": user.nickname or "",
        "avatar": user.avatar or "",
        "role": user.role,
        "email": user.email or "",
        "subscription_expire_at": expire_at,
        "is_trial": user.is_trial,
        "is_subscription_active": user.is_subscription_active,
    }


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _login_rate_limit_key(request: Request, email: str) -> str:
    return f"{_get_client_ip(request)}:{email.strip().lower()}"


def _prune_attempts(timestamps: list[float], now: float) -> list[float]:
    return [ts for ts in timestamps if now - ts < _LOGIN_WINDOW_SECONDS]


def _check_login_rate_limit(key: str) -> int:
    now = time.time()
    attempts = _prune_attempts(_login_attempts.get(key, []), now)
    if attempts:
        _login_attempts[key] = attempts
    else:
        _login_attempts.pop(key, None)

    if len(attempts) >= _LOGIN_MAX_ATTEMPTS:
        retry_after = max(1, int(_LOGIN_WINDOW_SECONDS - (now - attempts[0])))
        return retry_after
    return 0


def _record_login_failure(key: str):
    now = time.time()
    attempts = _prune_attempts(_login_attempts.get(key, []), now)
    attempts.append(now)
    _login_attempts[key] = attempts


def _clear_login_attempts(key: str):
    _login_attempts.pop(key, None)


# ═══════════════════════════════════════════════
#  邮箱注册 / 登录
# ═══════════════════════════════════════════════

@router.post("/register")
def email_register(body: EmailRegisterRequest, db: Session = Depends(get_db)):
    """邮箱注册"""
    email = body.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="邮箱格式不正确")
    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail="密码至少 8 位")
    if body.password.isdigit() or body.password.isalpha():
        raise HTTPException(status_code=400, detail="密码需要同时包含字母和数字")

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=409, detail="该邮箱已注册")

    user = _create_new_user(
        db, email=email,
        password_hash=_hash_password(body.password),
        nickname=body.nickname or email.split("@")[0],
    )
    return _login_response(db, user)


@router.post("/login")
def email_login(body: EmailLoginRequest, request: Request, db: Session = Depends(get_db)):
    """邮箱登录"""
    email = body.email.strip().lower()
    limit_key = _login_rate_limit_key(request, email)
    retry_after = _check_login_rate_limit(limit_key)
    if retry_after > 0:
        raise HTTPException(status_code=429, detail=f"登录尝试过于频繁，请 {retry_after} 秒后重试")

    user = db.query(User).filter(User.email == email).first()
    if not user or not user.password_hash or not _verify_password(body.password, user.password_hash):
        _record_login_failure(limit_key)
        raise HTTPException(status_code=401, detail="邮箱或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已被停用")

    _clear_login_attempts(limit_key)
    # 自动迁移旧 SHA256 哈希到 bcrypt
    if not user.password_hash.startswith("$2b$"):
        user.password_hash = _hash_password(body.password)
    return _login_response(db, user)


# ═══════════════════════════════════════════════
#  Google OAuth
# ═══════════════════════════════════════════════

@router.get("/google/url")
def google_oauth_url(redirect_uri: str = Query("")):
    """返回 Google OAuth 授权 URL"""
    if not settings.google_client_id:
        raise HTTPException(status_code=503, detail="Google OAuth 未配置")
    if not redirect_uri:
        redirect_uri = f"{settings.frontend_url}/auth/callback?provider=google"
    import urllib.parse
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    return {"url": url}


@router.post("/google/callback")
async def google_callback(body: GoogleCallbackRequest, db: Session = Depends(get_db)):
    """Google OAuth 回调：用 code 换取用户信息"""
    redirect_uri = body.redirect_uri or f"{settings.frontend_url}/auth/callback?provider=google"

    async with httpx.AsyncClient() as client:
        token_resp = await client.post("https://oauth2.googleapis.com/token", data={
            "code": body.code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }, timeout=15)

    if token_resp.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Google 授权失败: {token_resp.text}")

    token_data = token_resp.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="未获取到 access_token")

    async with httpx.AsyncClient() as client:
        userinfo_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )

    if userinfo_resp.status_code != 200:
        raise HTTPException(status_code=400, detail="获取 Google 用户信息失败")

    info = userinfo_resp.json()
    google_id = info.get("id", "")
    email = info.get("email", "")
    name = info.get("name", "")
    avatar = info.get("picture", "")

    # 查找已有用户（先按 oauth_id，再按 email）
    user = db.query(User).filter(User.oauth_provider == "google", User.oauth_id == google_id).first()
    if not user and email:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.oauth_provider = "google"
            user.oauth_id = google_id
            if not user.avatar and avatar:
                user.avatar = avatar

    if not user:
        user = _create_new_user(
            db, email=email, oauth_provider="google", oauth_id=google_id,
            nickname=name, avatar=avatar,
        )
    return _login_response(db, user)


# ═══════════════════════════════════════════════
#  GitHub OAuth
# ═══════════════════════════════════════════════

@router.get("/github/url")
def github_oauth_url(redirect_uri: str = Query("")):
    """返回 GitHub OAuth 授权 URL"""
    if not settings.github_client_id:
        raise HTTPException(status_code=503, detail="GitHub OAuth 未配置")
    if not redirect_uri:
        redirect_uri = f"{settings.frontend_url}/auth/callback?provider=github"
    import urllib.parse
    params = {
        "client_id": settings.github_client_id,
        "redirect_uri": redirect_uri,
        "scope": "read:user user:email",
    }
    url = "https://github.com/login/oauth/authorize?" + urllib.parse.urlencode(params)
    return {"url": url}


@router.post("/github/callback")
async def github_callback(body: GithubCallbackRequest, db: Session = Depends(get_db)):
    """GitHub OAuth 回调"""
    async with httpx.AsyncClient() as client:
        token_resp = await client.post("https://github.com/login/oauth/access_token", json={
            "client_id": settings.github_client_id,
            "client_secret": settings.github_client_secret,
            "code": body.code,
        }, headers={"Accept": "application/json"}, timeout=15)

    if token_resp.status_code != 200:
        raise HTTPException(status_code=400, detail="GitHub 授权失败")

    token_data = token_resp.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail=f"GitHub 授权失败: {token_data.get('error_description', '')}")

    async with httpx.AsyncClient() as client:
        user_resp = await client.get("https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"}, timeout=10)
        email_resp = await client.get("https://api.github.com/user/emails",
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"}, timeout=10)

    if user_resp.status_code != 200:
        raise HTTPException(status_code=400, detail="获取 GitHub 用户信息失败")

    info = user_resp.json()
    github_id = str(info.get("id", ""))
    name = info.get("name") or info.get("login", "")
    avatar = info.get("avatar_url", "")

    email = info.get("email") or ""
    if not email and email_resp.status_code == 200:
        emails = email_resp.json()
        primary = next((e for e in emails if e.get("primary")), None)
        if primary:
            email = primary.get("email", "")

    user = db.query(User).filter(User.oauth_provider == "github", User.oauth_id == github_id).first()
    if not user and email:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.oauth_provider = "github"
            user.oauth_id = github_id
            if not user.avatar and avatar:
                user.avatar = avatar

    if not user:
        user = _create_new_user(
            db, email=email, oauth_provider="github", oauth_id=github_id,
            nickname=name, avatar=avatar,
        )
    return _login_response(db, user)


# ═══════════════════════════════════════════════
#  微信登录（保留兼容）
# ═══════════════════════════════════════════════

@router.get("/wechat/oauth-url")
def get_oauth_url(redirect_uri: str = Query(...)):
    import urllib.parse
    encoded = urllib.parse.quote(redirect_uri, safe="")
    url = (
        f"https://open.weixin.qq.com/connect/oauth2/authorize"
        f"?appid={settings.wechat_appid}"
        f"&redirect_uri={encoded}"
        f"&response_type=code"
        f"&scope=snsapi_userinfo"
        f"&state=login"
        f"#wechat_redirect"
    )
    return {"url": url}


@router.post("/wechat/callback")
async def oauth_callback(body: OAuthCallbackRequest, db: Session = Depends(get_db)):
    try:
        userinfo = await get_wx_userinfo_by_code(body.code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"微信授权失败: {e}")
    user = _get_or_create_user(db, userinfo["openid"], userinfo)
    return _login_response(db, user)


@router.post("/scene/create")
async def create_scene(db: Session = Depends(get_db)):
    scene_id = str(uuid.uuid4())
    expire_at = datetime.utcnow() + timedelta(minutes=30)
    try:
        qr_data = await create_scene_qrcode(scene_id)
        qr_url = qr_data["qr_url"]
        ticket = qr_data["ticket"]
    except Exception as e:
        if settings.debug:
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=220x220&data={scene_id}"
            ticket = "dev_ticket"
        else:
            raise HTTPException(status_code=503, detail=f"创建二维码失败: {e}")

    scene = WechatScene(scene_id=scene_id, ticket=ticket, qr_url=qr_url, expire_at=expire_at)
    db.add(scene)
    db.commit()
    return {"scene_id": scene_id, "qr_url": qr_url, "expire_at": expire_at.isoformat()}


@router.get("/scene/{scene_id}/status")
def poll_scene(scene_id: str, db: Session = Depends(get_db)):
    scene = db.query(WechatScene).filter(WechatScene.scene_id == scene_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail="scene not found")
    if datetime.utcnow() > scene.expire_at:
        return {"status": "expired"}
    if scene.status == "authorized" and scene.token:
        return {"status": "authorized", "token": scene.token}
    return {"status": scene.status}


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return _user_to_dict(current_user)


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@router.post("/change-password")
def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """用户自己修改密码"""
    if not current_user.password_hash:
        raise HTTPException(status_code=400, detail="该账号使用第三方登录，无法修改密码")
    if not _verify_password(body.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    if len(body.new_password) < 8:
        raise HTTPException(status_code=400, detail="新密码至少 8 位")
    if body.new_password.isdigit() or body.new_password.isalpha():
        raise HTTPException(status_code=400, detail="新密码需同时包含字母和数字")
    current_user.password_hash = _hash_password(body.new_password)
    db.commit()
    return {"ok": True, "message": "密码修改成功"}


@router.post("/refresh")
def refresh_token(current_user: User = Depends(get_current_user)):
    token = create_jwt_token(current_user.id, int(current_user.session_version or 1))
    return {"token": token}


# ── 微信服务器消息推送 ──────────────────────────────────────────────────────────

@router.get("/wechat/notify")
def wechat_verify(signature: str = Query(""), timestamp: str = Query(""),
                  nonce: str = Query(""), echostr: str = Query("")):
    if verify_wechat_signature(signature, timestamp, nonce):
        return PlainTextResponse(echostr)
    raise HTTPException(status_code=403, detail="signature invalid")


@router.post("/wechat/notify")
async def wechat_event(request: Request, signature: str = Query(""),
                       timestamp: str = Query(""), nonce: str = Query(""),
                       db: Session = Depends(get_db)):
    if not verify_wechat_signature(signature, timestamp, nonce):
        raise HTTPException(status_code=403, detail="signature invalid")
    body = await request.body()
    try:
        root = ET.fromstring(body.decode("utf-8"))
        msg_type = root.findtext("MsgType", "")
        event = root.findtext("Event", "")
        event_key = root.findtext("EventKey", "")
        openid = root.findtext("FromUserName", "")
    except ET.ParseError:
        return PlainTextResponse("success")

    if msg_type == "event" and event in ("SCAN", "subscribe") and event_key:
        scene_id = event_key.replace("qrscene_", "")
        scene = db.query(WechatScene).filter(WechatScene.scene_id == scene_id).first()
        if scene and scene.status == "pending":
            user = db.query(User).filter(User.wechat_openid == openid).first()
            if not user:
                user = _get_or_create_user(db, openid, {"nickname": "", "avatar": ""})
            _rotate_user_session(user)
            token = create_jwt_token(user.id, user.session_version)
            scene.status = "authorized"
            scene.openid = openid
            scene.token = token
            db.commit()
    return PlainTextResponse("success")

