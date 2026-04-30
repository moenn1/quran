from fastapi import APIRouter, Depends

from qurankit_api.core.config import Settings, get_app_settings
from qurankit_api.schemas.errors import COMMON_ERROR_RESPONSES
from qurankit_api.schemas.health import HealthStatus


router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthStatus,
    responses=COMMON_ERROR_RESPONSES,
    summary="Read API health status",
)
async def read_health_status(
    settings: Settings = Depends(get_app_settings),
) -> HealthStatus:
    return HealthStatus(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        api_prefix=settings.api_v1_prefix,
        database_configured=bool(settings.database_url),
        privacy_mode=settings.privacy_mode,
        source_attribution_required=settings.source_attribution_required,
    )
