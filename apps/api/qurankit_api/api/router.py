from fastapi import APIRouter

from qurankit_api.api.routes.auth import router as auth_router
from qurankit_api.api.routes.browse import router as browse_router
from qurankit_api.api.routes.health import router as health_router
from qurankit_api.api.routes.search import router as search_router
from qurankit_api.api.routes.study import router as study_router


router = APIRouter()
router.include_router(health_router)
router.include_router(auth_router)
router.include_router(browse_router)
router.include_router(search_router)
router.include_router(study_router)
