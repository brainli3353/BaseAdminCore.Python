from __future__ import annotations

import json
from dataclasses import asdict, dataclass


@dataclass
class LoginOtpChallenge:
    user_id: int
    account: str
    setup_secret: str
    bind_required: bool
    fail_times: int = 0

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, raw: str) -> LoginOtpChallenge:
        return cls(**json.loads(raw))
