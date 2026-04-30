from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class ErrorPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    details: Any | None = None


class ErrorMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str


class ErrorEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error: ErrorPayload
    meta: ErrorMeta


COMMON_ERROR_RESPONSES = {
    422: {
        "model": ErrorEnvelope,
        "description": "Request validation failed.",
    },
    500: {
        "model": ErrorEnvelope,
        "description": "Unexpected server error.",
    },
}
