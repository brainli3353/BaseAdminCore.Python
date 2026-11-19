/** 打印模板 API(契约 /api/sysPrint/*)。
 * 本仓口径:后端只存模板不渲染(前端不做设计器,预览/打印由业务侧或后续按需实现);
 * 模板全文 template 是大字段,仅 detail 返回,列表不含。 */
import service from '../request'
import type { PageResult } from '@/types/api'

/** 列表/详情共用业务字段(与后端 SysPrintOutput 逐字对齐,JSON camelCase)。 */
export interface SysPrintOutput {
	id: number | string
	name: string
	/** 1 浏览器打印 / 2 客户端打印(仅存储语义,本仓后端不渲染) */
	printType: number
	/** 1 启用 / 2 停用 */
	status: number
	orderNo: number
	remark: string | null
	createTime: string | null
}

/** 详情 = 列表字段 + 模板全文大字段。 */
export interface SysPrintDetailOutput extends SysPrintOutput {
	template: string
}

export interface SysPrintQuery {
	/** 名称模糊 */
	name?: string | null
	pageIndex?: number
	pageSize?: number
	orderBy?: string
	desc?: boolean
	/** 创建时间范围起(批 UX B1d,CreateTime 闭区间;可空=不过滤) */
	startDate?: string | null
	/** 创建时间范围止(批 UX B1d,CreateTime 闭区间;可空=不过滤) */
	endDate?: string | null
}

/** 新增入参;状态随契约字段一起提交(后端输入模型含 status 才生效,未含则服务端默认启用)。 */
export interface SysPrintAddInput {
	name: string
	template: string
	printType: number
	status?: number
	orderNo?: number
	remark?: string
}

/** 更新入参(后端为部分更新:不传=不改;页面按 detail 拉全字段后整体提交)。 */
export interface SysPrintUpdateInput {
	id: number | string
	name?: string
	template?: string
	printType?: number
	status?: number
	orderNo?: number
	remark?: string
}

export const pagePrint = (q: SysPrintQuery) =>
	service.get('/api/sysPrint/page', { params: q }) as Promise<PageResult<SysPrintOutput>>

/** 详情(含 template 全文)。 */
export const printDetail = (id: number | string) =>
	service.get(`/api/sysPrint/detail?id=${id}`) as Promise<SysPrintDetailOutput>

/** 新增;同名拒绝由后端业务码返回(400/code=1),失败交全局拦截器提示。 */
export const addPrint = (d: SysPrintAddInput) =>
	service.post('/api/sysPrint/add', d) as Promise<number | string>

export const updatePrint = (d: SysPrintUpdateInput) =>
	service.post('/api/sysPrint/update', d) as Promise<null>

/** 复制一行(后端自动改名「原名 - copy(N)」)。 */
export const copyPrint = (id: number | string) =>
	service.post(`/api/sysPrint/copy?id=${id}`) as Promise<null>

/** 软删。 */
export const deletePrint = (id: number | string) =>
	service.post(`/api/sysPrint/delete?id=${id}`) as Promise<null>