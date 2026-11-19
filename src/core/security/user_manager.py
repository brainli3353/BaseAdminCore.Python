"""当前登录用户门面（对齐上游 UserManager，单点判定超管/身份字段）。"""

from __future__ import annotations

from src.core.db.context import UserContext, get_current_user

SUPER_ADMIN_ACCOUNT_TYPE = 999


class UserManager:
    @property
    def user(self) -> UserContext | None:
        return get_current_user()

    @property
    def is_authenticated(self) -> bool:
        return self.user is not None

    @property
    def user_id(self) -> int | None:
        return self.user.user_id if self.user else None

    @property
    def account(self) -> str | None:
        return self.user.account if self.user else None

    @property
    def real_name(self) -> str | None:
        return self.user.real_name if self.user else None

    @property
    def org_id(self) -> int | None:
        return self.user.org_id if self.user else None

    @property
    def tenant_id(self) -> int | None:
        return self.user.tenant_id if self.user else None

    @property
    def role_ids(self) -> tuple[int, ...]:
        return self.user.role_ids if self.user else ()

    @property
    def is_super_admin(self) -> bool:
        return bool(self.user and self.user.is_super_admin)
