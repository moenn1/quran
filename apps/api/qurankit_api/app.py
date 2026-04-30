from __future__ import annotations

from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import Depends, FastAPI, Request

from qurankit_api.api.router import router as api_router
from qurankit_api.core.config import Settings, get_app_settings, get_settings
from qurankit_api.core.errors import register_exception_handlers
from qurankit_api.db import create_engine_from_url, create_session_factory
from qurankit_api.schemas.errors import COMMON_ERROR_RESPONSES
from qurankit_api.schemas.health import ServiceInfo


def build_openapi_description(settings: Settings) -> str:
    return (
        "QuranKit is a source-transparent Quran API scaffold.\n\n"
        "- Quran text must preserve upstream source bytes during ingestion.\n"
        "- Source attribution is required for Quran text, translations, and sourced metadata.\n"
        "- Bookmarks, notes, and reading progress are private by default.\n"
        f"- {settings.semantic_search_disclaimer}"
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        engine = None
        session_factory = None

        if app_settings.database_url:
            engine = create_engine_from_url(app_settings.database_url)
            session_factory = create_session_factory(engine)

        app.state.engine = engine
        app.state.session_factory = session_factory

        try:
            yield
        finally:
            if engine is not None:
                engine.dispose()

    app = FastAPI(
        title=app_settings.app_name,
        version=app_settings.app_version,
        description=build_openapi_description(app_settings),
        lifespan=lifespan,
        contact={
            "name": "Mohamed En-Nassibi",
            "email": app_settings.support_email,
        },
        docs_url=app_settings.docs_url,
        openapi_url=app_settings.openapi_url,
        redoc_url=app_settings.redoc_url,
        openapi_tags=[
            {
                "name": "Meta",
                "description": "Service discovery and documentation endpoints.",
            },
            {
                "name": "Health",
                "description": "Lightweight API availability checks.",
            },
            {
                "name": "Quran Browse",
                "description": "Read Quran browse data from the normalized QuranKit database.",
            },
        ],
    )
    app.state.settings = app_settings

    @app.middleware("http")
    async def attach_request_id(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    register_exception_handlers(app)
    app.include_router(api_router, prefix=app_settings.api_v1_prefix)

    @app.get(
        "/",
        response_model=ServiceInfo,
        responses=COMMON_ERROR_RESPONSES,
        summary="Read service metadata",
        tags=["Meta"],
    )
    async def read_service_info(
        settings: Settings = Depends(get_app_settings),
    ) -> ServiceInfo:
        return ServiceInfo(
            service=settings.app_name,
            version=settings.app_version,
            environment=settings.environment,
            api_prefix=settings.api_v1_prefix,
            docs_url=settings.docs_url or "",
            openapi_url=settings.openapi_url,
            privacy_mode=settings.privacy_mode,
            source_attribution_required=settings.source_attribution_required,
            semantic_search_disclaimer=settings.semantic_search_disclaimer,
        )

    return app
