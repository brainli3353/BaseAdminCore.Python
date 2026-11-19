/** 参数配置 API(契约 /api/sysConfig/*)。 */
import service from '../request'
import type { PageResult } from '@/types/api'

export interface SysConfigOutput {
	id: number | string
	name: string | null
	code: string
	value: string
	groupCode: string | null
	/** 内置项:禁删 */
	sysFlag: boolean
	remark: string | null
	/** 枚举选项(每行 `值|显示名`;非空 = 值列快捷下拉) */
	enumOptions: string | null
	createTime: string | null
	updateTime: string | null
}

export interface ConfigQuery {
	name?: string | null
	code?: string | null
	groupCode?: string | null
	pageIndex?: number
	pageSize?: number
	orderBy?: string
	desc?: boolean
}

export const pageConfig = (q: ConfigQuery) =>
	service.get('/api/sysConfig/page', { params: q }) as Promise<PageResult<SysConfigOutput>>

export const addConfig = (d: { name: string; code: string; value: string; groupCode?: string; remark?: string; enumOptions?: string }) =>
	service.post('/api/sysConfig/add', d) as Promise<number | string>

export const updateConfig = (d: { id: number | string; name?: string; value?: string; groupCode?: string; remark?: string; enumOptions?: string }) =>
	service.post('/api/sysConfig/update', d) as Promise<null>

export const deleteConfig = (id: number | string) =>
	service.post(`/api/sysConfig/delete?id=${id}`) as Promise<null>
