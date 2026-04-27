from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

router = APIRouter()

_ALLOWED_IMAGE_HOSTS = {
    # Douyin CDN
    "p3-sign.douyinpic.com",
    "p6-sign.douyinpic.com",
    "p9-sign.douyinpic.com",
    "p26-sign.douyinpic.com",
    "p3-pc-sign.douyinpic.com",
    "p16-sign.douyinpic.com",
    "p1-sign.douyinpic.com",
    "p3.douyinpic.com",
    "p6.douyinpic.com",
    "p9.douyinpic.com",
    "p26.douyinpic.com",
    "p16.douyinpic.com",
    # Xiaohongshu CDN
    "sns-img-bd.xhscdn.com",
    "sns-img-hw.xhscdn.com",
    "sns-img-qc.xhscdn.com",
    "ci.xiaohongshu.com",
    "sns-webpic-qc.xhscdn.com",
    "sns-avatar-qc.xhscdn.com",
}


def _is_allowed_image_host(hostname: str) -> bool:
    if hostname in _ALLOWED_IMAGE_HOSTS:
        return True
    if hostname.endswith(".xhscdn.com"):
        return True
    if hostname.endswith(".douyinpic.com"):
        return True
    return False


# 允许的 URL 协议（仅 http/https）
_ALLOWED_SCHEMES = {"http", "https"}

# 允许的图片 Content-Type
_ALLOWED_CONTENT_TYPES = {
    "image/jpeg", "image/png", "image/webp",
    "image/gif", "image/avif", "image/svg+xml",
}


@router.get("/image-proxy")
async def image_proxy(url: str):
    parsed = urlparse(url)

    # 必须为 http/https，阻止 file://, gopher://, ftp:// 等协议
    if (parsed.scheme or "").lower() not in _ALLOWED_SCHEMES:
        raise HTTPException(status_code=400, detail="不支持该协议")

    if not _is_allowed_image_host(parsed.hostname or ""):
        raise HTTPException(status_code=403, detail="域名不在白名单中")

    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=False) as client:
            resp = await client.get(url, headers={"Referer": ""})
            if resp.status_code != 200:
                raise HTTPException(status_code=502, detail="上游图片不可用")

            # 将 content-type 限制在允许的图片类型，防止 HTML/JS 透传
            raw_ct = resp.headers.get("content-type", "")
            ct_base = raw_ct.split(";")[0].strip().lower()
            if ct_base not in _ALLOWED_CONTENT_TYPES:
                raise HTTPException(status_code=502, detail="上游返回非图片内容")

            return Response(
                content=resp.content,
                media_type=ct_base or "image/jpeg",
                headers={"Cache-Control": "public, max-age=86400"},
            )
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="图片请求超时")
    except Exception:
        # 不将内部异常信息露出到客户端
        raise HTTPException(status_code=502, detail="图片代理失败")
