"""TOTP 三态校验 + 防重放（对齐上游 OtpService）。"""

from __future__ import annotations

import time

import pyotp

INVALID = "invalid"
REUSED = "reused"
OK = "ok"

WINDOW = 1
INTERVAL = 30


def generate_setup_secret() -> str:
    return pyotp.random_base32()


def _match_step(code: str, secret: str) -> int | None:
    code = code.strip()
    if not code:
        return None
    totp = pyotp.TOTP(secret, interval=INTERVAL)
    current_step = int(time.time() // INTERVAL)
    for offset in range(-WINDOW, WINDOW + 1):
        step = current_step + offset
        if totp.at(step * INTERVAL) == code:
            return step
    return None


def validate(code: str, secret: str, last_used_time_step: int | None) -> tuple[str, int | None]:
    if not secret or not code:
        return INVALID, None
    try:
        step = _match_step(code, secret)
    except Exception:
        return INVALID, None
    if step is None:
        return INVALID, None
    if last_used_time_step is not None and step <= last_used_time_step:
        return REUSED, None
    return OK, step
