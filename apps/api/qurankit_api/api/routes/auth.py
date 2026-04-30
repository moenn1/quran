from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from qurankit_api.core.auth import (
    authenticate_user,
    generate_password_salt,
    hash_password,
    issue_access_token,
    validate_email,
    validate_password,
)
from qurankit_api.core.config import Settings, get_app_settings
from qurankit_api.core.errors import ApiError
from qurankit_api.db.dependencies import get_db_session
from qurankit_api.models import User
from qurankit_api.schemas.auth import AuthResponse, AuthTokenPayload, LoginRequest, RegisterRequest, UserProfile
from qurankit_api.schemas.errors import COMMON_ERROR_RESPONSES, ErrorEnvelope


AUTH_ERROR_RESPONSES = {
    **COMMON_ERROR_RESPONSES,
    401: {
        "model": ErrorEnvelope,
        "description": "Authentication failed.",
    },
    409: {
        "model": ErrorEnvelope,
        "description": "The requested account already exists.",
    },
    503: {
        "model": ErrorEnvelope,
        "description": "Database access is unavailable for this API instance.",
    },
}

router = APIRouter(prefix="/auth", tags=["Auth"])


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _response_payload(user: User, token: str) -> AuthResponse:
    assert user.email is not None
    return AuthResponse(
        user=UserProfile(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            created_at=user.created_at,
        ),
        token=AuthTokenPayload(access_token=token),
    )


def _apply_auth_headers(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"


@router.post(
    "/register",
    response_model=AuthResponse,
    responses=AUTH_ERROR_RESPONSES,
    status_code=status.HTTP_201_CREATED,
    summary="Register a private QuranKit study account",
)
async def register(
    request: RegisterRequest,
    response: Response,
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
) -> AuthResponse:
    _apply_auth_headers(response)
    email = validate_email(request.email)
    validate_password(request.password, settings)

    existing = session.scalar(select(User).where(User.email == email))
    if existing is not None:
        raise ApiError(
            status_code=409,
            code="email_already_registered",
            message=f"An account for `{email}` already exists.",
            details={"email": email},
        )

    password_salt = generate_password_salt()
    user = User(
        email=email,
        display_name=_optional_text(request.display_name),
        password_salt=password_salt,
        password_hash_iterations=settings.auth_password_iterations,
        password_hash=hash_password(
            request.password,
            salt=password_salt,
            iterations=settings.auth_password_iterations,
        ),
    )
    session.add(user)
    session.flush()

    token = issue_access_token(
        session,
        user=user,
        metadata={"issued_for": "register"},
    )
    session.commit()
    session.refresh(user)
    return _response_payload(user, token)


@router.post(
    "/login",
    response_model=AuthResponse,
    responses=AUTH_ERROR_RESPONSES,
    summary="Exchange QuranKit credentials for a bearer token",
)
async def login(
    request: LoginRequest,
    response: Response,
    session: Session = Depends(get_db_session),
) -> AuthResponse:
    _apply_auth_headers(response)
    user = authenticate_user(
        session,
        email=request.email,
        password=request.password,
    )
    token = issue_access_token(
        session,
        user=user,
        metadata={"issued_for": "login"},
    )
    session.commit()
    session.refresh(user)
    return _response_payload(user, token)
