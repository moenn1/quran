from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from qurankit_api.schemas.errors import ErrorEnvelope, ErrorMeta, ErrorPayload


@dataclass(slots=True)
class ApiError(Exception):
    status_code: int
    code: str
    message: str
    details: Any | None = None


def build_error_envelope(
    request_id: str,
    code: str,
    message: str,
    details: Any | None = None,
) -> dict[str, Any]:
    return ErrorEnvelope(
        error=ErrorPayload(code=code, message=message, details=details),
        meta=ErrorMeta(request_id=request_id),
    ).model_dump(mode="json")


def get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def default_code(status_code: int) -> str:
    return {
        404: "not_found",
        405: "method_not_allowed",
        422: "validation_error",
        500: "internal_server_error",
    }.get(status_code, "http_error")


def default_message(status_code: int) -> str:
    return {
        404: "Route not found.",
        405: "Method not allowed.",
        422: "Request validation failed.",
        500: "Internal server error.",
    }.get(status_code, "Request failed.")


def default_details(request: Request) -> dict[str, str]:
    return {
        "method": request.method,
        "path": request.url.path,
    }


def error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: Any | None = None,
) -> JSONResponse:
    request_id = get_request_id(request)
    headers = {"X-Request-ID": request_id}
    if getattr(request.state, "private_no_store", False):
        headers["Cache-Control"] = "private, no-store"
        headers["Pragma"] = "no-cache"
    return JSONResponse(
        status_code=status_code,
        content=build_error_envelope(
            request_id=request_id,
            code=code,
            message=message,
            details=details,
        ),
        headers=headers,
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def handle_api_error(request: Request, exc: ApiError) -> JSONResponse:
        return error_response(
            request=request,
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            details=exc.details,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return error_response(
            request=request,
            status_code=422,
            code=default_code(422),
            message=default_message(422),
            details={"errors": exc.errors()},
        )

    @app.exception_handler(HTTPException)
    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        request: Request,
        exc: HTTPException | StarletteHTTPException,
    ) -> JSONResponse:
        message = default_message(exc.status_code)
        details: Any | None = default_details(request)

        if isinstance(exc.detail, str) and exc.detail not in {"Not Found", "Method Not Allowed"}:
            message = exc.detail
        elif exc.detail not in {None, "Not Found", "Method Not Allowed"}:
            details = exc.detail

        return error_response(
            request=request,
            status_code=exc.status_code,
            code=default_code(exc.status_code),
            message=message,
            details=details,
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(
        request: Request,
        _exc: Exception,
    ) -> JSONResponse:
        return error_response(
            request=request,
            status_code=500,
            code=default_code(500),
            message=default_message(500),
            details=None,
        )
