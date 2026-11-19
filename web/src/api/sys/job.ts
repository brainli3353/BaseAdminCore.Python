/** 定时任务 API(契约 /api/sysJob/*)。 */
import service from '../request'
import type { PageResult } from '@/types/api'

export interface JobDetailOutput {
	id: number | string
	jobName: string | null
	/** 间隔(秒,正整数) */
	interval: number
	enabled: boolean
	lastRunTime: string | null
	remark: string | null
	createTime: string | null
}

export interface JobQuery {
	/** 后端参数名 name,模糊匹配 jobName */
	name?: string | null
	pageIndex?: number
	pageSize?: number
	orderBy?: string
	desc?: boolean
	/** 启用状态精确过滤(批 UX,可空=不过滤) */
	enabled?: boolean | null
}

export const pageJob = (q: JobQuery) =>
	service.get('/api/sysJob/page', { params: q }) as Promise<PageResult<JobDetailOutput>>

export const addJob = (d: { jobName: string; interval: number; remark?: string }) =>
	service.post('/api/sysJob/add', d) as Promise<number | string>

export const updateJob = (d: { id: number | string; interval?: number; enabled?: boolean; remark?: string }) =>
	service.post('/api/sysJob/update', d) as Promise<null>

export const enableJob = (id: number | string) =>
	service.post(`/api/sysJob/enable?id=${id}`) as Promise<null>

export const disableJob = (id: number | string) =>
	service.post(`/api/sysJob/disable?id=${id}`) as Promise<null>

export const runJobNow = (id: number | string) =>
	service.post(`/api/sysJob/runNow?id=${id}`) as Promise<null>

/* ── 执行记录(2026-09-30;契约 GET /api/sysJob/logPage) ────────────────────────────── */
/** 执行日志行 {id, jobName, trigger, triggeredAt, durationMs, success, errorMsg, instanceId, nodeTag}。 */
export interface JobLogOutput {
	id: number | string
	jobName: string | null
	/** 触发方式:scheduled=定时 / manual=手动 */
	trigger: string | null
	/** 执行开始时刻(ISO 字符串) */
	triggeredAt: string | null
	/** 执行耗时(毫秒) */
	durationMs: number
	/** 执行体是否正常完成(false=抛异常,errorMsg 有值) */
	success: boolean
	errorMsg: string | null
	instanceId: string | null
	nodeTag: string | null
}

export interface JobLogQuery {
	/** 任务名(精确) */
	jobName?: string | null
	pageIndex?: number
	pageSize?: number
	orderBy?: string
	desc?: boolean
}

/** 执行日志分页(最新在前)。 */
export const pageJobLog = (q: JobLogQuery) =>
	service.get('/api/sysJob/logPage', { params: q }) as Promise<PageResult<JobLogOutput>>

/* ── 集群视图(只读:实例节点 + 运行中任务;契约 GET /api/sysJob/nodes) ─────────────── */
/**
 * 实例节点行 {instanceId, nodeTag, startedAt, lastBeat, isAlive, isSelf}。
 * 僵尸节点(最后心跳超 90 秒)后端已过滤,故 isAlive 恒为 true;
 * isSelf 标注该行是否本实例(便于运维对照)。
 */
export interface JobNodeOutput {
	/** 实例 Id(长串) */
	instanceId: string
	/** 实例标签(部署时指定,便于区分机器) */
	nodeTag: string
	startedAt: string | null
	lastBeat: string | null
	isAlive: boolean
	isSelf: boolean
}

/** 运行中任务行 {jobName, instanceId, nodeTag, startedAt, trigger}(trigger=scheduled/manual)。 */
export interface JobRunningOutput {
	jobName: string
	instanceId: string
	nodeTag: string | null
	startedAt: string | null
	/** 触发方式:scheduled=定时 / manual=手动 */
	trigger: string | null
}

/** 集群视图 {nodes, running}。 */
export interface JobClusterOutput {
	nodes: JobNodeOutput[]
	running: JobRunningOutput[]
}

/** 拉集群视图(只读;失败交全局拦截器提示)。 */
export const getJobNodes = () =>
	service.get('/api/sysJob/nodes') as Promise<JobClusterOutput>
