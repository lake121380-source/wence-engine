"""
认证服务：JWT 签发/验证 + 微信公众号 OAuth / 场景二维码
"""
import uuid
import time
import hmac
import hashlib
import httpx
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt

from config import settings

# ── 微信公众号 Access Token（进程级缓存，实际建议用 Redis）──
_wx_token_cache: dict = {"token": "", "expire_at": 0}


async def get_wx_access_token() -> str:
    """获取/刷新公众号 access_token（缓存 7000 秒）"""
    now = time.time()
    if _wx_token_cache["expire_at"] > now + 60:
        return _wx_token_cache["token"]

    url = (
        "https://api.weixin.qq.com/cgi-bin/token"
        f"?grant_type=client_credential"
        f"&appid={settings.wechat_appid}"
        f"&secret={settings.wechat_appsecret}"
    )
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=10)
        data = resp.json()

    if "access_token" not in data:
        raise RuntimeError(f"获取 wx access_token 失败: {data}")

    _wx_token_cache["token"] = data["access_token"]
    _wx_token_cache["expire_at"] = now + data.get("expires_in", 7200)
    return _wx_token_cache["token"]


async def create_scene_qrcode(scene_id: str) -> dict:
    """
    创建带参数场景二维码（PC 扫码登录用）
    返回: {ticket, url, qr_url}
    """
    access_token = await get_wx_access_token()
    url = f"https://api.weixin.qq.com/cgi-bin/qrcode/create?access_token={access_token}"
    body = {
        "action_name": "QR_STR_SCENE",
        "expire_seconds": 1800,               # 30分钟有效
        "action_info": {
            "scene": {"scene_str": scene_id}
        }
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=body, timeout=10)
        data = resp.json()

    if "ticket" not in data:
        raise RuntimeError(f"创建扫码二维码失败: {data}")

    ticket = data["ticket"]
    qr_url = f"https://mp.weixin.qq.com/cgi-bin/showqrcode?ticket={ticket}"
    return {"ticket": ticket, "qr_url": qr_url}


async def get_wx_userinfo_by_code(code: str) -> dict:
    """
    OAuth 网页授权：以 code 换取 openid + 用户信息（scope=snsapi_userinfo）
    返回: {openid, unionid, nickname, headimgurl, ...}
    """
    # Step1: 换 access_token + openid
    token_url = (
        "https://api.weixin.qq.com/sns/oauth2/access_token"
        f"?appid={settings.wechat_appid}"
        f"&secret={settings.wechat_appsecret}"
        f"&code={code}"
        f"&grant_type=authorization_code"
    )
    async with httpx.AsyncClient() as client:
        resp = await client.get(token_url, timeout=10)
        token_data = resp.json()

    if "openid" not in token_data:
        raise RuntimeError(f"OAuth 换取 token 失败: {token_data}")

    openid = token_data["openid"]
    access_token = token_data["access_token"]
    unionid = token_data.get("unionid", "")

    # Step2: 获取用户信息
    info_url = (
        f"https://api.weixin.qq.com/sns/userinfo"
        f"?access_token={access_token}"
        f"&openid={openid}"
        f"&lang=zh_CN"
    )
    async with httpx.AsyncClient() as client:
        resp = await client.get(info_url, timeout=10)
        info = resp.json()

    return {
        "openid": openid,
        "unionid": unionid or info.get("unionid", ""),
        "nickname": info.get("nickname", ""),
        "avatar": info.get("headimgurl", ""),
    }


# ── JWT ──────────────────────────────────────────────────────────────────────

def create_jwt_token(user_id: int, session_version: int) -> str:
    payload = {
        "sub": str(user_id),
        "sv": int(session_version),
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=settings.jwt_expire_hours),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_jwt_token(token: str) -> Optional[dict[str, int]]:
    """解码 JWT，返回 {user_id, session_version}；无效/过期返回 None"""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return {
            "user_id": int(payload["sub"]),
            "session_version": int(payload.get("sv", 0)),
        }
    except (JWTError, KeyError, ValueError):
        return None


# ── 微信消息签名验证 ──────────────────────────────────────────────────────────

def verify_wechat_signature(signature: str, timestamp: str, nonce: str) -> bool:
    """验证微信服务器推送的签名"""
    items = sorted([settings.wechat_token, timestamp, nonce])
    combined = "".join(items)
    expected = hashlib.sha1(combined.encode("utf-8")).hexdigest()
    return hmac.compare_digest(expected, signature)
