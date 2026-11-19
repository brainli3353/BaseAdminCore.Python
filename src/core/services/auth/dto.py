from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, Field


class LoginInput(BaseModel):
    account: str | None = None
    password: str | None = None


class LoginOtpInput(BaseModel):
    model_config = {"populate_by_name": True}

    challenge_id: str | None = Field(default=None, alias="challengeId")
    code: str | None = None


@dataclass
class LoginOutput:
    challenge_id: str
    bind_required: bool
    otpauth_uri: str | None = None
    secret: str | None = None


@dataclass
class LoginResult:
    success: bool
    error: str | None = None
    data: LoginOutput | None = None
    token: str | None = None
    password_expired: bool = False
    refresh_token: str | None = None
    error_code: str | None = None


@dataclass
class UserTokenState:
    token_version: int
    is_disabled: bool
    tenant_valid: bool
