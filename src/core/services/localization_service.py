from __future__ import annotations

import json
from pathlib import Path

LANG_DIR = Path(__file__).resolve().parent.parent / "localization"

CULTURES = [
    {"code": "zh-CN", "name": "简体中文", "isDefault": True},
    {"code": "en", "name": "English", "isDefault": False},
]


class LocalizationService:
    def get_cultures(self) -> list[dict]:
        return CULTURES

    def get_language(self, culture: str) -> dict:
        path = LANG_DIR / f"Lang.{culture}.json"
        if not path.is_file():
            path = LANG_DIR / "Lang.zh-CN.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def get(self, key: str, culture: str) -> str:
        data = self.get_language(culture)
        for part in key.split("."):
            data = data.get(part, {}) if isinstance(data, dict) else {}
        return data if isinstance(data, str) else key
