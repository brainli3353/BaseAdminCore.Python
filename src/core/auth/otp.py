"""OTP（TOTP，pyotp）——对齐上游 Otp.NET 两阶段登录。"""

from __future__ import annotations

import pyotp


class OtpValidateResult:
    INVALID = "invalid"
    REUSED = "reused"
    OK = "ok"


def generate_secret() -> str:
    return pyotp.random_base32()


def verify(secret: str, code: str, window: int = 1) -> bool:
    if not secret or not code:
        return False
    return pyotp.TOTP(secret).verify(code.strip(), valid_window=window)


def provisioning_uri(secret: str, account: str, issuer: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=account, issuer_name=issuer)
