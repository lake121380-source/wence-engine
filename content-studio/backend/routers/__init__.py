"""
API 路由聚合入口。
"""

from fastapi import APIRouter

from routers.analyses import router as analyses_router
from routers.auth import router as auth_router
from routers.creators import router as creators_router
from routers.documents import router as documents_router
from routers.generations import router as generations_router
from routers.media_proxy import router as media_proxy_router
from routers.payment import router as payment_router
from routers.style_templates import router as style_templates_router
from routers.topics import router as topics_router
from routers.viewpoints import router as viewpoints_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(payment_router)
router.include_router(creators_router)
router.include_router(documents_router)
router.include_router(topics_router)
router.include_router(style_templates_router)
router.include_router(generations_router)
router.include_router(analyses_router)
router.include_router(viewpoints_router)
router.include_router(media_proxy_router)

try:
    from routers.tenant import router as tenant_router

    router.include_router(tenant_router)
except ImportError:
    pass

try:
    from routers.admin import router as admin_router

    router.include_router(admin_router)
except ImportError:
    pass
