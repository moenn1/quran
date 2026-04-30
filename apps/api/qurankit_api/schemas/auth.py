from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    password: str
    display_name: str | None = None


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    password: str


class UserProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    email: str
    display_name: str | None = None
    created_at: datetime


class AuthTokenPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    access_token: str
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user: UserProfile
    token: AuthTokenPayload
