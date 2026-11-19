/** 日志审计 API(契约 /api/sysLogOp、/api/sysLogLogin、/api/sysLogEx、/api/sysLogHttp 四控制器合一)。 */
import service from '../request'
import type { PageResult } from '@/types/api'

/* ── 操作日志 ─────────────────────────────── */
export interface SysLogOpOutput {
	id: number | string
	controllerName: string | null
	actionName: string | null
	httpMethod: string | null
	remoteIp: string | null
	/** int,毫秒 */
	elapsedMs: number
	account: string | null
	success: boolean
	createTime: string | null
}

export interface LogOpQuery {
	/** 精确 */
	account?: string | null
	/** 模糊 */
	controllerName?: string | null
	success?: boolean | null
	startTime?: string | null
	endTime?: string | null
	pageIndex?: number
	pageSize?: number
	orderBy?: string
	desc?: boolean
}

export const pageLogOp = (q: LogOpQuery) =>
	service.get('/api/sysLogOp/page', { params: q }) as Promise<PageResult<SysLogOpOutput>>

/** 详情=全字段(含两大字段:请求参数/返回结果;批 AZ 参照口径,列表不载大字段)。 */
export interface SysLogOpDetailOutput extends SysLogOpOutput {
	requestParam: string | null
	returnResult: string | null
}

export const logOpDetail = (id: number | string) =>
	service.get(`/api/sysLogOp/detail?id=${id}`) as Promise<SysLogOpDetailOutput>

/* ── 登录日志 ─────────────────────────────── */
export interface SysLogLoginOutput {
	id: number | string
	account: string | null
	remoteAddr: string | null
	browser: string | null
	os: string | null
	/** true 成功 / false 失败 */
	status: boolean
	message: string | null
	loginType: string | null
	createTime: string | null
}

export interface LogLoginQuery {
	/** 精确 */
	account?: string | null
	/** 三态:undefined/null=不过滤 */
	status?: boolean | null
	startTime?: string | null
	endTime?: string | null
	pageIndex?: number
	pageSize?: number
	orderBy?: string
	desc?: boolean
	/** 登录类型精确过滤:login=登录 / logout=登出(批 UX,可空=不过滤) */
	loginType?: string | null
}

export const pageLogLogin = (q: LogLoginQuery) =>
	service.get('/api/sysLogLogin/page', { params: q }) as Promise<PageResult<SysLogLoginOutput>>

/* ── 异常日志 ─────────────────────────────── */
export interface SysLogExOutput {
	id: number | string
	controllerName: string | null
	actionName: string | null
	httpMethod: string | null
	requestUrl: string | null
	remoteIp: string | null
	traceId: string | null
	threadId: number | null
	account: string | null
	realName: string | null
	logLevel: string | null
	createTime: string | null
}

/** 详情=全字段(含大字段)。 */
export interface SysLogExDetailOutput extends SysLogExOutput {
	requestParam: string | null
	returnResult: string | null
	exception: string | null
}

export interface LogExQuery {
	/** 精确 */
	account?: string | null
	/** 模糊 */
	controllerName?: string | null
	/** 精确 */
	remoteIp?: string | null
	startTime?: string | null
	endTime?: string | null
	pageIndex?: number
	pageSize?: number
	orderBy?: string
	desc?: boolean
	/** 日志级别精确过滤(枚举名串,批 UX,可空=不过滤) */
	logLevel?: string | null
}

export const pageLogEx = (q: LogExQuery) =>
	service.get('/api/sysLogEx/page', { params: q }) as Promise<PageResult<SysLogExOutput>>

export const logExDetail = (id: number | string) =>
	service.get(`/api/sysLogEx/detail?id=${id}`) as Promise<SysLogExDetailOutput>

/* ── Http 出站日志 ─────────────────────────────── */
export interface SysLogHttpOutput {
	id: number | string
	httpMethod: string | null
	requestUrl: string | null
	/** 出站响应状态码;未拿到响应(连接失败/超时)为 null */
	statusCode: number | null
	/** 耗时(毫秒);请求未完成(异常中断)为 null(与实体/SysLogOp 同口径字段名 ElapsedMs) */
	elapsedMs: number | null
	account: string | null
	realName: string | null
	traceId: string | null
	/** true=该次出站带异常(列表状态列显红) */
	hasException: boolean
	createTime: string | null
}

/** 详情=含大字段(请求头/请求体/响应体/异常全文)。 */
export interface SysLogHttpDetailOutput {
	id: number | string
	httpMethod: string | null
	requestUrl: string | null
	statusCode: number | null
	/** 耗时(毫秒);同列表字段名 */
	elapsedMs: number | null
	account: string | null
	realName: string | null
	traceId: string | null
	requestHeaders: string | null
	requestBody: string | null
	responseBody: string | null
	exception: string | null
	createTime: string | null
}

export interface LogHttpQuery {
	/** 精确 */
	account?: string | null
	/** 模糊(Contains) */
	url?: string | null
	/** 精确 */
	httpMethod?: string | null
	/** 精确 */
	statusCode?: number | null
	startTime?: string | null
	endTime?: string | null
	pageIndex?: number
	pageSize?: number
	orderBy?: string
	desc?: boolean
}

export const pageLogHttp = (q: LogHttpQuery) =>
	service.get('/api/sysLogHttp/page', { params: q }) as Promise<PageResult<SysLogHttpOutput>>

export const logHttpDetail = (id: number | string) =>
	service.get(`/api/sysLogHttp/detail?id=${id}`) as Promise<SysLogHttpDetailOutput>

/* ── 差异日志(批 CE,闭环 CC 批 D2 孤儿键:端点/种子在库,本批补 UI) ─────────────────────────── */
/** 列表=排除四大字段(BeforeData/AfterData/Sql/Parameters;批 X 5.4 口径,与异常日志列表同义)。 */
export interface SysLogDiffOutput {
	id: number | string
	/** 业务对象(手动传入;未传=表名) */
	businessData: string | null
	/** INSERT/UPDATE/DELETE */
	diffType: string | null
	/** 耗时(毫秒) */
	elapsed: number | null
	createUserName: string | null
	createTime: string | null
}

/** 详情=全字段(含四大字段;参照 logdiff 详情口径)。 */
export interface SysLogDiffDetailOutput extends SysLogDiffOutput {
	beforeData: string | null
	afterData: string | null
	sql: string | null
	parameters: string | null
}

export interface LogDiffQuery {
	startTime?: string | null
	endTime?: string | null
	pageIndex?: number
	pageSize?: number
	orderBy?: string
	desc?: boolean
}

export const pageLogDiff = (q: LogDiffQuery) =>
	service.get('/api/sysLogDiff/page', { params: q }) as Promise<PageResult<SysLogDiffOutput>>

export const logDiffDetail = (id: number | string) =>
	service.get('/api/sysLogDiff/detail', { params: { id } }) as Promise<SysLogDiffDetailOutput>
