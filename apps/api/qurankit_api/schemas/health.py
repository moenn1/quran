from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class HealthStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"]
    service: str
    version: str
    environment: str
    api_prefix: str
    database_configured: bool
    privacy_mode: str
    source_attribution_required: bool


class ServiceInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service: str
    version: str
    environment: str
    api_prefix: str
    docs_url: str
    openapi_url: str
    privacy_mode: str
    source_attribution_required: bool
    semantic_search_disclaimer: str
