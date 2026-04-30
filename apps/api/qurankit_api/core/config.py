from __future__ import annotations

from functools import lru_cache
from typing import cast

from fastapi import Request
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="QURANKIT_",
        extra="ignore",
    )

    app_name: str = "QuranKit API"
    app_version: str = "0.1.0"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    docs_url: str | None = "/docs"
    openapi_url: str = "/openapi.json"
    redoc_url: str | None = None
    privacy_mode: str = "private-by-default"
    source_attribution_required: bool = True
    semantic_search_disclaimer: str = (
        "Related passages are ranked by textual similarity only. They are not tafsir, "
        "fatwa, or religious rulings."
    )
    database_url: str | None = None
    support_email: str = "mohamed.enn2001@gmail.com"
    auth_min_password_length: int = 8
    auth_password_iterations: int = 310_000


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def get_app_settings(request: Request) -> Settings:
    return cast(Settings, request.app.state.settings)
