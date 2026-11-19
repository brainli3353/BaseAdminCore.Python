"""PBKDF2 密码哈希（对齐上游 Pbkdf2Helper：16B 盐 + 10 万轮 SHA256 + 32B 密钥）。"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os

ITERATIONS = 100_000
SALT_SIZE = 16
KEY_SIZE = 32


def hash_password(password: str) -> str:
    salt = os.urandom(SALT_SIZE)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS, KEY_SIZE)
    return f"{base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, stored: str | None) -> bool:
    parts = (stored or "").split("$")
    if len(parts) != 2:
        return False
    try:
        salt = base64.b64decode(parts[0])
        expected = base64.b64decode(parts[1])
    except (ValueError, TypeError):
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS, len(expected))
    return hmac.compare_digest(actual, expected)
