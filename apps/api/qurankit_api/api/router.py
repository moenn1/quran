from fastapi import APIRouter

from qurankit_api.api.routes.browse import router as browse_router
from qurankit_api.api.routes.health import router as health_router
from qurankit_api.api.routes.search import router as search_router


router = APIRouter()
router.include_router(health_router)
router.include_router(browse_router)
router.include_router(search_router)
