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


@router.get("/image-proxy")
async def image_proxy(url: str):
    parsed = urlparse(url)
    if not _is_allowed_image_host(parsed.hostname or ""):
        raise HTTPException(status_code=403, detail="域名不在白名单中")

    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(url, headers={"Referer": ""})
            if resp.status_code != 200:
                raise HTTPException(status_code=502, detail="上游返回非200")
            content_type = resp.headers.get("content-type", "image/jpeg")
            return Response(
                content=resp.content,
                media_type=content_type,
                headers={"Cache-Control": "public, max-age=86400"},
            )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="图片请求超时")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
