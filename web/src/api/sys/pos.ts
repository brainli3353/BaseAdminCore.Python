/** 职位管理 API(契约 /api/sysPos/*)。 */
import service from '../request'
import type { PageResult } from '@/types/api'

export interface PosOutput {
	id: number | string
	name: string | null
	code: string | null
	sort: number
	remark: string | null
	/** 0 正常 / 1 停用 */
	status: number
}

export interface PosQuery {
	name?: string | null
	pageIndex?: number
	pageSize?: number
	orderBy?: string
	desc?: boolean
	/** 状态精确过滤:0 正常 / 1 停用(批 UX,可空=不过滤) */
	status?: number | null
}

export const pagePos = (q: PosQuery) =>
	service.get('/api/sysPos/page', { params: q }) as Promise<PageResult<PosOutput>>

export const addPos = (d: { name: string; code?: string; sort?: number; remark?: string; status?: number }) =>
	service.post('/api/sysPos/add', d) as Promise<number | string>

export const updatePos = (d: {
	id: number | string
	name: string
	code?: string
	sort?: number
	remark?: string
	status?: number
}) => service.put('/api/sysPos/update', d) as Promise<null>

export const deletePos = (id: number | string) => service.delete(`/api/sysPos/delete?id=${id}`) as Promise<null>

/** 导入行级错误(契约:行级错误走 200+data,非异常)。 */
export interface ImportRowError {
	row: number
	field: string | null
	reason: string
}

/** 导入报告(契约 /api/sysPos/import)。 */
export interface ImportReport {
	total: number
	imported: number
	errors: ImportRowError[]
	/** true 时 errors 仅含前 100 条 */
	truncated: boolean
}

/** 批量导入职位(multipart,字段名 file);文件级错误由全局拦截器统一弹窗。 */
export const importPos = (file: File) => {
	const fd = new FormData()
	fd.append('file', file)
	return service.post('/api/sysPos/import', fd) as Promise<ImportReport>
}
