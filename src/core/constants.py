"""全局常量：缓存键、多库标识、Claim 名、错误码。"""

from __future__ import annotations


class CacheConst:
    KeyDict = "sys_dict:"
    KeyUserApiPerm = "sys_user_apio:"  # 用户按钮权限有效集
    KeyUserOrg = "sys_user_org:"  # 用户机构范围集
    KeyRoleMaxDataScope = "sys_role_scope:"  # 角色数据范围
    KeyJobLock = "sys_job_lock:"
    KeyUserToken = "sys_user_token:"  # TokenVersion 快路径
    KeyPasswordError = "sys_password_error:"
    KeyOtpError = "sys_otp_error:"
    KeyOpenAccess = "sys_open_access:"
    KeyOpenAccessNonce = "sys_open_access_nonce:"
    KeyUserOnline = "sys_user_online"
    GroupOnline = "GROUP_ONLINE_"
    OnlineUserTtl = 24 * 3600
    KeyColumnCustom = "sys_column_custom:"
    KeyConfig = "sys_config:"
    KeyRoleTable = "sys_role_table:"
    KeyRoleTableManaged = "sys_role_table:__managed"
    KeyJobNode = "sys_job_node:"
    KeyJobRunning = "sys_job_running:"
    KeyQueuePrefix = "queue:"
    KeyStartupSchema = "sys_startup_schema"
    KeyWorkerId = "sys_worker_id:"
    KeySqlSugarCache = "sys_sqlSugar:"


class DbConst:
    MainConfigId = "main"
    LogConfigId = "log"
    DefaultTenantId = 1


class ClaimsConst:
    UserId = "uid"
    Account = "acct"
    RealName = "rn"
    OrgId = "org"
    TenantId = "tid"
    TokenVersion = "tv"
    RoleIds = "rids"
    IsSuperAdmin = "is_super"
    SuperAdminTenantId = 0


class ErrorCodes:
    Success = 0
    Fail = 1
    ParamInvalid = 400
    Unauthorized = 401
    Forbidden = 403
    NotFound = 404
    Conflict = 409
    TooManyRequests = 429
    ServerError = 500


class ErrorKeys:
    AuthLoginFailed = "auth.login_failed"
    AuthTooManyAttempts = "auth.too_many_attempts"
    AuthAccountDisabled = "auth.account_disabled"
    AuthChallengeExpired = "auth.challenge_expired"
    AuthOtpVerifyFailed = "auth.otp_verify_failed"
    AuthOtpReused = "auth.otp_reused"
    TenantNotFound = "tenant.not_found"
    TenantDisabled = "tenant.disabled"
    TenantExpired = "tenant.expired"
    NoticeNotFound = "notice.not_found"
    OpenAccessNotFound = "open_access.not_found"
    UserNotFound = "user.not_found"
    UserAccountExists = "user.account_exists"
    UserAccountDisabled = "user.account_disabled"
    UserOldPasswordWrong = "user.old_password_wrong"
    UserPasswordSameAsHistory = "user.password_same_as_history"
    UserPasswordStrengthInvalid = "user.password_strength_invalid"
    MenuNotFound = "menu.not_found"
    MenuNameExists = "menu.name_exists"
    MenuParentIsButton = "menu.parent_is_button"
    MenuDuplicate = "menu.duplicate"
    RoleNotFound = "role.not_found"
    RoleCodeExists = "role.code_exists"
    RoleBuiltInForbidden = "role.built_in_forbidden"
    RoleMenuNotFound = "role.menu_not_found"
    OrgNotFound = "org.not_found"
    OrgDuplicate = "org.duplicate"
    OrgParentSelf = "org.parent_self"
    OrgParentDescendant = "org.parent_descendant"
    OrgTopForbidden = "org.top_forbidden"
    OrgOutOfScope = "org.out_of_scope"
    OrgParentOutOfScope = "org.parent_out_of_scope"
    OrgTopMoveForbidden = "org.top_move_forbidden"
    PosNotFound = "pos.not_found"
    PosCodeExists = "pos.code_exists"
    DictTypeNotFound = "dict.type_not_found"
    DictDataNotFound = "dict.data_not_found"
    ConfigNotFound = "config.not_found"
    ConfigCodeExists = "config.code_exists"
    FileNotFound = "file.not_found"
    FileForbidden = "file.forbidden"
    CommonNotFound = "common.not_found"
    CommonUnauthorized = "common.unauthorized"
    CommonForbidden = "common.forbidden"
    CommonParamInvalid = "common.param_invalid"
    CommonServerError = "common.server_error"
    CommonConflict = "common.conflict"
