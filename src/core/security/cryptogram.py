"""AES-256-CBC 加解密（对齐上游 CryptogramHelper：Base64(IV||密文)）。"""

from __future__ import annotations

import base64
import hashlib
import os

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from src.core.config import get_settings


def _key() -> bytes:
    raw = get_settings().cryptogram.key or "CHANGE_ME__local_dev_key"
    return hashlib.sha256(raw.encode("utf-8")).digest()


def encrypt(plain: str) -> str:
    iv = os.urandom(16)
    padder = padding.PKCS7(128).padder()
    padded = padder.update(plain.encode("utf-8")) + padder.finalize()
    cipher = Cipher(algorithms.AES(_key()), modes.CBC(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()
    return base64.b64encode(iv + ciphertext).decode()


def decrypt(cipher_text: str) -> str:
    raw = base64.b64decode(cipher_text)
    iv, ciphertext = raw[:16], raw[16:]
    cipher = Cipher(algorithms.AES(_key()), modes.CBC(iv))
    decryptor = cipher.decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    return (unpadder.update(padded) + unpadder.finalize()).decode("utf-8")
