from fastapi import APIRouter

from qurankit_api.api.routes.health import router as health_router


router = APIRouter()
router.include_router(health_router)
