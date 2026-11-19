/** 统一响应模型(与后端 Core/Models/ApiResult.cs 逐字对齐,JSON 为 camelCase)。
 * Code=0 成功;非 0 业务失败(HTTP 状态码与业务码同时表达,如 401+code)。 */
export interface ApiResult<T = unknown> {
	code: number
	msg: string
	/** 稳定错误码(批 AQ):客户端按此编程判断;成功与存量失败为空 */
	errCode?: string
	data: T
}

/** 统一分页结果(与后端 PageResult<T> 对齐)。 */
export interface PageResult<T> {
	total: number
	list: T[]
}

/** 菜单树节点(与 MenuOutput 对齐)。type: 1 目录 / 2 菜单 / 3 按钮(导航树已剔按钮);status: 0 启用 / 1 停用(批 CH G28);
 * isKeepAlive: 0 不缓存(切回页签重新挂载/重取数) / 1 缓存(keep-alive 保留组件状态)。 */
export interface MenuNode {
	/** G33:后端 long id 经 JSON 出口为 string(读侧兼容 number,故并集) */
	id: number | string
	pid: number | string
	name: string | null
	title: string | null
	type: number
	permission: string | null
	orderNo: number
	icon: string | null
	status: number
	isKeepAlive: number
	children: MenuNode[]
}

/** 一阶段登录成功响应(LoginOutput)。 */
export interface LoginChallenge {
	challengeId: string
	bindRequired: boolean
	otpauthUri: string | null
	secret: string | null
}

/** 二阶段成功 / 全局开关关闭时密码直登的令牌结果(与后端 LoginResult 对齐:Success 时 Token 非空,
 * data 形状 = token 字符串,经响应头 X-Refresh-Token / X-Password-Expired 透传)。 */
export interface LoginTokenResult {
	accessToken: string
	refreshToken: string | null
	passwordExpired: boolean
}

/** 当前用户信息(/api/auth/me)。 */
export interface UserInfo {
	/** G33:后端 long id 经 JSON 出口为 string */
	userId: number | string
	account: string
	realName: string
	/** 账号类型:999 超管(契约 §2 穿透)/ 777 普通 */
	accountType: number
	/** 按钮权限键集合(如 "sysUser/add");驱动 v-perm 显隐(与后端 [MenuPerm] 同一份数据)。 */
	permissions: string[]
}
