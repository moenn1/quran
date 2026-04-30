from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from qurankit_api.core.config import Settings
from qurankit_api.core.errors import ApiError
from qurankit_api.db.base import utcnow
from qurankit_api.models import AuthToken, User


TOKEN_PREFIX = "qkt_"
TOKEN_PREFIX_LENGTH = 12


@dataclass(frozen=True, slots=True)
class AuthenticatedIdentity:
    user: User
    auth_token: AuthToken


def normalize_email(value: str) -> str:
    return value.strip().casefold()


def validate_email(value: str) -> str:
    normalized = normalize_email(value)
    if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
        raise ApiError(
            status_code=422,
            code="invalid_email",
            message="Email must look like `name@example.com`.",
            details={"field": "email"},
        )
    return normalized


def validate_password(value: str, settings: Settings) -> str:
    if len(value) < settings.auth_min_password_length:
        raise ApiError(
            status_code=422,
            code="weak_password",
            message=(
                "Password must be at least "
                f"{settings.auth_min_password_length} characters long."
            ),
            details={
                "field": "password",
                "minimum_length": settings.auth_min_password_length,
            },
        )
    return value


def _urlsafe_b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def generate_password_salt() -> str:
    return _urlsafe_b64(secrets.token_bytes(16))


def hash_password(
    password: str,
    *,
    salt: str,
    iterations: int,
) -> str:
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    )
    return _urlsafe_b64(digest)


def verify_password(
    password: str,
    *,
    expected_hash: str | None,
    salt: str | None,
    iterations: int | None,
) -> bool:
    if not expected_hash or not salt or not iterations:
        return False
    candidate = hash_password(password, salt=salt, iterations=iterations)
    return hmac.compare_digest(candidate, expected_hash)


def hash_access_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def issue_access_token(
    session: Session,
    *,
    user: User,
    metadata: dict[str, Any] | None = None,
) -> str:
    token = TOKEN_PREFIX + secrets.token_urlsafe(32)
    auth_token = AuthToken(
        user_id=user.id,
        token_hash=hash_access_token(token),
        token_prefix=token[:TOKEN_PREFIX_LENGTH],
        metadata_json=metadata,
    )
    session.add(auth_token)
    session.flush()
    return token


def resolve_access_token(session: Session, token: str) -> AuthenticatedIdentity:
    token_hash = hash_access_token(token)
    row = session.execute(
        select(AuthToken, User)
        .join(User, AuthToken.user_id == User.id)
        .where(
            AuthToken.token_hash == token_hash,
            AuthToken.revoked_at.is_(None),
        ),
    ).one_or_none()

    if row is None:
        raise ApiError(
            status_code=401,
            code="invalid_token",
            message="Bearer token is invalid or has been revoked.",
            details=None,
        )

    auth_token, user = row
    if auth_token.expires_at is not None and auth_token.expires_at <= utcnow():
        raise ApiError(
            status_code=401,
            code="invalid_token",
            message="Bearer token is invalid or has been revoked.",
            details=None,
        )
    auth_token.last_used_at = utcnow()
    return AuthenticatedIdentity(user=user, auth_token=auth_token)


def authenticate_user(
    session: Session,
    *,
    email: str,
    password: str,
) -> User:
    user = session.scalar(select(User).where(User.email == normalize_email(email)))
    if user is None or not verify_password(
        password,
        expected_hash=user.password_hash,
        salt=user.password_salt,
        iterations=user.password_hash_iterations,
    ):
        raise ApiError(
            status_code=401,
            code="invalid_credentials",
            message="Email or password is incorrect.",
            details=None,
        )
    return user
